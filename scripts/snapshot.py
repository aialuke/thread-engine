#!/usr/bin/env python3
"""Daily 36-60 hour snapshots. One read-only Grok call fetches the X numbers;
everything else (payloads, recording, missed marks, evaluation, commit) is code.

Run by the launchd job and by /next. Prints a short plain-English summary.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GROK = Path.home() / ".grok" / "bin" / "grok"
HANDLE = "exitzerocode"

COUNT = {"type": ["integer", "null"]}
SCHEMA = {
    "type": "object",
    "required": ["followers", "posts"],
    "properties": {
        "followers": COUNT,
        "posts": {"type": "array", "items": {
            "type": "object",
            "required": ["root_id", "root", "cards", "repliers", "error"],
            "properties": {
                "root_id": {"type": "string"},
                "root": {"type": "object",
                         "required": ["views", "likes", "reposts", "quotes", "replies", "bookmarks"],
                         "properties": {k: COUNT for k in ("views", "likes", "reposts", "quotes", "replies", "bookmarks")}},
                "cards": {"type": "array", "items": {"type": "object", "required": ["id", "views"],
                                                     "properties": {"id": {"type": "string"}, "views": COUNT}}},
                "repliers": {"type": "array", "items": {"type": "string"}},
                "error": {"type": ["string", "null"]},
            }}},
    },
}


def brief(due: list[dict]) -> str:
    lines = [
        f"Read-only. For each post id below by @{HANDLE}, return what the X read tools show now. Never estimate: a value you cannot read is null.",
        "- x_thread_fetch the root. Root numbers come from its Engagement line. For each listed card id, give its Views.",
        "- x_keyword_search conversation_id:<root id>, mode Top, limit 10; page older with max_id until fewer than 10 return or 5 pages. "
        f"repliers = every reply author handle without @, excluding @{HANDLE}, one entry per reply.",
        f"- x_user_search {HANDLE} once; followers = its Followers.",
        "- If a fetch fails, return that root with null numbers and the error text in error.",
        "",
    ]
    for post in due:
        lines.append(f"root {post['root_id']}; card ids: {', '.join(post['card_ids']) or 'none'}")
    return "\n".join(lines)


def last_json_object(text: str) -> dict:
    decoder = json.JSONDecoder()
    found, i = [], 0
    while (start := text.find("{", i)) >= 0:
        try:
            obj, i = decoder.raw_decode(text, start)
            found.append(obj)
        except json.JSONDecodeError:
            i = start + 1
    if not found:
        raise ValueError("no JSON object in Grok output")
    return found[-1]


def repliers_complete(post: dict, has_cards: bool) -> bool | None:
    replies = post["root"].get("replies")
    if replies is None:
        return None
    own_direct = 1 if has_cards else 0
    return replies - own_direct <= len(post["repliers"])


def loop(*args: str) -> dict:
    result = subprocess.run([sys.executable, "scripts/loop.py", *args], cwd=ROOT,
                            capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return json.loads(result.stdout)


def fetch(due: list[dict]) -> tuple[dict, float | None]:
    result = subprocess.run(
        [str(GROK), "-p", brief(due), "--json-schema", json.dumps(SCHEMA), "--output-format", "json",
         "--sandbox", "read-only", "--deny", "Bash", "--deny", "Edit", "--deny", "Write", "--effort", "low"],
        cwd=ROOT, capture_output=True, text=True, check=False, timeout=900)
    if result.returncode != 0:
        raise RuntimeError(f"grok exited {result.returncode}: {result.stderr.strip()[-300:]}")
    envelope = last_json_object(result.stdout)
    return last_json_object(envelope.get("text", "")), envelope.get("total_cost_usd")


def main(fetcher=fetch) -> int:
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M")
    due = loop("due")["due"]
    recorded, skipped, cost = [], [], None
    if due:
        data, cost = fetcher(due)
        raw = ROOT / "ledger" / "raw" / f"snapshot-{stamp}.json"
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        cards_by_root = {p["root_id"]: bool(p["card_ids"]) for p in due}
        for post in data.get("posts", []):
            root_id = str(post.get("root_id", ""))
            if root_id not in cards_by_root or post.get("error") or post["root"].get("views") is None:
                skipped.append(root_id)
                continue
            payload = {"root_id": root_id, "observed_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                       "root": post["root"], "cards": post["cards"], "repliers": post["repliers"],
                       "repliers_complete": repliers_complete(post, cards_by_root[root_id]),
                       "followers": data.get("followers"), "raw_file": str(raw.relative_to(ROOT))}
            inbox = ROOT / "loop" / "inbox" / f"snap-{root_id}.json"
            inbox.parent.mkdir(parents=True, exist_ok=True)
            inbox.write_text(json.dumps(payload), encoding="utf-8")
            result = loop("record-snapshot", "--json", str(inbox.relative_to(ROOT)))
            recorded.append((root_id, post["root"]["views"], result.get("kind")))
    missed = loop("mark-missed")["marked_missed"]
    events = loop("evaluate").get("events", [])
    with (ROOT / "ledger" / "runs.log").open("a", encoding="utf-8") as log:
        log.write(f"{now.isoformat(timespec='seconds')} snapshot due={len(due)} recorded={len(recorded)} "
                  f"skipped={len(skipped)} cost_usd={cost if cost is not None else 0}\n")
    loop("commit-data", "--message", f"snapshots {now.date().isoformat()}")
    for root_id, views, kind in recorded:
        print(f"Snapshot {root_id}: {views} views ({kind}).")
    for root_id in skipped:
        print(f"No snapshot for {root_id}: X did not return its numbers. It stays due until its window closes.")
    for root_id in missed:
        print(f"Missed {root_id}: its 36-60 hour window closed without a snapshot.")
    for event in events:
        print(f"Experiment moved from {event['from']} to {event['to']} ({event['result']}).")
    if not (recorded or skipped or missed or events):
        print("Nothing was due.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
