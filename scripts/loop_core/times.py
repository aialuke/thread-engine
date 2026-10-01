"""Timestamps as the loop stores them: ISO 8601 with a timezone in, UTC out. No clock here; callers pass `now`."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from loop_core.errors import LoopError

LOCAL_TZ = ZoneInfo("Australia/Brisbane")


def parse_time(value: str) -> datetime:
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LoopError(f"bad time {value!r}; use ISO 8601 with a timezone") from exc
    if stamp.tzinfo is None:
        raise LoopError(f"time {value!r} has no timezone")
    return stamp.astimezone(timezone.utc)


def iso(stamp: datetime) -> str:
    return stamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def local(stamp_iso: str) -> str:
    return parse_time(stamp_iso).astimezone(LOCAL_TZ).strftime("%a %d %b %H:%M")
