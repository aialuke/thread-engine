"""Whether the Daily run is healthy: warnings for a missed or failed run and for a Final read about to be lost.

Vocabulary is CONTEXT.md's. Plain values in, plain values out: no files, no clock, no argparse. The caller
(loop.py status) reads ledger/runs.log, the ledger and the clock. runs.log lines look like
`<iso time> snapshot ok ...` or `<iso time> snapshot failed [stage=<stage> ]error=<repr>`.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from loop_core.errors import LoopError
from loop_core.times import parse_time

STALE_RUN_H = 26  # the job runs every 24 hours; two hours of grace for a Mac that woke late
LOCAL_TZ = ZoneInfo("Australia/Brisbane")
FAILED_DETAIL = re.compile(r"(?:stage=(?P<stage>\S+) )?error=(?P<error>.*)")


def last_runs(lines: list[str]) -> dict:
    """The latest daily run and the latest successful one. Backfill (`ingest`) and unreadable lines are not runs."""
    last_ok, last = None, None
    for line in lines:
        parts = line.split(maxsplit=3)
        if len(parts) < 3 or parts[1] != "snapshot" or parts[2] not in ("ok", "failed"):
            continue
        try:
            at = parse_time(parts[0])
        except LoopError:
            continue
        outcome = parts[2]
        last = {"outcome": outcome, "at": at, "detail": parts[3] if outcome == "failed" and len(parts) > 3 else ""}
        if outcome == "ok":
            last_ok = at
    return {"last_ok": last_ok, "last": last}


def warnings(now: datetime, runs: dict, finals_at_risk: list[tuple[str, datetime]]) -> list[str]:
    """Plain-English warnings, in the order stale run, failed run, Final reads at risk. Empty when all is well.

    `finals_at_risk` is (root_id, cutoff) for each post with no Final read that is inside its last 48 hours.
    """
    out = []
    last_ok, last = runs["last_ok"], runs["last"]
    if last_ok is None:
        out.append("No daily run has been logged yet, so nothing is being read.")
    elif now - last_ok > timedelta(hours=STALE_RUN_H):
        hours = int((now - last_ok).total_seconds() // 3600)
        out.append(f"The daily run last succeeded {hours} hours ago. The job may not have run: "
                   "was the Mac off or locked? /snapshot reads the posts now.")
    if last is not None and last["outcome"] == "failed":
        found = FAILED_DETAIL.fullmatch(last["detail"])
        error = found["error"].strip("'\"") if found else last["detail"]
        if found and found["stage"]:
            out.append(f"The last daily run failed while recording (stage {found['stage']}): {error}. "
                       "Some records may be partly written.")
        else:
            out.append(f"The last daily run failed: the X read failed ({error}). Nothing was recorded.")
    for root_id, cutoff in finals_at_risk:
        when = cutoff.astimezone(LOCAL_TZ).strftime("%d %b %H:%M")
        out.append(f"Post {root_id} has no final read yet, and X stops returning its organic numbers after "
                   f"{when} Brisbane time.")
    return out
