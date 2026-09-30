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
        for bad in (None, 1, "x", [1], [{}]):
            self.assertRefused(lambda: payloads.validate_item(item(topics=bad)), "item topics must be a list of text")
        payloads.validate_item(item(topics=["a", "b"]))


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


class InteractionInputs(Refused):
    MENTION = {"author_id": "9", "id": "m1", "conversation_id": 100, "created_at": T0}

    def test_mentions_and_targets_are_normalised(self) -> None:
        observed, mentions, targets, since = payloads.interaction_inputs({
            "observed_at": T0, "self_ids": [1],
            "mentions": [self.MENTION, {**self.MENTION, "id": "m2", "replied_to": 55}],
            "reply_targets": [{"user_id": 7, "item_id": 200, "at": T0}], "since_id": "abc"})
        self.assertEqual(observed, datetime(2026, 10, 1, tzinfo=timezone.utc))
        self.assertEqual(list(mentions), [("9", "100", "m1", T0, "100"), ("9", "100", "m2", T0, "55")])
        self.assertEqual(list(targets), [("7", "200", T0)])
        self.assertEqual(since, "abc")

    def test_own_authorless_and_targetless_entries_are_dropped_unread(self) -> None:
        _, mentions, targets, since = payloads.interaction_inputs({
            "observed_at": T0, "self_ids": ["9"],
            "mentions": [{"author_id": 9}, {"id": "x"}], "reply_targets": [{"user_id": 9}, {}]})
        self.assertEqual((list(mentions), list(targets), since), ([], [], None))

    def test_a_missing_field_is_a_refusal(self) -> None:
        _, mentions, _, _ = payloads.interaction_inputs({"observed_at": T0,
                                                         "mentions": [{"author_id": "9", "id": "m"}]})
        self.assertRefused(lambda: list(mentions), "record-interactions: payload is missing 'conversation_id'")

    def test_a_bad_time_is_refused_where_the_entry_is_reached(self) -> None:
        good = {"author_id": "9", "id": "m", "conversation_id": 1, "created_at": T0}
        for bad in ("zz", None, 5):
            _, mentions, targets, _ = payloads.interaction_inputs({
                "observed_at": T0, "mentions": [{**good, "created_at": bad}],
                "reply_targets": [{"user_id": "7", "item_id": 2, "at": bad}]})
            with self.subTest(bad=bad):
                with self.assertRaises(LoopError):
                    list(mentions)
                with self.assertRaises(LoopError):
                    list(targets)

    def test_entries_are_read_only_as_they_are_asked_for(self) -> None:
        good = {"author_id": "9", "id": "m", "conversation_id": 1, "created_at": T0}
        _, mentions, _, _ = payloads.interaction_inputs({"observed_at": T0, "mentions": [good, {"author_id": "8"}]})
        self.assertEqual(next(mentions)[:3], ("9", "1", "m"))  # the bad second entry has not been read yet
        with self.assertRaises(LoopError):
            next(mentions)

    def test_observed_at_is_required(self) -> None:
        self.assertRefused(lambda: payloads.interaction_inputs({}), "bad time ''; use ISO 8601 with a timezone")


class FollowerInputs(Refused):
    def test_ids_are_text_sorted_and_without_our_own(self) -> None:
        observed, ids = payloads.follower_inputs({"observed_at": T0, "self_ids": [2], "ids": [3, 1, 2, 3]})
        self.assertEqual((observed, ids), (datetime(2026, 10, 1, tzinfo=timezone.utc), ["1", "3"]))

    def test_ids_are_required_and_must_be_a_list(self) -> None:
        self.assertRefused(lambda: payloads.follower_inputs({"observed_at": T0}),
                           "record-followers: ids required (a missing list would record zero followers)")
        self.assertEqual(payloads.follower_inputs({"observed_at": T0, "ids": []})[1], [])
        for bad in (None, {}, "12345", 7):
            self.assertRefused(lambda: payloads.follower_inputs({"observed_at": T0, "ids": bad}),
                               "record-followers: ids must be a list")

    def test_total_defaults_to_the_id_count(self) -> None:
        self.assertEqual(payloads.follower_total({}, ["1", "2"]), 2)
        self.assertEqual(payloads.follower_total({"total": 500}, ["1"]), 500)

    def test_verified(self) -> None:
        self.assertIsNone(payloads.verified_count({}))
        self.assertIsNone(payloads.verified_count({"verified": None}))
        self.assertEqual(payloads.verified_count({"verified": 0}), 0)
        self.assertRefused(lambda: payloads.verified_count({"verified": -1}),
                           "verified must be a non-negative integer or null")


class ExperimentPayloads(Refused):
    def test_terms(self) -> None:
        self.assertEqual(payloads.experiment_terms({"primary": "likes", "cohort": [10001, "10002", "10003"]}),
                         ("likes", 1.5, ["10001", "10002", "10003"]))
        self.assertEqual(payloads.experiment_terms({"primary": "likes", "effect": "2", "cohort": ["10001", "10002", "10003"]})[1:],
                         (2.0, ["10001", "10002", "10003"]))

    def test_cohort_must_be_a_list_of_unique_post_ids(self) -> None:
        self.assertRefused(lambda: payloads.experiment_terms({"primary": "likes", "cohort": "abc"}),
                           "cohort must be a list of post ids")
        self.assertRefused(lambda: payloads.experiment_terms({"primary": "likes", "cohort": ["10001", "10001", "10002"]}),
                           "cohort lists 10001 more than once")
        self.assertRefused(lambda: payloads.experiment_terms({"primary": "likes", "cohort": ["10001", "10002", "abc"]}),
                           "cohort has 'abc', which is not a post id")

    def test_term_refusals_in_order(self) -> None:
        self.assertRefused(lambda: payloads.experiment_terms({}),
                           "primary must be one of ('views', 'likes', 'reposts', 'quotes', 'replies', 'bookmarks', 'engagement_rate', 'visit_rate')")
        self.assertRefused(lambda: payloads.experiment_terms({"primary": "replies"}),
                           "primary 'replies' cannot be scored: a root's replies count the account's own thread cards")
        self.assertRefused(lambda: payloads.experiment_terms({"primary": "likes", "effect": 1.0, "cohort": []}),
                           "effect must be above 1.0")
        self.assertRefused(lambda: payloads.experiment_terms({"primary": "likes", "cohort": [1, 2]}),
                           "cohort needs at least 3 posts")

    def test_a_non_numeric_effect_is_refused(self) -> None:
        self.assertRefused(lambda: payloads.experiment_terms({"primary": "likes", "effect": "x"}),
                           "open-experiment: payload is malformed: could not convert string to float: 'x'")

    def test_texts(self) -> None:
        got = payloads.experiment_texts({"question": " q ", "treatment": "t", "control": "c"})
        self.assertEqual(got, {"question": " q ", "treatment": "t", "control": "c", "reference_facts": []})
        self.assertRefused(lambda: payloads.experiment_texts({"question": "q", "treatment": "t", "control": " "}),
                           "control required")
        self.assertRefused(lambda: payloads.experiment_texts({"question": "q", "treatment": 3, "control": "c"}),
                           "treatment required")


class Malformed(Refused):
    def test_wrong_shapes_are_refused_not_raised(self) -> None:
        for call in (lambda: payloads.post_from_payload([]), lambda: payloads.snapshot_root_id(None),
                     lambda: payloads.activity_header({"stage": []}), lambda: payloads.experiment_texts(None),
                     lambda: list(payloads.activity_items({"items": "x"})),
                     lambda: payloads.snapshot_from_payload({"root": 1}, OBSERVED, 48.0, "valid", [])):
            with self.subTest(call=call):
                with self.assertRaises(LoopError):
                    call()

    def test_a_missing_key_is_named_or_refused(self) -> None:
        # validate_item reads the id first, and a missing one is a LoopError of its own.
        self.assertRefused(lambda: list(payloads.activity_items({"items": [{"kind": "reply"}]})),
                           "item id missing or bad")
        self.assertRefused(lambda: payloads.follower_inputs({"observed_at": T0, "ids": [1], "self_ids": 5}),
                           "record-followers: payload is malformed: 'int' object is not iterable")

    def test_loop_errors_pass_through_untouched(self) -> None:
        self.assertRefused(lambda: payloads.activity_header({"stage": "x", "observed_at": T0}),
                           "stage must be one of ['48h', 'backfill', 'final']")

    def test_since_id(self) -> None:
        self.assertIsNone(payloads.newer_since_id(None, "5"))
        self.assertIsNone(payloads.newer_since_id("", None))
        self.assertEqual(payloads.newer_since_id("7", None), "7")
        self.assertRefused(lambda: payloads.newer_since_id("abc", None),
                           "record-interactions: payload is malformed: invalid literal for int() with base 10: 'abc'")
        self.assertRefused(lambda: payloads.newer_since_id("5.5", None),
                           "record-interactions: payload is malformed: invalid literal for int() with base 10: '5.5'")
        self.assertEqual(payloads.newer_since_id("10", "9"), "10")
        self.assertIsNone(payloads.newer_since_id("9", "10"))
        self.assertEqual(payloads.newer_since_id(7.0, "5"), "7.0")  # compatibility: int() coercion once one is saved
        self.assertIsNone(payloads.newer_since_id(True, "5"))
        self.assertRefused(lambda: payloads.newer_since_id(7.0, None),
                           "record-interactions: payload is malformed: invalid literal for int() with base 10: '7.0'")
        self.assertRefused(lambda: payloads.newer_since_id("abc", "5"),
                           "record-interactions: payload is malformed: invalid literal for int() with base 10: 'abc'")
        self.assertRefused(lambda: payloads.newer_since_id("6", "abc"),
                           "record-interactions: the saved mentions_since_id 'abc' is not a number")


if __name__ == "__main__":
    unittest.main()
