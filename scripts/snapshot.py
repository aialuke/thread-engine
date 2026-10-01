#!/usr/bin/env python3
"""Daily X API read of the account's own posts. Run by the launchd job and by /next.

Each run reads, through scripts/x_api.py (owned reads, see reference/x-api.md),
the windows `loop.py due-reads` hands back (see CONTEXT.md for Read, 48h read
and Final read):
- every post, reply and quote that has turned 36 hours old since the last run
  (its 36-60 hour read; later than 60 hours is labelled late);
- every item that has turned 26 days old: the final read, before X drops
  organic numbers at 30 days;
- follower ids, and mentions since the last run.

loop.py owns those thresholds and the read cursors; this script holds none.
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
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import durable  # noqa: E402
import x_api  # noqa: E402
from loop_core.reads import stage_label, window_label  # noqa: E402

ROOT = x_api.ROOT


def loop(*args: str) -> dict:
    result = subprocess.run([sys.executable, "scripts/loop.py", *args], cwd=ROOT,
                            capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return json.loads(result.stdout)


def inbox(name: str, data: dict) -> str:
    path = ROOT / "loop" / "inbox" / name
    durable.atomic_write(path, json.dumps(data, ensure_ascii=False))
    return str(path.relative_to(ROOT))


def stamp(value: str) -> str:
    """X returns milliseconds; the ledger keeps seconds."""
    return x_api.iso(x_api.parse_time(value))


def normalize(item: dict) -> dict:
    return {
        "id": item["id"],
        "kind": x_api.kind(item),
        "created_at": stamp(item["created_at"]),
        "conversation_id": item.get("conversation_id") or item["id"],
        "topics": sorted({a["entity"]["name"] for a in item.get("context_annotations") or []}),
        # The account's own words; other accounts' handles are not kept.
        "text": re.sub(r"@\w+", "@_", x_api.full_text(item)),
        "public": x_api.public_counts(item.get("public_metrics")),
        "organic": x_api.organic_counts(item.get("organic_metrics")),
    }


def snapshot_root(public: dict) -> dict:
    """A Snapshot's root counts. Activity stores the impression count as impressions; a Snapshot stores it as views."""
    return {"views": public.get("impressions"), "likes": public.get("likes"), "reposts": public.get("reposts"),
            "quotes": public.get("quotes"), "replies": public.get("replies"), "bookmarks": public.get("bookmarks")}


class ApiReader:
    """The three reads the daily run needs, over one x_api client."""

    def __init__(self, client: x_api.Client | None = None) -> None:
        self.client = client or x_api.Client()

    def followers(self) -> list[dict]:
        return x_api.followers(self.client)

    def timeline(self, start: str, end: str, now: datetime | None = None) -> list[dict]:
        return x_api.timeline(self.client, start, end, now)

    def mentions(self, since_id: str | None) -> list[dict]:
        return x_api.mentions(self.client, since_id)

    def usage(self) -> dict:
        return self.client.usage()


def process(observed: datetime, followers: list[dict], windows: list[tuple[str, list[dict], dict]],
            mentions: list[dict], raw_file: str, self_handles: list[str]) -> list[str]:
    """Record one run's reads through loop.py. Returns plain-English lines.

    self_handles comes from the due-reads answer the run already asked for.
    """
    at = x_api.iso(observed)
    handles = {handle.lower() for handle in self_handles}
    self_ids = {x_api.USER_ID} | {f["id"] for f in followers if (f.get("username") or "").lower() in handles}
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
        normalized = {i["id"]: normalize(i) for i in items}
        for item in sorted(items, key=lambda i: i["created_at"]):
            if x_api.kind(item) not in {"original", "quote"}:
                continue
            if item["id"] not in ledger:
                cards = [{"id": c["id"], "text": x_api.full_text(c)} for c in items
                         if x_api.kind(c) == "thread_card" and c.get("conversation_id") == item["id"]]
                cards = sorted(cards, key=lambda c: int(c["id"]))
                loop("record-post", "--json", inbox(f"post-{item['id']}.json", {
                    "root_id": item["id"], "slug": f"x-{item['id']}", "format": "other", "lane": "other",
                    "posted_at": stamp(item["created_at"]), "retrospective": True, "made_in_repo": False,
                    "auto": True, "cards": cards}))
                ledger.add(item["id"])
                lines.append(f"Recorded {item['id']} automatically: posted outside the repo, lane 'other' until reviewed.")
                post = {"cards": cards}
            else:
                post = json.loads((ROOT / "ledger" / f"{item['id']}.json").read_text())
            row = normalized[item["id"]]
            payload = {"root_id": item["id"], "observed_at": at, "source": "api", "raw_file": raw_file,
                       "root": snapshot_root(row["public"]),
                       "organic": row["organic"], "outside_replies": outside.get(item["id"], 0),
                       "repliers_complete": True, "followers": follow["followers"],
                       "cards": [{"id": c["id"], "views": snapshot_root(normalized[c["id"]]["public"])["views"]}
                                 for c in post.get("cards", []) if c["id"] in normalized]}
            if stage == "final":
                payload["stage"] = "final"
            loop("record-snapshot", "--json", inbox(f"snap-{item['id']}.json", payload))
            share = x_api.nonorganic_share(item)
            if share is not None and share > x_api.NONORGANIC_SHARE and not post.get("nonorganic"):
                loop("mark-nonorganic", "--root-id", item["id"], "--reason",
                     f"{round(share * 100)}% of {row['public']['impressions']} impressions non-organic at the {stage} read")
                lines.append(f"Marked {item['id']} non-organic: {round(share * 100)}% of its reach was not organic.")
        made = loop("record-activity", "--json", inbox(f"activity-{stage}.json", {
            "stage": stage, "observed_at": at, "items": [normalized[i["id"]] for i in items], "cursor": cursor}))
        label = stage_label(stage)
        lines.append(f"{label}: {made['recorded']} posts, replies and quotes.")
    for root_id in loop("mark-missed")["marked_missed"]:
        lines.append(f"Missed {root_id}: its {window_label()} window closed without a snapshot.")
    for event in loop("evaluate").get("events", []):
        lines.append(f"Experiment moved from {event['from']} to {event['to']} ({event['result']}).")
    return lines


def log(line: str) -> None:
    durable.append_line(ROOT / "ledger" / "runs.log", line)


def run(reader=None, now: datetime | None = None) -> int:
    try:
        lock = durable.acquire_write_lock(ROOT)
    except durable.LockBusy as exc:
        print(f"The daily run is already going ({exc}). Nothing was started.")
        return 1
    try:
        return _run(reader, now)
    finally:
        lock.release()


def _run(reader=None, now: datetime | None = None) -> int:
    # One whole-second clock for the run: loop.py builds the windows from it, and x_api.timeline checks each
    # window against it. iso() drops fractions, so a fractional clock would put the floor just outside the horizon.
    now = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    plan = loop("--now", x_api.iso(now), "due-reads", "--horizon-days", str(x_api.ORGANIC_DAYS))
    private = ROOT / "loop" / "followers" / "interactions.json"
    since = json.loads(private.read_text()).get("mentions_since_id") if private.is_file() else None
    try:
        reader = reader or ApiReader()
        followers = reader.followers()
        reads = [(w, reader.timeline(w["start"], w["end"], now) if w["fetch"] else []) for w in plan["windows"]]
        mentions = reader.mentions(since)
    except (x_api.XApiError, RuntimeError) as exc:
        log(f"{x_api.iso(now)} snapshot failed error={str(exc)[:160]!r}")
        print(f"The X read failed, so nothing was recorded and nothing moved on: {exc}. "
              "The next run picks the same posts up.")
        return 1
    items48 = next((items for w, items in reads if w["stage"] == "48h"), [])
    final = next((items for w, items in reads if w["stage"] == "final"), [])
    windows = [(w["stage"], items, w["cursor"]) for w, items in reads]
    # Recording is not all-or-nothing: a failure here leaves earlier writes in place, so say so.
    stage = "raw-file"
    try:
        raw = durable.write_new_text(
            ROOT / "ledger" / "raw" / "api", f"run-{now.strftime('%Y%m%dT%H%M%S')}", ".json",
            json.dumps({"fetched_at": x_api.iso(now), "followers": followers, "read48": items48,
                        "final": final, "mentions": mentions}, indent=1, ensure_ascii=False) + "\n")
        stage = "record"
        lines = process(now, followers, windows, mentions, str(raw.relative_to(ROOT)), plan["self_handles"])
        stage = "usage"
        usage = reader.usage()
        log(f"{x_api.iso(now)} snapshot ok read48={len(items48)} final={len(final)} followers={len(followers)} "
            f"api_items={usage['items_read']} cost_usd={usage['cost_usd']}")
        stage = "commit-data"
        loop("commit-data", "--message", f"snapshots {now.date().isoformat()}")
    except Exception as exc:
        try:
            log(f"{x_api.iso(now)} snapshot failed stage={stage} error={str(exc)[:160]!r}")
        except OSError:
            pass
        print(f"The snapshot failed while at stage {stage}: {exc}. "
              "Some records may be partly written. Run /next to see it.")
        return 1
    lines.append(f"Estimated X API cost: ${usage['cost_usd']:.3f}.")
    print("\n".join(lines))
    return 0


def ingest(path: str) -> int:
    """Record a backfill file from x_api.py backfill: one 'backfill' read of every item, and the cursors."""
    try:
        lock = durable.acquire_write_lock(ROOT)
    except durable.LockBusy as exc:
        print(f"The daily run is already going ({exc}). Nothing was started.")
        return 1
    try:
        return _ingest(path)
    finally:
        lock.release()


def _ingest(path: str) -> int:
    raw = json.loads((ROOT / path).read_text(encoding="utf-8"))
    observed = x_api.parse_time(raw["fetched_at"])
    plan = loop("due-reads", "--backfill", "--fetched-at", raw["fetched_at"], "--since", raw["since"])
    lines = process(observed, raw["followers"], [("backfill", raw["timeline"], plan["cursor"])],
                    raw["mentions"], path, plan["self_handles"])
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
