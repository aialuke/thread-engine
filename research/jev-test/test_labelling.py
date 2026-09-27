#!/usr/bin/env python3
"""Offline checks for labelling.py. No network, no real data.

    python3 -m unittest discover -s research/jev-test
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import labelling  # noqa: E402


def score(pid: str, r: int, re: int, u: int) -> dict:
    return {"id": pid, "relevant": r, "real": re, "useful": u}


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.discovery, self.private = root / "discovery", root / "private"
        self.discovery.mkdir()
        self.private.mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, folder: Path, name: str, rows: list[dict]) -> None:
        (folder / name).write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


class RuleTests(unittest.TestCase):
    def test_good_is_discoverys_useful_post_rule(self) -> None:
        self.assertTrue(labelling.good(score("a", 2, 2, 1)))
        self.assertTrue(labelling.good(score("a", 2, 2, 2)))
        self.assertFalse(labelling.good(score("a", 1, 2, 2)))
        self.assertFalse(labelling.good(score("a", 2, 1, 2)))
        self.assertFalse(labelling.good(score("a", 2, 2, 0)))
        self.assertIsNone(labelling.good(None))


class PanelTests(Base):
    def setUp(self) -> None:
        super().setUp()
        ids = [f"p{n:02d}" for n in range(30)]
        for s in labelling.SETS:
            self.write(self.discovery, f"corpus-{s}.jsonl",
                       [{"id": f"{s}-{i}", "idea": f"idea {int(i[1:]) % 3}", "text": "t </script> x"} for i in ids])
            self.write(self.discovery, f"scores-{s}.jsonl", [score(f"{s}-{i}", 2, 2, 2) for i in ids])
            # the second scorer disagrees on the first ten
            self.write(self.discovery, f"second-scores-{s}.jsonl",
                       [score(f"{s}-{i}", 0 if n < 10 else 2, 2, 2) for n, i in enumerate(ids)])

    def test_disputed_and_scorer_counts(self) -> None:
        posts = labelling.panel(self.private, self.discovery)
        self.assertEqual(len(posts), 90)
        self.assertEqual(sum(p["disputed"] for p in posts), 30)
        self.assertTrue(all(p["scorers"] == 2 for p in posts))

    def test_sample_is_deterministic_and_balanced(self) -> None:
        a = labelling.choose(labelling.panel(self.private, self.discovery), 12, 6)
        b = labelling.choose(labelling.panel(self.private, self.discovery), 12, 6)
        self.assertEqual([p["id"] for p in a], [p["id"] for p in b])
        self.assertEqual(sum(p["why_chosen"] == "disputed" for p in a), 12)
        self.assertEqual(sum(p["why_chosen"].startswith("random") for p in a), 6)
        self.assertEqual(len({p["set"] for p in a if p["why_chosen"] == "disputed"}), 3)
        self.assertTrue(all(not p["disputed"] for p in a if p["why_chosen"].startswith("random")))

    def test_page_hides_votes_and_escapes_script(self) -> None:
        sample = labelling.choose(labelling.panel(self.private, self.discovery), 6, 3)
        page = labelling.write_page(sample, self.private).read_text(encoding="utf-8")
        self.assertNotIn("t </script> x", page)
        self.assertIn("t <\\/script> x", page)
        self.assertNotIn('"votes"', page)
        self.assertNotIn("why_chosen", page)
        manifest = json.loads((self.private / f"label-sample-{labelling.sample_hash(sample)}.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["posts"]), 9)

    def test_grok_preamble_on_first_line_is_parsed(self) -> None:
        s = "stagespam-tool"
        corpus = [{"id": "a1", "idea": "i", "text": "First post text here"}, {"id": "b2", "idea": "i", "text": "Second post"}]
        self.write(self.discovery, f"corpus-{s}.jsonl", corpus)
        lines = [json.dumps({"id": c["id"], "opening": c["text"][:30], "relevant": 2, "real": 2, "useful": 1,
                             "act": True, "type": "genuine", "why": "w"}) for c in corpus]
        envelope = Path(self.tmp.name) / "out.json"
        envelope.write_text(json.dumps({"text": "I'll score each post." + lines[0] + "\n" + lines[1]}), encoding="utf-8")
        result = labelling.ingest_grok(s, envelope, self.private, self.discovery)
        self.assertEqual((result["kept"], result["problems"]), (2, []))

    def test_ingest_labels_checks_the_sample(self) -> None:
        sample = labelling.choose(labelling.panel(self.private, self.discovery), 6, 3)
        labelling.write_page(sample, self.private)
        good_file = Path(self.tmp.name) / "labels.json"
        good_file.write_text(json.dumps({"sample": labelling.sample_hash(sample),
                                         "labels": [{"id": sample[0]["id"], "label": "yes", "why": ""}]}), encoding="utf-8")
        self.assertEqual(labelling.ingest_labels(good_file, self.private)["answered"], 1)
        good_file.write_text(json.dumps({"sample": "other", "labels": []}), encoding="utf-8")
        with self.assertRaises(SystemExit):
            labelling.ingest_labels(good_file, self.private)


if __name__ == "__main__":
    unittest.main()


class NoOverwriteTests(Base):
    def test_page_and_labels_are_never_overwritten(self) -> None:
        posts = [{"id": f"p{i}", "set": "s", "idea": "i", "text": "t", "job": "worth-joining", "votes": {},
                  "why_chosen": "disputed", "replies": 3, "age_hours": 2.5} for i in range(3)]
        page = labelling.write_page(posts, self.private).read_text(encoding="utf-8")
        self.assertIn('"replies": 3', page)
        self.assertIn(labelling.QUESTIONS["worth-joining"], page)
        with self.assertRaises(SystemExit):
            labelling.write_page(posts, self.private)
        labels = Path(self.tmp.name) / "labels.json"
        labels.write_text(json.dumps({"sample": labelling.sample_hash(posts),
                                      "labels": [{"id": "p0", "label": "reply", "why": ""}]}), encoding="utf-8")
        self.assertEqual(labelling.ingest_labels(labels, self.private)["answered"], 1)
        with self.assertRaises(SystemExit):
            labelling.ingest_labels(labels, self.private)

    def test_operator_never_samples_the_final_set(self) -> None:
        with self.assertRaises(SystemExit):
            labelling.panel_typed(["stage1-B3-final"], self.private)
