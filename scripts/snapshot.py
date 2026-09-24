#!/usr/bin/env python3
"""Daily X API read of the account's own posts. Run by the launchd job and by /next.

Each run reads, through scripts/x_api.py (owned reads, see reference/x-api.md):
- every post, reply and quote that has turned 36 hours old since the last run
  (its 36-60 hour read; later than 60 hours is labelled late);
- every item that has turned 26 days old: the final read, before X drops
  organic numbers at 30 days;
- follower ids, and mentions since the last run.

Everything is recorded through loop.py. A failed read records nothing and moves
no cursor, so the next good run picks the same items up. Raw responses go to
ledger/raw/api/ (gitignored). Prints plain English.

    python3 scripts/snapshot.py
    python3 scripts/snapshot.py --ingest ledger/raw/api/backfill-<stamp>.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import x_api  # noqa: E402

ROOT = x_api.ROOT
READ48_MIN_H = 36
FINAL_MIN_DAYS = 26
NONORGANIC_SHARE = x_api.NONORGANIC_SHARE


def loop(*args: str) -> dict:
    result = subprocess.run([sys.executable, "scripts/loop.py", *args], cwd=ROOT,
                            capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return json.loads(result.stdout)


def inbox(name: str, data: dict) -> str:
    path = ROOT / "loop" / "inbox" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(path.relative_to(ROOT))


def stamp(value: str) -> str:
    """X returns milliseconds; the ledger keeps seconds."""
    return x_api.iso(x_api.parse_time(value))


def normalize(item: dict) -> dict:
    public = item.get("public_metrics") or {}
    organic = item.get("organic_metrics") or {}
    return {
        "id": item["id"],
        "kind": x_api.kind(item),
        "created_at": stamp(item["created_at"]),
        "conversation_id": item.get("conversation_id") or item["id"],
        "topics": sorted({a["entity"]["name"] for a in item.get("context_annotations") or []}),
        # The account's own words; other accounts' handles are not kept.
        "text": re.sub(r"@\w+", "@_", item.get("text", ""))[:300],
        "public": {"impressions": public.get("impression_count"), "likes": public.get("like_count"),
                   "replies": public.get("reply_count"), "reposts": public.get("retweet_count"),
                   "quotes": public.get("quote_count"), "bookmarks": public.get("bookmark_count")},
        "organic": {"impressions": organic.get("impression_count"), "likes": organic.get("like_count"),
                    "replies": organic.get("reply_count"), "reposts": organic.get("retweet_count"),
                    "profile_visits": organic.get("user_profile_clicks"),
                    "url_clicks": organic.get("url_link_clicks", 0) if organic else None},
    }


class ApiReader:
    """The three reads the daily run needs, over one x_api client."""

    def __init__(self, client: x_api.Client | None = None) -> None:
        self.client = client or x_api.Client()

    def followers(self) -> list[dict]:
        return x_api.followers(self.client)

    def timeline(self, start: str, end: str) -> list[dict]:
        return x_api.timeline(self.client, start, end)

    def mentions(self, since_id: str | None) -> list[dict]:
        return x_api.mentions(self.client, since_id)

    def usage(self) -> dict:
        return self.client.usage()


def process(observed: datetime, followers: list[dict], windows: list[tuple[str, list[dict], dict]],
            mentions: list[dict], raw_file: str) -> list[str]:
    """Record one run's reads through loop.py. Returns plain-English lines."""
    at = x_api.iso(observed)
    self_handles = set(json.loads((ROOT / "loop" / "state.json").read_text())["self_handles"])
    self_ids = {x_api.USER_ID} | {f["id"] for f in followers if (f.get("username") or "").lower() in self_handles}
    lines = []

    fetched = [i for _, items, _ in windows for i in items if x_api.kind(i) != "repost"]
    targets = [{"item_id": i["id"], "user_id": i["in_reply_to_user_id"], "at": stamp(i["created_at"])}
               for i in fetched if x_api.kind(i) == "reply" and i.get("in_reply_to_user_id")]
    mention_rows = [{"id": m["id"], "author_id": m.get("author_id"), "conversation_id": m.get("conversation_id") or m["id"],
                     "replied_to": next((r["id"] for r in m.get("referenced_tweets") or [] if r["type"] == "replied_to"), None),
                     "created_at": stamp(m["created_at"])} for m in mentions]
    since = max((m["id"] for m in mentions), key=int, default=None)
    talk = loop("record-interactions", "--json", inbox("interactions.json", {
        "observed_at": at, "self_ids": sorted(self_ids), "mentions": mention_rows,
        "reply_targets": targets, "since_id": since}))
    outside = talk["outside_replies"]

    verified = sum(1 for f in followers if f.get("verified") and f["id"] not in self_ids)
    follow = loop("record-followers", "--json", inbox("followers.json", {
        "observed_at": at, "self_ids": sorted(self_ids), "ids": [f["id"] for f in followers],
        "total": len(followers), "verified": verified}))
    lines.append(f"Verified followers: {follow.get('verified_followers')} of the 500 X's rewards program needs.")
    if follow.get("baseline"):
        lines.append(f"Followers: {follow['followers']} (first count, nothing to compare yet).")
    else:
        lines.append(f"Followers: {follow['followers']} ({follow['new']} new, {follow['lost']} lost; "
                     f"{follow['new'] - follow['unattributed']} of the new credited to something they engaged with).")

    ledger = {p.stem for p in (ROOT / "ledger").glob("*.json")}
    for stage, items, cursor in windows:
        items = [i for i in items if x_api.kind(i) != "repost"]
        by_id = {i["id"]: i for i in items}
        for item in sorted(items, key=lambda i: i["created_at"]):
            if x_api.kind(item) not in {"original", "quote"}:
                continue
            if item["id"] not in ledger:
                cards = [{"id": c["id"], "text": c.get("text", "")} for c in items
                         if x_api.kind(c) == "thread_card" and c.get("conversation_id") == item["id"]]
                loop("record-post", "--json", inbox(f"post-{item['id']}.json", {
                    "root_id": item["id"], "slug": f"x-{item['id']}", "format": "other", "lane": "other",
                    "posted_at": stamp(item["created_at"]), "retrospective": True, "made_in_repo": False,
                    "auto": True, "cards": sorted(cards, key=lambda c: int(c["id"]))}))
                ledger.add(item["id"])
                lines.append(f"Recorded {item['id']} automatically: posted outside the repo, lane 'other' until reviewed.")
            post = json.loads((ROOT / "ledger" / f"{item['id']}.json").read_text())
            row = normalize(item)
            payload = {"root_id": item["id"], "observed_at": at, "source": "api", "raw_file": raw_file,
                       "root": {"views": row["public"]["impressions"], "likes": row["public"]["likes"],
                                "reposts": row["public"]["reposts"], "quotes": row["public"]["quotes"],
                                "replies": row["public"]["replies"], "bookmarks": row["public"]["bookmarks"]},
                       "organic": row["organic"], "outside_replies": outside.get(item["id"], 0),
                       "repliers_complete": True, "followers": follow["followers"],
                       "cards": [{"id": c["id"], "views": (by_id[c["id"]].get("public_metrics") or {}).get("impression_count")}
                                 for c in post.get("cards", []) if c["id"] in by_id]}
            if stage == "final":
                payload["stage"] = "final"
            loop("record-snapshot", "--json", inbox(f"snap-{item['id']}.json", payload))
            share = x_api.nonorganic_share(item)
            if share is not None and share > NONORGANIC_SHARE and not post.get("nonorganic"):
                loop("mark-nonorganic", "--root-id", item["id"], "--reason",
                     f"{round(share * 100)}% of {row['public']['impressions']} impressions non-organic at the {stage} read")
                lines.append(f"Marked {item['id']} non-organic: {round(share * 100)}% of its reach was not organic.")
        made = loop("record-activity", "--json", inbox(f"activity-{stage}.json", {
            "stage": stage, "observed_at": at, "items": [normalize(i) for i in items], "cursor": cursor}))
        label = {"48h": "36–60 hour read", "final": "final 26–29 day read", "backfill": "backfill"}[stage]
        lines.append(f"{label}: {made['recorded']} posts, replies and quotes.")
    for root_id in loop("mark-missed")["marked_missed"]:
        lines.append(f"Missed {root_id}: its 36–60 hour window closed without a snapshot.")
    for event in loop("evaluate").get("events", []):
        lines.append(f"Experiment moved from {event['from']} to {event['to']} ({event['result']}).")
    return lines


def log(line: str) -> None:
    with (ROOT / "ledger" / "runs.log").open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def run(reader=None, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    api = loop("status").get("api", {})
    floor = now - timedelta(days=x_api.ORGANIC_DAYS)
    read_from = max(x_api.parse_time(api["read48_until"]) if api.get("read48_until") else now - timedelta(hours=60), floor)
    read_to = now - timedelta(hours=READ48_MIN_H)
    final_from = max(x_api.parse_time(api["final_until"]) if api.get("final_until") else floor, floor)
    final_to = now - timedelta(days=FINAL_MIN_DAYS)
    private = ROOT / "loop" / "followers" / "interactions.json"
    since = json.loads(private.read_text()).get("mentions_since_id") if private.is_file() else None
    try:
        reader = reader or ApiReader()
        followers = reader.followers()
        items48 = reader.timeline(x_api.iso(read_from), x_api.iso(read_to)) if read_from < read_to else []
        final = reader.timeline(x_api.iso(final_from), x_api.iso(final_to)) if final_from < final_to else []
        mentions = reader.mentions(since)
    except (x_api.XApiError, RuntimeError) as exc:
        log(f"{x_api.iso(now)} snapshot failed error={str(exc)[:160]!r}")
        print(f"The X read failed, so nothing was recorded and nothing moved on: {exc}. "
              "The next run picks the same posts up.")
        return 1
    raw = ROOT / "ledger" / "raw" / "api" / f"run-{now.strftime('%Y%m%dT%H%M')}.json"
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_text(json.dumps({"fetched_at": x_api.iso(now), "followers": followers, "read48": items48,
                               "final": final, "mentions": mentions}, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    windows = [("48h", items48, {"read48_until": x_api.iso(read_to)})]
    if final_from < final_to:
        windows.append(("final", final, {"final_until": x_api.iso(final_to)}))
    lines = process(now, followers, windows, mentions, str(raw.relative_to(ROOT)))
    usage = reader.usage()
    log(f"{x_api.iso(now)} snapshot ok read48={len(items48)} final={len(final)} followers={len(followers)} "
        f"api_items={usage['items_read']} cost_usd={usage['cost_usd']}")
    loop("commit-data", "--message", f"snapshots {now.date().isoformat()}")
    lines.append(f"Estimated X API cost: ${usage['cost_usd']:.3f}.")
    print("\n".join(lines))
    return 0


def ingest(path: str) -> int:
    """Record a backfill file from x_api.py backfill: one 'backfill' read of every item, and the cursors."""
    raw = json.loads((ROOT / path).read_text(encoding="utf-8"))
    observed = x_api.parse_time(raw["fetched_at"])
    cursor = {"read48_until": x_api.iso(observed - timedelta(hours=READ48_MIN_H)),
              "final_until": x_api.iso(x_api.parse_time(raw["since"]))}
    lines = process(observed, raw["followers"], [("backfill", raw["timeline"], cursor)], raw["mentions"], path)
    log(f"{x_api.iso(datetime.now(timezone.utc))} snapshot ingest {path} items={len(raw['timeline'])}")
    loop("commit-data", "--message", f"ingest {Path(path).name}")
    print("\n".join(lines))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Daily X API read of the account's own posts.")
    parser.add_argument("--ingest", help="record a backfill file from x_api.py backfill")
    args = parser.parse_args(argv)
    return ingest(args.ingest) if args.ingest else run()


if __name__ == "__main__":
    sys.exit(main())
