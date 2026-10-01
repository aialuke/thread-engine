"""The Experiment rules: which states are open, how a Round moves an Experiment, what a closed one teaches,
which Slot comes next, and whether a post is in an experiment.

Vocabulary is CONTEXT.md's. Plain dicts in, plain dicts out: no files, no clock, no argparse. The
caller (loop.py) reads the ledger and the clock, and saves the state this returns.
"""

from __future__ import annotations

import copy
from datetime import datetime, timedelta
from typing import NamedTuple

from loop_core.errors import LoopError
from loop_core.times import parse_time

EXPLORE_ALTERNATE_DAYS = 28
OPEN_STATES = {"testing", "promising", "unclear"}
STALE_AFTER_DAYS = 42
TRANSITIONS = {
    ("testing", "pass"): "promising",
    ("testing", "mixed"): "unclear",
    ("testing", "fail"): "no_effect",
    ("promising", "pass"): "adopted",
    ("promising", "mixed"): "not_replicated",
    ("promising", "fail"): "not_replicated",
    ("unclear", "pass"): "promising",
    ("unclear", "mixed"): "no_effect",
    ("unclear", "fail"): "no_effect",
}
# Two passing rounds of three (or mixed, then two passes) adopt a lesson. At a chance-pass rate of 1/2 per post
# that is about 2%; at 2/3 it is about 12.7% (blind Codex review task-munjqiqe-7wiz8s, re-derived 2026-09-30).
FALSE_ADOPTION_CAVEAT = "A chance result adopts about 1 time in 50 to 1 in 8 at this size."


def open_experiment(state: dict) -> dict | None:
    for exp in state["experiments"]:
        if exp["status"] in OPEN_STATES:
            return exp
    return None


def next_id(prefix: str, items: list[dict]) -> str:
    return f"{prefix}-{len(items) + 1:03d}"


def round_result(passes: int, size: int) -> str:
    if passes == size:
        return "pass"
    if passes >= size - 1:
        return "mixed"
    return "fail"


def lesson_outcome(lesson: dict) -> str:
    """The close result: adopted, not_replicated, or no_effect. A stored status of stale is the old overwrite; the outcome was adopted."""
    if lesson.get("status") == "stale":
        return "adopted"
    return lesson["status"]


def lesson_is_stale(lesson: dict, at: datetime) -> bool:
    """An adopted lesson whose last evidence is more than STALE_AFTER_DAYS old. The outcome stays adopted."""
    if lesson.get("status") == "stale":
        return True
    if lesson_outcome(lesson) != "adopted":
        return False
    return at - parse_time(lesson["last_evidence_at"]) > timedelta(days=STALE_AFTER_DAYS)


def newly_stale(lesson: dict, at: datetime, last_review: datetime | None) -> bool:
    if not lesson_is_stale(lesson, at):
        return False
    if last_review is None:
        return True
    return parse_time(lesson["last_evidence_at"]) + timedelta(days=STALE_AFTER_DAYS) > last_review


def rule_application(rules: list[dict], lesson_id: str) -> str:
    latest = next((rule for rule in reversed(rules) if rule.get("lesson") == lesson_id), None)
    if latest is None:
        return "none"
    return "reverted" if latest.get("undone") else "applied"


class Membership(NamedTuple):
    """Outside an experiment, or in one on treatment or control.

    The ledger still stores this as experiment and arm. place() is the only writer of that pair.
    """

    experiment: str | None
    arm: str

    def place(self, post: dict) -> None:
        post["experiment"] = self.experiment
        post["arm"] = self.arm


OUTSIDE = Membership(None, "none")
IN_ARMS = frozenset({"treatment", "control"})


def membership(experiment: object, arm: object) -> Membership | None:
    """The pair, or None when the two fields disagree. None is not a membership."""
    if experiment is None and arm == "none":
        return OUTSIDE
    if isinstance(experiment, str) and arm in IN_ARMS:
        return Membership(experiment, arm)
    return None


def require_membership(post: dict) -> Membership:
    member = membership(post.get("experiment"), post.get("arm", "none"))
    if member is not None:
        return member
    if post.get("experiment") is not None:
        raise LoopError("a post in an experiment needs arm treatment or control")
    raise LoopError("arm set without an experiment")


def edit_leaves(edit: dict) -> bool:
    """Whether recording this edit drops the post out of its experiment.

    A deviation always does. A violation does when leaves is true: the class stays violation,
    and the deviation's effect still applies.
    """
    if edit.get("class") == "deviation":
        return True
    return edit.get("class") == "violation" and edit.get("leaves") is True


def leave_experiment(post: dict) -> bool:
    if not any(edit_leaves(edit) for edit in post.get("edits") or []):
        return False
    if membership(post.get("experiment"), post.get("arm", "none")) == OUTSIDE:
        return False
    OUTSIDE.place(post)
    return True


def lesson_basis(lesson: dict, experiments: list[dict]) -> str | None:
    if lesson_outcome(lesson) != "adopted":
        return None
    if lesson.get("experiment") is None:
        edits = lesson["evidence"]
        return f"Provisional: {len(edits)} operator edits ({', '.join(edits)}). Not measured against anything."
    exp = next((e for e in experiments if e["id"] == lesson["experiment"]), None)
    if exp is None:
        return f"Provisional: experiment {lesson['experiment']} is not in the ledger, so its rounds cannot be shown."
    rounds = len(exp["rounds"])
    posts = sum(len(rnd["posts"]) for rnd in exp["rounds"])
    return (f"Provisional: adopted after {rounds} rounds ({posts} treatment posts) against a cohort of "
            f"{len(exp['cohort'])}. {FALSE_ADOPTION_CAVEAT}")


def evaluate_rounds(state: dict, ready: list[tuple[str, float]], at: str,
                    notes: dict[str, str] | None = None) -> tuple[dict, dict]:
    """Run every Round the ready posts complete on the open Experiment. Returns (new state, evaluate's answer).

    `ready` is (root_id, primary value) for each unconsumed treatment post, in posting order. `notes` says why
    a post's value is a forced miss (root_id to reason); a Round keeps the notes of its own posts. The caller
    has already checked that an Experiment is open. `state` is not changed; a closed Experiment adds a Lesson to the
    new state, and posts left over once it closes are dropped.
    """
    state = copy.deepcopy(state)
    exp = open_experiment(state)
    events = []
    while exp["status"] in OPEN_STATES and len(ready) >= exp["size"]:
        batch, ready = ready[: exp["size"]], ready[exp["size"]:]
        passes = sum(1 for _, value in batch if value >= exp["threshold"])
        result = round_result(passes, exp["size"])
        before = exp["status"]
        exp["status"] = TRANSITIONS[(before, result)]
        rnd = {"posts": [pid for pid, _ in batch], "values": [value for _, value in batch],
               "passes": passes, "result": result, "at": at}
        noted = {pid: (notes or {})[pid] for pid, _ in batch if pid in (notes or {})}
        if noted:
            rnd["notes"] = noted
        exp["rounds"].append(rnd)
        events.append({"from": before, "result": result, "to": exp["status"]})
        if exp["status"] not in OPEN_STATES:
            exp["closed_at"] = at
            evidence = [pid for rnd in exp["rounds"] for pid in rnd["posts"]]
            state["lessons"].append({
                "id": next_id("L", state["lessons"]),
                "experiment": exp["id"],
                "statement": exp["treatment"],
                "status": exp["status"],
                "evidence": evidence,
                "reference_facts": exp.get("reference_facts", []),
                "created_at": at,
                "last_evidence_at": at,
            })
    waiting = exp["size"] - len(ready) if exp["status"] in OPEN_STATES else 0
    return state, {"evaluated": True, "experiment": exp["id"], "status": exp["status"],
                   "events": events, "posts_needed_for_next_round": waiting}


def next_slot(state: dict, started: datetime, posts: list[dict], at: datetime) -> dict:
    live = [p for p in posts if not p["retrospective"] and parse_time(p["posted_at"]) >= started]
    count = len(live)
    alternating = at - started < timedelta(days=EXPLORE_ALTERNATE_DAYS)
    explore = count % 2 == 0 if alternating else count % 3 == 0
    exp = open_experiment(state)
    slot = {"slot": "explore" if explore else "exploit", "posts_since_start": count,
            "rule": "alternate" if alternating else "one in three explores"}
    if explore:
        slot["experiment"] = exp["id"] if exp else None
        slot["arm"] = "treatment" if exp else None
        slot["action"] = "post the treatment" if exp else "open an experiment first"
    else:
        adopted = [l for l in state["lessons"] if lesson_outcome(l) == "adopted"]
        slot["experiment"] = exp["id"] if exp else None
        slot["arm"] = "control" if exp else None
        slot["action"] = "post the current best approach"
        slot["adopted_lessons"] = [l["id"] for l in adopted]
    return slot
