"""Whether a Read may become a Snapshot: the ordered rules record-snapshot applies to a post's ledger.

Plain values in, plain values out. The Payload is validated only after this admits the Read, so a
repeat valid or Final read is skipped even when its Payload is malformed.
"""

from __future__ import annotations

from typing import NamedTuple

from loop_core.errors import need
from loop_core.reads import need_final_age, snapshot_kind, valid_snapshot


class Admission(NamedTuple):
    """kind: what to record, or None. skip: why nothing is recorded, or None. Exactly one is set."""

    kind: str | None
    skip: str | None


def admit_snapshot(post: dict, hours: float, is_final: bool) -> Admission:
    """Decide what a Read of this post, taken `hours` after it was posted, becomes. Raises LoopError to refuse.

    The order is part of the interface: a Final read's age is refused before its duplicate is skipped, and
    a duplicate 48h read is skipped before a missed post refuses it.
    """
    need(hours >= 0, "observed before the post existed")
    kind = snapshot_kind(hours)
    if is_final:
        need_final_age(hours)
        kind = "final"
        if any(s["kind"] == "final" for s in post["snapshots"]):
            return Admission(None, "final read already exists")
    if kind == "valid" and valid_snapshot(post):
        return Admission(None, "valid snapshot already exists")
    need(not (kind == "valid" and post["missed"]), "post already marked missed")
    return Admission(kind, None)
