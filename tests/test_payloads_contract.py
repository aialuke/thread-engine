#!/usr/bin/env python3
"""Pins what scripts/loop.py does with each Payload today, so moving the parsing cannot change it.

Everything here goes through the CLI (loop.main, or a subprocess where a traceback is the
behaviour). Cases marked "compatibility" pin behaviour nobody chose; changing one is a
separate, deliberate commit.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest

from test_loop import REPO, T0, LoopCase, hours

LOOP = REPO / "scripts" / "loop.py"
BAD_TIME = "bad time {!r}; use ISO 8601 with a timezone"
NONNEG = "{} must be a non-negative integer or null"


def sorted_repr(*names: str) -> str:
    return repr(sorted(names))


class Cli(LoopCase):
    def cli(self, *argv: str, now: str | None = None) -> subprocess.CompletedProcess:
        args = [sys.executable, str(LOOP), "--root", str(self.root)]
        if now:
            args += ["--now", now]
        return subprocess.run([*args, *argv], capture_output=True, text=True, check=False)


class PostPayload(LoopCase):
    BASE = {"root_id": "1000000001", "slug": "s", "format": "single-tip", "lane": "main", "posted_at": T0}

    def refused(self, **change) -> str:
        return self.fails("record-post", "--json", self.payload({**self.BASE, **change}))

    def test_every_validator_message(self) -> None:
        formats = sorted_repr("settings", "comparison", "tool-swap", "single-tip", "build-log", "tool-verdict", "other")
        cases = [
            ({"root_id": "x"}, "root_id missing or bad"),
            ({"slug": ""}, "slug required"),
            ({"format": "meme"}, f"format must be one of {formats}"),
            ({"lane": "z"}, "lane must be main or other"),
            ({"posted_at": "2026-10-01T00:00:00"}, "time '2026-10-01T00:00:00' has no timezone"),
            ({"posted_at": ""}, BAD_TIME.format("")),
            ({"retrospective": "yes"}, "retrospective must be true or false"),
            ({"made_in_repo": 1}, "made_in_repo must be true or false"),
            ({"arm": "q"}, "arm must be one of ['control', 'none', 'treatment']"),
            ({"cards": "x"}, "cards must be a list"),
            ({"cards": [{"id": "a"}]}, "card id bad"),
            ({"cards": [{"id": "1000000009", "text": 3}]}, "card text must be text"),
            ({"edits": [{"class": "z"}]},
             "edit class must be one of ['correction', 'deviation', 'preference', 'violation']"),
            ({"production_minutes": -1}, NONNEG.format("production_minutes")),
            ({"production_minutes": True}, NONNEG.format("production_minutes")),
        ]
        for change, message in cases:
            with self.subTest(change=change):
                self.assertEqual(self.refused(**change), message)

    def test_experiment_rules_run_after_the_payload_is_valid(self) -> None:
        self.assertEqual(self.refused(experiment="E9", arm="treatment"), "no experiment E9")
        self.assertEqual(self.refused(arm="treatment"), "arm set without an experiment")
        self.assertEqual(self.refused(arm="q", experiment="E9"),
                         "arm must be one of ['control', 'none', 'treatment']")

    def test_defaults_are_stored(self) -> None:
        self.ok("record-post", "--json", self.payload(self.BASE))
        post = json.loads((self.root / "ledger" / "1000000001.json").read_text())
        self.assertEqual(post, {
            "root_id": "1000000001", "slug": "s", "format": "single-tip", "lane": "main", "posted_at": T0,
            "retrospective": False, "made_in_repo": True, "experiment": None, "arm": "none",
            "hypothesis": None, "cards": [], "media": [], "ai_media": False, "production_minutes": None,
            "edits": [], "draft": None, "snapshots": [], "missed": False, "auto": False})

    def test_root_id_number_is_coerced_to_text(self) -> None:
        self.ok("record-post", "--json", self.payload({**self.BASE, "root_id": 1000000001}))
        self.assertTrue((self.root / "ledger" / "1000000001.json").exists())


class SnapshotPayload(LoopCase):
    def setUp(self) -> None:
        super().setUp()
        self.n = 0

    def fresh(self) -> str:
        self.n += 1
        root_id = f"10000001{self.n:02d}"
        self.post(root_id, T0)
        return root_id

    def refused(self, root_id: str, **change) -> str:
        return self.fails("record-snapshot", "--json",
                          self.payload({"root_id": root_id, "observed_at": hours(48), **change}))

    def test_messages(self) -> None:
        cases = [
            ({"observed_at": "zz"}, BAD_TIME.format("zz")),
            ({"root": {"views": -1}}, NONNEG.format("root.views")),
            ({"organic": {"likes": -1}}, NONNEG.format("organic.likes")),
            ({"followers": -1}, NONNEG.format("followers")),
            ({"cards": [{"views": -1}]}, NONNEG.format("card views")),
            ({"outside_replies": -1}, NONNEG.format("outside_replies")),
            ({"observed_at": hours(-1)}, "observed before the post existed"),
            ({"stage": "final"}, "a final read needs a post 26 to 29 days old"),
        ]
        for change, message in cases:
            with self.subTest(change=change):
                self.assertEqual(self.refused(self.fresh(), **change), message)

    def test_unknown_post_names_its_file(self) -> None:
        self.assertRegex(self.refused("1999999999"), r"^missing .*ledger/1999999999\.json$")

    def test_an_unknown_organic_key_is_dropped_not_refused(self) -> None:
        root_id = self.fresh()
        self.ok("record-snapshot", "--json", self.payload({
            "root_id": root_id, "observed_at": hours(48), "organic": {"bogus": 1, "likes": 2}}))
        snap = json.loads((self.root / "ledger" / f"{root_id}.json").read_text())["snapshots"][0]
        self.assertEqual(snap["organic"], {"impressions": None, "likes": 2, "replies": None, "reposts": None,
                                           "profile_visits": None, "url_clicks": None})

    def test_stored_defaults(self) -> None:
        root_id = self.fresh()
        self.ok("record-snapshot", "--json", self.payload({"root_id": root_id, "observed_at": hours(48)}))
        snap = json.loads((self.root / "ledger" / f"{root_id}.json").read_text())["snapshots"][0]
        self.assertEqual(snap, {
            "observed_at": hours(48), "age_hours": 48.0, "kind": "valid", "source": "grok",
            "root": {m: None for m in ("views", "likes", "reposts", "quotes", "replies", "bookmarks")},
            "cards": [], "outside_replies": None, "outside_repliers": [], "repliers_complete": None,
            "followers": None, "raw_file": None,
            "missing": ["views", "likes", "reposts", "quotes", "replies", "bookmarks"]})

    def test_duplicates_return_before_the_payload_is_validated(self) -> None:
        # Check order (compatibility): a repeat valid or final read is skipped without looking at the numbers.
        root_id = self.fresh()
        self.ok("record-snapshot", "--json", self.payload({"root_id": root_id, "observed_at": hours(48)}))
        again = self.ok("record-snapshot", "--json", self.payload({
            "root_id": root_id, "observed_at": hours(48), "root": {"views": -1}, "followers": -1}))
        self.assertEqual(again, {"recorded": False, "reason": "valid snapshot already exists", "root_id": root_id})

    def test_a_bad_payload_writes_nothing(self) -> None:
        root_id = self.fresh()
        before = (self.root / "ledger" / f"{root_id}.json").read_text()
        self.refused(root_id, root={"views": -1})
        self.assertEqual((self.root / "ledger" / f"{root_id}.json").read_text(), before)


class ActivityPayload(Cli):
    ITEM = {"id": "1000000005", "kind": "original", "created_at": T0, "conversation_id": "1000000005"}

    def refused(self, **change) -> str:
        return self.fails("record-activity", "--json", self.payload({"stage": "48h", "observed_at": T0, **change}))

    def test_header_messages(self) -> None:
        self.assertEqual(self.refused(stage="x"), "stage must be one of ['48h', 'backfill', 'final']")
        self.assertEqual(self.fails("record-activity", "--json", self.payload({"stage": "48h"})), BAD_TIME.format(""))

    def test_item_messages(self) -> None:
        cases = [
            ({"id": "x"}, "item id missing or bad"),
            ({"kind": "z"}, "item kind must be one of ['original', 'quote', 'reply', 'repost', 'thread_card']"),
            ({"created_at": "q"}, BAD_TIME.format("q")),
            ({"conversation_id": "q"}, "item conversation_id bad"),
            ({"public": {"zz": 1}}, "unknown public measure 'zz'"),
            ({"organic": {"likes": -1}}, NONNEG.format("organic.likes")),
        ]
        for change, message in cases:
            with self.subTest(change=change):
                self.assertEqual(self.refused(items=[{**self.ITEM, **change}]), message)

    def test_topics_must_be_a_list_of_text_before_anything_is_written(self) -> None:
        # Was accepted, stored, and then broke the account view once follower data existed.
        for bad in (None, 1, [{}], [1], "x"):
            with self.subTest(topics=bad):
                self.assertEqual(self.refused(items=[{**self.ITEM, "topics": bad}]),
                                 "item topics must be a list of text")
        self.assertFalse((self.root / "ledger" / "activity" / "2026-10.json").exists())

    def test_a_bad_cursor_fails_after_the_month_file_is_written(self) -> None:
        # Check order (compatibility): items are written, then the cursor is parsed; the state cursor is not moved.
        error = self.refused(items=[self.ITEM], cursor={"read48_until": "zz"})
        self.assertEqual(error, BAD_TIME.format("zz"))
        self.assertTrue((self.root / "ledger" / "activity" / "2026-10.json").exists())
        state = json.loads((self.root / "loop" / "state.json").read_text())
        self.assertNotIn("read48_until", state.get("api", {}))

    def test_a_bad_second_item_leaves_no_month_file(self) -> None:
        self.refused(items=[self.ITEM, {**self.ITEM, "id": "x"}])
        self.assertFalse((self.root / "ledger" / "activity" / "2026-10.json").exists())

    def test_result_shape_and_cursor(self) -> None:
        result = self.ok("record-activity", "--json", self.payload({
            "stage": "48h", "observed_at": T0, "items": [self.ITEM],
            "cursor": {"read48_until": "2026-10-01T00:00:00+00:00"}}))
        self.assertEqual(result, {"recorded": 1, "stage": "48h", "cursors": {"read48_until": T0}})


class InteractionsPayload(Cli):
    MENTION = {"author_id": "9", "id": "1", "conversation_id": "1000000001", "created_at": T0}

    def send(self, data: dict) -> subprocess.CompletedProcess:
        return self.cli("record-interactions", "--json", self.payload(data))

    def test_observed_at_is_required_and_reported(self) -> None:
        self.assertEqual(self.fails("record-interactions", "--json", self.payload({})), BAD_TIME.format(""))

    def test_a_mention_without_conversation_id_is_refused(self) -> None:
        run = self.send({"observed_at": T0, "mentions": [{k: v for k, v in self.MENTION.items()
                                                          if k != "conversation_id"}]})
        self.assertEqual((run.returncode, run.stdout), (1, ""))
        self.assertEqual(json.loads(run.stderr),
                         {"error": "record-interactions: payload is missing 'conversation_id'"})
        self.assertFalse((self.root / "loop" / "followers" / "interactions.json").exists())

    def test_null_mentions_is_refused(self) -> None:
        run = self.send({"observed_at": T0, "mentions": None})
        self.assertEqual((run.returncode, run.stdout), (1, ""))
        self.assertRegex(json.loads(run.stderr)["error"], r"^record-interactions: payload is malformed: ")

    def test_a_skipped_mention_is_not_read_further(self) -> None:
        # Compatibility: own and authorless mentions are dropped before conversation_id is looked up.
        bare = {"id": "1"}
        result = self.ok("record-interactions", "--json", self.payload({
            "observed_at": T0, "self_ids": [9], "mentions": [{**bare, "author_id": "9"}, bare]}))
        self.assertEqual(result, {"people": 0, "mentions_since_id": None, "outside_replies": {}})

    def test_entries_are_read_one_at_a_time(self) -> None:
        # Check order (compatibility): an early entry's bad time is refused before a later entry is read at all,
        # and a reply target is only read after every mention has been applied.
        late = {"author_id": "8"}
        run = self.send({"observed_at": T0, "mentions": [{**self.MENTION, "created_at": "zz"}, late]})
        self.assertEqual((run.returncode, run.stdout), (1, ""))
        self.assertEqual(json.loads(run.stderr), {"error": BAD_TIME.format("zz")})
        run = self.send({"observed_at": T0, "mentions": [{**self.MENTION, "created_at": "zz"}],
                         "reply_targets": [{"user_id": "5"}]})
        self.assertEqual(json.loads(run.stderr), {"error": BAD_TIME.format("zz")})
        run = self.send({"observed_at": T0, "mentions": [self.MENTION],
                         "reply_targets": [{"user_id": "5", "item_id": "1", "at": "zz"}, {"user_id": "6"}]})
        self.assertEqual(json.loads(run.stderr), {"error": BAD_TIME.format("zz")})

    def test_own_and_authorless_mentions_are_skipped(self) -> None:
        result = self.ok("record-interactions", "--json", self.payload({
            "observed_at": T0, "self_ids": [9],
            "mentions": [self.MENTION, {**self.MENTION, "author_id": ""}, {**self.MENTION, "author_id": "7", "id": "2"}]}))
        self.assertEqual(result, {"people": 1, "mentions_since_id": None, "outside_replies": {"1000000001": 1}})

    def test_since_id_is_kept_as_text_and_compared_with_the_saved_one(self) -> None:
        self.ok("record-interactions", "--json", self.payload({"observed_at": T0, "since_id": "007"}))
        kept = self.ok("record-interactions", "--json", self.payload({"observed_at": T0, "since_id": "5"}))
        self.assertEqual(kept["mentions_since_id"], "007")
        newer = self.ok("record-interactions", "--json", self.payload({"observed_at": T0, "since_id": "12"}))
        self.assertEqual(newer["mentions_since_id"], "12")

    def test_a_first_non_numeric_since_id_is_refused_and_writes_nothing(self) -> None:
        run = self.send({"observed_at": T0, "since_id": "abc"})
        self.assertEqual((run.returncode, run.stdout), (1, ""))
        self.assertRegex(json.loads(run.stderr)["error"], r"^record-interactions: payload is malformed: ")
        self.assertFalse((self.root / "loop" / "followers" / "interactions.json").exists())

    def test_a_non_numeric_since_id_is_refused_once_one_is_saved(self) -> None:
        self.ok("record-interactions", "--json", self.payload({"observed_at": T0, "since_id": "5"}))
        run = self.send({"observed_at": T0, "since_id": "abc"})
        self.assertEqual(run.returncode, 1)
        self.assertRegex(json.loads(run.stderr)["error"], r"^record-interactions: payload is malformed: ")


class FollowersPayload(Cli):
    def send(self, data: dict) -> subprocess.CompletedProcess:
        return self.cli("record-followers", "--json", self.payload(data))

    def files(self) -> list[str]:
        folder = self.root / "loop" / "followers"
        return sorted(p.name for p in folder.glob("followers-*.json")) if folder.is_dir() else []

    def test_observed_at_is_required(self) -> None:
        self.assertEqual(self.fails("record-followers", "--json", self.payload({})), BAD_TIME.format(""))

    def test_missing_ids_is_refused_and_nothing_is_written(self) -> None:
        # Was: recorded zero followers, so the next real list would be credited as all-new followers.
        self.assertEqual(self.fails("record-followers", "--json", self.payload({"observed_at": T0})),
                         "record-followers: ids required (a missing list would record zero followers)")
        self.assertEqual(self.files(), [])

    def test_ids_that_are_not_a_list_are_refused_and_nothing_is_written(self) -> None:
        for bad in ({}, "12345", 7):
            with self.subTest(ids=bad):
                self.assertEqual(self.fails("record-followers", "--json",
                                            self.payload({"observed_at": T0, "ids": bad})),
                                 "record-followers: ids must be a list")
        self.assertEqual(self.files(), [])

    def test_null_ids_is_refused(self) -> None:
        run = self.send({"observed_at": T0, "ids": None})
        self.assertEqual((run.returncode, run.stdout), (1, ""))
        self.assertEqual(json.loads(run.stderr), {"error": "record-followers: ids must be a list"})
        self.assertEqual(self.files(), [])

    def test_a_bad_verified_count_fails_after_the_ids_file_is_written(self) -> None:
        # Check order (compatibility): the day's ids are saved, then `verified` is checked.
        self.assertEqual(self.fails("record-followers", "--json",
                                    self.payload({"observed_at": T0, "ids": [1], "verified": -1})),
                         NONNEG.format("verified"))
        self.assertEqual(self.files(), ["followers-2026-10-01.json"])
        self.assertFalse((self.root / "ledger" / "activity" / "account.json").exists())

    def test_own_ids_are_removed_and_total_defaults_to_the_count(self) -> None:
        row = self.ok("record-followers", "--json", self.payload({
            "observed_at": T0, "self_ids": [1], "ids": [1, 2, 3], "verified": 4}))
        self.assertEqual(row, {"date": "2026-10-01", "at": T0, "followers": 2, "verified_followers": 4,
                               "baseline": True})
        total = self.ok("record-followers", "--json", self.payload({
            "observed_at": hours(24), "ids": [2, 3, 4], "total": 500}))
        self.assertEqual((total["followers"], total["new"], total["lost"]), (500, 1, 0))


class ExperimentPayload(LoopCase):
    def refused(self, data: dict) -> str:
        return self.fails("open-experiment", "--json", self.payload(data))

    def seed(self, count: int = 3) -> list[str]:
        ids = []
        for i in range(count):
            root_id = f"20000000{i:02d}"
            self.post(root_id, hours(-500 + i), retrospective=True, made_in_repo=False)
            self.snap(root_id, hours(-400 + i), 1000, bookmarks=100 * (i + 1))
            ids.append(root_id)
        return ids

    def test_terms_messages(self) -> None:
        metrics = "('views', 'likes', 'reposts', 'quotes', 'replies', 'bookmarks')"
        cases = [
            ({}, f"primary must be one of {metrics}"),
            ({"primary": "views"},
             "primary 'views' cannot be scored: views include paid (boosted) reach and say nothing about follows"),
            ({"primary": "replies"},
             "primary 'replies' cannot be scored: a root's replies count the account's own thread cards"),
            ({"primary": "likes", "effect": 1}, "effect must be above 1.0"),
            ({"primary": "likes", "cohort": ["1"]}, "cohort needs at least 3 posts"),
        ]
        for data, message in cases:
            with self.subTest(data=data):
                self.assertEqual(self.refused(data), message)

    def test_a_non_numeric_effect_is_refused(self) -> None:
        self.assertEqual(self.refused({"primary": "likes", "effect": "x"}),
                         "open-experiment: payload is malformed: could not convert string to float: 'x'")

    def test_text_fields_are_checked_after_the_cohort(self) -> None:
        ids = self.seed()
        base = {"primary": "bookmarks", "cohort": ids}
        for field in ("question", "treatment", "control"):
            given = {"question": "q", "treatment": "t", "control": "c"}
            given[field] = "  "
            with self.subTest(field=field):
                self.assertEqual(self.refused({**base, **given}), f"{field} required")
        # cohort problems win over missing text
        self.assertEqual(self.refused({"primary": "bookmarks", "cohort": ids[:2]}),
                         "cohort needs at least 3 posts")

    def test_open_experiment_check_comes_before_the_payload_is_read(self) -> None:
        ids = self.seed()
        self.ok("open-experiment", "--json", self.payload({
            "question": "q", "treatment": "t", "control": "c", "primary": "bookmarks", "cohort": ids}), now=T0)
        self.assertEqual(self.fails("open-experiment", "--json", str(self.root / "nope.json")),
                         "an experiment is already open; one at a time")

    def test_defaults(self) -> None:
        ids = self.seed()
        result = self.ok("open-experiment", "--json", self.payload({
            "question": "q", "treatment": "t", "control": "c", "primary": "bookmarks", "cohort": ids}), now=T0)
        self.assertEqual(result, {"opened": "E-001", "cohort_median": 200, "threshold": 300.0})
        exp = json.loads((self.root / "loop" / "state.json").read_text())["experiments"][0]
        self.assertEqual((exp["effect"], exp["size"], exp["reference_facts"], exp["status"]),
                         (1.5, 3, [], "testing"))


if __name__ == "__main__":
    unittest.main()
