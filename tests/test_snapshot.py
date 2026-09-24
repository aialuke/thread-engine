#!/usr/bin/env python3
"""Checks for scripts/snapshot.py with a fake X reader. No network, no Keychain."""

from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import snapshot  # noqa: E402
import x_api  # noqa: E402

NOW = datetime(2026, 10, 10, 10, 0, tzinfo=timezone.utc)
ME = x_api.USER_ID


def at(hours: float, base: datetime = NOW) -> str:
    return (base - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def tweet(item_id: str, hours_ago: float, kind: str = "original", reply_to: str | None = None,
          conv: str | None = None, public: int = 100, organic: int = 100, visits: int = 0) -> dict:
    item = {"id": item_id, "created_at": at(hours_ago), "text": "@someone hello from the build",
            "conversation_id": conv or item_id,
            "public_metrics": {"impression_count": public, "like_count": 2, "reply_count": 1, "retweet_count": 0,
                               "quote_count": 0, "bookmark_count": 1},
            "organic_metrics": {"impression_count": organic, "like_count": 2, "reply_count": 1, "retweet_count": 0,
                                "user_profile_clicks": visits},
            "context_annotations": [{"domain": {"name": "Unified Twitter Taxonomy"}, "entity": {"name": "Technology"}}]}
    if kind in {"reply", "thread_card"}:
        item["referenced_tweets"] = [{"type": "replied_to", "id": conv or "1"}]
        item["in_reply_to_user_id"] = ME if kind == "thread_card" else reply_to
    return item


class FakeReader:
    def __init__(self, followers: list[dict], items: list[dict], mentions: list[dict] | None = None, fail: bool = False):
        self._followers, self.items, self._mentions, self.fail = followers, items, list(mentions or []), fail
        self.windows, self.since = [], []

    def followers(self) -> list[dict]:
        if self.fail:
            raise x_api.XApiError("Keychain has no consumer_key under thread-engine-x, or the Keychain is locked")
        return self._followers

    def timeline(self, start: str, end: str) -> list[dict]:
        self.windows.append((start, end))
        begin, finish = x_api.parse_time(start), x_api.parse_time(end)
        return [i for i in self.items if begin <= x_api.parse_time(i["created_at"]) < finish]

    def mentions(self, since_id):
        self.since.append(since_id)
        return self._mentions

    def usage(self) -> dict:
        return {"calls": 4, "items_read": 9, "cost_usd": 0.009, "missing_access_header": []}


FOLLOWERS = [{"id": "11", "username": "builder"}, {"id": "22", "username": "AwakenLuke"}]
MENTION = {"id": "3000000001", "author_id": "800", "conversation_id": "1000000001", "created_at": at(38),
           "referenced_tweets": [{"type": "replied_to", "id": "1000000001"}]}


class DailyRun(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "scripts").mkdir()
        shutil.copy(REPO / "scripts" / "loop.py", self.root / "scripts" / "loop.py")
        shutil.copy(REPO / ".gitignore", self.root / ".gitignore")
        for args in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"],
                     ["config", "commit.gpgsign", "false"]):
            subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)
        self.old_root, snapshot.ROOT = snapshot.ROOT, self.root
        snapshot.loop("init", "--self-handles", "exitzerocode,awakenluke")
        self.items = [
            tweet("1000000001", 40, organic=90, visits=2),
            tweet("1000000002", 40, kind="thread_card", conv="1000000001"),
            tweet("1000000003", 39, kind="reply", reply_to="900", conv="5000000001"),
            tweet("1000000004", 45, public=2000, organic=100),
        ]

    def tearDown(self) -> None:
        snapshot.ROOT = self.old_root
        self.tmp.cleanup()

    def run_once(self, reader: FakeReader, now: datetime = NOW) -> tuple[int, str]:
        out = io.StringIO()
        with redirect_stdout(out):
            code = snapshot.run(reader, now=now)
        return code, out.getvalue()

    def ledger(self, root_id: str) -> dict:
        return json.loads((self.root / "ledger" / f"{root_id}.json").read_text())

    def activity(self) -> dict:
        rows = {}
        for path in (self.root / "ledger" / "activity").glob("????-??.json"):
            rows.update(json.loads(path.read_text())["items"])
        return rows

    def state(self) -> dict:
        return json.loads((self.root / "loop" / "state.json").read_text())

    def test_first_run_records_whole_account_and_commits_no_private_data(self) -> None:
        code, out = self.run_once(FakeReader(FOLLOWERS, self.items, [MENTION]))
        self.assertEqual(code, 0, out)
        post = self.ledger("1000000001")
        self.assertEqual((post["auto"], post["lane"], post["cards"][0]["id"]), (True, "other", "1000000002"))
        snap = post["snapshots"][0]
        self.assertEqual((snap["kind"], snap["source"], snap["outside_replies"]), ("valid", "api", 1))
        self.assertEqual(snap["organic"]["profile_visits"], 2)
        self.assertIn("95%", self.ledger("1000000004")["nonorganic"]["reason"])
        self.assertIsNone(self.ledger("1000000001").get("nonorganic"))
        rows = self.activity()
        self.assertEqual(sorted(rows), ["1000000001", "1000000002", "1000000003", "1000000004"])
        self.assertEqual(rows["1000000003"]["reads"]["48h"]["label"], "valid")
        self.assertNotIn("someone", rows["1000000003"]["text"])
        self.assertEqual(self.state()["api"]["read48_until"], x_api.iso(NOW - timedelta(hours=36)))
        self.assertIn("snapshot ok", (self.root / "ledger" / "runs.log").read_text())
        tracked = subprocess.run(["git", "ls-files"], cwd=self.root, capture_output=True, text=True).stdout
        self.assertIn("ledger/activity/account.json", tracked)
        self.assertNotIn("loop/followers", tracked)
        self.assertNotIn("ledger/raw/api", tracked)
        self.assertIn("non-organic", out)

    def test_failed_read_records_nothing_and_moves_no_cursor(self) -> None:
        code, out = self.run_once(FakeReader(FOLLOWERS, self.items, fail=True))
        self.assertEqual(code, 1)
        self.assertIn("nothing was recorded", out)
        self.assertEqual(list((self.root / "ledger").glob("*.json")), [])
        self.assertNotIn("api", self.state())
        self.assertIn("snapshot failed", (self.root / "ledger" / "runs.log").read_text())

    def test_next_day_continues_from_cursor_and_credits_the_new_follower(self) -> None:
        self.run_once(FakeReader(FOLLOWERS, self.items, [MENTION]))
        later = NOW + timedelta(hours=24)
        reader = FakeReader(FOLLOWERS + [{"id": "800", "username": "replier"}], self.items)
        code, out = self.run_once(reader, now=later)
        self.assertEqual(code, 0, out)
        self.assertEqual(reader.windows[0][0], x_api.iso(NOW - timedelta(hours=36)))
        self.assertEqual(reader.since, ["3000000001"])
        day = json.loads((self.root / "ledger" / "activity" / "account.json").read_text())["days"][-1]
        self.assertEqual((day["new"], day["attributed"]), (1, {"1000000001": 1}))
        self.assertIn("1 of the new credited", out)
        summary = (self.root / "ledger" / "SUMMARY.md").read_text()
        row = next(line for line in summary.splitlines() if "x-1000000001" in line)
        self.assertEqual(row.split("|")[12].strip(), "≥1")

    def test_final_read_at_26_days(self) -> None:
        old = tweet("1000000009", 24 * 27, organic=300)
        code, out = self.run_once(FakeReader(FOLLOWERS, [old]))
        self.assertEqual(code, 0, out)
        self.assertEqual(self.ledger("1000000009")["snapshots"][-1]["kind"], "final")
        self.assertEqual(self.activity()["1000000009"]["reads"]["final"]["organic"]["impressions"], 300)
        self.assertEqual(self.state()["api"]["final_until"], x_api.iso(NOW - timedelta(days=26)))

    def test_ingest_backfill_sets_cursors(self) -> None:
        raw = {"fetched_at": x_api.iso(NOW), "since": "2026-10-01T00:00:00Z", "followers": FOLLOWERS,
               "timeline": self.items, "mentions": [MENTION]}
        path = self.root / "ledger" / "raw" / "api" / "backfill-test.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(raw))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(snapshot.ingest("ledger/raw/api/backfill-test.json"), 0)
        api = self.state()["api"]
        self.assertEqual((api["read48_until"], api["final_until"]),
                         (x_api.iso(NOW - timedelta(hours=36)), "2026-10-01T00:00:00Z"))
        self.assertEqual(self.activity()["1000000001"]["reads"]["backfill"]["label"], "backfill")


if __name__ == "__main__":
    unittest.main()
