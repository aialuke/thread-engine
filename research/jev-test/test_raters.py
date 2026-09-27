#!/usr/bin/env python3
"""Offline checks for raters.py. Temp dirs and made-up posts only. No network, no real data.

    python3 -m unittest discover -s research/jev-test
"""

from __future__ import annotations

import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import raters  # noqa: E402

QUESTIONS = {
    "relevant": {"type": "score", "instructions": "How close?", "criteria": ["a", "b", "c"]},
    "real": {"type": "score", "instructions": "Real?", "criteria": ["a", "b", "c"]},
    "useful": {"type": "score", "instructions": "Useful?", "criteria": ["a", "b", "c"]},
    "type": {"type": "choice", "instructions": "Kind?", "criteria": {"genuine": "g", "promotion": "p"}},
    "act": {"type": "noul", "instructions": "Act?"},
}
CORPUS = {"a1": {"id": "a1", "idea": "idea one", "text": "First made-up post, long enough to open with"},
          "b2": {"id": "b2", "idea": "idea one", "text": "Second made-up post\nwith a line break in it"}}


def score(level: int, p: float = 0.8) -> dict:
    rest = (1 - p) / 2
    return {"probabilities": {str(k): (p if k == level else rest) for k in range(3)}}


def answers(rel: int = 2, real: int = 2, use: int = 2, p: float = 0.8) -> dict:
    return {"relevant": score(rel, p), "real": score(real, p), "useful": score(use, p),
            "type": {"probabilities": {"genuine": 0.9, "promotion": 0.1}}, "act": {"noul": 0.7}}


def line(pid: str, **kw) -> str:
    return json.dumps({"id": pid, "opening": CORPUS[pid]["text"][:30], "answers": answers(**kw)})


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.private = self.root / "private"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def file(self, name: str, text: str) -> Path:
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def write_rater(self, rater: str, set_name: str, verdicts: dict, repeat: bool = False, p: float = 0.8) -> None:
        """verdicts: id -> True (good) | False (not good) | None (unavailable row)."""
        path = raters.rater_file(self.private, rater, set_name, repeat)
        path.parent.mkdir(parents=True, exist_ok=True)
        out = []
        for pid, v in verdicts.items():
            if v is None:
                out.append({"id": pid, "unavailable": True, "answers": None})
            else:
                out.append({"id": pid, "answers": answers(2 if v else 0, 2, 2, p)})
        path.write_text("".join(json.dumps(r) + "\n" for r in out), encoding="utf-8")


class BriefTests(unittest.TestCase):
    def test_brief_lists_every_question_verbatim(self) -> None:
        brief = raters.rater_brief("synthetic", QUESTIONS, "corpus.jsonl", "demand")
        for qid, q in QUESTIONS.items():
            self.assertIn(f'"{qid}"', brief)
            self.assertIn(json.dumps(q["instructions"]), brief)
        self.assertIn("corpus.jsonl", brief)
        self.assertIn("age_hours", brief)
        self.assertIn("replies", brief)
        self.assertIn("Do not search", brief)

    def test_brief_from_the_real_rubric_names_every_question(self) -> None:
        questions = raters.spec_questions("demand")
        brief = raters.rater_brief("synthetic", questions, "c.jsonl", "demand")
        for qid in questions:
            self.assertIn(f'"{qid}"', brief)

    def test_brief_example_line_passes_ingest_checks(self) -> None:
        for q in QUESTIONS.values():
            _, problem = raters.check_answer("q", q, raters.example_answer(q))
            self.assertIsNone(problem)


class IngestTests(Base):
    def ingest(self, text: str, **kw) -> dict:
        return raters.ingest("codex", "s", [self.file("out.txt", text)], CORPUS, QUESTIONS, self.private, **kw)

    def test_happy_path_writes_rows_in_jevs_shape(self) -> None:
        result = self.ingest(line("a1") + "\n" + line("b2") + "\n")
        self.assertEqual((result["rows"], result["of"]), (2, 2))
        saved = raters.rows(self.private / "raters" / "codex-s.jsonl")
        self.assertEqual([r["id"] for r in saved], ["a1", "b2"])
        self.assertEqual(saved[0]["answers"]["type"]["choice"], "genuine")
        self.assertTrue((self.private / ".gitignore").exists())

    def test_repeat_goes_to_its_own_file(self) -> None:
        self.ingest(line("a1") + "\n" + line("b2"), repeat=True)
        self.assertTrue((self.private / "raters" / "codex-s-repeat.jsonl").exists())
        self.assertFalse((self.private / "raters" / "codex-s.jsonl").exists())

    def test_preamble_and_grok_envelope(self) -> None:
        text = "Here are my ratings." + line("a1") + "\n```\n" + line("b2") + "\n```"
        self.assertEqual(self.ingest(json.dumps({"text": text}))["rows"], 2)

    def test_opening_is_case_and_whitespace_insensitive(self) -> None:
        row = json.loads(line("b2"))
        row["opening"] = "  SECOND made-up   post with a"
        self.assertEqual(self.ingest(line("a1") + "\n" + json.dumps(row))["rows"], 2)

    def test_small_sum_error_is_renormalised(self) -> None:
        row = json.loads(line("a1"))
        row["answers"]["relevant"]["probabilities"] = {"0": 0.0, "1": 0.2, "2": 0.83}
        result = self.ingest(json.dumps(row) + "\n" + line("b2"))
        self.assertEqual(result["renormalised_answers"], 1)
        saved = raters.rows(self.private / "raters" / "codex-s.jsonl")[0]
        self.assertAlmostEqual(sum(saved["answers"]["relevant"]["probabilities"].values()), 1.0)

    def assert_nothing_written(self, text: str, needle: str) -> None:
        with self.assertRaises(ValueError) as ctx:
            self.ingest(text)
        self.assertIn(needle, str(ctx.exception))
        self.assertFalse((self.private / "raters" / "codex-s.jsonl").exists())

    def test_fail_closed_on_missing_id(self) -> None:
        self.assert_nothing_written(line("a1"), "b2: missing")

    def test_fail_closed_on_duplicate_id(self) -> None:
        self.assert_nothing_written(line("a1") + "\n" + line("a1") + "\n" + line("b2"), "a1: answered 2 times")

    def test_fail_closed_on_bad_sum(self) -> None:
        row = json.loads(line("a1"))
        row["answers"]["useful"]["probabilities"] = {"0": 0.5, "1": 0.5, "2": 0.5}
        self.assert_nothing_written(json.dumps(row) + "\n" + line("b2"), "sum to 1.500")

    def test_fail_closed_on_wrong_opening(self) -> None:
        row = json.loads(line("a1"))
        row["opening"] = "Something else entirely here"
        self.assert_nothing_written(json.dumps(row) + "\n" + line("b2"), "opening")

    def test_fail_closed_on_missing_question_or_bad_noul(self) -> None:
        row = json.loads(line("a1"))
        del row["answers"]["type"]
        row["answers"]["act"] = {"noul": 1.4}
        self.assert_nothing_written(json.dumps(row) + "\n" + line("b2"), "type: missing")


class GoodnessTests(unittest.TestCase):
    def test_p_good(self) -> None:
        a = {"relevant": {"probabilities": {"0": 0.1, "1": 0.1, "2": 0.8}},
             "real": {"probabilities": {"0": 0.0, "1": 0.5, "2": 0.5}},
             "useful": {"probabilities": {"0": 0.4, "1": 0.3, "2": 0.3}}}
        self.assertAlmostEqual(raters.p_good(a), 0.8 * 0.5 * 0.6)
        self.assertIsNone(raters.p_good(None))
        self.assertIsNone(raters.p_good({"relevant": a["relevant"]}))

    def test_good_level_uses_most_probable_with_ties_low(self) -> None:
        self.assertTrue(raters.good_level(answers(2, 2, 1)))
        self.assertFalse(raters.good_level(answers(2, 1, 2)))
        self.assertFalse(raters.good_level(answers(2, 2, 0)))
        tie = answers()
        tie["real"] = {"probabilities": {"0": 0.0, "1": 0.5, "2": 0.5}}
        self.assertFalse(raters.good_level(tie))
        self.assertIsNone(raters.good_level(None))


class StatsTests(unittest.TestCase):
    def test_kappa_on_a_hand_worked_table(self) -> None:
        # yes/yes 20, yes/no 5, no/yes 10, no/no 15; n 50
        # po = 35/50 = 0.7; pa = 25/50 = 0.5, pb = 30/50 = 0.6; pe = 0.3 + 0.2 = 0.5; kappa = 0.4
        pairs = [(True, True)] * 20 + [(True, False)] * 5 + [(False, True)] * 10 + [(False, False)] * 15
        self.assertAlmostEqual(raters.kappa(pairs), 0.4)
        self.assertIsNone(raters.kappa([(True, True)] * 3))

    def test_bootstrap_is_deterministic_and_resamples_conversations(self) -> None:
        ids = ["a", "b", "c", "d"]
        convo = {"a": "c1", "b": "c1", "c": "c2", "d": "c3"}
        a = {"a": True, "b": True, "c": False, "d": True}
        b = {"a": True, "b": False, "c": False, "d": False}
        stat = lambda s: raters.agree_pct([(a[i], b[i]) for i in s])  # noqa: E731
        one = raters.bootstrap(ids, convo.get, stat, 200, seed=5)
        self.assertEqual(one, raters.bootstrap(ids, convo.get, stat, 200, seed=5))
        rng = random.Random(1)
        clusters = raters.clusters_of(ids, convo.get)
        for _ in range(200):
            draw = raters.resample(clusters, rng)
            self.assertEqual(draw.count("a"), draw.count("b"))
        # missing conversation id: the post is its own conversation
        key = {"a": {"post_id": "a", "conversation_id": "c1"}, "b": {"post_id": "b", "conversation_id": "c1"},
               "c": {"post_id": "c"}, "d": {"post_id": "d"}}
        stats = raters.pair_stats(a, b, lambda i: key[i].get("conversation_id") or key[i]["post_id"], 5, 100)
        self.assertEqual(stats["conversations"], 3)

    def test_soft_agreement_leave_one_out(self) -> None:
        p = {"x": {"1": 0.9, "2": 0.1}, "y": {"1": 0.7, "2": 0.3}, "z": {"1": 0.5, "2": 0.5, "3": 0.2}}
        out = raters.soft_agreement(p)
        self.assertEqual(out["n"], 2)
        # x: |0.9-0.6| = 0.3, |0.1-0.4| = 0.3 -> 0.3; y: |0.7-0.7|, |0.3-0.3| -> 0; z: |0.5-0.8|, |0.5-0.2| -> 0.3
        self.assertEqual(out["raters"], {"x": 0.3, "y": 0.0, "z": 0.3})

    def test_coverage_thresholds(self) -> None:
        p = {"1": 0.97, "2": 0.15, "3": 0.35, "4": 0.55}     # confidence 0.97, 0.85, 0.65, 0.55
        binary = {i: v >= 0.5 for i, v in p.items()}
        panel = {"1": True, "2": True, "3": False, "4": True}
        cov = raters.coverage(p, binary, panel)
        by_t = {row["threshold"]: row for row in cov["curve"]}
        self.assertEqual([by_t[t]["posts"] for t in raters.THRESHOLDS], [4, 3, 2, 2, 1, 1])
        self.assertEqual(by_t[0.5]["share_pct"], 100.0)
        self.assertEqual((by_t[0.5]["n"], by_t[0.5]["agreement_pct"]), (4, 75.0))
        self.assertEqual((by_t[0.8]["n"], by_t[0.8]["agreement_pct"]), (2, 50.0))
        self.assertEqual(by_t[0.95]["agreement_pct"], 100.0)
        self.assertEqual(sum(b["n"] for b in cov["calibration"]), 4)

    def test_majority_excludes_ties(self) -> None:
        self.assertTrue(raters.majority([True, True, False]))
        self.assertIsNone(raters.majority([True, False]))
        self.assertIsNone(raters.majority([True]))


class CompareTests(Base):
    def setUp(self) -> None:
        super().setUp()
        self.ids = [f"p{n}" for n in range(8)]
        self.key = {i: {"post_id": i, "conversation_id": f"c{n // 2}"} for n, i in enumerate(self.ids)}
        self.idea_of = {i: ("idea one" if n < 4 else "idea two") for n, i in enumerate(self.ids)}
        truth = {i: n % 2 == 0 for n, i in enumerate(self.ids)}
        self.write_rater("jev", "s", {**truth, "p7": None}, p=0.9)
        self.write_rater("codex", "s", truth)
        self.write_rater("claude", "s", {**truth, "p1": True})
        self.write_rater("grok", "s", truth)
        self.write_rater("codex", "s", {**truth, "p3": True}, repeat=True)
        self.operator = {"sample": "x", "labels": [
            {"id": "p0", "label": "reply", "why": ""}, {"id": "p1", "label": "no", "why": ""},
            {"id": "p2", "label": "post", "why": ""}, {"id": "p3", "label": "unsure", "why": ""},
            {"id": "p4", "label": None, "why": ""}]}

    def run_compare(self) -> dict:
        return raters.compare("s", self.private, self.key, self.idea_of, self.operator,
                              ["codex", "claude", "grok"], resamples=50)

    def pair(self, report: dict, a: str, b: str) -> dict:
        return next(p for p in report["pairwise"] if {p["a"], p["b"]} == {a, b})

    def test_report_is_written_and_directional(self) -> None:
        report = self.run_compare()
        saved = json.loads((self.private / "compare-raters-s.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["pairwise"], json.loads(json.dumps(report["pairwise"])))
        self.assertIn("Directional", report["note"])
        self.assertTrue(all("n" in p for p in report["pairwise"]))

    def test_unavailable_rows_are_excluded_not_counted_as_no(self) -> None:
        report = self.run_compare()
        self.assertEqual(report["raters"]["jev"], {"available": 7, "unavailable": 1, "file_found": True})
        jc = self.pair(report, "jev", "codex")
        self.assertEqual((jc["n"], jc["agreement_pct"]), (7, 100.0))
        self.assertEqual(report["jev_coverage"]["good_level"]["posts"], 7)

    def test_pairwise_self_agreement_and_operator(self) -> None:
        report = self.run_compare()
        cc = self.pair(report, "codex", "claude")
        self.assertEqual((cc["n"], cc["agreement_pct"]), (8, 87.5))
        self.assertEqual(len(cc["agreement_ci90"]), 2)
        self.assertEqual(report["self_agreement"]["codex"]["agreement_pct"], 87.5)
        self.assertEqual(cc["self_agreement_ceiling_pct"], {"codex": 87.5})
        jo = self.pair(report, "jev", "operator")
        self.assertEqual((jo["n"], jo["agreement_pct"]), (3, 100.0))   # unsure and blank excluded
        self.assertIn(raters.JEV_P50, {p["a"] for p in report["pairwise"]} | {p["b"] for p in report["pairwise"]})
        self.assertEqual(report["operator"]["reply_n"], 1)
        self.assertAlmostEqual(report["operator"]["reply_pct"], 33.3)

    def test_per_idea_and_soft_agreement(self) -> None:
        report = self.run_compare()
        one = next(r for r in report["per_idea"] if r["idea"] == "idea one")
        self.assertEqual(one["jev_vs"]["claude"]["n"], 4)
        self.assertEqual(one["jev_vs"]["claude"]["agreement_pct"], 75.0)
        self.assertEqual(report["soft_agreement"]["n"], 7)

    def test_reply_worthy_auc(self) -> None:
        path = raters.rater_file(self.private, "jev", "s")
        out = []
        for r in raters.rows(path):
            if r.get("answers"):
                r["answers"]["reply_worthy"] = {"noul": 0.9 if r["id"] == "p0" else 0.2}
            out.append(r)
        path.write_text("".join(json.dumps(r) + "\n" for r in out), encoding="utf-8")
        auc = self.run_compare()["operator"]["jev_reply_worthy_auc"]
        self.assertEqual((auc["auc"], auc["n_reply"], auc["n_not_reply"]), (1.0, 1, 2))


if __name__ == "__main__":
    unittest.main()


class PaperMeasuresTests(unittest.TestCase):
    def test_coverage_has_random_baseline_and_auroc(self) -> None:
        p = {"a": 0.95, "b": 0.9, "c": 0.55, "d": 0.5}
        binary = {"a": True, "b": True, "c": True, "d": False}
        panel = {"a": True, "b": True, "c": False, "d": True}
        out = raters.coverage(p, binary, panel)
        self.assertEqual(out["curve"][0]["random_same_share_agreement_pct"], 50.0)
        self.assertEqual(out["confidence_auroc"]["auroc"], 1.0)   # confident posts agree, unsure ones don't
