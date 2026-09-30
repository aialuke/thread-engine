#!/usr/bin/env python3
"""Checks for scripts/loop_core/health.py, the daily-run warnings, and reads.final_at_risk. Stdlib only."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from loop_core import health, reads  # noqa: E402

NOW = datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc)


def ok_line(at: datetime) -> str:
    return f"{at.strftime('%Y-%m-%dT%H:%M:%SZ')} snapshot ok read48=1 final=0 followers=38 api_items=39 cost_usd=0.039"


def failed_line(at: datetime, detail: str = "error='credits'") -> str:
    return f"{at.strftime('%Y-%m-%dT%H:%M:%SZ')} snapshot failed {detail}"


def ago(hours: float) -> datetime:
    return NOW - timedelta(hours=hours)


class FinalAtRisk(unittest.TestCase):
    def test_window_is_the_last_48_hours_before_the_cutoff(self) -> None:
        got = [reads.final_at_risk(h) for h in (647.9, 648, 696, 696.1)]
        self.assertEqual(got, [False, True, True, False])

    def test_it_is_inside_the_final_window(self) -> None:
        self.assertTrue(all(reads.in_final_window(h) for h in (reads.FINAL_WARN_H, reads.FINAL_MAX_DAYS * 24)))


class LastRuns(unittest.TestCase):
    def test_empty_and_missing_logs_have_no_runs(self) -> None:
        self.assertEqual(health.last_runs([]), {"last_ok": None, "last": None})
        self.assertEqual(health.last_runs(["", "garbage", "not-a-time snapshot ok"]), {"last_ok": None, "last": None})

    def test_last_ok_is_the_latest_ok_and_last_is_the_final_line(self) -> None:
        runs = health.last_runs([ok_line(ago(60)), ok_line(ago(30)), failed_line(ago(6))])
        self.assertEqual(runs["last_ok"], ago(30))
        self.assertEqual(runs["last"], {"outcome": "failed", "at": ago(6), "detail": "error='credits'"})

    def test_an_ingest_line_is_not_a_daily_run(self) -> None:
        line = f"{ago(1).strftime('%Y-%m-%dT%H:%M:%SZ')} snapshot ingest ledger/raw/api/x.json items=9"
        self.assertEqual(health.last_runs([ok_line(ago(40)), line]),
                         {"last_ok": ago(40), "last": {"outcome": "ok", "at": ago(40), "detail": ""}})


class Warnings(unittest.TestCase):
    def warn(self, lines: list[str], finals=()) -> list[str]:
        return health.warnings(NOW, health.last_runs(lines), list(finals))

    def test_a_fresh_ok_run_is_quiet(self) -> None:
        self.assertEqual(self.warn([ok_line(ago(25))]), [])

    def test_the_stale_line_is_at_26_hours_exactly(self) -> None:
        self.assertEqual(self.warn([ok_line(ago(26))]), [])
        stale = self.warn([ok_line(ago(26.1))])
        self.assertEqual(len(stale), 1)
        self.assertIn("26 hours ago", stale[0])

    def test_no_run_at_all_is_a_warning(self) -> None:
        self.assertIn("No daily run", self.warn([])[0])

    def test_a_failed_last_line_is_reported_with_its_error(self) -> None:
        got = self.warn([ok_line(ago(20)), failed_line(ago(2), "error='Keychain locked'")])
        self.assertEqual(len(got), 1)
        self.assertIn("X read failed", got[0])
        self.assertIn("Keychain locked", got[0])

    def test_a_recording_failure_names_its_stage(self) -> None:
        got = self.warn([ok_line(ago(20)), failed_line(ago(2), "stage=record error='boom'")])
        self.assertIn("record", got[0])
        self.assertIn("partly written", got[0])

    def test_failed_then_ok_is_quiet(self) -> None:
        self.assertEqual(self.warn([failed_line(ago(30)), ok_line(ago(6))]), [])

    def test_stale_and_failed_are_both_said(self) -> None:
        self.assertEqual(len(self.warn([ok_line(ago(40)), failed_line(ago(2))])), 2)

    def test_a_final_read_at_risk_names_the_post_and_its_cutoff(self) -> None:
        deadline = datetime(2026, 10, 18, 10, 0, tzinfo=timezone.utc)
        got = self.warn([ok_line(ago(5))], [("2100000000000000001", deadline)])
        self.assertEqual(len(got), 1)
        self.assertIn("2100000000000000001", got[0])
        self.assertIn("18 Oct 20:00", got[0])  # Brisbane is UTC+10

    def test_warnings_come_out_in_the_order_stale_failed_finals(self) -> None:
        got = self.warn([ok_line(ago(40)), failed_line(ago(2))], [("1", NOW)])
        self.assertEqual([("hours ago" in g, "failed" in g, "final read" in g) for g in got],
                         [(True, False, False), (False, True, False), (False, False, True)])


if __name__ == "__main__":
    unittest.main()
