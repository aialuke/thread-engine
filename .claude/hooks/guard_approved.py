#!/usr/bin/env python3
"""PreToolUse hook for both Grok and Claude Code.

The model may never create, change or remove a draft's approval marker file, or
start another agent session to type the approve command for it. Edit tools may
not write loop state, which changes only through scripts/loop.py. No session may
read the X API keys from the Keychain; scripts/x_api.py reads them in its own
process, which this hook never sees. Checks look at
file paths and shell write verbs, never at prose, so docs and skills that mention
these files stay editable.

Grok sends toolName/toolInput and reads the JSON decision on stdout.
Claude Code sends tool_name/tool_input and, on exit 2, reads stderr.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import PurePosixPath

MARKER = "APPROVE" + "D"
APPROVE_CMD = "/appro" + "ve"

# Tools that cannot change files. Subagent tools are included because their own
# tool calls pass through this hook too.
NO_WRITE = {
    "read_file", "grep", "list_dir", "spawn_subagent",                     # Grok
    "Read", "Grep", "Glob", "LS", "ListDir", "WebFetch", "WebSearch",       # Claude Code
    "Agent", "Task", "Skill", "ToolSearch", "TodoWrite", "AskUserQuestion",
}
SHELL = {"run_terminal_command", "Bash"}
LOOP_STATE = re.compile(r"(^|/)(loop/state\.json|ledger/[0-9]+\.json|ledger/SUMMARY\.md|experiments\.md|learnings\.md"
                        r"|ledger/activity/[^/]+|loop/followers/[^/]+)$")
SHELL_KEYCHAIN = re.compile(r"\bsecurity\s+(find-(generic|internet)-password|dump-keychain)\b")
SHELL_MARKER_WRITE = re.compile(
    rf"/{MARKER}\b"                                                   # any path ending in the marker
    rf"|\b(touch|tee|cp|mv|rm|ln|install|truncate)\b[^;&|\n]*\b{MARKER}\b"
    rf"|>{{1,2}}\s*\S*\b{MARKER}\b")
# An agent CLI invoked with a prompt that starts with the approve command,
# e.g. `grok -p "/approve x"`. Not a mere mention of both words on one line.
SHELL_NESTED_APPROVE = re.compile(
    rf"(^|[\s;&|/])(grok|claude|codex)(\s+-{{1,2}}[\w-]+(\s+[^\s\"'-]\S*)?)*\s+[\"']?{re.escape(APPROVE_CMD)}\b")


def deny(reason: str) -> None:
    print(json.dumps({"decision": "deny", "reason": reason}))
    print(reason, file=sys.stderr)
    sys.exit(2)


def path_values(value) -> list[str]:
    """Every string in the tool input that looks like a single path."""
    if isinstance(value, dict):
        return [p for v in value.values() for p in path_values(v)]
    if isinstance(value, list):
        return [p for v in value for p in path_values(v)]
    if isinstance(value, str) and value and len(value) < 400 and not re.search(r"\s", value):
        return [value]
    return []


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    tool = str(event.get("toolName") or event.get("tool_name") or "")
    if tool in NO_WRITE or tool.startswith(("x_", "web_")):
        sys.exit(0)
    tool_input = event.get("toolInput") or event.get("tool_input") or {}
    approval_reason = (f"The {MARKER} file is created only by the operator typing {APPROVE_CMD} <slug>. "
                       "Ask the operator to review the draft and approve it.")
    if tool in SHELL:
        command = str(tool_input.get("command", "")) if isinstance(tool_input, dict) else ""
        if SHELL_MARKER_WRITE.search(command) or SHELL_NESTED_APPROVE.search(command):
            deny(approval_reason)
        if SHELL_KEYCHAIN.search(command):
            deny("X API keys stay in the Keychain and never enter a session. "
                 "Check them with python3 scripts/x_api.py keys; the client reads them itself.")
        sys.exit(0)
    for path in path_values(tool_input):
        if PurePosixPath(path).name == MARKER:
            deny(approval_reason)
        if LOOP_STATE.search(path):
            deny("Loop state and its generated views change only through python3 scripts/loop.py.")
    sys.exit(0)


if __name__ == "__main__":
    main()
