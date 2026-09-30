#!/usr/bin/env python3
"""Checks for scripts/loop_core/experiments.py, the Experiment rules, on plain dicts. Stdlib only."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

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
            "last_evidence_at": AT, "rule_state": "none"}])

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


if __name__ == "__main__":
    unittest.main()
