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
        thresholds.write_text(json.dumps({"frozen": False}), encoding="utf-8")
        with self.assertRaises(jev.Stop):
            jev.load_set("stage1-B3-final", self.store, discovery)
        rows = jev.load_set("stage1-B3-validation", self.store, discovery)
        self.assertTrue(all(r["job"] == "worth-joining" for r in rows))
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
