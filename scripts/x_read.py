#!/usr/bin/env python3
"""Read X through one read-only Grok call and print JSON. For skills running
anywhere, including Claude Code, which has no X tools.

    python3 scripts/x_read.py search "<X search query>"
    python3 scripts/x_read.py thread <root post id>

Search returns at most 10 posts per query. A value X did not return is null.

Grok has returned invented posts (24 Sep 2026: three made-up ids and handles). So every
post Grok returns is looked up by id in the X API (x_api.lookup, about $0.005 a post):
a post X doesn't have, or whose text doesn't match, is dropped and listed under
"dropped"; kept posts carry X's own author, time, text and numbers. If the lookup
can't run, nothing is returned.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys

from grok_read import run_structured
import x_api

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


def _plain(text: str | None) -> str:
    text = re.sub(r"https?://\S+", "", text or "")
    return " ".join(text.casefold().split())


def same_text(claimed: str | None, real: str | None) -> bool:
    """Grok may shorten or reflow a post; a real match shares its opening or most of its words."""
    a, b = _plain(claimed), _plain(real)
    if not a or not b:
        return False
    return a[:40] in b or difflib.SequenceMatcher(None, a, b).ratio() >= 0.6


def verify(posts: list[dict], lookup) -> tuple[list[dict], list[dict]]:
    """Keep only posts X has, with matching text, and replace their fields with X's own."""
    real = {p["id"]: p for p in lookup([str(p.get("id", "")) for p in posts])}
    kept, dropped = [], []
    for post in posts:
        found = real.get(str(post.get("id", "")))
        if found is None:
            dropped.append({"id": post.get("id"), "claimed_author": post.get("author"), "reason": "X has no such post"})
        elif not same_text(post.get("text"), found.get("text")):
            dropped.append({"id": post.get("id"), "claimed_author": post.get("author"),
                            "reason": "text does not match the real post"})
        else:
            m = found.get("public_metrics") or {}
            kept.append({**post, "author": found.get("author"), "created_at": found.get("created_at"),
                         "text": found.get("text"), "verified": True,
                         "metrics": {"views": m.get("impression_count"), "likes": m.get("like_count"),
                                     "reposts": m.get("retweet_count"), "quotes": m.get("quote_count"),
                                     "replies": m.get("reply_count"), "bookmarks": m.get("bookmark_count")}})
    return kept, dropped


def api_lookup(client: x_api.Client):
    return lambda ids: x_api.lookup(client, ids)


def main(argv: list[str] | None = None, reader=run_structured, lookup=None) -> int:
    parser = argparse.ArgumentParser(description="Read X through one read-only Grok call.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("search").add_argument("query")
    sub.add_parser("thread").add_argument("root_id")
    args = parser.parse_args(argv)
    if args.command == "thread" and not re.fullmatch(r"[0-9]{5,25}", args.root_id):
        print(json.dumps({"error": f"bad post id {args.root_id!r}"}), file=sys.stderr)
        return 1
    client = None
    if lookup is None:
        client = x_api.Client()
        lookup = api_lookup(client)
    try:
        if args.command == "search":
            data, cost = reader(search_prompt(args.query), SEARCH_SCHEMA)
            data = {"query": args.query, "limit": 10, **data}
            data["posts"], data["dropped"] = verify(data.get("posts") or [], lookup)
        else:
            data, cost = reader(thread_prompt(args.root_id), THREAD_SCHEMA)
            posts = [p for p in [data.get("root")] + list(data.get("own_replies") or []) if p]
            kept, data["dropped"] = verify(posts, lookup)
            kept_ids = {p["id"] for p in kept}
            data["root"] = next((p for p in kept if p["id"] == (data.get("root") or {}).get("id")), None)
            data["own_replies"] = [p for p in kept if p["id"] != (data["root"] or {}).get("id")
                                   and p["id"] in kept_ids]
    except (RuntimeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1
    except x_api.XApiError as exc:
        print(json.dumps({"error": f"could not check Grok's posts against X, so none are returned: {exc}"}),
              file=sys.stderr)
        return 1
    data["cost_usd"] = cost
    if client is not None:
        data["verify_cost_usd"] = client.usage()["cost_usd"]
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
