#!/usr/bin/env python3
"""Offline checks for extract_subagent.py: made-up transcripts only.

    python3 -m unittest discover -s research/jev-test -p 'test_extract_subagent.py'
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import extract_subagent as ex  # noqa: E402


def line(pid: str) -> str:
    return json.dumps({"id": pid, "opening": "x", "answers": {"act": {"noul": 0.5}}})


def assistant(*parts) -> dict:
    return {"type": "assistant", "message": {"role": "assistant", "content": list(parts)}}


def handback(text: str) -> dict:
    return {"type": "tool_use", "name": ex.HANDBACK, "input": {"message": text}}


class ExtractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.corpus = {"p1": {"id": "p1", "text": "a"}, "p2": {"id": "p2", "text": "b"}}

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def transcript(self, name: str, *rows, description: str = "rater") -> Path:
        path = self.dir / "subagents" / f"agent-{name}.jsonl"
        path.parent.mkdir(exist_ok=True)
        path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        path.with_name(f"agent-{name}.meta.json").write_text(json.dumps({"description": description}), encoding="utf-8")
        return path

    def test_handback_wins_over_the_summary_text_after_it(self) -> None:
        path = self.transcript("a", assistant({"type": "text", "text": line("p9")}),
                               assistant(handback(line("p1") + "\n" + line("p2"))),
                               {"type": "user", "message": {"content": "ok"}},
                               assistant({"type": "text", "text": "All rated; I wrote no files."}))
        out = ex.extract([path], self.corpus, self.dir / "out.jsonl")
        self.assertEqual((out["lines"], out["of"]), (2, 2))
        self.assertEqual([json.loads(x)["id"] for x in (self.dir / "out.jsonl").read_text().splitlines()], ["p1", "p2"])

    def test_last_text_is_used_when_there_is_no_handback(self) -> None:
        path = self.transcript("b", assistant({"type": "text", "text": "thinking aloud"}),
                               assistant({"type": "text", "text": "Here:\n" + line("p1") + "\n" + line("p2")}))
        self.assertEqual(ex.final_reply(path).count('"id"'), 2)

    def test_fails_closed_on_missing_duplicate_or_foreign_ids_and_never_overwrites(self) -> None:
        one = self.transcript("c", assistant(handback(line("p1"))))
        two = self.transcript("d", assistant(handback(line("p1") + "\n" + line("p7"))))
        out = self.dir / "out.jsonl"
        with self.assertRaisesRegex(SystemExit, "p2: missing"):
            ex.extract([one], self.corpus, out)
        with self.assertRaisesRegex(SystemExit, "p1: answered 2 times"):
            ex.extract([one, two], self.corpus, out)
        with self.assertRaisesRegex(SystemExit, "p7: not in the corpus"):
            ex.extract([two], self.corpus, out)
        self.assertFalse(out.exists())
        out.write_text("keep")
        with self.assertRaisesRegex(SystemExit, "already exists"):
            ex.extract([one], self.corpus, out)
        self.assertEqual(out.read_text(), "keep")

    def test_session_picks_subagents_by_description(self) -> None:
        self.transcript("e", assistant(handback(line("p1"))), description="Claude rater stage2-B4-validation b1")
        self.transcript("f", assistant(handback(line("p2"))), description="Claude rater stage2-B4-validation b2")
        self.transcript("g", assistant(handback(line("p2"))), description="Claude rater stage3-B4-validation b1")
        picked = ex.session_transcripts(str(self.dir), "stage2-B4-validation")
        self.assertEqual([p.name for p in picked], ["agent-e.jsonl", "agent-f.jsonl"])
        with self.assertRaisesRegex(SystemExit, "no subagent"):
            ex.session_transcripts(str(self.dir), "stage9")


if __name__ == "__main__":
    unittest.main()
