#!/usr/bin/env python3
"""Read X through one read-only Grok call and print JSON. For skills running
anywhere, including Claude Code, which has no X tools.

    python3 scripts/x_read.py search "<X search query>"
    python3 scripts/x_read.py thread <root post id>

Search returns at most 10 posts per query. A value X did not return is null.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

from grok_read import run_structured

HANDLE = "exitzerocode"
STR = {"type": ["string", "null"]}
INT = {"type": ["integer", "null"]}
METRICS = {k: INT for k in ("views", "likes", "reposts", "quotes", "replies", "bookmarks")}
POST = {"type": "object", "required": ["id", "author", "created_at", "text"],
        "properties": {"id": {"type": "string"}, "author": STR, "created_at": STR, "text": STR,
                       "media": {"type": "array", "items": {"type": "string"}},
                       "metrics": {"type": "object", "properties": METRICS}}}
SEARCH_SCHEMA = {"type": "object", "required": ["posts", "error"],
                 "properties": {"posts": {"type": "array", "items": POST}, "error": STR}}
THREAD_SCHEMA = {"type": "object", "required": ["root", "own_replies", "error"],
                 "properties": {"root": POST, "own_replies": {"type": "array", "items": POST}, "error": STR}}
EVIDENCE = ("Never estimate: a value you could not read is null. created_at is ISO 8601 UTC ending in Z. "
            "author is the handle without @. If a call fails, put its error text in error.")


def search_prompt(query: str) -> str:
    return (f"Read-only. Run x_keyword_search once with this exact query, mode Latest, limit 10: {query}\n"
            f"Return every post it gives, with metrics from its Engagement line. {EVIDENCE}")


def thread_prompt(root_id: str) -> str:
    return (f"Read-only. x_thread_fetch post {root_id}. root is that post with metrics from its Engagement line "
            f"and its media types. own_replies are the replies by @{HANDLE} under it, in order, each with its "
            f"text, media and metrics. {EVIDENCE}")


def main(argv: list[str] | None = None, reader=run_structured) -> int:
    parser = argparse.ArgumentParser(description="Read X through one read-only Grok call.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("search").add_argument("query")
    sub.add_parser("thread").add_argument("root_id")
    args = parser.parse_args(argv)
    if args.command == "thread" and not re.fullmatch(r"[0-9]{5,25}", args.root_id):
        print(json.dumps({"error": f"bad post id {args.root_id!r}"}), file=sys.stderr)
        return 1
    try:
        if args.command == "search":
            data, cost = reader(search_prompt(args.query), SEARCH_SCHEMA)
            data = {"query": args.query, "limit": 10, **data}
        else:
            data, cost = reader(thread_prompt(args.root_id), THREAD_SCHEMA)
    except (RuntimeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1
    data["cost_usd"] = cost
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
