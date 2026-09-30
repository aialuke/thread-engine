"""What each Payload must look like: the shape, ranges and vocabularies of a post, a Snapshot and an activity item.

Plain values in, LoopError out. No files, no clock, no repo state: whether a post exists or a Read is
a duplicate is loop.py's to decide. Messages are part of the CLI, so they do not change here.
"""

from __future__ import annotations

import re
from datetime import datetime

from loop_core.errors import need
from loop_core.times import iso, parse_time

FORMATS = {"settings", "comparison", "tool-swap", "single-tip", "build-log", "tool-verdict", "other"}
ARMS = {"treatment", "control", "none"}
EDIT_CLASSES = {"preference", "correction", "deviation", "violation"}
METRICS = ("views", "likes", "reposts", "quotes", "replies", "bookmarks")
ITEM_KINDS = {"original", "quote", "reply", "thread_card", "repost"}
PUBLIC_KEYS = ("impressions", "likes", "replies", "reposts", "quotes", "bookmarks")
ORGANIC_KEYS = ("impressions", "likes", "replies", "reposts", "profile_visits", "url_clicks")
POST_ID_RE = re.compile(r"^[0-9]{5,25}$")
READ_STAGES = {"backfill", "48h", "final"}
CURSOR_KEYS = ("read48_until", "final_until")


def check_count(value, field: str) -> None:
    need(value is None or (isinstance(value, int) and not isinstance(value, bool) and value >= 0),
         f"{field} must be a non-negative integer or null")


def validate_post(post: dict) -> None:
    need(POST_ID_RE.fullmatch(str(post.get("root_id", ""))) is not None, "root_id missing or bad")
    need(isinstance(post.get("slug"), str) and post["slug"], "slug required")
    need(post.get("format") in FORMATS, f"format must be one of {sorted(FORMATS)}")
    need(post.get("lane") in {"main", "other"}, "lane must be main or other")
    parse_time(post.get("posted_at", ""))
    need(isinstance(post.get("retrospective"), bool), "retrospective must be true or false")
    need(isinstance(post.get("made_in_repo"), bool), "made_in_repo must be true or false")
    need(post.get("arm", "none") in ARMS, f"arm must be one of {sorted(ARMS)}")
    need(isinstance(post.get("cards", []), list), "cards must be a list")
    for card in post.get("cards", []):
        need(POST_ID_RE.fullmatch(str(card.get("id", ""))) is not None, "card id bad")
        need(isinstance(card.get("text", ""), str), "card text must be text")
    for edit in post.get("edits", []):
        need(edit.get("class") in EDIT_CLASSES, f"edit class must be one of {sorted(EDIT_CLASSES)}")
    check_count(post.get("production_minutes"), "production_minutes")
    mark = post.get("nonorganic")
    need(mark is None or (isinstance(mark, dict) and isinstance(mark.get("reason"), str)),
         "nonorganic must be null or {reason, at}")
    for snap in post.get("snapshots", []):
        validate_snapshot(snap)


def validate_snapshot(snap: dict) -> None:
    parse_time(snap.get("observed_at", ""))
    need(snap.get("kind") in {"valid", "late", "early", "final"}, "snapshot kind bad")
    for metric in METRICS:
        check_count(snap.get("root", {}).get(metric), f"root.{metric}")
    for key, value in (snap.get("organic") or {}).items():
        need(key in ORGANIC_KEYS, f"unknown organic measure {key!r}")
        check_count(value, f"organic.{key}")
    check_count(snap.get("followers"), "followers")
    for card in snap.get("cards", []):
        check_count(card.get("views"), "card views")


def validate_item(item: dict) -> None:
    need(POST_ID_RE.fullmatch(str(item.get("id", ""))) is not None, "item id missing or bad")
    need(item.get("kind") in ITEM_KINDS, f"item kind must be one of {sorted(ITEM_KINDS)}")
    parse_time(item.get("created_at", ""))
    need(POST_ID_RE.fullmatch(str(item.get("conversation_id", ""))) is not None, "item conversation_id bad")
    for group, keys in (("public", PUBLIC_KEYS), ("organic", ORGANIC_KEYS)):
        for key, value in (item.get(group) or {}).items():
            need(key in keys, f"unknown {group} measure {key!r}")
            check_count(value, f"{group}.{key}")


def post_from_payload(payload: dict) -> dict:
    """The post record a record-post Payload describes, defaults filled in and validated. No snapshots yet."""
    post = {
        "root_id": str(payload.get("root_id", "")),
        "slug": payload.get("slug"),
        "format": payload.get("format"),
        "lane": payload.get("lane"),
        "posted_at": payload.get("posted_at", ""),
        "retrospective": payload.get("retrospective", False),
        "made_in_repo": payload.get("made_in_repo", True),
        "experiment": payload.get("experiment"),
        "arm": payload.get("arm", "none"),
        "hypothesis": payload.get("hypothesis"),
        "cards": payload.get("cards", []),
        "media": payload.get("media", []),
        "ai_media": payload.get("ai_media", False),
        "production_minutes": payload.get("production_minutes"),
        "edits": payload.get("edits", []),
        "draft": payload.get("draft"),
        "snapshots": [],
        "missed": False,
        "auto": bool(payload.get("auto", False)),
    }
    validate_post(post)
    return post


def snapshot_from_payload(payload: dict, observed: datetime, hours: float, kind: str, self_handles: list[str]) -> dict:
    """The Snapshot a record-snapshot Payload describes, for a Read already placed at `hours` old as `kind`."""
    if payload.get("repliers") is not None:
        own = set(self_handles)
        repliers = [str(h).lstrip("@").lower() for h in payload["repliers"]]
        outside = [h for h in repliers if h not in own]
        outside_count, outside_names = len(outside), sorted(set(outside))
    else:
        # X API reads count outside replies by id; names of other accounts are not stored.
        outside_count, outside_names = payload.get("outside_replies"), []
        check_count(outside_count, "outside_replies")
    root = {m: payload.get("root", {}).get(m) for m in METRICS}
    snap = {
        "observed_at": iso(observed),
        "age_hours": round(hours, 1),
        "kind": kind,
        "source": payload.get("source", "grok"),
        "root": root,
        "cards": payload.get("cards", []),
        "outside_replies": outside_count,
        "outside_repliers": outside_names,
        "repliers_complete": payload.get("repliers_complete"),
        "followers": payload.get("followers"),
        "raw_file": payload.get("raw_file"),
        "missing": [m for m in METRICS if root[m] is None],
    }
    if payload.get("organic") is not None:
        snap["organic"] = {k: payload["organic"].get(k) for k in ORGANIC_KEYS}
    validate_snapshot(snap)
    return snap


def activity_header(payload: dict) -> tuple[str, datetime]:
    """The stage and observation time of a record-activity Payload."""
    stage = payload.get("stage")
    need(stage in READ_STAGES, f"stage must be one of {sorted(READ_STAGES)}")
    return stage, parse_time(payload.get("observed_at", ""))


def cursor_updates(payload: dict) -> dict[str, str]:
    """The read cursors a record-activity Payload moves, as stored timestamps. Absent or empty ones stay put."""
    given = payload.get("cursor") or {}
    return {key: iso(parse_time(given[key])) for key in CURSOR_KEYS if given.get(key)}
