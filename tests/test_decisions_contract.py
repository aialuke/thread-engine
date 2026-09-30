#!/usr/bin/env python3
"""Pins what scripts/loop.py does today in record-snapshot, record-post, evaluate and next-slot.

Written before the decisions moved into loop_core, so the move cannot change a message, an
output, the persisted bytes or which check wins. Everything goes through loop.main, with the
raw stdout, stderr and exit code and the bytes of loop/state.json and ledger/*.json.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from test_loop import REPO, T0, LoopCase, hours

from loop_core import experiments  # noqa: E402
import loop  # noqa: E402  (after test_loop: it puts scripts/ on the path)

LOOP = REPO / "scripts" / "loop.py"
ROOT_METRICS = {"views": 1, "likes": 0, "reposts": 0, "quotes": 0, "replies": 0, "bookmarks": 0}
FINAL_H = 24 * 27


class RawCase(LoopCase):
    def raw(self, *argv: str, now: str | None = None) -> tuple[int, str, str]:
        args = ["--root", str(self.root)]
        if now:
            args += ["--now", now]
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = loop.main([*args, *argv])
        return code, out.getvalue(), err.getvalue()

    def tree(self) -> dict[str, bytes]:
        files = [self.root / "loop" / "state.json", *sorted((self.root / "ledger").glob("*.json"))]
        return {str(f.relative_to(self.root)): f.read_bytes() for f in files if f.exists()}

    def refusal(self, *argv: str, now: str | None = None) -> str:
        """The exact stderr error of a refused command; the persisted files must not change."""
        before = self.tree()
        code, out, err = self.raw(*argv, now=now)
        self.assertEqual((code, out), (1, ""), err)
        self.assertEqual(self.tree(), before)
        return json.loads(err)["error"]

    def soft(self, *argv: str, now: str | None = None) -> dict:
        """A soft return: exit 0, stderr empty, no ledger or state bytes change."""
        before = self.tree()
        code, out, err = self.raw(*argv, now=now)
        self.assertEqual((code, err), (0, ""), out)
        self.assertEqual(self.tree(), before)
        return json.loads(out)

    def ledger_path(self, root_id: str) -> Path:
        return self.root / "ledger" / f"{root_id}.json"

    def edit_post(self, root_id: str, **change) -> None:
        path = self.ledger_path(root_id)
        data = json.loads(path.read_text())
        data.update(change)
        path.write_text(json.dumps(data, indent=2) + "\n")

    def edit_state(self, **change) -> None:
        path = self.root / "loop" / "state.json"
        data = json.loads(path.read_text())
        data.update(change)
        path.write_text(json.dumps(data, indent=2) + "\n")

    def state(self) -> dict:
        return json.loads((self.root / "loop" / "state.json").read_text())

    def lesson(self, lesson_id: str, status: str) -> dict:
        return {"id": lesson_id, "experiment": "E-001", "statement": "s", "status": status, "evidence": [],
                "reference_facts": [], "created_at": T0, "last_evidence_at": T0, "rule_state": "none"}

    def experiment(self, status: str) -> dict:
        """An experiment as open-experiment stores it, for tests that need one without a cohort."""
        return {"id": "E-001", "question": "q", "treatment": "t", "control": "c", "reference_facts": [],
                "primary": "bookmarks", "effect": 1.5, "size": 3, "cohort": [], "cohort_median": 200,
                "threshold": 300, "opened_at": T0, "status": status, "rounds": [], "closed_at": None}

    def snap_json(self, root_id: str, observed_at: str, **extra) -> str:
        return self.payload({"root_id": root_id, "observed_at": observed_at, "root": ROOT_METRICS, **extra})


class SnapshotAdmission(RawCase):
    ID = "1000000001"

    def setUp(self) -> None:
        super().setUp()
        self.post(self.ID, T0)

    def read(self, observed_at: str, **extra) -> str:
        return self.snap_json(self.ID, observed_at, **extra)

    def test_negative_age_is_refused(self) -> None:
        self.assertEqual(self.refusal("record-snapshot", "--json", self.read(hours(-1))),
                         "observed before the post existed")

    def test_final_age_is_refused_even_when_a_final_read_exists(self) -> None:
        self.ok("record-snapshot", "--json", self.read(hours(FINAL_H), stage="final"))
        self.assertEqual(self.refusal("record-snapshot", "--json", self.read(hours(10), stage="final")),
                         "a final read needs a post 26 to 29 days old")

    def test_a_final_duplicate_is_skipped_before_the_payload_is_validated(self) -> None:
        self.ok("record-snapshot", "--json", self.read(hours(FINAL_H), stage="final"))
        got = self.soft("record-snapshot", "--json", self.read(hours(FINAL_H + 1), stage="final", root=5))
        self.assertEqual(got, {"recorded": False, "reason": "final read already exists", "root_id": self.ID})

    def test_a_valid_duplicate_is_skipped_before_the_payload_is_validated(self) -> None:
        self.ok("record-snapshot", "--json", self.read(hours(48)))
        got = self.soft("record-snapshot", "--json", self.read(hours(50), root=5))
        self.assertEqual(got, {"recorded": False, "reason": "valid snapshot already exists", "root_id": self.ID})

    def test_a_valid_duplicate_beats_the_missed_refusal(self) -> None:
        self.ok("record-snapshot", "--json", self.read(hours(48)))
        self.edit_post(self.ID, missed=True)
        got = self.soft("record-snapshot", "--json", self.read(hours(50)))
        self.assertEqual(got["reason"], "valid snapshot already exists")

    def test_the_missed_refusal_comes_before_the_payload_is_validated(self) -> None:
        self.ok("mark-missed", now=hours(61))
        self.assertEqual(self.refusal("record-snapshot", "--json", self.read(hours(48), root=5)),
                         "post already marked missed")

    def test_early_late_and_final_reads_are_allowed_on_a_missed_post(self) -> None:
        self.ok("mark-missed", now=hours(61))
        kinds = [self.ok("record-snapshot", "--json", self.read(hours(h), **extra))["kind"]
                 for h, extra in ((10, {}), (70, {}), (FINAL_H, {"stage": "final"}))]
        self.assertEqual(kinds, ["early", "late", "final"])

    def test_repeated_early_reads_are_all_recorded(self) -> None:
        for h in (10, 20):
            self.assertTrue(self.ok("record-snapshot", "--json", self.read(hours(h)))["recorded"])
        self.assertEqual(len(json.loads(self.ledger_path(self.ID).read_text())["snapshots"]), 2)

    def test_a_stage_other_than_final_is_ignored(self) -> None:
        got = self.ok("record-snapshot", "--json", self.read(hours(48), stage="48h"))
        self.assertEqual((got["recorded"], got["kind"]), (True, "valid"))

    def test_a_bad_post_id_is_refused(self) -> None:
        self.assertEqual(self.refusal("record-snapshot", "--json", self.snap_json("x", hours(48))),
                         "bad post id 'x'")

    def test_an_unknown_post_beats_a_bad_time(self) -> None:
        error = self.refusal("record-snapshot", "--json", self.payload({"root_id": "2222222222", "observed_at": "nope"}))
        self.assertTrue(error.startswith("missing ") and error.endswith("2222222222.json"), error)

    def test_a_recorded_read_reports_its_kind_and_age(self) -> None:
        got = self.ok("record-snapshot", "--json", self.read(hours(48)))
        self.assertEqual(got, {"recorded": True, "root_id": self.ID, "kind": "valid", "age_hours": 48.0,
                               "missing": got["missing"]})

    def test_not_initialised_beats_every_payload_error(self) -> None:
        with tempfile.TemporaryDirectory() as bare:
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = loop.main(["--root", bare, "record-snapshot", "--json", "/nonexistent.json"])
        self.assertEqual((code, out.getvalue()), (1, ""))
        self.assertEqual(json.loads(err.getvalue()), {"error": "loop not initialised; run init"})


class RecordPostRules(RawCase):
    ID = "1000000001"

    def payload_for(self, **extra) -> str:
        data = {"root_id": self.ID, "slug": "s1", "format": "single-tip", "lane": "main", "posted_at": T0,
                "made_in_repo": True}
        data.update(extra)
        return self.payload(data)

    def put_experiment(self, status: str) -> None:
        self.edit_state(experiments=[self.experiment(status)])

    def test_an_invalid_payload_beats_the_already_recorded_skip(self) -> None:
        self.post(self.ID, T0)
        self.assertNotIn("already", self.refusal("record-post", "--json", self.payload_for(format="nope")))

    def test_an_invalid_payload_beats_a_corrupt_existing_file(self) -> None:
        self.ledger_path(self.ID).write_text("{")
        self.assertNotIn("valid JSON", self.refusal("record-post", "--json", self.payload_for(format="nope")))

    def test_a_corrupt_existing_file_is_read_only_when_the_payload_is_valid(self) -> None:
        self.ledger_path(self.ID).write_text("{")
        self.assertIn("is not valid JSON", self.refusal("record-post", "--json", self.payload_for()))

    def test_an_already_recorded_post_hides_a_bad_experiment(self) -> None:
        self.post(self.ID, T0)
        got = self.soft("record-post", "--json", self.payload_for(experiment="E-009", arm="treatment"))
        self.assertEqual(got, {"recorded": False, "reason": "already recorded", "root_id": self.ID})

    def test_a_missing_experiment_is_refused(self) -> None:
        self.assertEqual(self.refusal("record-post", "--json", self.payload_for(experiment="E-009", arm="treatment")),
                         "no experiment E-009")

    def test_a_closed_experiment_is_refused(self) -> None:
        self.put_experiment("no_effect")
        self.assertEqual(self.refusal("record-post", "--json", self.payload_for(experiment="E-001", arm="treatment")),
                         "experiment E-001 is closed")

    def test_a_post_in_an_experiment_needs_an_arm(self) -> None:
        self.put_experiment("testing")
        self.assertEqual(self.refusal("record-post", "--json", self.payload_for(experiment="E-001")),
                         "a post in an experiment needs arm treatment or control")

    def test_a_retrospective_post_cannot_join_an_experiment(self) -> None:
        self.put_experiment("testing")
        got = self.refusal("record-post", "--json",
                           self.payload_for(experiment="E-001", arm="control", retrospective=True, made_in_repo=False))
        self.assertEqual(got, "retrospective posts cannot join an experiment")

    def test_an_arm_needs_an_experiment(self) -> None:
        self.assertEqual(self.refusal("record-post", "--json", self.payload_for(arm="treatment")),
                         "arm set without an experiment")

    def test_a_posted_record_replaces_an_auto_post_and_keeps_its_history(self) -> None:
        self.post(self.ID, T0, auto=True, retrospective=True, made_in_repo=False, lane="other", format="other")
        self.snap(self.ID, hours(40), 50)
        self.edit_post(self.ID, missed=True, nonorganic={"reason": "boosted"}, amendments=[{"from": "other"}])
        kept = json.loads(self.ledger_path(self.ID).read_text())
        got = self.ok("record-post", "--json", self.payload_for(format="build-log"))
        self.assertEqual(got, {"recorded": True, "root_id": self.ID})
        post = json.loads(self.ledger_path(self.ID).read_text())
        for key in ("snapshots", "missed", "nonorganic", "amendments"):
            self.assertEqual(post[key], kept[key], key)
        self.assertEqual((post["format"], post["auto"]), ("build-log", False))

    def test_an_auto_record_does_not_replace_an_auto_post(self) -> None:
        self.post(self.ID, T0, auto=True, retrospective=True, made_in_repo=False, lane="other", format="other")
        got = self.soft("record-post", "--json", self.payload_for(auto=True, retrospective=True, made_in_repo=False,
                                                                   lane="other", format="other"))
        self.assertEqual(got["reason"], "already recorded")

    def test_not_initialised_beats_every_payload_error(self) -> None:
        with tempfile.TemporaryDirectory() as bare:
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = loop.main(["--root", bare, "record-post", "--json", "/nonexistent.json"])
        self.assertEqual((code, json.loads(err.getvalue())), (1, {"error": "loop not initialised; run init"}))


class ExperimentSetup(RawCase):
    def seed_cohort(self, values=(100, 200, 300)) -> list[str]:
        ids = []
        for i, value in enumerate(values):
            root_id = f"20000000{i:02d}"
            self.post(root_id, hours(-500 + i), retrospective=True, made_in_repo=False)
            self.snap(root_id, hours(-400 + i), 1000, bookmarks=value)
            ids.append(root_id)
        return ids

    def open(self) -> None:
        self.ok("open-experiment", "--json", self.payload({
            "question": "Standalone beats a thread?", "treatment": "standalone post",
            "control": "3-card thread", "primary": "bookmarks", "cohort": self.seed_cohort()}), now=T0)

    def treatment(self, start: int, values: list[int | None]) -> list[str]:
        ids = []
        for i, value in enumerate(values):
            root_id = f"30000000{start + i:02d}"
            posted = hours(10 * (start + i))
            self.post(root_id, posted, experiment="E-001", arm="treatment")
            data = {"root_id": root_id, "observed_at": hours(40, posted),
                    "root": {**ROOT_METRICS, "views": 1000, "bookmarks": value}}
            self.ok("record-snapshot", "--json", self.payload(data))
            ids.append(root_id)
        return ids


class Evaluate(ExperimentSetup):
    def test_no_open_experiment_returns_before_the_ledger_or_the_clock(self) -> None:
        with mock.patch.object(loop.Repo, "posts", side_effect=AssertionError("ledger read")), \
                mock.patch.object(loop, "render"):
            code, out, err = self.raw("evaluate", now="not a time")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out), {"evaluated": False, "reason": "no open experiment"})

    def test_a_ledger_failure_beats_a_bad_clock(self) -> None:
        self.open()
        self.ledger_path("9999999999").write_text("{")
        error = self.refusal("evaluate", now="not a time")
        self.assertIn("is not valid JSON", error)

    def test_a_bad_clock_is_refused_with_an_open_experiment(self) -> None:
        self.open()
        self.assertIn("bad time", self.refusal("evaluate", now="not a time"))

    def test_a_round_that_has_not_filled_still_saves_the_state(self) -> None:
        self.open()
        self.treatment(0, [300])
        saves = []
        original = loop.Repo.save_state
        with mock.patch.object(loop.Repo, "save_state", autospec=True,
                               side_effect=lambda repo, state: (saves.append(1), original(repo, state))):
            got = self.ok("evaluate", now=hours(200))
        self.assertEqual(got, {"evaluated": True, "experiment": "E-001", "status": "testing", "events": [],
                               "posts_needed_for_next_round": 2})
        self.assertEqual(len(saves), 1)

    def test_two_rounds_close_in_one_call_and_leftover_posts_are_discarded(self) -> None:
        self.open()
        first = self.treatment(0, [300, 400, 500])
        second = self.treatment(3, [310, 320, 330])
        self.treatment(6, [900])
        got = self.ok("evaluate", now=hours(300))
        self.assertEqual(got, {"evaluated": True, "experiment": "E-001", "status": "adopted",
                               "events": [{"from": "testing", "result": "pass", "to": "promising"},
                                          {"from": "promising", "result": "pass", "to": "adopted"}],
                               "posts_needed_for_next_round": 0})
        state = self.state()
        exp = state["experiments"][0]
        self.assertEqual(exp["closed_at"], hours(300))
        self.assertEqual([r["posts"] for r in exp["rounds"]], [first, second])
        self.assertEqual(exp["rounds"][0], {"posts": first, "values": [300, 400, 500], "passes": 3,
                                            "result": "pass", "at": hours(300)})
        self.assertEqual(state["lessons"], [{
            "id": "L-001", "experiment": "E-001", "statement": "standalone post", "status": "adopted",
            "evidence": first + second, "reference_facts": [], "created_at": hours(300),
            "last_evidence_at": hours(300), "rule_state": "none"}])

    def test_no_posts_passing_closes_as_no_effect(self) -> None:
        self.open()
        self.treatment(0, [10, 10, 10])
        got = self.ok("evaluate", now=hours(200))
        self.assertEqual(got["events"], [{"from": "testing", "result": "fail", "to": "no_effect"}])
        self.assertEqual(self.state()["experiments"][0]["rounds"][0]["passes"], 0)
        self.assertEqual(self.state()["lessons"][0]["status"], "no_effect")

    def test_a_late_only_post_and_a_null_metric_are_not_ready(self) -> None:
        self.open()
        self.treatment(0, [300, None])
        self.post("3000000005", hours(50), experiment="E-001", arm="treatment")
        self.ok("record-snapshot", "--json", self.payload({
            "root_id": "3000000005", "observed_at": hours(150), "root": {**ROOT_METRICS, "bookmarks": 999}}))
        got = self.ok("evaluate", now=hours(300))
        self.assertEqual((got["events"], got["posts_needed_for_next_round"]), ([], 2))

    def test_a_post_already_in_a_round_is_not_counted_again(self) -> None:
        self.open()
        self.treatment(0, [10, 10, 10])
        self.ok("evaluate", now=hours(200))
        self.assertEqual(self.soft("evaluate", now=hours(300)),
                         {"evaluated": False, "reason": "no open experiment"})

    def test_round_result_thresholds(self) -> None:
        self.assertEqual([experiments.round_result(p, 3) for p in (3, 2, 1, 0)], ["pass", "mixed", "fail", "fail"])

    def test_the_transition_table(self) -> None:
        self.assertEqual(experiments.TRANSITIONS, {
            ("testing", "pass"): "promising", ("testing", "mixed"): "unclear", ("testing", "fail"): "no_effect",
            ("promising", "pass"): "adopted", ("promising", "mixed"): "not_replicated",
            ("promising", "fail"): "not_replicated",
            ("unclear", "pass"): "promising", ("unclear", "mixed"): "no_effect", ("unclear", "fail"): "no_effect"})

    def test_a_promising_experiment_that_fails_is_not_replicated(self) -> None:
        self.open()
        self.treatment(0, [300, 400, 500])
        self.ok("evaluate", now=hours(200))
        self.treatment(3, [10, 10, 10])
        self.assertEqual(self.ok("evaluate", now=hours(300))["status"], "not_replicated")

    def test_an_unclear_experiment_that_passes_becomes_promising(self) -> None:
        self.open()
        self.treatment(0, [300, 400, 50])
        self.ok("evaluate", now=hours(200))
        self.treatment(3, [300, 400, 500])
        self.assertEqual(self.ok("evaluate", now=hours(300))["status"], "promising")

    def test_an_unclear_experiment_that_stays_mixed_ends_with_no_effect(self) -> None:
        self.open()
        self.treatment(0, [300, 400, 50])
        self.ok("evaluate", now=hours(200))
        self.treatment(3, [300, 400, 50])
        self.assertEqual(self.ok("evaluate", now=hours(300))["status"], "no_effect")


class NextSlot(RawCase):
    def add(self, count: int, base: str = T0) -> None:
        for i in range(count):
            self.post(f"50000000{i:02d}", hours(i + 1, base))

    def slot(self, at: str) -> dict:
        return self.ok("next-slot", now=at)

    def test_it_alternates_before_28_days_and_switches_at_exactly_28(self) -> None:
        self.assertEqual(self.slot(hours(24 * 28 - 1))["rule"], "alternate")
        self.assertEqual(self.slot(hours(24 * 28))["rule"], "one in three explores")

    def test_explore_and_exploit_outputs_with_no_experiment(self) -> None:
        self.assertEqual(self.slot(hours(1)), {
            "slot": "explore", "posts_since_start": 0, "rule": "alternate", "experiment": None, "arm": None,
            "action": "open an experiment first"})
        self.add(1)
        self.assertEqual(self.slot(hours(5)), {
            "slot": "exploit", "posts_since_start": 1, "rule": "alternate", "experiment": None, "arm": None,
            "action": "post the current best approach", "adopted_lessons": []})

    def test_outputs_with_an_open_experiment_and_adopted_lessons(self) -> None:
        self.edit_state(experiments=[self.experiment("testing")],
                        lessons=[self.lesson("L-001", "adopted"), self.lesson("L-002", "no_effect")])
        self.assertEqual(self.slot(hours(1)), {
            "slot": "explore", "posts_since_start": 0, "rule": "alternate", "experiment": "E-001",
            "arm": "treatment", "action": "post the treatment"})
        self.add(1)
        self.assertEqual(self.slot(hours(5)), {
            "slot": "exploit", "posts_since_start": 1, "rule": "alternate", "experiment": "E-001",
            "arm": "control", "action": "post the current best approach", "adopted_lessons": ["L-001"]})

    def test_one_in_three_explores_after_28_days(self) -> None:
        late = hours(24 * 30)
        results = []
        for n in range(4):
            if n:
                self.post(f"51000000{n:02d}", hours(n))
            results.append(self.slot(late)["slot"])
        self.assertEqual(results, ["explore", "exploit", "exploit", "explore"])

    def test_the_start_time_counts_and_earlier_or_retrospective_posts_do_not(self) -> None:
        self.post("5200000001", T0)
        self.post("5200000002", hours(-1))
        self.post("5200000003", hours(2), retrospective=True, made_in_repo=False)
        self.assertEqual(self.slot(hours(5))["posts_since_start"], 1)


class SoftReturnsStillRender(RawCase):
    def test_a_record_post_skip_and_an_evaluate_soft_return_regenerate_the_views(self) -> None:
        summary = self.root / "ledger" / "SUMMARY.md"
        self.post("1000000001", T0)
        for argv in (("record-post", "--json", self.payload({
                "root_id": "1000000001", "slug": "s1", "format": "single-tip", "lane": "main", "posted_at": T0,
                "made_in_repo": True})), ("evaluate",)):
            summary.unlink()
            code, out, err = self.raw(*argv, now=T0)
            self.assertEqual((code, err), (0, ""))
            self.assertIn('"recorded": false' if argv[0] == "record-post" else '"evaluated": false', out)
            self.assertTrue(summary.exists(), argv[0])


class ProcessExit(RawCase):
    def test_the_process_exits_1_with_the_error_on_stderr_and_0_with_json_on_stdout(self) -> None:
        run = lambda *argv: subprocess.run([sys.executable, str(LOOP), "--root", str(self.root), *argv],
                                           capture_output=True, text=True, check=False)
        bad = run("record-snapshot", "--json", self.snap_json("2222222222", hours(48)))
        self.assertEqual((bad.returncode, bad.stdout), (1, ""))
        self.assertIn("missing ", json.loads(bad.stderr)["error"])
        good = run("next-slot")
        self.assertEqual((good.returncode, good.stderr), (0, ""))
        self.assertEqual(json.loads(good.stdout)["slot"], "explore")


if __name__ == "__main__":
    unittest.main()
