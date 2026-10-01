#!/usr/bin/env python3
"""Ask Jev which model and which agent type should take each pstack-review task (research code, unvalidated use).

    python3 research/jev-test/pstack_routing.py            # runs every card, prints a table
Each card is one request with one Choice question; options run in both orders to expose position bias.
Reuses scripts/jev_design_vote.py (request checks) and the Keychain read in scripts/jev_referee.py.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import subprocess  # noqa: E402

from jev_design_vote import check_answers, check_question, post  # noqa: E402
from jev_referee import PINNED_MODEL, read_key  # noqa: E402

OUT = Path(__file__).resolve().parent / "private" / "pstack-routing"

TASKS = {
    "T1": "Read in full the 23 playbooks of the pstack plugin plus poteto-mode/SKILL.md (about 25 markdown files). Per playbook, report the concrete gates or steps that add rigor with exact quotes, what depends on Cursor, and overlap with our own rules. Read-only; write a cited report.",
    "T2": "Read in full the 23 principle skills and the 10 guide documents of the pstack plugin. Report what each principle changes in an agent's decisions with exact quotes, and whether it is portable to Claude Code. Read-only; write a cited report.",
    "T3": "Read in full about 24 remaining pstack skills (architect, arena, swarm, interrogate, eval, reflect, tdd, unslop and others) and two agent files. Report mechanisms with quotes, Cursor-specific dependencies, and how many subagents each skill spawns. Read-only; write a cited report.",
    "T4": "Take three finished reports on the pstack plugin plus our own RULES.md and skills. Judge what to adopt, adapt or skip for a solo, no-code operator whose repo forbids auto-posting. Write the recommendation with reasons.",
    "C1": "Rename one variable across 200 files with a mechanical find-and-replace, then run the tests.",
    "C2": "Choose the core architecture for a novel system with no precedent, weighing several competing designs and long-term consequences.",
}
MODELS = {
    "haiku-4.5": "smallest, fastest and cheapest Claude model",
    "sonnet-5.5": "mid-size Claude model, balanced cost and quality",
    "opus-5.5": "large Claude model, strong judgement, higher cost",
    "fable-5.1": "most capable Claude model, highest cost",
    "codex": "OpenAI Codex, an independent second model outside Claude",
}
AGENTS = {
    "general-purpose": "multi-step research and file reading, all tools",
    "Explore": "read-only search across many files, returns conclusions not content",
    "literature-reader": "reads web sources and writes a cited report with exact quotes",
    "Plan": "designs implementation plans, read-only",
    "codex-rescue": "hands a substantial task to Codex",
    "claude": "catch-all agent for anything else",
}


def card(task: str, kind: str, reverse: bool) -> dict:
    options = MODELS if kind == "model" else AGENTS
    items = list(options.items())[::-1] if reverse else list(options.items())
    ask = ("Which model should run this task, weighing quality of the result against cost?"
           if kind == "model" else "Which agent type should run this task?")
    q = {"type": "choice", "instructions": ask, "criteria": dict(items)}
    check_question("pick", q)
    return {"model": PINNED_MODEL, "state": {"task": TASKS[task]}, "questions": {"pick": q}}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    key = read_key(subprocess.run)
    rows, usage = [], []
    for task in TASKS:
        for kind in ("model", "agent"):
            if task.startswith("C") and kind == "agent":
                continue
            for reverse in (False, True):
                c = card(task, kind, reverse)
                got = check_answers(c, post(c, key, 60.0, urllib.request.urlopen, time.sleep))
                a = got["answers"]["pick"]
                (OUT / f"{task}-{kind}-{'rev' if reverse else 'fwd'}.json").write_text(json.dumps(got, indent=1))
                top = sorted(a["probabilities"].items(), key=lambda kv: -kv[1])[:3]
                rows.append((task, kind, "rev" if reverse else "fwd", a["choice"], a["confidence"], top))
                usage.append(got.get("usage"))
    for r in rows:
        print(r[0], r[1], r[2], "->", r[3], f"conf={r[4]:.2f}", " ".join(f"{k}:{v:.2f}" for k, v in r[5]))
    print("requests:", len(rows), "usage:", json.dumps(usage[-1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
