#!/usr/bin/env python3
"""Checks for scripts/loop.py. Stdlib only. Git tests use a throwaway repo."""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "tests"))

import loop  # noqa: E402

T0 = "2026-10-01T00:00:00Z"


def hours(h: float, base: str = T0) -> str:
    stamp = loop.parse_time(base)
    from datetime import timedelta
    return loop.iso(stamp + timedelta(hours=h))


class LoopCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.counter = 0
        self.ok("init", "--self-handles", "exitzerocode,@AwakenLuke", now=T0)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_loop(self, *argv: str, now: str | None = None) -> tuple[int, dict]:
        args = ["--root", str(self.root)]
        if now:
            args += ["--now", now]
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = loop.main([*args, *argv])
        text = out.getvalue() if code == 0 else err.getvalue()
        return code, json.loads(text)

    def ok(self, *argv: str, now: str | None = None) -> dict:
        code, data = self.run_loop(*argv, now=now)
        self.assertEqual(code, 0, data)
        return data

    def fails(self, *argv: str, now: str | None = None) -> str:
        code, data = self.run_loop(*argv, now=now)
        self.assertEqual(code, 1, data)
        return data["error"]

    def payload(self, data: dict) -> str:
        self.counter += 1
        path = self.root / f"payload-{self.counter}.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return str(path)

    def post(self, root_id: str, posted_at: str, **extra) -> dict:
        data = {"root_id": root_id, "slug": f"s{root_id[-3:]}", "format": "single-tip",
                "lane": "main", "posted_at": posted_at, "made_in_repo": True}
        data.update(extra)
        return self.ok("record-post", "--json", self.payload(data))

    def snap(self, root_id: str, observed_at: str, views: int | None, repliers=None, bookmarks: int = 0) -> dict:
        data = {"root_id": root_id, "observed_at": observed_at,
                "root": {"views": views, "likes": 1, "reposts": 0, "quotes": 0, "replies": 1, "bookmarks": bookmarks},
                "followers": 40}
        if repliers is not None:
            data["repliers"] = repliers
        return self.ok("record-snapshot", "--json", self.payload(data))


class PostsAndSnapshots(LoopCase):
    def test_record_post_is_idempotent(self) -> None:
        self.assertTrue(self.post("1000000001", T0)["recorded"])
        again = self.post("1000000001", T0)
        self.assertFalse(again["recorded"])
        self.assertEqual(again["reason"], "already recorded")

    def test_bad_format_refused(self) -> None:
        data = {"root_id": "1000000002", "slug": "x", "format": "meme", "lane": "main", "posted_at": T0}
        self.assertIn("format", self.fails("record-post", "--json", self.payload(data)))

    def test_naive_time_refused(self) -> None:
        data = {"root_id": "1000000003", "slug": "x", "format": "settings", "lane": "main",
                "posted_at": "2026-10-01T00:00:00"}
        self.assertIn("timezone", self.fails("record-post", "--json", self.payload(data)))

    def test_window_edges(self) -> None:
        self.post("1000000010", T0)
        self.assertEqual(self.snap("1000000010", hours(35.9), 5)["kind"], "early")
        self.assertEqual(self.snap("1000000010", hours(36), 10)["kind"], "valid")
        second = self.snap("1000000010", hours(40), 12)
        self.assertFalse(second["recorded"])
        self.assertEqual(self.snap("1000000010", hours(60.1), 14)["kind"], "late")

    def test_due_missed_pending(self) -> None:
        self.post("1000000020", T0)
        self.post("1000000021", hours(-40))
        self.post("1000000022", hours(-70))
        due = self.ok("due", now=T0)
        self.assertEqual([r["root_id"] for r in due["pending"]], ["1000000020"])
        self.assertEqual([r["root_id"] for r in due["due"]], ["1000000021"])
        self.assertEqual([r["root_id"] for r in due["missed"]], ["1000000022"])
        self.assertEqual(self.ok("mark-missed", now=T0)["marked_missed"], ["1000000022"])
        self.assertEqual(self.ok("due", now=T0)["missed"], [])

    def test_retrospective_post_still_gets_a_timed_snapshot(self) -> None:
        self.post("1000000030", T0, retrospective=True, made_in_repo=False)
        self.post("1000000031", hours(-100), retrospective=True, made_in_repo=False)
        due = self.ok("due", now=hours(40))
        self.assertEqual([r["root_id"] for r in due["due"]], ["1000000030"])
        self.assertEqual(due["missed"], [])
        self.assertEqual(self.snap("1000000030", hours(40), 100)["kind"], "valid")

    def test_outside_replies_exclude_own_handles(self) -> None:
        self.post("1000000040", T0)
        self.snap("1000000040", hours(40), 50, repliers=["exitzerocode", "awakenluke", "@Someone", "someone", "other"])
        post = json.loads((self.root / "ledger" / "1000000040.json").read_text())
        self.assertEqual(post["snapshots"][0]["outside_repliers"], ["other", "someone"])
        self.assertEqual(post["snapshots"][0]["outside_replies"], 3)

    def test_incomplete_repliers_marked_as_lower_bound(self) -> None:
        self.post("1000000045", T0)
        data = {"root_id": "1000000045", "observed_at": hours(40),
                "root": {"views": 9, "likes": 0, "reposts": 0, "quotes": 0, "replies": 32, "bookmarks": 0},
                "repliers": ["a", "b"], "repliers_complete": False}
        self.ok("record-snapshot", "--json", self.payload(data))
        self.assertIn("| ≥2 |", (self.root / "ledger" / "SUMMARY.md").read_text())

    def test_set_repliers_complete_corrects_and_logs(self) -> None:
        self.post("1000000046", T0)
        self.snap("1000000046", hours(40), 9, repliers=["a"])
        self.assertIn("| 1 |", (self.root / "ledger" / "SUMMARY.md").read_text())
        self.assertIn("--reason", self.fails("set-repliers-complete", "--root-id", "1000000046",
                                             "--value", "false", "--reason", " "))
        done = self.ok("set-repliers-complete", "--root-id", "1000000046", "--value", "false",
                       "--reason", "search returned fewer authors than replies", now=hours(50))
        self.assertEqual(done["snapshots_changed"], 1)
        self.assertIn("| ≥1 |", (self.root / "ledger" / "SUMMARY.md").read_text())
        post = json.loads((self.root / "ledger" / "1000000046.json").read_text())
        self.assertEqual(post["amendments"][0]["reason"], "search returned fewer authors than replies")
        again = self.ok("set-repliers-complete", "--root-id", "1000000046", "--value", "false", "--reason", "x")
        self.assertEqual(again["snapshots_changed"], 0)
        self.assertEqual(self.ok("validate")["problems"], [])

    def test_missing_metric_recorded_not_zero(self) -> None:
        self.post("1000000050", T0)
        result = self.snap("1000000050", hours(40), None)
        self.assertEqual(result["missing"], ["views"])

    def test_render_writes_views(self) -> None:
        self.post("1000000060", T0)
        self.assertTrue((self.root / "ledger" / "SUMMARY.md").is_file())
        self.assertTrue((self.root / "experiments.md").is_file())
        self.assertTrue((self.root / "learnings.md").is_file())

    def test_validate_reports_clean(self) -> None:
        self.post("1000000070", T0)
        self.assertEqual(self.ok("validate")["problems"], [])

    def test_validate_names_a_bad_post_and_keeps_going(self) -> None:
        self.post("1000000071", T0)
        good = json.loads((self.root / "ledger" / "1000000071.json").read_text())
        (self.root / "ledger" / "1000000072.json").write_text(json.dumps(good), encoding="utf-8")
        bad = json.loads((self.root / "ledger" / "1000000071.json").read_text())
        bad["lane"] = "unset"
        (self.root / "ledger" / "1000000071.json").write_text(json.dumps(bad), encoding="utf-8")
        broken = self.root / "ledger" / "1000000073.json"
        broken.write_text("{", encoding="utf-8")
        self.assertEqual(self.ok("validate"), {
            "posts": 3,
            "problems": [
                "1000000071.json: lane must be main or other",
                "1000000072.json: file name does not match root_id",
                "1000000073.json: "
                f"{broken.resolve()} is not valid JSON: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)",
            ],
        })


class Experiments(LoopCase):
    def seed_cohort(self, values=(100, 200, 300)) -> list[str]:
        ids = []
        for i, value in enumerate(values):
            root_id = f"20000000{i:02d}"
            self.post(root_id, hours(-500 + i), retrospective=True, made_in_repo=False)
            self.snap(root_id, hours(-400 + i), 1000, bookmarks=value)
            ids.append(root_id)
        return ids

    def open(self, cohort: list[str]) -> dict:
        return self.ok("open-experiment", "--json", self.payload({
            "question": "Standalone beats a thread?", "treatment": "standalone post",
            "control": "3-card thread", "primary": "bookmarks", "cohort": cohort}), now=T0)

    def treatment(self, start: int, values: list[int]) -> None:
        for i, value in enumerate(values):
            root_id = f"30000000{start + i:02d}"
            posted = hours(10 * (start + i))
            self.post(root_id, posted, experiment="E-001", arm="treatment")
            self.snap(root_id, hours(40, posted), 1000, bookmarks=value)

    def test_cohort_frozen_median_and_threshold(self) -> None:
        opened = self.open(self.seed_cohort())
        self.assertEqual(opened["cohort_median"], 200)
        self.assertEqual(opened["threshold"], 300)

    def test_cohort_too_small(self) -> None:
        ids = self.seed_cohort((100, 200))
        error = self.fails("open-experiment", "--json", self.payload({
            "question": "q", "treatment": "t", "control": "c", "primary": "bookmarks", "cohort": ids}))
        self.assertIn("at least 3", error)

    def test_one_experiment_at_a_time(self) -> None:
        ids = self.seed_cohort()
        self.open(ids)
        self.assertIn("one at a time", self.fails("open-experiment", "--json", self.payload({
            "question": "q", "treatment": "t", "control": "c", "primary": "bookmarks", "cohort": ids})))

    def test_pass_then_replicate_adopts(self) -> None:
        self.open(self.seed_cohort())
        self.treatment(0, [300, 400, 500])
        first = self.ok("evaluate", now=hours(200))
        self.assertEqual(first["status"], "promising")
        self.treatment(3, [310, 320, 330])
        second = self.ok("evaluate", now=hours(300))
        self.assertEqual(second["status"], "adopted")
        lessons = self.ok("status", now=hours(300))
        self.assertIsNone(lessons["open_experiment"])
        state = json.loads((self.root / "loop" / "state.json").read_text())
        self.assertEqual(state["lessons"][0]["status"], "adopted")
        self.assertEqual(len(state["lessons"][0]["evidence"]), 6)

    def test_fail_closes_no_effect(self) -> None:
        self.open(self.seed_cohort())
        self.treatment(0, [100, 400, 50])
        self.assertEqual(self.ok("evaluate", now=hours(200))["status"], "no_effect")

    def test_mixed_then_fail(self) -> None:
        self.open(self.seed_cohort())
        self.treatment(0, [300, 400, 50])
        self.assertEqual(self.ok("evaluate", now=hours(200))["status"], "unclear")
        self.treatment(3, [300, 10, 10])
        self.assertEqual(self.ok("evaluate", now=hours(300))["status"], "no_effect")

    def test_promising_not_replicated(self) -> None:
        self.open(self.seed_cohort())
        self.treatment(0, [300, 400, 500])
        self.ok("evaluate", now=hours(200))
        self.treatment(3, [300, 400, 10])
        self.assertEqual(self.ok("evaluate", now=hours(300))["status"], "not_replicated")

    def test_evaluate_waits_for_three(self) -> None:
        self.open(self.seed_cohort())
        self.treatment(0, [300, 400])
        result = self.ok("evaluate", now=hours(200))
        self.assertEqual(result["status"], "testing")
        self.assertEqual(result["posts_needed_for_next_round"], 1)

    def test_control_posts_do_not_count(self) -> None:
        self.open(self.seed_cohort())
        for i in range(3):
            root_id = f"40000000{i:02d}"
            posted = hours(10 * i)
            self.post(root_id, posted, experiment="E-001", arm="control")
            self.snap(root_id, hours(40, posted), 900, bookmarks=900)
        self.assertEqual(self.ok("evaluate", now=hours(200))["events"], [])

    def snap_organic(self, root_id: str, observed_at: str, impressions: int, likes: int = 0, reposts: int = 0,
                     visits: int = 0) -> dict:
        data = {"root_id": root_id, "observed_at": observed_at,
                "root": {"views": impressions, "likes": likes, "reposts": reposts, "quotes": 0, "replies": 9,
                         "bookmarks": 0},
                "organic": {"impressions": impressions, "likes": likes, "replies": 9, "reposts": reposts,
                            "profile_visits": visits, "url_clicks": 0},
                "followers": 40}
        return self.ok("record-snapshot", "--json", self.payload(data))

    def rate_cohort(self, rows=((1000, 10, 0, 0), (1000, 20, 0, 0), (1000, 30, 0, 0))) -> list[str]:
        ids = []
        for i, (impressions, likes, reposts, visits) in enumerate(rows):
            root_id = f"21000000{i:02d}"
            self.post(root_id, hours(-500 + i), retrospective=True, made_in_repo=False)
            self.snap_organic(root_id, hours(-400 + i), impressions, likes, reposts, visits)
            ids.append(root_id)
        return ids

    def open_rate(self, cohort: list[str], primary: str = "engagement_rate") -> dict:
        return self.ok("open-experiment", "--json", self.payload({
            "question": "q", "treatment": "t", "control": "c", "primary": primary, "cohort": cohort}), now=T0)

    def rate_treatment(self, start: int, rows: list[tuple[int, int, int]]) -> None:
        for i, (impressions, likes, reposts) in enumerate(rows):
            root_id = f"31000000{start + i:02d}"
            posted = hours(10 * (start + i))
            self.post(root_id, posted, experiment="E-001", arm="treatment")
            self.snap_organic(root_id, hours(40, posted), impressions, likes, reposts)

    def test_engagement_rate_cohort_median_and_bar_are_per_thousand_impressions(self) -> None:
        opened = self.open_rate(self.rate_cohort())
        self.assertEqual((opened["cohort_median"], opened["threshold"]), (20.0, 30.0))

    def test_engagement_rate_counts_likes_plus_reposts_only(self) -> None:
        ids = self.rate_cohort(((1000, 9, 1, 0), (1000, 15, 5, 0), (1000, 25, 5, 0)))
        self.assertEqual(self.open_rate(ids)["cohort_median"], 20.0)

    def test_cohort_posts_under_the_floor_or_without_organic_are_not_admitted(self) -> None:
        ids = self.rate_cohort(((49, 5, 0, 0), (1000, 20, 0, 0), (1000, 30, 0, 0)))
        error = self.fails("open-experiment", "--json", self.payload({
            "question": "q", "treatment": "t", "control": "c", "primary": "engagement_rate", "cohort": ids}))
        self.assertEqual(error, "only 2 cohort posts have an engagement_rate snapshot with 50 or more organic impressions")
        bare = self.seed_cohort()
        self.assertIn("only 0 cohort posts", self.attempt(bare, "engagement_rate"))
        four = self.rate_cohort(((49, 5, 0, 0), (1000, 20, 0, 0), (1000, 30, 0, 0), (100, 3, 0, 0)))
        opened = self.open_rate(four)
        self.assertEqual(opened["cohort_median"], 30.0)
        exp = json.loads((self.root / "loop" / "state.json").read_text())["experiments"][0]
        self.assertEqual([c["root_id"] for c in exp["cohort"]], four[1:])

    def test_zero_median_rate_cohort_refused(self) -> None:
        self.assertIn("median", self.attempt(self.rate_cohort(((1000, 0, 0, 0), (1000, 0, 0, 0), (1000, 5, 0, 0))),
                                             "engagement_rate"))

    def test_visit_rate_needs_spread_across_the_cohort(self) -> None:
        self.assertIn("median profile visits is 0", self.attempt(
            self.rate_cohort(((1000, 1, 0, 0), (1000, 1, 0, 0), (1000, 1, 0, 3))), "visit_rate"))
        self.assertIn("needs 5", self.attempt(
            self.rate_cohort(((1000, 1, 0, 2), (1000, 1, 0, 2), (1000, 1, 0, 2))), "visit_rate"))
        ids = self.rate_cohort(((1000, 1, 0, 2),) * 4 + ((1000, 1, 0, 3), (1000, 1, 0, 2)))
        self.assertEqual(self.open_rate(ids, "visit_rate")["cohort_median"], 2.0)

    def test_treatment_rates_are_scored_and_below_the_floor_is_a_miss_with_a_note(self) -> None:
        self.open_rate(self.rate_cohort())
        self.rate_treatment(0, [(1000, 40, 0), (1000, 50, 0), (49, 40, 0)])
        result = self.ok("evaluate", now=hours(200))
        self.assertEqual((result["status"], result["events"][0]["result"]), ("unclear", "mixed"))
        rnd = json.loads((self.root / "loop" / "state.json").read_text())["experiments"][0]["rounds"][0]
        self.assertEqual((rnd["values"], rnd["passes"], rnd["notes"]), ([40.0, 50.0, 0.0], 2, {"3100000002": "below_floor"}))
        self.assertIn("below_floor", (self.root / "experiments.md").read_text())

    def test_a_treatment_post_without_organic_numbers_waits(self) -> None:
        self.open_rate(self.rate_cohort())
        self.rate_treatment(0, [(1000, 40, 0), (1000, 50, 0)])
        bare = "3100000009"
        self.post(bare, hours(95), experiment="E-001", arm="treatment")
        self.snap(bare, hours(40, hours(95)), 1000)
        self.assertEqual(self.ok("evaluate", now=hours(300))["posts_needed_for_next_round"], 1)

    def test_control_posts_do_not_count_toward_a_rate_experiment(self) -> None:
        self.open_rate(self.rate_cohort())
        for i in range(3):
            root_id = f"41000000{i:02d}"
            posted = hours(10 * i)
            self.post(root_id, posted, experiment="E-001", arm="control")
            self.snap_organic(root_id, hours(40, posted), 1000, likes=900)
        self.assertEqual(self.ok("evaluate", now=hours(200))["events"], [])

    def test_a_round_without_notes_keeps_its_old_shape(self) -> None:
        self.open(self.seed_cohort())
        self.treatment(0, [300, 400, 500])
        self.ok("evaluate", now=hours(200))
        rnd = json.loads((self.root / "loop" / "state.json").read_text())["experiments"][0]["rounds"][0]
        self.assertNotIn("notes", rnd)

    def attempt(self, cohort: list[str], primary: str) -> str:
        return self.fails("open-experiment", "--json", self.payload({
            "question": "q", "treatment": "t", "control": "c", "primary": primary, "cohort": cohort}))

    def test_views_and_replies_cannot_be_scored(self) -> None:
        ids = self.seed_cohort()
        self.assertIn("paid", self.attempt(ids, "views"))
        self.assertIn("thread cards", self.attempt(ids, "replies"))
        self.assertIn("primary must be one of", self.fails("open-experiment", "--json", self.payload({
            "question": "q", "treatment": "t", "control": "c", "cohort": ids})))

    def test_zero_median_cohort_refused(self) -> None:
        self.assertIn("median", self.attempt(self.seed_cohort((0, 0, 5)), "bookmarks"))

    def test_nonorganic_post_kept_out_of_cohorts_and_rounds(self) -> None:
        ids = self.seed_cohort()
        marked = self.ok("mark-nonorganic", "--root-id", ids[0], "--reason", "95% boosted")
        self.assertTrue(marked["marked"])
        self.assertFalse(self.ok("mark-nonorganic", "--root-id", ids[0], "--reason", "again")["marked"])
        self.assertIn("non-organic", self.attempt(ids, "bookmarks"))
        self.assertIn("non-organic", (self.root / "ledger" / "SUMMARY.md").read_text())
        self.open(ids[1:] + [self.extra_cohort()])
        self.treatment(0, [300, 400])
        boosted = "3000000009"
        self.post(boosted, hours(95), experiment="E-001", arm="treatment")
        self.snap(boosted, hours(40, hours(95)), 1000, bookmarks=5000)
        self.ok("mark-nonorganic", "--root-id", boosted, "--reason", "boosted after posting")
        self.assertEqual(self.ok("evaluate", now=hours(300))["posts_needed_for_next_round"], 1)

    def extra_cohort(self) -> str:
        root_id = "2000000099"
        self.post(root_id, hours(-450), retrospective=True, made_in_repo=False)
        self.snap(root_id, hours(-350), 1000, bookmarks=220)
        return root_id

    def test_arm_without_experiment_refused(self) -> None:
        data = {"root_id": "5000000001", "slug": "x", "format": "settings", "lane": "main",
                "posted_at": T0, "arm": "treatment"}
        self.assertIn("arm set without", self.fails("record-post", "--json", self.payload(data)))

    def test_slot_alternates_then_one_in_three(self) -> None:
        self.assertEqual(self.ok("next-slot", now=hours(1))["slot"], "explore")
        self.post("6000000001", hours(1))
        self.assertEqual(self.ok("next-slot", now=hours(2))["slot"], "exploit")
        self.post("6000000002", hours(2))
        late = hours(24 * 30)
        self.assertEqual(self.ok("next-slot", now=late)["rule"], "one in three explores")
        self.assertEqual(self.ok("next-slot", now=late)["slot"], "exploit")
        self.post("6000000003", hours(3))
        self.assertEqual(self.ok("next-slot", now=late)["slot"], "explore")

    def test_review_due_and_stale(self) -> None:
        self.assertTrue(self.ok("review-due", now=T0)["review_due"])
        self.ok("mark-reviewed", now=T0)
        self.assertFalse(self.ok("review-due", now=hours(24))["review_due"])
        self.assertTrue(self.ok("review-due", now=hours(24 * 7))["review_due"])

    def test_a_stale_lesson_keeps_adopted(self) -> None:
        path = self.root / "loop" / "state.json"
        state = json.loads(path.read_text())
        old = hours(-24 * 50)
        state["lessons"] = [{
            "id": "L-001", "experiment": None, "statement": "short", "status": "adopted",
            "evidence": ["1", "2", "3"], "reference_facts": [], "created_at": old, "last_evidence_at": old,
        }, {
            "id": "L-002", "experiment": None, "statement": "fresh", "status": "adopted",
            "evidence": ["4"], "reference_facts": [], "created_at": T0, "last_evidence_at": T0,
        }]
        path.write_text(json.dumps(state))
        got = self.ok("mark-reviewed", now=T0)
        self.assertEqual(got["newly_stale"], ["L-001"])
        saved = json.loads(path.read_text())
        self.assertEqual([lesson["status"] for lesson in saved["lessons"]], ["adopted", "adopted"])
        self.assertEqual(self.ok("status", now=T0)["stale_lessons"], ["L-001"])
        self.assertEqual(self.ok("mark-reviewed", now=hours(1))["newly_stale"], [])
        self.assertIn("| L-001 | adopted | stale | none |", (self.root / "learnings.md").read_text())
        self.assertIn("| L-002 | adopted | current | none |", (self.root / "learnings.md").read_text())

    def test_lane_share(self) -> None:
        self.post("7000000001", hours(1))
        self.post("7000000002", hours(2), lane="other")
        share = self.ok("lane-share")
        self.assertEqual((share["main"], share["window"]), (1, 2))


class ApiData(LoopCase):
    def item(self, item_id: str, created: str, kind: str = "reply", conv: str | None = None, **organic) -> dict:
        base = {"impressions": 100, "likes": 2, "replies": 0, "reposts": 0, "profile_visits": 1, "url_clicks": 0}
        base.update(organic)
        return {"id": item_id, "kind": kind, "created_at": created, "conversation_id": conv or item_id,
                "topics": ["Technology"], "text": "a reply",
                "public": {"impressions": base["impressions"], "likes": base["likes"], "replies": 0, "reposts": 0,
                           "quotes": 0, "bookmarks": 1},
                "organic": base}

    def activity(self, stage: str, observed: str, items: list[dict], cursor: dict | None = None) -> dict:
        data = {"stage": stage, "observed_at": observed, "items": items}
        if cursor:
            data["cursor"] = cursor
        return self.ok("record-activity", "--json", self.payload(data))

    def rows(self) -> dict:
        rows = {}
        for path in (self.root / "ledger" / "activity").glob("????-??.json"):
            rows.update(json.loads(path.read_text())["items"])
        return rows

    def write_runs(self, *lines: str) -> None:
        (self.root / "ledger").mkdir(exist_ok=True)
        (self.root / "ledger" / "runs.log").write_text("".join(line + "\n" for line in lines), encoding="utf-8")

    def test_status_health_reads_the_run_log(self) -> None:
        now = hours(100)
        self.assertIn("No daily run", self.ok("status", now=now)["health"]["warnings"][0])
        self.write_runs(f"{hours(99)} snapshot ok read48=0 final=0 followers=1 api_items=1 cost_usd=0.001")
        self.assertEqual(self.ok("status", now=now)["health"], {"warnings": []})
        self.write_runs(f"{hours(60)} snapshot ok read48=0", f"{hours(90)} snapshot failed error='credits'")
        warnings = self.ok("status", now=now)["health"]["warnings"]
        self.assertEqual(len(warnings), 2)
        self.assertIn("credits", warnings[1])

    def test_status_warns_of_a_final_read_about_to_be_lost(self) -> None:
        self.post("9700000001", T0)
        self.post("9700000002", T0)
        self.post("9700000003", hours(400))
        self.post("9700000004", hours(-200))
        self.activity("final", hours(27 * 24), [self.item("9700000002", T0, kind="original")])
        now = hours(650)  # 9700000001 and 9700000002 are 650h old; 9700000004 is past the cutoff
        self.write_runs(f"{hours(649)} snapshot ok read48=0")
        got = self.ok("status", now=now)["health"]["warnings"]
        self.assertEqual(len(got), 1, got)
        self.assertIn("9700000001", got[0])
        self.write_runs(f"{hours(599)} snapshot ok read48=0")
        self.assertEqual(self.ok("status", now=hours(600))["health"], {"warnings": []})  # 647h: not yet at risk

    def test_activity_rows_labels_and_cursor(self) -> None:
        made = self.activity("48h", hours(40), [self.item("9000000001", T0)], cursor={"read48_until": hours(4)})
        self.assertEqual(made["cursors"]["read48_until"], hours(4))
        self.assertEqual(self.rows()["9000000001"]["reads"]["48h"]["label"], "valid")
        self.activity("48h", hours(40), [self.item("9000000001", T0)])
        self.assertEqual(len(self.rows()), 1)
        self.activity("48h", hours(80), [self.item("9000000001", T0, impressions=999)])
        self.assertEqual(self.rows()["9000000001"]["reads"]["48h"]["organic"]["impressions"], 100)
        self.assertIn("unknown organic", self.fails("record-activity", "--json", self.payload(
            {"stage": "48h", "observed_at": hours(40), "items": [self.item("9000000002", T0, shares=3)]})))

    def due_reads(self, now: str, *extra: str) -> dict:
        return self.ok("due-reads", "--horizon-days", "29", *extra, now=now)

    def test_due_reads_first_run_returns_both_windows_with_their_cursors(self) -> None:
        now = hours(24 * 10)
        out = self.due_reads(now)
        self.assertEqual(out["now"], now)
        self.assertEqual(out["windows"], [
            {"stage": "48h", "start": hours(24 * 10 - 60), "end": hours(24 * 10 - 36), "fetch": True,
             "cursor": {"read48_until": hours(24 * 10 - 36)}},
            {"stage": "final", "start": hours(24 * 10 - 24 * 29), "end": hours(24 * 10 - 24 * 26), "fetch": True,
             "cursor": {"final_until": hours(24 * 10 - 24 * 26)}}])

    def test_due_reads_resumes_from_the_saved_cursors(self) -> None:
        self.activity("48h", hours(24 * 9), [], cursor={"read48_until": hours(24 * 9), "final_until": hours(-24 * 17)})
        windows = self.due_reads(hours(24 * 10))["windows"]
        self.assertEqual((windows[0]["start"], windows[1]["start"]), (hours(24 * 9), hours(-24 * 17)))

    def test_due_reads_clamps_an_old_cursor_to_the_horizon(self) -> None:
        self.activity("48h", hours(0), [], cursor={"read48_until": hours(-24 * 40), "final_until": hours(-24 * 40)})
        windows = self.due_reads(hours(24 * 10))["windows"]
        floor = hours(24 * 10 - 24 * 29)
        self.assertEqual((windows[0]["start"], windows[1]["start"]), (floor, floor))

    def test_due_reads_keeps_an_empty_48h_window_and_drops_an_empty_final_window(self) -> None:
        now = hours(24 * 10)
        self.activity("48h", now, [], cursor={"read48_until": hours(24 * 10 - 36), "final_until": hours(24 * 10 - 24 * 26)})
        windows = self.due_reads(now)["windows"]
        self.assertEqual([w["stage"] for w in windows], ["48h"])
        self.assertFalse(windows[0]["fetch"])
        self.assertEqual(windows[0]["cursor"], {"read48_until": hours(24 * 10 - 36)})

    def test_due_reads_rounds_the_clock_down_to_whole_seconds(self) -> None:
        out = self.due_reads("2026-10-11T00:00:00.750Z")
        self.assertEqual(out["now"], "2026-10-11T00:00:00Z")
        self.assertEqual(out["windows"][1]["start"], hours(24 * 10 - 24 * 29))

    def test_due_reads_backfill_returns_the_cursor_pair(self) -> None:
        out = self.ok("due-reads", "--backfill", "--fetched-at", hours(24 * 10), "--since", T0)
        self.assertEqual(out, {"stage": "backfill", "self_handles": ["exitzerocode", "awakenluke"],
                               "cursor": {"read48_until": hours(24 * 10 - 36), "final_until": T0}})

    def test_due_reads_writes_nothing(self) -> None:
        state = self.root / "loop" / "state.json"
        before = state.read_text()
        self.due_reads(hours(24 * 10))
        self.ok("due-reads", "--backfill", "--fetched-at", hours(24 * 10), "--since", T0)
        self.assertEqual(state.read_text(), before)

    def test_due_reads_needs_the_horizon_or_the_backfill_facts(self) -> None:
        self.assertIn("--horizon-days", self.fails("due-reads", now=hours(24 * 10)))
        self.assertIn("--fetched-at", self.fails("due-reads", "--backfill", now=hours(24 * 10)))

    def test_follow_credit_is_counts_only_and_a_lower_bound(self) -> None:
        self.ok("record-interactions", "--json", self.payload({
            "observed_at": hours(1), "self_ids": ["111"], "since_id": "9000000050",
            "mentions": [{"id": "9000000050", "author_id": "501", "conversation_id": "9000000010",
                          "replied_to": "9000000010", "created_at": hours(1)},
                         {"id": "9000000051", "author_id": "111", "conversation_id": "9000000010",
                          "replied_to": "9000000010", "created_at": hours(1)}],
            "reply_targets": [{"item_id": "9000000020", "user_id": "502", "at": hours(1)}]}))
        follow = lambda at, ids: self.ok("record-followers", "--json", self.payload(
            {"observed_at": at, "self_ids": ["111"], "ids": ids, "total": len(ids)}))
        self.assertTrue(follow(hours(2), ["400", "111"])["baseline"])
        day = follow(hours(26), ["400", "501", "502", "503", "111"])
        self.assertEqual((day["new"], day["lost"], day["unattributed"]), (3, 0, 1))
        self.assertEqual(day["attributed"], {"9000000010": 1, "9000000020": 1})
        again = follow(hours(30), ["400", "501", "502", "503", "111"])
        self.assertEqual(again["new"], 3)
        self.assertLessEqual(len(list((self.root / "loop" / "followers").glob("followers-*.json"))), 2)
        committed = (self.root / "ledger" / "activity" / "account.json").read_text()
        for private in ("501", "502", "503", "400"):
            self.assertNotIn(f'"{private}"', committed)

    def test_export_gives_exact_follows_for_post_and_its_cards(self) -> None:
        self.post("9500000001", T0)
        self.activity("48h", hours(40), [self.item("9500000001", T0, kind="original"),
                                         self.item("9500000002", T0, kind="thread_card", conv="9500000001"),
                                         self.item("9500000003", T0, conv="7000000000")])
        export = self.root / "export.csv"
        export.write_text("\ufeffPost id,Date,Post text,Impressions,Likes,Replies,Reposts,Bookmarks,Shares,New follows,Profile visits\n"
                          "9500000001,x,t,855,24,32,0,0,0,13,20\n9500000002,x,t,10,0,0,0,0,0,1,0\n"
                          "9500000003,x,t,40,0,0,0,0,0,2,0\n9599999999,x,t,1,0,0,0,0,0,0,0\n", encoding="utf-8")
        made = self.ok("record-export", "--csv", str(export))
        self.assertEqual((made["recorded"], made["not_in_activity"]), (3, 1))
        row = next(l for l in (self.root / "ledger" / "SUMMARY.md").read_text().splitlines() if "s001" in l)
        self.assertEqual(row.rstrip(" |").split("|")[-2].strip(), "14", row)
        bad = self.root / "other.csv"
        bad.write_text("a,b\n1,2\n", encoding="utf-8")
        self.assertIn("not an X analytics", self.fails("record-export", "--csv", str(bad)))

    def test_eligibility_block_tracks_both_thresholds(self) -> None:
        self.activity("48h", hours(40), [self.item("9600000001", T0, kind="original", impressions=900),
                                         self.item("9600000002", T0, kind="reply", impressions=5000)])
        self.ok("record-followers", "--json", self.payload(
            {"observed_at": hours(41), "ids": ["1", "2", "3"], "total": 3, "verified": 2}))
        made = self.ok("record-eligibility", "--verified-followers", "26", "--qualified-impressions", "337",
                       now=hours(42))
        self.assertEqual((made["verified_followers"], made["qualified_impressions"]), (26, 337))
        self.assertIn("whole number", self.fails("record-eligibility", "--verified-followers", "x",
                                                 "--qualified-impressions", "1"))
        summary = (self.root / "ledger" / "SUMMARY.md").read_text()
        self.assertIn("## Original Content Rewards", summary)
        self.assertIn("26 verified followers, 337 qualified impressions", summary)
        self.assertIn("Verified followers from the daily read: 2 of 500", summary)
        self.assertIn("last 90 days: 900.", summary)  # the reply's 5,000 never counts
        self.assertIn("qualified at the last screen reading: 37%", summary)

    def test_interactions_prune_old_people(self) -> None:
        self.ok("record-interactions", "--json", self.payload({
            "observed_at": hours(0), "reply_targets": [{"item_id": "9000000020", "user_id": "600", "at": hours(0)}]}))
        later = self.ok("record-interactions", "--json", self.payload({"observed_at": hours(24 * 8)}))
        self.assertEqual(later["people"], 0)

    def test_auto_post_replaced_by_posted_record(self) -> None:
        self.post("9100000001", T0, auto=True, retrospective=True, made_in_repo=False, lane="other", format="other")
        self.snap("9100000001", hours(40), 50)
        replaced = self.post("9100000001", T0, format="build-log")
        self.assertTrue(replaced["recorded"])
        post = json.loads((self.root / "ledger" / "9100000001.json").read_text())
        self.assertEqual((post["format"], post["auto"], len(post["snapshots"])), ("build-log", False, 1))
        self.assertFalse(self.post("9100000001", T0)["recorded"])

    def test_set_lane_logs_amendment(self) -> None:
        self.post("9200000001", T0, lane="other")
        self.assertTrue(self.ok("set-lane", "--root-id", "9200000001", "--lane", "main", "--reason", "builder question")["changed"])
        post = json.loads((self.root / "ledger" / "9200000001.json").read_text())
        self.assertEqual((post["lane"], post["amendments"][0]["from"]), ("main", "other"))
        self.assertIn("main or other", self.fails("set-lane", "--root-id", "9200000001", "--lane", "unset", "--reason", "x"))

    def test_api_snapshot_and_final_read(self) -> None:
        self.post("9300000001", T0)
        data = {"root_id": "9300000001", "observed_at": hours(40), "source": "api", "outside_replies": 2,
                "root": {"views": 300, "likes": 3, "reposts": 0, "quotes": 0, "replies": 5, "bookmarks": 1},
                "organic": {"impressions": 280, "likes": 3, "replies": 5, "reposts": 0, "profile_visits": 2, "url_clicks": 0}}
        made = self.ok("record-snapshot", "--json", self.payload(data))
        self.assertEqual(made["kind"], "valid")
        early_final = dict(data, observed_at=hours(24 * 20), stage="final")
        self.assertIn("26 to 29 days", self.fails("record-snapshot", "--json", self.payload(early_final)))
        final = dict(data, observed_at=hours(24 * 27), stage="final")
        self.assertEqual(self.ok("record-snapshot", "--json", self.payload(final))["kind"], "final")
        self.assertFalse(self.ok("record-snapshot", "--json", self.payload(final))["recorded"])
        post = json.loads((self.root / "ledger" / "9300000001.json").read_text())
        self.assertEqual(post["snapshots"][0]["outside_replies"], 2)
        self.assertEqual(post["snapshots"][0]["outside_repliers"], [])
        self.assertEqual(loop.best_snapshot(post)["kind"], "valid")

    def test_summary_shows_organic_and_account(self) -> None:
        self.post("9400000001", T0)
        root = self.item("9400000001", T0, kind="original", impressions=90, profile_visits=3)
        root["public"]["impressions"] = 100
        self.activity("48h", hours(40), [root, self.item("9400000002", hours(1), conv="9400000001", impressions=60)])
        self.ok("record-interactions", "--json", self.payload({
            "observed_at": hours(41), "reply_targets": [{"item_id": "9400000002", "user_id": "700", "at": hours(41)}]}))
        for at, ids in ((hours(41), ["1"]), (hours(66), ["1", "700"])):
            self.ok("record-followers", "--json", self.payload({"observed_at": at, "ids": ids, "total": len(ids)}))
        summary = (self.root / "ledger" / "SUMMARY.md").read_text()
        row = next(line for line in summary.splitlines() if "s001" in line)
        self.assertIn("| 90 | 10% | 3 |", row)
        self.assertEqual(row.rstrip(" |").split("|")[-2].strip(), "≥1", row)
        self.assertIn("## Account", summary)
        self.assertIn("1 new, 0 lost; 1 of the new credited", summary)


class Reference(LoopCase):
    def test_set_reference_records_the_status_the_time_and_the_files(self) -> None:
        stale = self.ok("set-reference", "--status", "stale",
                        "--files", "reference/x-algorithm.md,reference/x-api.md", now=hours(3))
        self.assertEqual(stale, {"reference": {
            "status": "stale", "checked_at": hours(3),
            "changed_files": ["reference/x-algorithm.md", "reference/x-api.md"]}})
        current = self.ok("set-reference", "--status", "current", now=hours(4))
        self.assertEqual(current, {"reference": {"status": "current", "checked_at": hours(4), "changed_files": []}})
        state = json.loads((self.root / "loop" / "state.json").read_text())
        self.assertEqual(state["reference"], current["reference"])

    def test_set_reference_refuses_a_bad_status_and_leaves_the_saved_one(self) -> None:
        self.assertEqual(self.fails("set-reference", "--status", "gone", now=hours(3)),
                         "status must be current or stale")
        state = json.loads((self.root / "loop" / "state.json").read_text())
        self.assertEqual(state["reference"], {"status": "current", "checked_at": T0, "changed_files": []})


class Preferences(LoopCase):
    def test_needs_three_posts_with_preference_edits(self) -> None:
        for i in range(3):
            self.post(f"800000000{i}", hours(i), edits=[{"class": "preference", "note": "shorter title"}])
        self.post("8000000009", hours(9), edits=[{"class": "violation", "note": "VERIFY left in"}])
        self.assertIn("at least 3", self.fails("add-preference", "--statement", "shorter titles",
                                               "--evidence", "8000000000,8000000001"))
        self.assertIn("no recorded preference", self.fails(
            "add-preference", "--statement", "x", "--evidence", "8000000000,8000000001,8000000009"))
        made = self.ok("add-preference", "--statement", "shorter titles",
                       "--evidence", "8000000000,8000000001,8000000002")
        self.assertEqual(made["status"], "adopted")


class Rules(LoopCase):
    def setUp(self) -> None:
        super().setUp()
        for args in (["init", "-q"], ["config", "user.email", "t@example.com"], ["config", "user.name", "t"],
                     ["config", "commit.gpgsign", "false"]):
            subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)
        skill = self.root / ".claude" / "skills" / "format-single-tip" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("v1\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=self.root, check=True, capture_output=True)
        self.skill = skill
        state_path = self.root / "loop" / "state.json"
        state = json.loads(state_path.read_text())
        state["lessons"].append({"id": "L-001", "experiment": "E-001", "statement": "short roots",
                                 "status": "adopted", "evidence": ["1"], "reference_facts": [],
                                 "created_at": T0, "last_evidence_at": T0})
        state["lessons"].append({"id": "L-002", "experiment": "E-002", "statement": "no",
                                 "status": "no_effect", "evidence": ["2"], "reference_facts": [],
                                 "created_at": T0, "last_evidence_at": T0})
        state_path.write_text(json.dumps(state))
        self.rel = ".claude/skills/format-single-tip/SKILL.md"

    def test_apply_then_undo(self) -> None:
        self.skill.write_text("v2\n", encoding="utf-8")
        applied = self.ok("commit-rule", "--lesson", "L-001", "--files", self.rel, now=T0)
        self.assertEqual(len(applied["committed"]), 40)
        undone = self.ok("undo", "--lesson", "L-001", now=T0)
        self.assertEqual(undone["reverted"], applied["committed"])
        self.assertEqual(self.skill.read_text(), "v1\n")
        state = json.loads((self.root / "loop" / "state.json").read_text())
        self.assertTrue(state["rules"][0]["undone"])
        self.assertIn("| L-001 | adopted | current | reverted |", (self.root / "learnings.md").read_text())

    def test_learnings_show_the_basis_of_an_adopted_lesson_only(self) -> None:
        self.ok("mark-reviewed", now=T0)
        rows = {line.split("|")[1].strip(): line for line in
                (self.root / "learnings.md").read_text().splitlines() if line.startswith("| L-")}
        self.assertIn("| Basis |", (self.root / "learnings.md").read_text())
        self.assertIn("experiment E-001 is not in the ledger", rows["L-001"])
        self.assertTrue(rows["L-002"].rstrip(" |").endswith("| –"), rows["L-002"])

    def test_rule_commit_body_carries_the_basis(self) -> None:
        self.skill.write_text("v2\n", encoding="utf-8")
        self.ok("commit-rule", "--lesson", "L-001", "--files", self.rel)
        body = subprocess.run(["git", "log", "-1", "--format=%B"], cwd=self.root, capture_output=True,
                              text=True, check=True).stdout
        self.assertIn("Provisional: experiment E-001 is not in the ledger", body)
        self.assertIn("Evidence: 1", body)

    def test_a_stale_adopted_lesson_can_still_change_a_rule(self) -> None:
        path = self.root / "loop" / "state.json"
        state = json.loads(path.read_text())
        state["lessons"][0]["last_evidence_at"] = hours(-24 * 50)
        path.write_text(json.dumps(state))
        self.ok("mark-reviewed", now=T0)
        self.skill.write_text("v2\n", encoding="utf-8")
        applied = self.ok("commit-rule", "--lesson", "L-001", "--files", self.rel, now=T0)
        self.assertEqual(len(applied["committed"]), 40)
        self.assertEqual(json.loads(path.read_text())["lessons"][0]["status"], "adopted")
        self.assertIn("| L-001 | adopted | stale | applied |", (self.root / "learnings.md").read_text())

    def test_only_adopted_lessons_apply(self) -> None:
        self.skill.write_text("v2\n", encoding="utf-8")
        self.assertIn("only adopted", self.fails("commit-rule", "--lesson", "L-002", "--files", self.rel))

    def test_rule_files_only(self) -> None:
        (self.root / "AGENTS.md").write_text("x", encoding="utf-8")
        self.assertIn("not a rule file", self.fails("commit-rule", "--lesson", "L-001", "--files", "AGENTS.md"))

    def test_undo_refuses_dirty_files(self) -> None:
        self.skill.write_text("v2\n", encoding="utf-8")
        self.ok("commit-rule", "--lesson", "L-001", "--files", self.rel)
        self.skill.write_text("v3 uncommitted\n", encoding="utf-8")
        self.assertIn("uncommitted", self.fails("undo", "--lesson", "L-001"))
        self.assertEqual(self.skill.read_text(), "v3 uncommitted\n")

    def test_undo_aborts_a_conflict_and_reverts_nothing(self) -> None:
        self.skill.write_text("v2\n", encoding="utf-8")
        applied = self.ok("commit-rule", "--lesson", "L-001", "--files", self.rel, now=T0)
        self.skill.write_text("later\n", encoding="utf-8")
        subprocess.run(["git", "add", "--", self.rel], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-qm", "later"], cwd=self.root, check=True, capture_output=True)
        error = self.fails("undo", "--lesson", "L-001")
        self.assertEqual(error, f"revert of {applied['committed'][:8]} conflicted with a later change; "
                         "nothing was reverted")
        self.assertEqual(self.skill.read_text(encoding="utf-8"), "later\n")
        rule = json.loads((self.root / "loop" / "state.json").read_text())["rules"][0]
        self.assertEqual((rule["undone"], rule["revert_commit"]), (False, None))
        status = subprocess.run(["git", "status"], cwd=self.root, capture_output=True, text=True, check=False)
        self.assertNotIn("currently reverting", status.stdout)
        revert = subprocess.run(["git", "rev-parse", "--verify", "REVERT_HEAD"], cwd=self.root,
                                capture_output=True, text=True, check=False)
        self.assertNotEqual(revert.returncode, 0)

    def git(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_commit_data_reports_a_clean_tree_and_commits_only_the_sweep(self) -> None:
        self.git("add", "-A")
        self.git("commit", "-qm", "sync")
        self.ok("commit-data", "--message", "render")
        self.git("add", "-A")
        self.git("commit", "-qm", "views")
        head = self.git("rev-parse", "HEAD").stdout.strip()
        self.assertEqual(self.ok("commit-data", "--message", "weekly review"),
                         {"committed": None, "reason": "nothing changed"})
        self.assertEqual(self.git("rev-parse", "HEAD").stdout.strip(), head)
        (self.root / "reviews").mkdir()
        (self.root / "reviews" / "week.md").write_text("week\n", encoding="utf-8")
        (self.root / "notes.md").write_text("nope\n", encoding="utf-8")
        committed = self.ok("commit-data", "--message", "weekly review 2026-W40")
        self.assertEqual(self.git("log", "-1", "--format=%s").stdout, "chore(data): weekly review 2026-W40\n")
        self.assertEqual(self.git("rev-parse", "HEAD").stdout.strip(), committed["committed"])
        self.assertEqual(self.git("show", "--name-only", "--format=", "HEAD").stdout.splitlines(),
                         ["reviews/week.md"])
        self.assertEqual(self.git("ls-files", "notes.md").stdout, "")

    def test_apply_does_not_sweep_other_files(self) -> None:
        other = self.root / "notes.md"
        other.write_text("draft", encoding="utf-8")
        self.skill.write_text("v2\n", encoding="utf-8")
        self.ok("commit-rule", "--lesson", "L-001", "--files", self.rel)
        tracked = subprocess.run(["git", "ls-files", "notes.md"], cwd=self.root,
                                 capture_output=True, text=True).stdout
        self.assertEqual(tracked, "")


HEAD = "<!-- Generated by scripts/loop.py. Do not edit; it is rewritten after every loop command. -->\n\n"
SUMMARY_GOLDEN = HEAD + (
    "# Ledger summary\n\n"
    "Times are Australia/Brisbane. Views and Snapshot come from the 36–60 hour snapshot, else the latest late one. "
    "Organic, Non-organic and Visits come from the X API read at 36–60 hours, else the September backfill. "
    "Follows are from X's analytics export (the post and its thread cards) when one has been recorded; "
    "≥n is the lower bound from matching new followers to who engaged. "
    "A leading ≥ means X search returned fewer reply authors than the reply count.\n\n"
    "| Posted | Slug | Format | Lane | Experiment | Views | Organic | Non-organic | Visits | Bookmarks | "
    "Outside replies | Follows | Snapshot |\n"
    "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|\n"
    "| Thu 10 Sep 14:00 | s000 | single-tip | main | retro | 1000 | – | – | – | 100 | – | – | late 100h |\n"
    "| Thu 10 Sep 15:00 | s001 | single-tip | main | retro | 1000 | – | – | – | 200 | – | – | late 100h |\n"
    "| Thu 10 Sep 16:00 | s002 | single-tip | main | retro | 1000 | – | – | – | 300 | – | – | late 100h |\n"
    "| Thu 01 Oct 20:00 | s000 | single-tip | main | E-001 treatment | 1000 | – | – | – | 400 | – | – | valid 40h |\n"
    "| Fri 02 Oct 06:00 | s001 | single-tip | main | – | – | – | – | – | – | – | – | pending |\n")
EXPERIMENTS_GOLDEN = HEAD + (
    "# Experiments\n\nOne runs at a time. Rules are fixed when it opens.\n\n"
    "## E-001: Standalone beats a thread?\n\n"
    "- **Status:** testing\n- **Treatment:** standalone post\n- **Compared with:** 3-card thread\n"
    "- **Primary outcome:** root bookmarks at the 36–60 hour snapshot\n"
    "- **Bar to beat:** 300 (1.5 × cohort median 200)\n"
    "- **Cohort, frozen 2026-10-01:** 2000000000 (100, late), 2000000001 (200, late), 2000000002 (300, late)\n\n")


class ReadWindowRules(LoopCase):
    """Pins the 48h and Final read rules so they can move without changing."""

    def kind_at(self, root_id: str, h: float) -> str:
        return self.snap(root_id, hours(h), 5)["kind"]

    def test_48h_window_edges_are_inclusive(self) -> None:
        for i, (h, kind) in enumerate([(35.99, "early"), (36, "valid"), (60, "valid"), (60.01, "late")]):
            root_id = f"400000000{i}"
            self.post(root_id, T0)
            self.assertEqual(self.kind_at(root_id, h), kind, h)

    def final_payload(self, root_id: str, days: float) -> dict:
        return {"root_id": root_id, "observed_at": hours(24 * days), "stage": "final",
                "root": {"views": 1, "likes": 0, "reposts": 0, "quotes": 0, "replies": 0, "bookmarks": 0}}

    def test_final_read_must_be_26_to_29_days_old(self) -> None:
        self.post("4000000010", T0)
        for days in (26 - 0.01, 29 + 0.01, 45):
            error = self.fails("record-snapshot", "--json", self.payload(self.final_payload("4000000010", days)))
            self.assertIn("26 to 29 days", error, days)
        for i, days in enumerate((26, 27, 29)):
            root_id = f"40000000{20 + i}"
            self.post(root_id, T0)
            made = self.ok("record-snapshot", "--json", self.payload(self.final_payload(root_id, days)))
            self.assertEqual(made["kind"], "final", days)

    def test_final_activity_read_must_be_26_to_29_days_old(self) -> None:
        item = {"id": "4000000040", "kind": "original", "created_at": T0, "conversation_id": "4000000040",
                "public": {}, "organic": {"impressions": 10}}
        for days in (26 - 0.01, 29 + 0.01):
            data = {"stage": "final", "observed_at": hours(24 * days), "items": [item]}
            self.assertIn("26 to 29 days", self.fails("record-activity", "--json", self.payload(data)), days)
        self.assertEqual(list((self.root / "ledger" / "activity").glob("2*.json")), [])
        for days in (26, 29):
            data = {"stage": "final", "observed_at": hours(24 * days), "items": [item]}
            self.assertEqual(self.ok("record-activity", "--json", self.payload(data))["recorded"], 1)

    def test_final_max_days_matches_the_x_organic_horizon(self) -> None:
        import x_api
        from loop_core import reads
        self.assertEqual(reads.FINAL_MAX_DAYS, x_api.ORGANIC_DAYS)

    def test_a_valid_snapshot_is_refused_once_the_post_is_missed(self) -> None:
        self.post("4000000030", T0)
        self.assertEqual(self.ok("mark-missed", now=hours(61))["marked_missed"], ["4000000030"])
        self.assertIn("missed", self.fails("record-snapshot", "--json", self.payload(
            {"root_id": "4000000030", "observed_at": hours(40),
             "root": {"views": 1, "likes": 0, "reposts": 0, "quotes": 0, "replies": 0, "bookmarks": 0}})))

    def test_due_classifies_at_the_window_edges(self) -> None:
        for i, h in enumerate((35.99, 36, 60, 60.01)):
            self.post(f"400000004{i}", hours(-h))
        due = self.ok("due", now=T0)
        ids = lambda key: sorted(r["root_id"] for r in due[key])
        self.assertEqual(ids("pending"), ["4000000040"])
        self.assertEqual(ids("due"), ["4000000041", "4000000042"])
        self.assertEqual(ids("missed"), ["4000000043"])
        self.assertEqual(due["window_hours"], [36.0, 60.0])

    def test_due_skips_a_post_with_a_valid_snapshot_or_marked_missed(self) -> None:
        self.post("4000000050", hours(-40))
        self.snap("4000000050", T0, 5)
        self.post("4000000051", hours(-70))
        self.ok("mark-missed", now=T0)
        due = self.ok("due", now=T0)
        self.assertEqual((due["due"], due["missed"], due["pending"]), ([], [], []))

    def test_mark_missed_waits_past_60h_and_spares_any_snapshot(self) -> None:
        self.post("4000000060", hours(-60))
        self.post("4000000061", hours(-60.01))
        self.post("4000000062", hours(-100))
        self.snap("4000000062", T0, 5)
        self.assertEqual(self.ok("mark-missed", now=T0)["marked_missed"], ["4000000061"])

    def test_best_snapshot_prefers_valid_then_the_last_late_one(self) -> None:
        self.post("4000000070", T0)
        self.snap("4000000070", hours(70), 1)
        self.snap("4000000070", hours(80), 2)
        self.snap("4000000070", hours(90), 3)
        post = json.loads((self.root / "ledger" / "4000000070.json").read_text())
        self.assertEqual(loop.best_snapshot(post)["age_hours"], 90)
        self.snap("4000000070", hours(40), 4)
        post = json.loads((self.root / "ledger" / "4000000070.json").read_text())
        self.assertEqual(loop.best_snapshot(post)["kind"], "valid")

    def test_due_reads_windows_at_a_fixed_clock(self) -> None:
        now = hours(24 * 40)
        plan = self.ok("due-reads", "--horizon-days", "30", now=now)
        self.assertEqual(plan["windows"], [
            {"stage": "48h", "start": hours(24 * 40 - 60), "end": hours(24 * 40 - 36), "fetch": True,
             "cursor": {"read48_until": hours(24 * 40 - 36)}},
            {"stage": "final", "start": hours(24 * 10), "end": hours(24 * 14), "fetch": True,
             "cursor": {"final_until": hours(24 * 14)}}])
        backfill = self.ok("due-reads", "--backfill", "--fetched-at", now, "--since", hours(24 * 5))
        self.assertEqual(backfill["cursor"], {"read48_until": hours(24 * 40 - 36), "final_until": hours(24 * 5)})

    def test_generated_views_are_pinned(self) -> None:
        for i, value in enumerate((100, 200, 300)):
            root_id = f"20000000{i:02d}"
            self.post(root_id, hours(-500 + i), retrospective=True, made_in_repo=False)
            self.snap(root_id, hours(-400 + i), 1000, bookmarks=value)
        self.ok("open-experiment", "--json", self.payload({
            "question": "Standalone beats a thread?", "treatment": "standalone post",
            "control": "3-card thread", "primary": "bookmarks",
            "cohort": ["2000000000", "2000000001", "2000000002"]}), now=T0)
        self.post("3000000000", hours(10), experiment="E-001", arm="treatment")
        self.snap("3000000000", hours(50), 1000, bookmarks=400)
        self.post("3000000001", hours(20))
        self.assertEqual((self.root / "ledger" / "SUMMARY.md").read_text(), SUMMARY_GOLDEN)
        self.assertEqual((self.root / "experiments.md").read_text(), EXPERIMENTS_GOLDEN)

    def test_view_prose_follows_the_window_constants(self) -> None:
        from loop_core import reads
        self.post("5000000000", T0)
        real = reads.SNAPSHOT_MAX_H
        reads.SNAPSHOT_MAX_H = 72.0
        self.addCleanup(setattr, reads, "SNAPSHOT_MAX_H", real)
        self.post("5000000001", T0)  # any command re-renders the views
        summary = (self.root / "ledger" / "SUMMARY.md").read_text()
        self.assertIn("the 36–72 hour snapshot", summary)
        self.assertIn("read at 36–72 hours", summary)
        self.assertNotIn("36–60", summary)


def loop_sources(scripts: Path) -> list[Path]:
    """loop.py and every module it loads from loop_core."""
    return [scripts / "loop.py", *sorted((scripts / "loop_core").rglob("*.py"))]


class Isolation(unittest.TestCase):
    def offences(self, paths: list[Path]) -> tuple[set[str], list[Path]]:
        from test_scripts import FORBIDDEN_TOP, _imported_tops, _reads_environ
        network = {name for path in paths for name in _imported_tops(path) & FORBIDDEN_TOP}
        return network, [path for path in paths if _reads_environ(path)]

    def test_no_network_imports_or_environment(self) -> None:
        sources = loop_sources(REPO / "scripts")
        self.assertGreater(len(sources), 1)
        self.assertEqual(self.offences(sources), (set(), []))

    def test_loop_core_writes_no_files(self) -> None:
        """loop.py is the only writer; loop_core modules stay pure."""
        from test_scripts import _writes_files
        core = sorted((REPO / "scripts" / "loop_core").rglob("*.py"))
        self.assertGreater(len(core), 1)
        self.assertEqual([p for p in core if _writes_files(p)], [])

    def test_write_scan_catches_writes_and_io_imports(self) -> None:
        from test_scripts import _writes_files
        cases = {"write_text": "p.write_text('x')\n", "unlink": "p.unlink()\n", "path_replace": "p.replace(q)\n",
                 "os_replace": "import os\nos.replace(a, b)\n", "open_w": "open('f', 'w')\n",
                 "open_kw": "open('f', mode='a')\n", "open_var": "open('f', mode)\n",
                 "subprocess": "import subprocess\n", "tempfile": "from tempfile import mkstemp\n"}
        clean = {"read": "open('f')\nopen('f', 'r')\nPath('f').read_text()\n", "pure": "x = 1 + 1\n",
                 "str_replace": "value.replace('Z', '+00:00')\n"}
        with tempfile.TemporaryDirectory() as tmp:
            for name, source in {**cases, **clean}.items():
                path = Path(tmp) / f"{name}.py"
                path.write_text(source)
                self.assertEqual(_writes_files(path), name in cases, name)

    def test_scan_reaches_nested_modules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scripts = Path(tmp)
            (scripts / "loop.py").write_text("import json\n")
            nested = scripts / "loop_core" / "deep"
            nested.mkdir(parents=True)
            (nested / "leak.py").write_text("import urllib.request\nimport os\nos.environ\n")
            network, environ = self.offences(loop_sources(scripts))
            self.assertEqual(network, {"urllib"})
            self.assertEqual(environ, [nested / "leak.py"])


if __name__ == "__main__":
    unittest.main()
