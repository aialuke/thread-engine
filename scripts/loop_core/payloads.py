"""What each Payload must look like: the shape, ranges and vocabularies of a post, a Snapshot and an activity item.

Plain values in, LoopError out. No files, no clock, no repo state: whether a post exists or a Read is
a duplicate is loop.py's to decide. Messages are part of the CLI, so they do not change here.
"""

from __future__ import annotations

import functools
import re
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime

from loop_core.errors import LoopError, need
from loop_core.rates import PRIMARIES
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
MIN_COHORT = 3
SCORABLE = METRICS + PRIMARIES  # what open-experiment accepts as a primary; METRICS alone is what a Snapshot stores
# Stored, but never an experiment's primary: they cannot tell a better post from a worse one.
UNSCORABLE = {
    "views": "views include paid (boosted) reach and say nothing about follows",
    "replies": "a root's replies count the account's own thread cards",
}


@contextmanager
def malformed(command: str):
    """Report a wrong-shaped Payload as a refusal, not a traceback.

    Only what runs inside is covered: a missing key, a field of the wrong type, a number that is not one.
    loop.py's own state code is outside it, so a bug there still shows as the traceback it is.
    """
    try:
        yield
    except KeyError as exc:
        raise LoopError(f"{command}: payload is missing {exc.args[0]!r}") from exc
    except (TypeError, AttributeError, ValueError) as exc:
        raise LoopError(f"{command}: payload is malformed: {exc}") from exc


def guarded(command: str):
    def wrap(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            with malformed(command):
                return func(*args, **kwargs)
        return inner
    return wrap


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
    topics = item.get("topics", [])
    need(isinstance(topics, list) and all(isinstance(t, str) for t in topics), "item topics must be a list of text")


@guarded("record-post")
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


@guarded("record-snapshot")
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
        "source": payload.get("source", "agent"),
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


@guarded("record-activity")
def activity_header(payload: dict) -> tuple[str, datetime]:
    """The stage and observation time of a record-activity Payload."""
    stage = payload.get("stage")
    need(stage in READ_STAGES, f"stage must be one of {sorted(READ_STAGES)}")
    return stage, parse_time(payload.get("observed_at", ""))


@guarded("record-activity")
def cursor_updates(payload: dict) -> dict[str, str]:
    """The read cursors a record-activity Payload moves, as stored timestamps. Absent or empty ones stay put."""
    given = payload.get("cursor") or {}
    return {key: iso(parse_time(given[key])) for key in CURSOR_KEYS if given.get(key)}


def interaction_inputs(payload: dict) -> tuple[datetime, Iterator[tuple], Iterator[tuple], object]:
    """What a record-interactions Payload says: when, who replied to us, who we replied to, the newest id.

    Returns (observed, mentions, reply_targets, since_id). `mentions` and `reply_targets` are read lazily,
    one entry at a time as the caller consumes them, so a bad entry is met at the same point it always was:
    after the entries before it were applied and before the entries after it are looked at. A mention is
    (author, conversation_id, mention id, created_at, item replied to); a reply target is (user, item, at).
    Entries by us or by no one are dropped before their other fields are read. `since_id` comes back exactly
    as given: whether it is a number only matters once one is saved.
    """
    command = "record-interactions"
    with malformed(command):
        observed = parse_time(payload.get("observed_at", ""))
        self_ids = {str(i) for i in payload.get("self_ids", [])}
        since = payload.get("since_id")

    def mentions() -> Iterator[tuple]:
        with malformed(command):
            for mention in payload.get("mentions", []):
                author = str(mention.get("author_id", ""))
                if not author or author in self_ids:
                    continue
                conversation = str(mention["conversation_id"])
                created_at = mention["created_at"]
                item = str(mention.get("replied_to") or mention["conversation_id"])
                parse_time(created_at)
                yield author, conversation, mention["id"], created_at, item

    def targets() -> Iterator[tuple]:
        with malformed(command):
            for target in payload.get("reply_targets", []):
                user = str(target.get("user_id", ""))
                if user and user not in self_ids:
                    item, at = str(target["item_id"]), target["at"]
                    parse_time(at)
                    yield user, item, at

    return observed, mentions(), targets(), since


def newer_since_id(since: object, saved: object) -> str | None:
    """The mentions cursor to keep: `since` when it is set and beats the `saved` one, else None.

    With no cursor saved, `since` must read as a whole number, so a bad first one is refused before it is saved.
    Once one is saved, `since` is compared as `int(since)`, as it always was.
    """
    if not since:
        return None
    if not saved:
        with malformed("record-interactions"):
            int(str(since))
        return str(since)
    with malformed("record-interactions"):
        newest = int(since)
    try:
        kept = int(saved)
    except (TypeError, ValueError) as exc:
        raise LoopError(f"record-interactions: the saved mentions_since_id {saved!r} is not a number") from exc
    return str(since) if newest > kept else None


@guarded("record-followers")
def follower_inputs(payload: dict) -> tuple[datetime, list[str]]:
    """When a record-followers Payload was read, and its follower ids without our own, sorted."""
    observed = parse_time(payload.get("observed_at", ""))
    self_ids = {str(i) for i in payload.get("self_ids", [])}
    need("ids" in payload, "record-followers: ids required (a missing list would record zero followers)")
    need(isinstance(payload["ids"], list), "record-followers: ids must be a list")
    return observed, sorted({str(i) for i in payload["ids"]} - self_ids)


@guarded("record-followers")
def follower_total(payload: dict, ids: list[str]) -> object:
    """The account's follower count: the Payload's `total` when it gives one, else how many ids it listed."""
    return payload.get("total", len(ids))


@guarded("record-followers")
def verified_count(payload: dict) -> int | None:
    """The verified-follower count, or None when the Payload has none."""
    if payload.get("verified") is None:
        return None
    check_count(payload["verified"], "verified")
    return payload["verified"]


@guarded("open-experiment")
def experiment_terms(payload: dict) -> tuple[str, float, list[str]]:
    """The measure, the effect to beat and the cohort of an open-experiment Payload."""
    metric = str(payload.get("primary") or "")
    need(metric in SCORABLE, f"primary must be one of {SCORABLE}")
    need(metric not in UNSCORABLE, f"primary {metric!r} cannot be scored: {UNSCORABLE.get(metric, '')}")
    effect = float(payload.get("effect", 1.5))
    need(effect > 1.0, "effect must be above 1.0")
    raw = payload.get("cohort", [])
    need(isinstance(raw, list), "cohort must be a list of post ids")
    cohort = [str(c) for c in raw]
    need(len(cohort) >= MIN_COHORT, f"cohort needs at least {MIN_COHORT} posts")
    for root_id in cohort:
        need(cohort.count(root_id) == 1, f"cohort lists {root_id} more than once")
        need(POST_ID_RE.match(root_id) is not None, f"cohort has {root_id!r}, which is not a post id")
    return metric, effect, cohort


@guarded("open-experiment")
def experiment_texts(payload: dict) -> dict:
    """The question, the two arms and any reference facts of an open-experiment Payload. The three texts are required."""
    for field in ("question", "treatment", "control"):
        need(isinstance(payload.get(field), str) and payload[field].strip(), f"{field} required")
    return {"question": payload["question"], "treatment": payload["treatment"], "control": payload["control"],
            "reference_facts": payload.get("reference_facts", [])}


@guarded("record-snapshot")
def snapshot_root_id(payload: dict) -> str:
    """Which post a record-snapshot Payload is about. The first thing read, so a non-object Payload stops here."""
    return str(payload.get("root_id", ""))


@guarded("record-snapshot")
def snapshot_observed(payload: dict) -> datetime:
    return parse_time(payload.get("observed_at", ""))


@guarded("record-snapshot")
def snapshot_is_final(payload: dict) -> bool:
    """True when the Payload says its Read is a Final read."""
    return payload.get("stage") == "final"


def activity_items(payload: dict) -> Iterator[dict]:
    """The items of a record-activity Payload, each validated as the caller reaches it."""
    with malformed("record-activity"):
        for item in payload.get("items", []):
            validate_item(item)
            yield item
