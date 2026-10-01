#!/usr/bin/env python3
"""Checks for scripts/loop_core/experiments.py, the Experiment rules, on plain dicts. Stdlib only."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from datetime import datetime, timedelta, timezone  # noqa: E402

from loop_core import experiments  # noqa: E402

AT = "2026-11-01T00:00:00Z"


def experiment(status: str = "testing", **extra) -> dict:
    return {"id": "E-001", "treatment": "standalone post", "reference_facts": ["f"], "size": 3, "threshold": 300,
            "status": status, "rounds": [], "closed_at": None, **extra}


def state(*exps: dict, lessons: list[dict] | None = None) -> dict:
    return {"experiments": list(exps), "lessons": lessons or []}


def ready(*values: int, start: int = 0) -> list[tuple[str, int]]:
    return [(f"p{start + i}", v) for i, v in enumerate(values)]


class Helpers(unittest.TestCase):
    def test_open_experiment_is_the_first_open_one(self) -> None:
        closed, open_, later = experiment("adopted"), experiment("unclear", id="E-002"), experiment(id="E-003")
        self.assertIs(experiments.open_experiment(state(closed, open_, later)), open_)
        self.assertIsNone(experiments.open_experiment(state(closed)))

    def test_next_id_counts_the_items(self) -> None:
        self.assertEqual([experiments.next_id("L", [{}] * n) for n in (0, 9, 99)], ["L-001", "L-010", "L-100"])

    def test_round_result_at_each_size(self) -> None:
        self.assertEqual([experiments.round_result(p, 3) for p in (3, 2, 1, 0)], ["pass", "mixed", "fail", "fail"])
        self.assertEqual([experiments.round_result(p, 5) for p in (5, 4, 3)], ["pass", "mixed", "fail"])

    def test_every_transition_lands_in_an_open_or_a_closed_state(self) -> None:
        closed = {"adopted", "not_replicated", "no_effect"}
        self.assertEqual({experiments.TRANSITIONS[k] for k in experiments.TRANSITIONS} - closed,
                         experiments.OPEN_STATES - {"testing"})
        self.assertTrue(all(before in experiments.OPEN_STATES for before, _ in experiments.TRANSITIONS))


class LessonBasis(unittest.TestCase):
    def measured(self, **extra) -> dict:
        return {"id": "L-001", "experiment": "E-001", "status": "adopted", "evidence": [f"p{i}" for i in range(6)], **extra}

    def rounds(self, *sizes: int) -> dict:
        return experiment("adopted", cohort=[{"root_id": f"c{i}"} for i in range(5)],
                          rounds=[{"posts": ["x"] * n} for n in sizes])

    def test_measured_lesson_states_rounds_posts_cohort_and_the_caveat(self) -> None:
        text = experiments.lesson_basis(self.measured(), [self.rounds(3, 3)])
        self.assertEqual(text, "Provisional: adopted after 2 rounds (6 treatment posts) against a cohort of 5. "
                               "A chance result adopts about 1 time in 50 to 1 in 8 at this size.")

    def test_a_mixed_round_first_counts_all_three_rounds(self) -> None:
        text = experiments.lesson_basis(self.measured(), [self.rounds(3, 3, 3)])
        self.assertIn("after 3 rounds (9 treatment posts)", text)

    def test_preference_lesson_names_its_edits_and_says_nothing_was_measured(self) -> None:
        lesson = {"id": "L-002", "experiment": None, "status": "adopted", "source": "operator edits",
                  "evidence": ["a", "b", "c"]}
        self.assertEqual(experiments.lesson_basis(lesson, []),
                         "Provisional: 3 operator edits (a, b, c). Not measured against anything.")

    def test_only_adopted_lessons_have_a_basis(self) -> None:
        for status in ("no_effect", "not_replicated"):
            self.assertIsNone(experiments.lesson_basis(self.measured(status=status), [self.rounds(3, 3)]))

    def test_a_stored_stale_status_is_still_an_adopted_outcome(self) -> None:
        self.assertEqual(experiments.lesson_outcome({"status": "stale"}), "adopted")
        self.assertEqual(experiments.lesson_basis(self.measured(status="stale"), [self.rounds(3, 3)]),
                         "Provisional: adopted after 2 rounds (6 treatment posts) against a cohort of 5. "
                         "A chance result adopts about 1 time in 50 to 1 in 8 at this size.")

    def test_a_missing_experiment_is_said_not_guessed(self) -> None:
        self.assertEqual(experiments.lesson_basis(self.measured(), []),
                         "Provisional: experiment E-001 is not in the ledger, so its rounds cannot be shown.")


class Evaluate(unittest.TestCase):
    def test_too_few_posts_change_nothing_and_say_how_many_are_needed(self) -> None:
        new, answer = experiments.evaluate_rounds(state(experiment()), ready(300, 400), AT)
        self.assertEqual(new, state(experiment()))
        self.assertEqual(answer, {"evaluated": True, "experiment": "E-001", "status": "testing", "events": [],
                                  "posts_needed_for_next_round": 1})

    def test_the_input_state_is_not_changed(self) -> None:
        before = state(experiment())
        frozen = copy.deepcopy(before)
        new, _ = experiments.evaluate_rounds(before, ready(300, 400, 500, 310, 320, 330), AT)
        self.assertEqual(before, frozen)
        self.assertEqual(new["experiments"][0]["status"], "adopted")

    def test_a_round_that_passes_moves_a_testing_experiment_to_promising(self) -> None:
        new, answer = experiments.evaluate_rounds(state(experiment()), ready(300, 301, 999), AT)
        exp = new["experiments"][0]
        self.assertEqual(exp["status"], "promising")
        self.assertEqual(exp["rounds"], [{"posts": ["p0", "p1", "p2"], "values": [300, 301, 999], "passes": 3,
                                          "result": "pass", "at": AT}])
        self.assertEqual(answer["events"], [{"from": "testing", "result": "pass", "to": "promising"}])
        self.assertEqual((new["lessons"], answer["posts_needed_for_next_round"]), ([], 3))

    def test_a_value_below_the_threshold_does_not_pass(self) -> None:
        new, _ = experiments.evaluate_rounds(state(experiment()), ready(299, 300, 300), AT)
        self.assertEqual(new["experiments"][0]["rounds"][0]["passes"], 2)
        self.assertEqual(new["experiments"][0]["status"], "unclear")

    def test_two_rounds_run_in_one_call_and_the_close_writes_a_lesson(self) -> None:
        new, answer = experiments.evaluate_rounds(state(experiment()), ready(300, 400, 500, 310, 320, 330), AT)
        exp = new["experiments"][0]
        self.assertEqual([e["to"] for e in answer["events"]], ["promising", "adopted"])
        self.assertEqual((exp["closed_at"], answer["posts_needed_for_next_round"]), (AT, 0))
        self.assertEqual(new["lessons"], [{
            "id": "L-001", "experiment": "E-001", "statement": "standalone post", "status": "adopted",
            "evidence": [f"p{i}" for i in range(6)], "reference_facts": ["f"], "created_at": AT,
            "last_evidence_at": AT}])

    def test_posts_left_over_once_the_experiment_closes_are_dropped(self) -> None:
        new, answer = experiments.evaluate_rounds(state(experiment()), ready(1, 1, 1, 999, 999, 999, 999), AT)
        self.assertEqual(len(new["experiments"][0]["rounds"]), 1)
        self.assertEqual((answer["status"], answer["posts_needed_for_next_round"]), ("no_effect", 0))

    def test_a_lesson_id_continues_the_existing_lessons(self) -> None:
        new, _ = experiments.evaluate_rounds(state(experiment(), lessons=[{"id": "L-001"}]), ready(1, 1, 1), AT)
        self.assertEqual([l["id"] for l in new["lessons"]], ["L-001", "L-002"])

    def test_the_lesson_takes_no_reference_facts_from_an_experiment_without_them(self) -> None:
        exp = experiment()
        del exp["reference_facts"]
        new, _ = experiments.evaluate_rounds(state(exp), ready(1, 1, 1), AT)
        self.assertEqual(new["lessons"][0]["reference_facts"], [])

    def test_each_open_state_takes_each_result(self) -> None:
        cases = {"testing": {"pass": "promising", "mixed": "unclear", "fail": "no_effect"},
                 "promising": {"pass": "adopted", "mixed": "not_replicated", "fail": "not_replicated"},
                 "unclear": {"pass": "promising", "mixed": "no_effect", "fail": "no_effect"}}
        values = {"pass": (300, 300, 300), "mixed": (300, 300, 0), "fail": (300, 0, 0)}
        for before, results in cases.items():
            for result, after in results.items():
                new, answer = experiments.evaluate_rounds(state(experiment(before)), ready(*values[result]), AT)
                self.assertEqual((answer["status"], answer["events"][0]["result"]), (after, result), (before, result))

    def test_the_first_open_experiment_is_the_one_that_runs(self) -> None:
        new, answer = experiments.evaluate_rounds(
            state(experiment("adopted"), experiment(id="E-002")), ready(300, 300, 300), AT)
        self.assertEqual((answer["experiment"], new["experiments"][0]["status"]), ("E-002", "adopted"))
        self.assertEqual(new["experiments"][1]["status"], "promising")


START = datetime(2026, 10, 1, tzinfo=timezone.utc)


def stamp(hours: float) -> str:
    return (START + timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")


def made(*hours: float, retrospective: bool = False) -> list[dict]:
    return [{"retrospective": retrospective, "posted_at": stamp(h)} for h in hours]


def slot(count: int, days: float, **kw) -> dict:
    st = kw.pop("state", state())
    return experiments.next_slot(st, START, made(*range(count)), START + timedelta(days=days))


class NextSlot(unittest.TestCase):
    def test_it_alternates_up_to_28_days_then_explores_one_in_three(self) -> None:
        self.assertEqual(slot(0, 27.99)["rule"], "alternate")
        self.assertEqual(slot(0, 28)["rule"], "one in three explores")

    def test_the_slot_follows_the_count(self) -> None:
        alternate = [slot(n, 1)["slot"] for n in range(4)]
        third = [slot(n, 40)["slot"] for n in range(7)]
        self.assertEqual(alternate, ["explore", "exploit", "explore", "exploit"])
        self.assertEqual(third, ["explore", "exploit", "exploit", "explore", "exploit", "exploit", "explore"])

    def test_explore_without_an_experiment_says_to_open_one(self) -> None:
        self.assertEqual(slot(0, 1), {"slot": "explore", "posts_since_start": 0, "rule": "alternate",
                                      "experiment": None, "arm": None, "action": "open an experiment first"})

    def test_an_open_experiment_sets_the_arm_for_each_slot(self) -> None:
        st = state(experiment("promising"), lessons=[{"id": "L-001", "status": "adopted"},
                                                     {"id": "L-002", "status": "no_effect"}])
        self.assertEqual(slot(0, 1, state=st), {
            "slot": "explore", "posts_since_start": 0, "rule": "alternate", "experiment": "E-001",
            "arm": "treatment", "action": "post the treatment"})
        self.assertEqual(slot(1, 1, state=st), {
            "slot": "exploit", "posts_since_start": 1, "rule": "alternate", "experiment": "E-001",
            "arm": "control", "action": "post the current best approach", "adopted_lessons": ["L-001"]})

    def test_exploit_lists_no_lessons_when_none_is_adopted(self) -> None:
        self.assertEqual(slot(1, 1)["adopted_lessons"], [])

    def test_the_start_time_counts_and_earlier_or_retrospective_posts_do_not(self) -> None:
        posts = made(-1, 0, 5) + made(2, retrospective=True)
        got = experiments.next_slot(state(), START, posts, START + timedelta(days=1))
        self.assertEqual(got["posts_since_start"], 2)


class LessonFreshness(unittest.TestCase):
    def lesson(self, **extra) -> dict:
        base = {"id": "L-001", "status": "adopted", "last_evidence_at": AT}
        base.update(extra)
        return base

    def at(self, days: float) -> datetime:
        return datetime(2026, 11, 1, tzinfo=timezone.utc) + timedelta(days=days)

    def test_freshness_does_not_replace_the_outcome(self) -> None:
        lesson = self.lesson()
        self.assertFalse(experiments.lesson_is_stale(lesson, self.at(42)))
        self.assertTrue(experiments.lesson_is_stale(lesson, self.at(42) + timedelta(seconds=1)))
        self.assertEqual(lesson["status"], "adopted")
        self.assertFalse(experiments.lesson_is_stale(self.lesson(status="no_effect"), self.at(100)))

    def test_newly_stale_is_the_crossing_since_the_last_review(self) -> None:
        lesson = self.lesson()
        self.assertTrue(experiments.newly_stale(lesson, self.at(50), None))
        reviewed = self.at(43)
        self.assertFalse(experiments.newly_stale(lesson, self.at(50), reviewed))
        self.assertTrue(experiments.newly_stale(lesson, self.at(50), self.at(40)))

    def test_rule_application_is_the_latest_rules_entry(self) -> None:
        rules = [{"lesson": "L-001", "undone": True}, {"lesson": "L-001", "undone": False}]
        self.assertEqual(experiments.rule_application(rules, "L-001"), "applied")
        self.assertEqual(experiments.rule_application(rules[:1], "L-001"), "reverted")
        self.assertEqual(experiments.rule_application([], "L-001"), "none")

    def test_a_deviation_edit_leaves_the_experiment(self) -> None:
        post = {"experiment": "E-001", "arm": "treatment", "edits": [{"class": "deviation"}]}
        self.assertTrue(experiments.leave_experiment(post))
        self.assertEqual((post["experiment"], post["arm"]), (None, "none"))
        kept = {"experiment": "E-001", "arm": "treatment", "edits": [{"class": "violation"}]}
        self.assertFalse(experiments.leave_experiment(kept))
        self.assertEqual(kept["arm"], "treatment")


if __name__ == "__main__":
    unittest.main()
