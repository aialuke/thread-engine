"""The Experiment rules: which states are open, how a Round moves an Experiment, what a closed one teaches.

Vocabulary is CONTEXT.md's. Plain dicts in, plain dicts out: no files, no clock, no argparse. The
caller (loop.py) reads the ledger and the clock, and saves the state this returns.
"""

from __future__ import annotations

import copy

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


def evaluate_rounds(state: dict, ready: list[tuple[str, int]], at: str) -> tuple[dict, dict]:
    """Run every Round the ready posts complete on the open Experiment. Returns (new state, evaluate's answer).

    `ready` is (root_id, primary value) for each unconsumed treatment post, in posting order. The caller has
    already checked that an Experiment is open. `state` is not changed; a closed Experiment adds a Lesson to the
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
        exp["rounds"].append({"posts": [pid for pid, _ in batch],
                              "values": [value for _, value in batch],
                              "passes": passes, "result": result, "at": at})
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
