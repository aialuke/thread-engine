#!/usr/bin/env python3
"""Checks for scripts/x_api.py with a fake opener. No network, no Keychain."""

from __future__ import annotations

import io
import json
import subprocess
import sys
import unittest
import urllib.error
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import x_api  # noqa: E402

KEYS = {"consumer_key": "CK-SECRET-VALUE", "consumer_secret": "CS-SECRET-VALUE",
        "access_token": "AT-SECRET-VALUE", "access_token_secret": "ATS-SECRET-VALUE"}
NOW = datetime(2026, 9, 24, 12, 0, tzinfo=timezone.utc)


class FakeResponse:
    def __init__(self, body: dict, level: str | None = "read") -> None:
        self.body, self.headers = body, ({"x-access-level": level} if level else {})

    def read(self) -> bytes:
        return json.dumps(self.body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None


class FakeOpener:
    """Replies in order; an int reply raises that HTTP status."""

    def __init__(self, *replies) -> None:
        self.replies, self.requests = list(replies), []

    def __call__(self, req, timeout=30):
        self.requests.append(req)
        reply = self.replies.pop(0)
        if isinstance(reply, int):
            raise urllib.error.HTTPError(req.full_url, reply, "err", {}, io.BytesIO(b'{"title":"nope"}'))
        return reply


def client(*replies) -> tuple[x_api.Client, FakeOpener]:
    opener = FakeOpener(*replies)
    return x_api.Client(keys=KEYS, opener=opener, sleep=lambda s: None), opener


class Signing(unittest.TestCase):
    def test_matches_published_oauth1_example(self) -> None:
        # X's "Creating a signature" worked example.
        keys = {"consumer_key": "xvz1evFS4wEEPTGEFPHBog",
                "consumer_secret": "kAcSOqF21Fu85e7zjz7ZN2U4ZRhfV3WpwPAoE3Z7kBw",
                "access_token": "370773112-GmHxMAgYyLbNEtIKZeRNFsMKPR9EyMZeS9weJAEb",
                "access_token_secret": "LswwdoUaIvS8ltyTt5jkRh4J50vUPVVHtR2YPi5kE"}
        header = x_api.oauth_header(
            "POST", "https://api.twitter.com/1.1/statuses/update.json",
            {"include_entities": "true", "status": "Hello Ladies + Gentlemen, a signed OAuth request!"},
            keys, "kYjzVBB8Y0ZFabxSWbWovY3uYSQ2pTgmZeNu2VS4cg", 1318622958)
        signature = unquote(header.split('oauth_signature="')[1].split('"')[0])
        self.assertEqual(signature, "hCtSmYh+iHYCEqBWrE7C7hYmtUk=")


class ReadOnly(unittest.TestCase):
    def test_refuses_anything_but_get_before_sending(self) -> None:
        c, opener = client()
        for method in ("POST", "PUT", "DELETE"):
            with self.assertRaises(x_api.XApiError):
                c.request(method, "/2/tweets", {}, x_api.POST)
        self.assertEqual(opener.requests, [])

    def test_stops_when_x_reports_write_access(self) -> None:
        c, _ = client(FakeResponse({"data": {"id": "1"}}, level="read-write"))
        with self.assertRaisesRegex(x_api.XApiError, "read-only"):
            x_api.me(c)

    def test_missing_access_header_is_logged_not_fatal(self) -> None:
        c, _ = client(FakeResponse({"data": {"id": "1"}}, level=None))
        x_api.me(c)
        self.assertEqual(c.usage()["missing_access_header"], ["/2/users/me"])

    def test_every_request_is_get_and_signed(self) -> None:
        c, opener = client(FakeResponse({"data": [{"id": "1"}]}))
        x_api.followers(c)
        req = opener.requests[0]
        self.assertEqual(req.get_method(), "GET")
        self.assertTrue(req.get_header("Authorization").startswith("OAuth "))


class Reads(unittest.TestCase):
    def test_timeline_pages_and_counts_owned_cost(self) -> None:
        c, opener = client(FakeResponse({"data": [{"id": "1"}, {"id": "2"}], "meta": {"next_token": "t2"}}),
                           FakeResponse({"data": [{"id": "3"}], "meta": {}}))
        items = x_api.timeline(c, "2026-09-20T00:00:00Z", now=NOW)
        self.assertEqual([i["id"] for i in items], ["1", "2", "3"])
        self.assertEqual((c.calls, c.items, round(c.cost, 4)), (2, 3, 0.003))
        query = parse_qs(urlsplit(opener.requests[1].full_url).query)
        self.assertEqual(query["pagination_token"], ["t2"])
        self.assertIn("organic_metrics", query["tweet.fields"][0])
        self.assertEqual(query["start_time"], ["2026-09-20T00:00:00Z"])

    def test_timeline_refuses_windows_past_organic_limit(self) -> None:
        c, opener = client()
        with self.assertRaisesRegex(x_api.XApiError, "29 days"):
            x_api.timeline(c, x_api.iso(NOW - timedelta(days=30)), now=NOW)
        self.assertEqual(opener.requests, [])

    def test_retries_once_on_server_error_not_on_auth_error(self) -> None:
        c, _ = client(503, FakeResponse({"data": {"id": "1"}}))
        self.assertEqual(x_api.me(c)["id"], "1")
        c, opener = client(401)
        with self.assertRaisesRegex(x_api.XApiError, "HTTP 401"):
            x_api.me(c)
        self.assertEqual(len(opener.requests), 1)

    def test_thread_reads_root_and_cards_from_the_timeline(self) -> None:
        root_id = "2102737637346095128"
        self.assertEqual(x_api.iso(x_api.posted_at(root_id)), "2026-09-23T12:31:34Z")
        card = {"id": "2102737637346095999", "conversation_id": root_id, "in_reply_to_user_id": x_api.USER_ID,
                "referenced_tweets": [{"type": "replied_to", "id": root_id}]}
        other = {"id": "2102737637346095555", "conversation_id": "1", "in_reply_to_user_id": "9",
                 "referenced_tweets": [{"type": "replied_to", "id": "1"}]}
        c, opener = client(FakeResponse({"data": [{"id": root_id, "conversation_id": root_id}, card, other]}))
        found = x_api.thread(c, root_id, now=NOW)
        self.assertEqual((found["root"]["id"], [x["id"] for x in found["cards"]]), (root_id, [card["id"]]))
        query = parse_qs(urlsplit(opener.requests[0].full_url).query)
        self.assertEqual(query["start_time"], ["2026-09-23T12:30:34Z"])
        c, _ = client(FakeResponse({"data": [other]}))
        with self.assertRaisesRegex(x_api.XApiError, "not one of"):
            x_api.thread(c, root_id, now=NOW)

    def test_kind_and_nonorganic_share(self) -> None:
        uid = x_api.USER_ID
        self.assertEqual(x_api.kind({}), "original")
        self.assertEqual(x_api.kind({"referenced_tweets": [{"type": "quoted"}]}), "quote")
        self.assertEqual(x_api.kind({"referenced_tweets": [{"type": "replied_to"}], "in_reply_to_user_id": "9"}),
                         "reply")
        self.assertEqual(x_api.kind({"referenced_tweets": [{"type": "replied_to"}], "in_reply_to_user_id": uid}),
                         "thread_card")
        boosted = {"public_metrics": {"impression_count": 2082}, "organic_metrics": {"impression_count": 98}}
        self.assertAlmostEqual(x_api.nonorganic_share(boosted), 0.953, places=3)
        self.assertIsNone(x_api.nonorganic_share({"public_metrics": {"impression_count": 0}}))


class NoSecretsInOutput(unittest.TestCase):
    def run_main(self, argv, c) -> str:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            x_api.main(argv, client=c)
        return out.getvalue() + err.getvalue()

    def test_success_and_failure_never_print_keys(self) -> None:
        ok, _ = client(FakeResponse({"data": {"id": "1", "username": "exitzerocode"}}))
        bad, _ = client(401)
        for text in (self.run_main(["me"], ok), self.run_main(["me"], bad)):
            for value in KEYS.values():
                self.assertNotIn(value, text)

    def test_missing_key_message_names_key_not_value(self) -> None:
        runner = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 44, "", "not found")
        with self.assertRaisesRegex(x_api.XApiError, "consumer_key"):
            x_api.keychain("consumer_key", runner=runner)

    def test_keys_check_never_asks_for_values(self) -> None:
        seen = []
        runner = lambda cmd, **kw: (seen.append(cmd), subprocess.CompletedProcess(cmd, 0, "", ""))[1]
        self.assertEqual(x_api.keys_present(runner)["missing"], [])
        self.assertTrue(all("-w" not in cmd for cmd in seen))


if __name__ == "__main__":
    unittest.main()
