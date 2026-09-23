#!/usr/bin/env python3
"""PreToolUse hook: the model may never create, edit or delete APPROVED, or start
another Grok to type /approve for it. Edit tools may not touch loop state, which
changes only through scripts/loop.py. Read-only tools are left alone."""

from __future__ import annotations

import json
import re
import sys

READ_ONLY = {"read_file", "Read", "grep", "Grep", "list_dir", "Glob", "ListDir"}
TOUCHES_APPROVAL = re.compile(r"APPROVED|/approve\b")
SHELL = {"run_terminal_command", "Bash"}
LOOP_STATE = re.compile(r"loop/state\.json|ledger/[0-9]+\.json|ledger/SUMMARY\.md|experiments\.md|learnings\.md")


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    tool = str(event.get("toolName", ""))
    if tool in READ_ONLY or tool.startswith(("x_", "web_")):
        sys.exit(0)
    if TOUCHES_APPROVAL.search(json.dumps(event.get("toolInput", {}))):
        print(json.dumps({
            "decision": "deny",
            "reason": "APPROVED is created only by the operator typing /approve <slug>. "
                      "Ask the operator to review the draft and approve it.",
        }))
        sys.exit(2)
    if tool not in SHELL and LOOP_STATE.search(json.dumps(event.get("toolInput", {}))):
        print(json.dumps({
            "decision": "deny",
            "reason": "Loop state and its generated views change only through python3 scripts/loop.py.",
        }))
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
