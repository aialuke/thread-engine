#!/usr/bin/env python3
"""Read other people's posts from X and print JSON. For skills running anywhere.

    python3 scripts/x_read.py search "<X API v2 search query>" [--hours 24] [--sort recency|relevancy]

Search returns at most 10 posts per query, from the last --hours hours (default 24,
at most 167). Queries use X API operators only (`-is:reply`, `min_replies:`, `lang:`);
website syntax such as `-filter:replies` or `min_faves:` is refused. The posts are X's
own data (author, time, text and numbers), so no id check is needed. A value X did not
return is null. Each call costs about $0.005 a post plus $0.010 an author (up to about
$0.15) and is logged to ledger/runs.log.

A search that saved its result and then died before the log line is resumed from that
file on the next call in the same UTC hour. The posts are not fetched again.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import durable
import x_api

LIMIT = 10
RUNS_LOG = x_api.ROOT / "ledger" / "runs.log"


def shape(post: dict) -> dict:
    return {"id": post.get("id"), "author": post.get("author"), "created_at": post.get("created_at"),
            "text": post.get("text"), "verified": post.get("verified"),
            "metrics": x_api.public_counts(post.get("public_metrics"))}


def _search_key(query: str, hours: float, sort: str, now: datetime) -> str:
    raw = f"{query}\n{hours}\n{sort}\n{now.strftime('%Y%m%dT%H')}"
    return hashlib.sha256(raw.encode()).hexdigest()[:20]


def _resume(result_path: Path, pending_path: Path, log_path: Path) -> dict | None:
    """The saved result of a search that died after the fetch, or None when there is nothing to resume."""
    if not (result_path.is_file() and pending_path.is_file()):
        return None
    try:
        saved = json.loads(result_path.read_text(encoding="utf-8"))
        output = saved["output"]
        line = saved["log_line"]
    except (OSError, json.JSONDecodeError, KeyError):
        return None
    existing = log_path.read_text(encoding="utf-8") if log_path.is_file() else ""
    if line not in existing:
        durable.append_line(log_path, line)
    pending_path.unlink(missing_ok=True)
    return output


def _search(client: x_api.Client, query: str, hours: float, sort: str, now: datetime,
            log_path: Path) -> tuple[int, dict | None]:
    folder = log_path.parent / "x-read-cache"
    key = _search_key(query, hours, sort, now)
    result_path = folder / f"{key}.json"
    pending_path = folder / f"{key}.pending"
    resumed = _resume(result_path, pending_path, log_path)
    if resumed is not None:
        return 0, resumed
    if pending_path.is_file():
        try:
            holder = int(pending_path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            holder = None
        if holder is not None and holder != os.getpid() and durable.pid_alive(holder):
            print(json.dumps({"error": f"a search for this query is already running (pid {holder})"}),
                  file=sys.stderr)
            return 1, None
        pending_path.unlink(missing_ok=True)
    folder.mkdir(parents=True, exist_ok=True)
    pending_path.write_text(f"{os.getpid()}\n", encoding="utf-8")
    try:
        posts = x_api.search(client, query, hours=hours, sort_order=sort, now=now)
    except x_api.XApiError as exc:
        pending_path.unlink(missing_ok=True)
        print(json.dumps({"error": str(exc), **client.usage()}), file=sys.stderr)
        return 1, None
    usage = client.usage()
    output = {"query": query, "limit": LIMIT, "hours": hours, "sort": sort,
              "posts": [shape(p) for p in posts], "cost_usd": usage["cost_usd"]}
    line = (f"{x_api.iso(now)} x_read search ok api_items={usage['items_read']} "
            f"cost_usd={usage['cost_usd']}")
    durable.atomic_write(result_path, json.dumps({"log_line": line, "output": output}, ensure_ascii=False))
    durable.append_line(log_path, line)
    pending_path.unlink(missing_ok=True)
    return 0, output


def main(argv: list[str] | None = None, client: x_api.Client | None = None,
         log_path: Path = RUNS_LOG, now: datetime | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read other people's posts from X API recent search.")
    sub = parser.add_subparsers(dest="command", required=True)
    sp = sub.add_parser("search")
    sp.add_argument("query")
    sp.add_argument("--hours", type=float, default=24)
    sp.add_argument("--sort", choices=("recency", "relevancy"), default="recency")
    args = parser.parse_args(argv)
    client = client or x_api.Client()
    now = now or datetime.now(timezone.utc)
    code, output = _search(client, args.query, args.hours, args.sort, now, log_path)
    if code != 0 or output is None:
        return code
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
