#!/usr/bin/env python3
"""Checks for scripts/loop_core/payloads.py: called directly, no repo, no CLI."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from loop_core import payloads  # noqa: E402
from loop_core.errors import LoopError  # noqa: E402

T0 = "2026-10-01T00:00:00Z"
OBSERVED = datetime(2026, 10, 3, tzinfo=timezone.utc)


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


class PostFromPayload(Refused):
    def test_defaults_are_filled_in(self) -> None:
        got = payloads.post_from_payload({"root_id": 1000000001, "slug": "s", "format": "other", "lane": "other",
                                          "posted_at": T0})
        self.assertEqual(got, {
            "root_id": "1000000001", "slug": "s", "format": "other", "lane": "other", "posted_at": T0,
            "retrospective": False, "made_in_repo": True, "experiment": None, "arm": "none", "hypothesis": None,
            "cards": [], "media": [], "ai_media": False, "production_minutes": None, "edits": [], "draft": None,
            "snapshots": [], "missed": False, "auto": False})

    def test_auto_is_coerced_and_snapshots_are_never_taken_from_the_payload(self) -> None:
        got = payloads.post_from_payload({**post(), "auto": 1, "snapshots": [{"kind": "x"}], "missed": True})
        self.assertEqual((got["auto"], got["snapshots"], got["missed"]), (True, [], False))

    def test_an_invalid_post_is_refused(self) -> None:
        self.assertRefused(lambda: payloads.post_from_payload({**post(), "lane": "z"}), "lane must be main or other")


class SnapshotFromPayload(Refused):
    def build(self, payload: dict, kind: str = "valid", handles=("me",)) -> dict:
        return payloads.snapshot_from_payload({"observed_at": T0, **payload}, OBSERVED, 48.04, kind, list(handles))

    def test_repliers_are_counted_outside_the_accounts_own_handles(self) -> None:
        snap = self.build({"repliers": ["Me", "@Other", "other", "third"]})
        self.assertEqual((snap["outside_replies"], snap["outside_repliers"]), (3, ["other", "third"]))

    def test_without_repliers_the_count_is_taken_as_given_and_no_names_are_stored(self) -> None:
        snap = self.build({"outside_replies": 4})
        self.assertEqual((snap["outside_replies"], snap["outside_repliers"]), (4, []))
        self.assertRefused(lambda: self.build({"outside_replies": -1}),
                           "outside_replies must be a non-negative integer or null")

    def test_shape_and_defaults(self) -> None:
        snap = self.build({"root": {"views": 5, "likes": 1}})
        self.assertEqual(snap["observed_at"], "2026-10-03T00:00:00Z")
        self.assertEqual((snap["age_hours"], snap["kind"], snap["source"]), (48.0, "valid", "grok"))
        self.assertEqual(snap["missing"], ["reposts", "quotes", "replies", "bookmarks"])
        self.assertNotIn("organic", snap)

    def test_organic_keeps_only_known_measures(self) -> None:
        snap = self.build({"organic": {"likes": 2, "bogus": 9}})
        self.assertEqual(snap["organic"], {"impressions": None, "likes": 2, "replies": None, "reposts": None,
                                           "profile_visits": None, "url_clicks": None})

    def test_the_built_snapshot_is_validated(self) -> None:
        self.assertRefused(lambda: self.build({"root": {"views": -1}}),
                           "root.views must be a non-negative integer or null")


class ActivityHeader(Refused):
    def test_stage_and_time(self) -> None:
        self.assertEqual(payloads.activity_header({"stage": "48h", "observed_at": T0}),
                         ("48h", datetime(2026, 10, 1, tzinfo=timezone.utc)))

    def test_refusals(self) -> None:
        self.assertRefused(lambda: payloads.activity_header({"stage": "x", "observed_at": T0}),
                           "stage must be one of ['48h', 'backfill', 'final']")
        self.assertRefused(lambda: payloads.activity_header({"stage": "final"}),
                           "bad time ''; use ISO 8601 with a timezone")


class CursorUpdates(Refused):
    def test_only_named_and_non_empty_cursors_move(self) -> None:
        got = payloads.cursor_updates({"cursor": {"read48_until": "2026-10-01T10:00:00+10:00", "final_until": "",
                                                  "other": "2026-10-01T00:00:00Z"}})
        self.assertEqual(got, {"read48_until": "2026-10-01T00:00:00Z"})

    def test_none_given(self) -> None:
        self.assertEqual(payloads.cursor_updates({}), {})
        self.assertEqual(payloads.cursor_updates({"cursor": None}), {})

    def test_a_bad_cursor_is_refused(self) -> None:
        self.assertRefused(lambda: payloads.cursor_updates({"cursor": {"final_until": "zz"}}),
                           "bad time 'zz'; use ISO 8601 with a timezone")


if __name__ == "__main__":
    unittest.main()
