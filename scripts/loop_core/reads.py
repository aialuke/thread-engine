"""The Read-window rules: which stage a post is in, what a Snapshot counts as, which Reads are due.

Vocabulary is CONTEXT.md's. A 48h read is a Read of a post between 36 and 60 hours after it was
posted; a Final read is one at 26 days or older; a Backfill read is not tied to a post's age.
Every threshold lives here. Plain values in, plain values out: no files, no clock, no argparse.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from loop_core.errors import need

SNAPSHOT_MIN_H = 36.0
SNAPSHOT_MAX_H = 60.0
FINAL_MIN_DAYS = 26
FINAL_MAX_DAYS = 29  # X drops organic numbers at 30 days; matches x_api.ORGANIC_DAYS (a test checks)
FINAL_WARN_H = FINAL_MAX_DAYS * 24 - 48  # a post without a Final read is at risk for its last 48 hours


def snapshot_kind(hours: float) -> str:
    if hours < SNAPSHOT_MIN_H:
        return "early"
    if hours <= SNAPSHOT_MAX_H:
        return "valid"
    return "late"


def best_snapshot(post: dict) -> dict | None:
    """The 48h Snapshot if there is one, else the latest late one."""
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
    """The 48h window as prose, e.g. "36–60 hour". The generated views quote it instead of restating it."""
    return f"{SNAPSHOT_MIN_H:g}–{SNAPSHOT_MAX_H:g} hour"


def past_window(hours: float) -> bool:
    """True once the 48h window has closed."""
    return hours > SNAPSHOT_MAX_H


def in_final_window(hours: float) -> bool:
    """True for a post old enough for its Final read and young enough for X to still return organic numbers."""
    return FINAL_MIN_DAYS * 24 <= hours <= FINAL_MAX_DAYS * 24


def final_at_risk(hours: float) -> bool:
    """True for a post inside the Final window's last 48 hours: it has one or two daily runs left to be read."""
    return FINAL_WARN_H <= hours <= FINAL_MAX_DAYS * 24


def need_final_age(hours: float) -> None:
    """Refuse a Final read of a post outside the Final window."""
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
