"""The Read-window rules: which stage a post is in, what a Snapshot counts as, which Reads are due.

Vocabulary is CONTEXT.md's. A 48h read is a Read of a post between 36 and 60 hours after it was
posted; a Final read is one at 26 days or older; a Backfill read is not tied to a post's age.
Every threshold lives here. Plain values in, plain values out: no files, no clock, no argparse.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import NamedTuple

from loop_core.errors import need

SNAPSHOT_MIN_H = 36.0
SNAPSHOT_MAX_H = 60.0
FINAL_MIN_DAYS = 26
FINAL_MAX_DAYS = 29  # X drops organic numbers at 30 days; stay a day inside. The timeline horizon uses this.
FINAL_WARN_H = FINAL_MAX_DAYS * 24 - 48  # a post without a Final read is at risk for its last 48 hours


def snapshot_kind(hours: float) -> str:
    if hours < SNAPSHOT_MIN_H:
        return "early"
    if hours <= SNAPSHOT_MAX_H:
        return "valid"
    return "late"


def best_snapshot(post: dict) -> dict | None:
    snaps = post.get("snapshots", [])
    for kind in ("valid", "late"):
        chosen = [s for s in snaps if s["kind"] == kind]
        if chosen:
            return chosen[0] if kind == "valid" else chosen[-1]
    return None


def valid_snapshot(post: dict) -> dict | None:
    for snap in post.get("snapshots", []):
        if snap["kind"] == "valid":
            return snap
    return None


def due_stage(hours: float, retrospective: bool) -> str | None:
    """Where a post with no 48h Snapshot stands: pending, due, or missed. None: leave it out.

    A retrospective post past the window is left out, not marked missed.
    """
    if retrospective and hours > SNAPSHOT_MAX_H:
        return None
    if hours < SNAPSHOT_MIN_H:
        return "pending"
    if hours <= SNAPSHOT_MAX_H:
        return "due"
    return "missed"


def window_label() -> str:
    return f"{SNAPSHOT_MIN_H:g}–{SNAPSHOT_MAX_H:g} hour"


def stage_label(stage: str) -> str:
    if stage == "48h":
        return f"{window_label()} read"
    if stage == "final":
        return f"final {FINAL_MIN_DAYS}–{FINAL_MAX_DAYS} day read"
    if stage == "backfill":
        return "backfill"
    raise ValueError(f"unknown read stage {stage!r}")


def past_window(hours: float) -> bool:
    return hours > SNAPSHOT_MAX_H


class ReadPosition(NamedTuple):
    """Where a root's 48h read stands. A Final read is a separate observation.

    valid: a snapshot from inside the window is stored.
    marked: the missed flag is set, and there is no valid snapshot.
    late: a late snapshot is stored, and the post is not marked missed.
    omitted: retrospective, past the window, with nothing usable stored.
    missed: past the window, not retrospective, nothing usable stored, not yet marked.
    due: inside the window, no valid snapshot.
    pending: before the window, no valid snapshot.
    """

    name: str


def read_position(post: dict, hours: float) -> ReadPosition:
    """The 48h position from the snapshots, the missed flag, and the age. Checked in that order."""
    if valid_snapshot(post):
        return ReadPosition("valid")
    if post.get("missed"):
        return ReadPosition("marked")
    if best_snapshot(post):
        return ReadPosition("late")
    if post.get("retrospective") and past_window(hours):
        return ReadPosition("omitted")
    return ReadPosition(due_stage(hours, False) or "pending")


_DUE_BUCKET = {
    "valid": None,
    "marked": None,
    "late": "missed",
    "omitted": None,
    "missed": "missed",
    "due": "due",
    "pending": "pending",
}


def due_bucket(post: dict, hours: float) -> str | None:
    """Which `due` list holds this post, or None when `due` leaves it out."""
    return _DUE_BUCKET[read_position(post, hours).name]


def snapshot_cell(post: dict) -> str:
    """The summary Snapshot cell: the best snapshot, else the missed flag, else pending.

    An unmarked miss stays pending until mark-missed writes the flag.
    """
    snap = best_snapshot(post)
    if snap:
        return f"{snap['kind']} {snap['age_hours']:g}h"
    if post.get("missed"):
        return "missed"
    return "pending"


def in_final_window(hours: float) -> bool:
    return FINAL_MIN_DAYS * 24 <= hours <= FINAL_MAX_DAYS * 24


def final_at_risk(hours: float) -> bool:
    return FINAL_WARN_H <= hours <= FINAL_MAX_DAYS * 24


def need_final_age(hours: float) -> None:
    need(in_final_window(hours), f"a final read needs a post {FINAL_MIN_DAYS} to {FINAL_MAX_DAYS} days old")


def backfill_cursor(fetched: datetime, since: datetime) -> dict[str, datetime]:
    return {"read48_until": fetched - timedelta(hours=SNAPSHOT_MIN_H), "final_until": since}


def read_windows(now: datetime, cursors: dict[str, datetime | None], horizon_days: float) -> list[dict]:
    """The Reads the Daily run should make at `now`, each with where it moves its cursor.

    `cursors` holds the saved read48_until / final_until (None when never read). The organic-metrics
    horizon is X's, so the caller passes it in. The 48h window is always returned: its cursor moves on
    even when there is nothing to fetch. The Final window is returned only when it is not empty.
    """
    floor = now - timedelta(days=horizon_days)
    read_from = max(cursors.get("read48_until") or now - timedelta(hours=SNAPSHOT_MAX_H), floor)
    read_to = now - timedelta(hours=SNAPSHOT_MIN_H)
    final_from = max(cursors.get("final_until") or floor, floor)
    final_to = now - timedelta(days=FINAL_MIN_DAYS)
    windows = [{"stage": "48h", "start": read_from, "end": read_to, "fetch": read_from < read_to,
                "cursor": {"read48_until": read_to}}]
    if final_from < final_to:
        windows.append({"stage": "final", "start": final_from, "end": final_to, "fetch": True,
                        "cursor": {"final_until": final_to}})
    return windows
