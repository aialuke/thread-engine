import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from loop_core import rates  # noqa: E402


def organic(impressions, likes=0, reposts=0, visits=0):
    return {"impressions": impressions, "likes": likes, "replies": 9, "reposts": reposts,
            "profile_visits": visits, "url_clicks": 0}


class Rates(unittest.TestCase):
    def test_engagement_rate_is_likes_plus_reposts_per_thousand_impressions(self) -> None:
        self.assertEqual(rates.engagement_rate(organic(200, likes=3, reposts=1)), 20.0)
        self.assertEqual(rates.engagement_rate(organic(100, likes=0)), 0.0)

    def test_engagement_rate_leaves_root_replies_out(self) -> None:
        self.assertEqual(rates.engagement_rate(organic(1000, likes=1)), 1.0)

    def test_visit_rate_is_profile_visits_per_thousand_impressions(self) -> None:
        self.assertEqual(rates.visit_rate(organic(500, visits=2)), 4.0)

    def test_missing_is_none_not_zero(self) -> None:
        for bad in (None, {}, organic(None), organic(0), {"impressions": 100, "likes": None, "reposts": 0}):
            with self.subTest(bad=bad):
                self.assertIsNone(rates.engagement_rate(bad))
        self.assertIsNone(rates.visit_rate({"impressions": 100, "profile_visits": None}))

    def test_rate_picks_the_primary(self) -> None:
        row = organic(100, likes=1, visits=5)
        self.assertEqual(rates.rate("engagement_rate", row), 10.0)
        self.assertEqual(rates.rate("visit_rate", row), 50.0)
        self.assertIsNone(rates.rate("likes", row))

    def test_the_floor_is_fifty_impressions_inclusive(self) -> None:
        self.assertFalse(rates.above_floor(organic(49)))
        self.assertTrue(rates.above_floor(organic(50)))
        self.assertFalse(rates.above_floor(None))
        self.assertFalse(rates.above_floor(organic(None)))


class ScorePrimary(unittest.TestCase):
    def test_a_rate_under_the_floor_is_a_forced_miss(self) -> None:
        snap = {"organic": organic(49, likes=5)}
        self.assertEqual(rates.score_primary(snap, "engagement_rate"), rates.PrimaryScore(0.0, True))

    def test_a_rate_at_the_floor_is_the_rate(self) -> None:
        snap = {"organic": organic(50, likes=5)}
        self.assertEqual(rates.score_primary(snap, "engagement_rate"), rates.PrimaryScore(100.0, False))

    def test_a_missing_rate_is_left_out(self) -> None:
        self.assertEqual(rates.score_primary(None, "engagement_rate"), rates.PrimaryScore(None, False))
        self.assertEqual(rates.score_primary({"organic": {}}, "visit_rate"), rates.PrimaryScore(None, False))

    def test_a_root_count_is_not_subject_to_the_floor(self) -> None:
        snap = {"root": {"bookmarks": 3}, "organic": organic(1)}
        self.assertEqual(rates.score_primary(snap, "bookmarks"), rates.PrimaryScore(3, False))


class VisitScreen(unittest.TestCase):
    def test_a_cohort_with_enough_spread_passes(self) -> None:
        self.assertIsNone(rates.visit_screen([1, 1, 2, 1, 3, 0]))

    def test_a_zero_median_is_refused(self) -> None:
        self.assertIn("median", rates.visit_screen([0, 0, 0, 0, 0, 1, 1, 1, 1]))

    def test_fewer_than_five_posts_with_a_visit_is_refused(self) -> None:
        self.assertIn("5", rates.visit_screen([2, 2, 2, 2]))

    def test_one_post_with_over_half_the_visits_is_refused(self) -> None:
        self.assertIn("half", rates.visit_screen([20, 1, 1, 1, 1, 1]))

    def test_exactly_half_is_allowed(self) -> None:
        self.assertIsNone(rates.visit_screen([5, 1, 1, 1, 1, 1]))


def snap(kind: str, impressions: int, likes: int = 10) -> dict:
    return {"kind": kind, "root": {"bookmarks": likes}, "organic": organic(impressions, likes=likes)}


class ScoreFor(unittest.TestCase):
    def test_a_cohort_can_use_a_late_snapshot_and_a_round_cannot(self) -> None:
        post = {"snapshots": [snap("late", 1000)]}
        cohort = rates.score_for(post, "engagement_rate", rates.COHORT)
        rnd = rates.score_for(post, "engagement_rate", rates.ROUND)
        self.assertEqual((cohort.outcome, cohort.snap_kind), ("scored", "late"))
        self.assertEqual(rnd.outcome, "unmeasured")

    def test_nonorganic_is_excluded_once(self) -> None:
        post = {"nonorganic": {"reason": "boosted"}, "snapshots": [snap("valid", 1000)]}
        got = rates.score_for(post, "bookmarks", rates.ROUND)
        self.assertEqual((got.outcome, got.reason), ("nonorganic", "boosted"))

    def test_below_floor_is_measured_and_counts_as_a_miss(self) -> None:
        post = {"snapshots": [snap("valid", 10)]}
        got = rates.score_for(post, "engagement_rate", rates.COHORT)
        self.assertEqual((got.outcome, got.value), ("below_floor", 0.0))


if __name__ == "__main__":
    unittest.main()
