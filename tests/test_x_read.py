#!/usr/bin/env python3
"""Checks for scripts/x_read.py with a fake X API client. No network, no Keychain."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "tests"))

import x_read  # noqa: E402
from test_x_api import FakeOpener, FakeResponse, KEYS  # noqa: E402

import x_api  # noqa: E402

BODY = {"data": [{"id": "2102736605039776235", "author_id": "77", "created_at": "2026-09-23T12:00:00.000Z",
                  "text": "Is there a free alternative to Premiere?",
                  "public_metrics": {"impression_count": 1200, "like_count": 30, "retweet_count": 2,
                                     "quote_count": 1, "reply_count": 4, "bookmark_count": 7}}],
        "includes": {"users": [{"id": "77", "username": "asker"}]}}


class XRead(unittest.TestCase):
    def call(self, argv, *replies):
        opener = FakeOpener(*replies)
        client = x_api.Client(keys=KEYS, opener=opener, sleep=lambda s: None)
        out, err = io.StringIO(), io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "runs.log"
            with redirect_stdout(out), redirect_stderr(err):
                code = x_read.main(argv, client=client, log_path=log)
            text = log.read_text(encoding="utf-8") if log.exists() else ""
        return code, out.getvalue(), err.getvalue(), text, opener

    def test_search_returns_x_posts_with_plain_metrics_cost_and_a_log_line(self) -> None:
        code, out, _, log, opener = self.call(["search", '"is there a free" lang:en'], FakeResponse(BODY))
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual((data["query"], data["limit"], data["sort"], data["cost_usd"]),
                         ('"is there a free" lang:en', 10, "recency", 0.015))
        post = data["posts"][0]
        self.assertEqual((post["id"], post["author"], post["verified"]), ("2102736605039776235", "asker", True))
        self.assertEqual(post["metrics"], {"impressions": 1200, "likes": 30, "replies": 4, "reposts": 2,
                                           "quotes": 1, "bookmarks": 7})
        self.assertNotIn("dropped", data)
        self.assertEqual(len(opener.requests), 1)
        self.assertRegex(log, r"x_read search ok api_items=2 cost_usd=0\.015\n$")

    def test_values_x_did_not_return_are_null(self) -> None:
        body = {"data": [{"id": "1", "author_id": "77", "text": "hi"}],
                "includes": {"users": [{"id": "77", "username": "a"}]}}
        _, out, _, _, _ = self.call(["search", "q"], FakeResponse(body))
        post = json.loads(out)["posts"][0]
        self.assertIsNone(post["created_at"])
        self.assertEqual(set(post["metrics"].values()), {None})

    def test_options_reach_the_request(self) -> None:
        before = datetime.now(timezone.utc)
        code, out, _, _, opener = self.call(
            ["search", "q", "--hours", "6", "--sort", "relevancy"], FakeResponse({}))
        after = datetime.now(timezone.utc)
        data = json.loads(out)
        self.assertEqual((code, data["hours"], data["sort"]), (0, 6, "relevancy"))
        query = parse_qs(urlsplit(opener.requests[0].full_url).query)
        self.assertEqual(query["sort_order"], ["relevancy"])
        start = x_api.parse_time(query["start_time"][0])
        end = x_api.parse_time(query["end_time"][0])
        self.assertEqual(end - start, timedelta(hours=6))
        self.assertGreaterEqual(end, before - timedelta(seconds=31))
        self.assertLessEqual(end, after - timedelta(seconds=29))

    def test_website_syntax_is_refused_without_a_call_or_a_log_line(self) -> None:
        code, out, err, log, opener = self.call(["search", "free editor -filter:replies"])
        self.assertEqual((code, out, log, opener.requests), (1, "", "", []))
        self.assertIn("website syntax", err)

    def test_x_failure_is_reported_not_raised(self) -> None:
        code, out, err, log, _ = self.call(["search", "q"], 401, 401)
        self.assertEqual((code, out, log), (1, "", ""))
        self.assertIn("HTTP 401", err)

    def test_a_saved_result_is_resumed_without_another_call(self) -> None:
        opener = FakeOpener(FakeResponse(BODY))
        client = x_api.Client(keys=KEYS, opener=opener, sleep=lambda _s: None)
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "runs.log"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(x_read.main(["search", "q"], client=client, log_path=log), 0)
            cache = next((Path(tmp) / "x-read-cache").glob("*.json"))
            pending = cache.with_suffix(".pending")
            pending.write_text("999999\n", encoding="utf-8")
            log.write_text("", encoding="utf-8")
            again = x_api.Client(keys=KEYS, opener=FakeOpener(), sleep=lambda _s: None)
            out = io.StringIO()
            with redirect_stdout(out):
                code = x_read.main(["search", "q"], client=again, log_path=log)
            self.assertEqual(code, 0)
            self.assertEqual(again.opener.requests, [])
            self.assertEqual(json.loads(out.getvalue())["posts"][0]["id"], "2102736605039776235")
            self.assertIn("x_read search ok", log.read_text(encoding="utf-8"))
            self.assertFalse(pending.exists())

    def test_thread_command_is_gone(self) -> None:
        with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()):
            x_read.main(["thread", "2102194978269389269"])


if __name__ == "__main__":
    unittest.main()
