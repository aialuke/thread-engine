#!/usr/bin/env python3
"""Offline checks for arms.py on a made-up block (B9). No network.

    python3 -m unittest discover -s research/jev-test -p 'test_arms.py'
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import arms  # noqa: E402

RATERS = ("jev", "codex", "claude", "grok")


def ans(good: bool, typ: str = "genuine", outside: float = 0.1, reply: float = 0.9, dec: float = 0.9) -> dict:
    lvl = {"0": 0.05, "1": 0.05, "2": 0.9} if good else {"0": 0.9, "1": 0.05, "2": 0.05}
    return {"relevant": {"probabilities": lvl}, "real": {"probabilities": lvl}, "useful": {"probabilities": lvl},
            "type": {"probabilities": {typ: 1.0}, "choice": typ}, "act": {"noul": 0.5},
            "answers_other": {"noul": 0.1}, "outside_domain": {"noul": outside},
            "reply_worthy": {"noul": reply}, "text_decidable": {"noul": dec}}


# post: stage, half, idea card, age, sightings [(source, variant)], text has a link, answers for every rater
POSTS = {
    "a1": (1, "validation", "wj-comedy-1", 0.5, [("K-recency", "v1")], False, ans(True)),
    "a2": (1, "validation", "wj-comedy-1", 3.0, [("K-recency", "v2")], False, ans(False, "off-topic", outside=0.9)),
    "a3": (1, "final", "wj-comedy-1b", 1.5, [("K-recency", "v1")], False, ans(True)),
    "a4": (1, "final", "wj-tech-1", 0.8, [("K-recency", "v1")], False, ans(True)),
    "b1": (2, "validation", "demand-tech-1", None, [("K-recency", "v1"), ("Knl-recency", "v1-no-links")], False, ans(True)),
    "b2": (2, "validation", "demand-tech-1", None, [("K-recency", "v1")], True, ans(True)),
    "b3": (2, "final", "demand-tech-1", None, [("Knl-recency", "v1-no-links")], False, ans(False, "promotion", reply=0.1)),
    "b4": (2, "final", "demand-tech-1", None, [("K-recency", "v2")], False, ans(True)),
    "c1": (3, "validation", "tr-tech-1", None, [("K-recency", "v1")], False, ans(True)),
    "c2": (3, "final", "tr-tech-1", None, [("Kspam-recency", "spam")], False, ans(False)),
}


class ArmsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.private, self.discovery = base / "private", base / "discovery"
        (self.private / "splits").mkdir(parents=True)
        (self.private / "raters").mkdir()
        self.discovery.mkdir()
        manifest = ["post_id,stage,idea,source,sort,variant,rank,call,result_count,eligible"]
        texts = ["post_id,text"]
        sets: dict[str, list] = {}
        for n, (pid, (stage, half, idea, age, sights, link, a)) in enumerate(POSTS.items()):
            post_id = str(1000 + n)
            for source, variant in sights:
                manifest.append(f"{post_id},stage{stage},{idea},{source},recency,{variant},0,x{source[:3]}{stage},10,True")
            texts.append(f"{post_id},SECRETTEXT {pid}{' https://t.co/abc' if link else ''}")
            sets.setdefault(f"stage{stage}-B9-{half}", []).append((pid, post_id, idea, age, a))
        (self.discovery / "manifest-B9.csv").write_text("\n".join(manifest) + "\n", encoding="utf-8")
        (self.discovery / "posts.csv").write_text("\n".join(texts) + "\n", encoding="utf-8")
        (self.discovery / "requests.jsonl").write_text(
            "".join(json.dumps({"call_id": c, "estimated_cost": 0.05}) + "\n"
                    for c in ("xK-r2", "xKnl2", "xK-r3", "xKsp3")), encoding="utf-8")
        keys: dict[int, dict] = {1: {}, 2: {}, 3: {}}
        for name, rows in sets.items():
            stage = int(name[5])
            corpus = [{"id": pid, "idea": idea, "text": f"SECRETTEXT {pid}", **({"age_hours": age} if age is not None else {})}
                      for pid, _, idea, age, _ in rows]
            (self.private / "splits" / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in corpus))
            for pid, post_id, idea, _, _ in rows:
                keys[stage][pid] = {"post_id": post_id, "conversation_id": f"c{post_id}", "idea_key": idea}
            self.write_raters(name, {pid: a for pid, _, _, _, a in rows})
        for stage, key in keys.items():
            (self.discovery / f"corpus-key-stage{stage}-B9.json").write_text(json.dumps(key))
        (self.discovery / "corpus-stage1-B9.jsonl").write_text(
            "".join(json.dumps({"id": p, "age_hours": POSTS[p][3]}) + "\n" for p in ("a1", "a2", "a3", "a4")))
        # arm 3: b1 and b2 again with their parents; Claude changes its mind on b2, text_decidable rises
        (self.private / "splits" / "stage2-B9-validation-parent.jsonl").write_text(
            "".join(json.dumps({"id": p, "idea": "i", "text": "SECRETTEXT", "parent": "SECRETPARENT"}) + "\n" for p in ("b1", "b2")))
        with_parent = {"b1": ans(True, dec=0.95), "b2": ans(True, dec=0.95)}
        self.write_raters("stage2-B9-validation-parent", with_parent, claude={"b2": ans(False, dec=0.95)})
        self.thresholds = base / "thresholds.json"
        self.thresholds.write_text(json.dumps({"frozen": True, "frozen_coverage_threshold": 0.8,
                                               "frozen_coverage_rule": "p_good_0.5"}))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_raters(self, name: str, answers: dict, **override) -> None:
        for r in RATERS:
            rows = {**answers, **override.get(r, {})}
            path = self.private / (f"answers-{name}.jsonl" if r == "jev" else f"raters/{r}-{name}.jsonl")
            path.write_text("".join(json.dumps({"id": p, "answers": a}) + "\n" for p, a in rows.items()))

    def run_arms(self) -> dict:
        return arms.run("B9", self.private, self.discovery, thresholds_path=self.thresholds)

    def test_every_arm_on_known_answers(self) -> None:
        report = self.run_arms()
        self.assertEqual(report["posts"], 10)
        a1 = report["arm1_no_links"]["summary"]
        self.assertEqual((a1["all:plain"]["pooled"]["posts"], a1["all:plain"]["pooled"]["good"]), (4, 4))
        self.assertEqual((a1["all:no_links"]["pooled"]["posts"], a1["all:no_links"]["pooled"]["good"]), (2, 1))
        self.assertEqual(a1["all:overlap"], {"good_plain": 4, "good_no_links": 1, "good_both": 1,
                                             "good_lost_by_no_links_pct": 75.0})
        plain_v1 = next(c for c in report["arm1_no_links"]["cells"]
                        if (c["idea"], c["variant"], c["arm"]) == ("demand-tech-1", "v1", "plain"))
        self.assertEqual((plain_v1["good_with_link"], plain_v1["good_only_plain_found"]), (1, 1))
        a2 = report["arm2_worth_joining_age"]
        self.assertEqual((a2["posts"], a2["good"]), (3, 2))
        self.assertEqual(a2["cuts"]["<=1h"], {"keeps_good_pct": 100.0, "drops_posts_pct": 33.3, "good_pct_kept": 100.0})
        a4 = report["arm4_cards"]
        self.assertEqual((a4["wj-comedy-1"]["outside_domain_pct"], a4["wj-comedy-1b"]["outside_domain_pct"]), (50.0, 0.0))
        self.assertEqual(a4["wj-comedy-1b"]["good_only_this_card"], 1)
        a3 = report["arm3_parent"]
        self.assertEqual((a3["replies"], a3["good_flips"]["claude"], a3["good_flips"]["codex"]), (2, 1, 0))
        self.assertEqual((a3["without_parent"]["panel_disputed_pct"], a3["with_parent"]["panel_disputed_pct"]), (0.0, 50.0))
        a5 = report["arm5_rules"]["all"]
        # c2 is genuine, in domain and reply-worthy but not good by the current rule: the rules disagree on it only
        self.assertEqual(a5["rules_disagree"]["posts"], 1)
        self.assertEqual(a5["rules_disagree"]["good_only_under_three_question"], 1)
        self.assertEqual(a5["current"]["panel_good_pct"], 70.0)
        self.assertIn("flag", report["arm5_rules"]["tool-research"])
        self.assertEqual(report["side_frozen_cutoff"]["all"]["agreement_pct"], 100.0)

    def test_a_post_found_in_two_stages_keeps_each_stages_ratings(self) -> None:
        # b4 (Demand, good) and c2 (Tool research, not good) become the same X post, seen by both stages
        b4 = next(i for i, p in enumerate(POSTS) if p == "b4")
        c2 = next(i for i, p in enumerate(POSTS) if p == "c2")
        key3 = json.loads((self.discovery / "corpus-key-stage3-B9.json").read_text())
        key3["c2"]["post_id"] = str(1000 + b4)
        (self.discovery / "corpus-key-stage3-B9.json").write_text(json.dumps(key3))
        manifest = (self.discovery / "manifest-B9.csv").read_text().replace(f"{1000 + c2},stage3", f"{1000 + b4},stage3")
        (self.discovery / "manifest-B9.csv").write_text(manifest)
        report = self.run_arms()
        summary = report["arm1_no_links"]["summary"]
        self.assertEqual((summary["demand:plain"]["pooled"]["posts"], summary["demand:plain"]["pooled"]["good"]), (3, 3))
        spam = summary["tool-research:spam_reference"]["pooled"]
        self.assertEqual((spam["posts"], spam["good"]), (1, 0))

    def test_output_holds_no_post_text_or_post_ids(self) -> None:
        self.run_arms()
        written = (self.private / "arms-B9.json").read_text()
        self.assertNotIn("SECRET", written)
        self.assertNotIn("1000", written)

    def test_a_missing_or_short_rater_file_stops_everything(self) -> None:
        (self.private / "raters" / "grok-stage3-B9-final.jsonl").unlink()
        with self.assertRaisesRegex(arms.Stop, "grok-stage3-B9-final.jsonl is missing"):
            self.run_arms()
        self.write_raters("stage3-B9-final", {"c2": ans(False)})
        (self.private / "raters" / "codex-stage3-B9-final.jsonl").write_text("")
        with self.assertRaisesRegex(arms.Stop, "covers 0 of 1"):
            self.run_arms()
        self.assertFalse((self.private / "arms-B9.json").exists())

    def test_three_question_rule_reads_type_domain_and_reply(self) -> None:
        self.assertTrue(arms.three_q(ans(False)))
        self.assertFalse(arms.three_q(ans(True, "promotion")))
        self.assertFalse(arms.three_q(ans(True, outside=0.6)))
        self.assertFalse(arms.three_q(ans(True, reply=0.4)))
        self.assertIsNone(arms.three_q({}))


if __name__ == "__main__":
    unittest.main()
