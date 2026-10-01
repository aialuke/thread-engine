#!/usr/bin/env python3
"""Read-only X API client for @exitzerocode's own data. GET requests only.

    python3 scripts/x_api.py keys
    python3 scripts/x_api.py me
    python3 scripts/x_api.py timeline --start <ISO> [--end <ISO>]
    python3 scripts/x_api.py followers
    python3 scripts/x_api.py mentions [--since-id <post id>]
    python3 scripts/x_api.py thread <root post id>
    python3 scripts/x_api.py user <handle>
    python3 scripts/x_api.py backfill --since <ISO>

Keys come from the macOS Keychain (service thread-engine-x) and are never printed.
The real no-writes guarantee is the app's Read permission, which X enforces; this
client also sends nothing but GET and stops if X reports an access level other
than read. Prints JSON with the items, calls made, items read and an estimated
cost. backfill saves the raw responses under ledger/raw/api/ (gitignored, other
people's data) and prints only counts.

Other people's posts and research go through x_read.py, which calls search() here.
Facts behind the numbers below: reference/x-api.md.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import re
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path

import durable
from loop_core.errors import LoopError
from loop_core.reads import FINAL_MAX_DAYS as ORGANIC_DAYS
from loop_core.times import iso, parse_time as _parse_time

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.x.com"
SERVICE = "thread-engine-x"
KEY_NAMES = ("consumer_key", "consumer_secret", "access_token", "access_token_secret")
HANDLE = "exitzerocode"
USER_ID = "1994313953191833600"
MAX_PAGES = 50
RETRY_SECONDS = 20
# Estimated USD per item returned (reference/x-api.md, pricing read 2026-09-24).
OWNED, POST, USER = 0.001, 0.005, 0.010
# note_tweet carries the whole text of a post over 280 characters; `text` alone is cut (reference/x-api.md P16).
TWEET_FIELDS = ",".join(("created_at", "text", "note_tweet", "conversation_id", "in_reply_to_user_id",
                         "referenced_tweets", "public_metrics", "organic_metrics", "non_public_metrics",
                         "context_annotations"))
MENTION_FIELDS = "created_at,author_id,conversation_id,in_reply_to_user_id,referenced_tweets"
NONORGANIC_SHARE = 0.10
HANDLE_RE = re.compile(r"[A-Za-z0-9_]{1,15}")
# Recent search (reference/x-api.md): 512-character queries, 7 days back, end_time at least 10 s before now.
SEARCH_QUERY_LIMIT = 512
SEARCH_MAX_HOURS = 167
SEARCH_END_LAG_SECONDS = 30
# Operators that exist on x.com's search box but not in the API: the API rejects or ignores them.
WEBSITE_OPERATOR_RE = re.compile(r"(?:^|[\s(\-])((?:min_faves|min_retweets|within_time|since|until|filter)):",
                                 re.IGNORECASE)


class XApiError(Exception):
    pass


def parse_time(value: str) -> datetime:
    """The loop's timestamp parse. A bad value is an XApiError so callers of this client see one exception."""
    try:
        return _parse_time(value)
    except LoopError as exc:
        raise XApiError(str(exc)) from exc


# X's metric names, and the plain names the ledger stores. One map for every reader of a post.
_PUBLIC_FIELDS = (("impression_count", "impressions"), ("like_count", "likes"), ("reply_count", "replies"),
                  ("retweet_count", "reposts"), ("quote_count", "quotes"), ("bookmark_count", "bookmarks"))
_ORGANIC_FIELDS = (("impression_count", "impressions"), ("like_count", "likes"), ("reply_count", "replies"),
                   ("retweet_count", "reposts"), ("user_profile_clicks", "profile_visits"))


def public_counts(metrics: dict | None) -> dict:
    """X public_metrics under the ledger's names. A missing metric is null, not zero."""
    metrics = metrics or {}
    return {name: metrics.get(field) for field, name in _PUBLIC_FIELDS}


def organic_counts(metrics: dict | None) -> dict:
    """X organic_metrics under the ledger's names. No organic block at all leaves every value null."""
    if not metrics:
        return {name: None for _, name in _ORGANIC_FIELDS} | {"url_clicks": None}
    counts = {name: metrics.get(field) for field, name in _ORGANIC_FIELDS}
    counts["url_clicks"] = metrics.get("url_link_clicks", 0)
    return counts


# ---------- keys and signing ----------


def keychain(name: str, runner: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> str:
    result = runner(["security", "find-generic-password", "-s", SERVICE, "-a", name, "-w"],
                    capture_output=True, text=True, check=False)
    if result.returncode != 0 or not result.stdout.strip():
        raise XApiError(f"Keychain has no {name} under {SERVICE}, or the Keychain is locked")
    return result.stdout.strip()


def keys_present(runner: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> dict:
    """Which keys exist, without reading any value (no -w)."""
    present, missing = [], []
    for name in KEY_NAMES:
        result = runner(["security", "find-generic-password", "-s", SERVICE, "-a", name],
                        capture_output=True, text=True, check=False)
        (present if result.returncode == 0 else missing).append(name)
    return {"present": present, "missing": missing}


def pct(value) -> str:
    return urllib.parse.quote(str(value), safe="~")


def oauth_header(method: str, url: str, params: dict, keys: dict, nonce: str, timestamp: int) -> str:
    """OAuth 1.0a HMAC-SHA1 user-context header."""
    oauth = {"oauth_consumer_key": keys["consumer_key"], "oauth_nonce": nonce,
             "oauth_signature_method": "HMAC-SHA1", "oauth_timestamp": str(timestamp),
             "oauth_token": keys["access_token"], "oauth_version": "1.0"}
    pairs = sorted((pct(k), pct(v)) for k, v in {**params, **oauth}.items())
    base = "&".join((method.upper(), pct(url), pct("&".join(f"{k}={v}" for k, v in pairs))))
    key = f"{pct(keys['consumer_secret'])}&{pct(keys['access_token_secret'])}"
    oauth["oauth_signature"] = base64.b64encode(hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()).decode()
    return "OAuth " + ", ".join(f'{pct(k)}="{pct(v)}"' for k, v in sorted(oauth.items()))


# ---------- client ----------


class Client:
    def __init__(self, keys: dict | None = None, opener: Callable = urllib.request.urlopen,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self._keys = keys
        self.opener, self.sleep = opener, sleep
        self.calls, self.items, self.cost = 0, 0, 0.0
        self.no_access_header: list[str] = []

    def keys(self) -> dict:
        if self._keys is None:
            self._keys = {name: keychain(name) for name in KEY_NAMES}
        return self._keys

    def _fetch(self, url: str, params: dict) -> tuple[str | None, dict]:
        query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote, safe=",")
        header = oauth_header("GET", url, params, self.keys(), secrets.token_hex(16), int(time.time()))
        req = urllib.request.Request(f"{url}?{query}" if query else url,
                                     headers={"Authorization": header}, method="GET")
        with self.opener(req, timeout=30) as resp:
            return resp.headers.get("x-access-level"), json.loads(resp.read() or b"{}")

    @staticmethod
    def _retryable(exc: Exception) -> bool:
        if isinstance(exc, urllib.error.HTTPError):
            return exc.code in (429, 500, 502, 503, 504)
        return True

    @staticmethod
    def _error(path: str, exc: Exception) -> XApiError:
        if isinstance(exc, urllib.error.HTTPError):
            detail = exc.read()[:400].decode("utf-8", errors="replace")
            return XApiError(f"GET {path} failed: HTTP {exc.code} {detail}")
        return XApiError(f"GET {path} failed: {getattr(exc, 'reason', exc)}")

    def request(self, method: str, path: str, params: dict, rate: float, partial_ok: bool = False) -> dict:
        if method != "GET":
            raise XApiError(f"{method} refused: this client only reads")
        url = API + path
        failures = (urllib.error.URLError, TimeoutError)
        try:
            level, body = self._fetch(url, params)
        except failures as exc:
            if not self._retryable(exc):
                raise self._error(path, exc) from None
            self.sleep(RETRY_SECONDS)
            try:
                level, body = self._fetch(url, params)
            except failures as again:
                raise self._error(path, again) from None
        self.calls += 1
        if level is None:
            if path not in self.no_access_header:
                self.no_access_header.append(path)
        elif level != "read":
            raise XApiError(f"X reports access level {level!r} for these keys; the app must be read-only. Stopping.")
        if "data" not in body and body.get("errors") and not partial_ok:
            raise XApiError(f"GET {path} returned errors: {json.dumps(body['errors'])[:400]}")
        data = body.get("data")
        count = len(data) if isinstance(data, list) else (1 if data else 0)
        self.items += count
        self.cost += count * rate
        return body

    def pages(self, path: str, params: dict, rate: float) -> list[dict]:
        found, token = [], None
        for _ in range(MAX_PAGES):
            page = dict(params)
            if token:
                page["pagination_token"] = token
            body = self.request("GET", path, page, rate)
            found.extend(body.get("data") or [])
            token = (body.get("meta") or {}).get("next_token")
            if not token:
                return found
        raise XApiError(f"GET {path}: more than {MAX_PAGES} pages; narrow the window")

    def usage(self) -> dict:
        return {"calls": self.calls, "items_read": self.items, "cost_usd": round(self.cost, 4),
                "missing_access_header": self.no_access_header}


# ---------- reads ----------


def me(client: Client) -> dict:
    fields = "created_at,description,pinned_tweet_id,public_metrics"
    return client.request("GET", "/2/users/me", {"user.fields": fields}, USER)["data"]


def timeline(client: Client, start: str, end: str | None = None, now: datetime | None = None) -> list[dict]:
    """Every post, reply and quote in [start, end), with organic metrics. Owned read."""
    now = now or datetime.now(timezone.utc)
    begin = parse_time(start)
    if begin < now - timedelta(days=ORGANIC_DAYS):
        raise XApiError(f"start {iso(begin)} is more than {ORGANIC_DAYS} days ago; "
                        "X no longer returns organic metrics for those posts")
    params = {"max_results": "100", "tweet.fields": TWEET_FIELDS, "start_time": iso(begin)}
    if end:
        params["end_time"] = iso(parse_time(end))
    return [with_full_text(item) for item in client.pages(f"/2/users/{USER_ID}/tweets", params, OWNED)]


def followers(client: Client) -> list[dict]:
    """Follower ids, handles and whether each is verified. Owned read. Callers store ids only."""
    found = client.pages(f"/2/users/{USER_ID}/followers",
                         {"max_results": "1000", "user.fields": "verified,verified_type"}, OWNED)
    return [{"id": u["id"], "username": u.get("username"), "verified": bool(u.get("verified"))} for u in found]


def mentions(client: Client, since_id: str | None = None) -> list[dict]:
    params = {"max_results": "100", "tweet.fields": MENTION_FIELDS}
    if since_id:
        params["since_id"] = since_id
    return client.pages(f"/2/users/{USER_ID}/mentions", params, OWNED)


def posted_at(post_id: str) -> datetime:
    """X post ids carry their creation time (snowflake: milliseconds since X's epoch, shifted 22 bits)."""
    return datetime.fromtimestamp(((int(post_id) >> 22) + 1288834974657) / 1000, tz=timezone.utc)


def thread(client: Client, root_id: str, now: datetime | None = None) -> dict:
    """The account's own root post and its thread cards, read from the timeline around the post's time."""
    if not root_id.isdigit():
        raise XApiError(f"bad post id {root_id!r}")
    start = posted_at(root_id) - timedelta(minutes=1)
    items = timeline(client, iso(start), iso(start + timedelta(hours=6)), now=now)
    root = next((i for i in items if i["id"] == root_id), None)
    if root is None:
        raise XApiError(f"{root_id} is not one of @{HANDLE}'s posts in the 6 hours after it was made")
    cards = sorted((i for i in items if i["id"] != root_id and i.get("conversation_id") == root_id
                    and kind(i) == "thread_card"), key=lambda i: int(i["id"]))
    return {"root": root, "cards": cards}


def lookup(client: Client, ids: list[str]) -> list[dict]:
    """Anyone's posts by id, with the author's handle. Not an owned read: about $0.005 a post and
    $0.010 an author. Ids X doesn't know are simply absent from the result."""
    ids = [i for i in dict.fromkeys(ids) if i.isdigit()][:100]
    if not ids:
        return []
    params = {"ids": ",".join(ids), "tweet.fields": "created_at,author_id,public_metrics,text,note_tweet",
              "expansions": "author_id", "user.fields": "username"}
    body = client.request("GET", "/2/tweets", params, POST, partial_ok=True)
    return _posts_with_authors(client, body)


def search(client: Client, query: str, hours: float = 24, sort_order: str = "recency",
           now: datetime | None = None) -> list[dict]:
    """Up to 10 of anyone's recent posts matching an X API v2 query, with the author's handle.
    Not an owned read: about $0.005 a post and $0.010 an author. The window is the last `hours`
    hours, ending SEARCH_END_LAG_SECONDS before now (X refuses an end_time too close to now)."""
    query = query.strip()
    if not query:
        raise XApiError("empty search query")
    if len(query) > SEARCH_QUERY_LIMIT:
        raise XApiError(f"query is {len(query)} characters; X allows {SEARCH_QUERY_LIMIT}")
    website = WEBSITE_OPERATOR_RE.search(query)
    if website:
        raise XApiError(f"{website.group(1)}: is website syntax and X's API refuses it; "
                        "use API operators (min_replies:, -is:reply, lang:)")
    if sort_order not in ("recency", "relevancy"):
        raise XApiError(f"sort must be recency or relevancy, not {sort_order!r}")
    if not 0 < hours <= SEARCH_MAX_HOURS:
        raise XApiError(f"hours must be between 0 and {SEARCH_MAX_HOURS}: X search reaches back 7 days")
    end = (now or datetime.now(timezone.utc)) - timedelta(seconds=SEARCH_END_LAG_SECONDS)
    params = {"query": query, "max_results": "10", "sort_order": sort_order,
              "start_time": iso(end - timedelta(hours=hours)), "end_time": iso(end),
              "tweet.fields": "created_at,author_id,public_metrics,text,note_tweet,referenced_tweets",
              "expansions": "author_id", "user.fields": "username"}
    body = client.request("GET", "/2/tweets/search/recent", params, POST, partial_ok=True)
    return _posts_with_authors(client, body)


def user(client: Client, handle: str) -> dict:
    """One account by handle: who it is and when it last posted, to check a handle before tagging it.
    Not an owned read: about $0.010."""
    handle = handle.removeprefix("@")
    if not HANDLE_RE.fullmatch(handle):
        raise XApiError(f"bad handle {handle!r}")
    fields = "created_at,verified,verified_type,public_metrics,most_recent_tweet_id"
    body = client.request("GET", f"/2/users/by/username/{handle}", {"user.fields": fields}, USER, partial_ok=True)
    data = body.get("data")
    if not data:
        detail = "; ".join(e.get("detail") or e.get("title", "") for e in body.get("errors") or [])
        raise XApiError(f"@{handle} not found on X{': ' + detail if detail else ''}")
    latest = data.get("most_recent_tweet_id")
    return {"handle": data.get("username"), "name": data.get("name"), "id": data.get("id"),
            "verified": bool(data.get("verified")), "verified_type": data.get("verified_type"),
            "created_at": data.get("created_at"),
            "followers": (data.get("public_metrics") or {}).get("followers_count"),
            "latest_post_at": iso(posted_at(latest)) if latest and latest.isdigit() else None}


# ---------- item helpers ----------


def full_text(item: dict) -> str:
    """The whole post: X cuts `text` at about 280 characters and puts the rest in note_tweet."""
    return (item.get("note_tweet") or {}).get("text") or item.get("text", "")


def with_full_text(item: dict) -> dict:
    if item.get("note_tweet"):
        item = {**item, "text": full_text(item)}
    return item


def _posts_with_authors(client: Client, body: dict) -> list[dict]:
    """Posts from a response that expanded author_id. Each included author is billed."""
    users = {u["id"]: u.get("username") for u in (body.get("includes") or {}).get("users", [])}
    client.items += len(users)
    client.cost += len(users) * USER
    return [{**with_full_text(post), "author": users.get(post.get("author_id"))} for post in body.get("data") or []]


def kind(item: dict) -> str:
    refs = item.get("referenced_tweets") or []
    types = {r.get("type") for r in refs}
    if "replied_to" in types:
        return "thread_card" if item.get("in_reply_to_user_id") == USER_ID else "reply"
    if "quoted" in types:
        return "quote"
    if "retweeted" in types:
        return "repost"
    return "original"


def nonorganic_share(item: dict) -> float | None:
    public = public_counts(item.get("public_metrics")).get("impressions")
    organic = organic_counts(item.get("organic_metrics")).get("impressions")
    if not public or organic is None:
        return None
    return max(0.0, (public - organic) / public)


def backfill(client: Client, since: str, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    items = timeline(client, since, now=now)
    data = {"fetched_at": iso(now), "since": since, "user_id": USER_ID,
            "me": me(client), "timeline": items, "followers": followers(client), "mentions": mentions(client)}
    raw = durable.write_new_text(
        ROOT / "ledger" / "raw" / "api", f"backfill-{now.strftime('%Y%m%dT%H%M%S')}", ".json",
        json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    kinds: dict[str, int] = {}
    for item in items:
        kinds[kind(item)] = kinds.get(kind(item), 0) + 1
    flagged = []
    for item in items:
        share = nonorganic_share(item)
        if kind(item) in {"original", "quote"} and share is not None and share > NONORGANIC_SHARE:
            flagged.append({"id": item["id"],
                            "public": public_counts(item.get("public_metrics"))["impressions"],
                            "organic": organic_counts(item.get("organic_metrics"))["impressions"],
                            "share": round(share, 3)})
    return {"raw_file": str(raw.relative_to(ROOT)), "items": len(items), "kinds": kinds,
            "followers": len(data["followers"]), "mentions": len(data["mentions"]),
            "nonorganic": flagged}


# ---------- cli ----------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only X API client for the account's own data.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("keys")
    sub.add_parser("me")
    sp = sub.add_parser("timeline")
    sp.add_argument("--start", required=True)
    sp.add_argument("--end")
    sub.add_parser("followers")
    sp = sub.add_parser("mentions")
    sp.add_argument("--since-id")
    sp = sub.add_parser("thread")
    sp.add_argument("root_id")
    sp = sub.add_parser("user")
    sp.add_argument("handle")
    sp = sub.add_parser("backfill")
    sp.add_argument("--since", required=True)
    return parser


def main(argv: list[str] | None = None, client: Client | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = client or Client()
    try:
        if args.command == "keys":
            print(json.dumps(keys_present(), indent=2))
            return 0
        if args.command == "me":
            result = {"data": me(client)}
        elif args.command == "timeline":
            result = {"items": timeline(client, args.start, args.end)}
        elif args.command == "followers":
            result = {"items": followers(client)}
        elif args.command == "mentions":
            result = {"items": mentions(client, args.since_id)}
        elif args.command == "thread":
            result = thread(client, args.root_id)
        elif args.command == "user":
            result = {"data": user(client, args.handle)}
        else:
            result = backfill(client, args.since)
            durable.append_line(ROOT / "ledger" / "runs.log",
                                f"{iso(datetime.now(timezone.utc))} x_api backfill ok api_items={client.items} "
                                f"cost_usd={round(client.cost, 4)}")
    except XApiError as exc:
        print(json.dumps({"error": str(exc), **client.usage()}), file=sys.stderr)
        return 1
    print(json.dumps({**result, **client.usage()}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
