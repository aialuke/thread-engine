#!/usr/bin/env python3
"""Offline checks for jev.py: fake opener, fake Keychain runner. No network, no Keychain.

    python3 -m unittest discover -s research/jev-test
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import jev  # noqa: E402

KEY = "TS-SECRET-VALUE"
TYPE_PROBS = {t: (0.9 if t == "genuine" else 0.1 / 6) for t in jev.load_questions()["shared"]["type"]["criteria"]}


def answer(model: str = jev.PINNED, tokens: int = 400) -> dict:
    return {"model": model, "usage": {"input_tokens": tokens, "output_tokens": 20},
            "answers": {"asks": {"type": "noul", "noul": 0.9},
                        "relevant": {"type": "score", "score": 1.8, "probabilities": {"0": 0.0, "1": 0.2, "2": 0.8}},
                        "real": {"type": "score", "score": 2.0, "probabilities": {"0": 0.0, "1": 0.0, "2": 1.0}},
                        "useful": {"type": "score", "score": 1.0, "probabilities": {"0": 0.1, "1": 0.8, "2": 0.1}},
                        "type": {"type": "choice", "choice": "genuine", "confidence": 0.9, "probabilities": TYPE_PROBS},
                        "act": {"type": "noul", "noul": 0.7},
                        **{d: {"type": "noul", "noul": 0.2} for d in jev.load_questions().get("diagnostics", {})}}}


class FakeResponse:
    def __init__(self, body: dict) -> None:
        self.body = body

    def read(self) -> bytes:
        return json.dumps(self.body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None


def http_error(code: int, headers: dict | None = None, body: str = "{}") -> urllib.error.HTTPError:
    return urllib.error.HTTPError(jev.ENDPOINT, code, "err", headers or {}, io.BytesIO(body.encode("utf-8")))  # type: ignore[arg-type]


class FakeOpener:
    """Plays back a list of responses or exceptions and records every request."""

    def __init__(self, *outcomes) -> None:
        self.outcomes, self.requests = list(outcomes), []

    def __call__(self, request, timeout=None):
        self.requests.append((request, timeout))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return FakeResponse(outcome)


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = jev.Store(Path(self.tmp.name) / "private")
        self.sleeps: list[float] = []

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def client(self, *outcomes) -> tuple[jev.Client, FakeOpener]:
        opener = FakeOpener(*outcomes)
        return jev.Client(self.store, key=KEY, opener=opener, sleep=self.sleeps.append), opener


class RequestTests(Base):
    def test_request_shape(self) -> None:
        client, opener = self.client(answer())
        client.ask({"idea": "i", "post": "p"}, {"asks": {"type": "noul", "instructions": "q"}}, jev.PINNED)
        request, timeout = opener.requests[0]
        self.assertEqual(request.full_url, jev.ENDPOINT)
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Authorization"), f"Bearer {KEY}")
        body = json.loads(request.data)
        self.assertEqual(body["model"], "jev-1.13.0")
        self.assertEqual(body["state"], {"idea": "i", "post": "p"})
        self.assertEqual(timeout, jev.TIMEOUT)

    def test_call_is_logged_and_priced(self) -> None:
        client, _ = self.client(answer(tokens=1_000_000))
        client.ask("s", {"asks": {"type": "noul", "instructions": "q"}}, jev.PINNED, label="t")
        rows = self.store.rows(self.store.calls)
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]["cost_usd"], 0.042)
        self.assertEqual(rows[0]["model"], jev.PINNED)

    def test_cache_hit_makes_no_call(self) -> None:
        client, opener = self.client(answer())
        q = {"asks": {"type": "noul", "instructions": "q"}}
        first = client.ask("s", q, jev.PINNED)
        second = client.ask("s", q, jev.PINNED)
        self.assertEqual(len(opener.requests), 1)
        self.assertFalse(first["cached"])
        self.assertTrue(second["cached"])
        self.assertEqual(len(self.store.rows(self.store.calls)), 1)


class RetryTests(Base):
    def test_429_honours_retry_after_then_succeeds(self) -> None:
        client, opener = self.client(http_error(429, {"Retry-After": "3"}), answer())
        client.ask("s", {"asks": {"type": "noul", "instructions": "q"}}, jev.PINNED)
        self.assertEqual(len(opener.requests), 2)
        self.assertEqual(self.sleeps, [3.0])

    def test_retry_after_ms_wins(self) -> None:
        self.assertEqual(jev.retry_delay(0, {"retry-after-ms": "1500", "Retry-After": "9"}), 1.5)

    def test_backoff_without_header_is_jittered_and_capped(self) -> None:
        self.assertAlmostEqual(jev.retry_delay(0, None, rand=lambda: 0.5), 0.5)
        self.assertLessEqual(jev.retry_delay(10, None, rand=lambda: 1.0), 5.0 * 1.25)

    def test_5xx_and_529_retry_until_exhausted(self) -> None:
        client, opener = self.client(http_error(529), http_error(503), http_error(500))
        with self.assertRaises(jev.JevError):
            client.ask("s", {"asks": {"type": "noul", "instructions": "q"}}, jev.PINNED)
        self.assertEqual(len(opener.requests), jev.MAX_RETRIES + 1)

    def test_401_and_422_do_not_retry_and_never_show_the_key(self) -> None:
        for code in (401, 422):
            client, opener = self.client(http_error(code, body='{"detail": "bad"}'))
            with self.assertRaises(jev.JevError) as ctx:
                client.ask(f"s{code}", {"asks": {"type": "noul", "instructions": "q"}}, jev.PINNED)
            self.assertEqual(len(opener.requests), 1)
            self.assertIn(str(code), str(ctx.exception))
            self.assertNotIn(KEY, str(ctx.exception))
        self.assertNotIn(KEY, self.store.budget.read_text(encoding="utf-8"))

    def test_connection_error_retries(self) -> None:
        client, opener = self.client(urllib.error.URLError("reset"), answer())
        client.ask("s", {"asks": {"type": "noul", "instructions": "q"}}, jev.PINNED)
        self.assertEqual(len(opener.requests), 2)


class BudgetTests(Base):
    def test_refuses_past_the_ceiling_without_calling(self) -> None:
        self.store.append(self.store.calls, {"cost_usd": jev.CEILING})
        client, opener = self.client(answer())
        with self.assertRaises(jev.Stop):
            client.ask("s", {"asks": {"type": "noul", "instructions": "q"}}, jev.PINNED)
        self.assertEqual(opener.requests, [])
        self.assertIn("REFUSED", self.store.budget.read_text(encoding="utf-8"))

    def test_cache_hit_still_served_past_the_ceiling(self) -> None:
        client, _ = self.client(answer())
        q = {"asks": {"type": "noul", "instructions": "q"}}
        client.ask("s", q, jev.PINNED)
        self.store.append(self.store.calls, {"cost_usd": jev.CEILING})
        self.assertTrue(client.ask("s", q, jev.PINNED)["cached"])


class GateTests(Base):
    def test_real_sets_refused_until_allowed(self) -> None:
        for name in jev.REAL_SETS:
            with self.assertRaises(jev.Stop) as ctx:
                jev.load_set(name, self.store, discovery=Path(self.tmp.name))
            self.assertIn("operator", str(ctx.exception))

    def test_real_set_loads_once_allowed(self) -> None:
        discovery = Path(self.tmp.name) / "discovery"
        discovery.mkdir()
        (discovery / "corpus-stagespam-tool.jsonl").write_text(
            json.dumps({"id": "a", "idea": "CapCut", "text": "t"}) + "\n", encoding="utf-8")
        self.store.set_config(real_data=True)
        rows = jev.load_set("stagespam-tool", self.store, discovery=discovery)
        self.assertEqual(rows[0]["job"], "tool")

    def test_unknown_set_refused(self) -> None:
        with self.assertRaises(jev.Stop):
            jev.load_set("pilot", self.store)

    def test_private_dir_is_gitignored(self) -> None:
        self.assertEqual((self.store.root / ".gitignore").read_text(encoding="utf-8"), "*\n!.gitignore\n")


class KeyTests(unittest.TestCase):
    def test_presence_check_never_asks_for_the_value(self) -> None:
        seen = []

        def runner(cmd, **kwargs):
            seen.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "", "")

        self.assertTrue(jev.key_present(runner))
        self.assertNotIn("-w", seen[0])
        self.assertEqual(seen[0][seen[0].index("-s") + 1], "thread-engine-typesafe")

    def test_missing_key_message_has_no_value(self) -> None:
        def runner(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 44, "", "not found")

        with self.assertRaises(jev.JevError) as ctx:
            jev.keychain(runner)
        self.assertIn("thread-engine-typesafe", str(ctx.exception))


class QuestionTests(unittest.TestCase):
    def test_rubric_is_valid_for_both_jobs(self) -> None:
        spec = jev.load_questions()
        demand, tool = jev.questions_for("demand", spec), jev.questions_for("tool", spec)
        self.assertEqual(set(demand), {"relevant", "real", "useful", "type", "act"})
        self.assertNotEqual(demand["useful"], tool["useful"])
        for q in demand.values():
            self.assertIn(q["type"], ("score", "choice", "noul"))
            if q["type"] == "score":
                self.assertTrue(2 <= len(q["criteria"]) <= 10)
        self.assertEqual(set(demand["type"]["criteria"]), {
            "genuine", "account-selling", "promotion", "engagement-bait", "product-marketing", "off-topic", "other"})

    def test_synthetic_set_is_complete(self) -> None:
        rows = jev.Store.rows(HERE / "synthetic.jsonl")
        self.assertGreaterEqual(len(rows), 30)
        self.assertEqual(len({r["id"] for r in rows}), len(rows))
        types = {r["label"]["type"] for r in rows}
        self.assertEqual(types, set(jev.load_questions()["shared"]["type"]["criteria"]))
        for r in rows:
            self.assertIn(r["job"], ("demand", "tool"))
            self.assertEqual(set(r["label"]), {"relevant", "real", "useful", "act", "type"})


class CompareTests(Base):
    def test_level_takes_the_most_probable_and_ties_low(self) -> None:
        self.assertEqual(jev.level({"probabilities": {"0": 0.1, "1": 0.8, "2": 0.1}}), 1)
        self.assertEqual(jev.level({"probabilities": {"0": 0.5, "1": 0.0, "2": 0.5}}), 0)
        self.assertIsNone(jev.level(None))

    def test_auc(self) -> None:
        self.assertEqual(jev.auc([0.9, 0.8], [0.1, 0.2]), 1.0)
        self.assertEqual(jev.auc([0.5], [0.5]), 0.5)
        self.assertIsNone(jev.auc([], [0.1]))

    def test_run_then_compare_on_real_set(self) -> None:
        discovery = Path(self.tmp.name) / "discovery"
        discovery.mkdir()

        def write(name: str, rows: list[dict]) -> None:
            (discovery / name).write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

        write("corpus-stagespam-demand.jsonl", [{"id": "a", "idea": "i", "text": "t1"}, {"id": "b", "idea": "i", "text": "t2"}])
        write("final-scores-stagespam-demand.jsonl", [
            {"id": "a", "relevant": 2, "real": 2, "useful": 1, "act": True, "type": "genuine", "source_of_label": "agreed"},
            {"id": "b", "relevant": 0, "real": 0, "useful": 0, "act": False, "type": "promotion", "source_of_label": "first only"}])
        write("scores-stagespam-demand.jsonl", [{"id": "a", "relevant": 2, "real": 2, "useful": 1, "act": True, "type": "genuine"}])
        write("second-scores-stagespam-demand.jsonl", [])
        self.store.set_config(real_data=True)
        client, _ = self.client(answer(), answer())
        summary = jev.run_set("stagespam-demand", client, self.store, jev.PINNED, discovery=discovery, out=lambda s: None)
        self.assertEqual(summary["new_calls"], 2)
        report = jev.compare_set("stagespam-demand", self.store, discovery=discovery)
        settled = report["groups"]["settled (agreed or adjudicated)"]
        self.assertEqual(settled["posts"], 1)
        self.assertEqual(settled["jev"]["relevant"]["exact_pct"], 100.0)
        self.assertEqual(settled["jev"]["type"]["exact_pct"], 100.0)
        self.assertEqual(settled["first scorer (Codex, voted)"]["useful"]["exact_pct"], 100.0)
        first_only = report["groups"]["first only (Codex's own label)"]
        self.assertEqual(first_only["jev"]["type"]["exact_pct"], 0.0)
        # a rerun is served from the cache
        again = jev.run_set("stagespam-demand", client, self.store, jev.PINNED, discovery=discovery, out=lambda s: None)
        self.assertEqual((again["new_calls"], again["cached"]), (0, 2))

    def test_smoke_falls_back_when_pin_refused(self) -> None:
        client, _ = self.client(http_error(422, body='{"detail": "unknown model"}'), answer(model="jev-1.13.0"))
        result = jev.smoke(client, self.store)
        self.assertIn("error", result[jev.PINNED])
        self.assertEqual(result[jev.FALLBACK]["served_by"], "jev-1.13.0")
        self.assertFalse(result["pinned_held"])
        self.assertEqual(self.store.config()["model"], jev.FALLBACK)


if __name__ == "__main__":
    unittest.main()


class BlockSetTests(Base):
    """Job map, the Worth-joining packet, unavailable answers, the sealed split and the final lock."""

    def test_job_map(self) -> None:
        self.assertEqual(jev.job_of("stage1-B3-validation", {}), "worth-joining")
        self.assertEqual(jev.job_of("stage3-B3-final", {}), "tool")
        self.assertEqual(jev.job_of("stagespam-tool", {}), "tool")
        self.assertEqual(jev.job_of("stage2-B3-validation", {}), "demand")
        self.assertEqual(jev.job_of("stagespam-demand", {}), "demand")
        self.assertIn("worth-joining", jev.load_questions()["useful"])

    def test_state_carries_replies_and_age_only_when_present(self) -> None:
        self.assertEqual(jev.state_of({"idea": "i", "text": "t"}), {"idea": "i", "post": "t"})
        self.assertEqual(jev.state_of({"idea": "i", "text": "t", "replies": 4, "age_hours": 1.5}),
                         {"idea": "i", "post": "t", "replies": 4, "age_hours": 1.5})

    def test_main_questions_unchanged_and_diagnostics_added(self) -> None:
        spec = jev.load_questions()
        main = jev.questions_for("demand", spec)
        asked = jev.request_questions("demand", spec)
        self.assertEqual({k: asked[k] for k in main}, main)
        self.assertEqual(set(asked) - set(main), set(spec["diagnostics"]))

    def test_incomplete_answer_is_unavailable_never_no(self) -> None:
        qs = jev.request_questions("demand")
        self.assertEqual(jev.answer_problems(answer()["answers"], qs), [])
        broken = {k: v for k, v in answer()["answers"].items() if k != "useful"}
        self.assertTrue(any("useful" in p for p in jev.answer_problems(broken, qs)))
        self.assertEqual(jev.answer_problems(None, qs), ["no answers"])

    def fixture(self, discovery: Path) -> None:
        discovery.mkdir()
        (discovery / "posts.csv").write_text(
            "post_id,conversation_id,author_id\n1,c1,a1\n2,c2,a2\n3,c1,a3\n4,c4,a1\n5,,a5\n6,c6,a6\n", encoding="utf-8")
        (discovery / "corpus-key-stage2.json").write_text(json.dumps({"x": {"post_id": "1"}}), encoding="utf-8")
        rows = [{"id": f"n{i}", "idea": "i", "text": f"t{i}"} for i in (2, 3, 4, 5, 6)]
        (discovery / "corpus-stage1-B3.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        (discovery / "corpus-key-stage1-B3.json").write_text(json.dumps({f"n{i}": {"post_id": str(i)} for i in (2, 3, 4, 5, 6)}),
                                                             encoding="utf-8")

    def test_split_seals_development_conversations_and_refuses_to_redo(self) -> None:
        discovery = Path(self.tmp.name) / "discovery"
        self.fixture(discovery)
        info = jev.split(1, "B3", self.store, discovery)
        self.assertEqual(info["dropped"], {"conversation already in development": 1})   # post 3 shares c1 with dev post 1
        self.assertEqual(info["validation"] + info["final"], 4)
        self.assertEqual(info["authors_also_in_development"], 1)                        # post 4's author a1
        again = [json.loads(line) for h in ("validation", "final")
                 for line in (self.store.root / "splits" / f"stage1-B3-{h}.jsonl").read_text().splitlines()]
        self.assertEqual({r["id"] for r in again}, {"n2", "n4", "n5", "n6"})
        self.assertEqual(jev.half_of("c:c2"), jev.half_of("c:c2"))
        with self.assertRaises(jev.Stop):
            jev.split(1, "B3", self.store, discovery)

    def test_final_set_sealed_until_freeze(self) -> None:
        discovery = Path(self.tmp.name) / "discovery"
        self.fixture(discovery)
        jev.split(1, "B3", self.store, discovery)
        self.store.set_config(real_data=True)
        thresholds = self.store.root.parent / "thresholds.json"
        thresholds.write_text(json.dumps({"frozen": False, "coverage_threshold": None}), encoding="utf-8")
        with self.assertRaises(jev.Stop):
            jev.load_set("stage1-B3-final", self.store, discovery)
        rows = jev.load_set("stage1-B3-validation", self.store, discovery)
        self.assertTrue(all(r["job"] == "worth-joining" for r in rows))
        with self.assertRaises(jev.Stop) as ctx:               # no cut-off chosen on validation yet
            jev.freeze("test", thresholds)
        self.assertIn("coverage_threshold", str(ctx.exception))
        with self.assertRaises(jev.Stop):
            jev.load_set("stage1-B3-final", self.store, discovery)
        thresholds.write_text(json.dumps({"frozen": False, "coverage_threshold": 0.8}), encoding="utf-8")
        jev.freeze("test", thresholds)
        jev.load_set("stage1-B3-final", self.store, discovery)
        with self.assertRaises(jev.Stop):
            jev.freeze("again", thresholds)

    def test_fresh_ask_skips_the_cache_both_ways(self) -> None:
        client, opener = self.client(answer(), answer(), answer())
        q = {"asks": {"type": "noul", "instructions": "q"}}
        client.ask("s", q, jev.PINNED)
        client.ask("s", q, jev.PINNED, fresh=True)
        self.assertEqual(len(opener.requests), 2)
        self.assertTrue(client.ask("s", q, jev.PINNED)["cached"])


class PaperChecksTests(Base):
    """Ranking in both orders and the rewording check (Li et al., JEV-as-a-Judge)."""

    def rows(self) -> list[dict]:
        return [{"id": f"r{i}", "idea": "i", "text": f"t{i}", "job": "worth-joining", "replies": i, "age_hours": 1.0}
                for i in range(3)]

    def test_rank_asks_both_orders_and_averages(self) -> None:
        first = {"model": jev.PINNED, "usage": {"input_tokens": 10},
                 "answers": {"best": {"type": "choice", "probabilities": {"r0": 0.6, "r1": 0.3, "r2": 0.1}}}}
        second = {"model": jev.PINNED, "usage": {"input_tokens": 10},
                  "answers": {"best": {"type": "choice", "probabilities": {"r0": 0.2, "r1": 0.7, "r2": 0.1}}}}
        client, opener = self.client(first, second)
        original = jev.load_set
        jev.load_set = lambda *a, **k: self.rows()
        try:
            jev.rank("stage1-B3-validation", client, self.store, jev.PINNED)
        finally:
            jev.load_set = original
        self.assertEqual(len(opener.requests), 2)
        order = [[c["id"] for c in json.loads(r.data)["state"]["candidates"]] for r, _ in opener.requests]
        self.assertEqual(order[0], list(reversed(order[1])))
        result = json.loads((self.store.root / "ranks-stage1-B3-validation.json").read_text())["i"]
        self.assertEqual(result["probabilities"]["r1"], 0.5)
        self.assertFalse(result["orders_agree_on_best"])

    def test_reworded_counts_flips(self) -> None:
        good = answer()
        bad = json.loads(json.dumps(answer()))
        bad["answers"]["real"]["probabilities"] = {"0": 0.9, "1": 0.1, "2": 0.0}
        client, _ = self.client(good, bad, good, good, good, good)
        original = jev.load_set
        jev.load_set = lambda *a, **k: [{**r, "job": "demand"} for r in self.rows()]
        try:
            out = jev.reworded("stage2-B3-validation", client, self.store, jev.PINNED, n=3)
        finally:
            jev.load_set = original
        self.assertEqual((out["compared"], out["flips"]), (3, 1))


class ReviewFixTests(Base):
    """Regression tests for the 28 Sep review: the final-set seal, one validator, no overwrites, the split
    publish, and the spend ceiling."""

    fixture = BlockSetTests.fixture

    def sealed(self, cut=0.8) -> tuple[Path, Path]:
        discovery = Path(self.tmp.name) / "discovery"
        self.fixture(discovery)
        jev.split(1, "B3", self.store, discovery)
        self.store.set_config(real_data=True)
        thresholds = self.store.root.parent / "thresholds.json"
        thresholds.write_text(json.dumps({"frozen": False, "coverage_threshold": cut}), encoding="utf-8")
        return discovery, thresholds

    # 1a
    def test_freeze_refuses_without_cut_off_and_records_it(self) -> None:
        _, thresholds = self.sealed(cut=None)
        for bad in (None, True, 0.3, "0.8"):
            thresholds.write_text(json.dumps({"frozen": False, "coverage_threshold": bad}), encoding="utf-8")
            with self.assertRaises(jev.Stop):
                jev.freeze("t", thresholds)
            self.assertFalse(jev.thresholds(thresholds)["frozen"])
        thresholds.write_text(json.dumps({"frozen": False, "coverage_threshold": 0.85}), encoding="utf-8")
        data = jev.freeze("t", thresholds)
        self.assertEqual((data["frozen_coverage_threshold"], data["frozen_coverage_rule"]), (0.85, "p_good_0.5"))
        self.assertEqual(set(data["questions"]), set(jev.load_questions()["useful"]))

    # 1b
    def test_every_jev_reader_refuses_final_until_frozen(self) -> None:
        discovery, _ = self.sealed()
        client, opener = self.client()
        calls = [lambda: jev.run_set("stage1-B3-final", client, self.store, jev.PINNED, discovery=discovery, out=lambda s: None),
                 lambda: jev.repeat("stage1-B3-final", client, self.store, jev.PINNED, discovery=discovery),
                 lambda: jev.rank("stage1-B3-final", client, self.store, jev.PINNED, discovery=discovery),
                 lambda: jev.reworded("stage1-B3-final", client, self.store, jev.PINNED, discovery=discovery),
                 lambda: jev.compare_set("stage1-B3-final", self.store, discovery=discovery)]
        for call in calls:
            with self.assertRaises(jev.Stop):
                call()
        self.assertEqual(opener.requests, [])

    def test_final_refused_by_corpus_path_and_after_questions_change(self) -> None:
        _, thresholds = self.sealed()
        corpus = self.store.root / "splits" / "stage1-B3-final.jsonl"
        with self.assertRaises(jev.Stop):
            jev.check_block("anything", corpus, root=self.store.root)
        with self.assertRaises(jev.Stop):
            jev.check_block(None, Path(self.tmp.name) / "copy-stage1-B3-final.jsonl", root=self.store.root)
        with self.assertRaises(jev.Stop):
            jev.check_block("my-final", root=self.store.root)            # not a recognisable final set
        jev.freeze("t", thresholds)
        jev.check_block("stage1-B3-final", corpus, root=self.store.root)
        data = jev.thresholds(thresholds)
        data["questions"]["worth-joining"] = "000000000000"
        thresholds.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(jev.Stop) as ctx:
            jev.check_block("stage1-B3-final", root=self.store.root)
        self.assertIn("changed after the freeze", str(ctx.exception))

    # 2
    def test_answer_validation_rejects_booleans_and_bad_sums_and_renormalises(self) -> None:
        qs = jev.request_questions("demand")
        a = answer()["answers"]
        for broken in ({**a, "act": {"noul": True}},
                       {**a, "relevant": {"probabilities": {"0": False, "1": 0.2, "2": 0.8}}},
                       {**a, "useful": {"probabilities": {"0": 0.5, "1": 0.5, "2": 0.5}}}):
            self.assertTrue(jev.answer_problems(broken, qs))
        clean, problems = jev.clean_answers({**a, "relevant": {"probabilities": {"0": 0.0, "1": 0.2, "2": 0.83}}}, qs)
        self.assertEqual(problems, [])
        self.assertAlmostEqual(sum(clean["relevant"]["probabilities"].values()), 1.0)

    def test_run_set_marks_bad_rows_unavailable_and_stores_renormalised(self) -> None:
        discovery = Path(self.tmp.name) / "discovery"
        discovery.mkdir()
        (discovery / "corpus-stagespam-demand.jsonl").write_text(
            "".join(json.dumps({"id": i, "idea": "i", "text": i}) + "\n" for i in ("a", "b")), encoding="utf-8")
        self.store.set_config(real_data=True)
        off = answer()
        off["answers"]["relevant"]["probabilities"] = {"0": 0.0, "1": 0.2, "2": 0.83}
        bad = answer()
        bad["answers"]["act"] = {"type": "noul", "noul": False}
        client, _ = self.client(off, bad)
        summary = jev.run_set("stagespam-demand", client, self.store, jev.PINNED, discovery=discovery, out=lambda s: None)
        self.assertEqual(summary["unavailable"], 1)
        saved = {r["id"]: r for r in self.store.rows(self.store.root / "answers-stagespam-demand.jsonl")}
        self.assertAlmostEqual(sum(saved["a"]["answers"]["relevant"]["probabilities"].values()), 1.0)
        self.assertIsNone(saved["b"]["answers"])
        self.assertTrue(saved["b"]["unavailable"])

    # 4
    def test_run_set_refuses_to_overwrite_answers_to_other_questions(self) -> None:
        discovery = Path(self.tmp.name) / "discovery"
        discovery.mkdir()
        (discovery / "corpus-stagespam-demand.jsonl").write_text(json.dumps({"id": "a", "idea": "i", "text": "t"}) + "\n",
                                                                 encoding="utf-8")
        self.store.set_config(real_data=True)
        path = self.store.root / "answers-stagespam-demand.jsonl"
        path.write_text(json.dumps({"id": "a", "questions": "oldhash00000", "answers": None}) + "\n", encoding="utf-8")
        client, opener = self.client(answer())
        with self.assertRaises(jev.Stop):
            jev.run_set("stagespam-demand", client, self.store, jev.PINNED, discovery=discovery, out=lambda s: None)
        self.assertEqual(opener.requests, [])
        self.assertIn("oldhash00000", path.read_text(encoding="utf-8"))
        jev.run_set("stagespam-demand", client, self.store, jev.PINNED, discovery=discovery, out=lambda s: None, replace=True)
        self.assertEqual(len(list(self.store.root.glob("answers-stagespam-demand.jsonl.*.bak"))), 1)
        self.assertNotIn("oldhash00000", path.read_text(encoding="utf-8"))

    def test_repeat_skips_tries_already_done(self) -> None:
        rows = [{"id": "r0", "idea": "i", "text": "t", "job": "demand"}]
        original = jev.load_set
        jev.load_set = lambda *a, **k: rows
        try:
            client, opener = self.client(answer(), answer(), answer())
            jev.repeat("stage2-B3-validation", client, self.store, jev.PINNED, n=1, times=2)
            out = jev.repeat("stage2-B3-validation", client, self.store, jev.PINNED, n=1, times=3)
        finally:
            jev.load_set = original
        self.assertEqual(len(opener.requests), 3)
        self.assertEqual(out["skipped_already_done"], 2)
        saved = self.store.rows(self.store.root / "repeats-stage2-B3-validation.jsonl")
        self.assertEqual(sorted((r["id"], r["try"]) for r in saved), [("r0", 0), ("r0", 1), ("r0", 2)])

    # 7a
    def test_split_leftovers_are_reported_and_unsealed(self) -> None:
        discovery = Path(self.tmp.name) / "discovery"
        self.fixture(discovery)
        splits = self.store.root / "splits"
        splits.mkdir(parents=True)
        (splits / "stage1-B3-validation.jsonl").write_text("", encoding="utf-8")   # a half with no manifest
        self.store.set_config(real_data=True)
        with self.assertRaises(jev.Stop) as ctx:
            jev.load_set("stage1-B3-validation", self.store, discovery)
        self.assertIn("not sealed", str(ctx.exception))
        self.assertIn("stage1-B3-validation.jsonl", str(ctx.exception))
        with self.assertRaises(jev.Stop) as ctx:
            jev.split(1, "B3", self.store, discovery)
        self.assertIn("partial split", str(ctx.exception))
        (splits / "stage1-B3-validation.jsonl").unlink()
        jev.split(1, "B3", self.store, discovery)
        self.assertEqual(sorted(p.name for p in splits.iterdir()),
                         ["split-stage1-B3.json", "stage1-B3-final.jsonl", "stage1-B3-validation.jsonl"])

    def test_split_publishes_nothing_if_a_write_fails(self) -> None:
        discovery = Path(self.tmp.name) / "discovery"
        self.fixture(discovery)
        original, seen = jev.os.replace, []

        def failing(src, dst):
            if seen:
                raise OSError("disk full")
            seen.append(dst)
            original(src, dst)

        jev.os.replace = failing
        try:
            with self.assertRaises(OSError):
                jev.split(1, "B3", self.store, discovery)
        finally:
            jev.os.replace = original
        self.assertFalse((self.store.root / "splits" / "split-stage1-B3.json").exists())
        with self.assertRaises(jev.Stop):                      # half-published: reported, never read
            jev.check_block("stage1-B3-validation", root=self.store.root)

    # 8
    def test_overshoot_refuses_every_later_call(self) -> None:
        self.store.append(self.store.calls, {"cost_usd": jev.CEILING - 0.001})
        client, opener = self.client(answer(tokens=1_000_000), answer())
        q = {"asks": {"type": "noul", "instructions": "q"}}
        client.ask("s1", q, jev.PINNED)                       # reserve fits; the real cost ($0.042) overshoots
        self.assertGreater(self.store.spent(), jev.CEILING)
        with self.assertRaises(jev.Stop):
            client.ask("s2", q, jev.PINNED)
        self.assertEqual(len(opener.requests), 1)

    def test_reserve_is_two_characters_a_token(self) -> None:
        q = {"asks": {"type": "noul", "instructions": "q"}}
        state = "x" * 200_000
        chars = len(json.dumps({"state": state, "model": jev.PINNED, "questions": q}, ensure_ascii=False))
        # room for a 3-characters-a-token reserve, not for a 2-characters-a-token one
        self.store.append(self.store.calls, {"cost_usd": jev.CEILING - (chars // 3 + 1) * jev.PRICE_PER_TOKEN - 0.0001})
        client, opener = self.client(answer())
        with self.assertRaises(jev.Stop):
            client.ask(state, q, jev.PINNED)
        self.assertEqual(opener.requests, [])


class B4ParentTests(Base):
    """28 Sep: B4 arm 3, replies rated again with the post they reply to (README.md, Experiment 4)."""

    fixture = BlockSetTests.fixture

    def sealed(self) -> Path:
        discovery = Path(self.tmp.name) / "discovery"
        self.fixture(discovery)
        jev.split(1, "B3", self.store, discovery)
        self.store.set_config(real_data=True)
        thresholds = self.store.root.parent / "thresholds.json"
        thresholds.write_text(json.dumps({"frozen": True, "frozen_coverage_threshold": 0.8,
                                          "questions": {j: jev.questions_hash(jev.request_questions(j))
                                                        for j in jev.load_questions()["useful"]}}), encoding="utf-8")
        rows = [{"post_id": "2", "stage": 1, "found": True, "parent_text": "the parent of 2"},
                {"post_id": "4", "stage": 1, "found": False, "parent_text": None},
                {"post_id": "5", "stage": 1, "found": True, "parent_text": "the parent of 5"}]
        (discovery / "parents-B3.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        return discovery

    def test_live_questions_still_hash_to_the_frozen_ones(self) -> None:
        frozen = jev.thresholds()
        spec = jev.load_questions()
        self.assertTrue(frozen["frozen"])
        self.assertEqual({job: jev.questions_hash(jev.request_questions(job, spec)) for job in spec["useful"]},
                         frozen["questions"])

    def test_parent_set_holds_only_found_parents_with_the_same_ids_and_is_written_once(self) -> None:
        discovery = self.sealed()
        halves = {h: {r["id"] for r in jev.Store.rows(self.store.root / "splits" / f"stage1-B3-{h}.jsonl")}
                  for h in ("validation", "final")}
        parented, not_found = set(), 0
        for half in ("validation", "final"):
            info = jev.parent_set(1, "B3", half, self.store, discovery)
            not_found += info["parent_not_found"]
            rows = jev.Store.rows(self.store.root / "splits" / f"stage1-B3-{half}-parent.jsonl")
            self.assertTrue({r["id"] for r in rows} <= halves[half])
            self.assertTrue(all(r["parent"].startswith("the parent of") for r in rows))
            parented |= {r["id"] for r in rows}
            with self.assertRaisesRegex(jev.Stop, "sealed"):
                jev.parent_set(1, "B3", half, self.store, discovery)
        self.assertEqual((parented, not_found), ({"n2", "n5"}, 1))            # n4's parent is gone
        half = "validation" if "n2" in halves["validation"] else "final"
        row = next(r for r in jev.load_set(f"stage1-B3-{half}-parent", self.store, discovery) if r["id"] == "n2")
        self.assertEqual((row["job"], jev.state_of(row)["parent"]), ("worth-joining", "the parent of 2"))

    def test_parent_names_follow_their_half_through_the_seal(self) -> None:
        self.sealed()
        self.assertEqual(jev.BLOCK_SET.match("stage2-B4-final-parent").groups(), ("2", "B4", "final", "-parent"))
        self.assertIsNone(jev.BLOCK_SET.match("stage2-B4-parent"))
        thresholds = self.store.root.parent / "thresholds.json"
        thresholds.write_text(json.dumps({"frozen": False, "coverage_threshold": 0.8}), encoding="utf-8")
        with self.assertRaisesRegex(jev.Stop, "sealed"):
            jev.check_block("stage1-B3-final-parent", root=self.store.root)
        with self.assertRaisesRegex(jev.Stop, "not sealed"):
            jev.check_block("stage1-B9-validation-parent", root=self.store.root)
        with self.assertRaisesRegex(jev.Stop, "missing"):
            jev.parent_set(1, "B3", "validation", self.store, Path(self.tmp.name) / "nowhere")

    def test_state_carries_the_parent_only_when_present(self) -> None:
        self.assertEqual(jev.state_of({"idea": "i", "text": "t", "parent": "p"}), {"idea": "i", "post": "t", "parent": "p"})
        self.assertNotIn("parent", jev.state_of({"idea": "i", "text": "t"}))
