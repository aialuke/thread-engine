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

    def snap(self, root_id: str, observed_at: str, views: int | None, repliers=None) -> dict:
        data = {"root_id": root_id, "observed_at": observed_at,
                "root": {"views": views, "likes": 1, "reposts": 0, "quotes": 0, "replies": 1, "bookmarks": 0},
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


class Experiments(LoopCase):
    def seed_cohort(self, values=(100, 200, 300)) -> list[str]:
        ids = []
        for i, value in enumerate(values):
            root_id = f"20000000{i:02d}"
            self.post(root_id, hours(-500 + i), retrospective=True, made_in_repo=False)
            self.snap(root_id, hours(-400 + i), value)
            ids.append(root_id)
        return ids

    def open(self, cohort: list[str]) -> dict:
        return self.ok("open-experiment", "--json", self.payload({
            "question": "Standalone beats a thread?", "treatment": "standalone post",
            "control": "3-card thread", "cohort": cohort}), now=T0)

    def treatment(self, start: int, values: list[int]) -> None:
        for i, value in enumerate(values):
            root_id = f"30000000{start + i:02d}"
            posted = hours(10 * (start + i))
            self.post(root_id, posted, experiment="E-001", arm="treatment")
            self.snap(root_id, hours(40, posted), value)

    def test_cohort_frozen_median_and_threshold(self) -> None:
        opened = self.open(self.seed_cohort())
        self.assertEqual(opened["cohort_median"], 200)
        self.assertEqual(opened["threshold"], 300)

    def test_cohort_too_small(self) -> None:
        ids = self.seed_cohort((100, 200))
        error = self.fails("open-experiment", "--json", self.payload({
            "question": "q", "treatment": "t", "control": "c", "cohort": ids}))
        self.assertIn("at least 3", error)

    def test_one_experiment_at_a_time(self) -> None:
        ids = self.seed_cohort()
        self.open(ids)
        self.assertIn("one at a time", self.fails("open-experiment", "--json", self.payload({
            "question": "q", "treatment": "t", "control": "c", "cohort": ids})))

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
            self.snap(root_id, hours(40, posted), 900)
        self.assertEqual(self.ok("evaluate", now=hours(200))["events"], [])

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

    def test_lane_share(self) -> None:
        self.post("7000000001", hours(1))
        self.post("7000000002", hours(2), lane="other")
        share = self.ok("lane-share")
        self.assertEqual((share["main"], share["window"]), (1, 2))


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
        skill = self.root / ".grok" / "skills" / "formats" / "single-tip" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("v1\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=self.root, check=True, capture_output=True)
        self.skill = skill
        state_path = self.root / "loop" / "state.json"
        state = json.loads(state_path.read_text())
        state["lessons"].append({"id": "L-001", "experiment": "E-001", "statement": "short roots",
                                 "status": "adopted", "evidence": ["1"], "reference_facts": [],
                                 "created_at": T0, "last_evidence_at": T0, "rule_state": "none"})
        state["lessons"].append({"id": "L-002", "experiment": "E-002", "statement": "no",
                                 "status": "no_effect", "evidence": ["2"], "reference_facts": [],
                                 "created_at": T0, "last_evidence_at": T0, "rule_state": "none"})
        state_path.write_text(json.dumps(state))
        self.rel = ".grok/skills/formats/single-tip/SKILL.md"

    def test_apply_then_undo(self) -> None:
        self.skill.write_text("v2\n", encoding="utf-8")
        applied = self.ok("commit-rule", "--lesson", "L-001", "--files", self.rel, now=T0)
        self.assertEqual(len(applied["committed"]), 40)
        undone = self.ok("undo", "--lesson", "L-001", now=T0)
        self.assertEqual(undone["reverted"], applied["committed"])
        self.assertEqual(self.skill.read_text(), "v1\n")
        state = json.loads((self.root / "loop" / "state.json").read_text())
        self.assertEqual(state["lessons"][0]["rule_state"], "reverted")

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

    def test_apply_does_not_sweep_other_files(self) -> None:
        other = self.root / "notes.md"
        other.write_text("draft", encoding="utf-8")
        self.skill.write_text("v2\n", encoding="utf-8")
        self.ok("commit-rule", "--lesson", "L-001", "--files", self.rel)
        tracked = subprocess.run(["git", "ls-files", "notes.md"], cwd=self.root,
                                 capture_output=True, text=True).stdout
        self.assertEqual(tracked, "")


class Isolation(unittest.TestCase):
    def test_no_network_imports_or_environment(self) -> None:
        from test_scripts import FORBIDDEN_TOP, _imported_tops, _reads_environ
        path = REPO / "scripts" / "loop.py"
        self.assertEqual(_imported_tops(path) & FORBIDDEN_TOP, set())
        self.assertFalse(_reads_environ(path))


if __name__ == "__main__":
    unittest.main()
