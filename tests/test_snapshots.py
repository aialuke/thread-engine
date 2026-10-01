#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from loop_core.errors import LoopError  # noqa: E402
from loop_core.snapshots import Admission, admit_snapshot  # noqa: E402

FINAL_H = 27 * 24


def post(*kinds: str, missed: bool = False) -> dict:
    return {"snapshots": [{"kind": k} for k in kinds], "missed": missed}


class Admit(unittest.TestCase):
    def refused(self, message: str, *args) -> None:
        with self.assertRaises(LoopError) as caught:
            admit_snapshot(*args)
        self.assertEqual(str(caught.exception), message)

    def test_the_kind_follows_the_age(self) -> None:
        got = [admit_snapshot(post(), h, False) for h in (0, 35.99, 36, 60, 60.01)]
        self.assertEqual([a.kind for a in got], ["early", "early", "valid", "valid", "late"])
        self.assertEqual({a.skip for a in got}, {None})

    def test_a_read_before_the_post_is_refused(self) -> None:
        self.refused("observed before the post existed", post(), -0.01, False)

    def test_a_final_read_takes_the_final_kind_inside_the_window(self) -> None:
        self.assertEqual(admit_snapshot(post("valid"), FINAL_H, True), Admission("final", None))

    def test_a_final_read_outside_the_window_is_refused_before_its_duplicate_is_skipped(self) -> None:
        self.refused("a final read needs a post 26 to 29 days old", post("final"), 10, True)

    def test_a_second_final_read_is_skipped(self) -> None:
        self.assertEqual(admit_snapshot(post("final"), FINAL_H, True), Admission(None, "final read already exists"))

    def test_a_second_valid_read_is_skipped(self) -> None:
        self.assertEqual(admit_snapshot(post("valid"), 48, False), Admission(None, "valid snapshot already exists"))

    def test_a_duplicate_valid_read_is_skipped_before_the_missed_refusal(self) -> None:
        self.assertEqual(admit_snapshot(post("valid", missed=True), 48, False),
                         Admission(None, "valid snapshot already exists"))

    def test_a_valid_read_of_a_missed_post_is_refused(self) -> None:
        self.refused("post already marked missed", post(missed=True), 48, False)

    def test_other_reads_of_a_missed_post_are_admitted(self) -> None:
        got = [admit_snapshot(post(missed=True), h, f).kind for h, f in ((10, False), (70, False), (FINAL_H, True))]
        self.assertEqual(got, ["early", "late", "final"])

    def test_repeated_early_reads_are_admitted(self) -> None:
        self.assertEqual(admit_snapshot(post("early", "early"), 10, False), Admission("early", None))

    def test_a_late_snapshot_does_not_count_as_a_valid_duplicate(self) -> None:
        self.assertEqual(admit_snapshot(post("late"), 48, False), Admission("valid", None))

    def test_a_second_late_read_is_admitted(self) -> None:
        self.assertEqual(admit_snapshot(post("late"), 70, False), Admission("late", None))


if __name__ == "__main__":
    unittest.main()
