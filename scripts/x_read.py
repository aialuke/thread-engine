#!/usr/bin/env python3
"""Read other people's posts from X and print JSON. For skills running anywhere,
including Claude Code, which has no X tools.

    python3 scripts/x_read.py search "<X API v2 search query>" [--hours 24] [--sort recency|relevancy]

Search returns at most 10 posts per query, from the last --hours hours (default 24,
at most 167). Queries use X API operators only (`-is:reply`, `min_replies:`, `lang:`);
website syntax such as `-filter:replies` or `min_faves:` is refused. The posts are X's
own data (author, time, text and numbers), so no id check is needed. A value X did not
return is null. Each call costs about $0.005 a post plus $0.010 an author (up to about
$0.15) and is logged to ledger/runs.log. Once a day's logged calls reach DAILY_CAP_USD the
next call is refused before it is sent.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import x_api

LIMIT = 10
LOG_LINE = re.compile(r"^(\d{4}-\d{2}-\d{2})T\S+ x_read search ok .*cost_usd=([0-9.]+)")
RUNS_LOG = x_api.ROOT / "ledger" / "runs.log"
DAILY_CAP_USD = 1.00   # about 6 full searches; the account's own daily snapshot is under $0.05


def shape(post: dict) -> dict:
    """One post as the skills read it: X's fields under plain names."""
    m = post.get("public_metrics") or {}
    return {"id": post.get("id"), "author": post.get("author"), "created_at": post.get("created_at"),
            "text": post.get("text"), "verified": True,
            "metrics": {"views": m.get("impression_count"), "likes": m.get("like_count"),
                        "reposts": m.get("retweet_count"), "quotes": m.get("quote_count"),
                        "replies": m.get("reply_count"), "bookmarks": m.get("bookmark_count")}}


def spent_today(log_path: Path, now: datetime) -> float:
    """USD already logged by x_read searches on this UTC date."""
    if not log_path.exists():
        return 0.0
    day, total = now.strftime("%Y-%m-%d"), 0.0
    for line in log_path.read_text(encoding="utf-8").splitlines():
        match = LOG_LINE.match(line)
        if match and match.group(1) == day:
            total += float(match.group(2))
    return total


def main(argv: list[str] | None = None, client: x_api.Client | None = None,
         log_path: Path = RUNS_LOG) -> int:
    parser = argparse.ArgumentParser(description="Read other people's posts from X API recent search.")
    sub = parser.add_subparsers(dest="command", required=True)
    sp = sub.add_parser("search")
    sp.add_argument("query")
    sp.add_argument("--hours", type=float, default=24)
    sp.add_argument("--sort", choices=("recency", "relevancy"), default="recency")
    args = parser.parse_args(argv)
    client = client or x_api.Client()
    now = datetime.now(timezone.utc)
    spent = spent_today(log_path, now)
    if spent >= DAILY_CAP_USD:
        print(json.dumps({"error": f"x_read searches have cost ${spent:.2f} today (cap ${DAILY_CAP_USD:.2f}); "
                                   "nothing was sent. Raising DAILY_CAP_USD in scripts/x_read.py is a Claude Code change."}),
              file=sys.stderr)
        return 1
    try:
        posts = x_api.search(client, args.query, hours=args.hours, sort_order=args.sort)
    except x_api.XApiError as exc:
        print(json.dumps({"error": str(exc), **client.usage()}), file=sys.stderr)
        return 1
    usage = client.usage()
    stamp = x_api.iso(now)
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"{stamp} x_read search ok api_items={usage['items_read']} cost_usd={usage['cost_usd']}\n")
    print(json.dumps({"query": args.query, "limit": LIMIT, "hours": args.hours, "sort": args.sort,
                      "posts": [shape(p) for p in posts], "cost_usd": usage["cost_usd"]},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
