#!/usr/bin/env python3
"""PreToolUse hook: the model may never create, edit or delete APPROVED, or start
another Grok to type /approve for it. Read-only tools are left alone."""

from __future__ import annotations

import json
import re
import sys

READ_ONLY = {"read_file", "Read", "grep", "Grep", "list_dir", "Glob", "ListDir"}
TOUCHES_APPROVAL = re.compile(r"APPROVED|/approve\b")


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
    sys.exit(0)


if __name__ == "__main__":
    main()
