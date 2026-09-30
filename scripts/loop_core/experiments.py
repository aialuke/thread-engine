"""The Experiment rules: which states are open, how a Round moves an Experiment, what a closed one teaches,
which Slot comes next.

Vocabulary is CONTEXT.md's. Plain dicts in, plain dicts out: no files, no clock, no argparse. The
caller (loop.py) reads the ledger and the clock, and saves the state this returns.
"""

from __future__ import annotations

import copy
from datetime import datetime, timedelta

from loop_core.times import parse_time

EXPLORE_ALTERNATE_DAYS = 28
OPEN_STATES = {"testing", "promising", "unclear"}
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
                "rule_state": "none",
            })
    waiting = exp["size"] - len(ready) if exp["status"] in OPEN_STATES else 0
    return state, {"evaluated": True, "experiment": exp["id"], "status": exp["status"],
                   "events": events, "posts_needed_for_next_round": waiting}


def next_slot(state: dict, started: datetime, posts: list[dict], at: datetime) -> dict:
    """The next Slot: explore or exploit, from the time since `started` and the posts made since then.

    Every other post alternates for the first 28 days, then one in three explores. Retrospective posts and
    posts from before `started` do not count.
    """
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
        adopted = [l for l in state["lessons"] if l["status"] == "adopted"]
        slot["experiment"] = exp["id"] if exp else None
        slot["arm"] = "control" if exp else None
        slot["action"] = "post the current best approach"
        slot["adopted_lessons"] = [l["id"] for l in adopted]
    return slot
