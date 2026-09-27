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

import jev  # noqa: E402
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


class ReviewFixTests(Base):
    """Regression tests for the 28 Sep review: seal and corpus binding, one validator, per-rule confidence,
    no overwrites, undefined kappa draws, per-idea intervals, the operator splits and the type majority."""

    FINAL = "stage2-B3-final"

    def seal(self, freeze: bool = False) -> Path:
        splits = self.private / "splits"
        splits.mkdir(parents=True, exist_ok=True)
        (splits / "split-stage2-B3.json").write_text("{}", encoding="utf-8")
        for half in ("validation", "final"):
            (splits / f"stage2-B3-{half}.jsonl").write_text(
                "".join(json.dumps(c) + "\n" for c in CORPUS.values()), encoding="utf-8")
        thresholds = self.root / "thresholds.json"
        thresholds.write_text(json.dumps({"frozen": False, "coverage_threshold": 0.8}), encoding="utf-8")
        if freeze:
            jev.freeze("t", thresholds)
        return splits

    # 2
    def test_one_validator_shared_with_jev(self) -> None:
        self.assertIs(raters.check_answer, jev.check_answer)
        _, problem = raters.check_answer("act", QUESTIONS["act"], {"noul": True})
        self.assertIsNotNone(problem)

    # 1b
    def test_ingest_brief_and_compare_refuse_final_until_frozen(self) -> None:
        splits = self.seal()
        final = splits / f"{self.FINAL}.jsonl"
        out = self.file("out.txt", line("a1") + "\n" + line("b2"))
        with self.assertRaises(SystemExit):
            raters.ingest("codex", self.FINAL, [out], CORPUS, QUESTIONS, self.private, corpus_path=final)
        with self.assertRaises(SystemExit):                  # by corpus path, whatever the set is called
            raters.ingest("codex", "s", [out], CORPUS, QUESTIONS, self.private, corpus_path=final)
        with self.assertRaises(SystemExit):
            raters.compare(self.FINAL, self.private, {}, {}, None, ["codex"], resamples=10)
        with self.assertRaises(SystemExit):
            raters.main(["brief", "--set", self.FINAL, "--corpus", str(final), "--job", "demand"])
        self.assertFalse((self.private / "raters").exists())

    # 1c
    def test_corpus_is_bound_to_the_set(self) -> None:
        splits = self.seal()
        validation = splits / "stage2-B3-validation.jsonl"
        raters.bind("stage2-B3-validation", validation, "demand")
        with self.assertRaises(SystemExit):
            raters.bind("stage1-B3-validation", validation)         # another stage
        with self.assertRaises(SystemExit):
            raters.bind("stage2-B4-validation", validation)         # another block
        with self.assertRaises(SystemExit):
            raters.bind("stage2-B3-validation", splits / "stage2-B3-other.jsonl")
        with self.assertRaises(SystemExit):
            raters.bind("stage2", validation)                       # a development set against a block file
        with self.assertRaises(SystemExit):
            raters.bind("stage2-B3-validation", validation, "tool")  # stage 2 is demand
        with self.assertRaises(SystemExit):
            raters.set_job("stage2-B3-validation", {"x": {"id": "x", "job": "tool"}})
        out = self.file("out.txt", line("a1") + "\n" + line("b2"))
        with self.assertRaises(SystemExit):
            raters.ingest("codex", "stage1-B3-validation", [out], CORPUS, QUESTIONS, self.private, corpus_path=validation)

    # 1d
    def test_compare_on_final_reports_the_preregistered_cut_off(self) -> None:
        self.seal(freeze=True)
        ids = [f"p{n}" for n in range(8)]
        truth = {i: n % 2 == 0 for n, i in enumerate(ids)}
        self.write_rater("jev", self.FINAL, {**truth, "p7": None}, p=0.9)
        for r in ("codex", "claude", "grok"):
            self.write_rater(r, self.FINAL, truth)
        key = {i: {"post_id": i, "conversation_id": f"c{n // 2}"} for n, i in enumerate(ids)}
        report = raters.compare(self.FINAL, self.private, key, {i: "idea" for i in ids}, None,
                                ["codex", "claude", "grok"], resamples=20)
        pre = report["preregistered"]
        # good posts: p_good 0.9 * 0.9 * 0.95 = 0.77 (under the 0.8 cut); not good: 1 - 0.043 = 0.96 (over it)
        self.assertEqual((pre["coverage_threshold"], pre["rule"]), (0.8, "p_good_0.5"))
        self.assertEqual((pre["posts"], pre["of"], pre["share_pct"], pre["agreement_pct"]), (3, 7, 42.9, 100.0))
        self.assertIn("exploratory", report["jev_coverage"]["status"])

    # 3
    def test_each_rule_has_its_own_confidence(self) -> None:
        a = {"relevant": {"probabilities": {"0": 0.25, "1": 0.35, "2": 0.40}},
             "real": {"probabilities": {"0": 0.25, "1": 0.35, "2": 0.40}},
             "useful": {"probabilities": {"0": 0.30, "1": 0.40, "2": 0.30}}}
        self.assertTrue(raters.good_level(a))                       # every most probable level is good
        pg = raters.p_good(a)
        self.assertAlmostEqual(pg, 0.4 * 0.4 * 0.7)                 # 0.112, so p_good calls it not good
        self.assertAlmostEqual(raters.confidence_p50(pg), 0.888)    # confident in "not good"
        self.assertAlmostEqual(raters.confidence_good_level(a), 0.112)   # not confident in "good"
        cov = raters.coverage({"x": pg}, {"x": True}, {"x": False}, confidence={"x": raters.confidence_good_level(a)})
        self.assertEqual(cov["curve"][0]["posts"], 0)               # never counted as a confident good_level call
        self.assertEqual(raters.coverage({"x": pg}, {"x": False}, {"x": False})["curve"][0]["posts"], 1)

    # 4
    def test_ingest_never_overwrites_and_replace_keeps_a_backup(self) -> None:
        text = line("a1") + "\n" + line("b2")
        run = lambda **kw: raters.ingest("codex", "s", [self.file("out.txt", text)], CORPUS, QUESTIONS,  # noqa: E731
                                         self.private, **kw)
        run()
        with self.assertRaises(ValueError) as ctx:
            run()
        self.assertIn("already exists", str(ctx.exception))
        result = run(replace=True)
        self.assertIn(".bak", result["backup"])
        self.assertEqual(len(list((self.private / "raters").glob("codex-s.jsonl.*.bak"))), 1)

    # 6a
    def test_undefined_kappa_draws_are_counted_and_flag_instability(self) -> None:
        ids = [f"x{n}" for n in range(10)]
        a = {i: True for i in ids}
        b = dict(a)
        a["x0"] = b["x0"] = False            # only one conversation varies: most draws have constant raters
        stats = raters.pair_stats(a, b, lambda i: i, 5, 200)
        self.assertGreater(stats["kappa_undefined_pct"], 10.0)
        self.assertTrue(stats["kappa_ci90_unstable"])
        stable = raters.bootstrap_detail(ids, lambda i: i, lambda s: raters.agree_pct([(a[i], b[i]) for i in s]), 50, 5)
        self.assertEqual((stable["undefined_pct"], stable["unstable"]), (0.0, False))

    # 6b, 6c, 6d
    def compare_with_operator(self) -> dict:
        ids = [f"p{n}" for n in range(8)]
        truth = {i: n % 2 == 0 for n, i in enumerate(ids)}
        self.write_rater("jev", "s", truth, p=0.9)
        path = raters.rater_file(self.private, "jev", "s")
        out = []
        for r in raters.rows(path):
            r["answers"]["text_decidable"] = {"noul": 0.1 if r["id"] == "p3" else 0.9}
            out.append(r)
        path.write_text("".join(json.dumps(r) + "\n" for r in out), encoding="utf-8")
        for r in ("codex", "claude", "grok"):
            self.write_rater(r, "s", truth)
        operator = {"sample": "x", "labels": [
            {"id": "p0", "label": "reply"}, {"id": "p1", "label": "no"}, {"id": "p2", "label": "post"},
            {"id": "p3", "label": "unsure"}]}
        sample = {"sample": "x", "posts": [{"id": "p0", "why_chosen": "disputed"}, {"id": "p1", "why_chosen": "disputed"},
                                           {"id": "p2", "why_chosen": "random (panel agreed)"},
                                           {"id": "p3", "why_chosen": "random (panel agreed)"}]}
        key = {i: {"post_id": i, "conversation_id": f"c{n // 2}"} for n, i in enumerate(ids)}
        return raters.compare("s", self.private, key, {i: "idea one" for i in ids}, operator,
                              ["codex", "claude", "grok"], resamples=20, sample=sample)

    def test_per_idea_has_intervals_and_prevalence(self) -> None:
        row = self.compare_with_operator()["per_idea"][0]["jev_vs"]["codex"]
        for k in ("n", "agreement_pct", "kappa", "yes_pct_jev", "yes_pct_other", "agreement_ci90", "kappa_ci90",
                  "conversations"):
            self.assertIn(k, row)

    def test_text_decidable_against_operator_unsure(self) -> None:
        auc = self.compare_with_operator()["operator"]["jev_text_decidable_auc"]
        self.assertEqual((auc["auc"], auc["n_answered"], auc["n_unsure"]), (1.0, 3, 1))

    def test_operator_agreement_split_by_why_chosen(self) -> None:
        split = self.compare_with_operator()["operator"]["by_why_chosen"]
        self.assertEqual((split["disputed"]["posts"], split["disputed"]["operator_answered"]), (2, 2))
        self.assertEqual((split["random"]["posts"], split["random"]["operator_answered"]), (2, 1))  # unsure excluded
        self.assertEqual(split["disputed"]["vs"]["jev"]["agreement_pct"], 100.0)
        self.assertEqual(split["random"]["vs"]["panel"]["n"], 1)

    def test_sample_sidecar_must_match_the_labels(self) -> None:
        with self.assertRaises(SystemExit):
            raters.compare("s", self.private, {}, {}, {"sample": "x", "labels": []}, ["codex"], resamples=5,
                           sample={"sample": "y", "posts": []})

    # 6e
    def test_type_majority_needs_two_votes_and_a_strict_majority(self) -> None:
        self.assertIsNone(raters.type_majority(["promotion"]))
        self.assertIsNone(raters.type_majority(["promotion", "genuine"]))
        self.assertEqual(raters.type_majority(["promotion", "promotion", "genuine"]), "promotion")


class KeyOrderTests(unittest.TestCase):
    """Re-review (57ab133..0505cb2): answers are found whatever their key order; nothing answer-like is skipped."""

    def test_reordered_answer_is_parsed_and_an_id_less_answer_is_a_problem(self) -> None:
        text = '{"opening": "x", "id": "a", "answers": {}}\n{"opening": "y", "answers": {}}\nnot json {"id": "b", oops\n```'
        parsed, problems = raters.parse_lines(text)
        self.assertEqual([p["id"] for p in parsed], ["a"])
        self.assertEqual(len(problems), 2)
