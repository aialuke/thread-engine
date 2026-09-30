#!/usr/bin/env python3
"""Jev judges where each learning should live (research code; see README.md, "Placement judge")."""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from jev_design_vote import check_answers, check_question, post  # noqa: E402
from jev_referee import PINNED_MODEL, read_key  # noqa: E402

OUT = Path(__file__).resolve().parent / "private" / "placement"

DEST = {
    "skill": "A project skill (.claude/skills/<name>/SKILL.md): a procedure the operator triggers by slash command and the agent follows step by step.",
    "research_doc": "A dated file under research/: findings, evidence and product lessons from one investigation.",
    "memory": "The agent's persistent memory notes: facts about the operator, feedback on how to work, project state and references that carry across sessions.",
    "rules_md": "The operator's global RULES.md: concrete, falsifiable behavioural rules for every project. Anything the agent already does correctly, or that can't be followed, doesn't belong.",
    "agents_md": "The project's AGENTS.md: the short list of operating rules and layout for thread-engine, loaded every session.",
    "none": "No new content: it is already covered elsewhere, or it should be left out.",
}
EXISTING = [
    "RULES.md, Delegation: reach for a second, independent model when stuck or when a conclusion deserves blind challenge before it is stated.",
    "AGENTS.md: start non-trivial work in Plan mode.",
    "RULES.md, Failure Investigation: don't silence a linter, weaken a failing test, or bypass a validation gate just to make output look green.",
]
ITEMS = [  # (id, text, my recommendation)
    ("L1", "The pre-run procedure for asking Jev to judge repo text: read the samples before sending, hand-audit the calibration terms, write the pass rule first, plant known-bad controls, pilot one card, repeat runs, get a second rater on contested calls, and state what leaves the machine.", "skill"),
    ("L2", "Which Jev question types are validated: implementation-detail and project-specific passed their controls; one-sense passed on a hand-audited set; faithful and self-contained failed their controls; a Score question gave bimodal answers.", "research_doc"),
    ("L3", "The current state of the Jev build-phase research: the two glossary runs, which questions are validated, and that only implementation-detail survived the last check.", "memory"),
    ("L4", "If a stop rule declared before a run fails, report and stop; do not change the thresholds or the calibration set to make it pass.", "rules_md"),
    ("L5", "Start non-trivial work in Plan mode.", "none"),
    ("L6", "Get an independent second rater on contested calls instead of relying on one model plus your own reading.", "none"),
    ("L7", "Do not turn the glossary check into a reusable slash command yet, because most of its questions are not validated.", "none"),
    ("L8", "AGENTS.md still calls the topics file 'the backlog' while the glossary now says Queue; align the wording.", "agents_md"),
    ("C1", "The steps to prepare a release, which the operator runs with a slash command and the agent follows in order.", "skill"),
    ("C2", "The operator prefers to see a one-line summary before any commit is made.", "memory"),
    ("C3", "New invariant for this project: a draft must never name a competitor's private pricing.", "agents_md"),
    ("C4", "Measured result of an experiment: the cut-off was frozen at 0.8 and Jev agreed with the panel on 92.6% of decided posts.", "research_doc"),
    ("C5", "In every project, run git status before ending a session.", "rules_md"),
]


def card(order: list[str]) -> dict:
    q = {}
    for i, (_, _, _) in enumerate(ITEMS):
        q[f"place_{i}"] = {"type": "choice", "criteria": {k: DEST[k] for k in order}, "instructions":
            f"Where should the learning in `learnings[{i}].text` live? Choose the one destination whose purpose fits it best. "
            "Choose `none` if `existing` already covers it or it should be left out."}
        check_question(f"place_{i}", q[f"place_{i}"])
    return {"model": PINNED_MODEL, "state": {"existing": EXISTING, "learnings": [{"id": i, "text": t} for i, (_, t, _) in enumerate(ITEMS)]}, "questions": q}


def run() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    key = read_key(subprocess.run)
    orders = {"A": list(DEST), "B": list(reversed(list(DEST)))}
    for name, order in orders.items():
        c = card(order)
        payload = check_answers(c, post(c, key, 60.0, urllib.request.urlopen, time.sleep))
        (OUT / f"order-{name}.json").write_text(json.dumps(payload["answers"], ensure_ascii=False), encoding="utf-8")
        print("ok", name, payload.get("usage"))
    return 0


def report() -> int:
    ans = {n: json.loads((OUT / f"order-{n}.json").read_text()) for n in "AB"}
    print("id  mine          A (p)              B (p)              verdict")
    ctl_ok = 0
    ctl_total = 0
    rows = []
    for i, (id_, text, rec) in enumerate(ITEMS):
        a, b = ans["A"][f"place_{i}"], ans["B"][f"place_{i}"]
        pa, pb = a["probabilities"][a["choice"]], b["probabilities"][b["choice"]]
        agree = a["choice"] == b["choice"] == rec
        split = a["choice"] != b["choice"]
        verdict = "AGREES" if agree else ("ORDER-SENSITIVE" if split else "DISAGREES")
        rows.append((id_, verdict))
        print(f"{id_:3} {rec:13} {a['choice']:12} ({pa:.2f})   {b['choice']:12} ({pb:.2f})   {verdict}")
        if id_.startswith("C"):
            ctl_total += 1
            ctl_ok += agree
    print(f"\ncontrols correct in both orders: {ctl_ok}/{ctl_total} (need >= 4)")
    if ctl_ok < 4:
        print("=> STOP: controls failed; ignore the learnings' verdicts")
    else:
        print("=> controls pass; learnings' verdicts are usable as one rater's view")
    return 0


if __name__ == "__main__":
    sys.exit({"run": run, "report": report}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__) or 1)())
