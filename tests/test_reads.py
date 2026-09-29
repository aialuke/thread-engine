#!/usr/bin/env python3
"""Checks for scripts/loop_core/reads.py, the Read-window rules. Stdlib only."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from loop_core import reads  # noqa: E402

NOW = datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc)


class Stages(unittest.TestCase):
    def test_snapshot_kind_edges(self) -> None:
        got = [reads.snapshot_kind(h) for h in (0, 35.99, 36, 60, 60.01)]
        self.assertEqual(got, ["early", "early", "valid", "valid", "late"])

    def test_due_stage_edges_and_retrospective(self) -> None:
        stages = [reads.due_stage(h, False) for h in (35.99, 36, 60, 60.01)]
        self.assertEqual(stages, ["pending", "due", "due", "missed"])
        self.assertEqual([reads.due_stage(h, True) for h in (35.99, 60, 60.01)], ["pending", "due", None])

    def test_past_window_and_final_ready(self) -> None:
        self.assertEqual([reads.past_window(h) for h in (60, 60.01)], [False, True])
        self.assertEqual([reads.final_ready(h) for h in (24 * 26 - 0.01, 24 * 26, 24 * 90)], [False, True, True])

    def test_best_snapshot_prefers_first_valid_else_last_late(self) -> None:
        late = [{"kind": "late", "n": 1}, {"kind": "late", "n": 2}, {"kind": "early", "n": 3}]
        self.assertEqual(reads.best_snapshot({"snapshots": late})["n"], 2)
        valid = [*late, {"kind": "valid", "n": 4}, {"kind": "valid", "n": 5}]
        self.assertEqual(reads.best_snapshot({"snapshots": valid})["n"], 4)
        self.assertEqual(reads.valid_snapshot({"snapshots": valid})["n"], 4)
        self.assertIsNone(reads.best_snapshot({"snapshots": [{"kind": "early"}, {"kind": "final"}]}))
        self.assertIsNone(reads.valid_snapshot({}))


class Windows(unittest.TestCase):
    def test_first_run_starts_at_the_window_and_the_horizon(self) -> None:
        first, final = reads.read_windows(NOW, {}, 30)
        self.assertEqual((first["stage"], first["start"], first["end"], first["fetch"]),
                         ("48h", NOW - timedelta(hours=60), NOW - timedelta(hours=36), True))
        self.assertEqual(first["cursor"], {"read48_until": NOW - timedelta(hours=36)})
        self.assertEqual((final["stage"], final["start"], final["end"]),
                         ("final", NOW - timedelta(days=30), NOW - timedelta(days=26)))
        self.assertEqual(final["cursor"], {"final_until": NOW - timedelta(days=26)})

    def test_cursors_resume_but_never_pass_the_horizon(self) -> None:
        saved = {"read48_until": NOW - timedelta(hours=40), "final_until": NOW - timedelta(days=28)}
        first, final = reads.read_windows(NOW, saved, 30)
        self.assertEqual((first["start"], final["start"]), (NOW - timedelta(hours=40), NOW - timedelta(days=28)))
        old = {"read48_until": NOW - timedelta(days=50), "final_until": NOW - timedelta(days=50)}
        first, final = reads.read_windows(NOW, old, 30)
        self.assertEqual((first["start"], final["start"]), (NOW - timedelta(days=30),) * 2)

    def test_empty_48h_window_is_kept_and_empty_final_is_dropped(self) -> None:
        saved = {"read48_until": NOW - timedelta(hours=36), "final_until": NOW - timedelta(days=26)}
        windows = reads.read_windows(NOW, saved, 30)
        self.assertEqual([(w["stage"], w["fetch"]) for w in windows], [("48h", False)])

    def test_backfill_cursor(self) -> None:
        since = NOW - timedelta(days=5)
        self.assertEqual(reads.backfill_cursor(NOW, since),
                         {"read48_until": NOW - timedelta(hours=36), "final_until": since})


if __name__ == "__main__":
    unittest.main()
