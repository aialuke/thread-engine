#!/usr/bin/env python3
"""Checks for scripts/loop_core/payloads.py: called directly, no repo, no CLI."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from loop_core import payloads  # noqa: E402
from loop_core.errors import LoopError  # noqa: E402

T0 = "2026-10-01T00:00:00Z"


def post(**change) -> dict:
    base = {"root_id": "1000000001", "slug": "s", "format": "single-tip", "lane": "main", "posted_at": T0,
            "retrospective": False, "made_in_repo": True}
    return {**base, **change}


def item(**change) -> dict:
    return {**{"id": "1000000005", "kind": "original", "created_at": T0, "conversation_id": "1000000005"}, **change}


class Refused(unittest.TestCase):
    def assertRefused(self, call, message: str) -> None:
        with self.assertRaises(LoopError) as caught:
            call()
        self.assertEqual(str(caught.exception), message)


class ValidatePost(Refused):
    def test_a_good_post_passes(self) -> None:
        payloads.validate_post(post())
        payloads.validate_post(post(arm="treatment", cards=[{"id": "1000000009", "text": "hi"}],
                                    edits=[{"class": "preference"}], production_minutes=0))

    def test_each_rule(self) -> None:
        cases = [
            (post(root_id="123"), "root_id missing or bad"),
            (post(slug=""), "slug required"),
            (post(format="meme"), None),
            (post(lane="z"), "lane must be main or other"),
            (post(retrospective=None), "retrospective must be true or false"),
            (post(made_in_repo="yes"), "made_in_repo must be true or false"),
            (post(cards={}), "cards must be a list"),
            (post(cards=[{"id": "1"}]), "card id bad"),
            (post(edits=[{"class": "z"}]), None),
            (post(production_minutes=1.5), "production_minutes must be a non-negative integer or null"),
            (post(nonorganic="paid"), "nonorganic must be null or {reason, at}"),
            (post(nonorganic={"reason": 3}), "nonorganic must be null or {reason, at}"),
        ]
        for data, message in cases:
            with self.subTest(data=data):
                with self.assertRaises(LoopError) as caught:
                    payloads.validate_post(data)
                if message:
                    self.assertEqual(str(caught.exception), message)

    def test_stored_snapshots_are_checked_too(self) -> None:
        self.assertRefused(lambda: payloads.validate_post(post(snapshots=[{"observed_at": T0, "kind": "x"}])),
                           "snapshot kind bad")

    def test_time_errors_are_loop_errors(self) -> None:
        self.assertRefused(lambda: payloads.validate_post(post(posted_at="2026-10-01T00:00:00")),
                           "time '2026-10-01T00:00:00' has no timezone")


class ValidateSnapshot(Refused):
    def snap(self, **change) -> dict:
        return {**{"observed_at": T0, "kind": "valid", "root": {"views": 1}, "organic": {"likes": 0}}, **change}

    def test_a_good_snapshot_passes(self) -> None:
        payloads.validate_snapshot(self.snap())
        payloads.validate_snapshot(self.snap(organic=None, followers=None, cards=[{"views": 3}]))

    def test_each_rule(self) -> None:
        self.assertRefused(lambda: payloads.validate_snapshot(self.snap(kind="x")), "snapshot kind bad")
        self.assertRefused(lambda: payloads.validate_snapshot(self.snap(root={"likes": -1})),
                           "root.likes must be a non-negative integer or null")
        self.assertRefused(lambda: payloads.validate_snapshot(self.snap(organic={"bogus": 1})),
                           "unknown organic measure 'bogus'")
        self.assertRefused(lambda: payloads.validate_snapshot(self.snap(followers=True)),
                           "followers must be a non-negative integer or null")
        self.assertRefused(lambda: payloads.validate_snapshot(self.snap(cards=[{"views": "3"}])),
                           "card views must be a non-negative integer or null")


class ValidateItem(Refused):
    def test_a_good_item_passes(self) -> None:
        payloads.validate_item(item())
        payloads.validate_item(item(public={"likes": 1}, organic={"url_clicks": 2}))

    def test_each_rule(self) -> None:
        self.assertRefused(lambda: payloads.validate_item(item(id="x")), "item id missing or bad")
        self.assertRefused(lambda: payloads.validate_item(item(kind="z")),
                           "item kind must be one of ['original', 'quote', 'reply', 'repost', 'thread_card']")
        self.assertRefused(lambda: payloads.validate_item(item(conversation_id="")), "item conversation_id bad")
        self.assertRefused(lambda: payloads.validate_item(item(public={"url_clicks": 1})),
                           "unknown public measure 'url_clicks'")
        self.assertRefused(lambda: payloads.validate_item(item(organic={"bookmarks": 1})),
                           "unknown organic measure 'bookmarks'")


class CheckCount(Refused):
    def test_counts(self) -> None:
        for good in (None, 0, 7):
            payloads.check_count(good, "n")
        for bad in (-1, 1.0, "3", True, False):
            with self.subTest(bad=bad):
                self.assertRefused(lambda: payloads.check_count(bad, "n"), "n must be a non-negative integer or null")


if __name__ == "__main__":
    unittest.main()
