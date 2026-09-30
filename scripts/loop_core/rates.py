"""The organic rates an Experiment can be scored on, and when a post or cohort is too thin to score.

Vocabulary is CONTEXT.md's. Plain values in, plain values out: no files, no clock, no argparse. A rate
comes from one organic observation, so numerator and denominator are read together. Root replies are left
out of engagement because a root's replies count the account's own thread cards (reference/x-api.md P8).
"""

from __future__ import annotations

import statistics

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
    """Organic likes plus reposts per 1,000 organic impressions."""
    organic = organic or {}
    likes, reposts = organic.get("likes"), organic.get("reposts")
    if likes is None or reposts is None:
        return None
    return per_thousand(likes + reposts, organic)


def visit_rate(organic: dict | None) -> float | None:
    """Organic profile visits per 1,000 organic impressions."""
    return per_thousand((organic or {}).get("profile_visits"), organic)


def rate(primary: str, organic: dict | None) -> float | None:
    """The named primary's value for one organic observation; None for anything else or when it is missing."""
    if primary == "engagement_rate":
        return engagement_rate(organic)
    if primary == "visit_rate":
        return visit_rate(organic)
    return None


def above_floor(organic: dict | None) -> bool:
    """True when the observation has at least MIN_IMPRESSIONS organic impressions."""
    impressions = (organic or {}).get("impressions")
    return impressions is not None and impressions >= MIN_IMPRESSIONS


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
