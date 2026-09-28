#!/usr/bin/env python3
"""PreToolUse hook for the literature-reader subagent's Write tool.

The reader may write one thing: its report. A write is allowed only to a
Markdown file inside a session scratchpad directory, or to a new Markdown file
under research/ in this repo. Existing repo files are never overwritten.
Everything else is refused with exit 2, whose stderr Claude Code shows the agent.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
RESEARCH = (REPO / "research").resolve()
TMP_ROOTS = (Path("/tmp").resolve(), Path("/private/tmp"))


def refuse(reason: str) -> int:
    print(f"literature-reader may only write its report: {reason}", file=sys.stderr)
    return 2


def in_scratchpad(path: Path) -> bool:
    return any(path.is_relative_to(root) for root in TMP_ROOTS) and "scratchpad" in path.parts


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return refuse("unreadable hook input")
    raw = (event.get("tool_input") or {}).get("file_path") or ""
    if not raw:
        return refuse("no file_path")
    path = Path(os.path.realpath(raw))
    if path.suffix != ".md":
        return refuse(f"{raw} is not a .md file")
    if in_scratchpad(path):
        return 0
    if path.is_relative_to(RESEARCH):
        if path.exists():
            return refuse(f"{raw} already exists; write a new file")
        return 0
    return refuse(f"{raw} is outside a scratchpad and research/")


if __name__ == "__main__":
    sys.exit(main())
