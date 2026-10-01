"""The organic rates an Experiment can be scored on, and when a post or cohort is too thin to score.

Vocabulary is CONTEXT.md's. Plain values in, plain values out: no files, no clock, no argparse. A rate
comes from one organic observation, so numerator and denominator are read together. Root replies are left
out of engagement because a root's replies count the account's own thread cards (reference/x-api.md P8).
"""

from __future__ import annotations

import statistics
from typing import NamedTuple

from loop_core.reads import best_snapshot, valid_snapshot

MIN_IMPRESSIONS = 50
PRIMARIES = ("engagement_rate", "visit_rate")
MIN_VISIT_POSTS = 5
MAX_VISIT_SHARE = 0.5


def per_thousand(actions: int | None, organic: dict | None) -> float | None:
    """Actions per 1,000 organic impressions, or None when either number is missing. Missing is not zero."""
    impressions = (organic or {}).get("impressions")
    if actions is None or not impressions:
        return None
    return 1000 * actions / impressions


def engagement_rate(organic: dict | None) -> float | None:
    organic = organic or {}
    likes, reposts = organic.get("likes"), organic.get("reposts")
    if likes is None or reposts is None:
        return None
    return per_thousand(likes + reposts, organic)


def visit_rate(organic: dict | None) -> float | None:
    return per_thousand((organic or {}).get("profile_visits"), organic)


def rate(primary: str, organic: dict | None) -> float | None:
    if primary == "engagement_rate":
        return engagement_rate(organic)
    if primary == "visit_rate":
        return visit_rate(organic)
    return None


def above_floor(organic: dict | None) -> bool:
    impressions = (organic or {}).get("impressions")
    return impressions is not None and impressions >= MIN_IMPRESSIONS


class PrimaryScore(NamedTuple):
    """How one Snapshot scores on a primary.

    value is None when the post is left out: no Snapshot, or a count that was not measured.
    below_floor is True when a rate was measured but organic impressions are under MIN_IMPRESSIONS.
    A cohort leaves that post out. A round counts it as a miss, and value is then 0.
    """

    value: float | None
    below_floor: bool


def score_primary(snap: dict | None, metric: str) -> PrimaryScore:
    if snap is None:
        return PrimaryScore(None, False)
    if metric not in PRIMARIES:
        return PrimaryScore(snap.get("root", {}).get(metric), False)
    value = rate(metric, snap.get("organic"))
    if value is None:
        return PrimaryScore(None, False)
    if not above_floor(snap.get("organic")):
        return PrimaryScore(0.0, True)
    return PrimaryScore(value, False)


COHORT = "cohort"
ROUND = "round"
_SNAPSHOT_FOR = {COHORT: best_snapshot, ROUND: valid_snapshot}


class Scored(NamedTuple):
    """One post read for a cohort or a round.

    outcome is nonorganic (reason set; a cohort refuses, a round skips), unmeasured (both skip),
    below_floor (value 0; a cohort skips, a round counts a miss), or scored.
    A cohort reads the best snapshot. A round reads only a valid one.
    """

    outcome: str
    value: float | None
    snap_kind: str | None
    reason: str | None


def score_for(post: dict, metric: str, purpose: str) -> Scored:
    """How this post scores for `purpose` (cohort or round). Non-organic is decided once, here."""
    if post.get("nonorganic"):
        return Scored("nonorganic", None, None, (post.get("nonorganic") or {}).get("reason"))
    snap = _SNAPSHOT_FOR[purpose](post)
    score = score_primary(snap, metric)
    kind = snap["kind"] if snap else None
    if score.value is None:
        return Scored("unmeasured", None, kind, None)
    if score.below_floor:
        return Scored("below_floor", score.value, kind, None)
    return Scored("scored", score.value, kind, None)


def visit_screen(visits: list[int]) -> str | None:
    """Why a cohort's profile visits are too sparse to score visit_rate on, or None when they will do.

    `visits` is each cohort post's visit count. Checked in order: the median, how many posts had a visit,
    and whether one post supplies more than half of them.
    """
    if statistics.median(visits) <= 0:
        return "the cohort's median profile visits is 0, so a visit rate cannot tell posts apart"
    with_visits = [v for v in visits if v > 0]
    if len(with_visits) < MIN_VISIT_POSTS:
        return f"only {len(with_visits)} cohort posts had a profile visit; visit_rate needs {MIN_VISIT_POSTS}"
    if max(with_visits) > MAX_VISIT_SHARE * sum(with_visits):
        return "one cohort post has more than half of the profile visits"
    return None
