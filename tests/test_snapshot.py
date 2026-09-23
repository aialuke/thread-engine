#!/usr/bin/env python3
"""Checks for scripts/snapshot.py with a fake Grok fetcher. No network."""

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


class SnapshotScript(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "scripts").mkdir()
        shutil.copy(REPO / "scripts" / "loop.py", self.root / "scripts" / "loop.py")
        for args in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"],
                     ["config", "commit.gpgsign", "false"]):
            subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)
        self.old_root, snapshot.ROOT = snapshot.ROOT, self.root
        snapshot.loop("init", "--self-handles", "exitzerocode")
        posted = (datetime.now(timezone.utc) - timedelta(hours=40)).strftime("%Y-%m-%dT%H:%M:%SZ")
        for root_id, cards in (("1111111111", [{"id": "1111111112"}]), ("2222222222", [])):
            payload = self.root / f"post-{root_id}.json"
            payload.write_text(json.dumps({"root_id": root_id, "slug": f"s{root_id[:2]}", "format": "single-tip",
                                           "lane": "main", "posted_at": posted, "cards": cards}))
            snapshot.loop("record-post", "--json", str(payload))

    def tearDown(self) -> None:
        snapshot.ROOT = self.old_root
        self.tmp.cleanup()

    def fake(self, due):
        self.seen = [p["root_id"] for p in due]
        root = {"views": 500, "likes": 2, "reposts": 0, "quotes": 0, "replies": 5, "bookmarks": 3}
        return {"followers": 40, "posts": [
            {"root_id": "1111111111", "root": root, "cards": [{"id": "1111111112", "views": 50}],
             "repliers": ["a", "b"], "error": None},
            {"root_id": "2222222222", "root": dict(root, views=None), "cards": [], "repliers": [],
             "error": "Failed to fetch thread"},
        ]}, 0.12

    def test_records_good_posts_skips_failed_and_logs_cost(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            snapshot.main(fetcher=self.fake)
        self.assertEqual(sorted(self.seen), ["1111111111", "2222222222"])
        good = json.loads((self.root / "ledger" / "1111111111.json").read_text())
        self.assertEqual(good["snapshots"][0]["kind"], "valid")
        self.assertFalse(good["snapshots"][0]["repliers_complete"])
        bad = json.loads((self.root / "ledger" / "2222222222.json").read_text())
        self.assertEqual(bad["snapshots"], [])
        self.assertIn("cost_usd=0.12", (self.root / "ledger" / "runs.log").read_text())
        self.assertIn("It stays due", out.getvalue())
        log = subprocess.run(["git", "log", "--oneline"], cwd=self.root, capture_output=True, text=True).stdout
        self.assertIn("chore(data): snapshots", log)

    def test_posts_stay_due_when_fetch_returns_nothing(self) -> None:
        calls = []
        with redirect_stdout(io.StringIO()):
            snapshot.main(fetcher=lambda due: calls.append(due) or ({"followers": 1, "posts": []}, 0))
        self.assertEqual(len(calls), 1)  # both posts are due
        with redirect_stdout(io.StringIO()):
            snapshot.main(fetcher=lambda due: calls.append(due) or ({"followers": 1, "posts": []}, 0))
        self.assertEqual(len(calls), 2)  # still due: the fetch returned nothing

    def test_last_json_object_takes_final_complete_object(self) -> None:
        text = '{"posts": [{"root_id": "1", "error": "pending"}]} partial {"posts": []}'
        self.assertEqual(snapshot.last_json_object(text), {"posts": []})


if __name__ == "__main__":
    unittest.main()
