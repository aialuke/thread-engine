#!/usr/bin/env python3
"""Discovery test harness (research code; nothing in scripts/ imports it).

    python3 research/discovery-test/harness.py status
    python3 research/discovery-test/harness.py pilot --dry-run
    python3 research/discovery-test/harness.py pilot next | all | <step> [--redo]
    python3 research/discovery-test/harness.py config --model <id> | --authors on|off | --best-arm <arm> | --pin-block <B|none>
    python3 research/discovery-test/harness.py console --before|--after <USD>
    python3 research/discovery-test/harness.py stage1|stage2|stage3 --idea <key> [--source K|G|T|C]
    python3 research/discovery-test/harness.py reread [--block B]
    python3 research/discovery-test/harness.py corpus --stage N [--block B [--batch 50]]
    python3 research/discovery-test/harness.py ingest-scores --stage N [--block B] [--second all] <file> [<file>…]
    python3 research/discovery-test/harness.py second-scores|finalise-scores --stage N [--block B] …
    python3 research/discovery-test/harness.py manifest --block B

The plan is plan.md in this folder. X API calls go through scripts/x_api.py's Client
(Keychain signing, GET only, read-only access check); this file only wraps it with
logging and a budget gate. Grok runs through the Grok Build CLI from an empty folder
outside the repo, with memory off, and its whole output stream is kept.

Everything written lands in private/ (gitignored, other people's posts; delete by
26 Mar 2027). A run can stop at any step (budget, Grok's weekly limit, an error) and
resume later: progress.json records each step, and the logs are append-only.
"""

from __future__ import annotations

import argparse
import csv
import email.utils
import hashlib
import io
import json
import os
import random
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
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import x_api  # noqa: E402
from grok_read import last_json_object  # noqa: E402
from x_read import same_text  # noqa: E402

PRIVATE = HERE / "private"
GROK = Path.home() / ".grok" / "bin" / "grok"
# Grok must start outside the repo, or it walks up and loads AGENTS.md and .claude/skills (seen on 26 Sep, g0001)
GROK_CWD_ROOT = Path.home() / "Library" / "Caches" / "thread-engine-discovery" / "grok-cwd"
PROJECT_SKILLS = {"approve", "draft-thread", "format-tool-swap", "next", "snapshot", "verify-settings"}
BRISBANE = ZoneInfo("Australia/Brisbane")
POST, USER = x_api.POST, x_api.USER

PILOT_CEILING = 2.50        # X API, pilot only (HANDOFF decision 3)
X_CHECKPOINT = 7.00         # X API, whole test: stop and report (operator, 27 Sep: was 6.00)
GROK_CHECKPOINT = 3.00      # Grok, whole test
GROK_RESERVE = 0.30         # worst case one Grok run, reserved before it starts
ARM_VERIFY_CAP = 30         # claimed ids checked per pilot arm (the prompt allows 3 searches × 10)
PROBE_VERIFY_CAP = 10
STAGE_VERIFY_CAP = 30
BLOCK_HOURS = 2             # steps more than this apart run in a new time block
GROK_TOKEN_USD = {"input": 2.00e-6, "cached": 0.50e-6, "output": 6.00e-6}   # grok-4.7 short context
# 26 Sep: the subscription pool ran out as "402 Payment Required: Grok Build usage balance exhausted"
LIMIT_RE = re.compile(r"limit|quota|429|402|exceed|exhausted|payment required|balance|too many|usage cap", re.I)

TWEET_FIELDS = ",".join((
    "attachments", "author_id", "context_annotations", "conversation_id", "created_at",
    "edit_history_tweet_ids", "entities", "geo", "id", "in_reply_to_user_id", "lang", "note_tweet",
    "possibly_sensitive", "public_metrics", "referenced_tweets", "reply_settings", "source", "text",
    "withheld"))
USER_FIELDS = "created_at,description,location,name,protected,public_metrics,url,username,verified,verified_type"
WINDOW_HOURS = {"worth-joining": 6, "demand": 24, "tool-research": 7 * 24}


class Stop(Exception):
    """A deliberate stop: budget, quiet hour, missing setting. Never retried automatically."""


# ---------- time ----------


def iso(stamp: datetime) -> str:
    return x_api.iso(stamp)


def guard_clock(now: datetime) -> None:
    local = now.astimezone(BRISBANE)
    minutes = local.hour * 60 + local.minute
    if 19 * 60 + 30 <= minutes < 20 * 60 + 30:
        raise Stop(f"{local:%H:%M} Brisbane is inside 19:30–20:30, the daily snapshot's hour; try after 20:30")


def parse_stamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return x_api.parse_time(value)
    except x_api.XApiError:
        pass
    try:
        return email.utils.parsedate_to_datetime(value).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def windows_at(now: datetime) -> dict:
    end = now.replace(microsecond=0) - timedelta(seconds=30)   # X wants end_time at least 10 s before the request
    return {job: {"start": iso(end - timedelta(hours=h)), "end": iso(end)} for job, h in WINDOW_HOURS.items()}


def in_window(created_at: str | None, window: dict) -> bool | None:
    stamp = parse_stamp(created_at)
    if stamp is None:
        return None
    return parse_stamp(window["start"]) <= stamp < parse_stamp(window["end"])


def eligible(post: dict | None, window: dict) -> tuple[bool | None, str]:
    """One rule for every source before scoring: X says English, not a retweet, inside the exact window."""
    if not post:
        return None, "not on X"
    if post.get("lang") and post["lang"] != "en":
        return False, f"lang {post['lang']}"
    if any(r.get("type") == "retweeted" for r in post.get("referenced_tweets") or []) or x_api.full_text(post).startswith("RT @"):
        return False, "retweet"
    inside = in_window(post.get("created_at"), window)
    if inside is None:
        return None, "no timestamp"
    return (True, "ok") if inside else (False, "outside window")


# ---------- storage ----------


class Store:
    """private/: append-only logs, the post table, progress. Totals are rebuilt from the logs."""

    def __init__(self, root: Path = PRIVATE) -> None:
        self.root = root
        for sub in ("raw", "grok", "grok-cwd"):
            (root / sub).mkdir(parents=True, exist_ok=True)
        self.requests, self.grok_log = root / "requests.jsonl", root / "grok.jsonl"
        self.budget, self.posts, self.progress_path = root / "budget.log", root / "posts.csv", root / "progress.json"
        self._seed_files()

    def _seed_files(self) -> None:
        readme = self.root / "README.md"
        if not readme.exists():
            readme.write_text(PRIVATE_README, encoding="utf-8")
        facts = self.root / "facts.md"
        if not facts.exists():
            facts.write_text(FACTS_SEED, encoding="utf-8")

    @staticmethod
    def append(path: Path, row: dict) -> None:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    @staticmethod
    def rows(path: Path) -> list[dict]:
        if not path.exists():
            return []
        # split on \n only: str.splitlines() also breaks on U+2028/U+0085 inside post text (26 Sep, Stage 2)
        return [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line.strip()]

    def write_atomic(self, path: Path, text: str) -> None:
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)

    # spend
    def x_spent(self, stage: str | None = None) -> float:
        return round(sum(r.get("estimated_cost") or 0 for r in self.rows(self.requests)
                         if stage is None or r.get("stage") == stage), 4)

    def grok_spent(self) -> float:
        return round(sum(r.get("cost_usd") or 0 for r in self.rows(self.grok_log)), 4)

    def log_budget(self, now: datetime, event: str, **detail) -> None:
        extra = " ".join(f"{k}={v}" for k, v in detail.items())
        with self.budget.open("a", encoding="utf-8") as fh:
            fh.write(f"{iso(now)} x_spent={self.x_spent():.4f} pilot={self.x_spent('pilot'):.4f} "
                     f"grok_spent={self.grok_spent():.4f} {event} {extra}".rstrip() + "\n")

    def check_x_budget(self, now: datetime, stage: str, reserve: float, what: str) -> None:
        spent, pilot = self.x_spent(), self.x_spent("pilot")
        if spent + reserve > X_CHECKPOINT + 1e-9:
            self.log_budget(now, "REFUSED", what=what, reserve=f"{reserve:.4f}", ceiling=X_CHECKPOINT)
            raise Stop(f"X API checkpoint: ${spent:.2f} spent + ${reserve:.2f} reserve passes ${X_CHECKPOINT:.2f}. "
                       "Report what's learned and ask the operator before going on.")
        if stage == "pilot" and pilot + reserve > PILOT_CEILING + 1e-9:
            self.log_budget(now, "REFUSED", what=what, reserve=f"{reserve:.4f}", ceiling=PILOT_CEILING)
            raise Stop(f"Pilot ceiling: ${pilot:.2f} spent + ${reserve:.2f} reserve passes ${PILOT_CEILING:.2f}.")

    def check_grok_budget(self, now: datetime, what: str) -> None:
        spent = self.grok_spent()
        if spent + GROK_RESERVE > GROK_CHECKPOINT + 1e-9:
            self.log_budget(now, "REFUSED", what=what, reserve=GROK_RESERVE, ceiling=GROK_CHECKPOINT)
            raise Stop(f"Grok checkpoint: ${spent:.2f} spent + ${GROK_RESERVE:.2f} reserve passes ${GROK_CHECKPOINT:.2f}.")

    # progress
    def progress(self) -> dict:
        if self.progress_path.exists():
            return json.loads(self.progress_path.read_text(encoding="utf-8"))
        return {"settings": {"authors_on_checks": False}, "blocks": [], "steps": {}}

    def save_progress(self, data: dict) -> None:
        self.write_atomic(self.progress_path, json.dumps(data, indent=1, ensure_ascii=False) + "\n")

    def block(self, now: datetime, new: bool = False) -> dict:
        """The current time block: shared windows for every step run within BLOCK_HOURS of its start.
        new=True starts a fresh block (a stage must not reuse the pilot's windows).
        A pinned block (config --pin-block) is returned with its original windows, however long ago it was used."""
        data = self.progress()
        pinned = data["settings"].get("pinned_block")
        if pinned:
            if new:
                raise Stop(f"block {pinned} is pinned; `config --pin-block none` before starting a new block")
            block = next((b for b in data["blocks"] if b["id"] == pinned), None)
            if block is None:
                raise Stop(f"pinned block {pinned} is not in progress.json")
            block["last_used"] = iso(now)
            self.save_progress(data)
            return block
        if data["blocks"] and not new:
            last = data["blocks"][-1]
            if now - parse_stamp(last["last_used"]) <= timedelta(hours=BLOCK_HOURS):
                last["last_used"] = iso(now)
                self.save_progress(data)
                return last
        block = {"id": f"B{len(data['blocks']) + 1}", "created": iso(now), "last_used": iso(now),
                 "brisbane": now.astimezone(BRISBANE).strftime("%Y-%m-%d %H:%M"), "windows": windows_at(now)}
        data["blocks"].append(block)
        self.save_progress(data)
        return block

    def pin_block(self, block_id: str) -> str | None:
        """Pin a block by id, or clear the pin with 'none'."""
        data = self.progress()
        if block_id.lower() == "none":
            data["settings"].pop("pinned_block", None)
        elif not any(b["id"] == block_id for b in data["blocks"]):
            raise Stop(f"no block {block_id}; blocks are {', '.join(b['id'] for b in data['blocks']) or 'none yet'}")
        else:
            data["settings"]["pinned_block"] = block_id
        self.save_progress(data)
        return data["settings"].get("pinned_block")

    def call_rows(self) -> dict[str, dict]:
        return {r["call_id"]: r for r in self.rows(self.requests) if r.get("call_id")}

    def next_id(self, path: Path, prefix: str) -> str:
        return f"{prefix}{len(self.rows(path)) + 1:04d}"

    # posts.csv
    POST_COLUMNS = ("post_id", "first_seen", "last_seen", "labels", "sightings", "created_at", "author_id",
                    "author", "lang", "conversation_id", "text", "claimed_text", "metrics", "reread")

    def load_posts(self) -> dict[str, dict]:
        if not self.posts.exists():
            return {}
        with self.posts.open(encoding="utf-8", newline="") as fh:
            return {row["post_id"]: row for row in csv.DictReader(fh)}

    def upsert_posts(self, now: datetime, found: list[dict]) -> None:
        """found: {post_id, sighting, label, x (X's post dict or None), claimed_text}."""
        table = self.load_posts()
        for item in found:
            row = table.get(item["post_id"]) or {c: "" for c in self.POST_COLUMNS} | {
                "post_id": item["post_id"], "first_seen": iso(now), "labels": "[]", "sightings": "[]"}
            row["last_seen"] = iso(now)
            sightings = json.loads(row["sightings"])
            sightings.append(item["sighting"])
            row["sightings"] = json.dumps(sightings, ensure_ascii=False)
            labels = json.loads(row["labels"])
            if item.get("label") and item["label"] not in labels:
                labels.append(item["label"])
            row["labels"] = json.dumps(labels)
            post = item.get("x")
            if post:
                row.update({"created_at": post.get("created_at", ""), "author_id": post.get("author_id", ""),
                            "author": post.get("author") or row["author"], "lang": post.get("lang", ""),
                            "conversation_id": post.get("conversation_id", ""), "text": x_api.full_text(post),
                            "metrics": json.dumps(post.get("public_metrics") or {})})
            if item.get("claimed_text") and not row["claimed_text"]:
                row["claimed_text"] = item["claimed_text"]
            if item.get("reread"):
                row["reread"] = json.dumps(item["reread"])
            table[item["post_id"]] = row
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=self.POST_COLUMNS)
        writer.writeheader()
        writer.writerows(table.values())
        self.write_atomic(self.posts, buf.getvalue())


# ---------- X API ----------


class Replay:
    """A response already read, so the wrapper can log it and the parent Client can still read it."""

    def __init__(self, headers, raw: bytes) -> None:
        self.headers, self._raw = headers, raw

    def read(self) -> bytes:
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None


def header(headers, name: str):
    if headers is None:
        return None
    return headers.get(name) or headers.get(name.lower()) or headers.get(name.title())


class LoggedClient(x_api.Client):
    """x_api.Client with every HTTP call logged. Signing, GET-only and the access check stay the parent's."""

    def __init__(self, store: Store, keys: dict | None = None, opener: Callable = urllib.request.urlopen,
                 sleep: Callable[[float], None] = time.sleep, clock: Callable[[], datetime] | None = None) -> None:
        super().__init__(keys=keys, opener=self._logged_open, sleep=sleep)
        self.store, self.inner = store, opener
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.context: dict = {}
        self.last_row: dict | None = None

    def _logged_open(self, req, timeout=30):
        now = self.clock()
        guard_clock(now)
        started = time.monotonic()
        try:
            with self.inner(req, timeout=timeout) as resp:
                raw, headers = resp.read() or b"{}", resp.headers
                status = getattr(resp, "status", None) or 200
        except urllib.error.HTTPError as exc:
            raw = exc.read() or b""
            self._record(req, now, exc.code, exc.headers, raw, started)
            raise urllib.error.HTTPError(exc.url, exc.code, exc.msg, exc.headers, io.BytesIO(raw)) from None
        except (urllib.error.URLError, TimeoutError) as exc:
            self._record(req, now, None, None, str(getattr(exc, "reason", exc)).encode(), started)
            raise
        self._record(req, now, status, headers, raw, started)
        return Replay(headers, raw)

    def _record(self, req, now: datetime, status, headers, raw: bytes, started: float) -> None:
        ctx = self.context
        call_id = self.store.next_id(self.store.requests, "x")
        (self.store.root / "raw" / f"{call_id}.json").write_bytes(raw)
        try:
            body = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            body = {}
        items = count_items(body)
        cost, note = estimate_cost(ctx.get("kind", "posts"), items) if status and status < 400 else (0.0, "not billed (assumed)")
        url = urllib.parse.urlsplit(req.full_url)
        row = {"call_id": call_id, "time_utc": iso(now), "time_brisbane": now.astimezone(BRISBANE).isoformat(),
               "stage": ctx.get("stage"), "step": ctx.get("step"), "idea": ctx.get("idea"),
               "source": ctx.get("source"), "block": ctx.get("block"), "endpoint": url.path,
               "params": ctx.get("params"), "status": status,
               "latency_ms": round((time.monotonic() - started) * 1000),
               "rate_limit": {k: header(headers, f"x-rate-limit-{k}") for k in ("limit", "remaining", "reset")},
               "access_level": header(headers, "x-access-level"),
               "result_count": (body.get("meta") or {}).get("result_count"), "meta": body.get("meta"),
               "items": items, "estimated_cost": cost, "price_note": note,
               "error_body": (body.get("errors") or body.get("detail") or raw[:2000].decode("utf-8", "replace"))
               if (status is None or status >= 400 or body.get("errors")) else None,
               "raw_path": f"raw/{call_id}.json"}
        self.store.append(self.store.requests, row)
        self.last_row = row

    def get(self, path: str, params: dict, *, kind: str, reserve: float, **ctx) -> tuple[dict, dict]:
        """(log row, body). A rejected request (4xx) comes back as data, not an exception."""
        now = self.clock()
        guard_clock(now)
        self.store.check_x_budget(now, ctx.get("stage", ""), reserve, f"{ctx.get('step')} {path}")
        self.context = {**ctx, "kind": kind, "params": params}
        self.last_row = None
        try:
            body = self.request("GET", path, params, 0.0, partial_ok=True)
        except x_api.XApiError:
            row = self.last_row
            if row is None or row["status"] is None or row["status"] < 400:
                raise  # network failure, or X reported write access: stop
            body = json.loads((self.store.root / row["raw_path"]).read_bytes() or b"{}") if row["raw_path"] else {}
        self.store.log_budget(now, "call", id=self.last_row["call_id"], step=ctx.get("step"),
                              status=self.last_row["status"], est=f"{self.last_row['estimated_cost']:.4f}")
        return self.last_row, body


def count_items(body: dict) -> dict:
    data = body.get("data")
    includes = body.get("includes") or {}
    return {"data": len(data) if isinstance(data, list) else (1 if data else 0),
            "users": len(includes.get("users") or []), "included_posts": len(includes.get("tweets") or [])}


def estimate_cost(kind: str, items: dict) -> tuple[float, str]:
    """Conservative: every item billed, repeats included, until the pilot shows otherwise."""
    if kind == "usage":
        return 0.0, "usage endpoint (assumed free)"
    if kind == "counts":
        return round(items["data"] * POST, 4), "counts price unknown; provisional $0.005 per bucket (F4)"
    cost = items["data"] * POST + items["included_posts"] * POST + items["users"] * USER
    return round(cost, 4), "posts $0.005, users $0.010 (F1/F2 unverified)"


def lookup_ids(client: LoggedClient, ids: list[str], authors: bool, **ctx) -> tuple[dict, dict, str]:
    """({id: X post}, {id: error title}, call id) for up to 100 ids."""
    ids = [i for i in dict.fromkeys(ids) if i.isdigit()][:100]
    if not ids:
        return {}, {}, ""
    params = {"ids": ",".join(ids), "tweet.fields": TWEET_FIELDS}
    if authors:
        params |= {"expansions": "author_id", "user.fields": USER_FIELDS}
    reserve = len(ids) * (POST + (USER if authors else 0))
    row, body = client.get("/2/tweets", params, kind="posts", reserve=reserve, **ctx)
    users = {u["id"]: u.get("username") for u in (body.get("includes") or {}).get("users", [])}
    found = {p["id"]: {**x_api.with_full_text(p), "author": users.get(p.get("author_id"))}
             for p in body.get("data") or []}
    errors = {e.get("resource_id") or e.get("value"): e.get("title") or e.get("detail")
              for e in body.get("errors") or [] if e.get("resource_id") or e.get("value")}
    return found, errors, row["call_id"]


# ---------- Grok ----------

SLOT_RE = re.compile(r"^- \[post:(\d+)\] ID:[ \t]*(\S*)[ \t]*$", re.M)


def parse_slots(text: str) -> list[dict]:
    """Rendered tool text -> result slots. A blank ID is an empty slot: counted, never scored."""
    marks = list(SLOT_RE.finditer(text))
    slots = []
    for n, mark in enumerate(marks):
        chunk = text[mark.end(): marks[n + 1].start() if n + 1 < len(marks) else len(text)]
        chunk = re.split(r"\n---\s*\n|\nMain Post:", chunk)[0]
        field = lambda name: (m.group(1).strip() if (m := re.search(rf"^- {name}:[ \t]*(.*)$", chunk, re.M)) else None)
        content = re.search(r"^- Content:[ \t]?(.*)", chunk, re.M | re.S)
        author = field("Author")
        handle = re.search(r"@([A-Za-z0-9_]{1,15})\s*$", author or "")
        stamp = parse_stamp(field("Timestamp"))
        post_id = mark.group(2) if mark.group(2).isdigit() else None
        slots.append({"slot": int(mark.group(1)), "id": post_id, "conversation_id": field("Conversation ID"),
                      "author": handle.group(1) if handle else None, "created_at": iso(stamp) if stamp else None,
                      "text": content.group(1).strip() if content else None})
    return slots


def text_of(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return "\n".join(text_of(v) for v in value.values())
    if isinstance(value, list):
        return "\n".join(text_of(v) for v in value)
    return str(value)


def find_key(obj, key: str):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            if (found := find_key(value, key)) is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            if (found := find_key(value, key)) is not None:
                return found
    return None


def parse_stream(stdout: str) -> dict:
    """streaming-json events -> tool calls (with raw output where the CLI gives it), text, usage, errors."""
    tools: dict[str, dict] = {}
    text, errors, end, other, apikey, commands = [], [], None, 0, None, None
    for line in stdout.split("\n"):   # not splitlines(): U+2028 can sit inside a JSON string
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            other += 1
            continue
        if not isinstance(event, dict):
            continue
        kind = event.get("type")
        apikey = apikey or find_key(event, "apiKeySource")
        if kind == "available_commands" and commands is None:
            commands = {"tools": event.get("tools") or [], "commands": event.get("commands") or []}
        if kind == "tool_call":
            tools[event.get("toolCallId") or f"t{len(tools)}"] = {
                "name": event.get("toolName") or event.get("title"), "kind": event.get("kind"),
                "input": event.get("rawInput"), "output": event.get("rawOutput"), "status": event.get("status")}
        elif kind == "tool_call_update":
            call = tools.setdefault(event.get("toolCallId") or f"t{len(tools)}", {"name": None, "input": None, "output": None})
            if event.get("rawOutput") is not None:
                call["output"] = event["rawOutput"]
            if event.get("rawInput") is not None and call.get("input") is None:
                call["input"] = event["rawInput"]
            call["status"] = event.get("status") or call.get("status")
            if event.get("content") and call.get("output") is None:
                call["content"] = event["content"]
        elif kind == "text":
            text.append(event.get("data") or "")
        elif kind == "error":
            errors.append(event.get("message") or json.dumps(event)[:500])
        elif kind == "end":
            end = event
    for call in tools.values():
        # server-side X search: rawOutput holds the observed call {name, input (JSON string)}, not its results
        out = call.get("output")
        if isinstance(out, dict) and out.get("name"):
            call["observed_tool"] = out["name"]
            try:
                call["observed_args"] = json.loads(out.get("input") or "null")
            except (TypeError, json.JSONDecodeError):
                call["observed_args"] = out.get("input")
    loaded = sorted(PROJECT_SKILLS & set((commands or {}).get("commands", [])))
    return {"tools": list(tools.values()), "text": "".join(text), "errors": errors, "end": end,
            "unparsed_lines": other, "api_key_source": apikey,
            "session_tools": (commands or {}).get("tools"), "project_skills_loaded": loaded}


def closing_posts(text: str) -> list[dict]:
    try:
        obj = last_json_object(text)
    except ValueError:
        return []
    posts = obj.get("posts") if isinstance(obj, dict) else None
    return [p for p in posts if isinstance(p, dict)] if isinstance(posts, list) else []


def grok_cost(end: dict | None, fetched: int) -> tuple[float, str]:
    if end and end.get("total_cost_usd") is not None:
        return float(end["total_cost_usd"]), "reported by CLI"
    usage = (end or {}).get("usage") or {}
    tokens = (usage.get("input_tokens", 0) * GROK_TOKEN_USD["input"]
              + usage.get("cache_read_input_tokens", 0) * GROK_TOKEN_USD["cached"]
              + usage.get("output_tokens", 0) * GROK_TOKEN_USD["output"])
    return round(tokens + fetched * POST, 4), "estimated (tokens at grok-4.7 rates + posts fetched × $0.005)"


class GrokRunner:
    def __init__(self, store: Store, runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
                 clock: Callable[[], datetime] | None = None, binary: Path = GROK, cwd_root: Path = GROK_CWD_ROOT) -> None:
        self.store, self.runner, self.binary, self.cwd_root = store, runner, binary, cwd_root
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self._version: str | None = None

    def version(self) -> str:
        if self._version is None:
            try:
                out = self.runner([str(self.binary), "--version"], capture_output=True, text=True, check=False, timeout=30)
                self._version = (out.stdout or out.stderr).strip()
            except (OSError, subprocess.SubprocessError) as exc:
                self._version = f"unknown ({exc})"
        return self._version

    def run(self, run_id: str, prompt: str, *, model: str, effort: str, timeout: int = 900) -> dict:
        now = self.clock()
        guard_clock(now)
        self.store.check_grok_budget(now, run_id)
        cwd = self.cwd_root / run_id
        if REPO in cwd.resolve().parents:
            raise Stop(f"{cwd} is inside the repo; Grok would load its AGENTS.md and skills")
        cwd.mkdir(parents=True, exist_ok=True)
        if any(cwd.iterdir()):
            raise Stop(f"{cwd} is not empty; Grok must start in an empty folder")
        cmd = [str(self.binary), "-p", prompt, "--verbatim", "--output-format", "streaming-json",
               "--sandbox", "read-only", "--deny", "Bash", "--deny", "Edit", "--deny", "Write",
               "-m", model, "--effort", effort, "--max-turns", "8"]
        env = {**os.environ, "GROK_MEMORY": "0"}
        started, timed_out = time.monotonic(), False
        try:
            result = self.runner(cmd, cwd=str(cwd), env=env, capture_output=True, text=True, check=False, timeout=timeout)
            stdout, stderr, code = result.stdout or "", result.stderr or "", result.returncode
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            code, timed_out = None, True
        saved = {}
        for name, data in (("stdout", stdout), ("stderr", stderr)):   # untouched, before any parsing
            path = self.store.root / "grok" / f"{run_id}.{name}"
            path.write_text(data, encoding="utf-8")
            saved[name] = {"path": str(path.relative_to(self.store.root)), "bytes": len(data.encode()),
                           "sha256": hashlib.sha256(data.encode()).hexdigest()}
        stream = parse_stream(stdout)
        failed = timed_out or code != 0 or bool(stream["errors"]) or stream["end"] is None
        status = "ok"
        if failed:
            evidence = stderr + "\n" + "\n".join(stream["errors"])
            if re.search(r"max[_ -]?turns", evidence, re.I):
                status = "blocked-grok-error"   # hit --max-turns: a prompt problem, not the weekly limit
            else:
                status = "blocked-grok-limit" if LIMIT_RE.search(evidence) else "blocked-grok-error"
        return {"run_id": run_id, "time_utc": iso(now), "time_brisbane": now.astimezone(BRISBANE).isoformat(),
                "duration_ms": round((time.monotonic() - started) * 1000), "prompt": prompt,
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "cmd_flags": cmd[3:],
                "model": model, "effort": effort, "cwd": str(cwd), "env": {"GROK_MEMORY": "0"},
                "cli_version": self.version(), "exit_code": code, "timed_out": timed_out, "status": status,
                "saved": saved, "stream": stream, "stderr_tail": stderr[-1000:]}


ID_IN_TEXT = re.compile(r"(?<![0-9])(1[0-9]{17,19}|2[0-9]{17,19})(?![0-9])")


def mentioned_ids(text: str, exclude: set) -> list[dict]:
    """Post ids Grok named in its answer but left out of its closing JSON (26 Sep: G-self listed 24, kept 0)."""
    return [{"slot": None, "id": pid, "author": None, "created_at": None, "text": None, "tool_index": None,
             "tool": None, "mentioned_only": True}
            for pid in dict.fromkeys(ID_IN_TEXT.findall(text)) if pid not in exclude]


def run_claims(run: dict) -> tuple[list[dict], str]:
    """Posts from the tools' own output when the CLI shows it, else from Grok's closing JSON.
    Ids named only in the answer text are added as mentioned_only (checked, labelled apart)."""
    raw_slots = []
    for n, tool in enumerate(run["stream"]["tools"]):
        for slot in parse_slots(text_of(tool.get("output")) or text_of(tool.get("content"))):
            raw_slots.append({**slot, "tool_index": n, "tool": tool.get("name")})
    if raw_slots:
        return raw_slots, "tool_output"
    posts = closing_posts(run["stream"]["text"])
    kept = [{"slot": n, "id": str(p.get("id")) if str(p.get("id") or "").isdigit() else None,
             "author": (p.get("author") or "").split("@")[-1] or None, "created_at": p.get("created_at"),
             "text": p.get("text"), "tool_index": None, "tool": None,
             "kept_by_grok": p.get("kept") if isinstance(p.get("kept"), bool) else None} for n, p in enumerate(posts)]
    return kept + mentioned_ids(run["stream"]["text"], {k["id"] for k in kept}), "closing_json"


def check_claims(client: LoggedClient, slots: list[dict], window: dict, cap: int, authors: bool,
                 claims_from: str, verify_when_tool_output: bool = True, **ctx) -> tuple[list[dict], dict]:
    """Label each claimed post and apply the exact window. Returns (per-slot results, four-step counts)."""
    ids = list(dict.fromkeys(s["id"] for s in slots if s["id"]))
    to_check = ids[:cap] if (verify_when_tool_output or claims_from != "tool_output") else []
    found, errors, call_id = lookup_ids(client, to_check, authors, **ctx) if to_check else ({}, {}, "")
    results = []
    for slot in slots:
        pid = slot["id"]
        x_post = found.get(pid) if pid else None
        if not pid:
            label = "empty_slot"
        elif pid not in to_check:
            label = "unchecked"
        elif x_post is None:
            title = (errors.get(pid) or "").lower()
            if "authoriz" in title or "forbidden" in title or "suspend" in title:
                label = "unavailable"
            else:
                # a deleted post is also absent: flag when the id's own timestamp matches the claimed time
                claimed = parse_stamp(slot.get("created_at"))
                match = claimed is not None and abs((x_api.posted_at(pid) - claimed).total_seconds()) < 120
                label = "not_found_time_matches" if match else "invented"
        elif slot.get("mentioned_only"):
            label = "mentioned_exists"
        elif same_text(slot.get("text"), x_api.full_text(x_post)) or not slot.get("text"):
            label = "real" if slot.get("text") else "real_no_claimed_text"
        else:
            label = "misquoted"
        stamp = (x_post or {}).get("created_at") or slot.get("created_at")
        if authors and x_post and slot.get("author") and x_post.get("author") \
                and slot["author"].lower() != x_post["author"].lower():
            label += "+wrong_author"
        ok, why = eligible(x_post, window)
        results.append({**slot, "label": label, "x": x_post, "in_window": in_window(stamp, window) if pid else None,
                        "eligible": ok, "eligible_reason": why, "verify_call": call_id or None})
    confirmed = [r for r in results if r["label"].startswith("real") and not r.get("mentioned_only")]
    mentioned = [r for r in results if r.get("mentioned_only")]
    counts = {"slots": len(slots) - len(mentioned), "numeric_ids": len(ids) - len(mentioned),
              "mentioned_only": len(mentioned),
              "mentioned_only_exist": sum(1 for r in mentioned if r["x"]),
              "mentioned_only_in_window": sum(1 for r in mentioned if r["x"] and r["in_window"]),
              "confirmed": len({r["id"] for r in confirmed}),
              "confirmed_in_window": len({r["id"] for r in confirmed if r["in_window"]}),
              "confirmed_eligible": len({r["id"] for r in confirmed if r["eligible"]}),
              "kept_by_grok": len({r["id"] for r in results if r["id"] and r.get("kept_by_grok")}),
              "out_of_window": len({r["id"] for r in results if r["id"] and r["in_window"] is False}),
              "labels": {lab: sum(1 for r in results if r["label"] == lab) for lab in sorted({r["label"] for r in results})},
              "unchecked": len(ids) - len(to_check)}
    return results, counts


# ---------- frozen ideas and queries (hashed on first stage use; re-checked after the pilot) ----------

IDEAS = {
    "demand-tech-1": {"job": "demand", "niche": "tech",
                      "text": "people asking for a free alternative to a paid creator or developer tool",
                      "k": ['("free alternative" OR "open source alternative" OR "cheaper alternative") (tool OR app OR software) -is:retweet lang:en',
                            '("is there a free" OR "any free alternative" OR "what do you use instead of") -is:retweet lang:en'],
                      "semantic": "someone asking for a free or open-source alternative to a paid creator or developer tool"},
    "demand-tech-2": {"job": "demand", "niche": "tech",
                      "text": "people stuck getting results from AI coding agents (Claude Code, Codex, Cursor)",
                      "k": ['("Claude Code" OR Codex OR Cursor) (stuck OR broken OR "doesn\'t work" OR "can\'t get" OR "keeps") -is:retweet lang:en',
                            '("Claude Code" OR Codex OR Cursor) ("how do I" OR "anyone know" OR "why does" OR help) -is:retweet lang:en'],
                      "semantic": "a developer frustrated or stuck because an AI coding agent like Claude Code, Codex or Cursor is not giving good results"},
    "demand-comedy-1": {"job": "demand", "niche": "comedy",
                        "text": "what people are collectively reacting to or annoyed by today",
                        "k": ['("is anyone else" OR "am I the only one" OR "why is everyone") -is:retweet lang:en min_likes:10',
                              '("everyone is talking about" OR "the discourse" OR "trending because") -is:retweet lang:en'],
                        "semantic": "people reacting to or complaining about something everyone is talking about today"},
    # 1b/2b: first query without min_likes:10 (27 Sep); the originals stay as run
    "demand-comedy-1b": {"job": "demand", "niche": "comedy",
                         "text": "what people are collectively reacting to or annoyed by today",
                         "k": ['("is anyone else" OR "am I the only one" OR "why is everyone") -is:retweet lang:en',
                               '("everyone is talking about" OR "the discourse" OR "trending because") -is:retweet lang:en'],
                         "semantic": "people reacting to or complaining about something everyone is talking about today"},
    "demand-comedy-2": {"job": "demand", "niche": "comedy",
                        "text": "running jokes or memes forming around a current event",
                        "k": ['(meme OR memes OR "the jokes") (today OR "this week" OR "right now") -is:retweet lang:en min_likes:10',
                              '("the timeline is" OR "twitter is" OR "X is") (jokes OR memes OR unhinged) -is:retweet lang:en'],
                        "semantic": "people making the same running joke or meme about something that just happened"},
    "demand-comedy-2b": {"job": "demand", "niche": "comedy",
                         "text": "running jokes or memes forming around a current event",
                         "k": ['(meme OR memes OR "the jokes") (today OR "this week" OR "right now") -is:retweet lang:en',
                               '("the timeline is" OR "twitter is" OR "X is") (jokes OR memes OR unhinged) -is:retweet lang:en'],
                         "semantic": "people making the same running joke or meme about something that just happened"},
    "wj-tech-1": {"job": "worth-joining", "niche": "tech",
                  "text": "builders sharing progress on an AI app or tool",
                  "k": ['("just shipped" OR "just launched" OR "working on" OR "build in public" OR buildinpublic) (AI OR agent OR LLM) -is:retweet -is:reply lang:en',
                        '#buildinpublic (AI OR agent OR LLM OR app) -is:retweet -is:reply lang:en'],
                  "semantic": "a builder sharing progress, a demo or a launch of an AI app or tool they are making",
                  "t_rule": [r"\b(shipped|launched|launch|building|working on|build in public|buildinpublic|demo|v\d)\b",
                             r"\b(AI|agent|agents|LLM|app|tool|model)\b"]},
    "wj-tech-2": {"job": "worth-joining", "niche": "tech",
                  "text": "discussion of an AI model or tool released in the last day",
                  "k": ['("just released" OR "just dropped" OR "now available" OR "new model") (AI OR LLM OR model) -is:retweet lang:en',
                        '(released OR launched OR announces OR announced) (GPT OR Claude OR Gemini OR Grok OR Llama OR Qwen OR DeepSeek) -is:retweet lang:en'],
                  "semantic": "people discussing an AI model or AI tool that was released in the last day",
                  "t_rule": [r"\b(released|release|launch|launched|new model|dropped|available|announc\w*)\b",
                             r"\b(AI|model|GPT|Claude|Gemini|Grok|Llama|Qwen|DeepSeek|agent|Codex|Cursor)\b"]},
    "wj-comedy-1": {"job": "worth-joining", "niche": "comedy",
                    "text": "a satirist's or comedian's post with an active thread of people riffing",
                    "k": ['(satire OR satirical OR comedian OR "stand up" OR standup) -is:retweet -is:reply lang:en min_replies:5',
                          '(joke OR bit OR "hot take") -is:retweet -is:reply lang:en min_replies:10 min_likes:50'],
                    "semantic": "a comedian or satirist's joke post that lots of people are riffing on in the replies"},
    "wj-comedy-2": {"job": "worth-joining", "niche": "comedy",
                    "text": "an absurd news story with people joking in the replies",
                    "k": ['("florida man" OR absurd OR "you can\'t make this up" OR "this is real") (news OR headline OR story) -is:retweet -is:reply lang:en min_replies:5',
                          '("real headline" OR "actual headline" OR "not the onion" OR "the onion") -is:retweet -is:reply lang:en'],
                    "semantic": "an absurd real news story that people are joking about"},
    "tr-tech-1": {"job": "tool-research", "niche": "tech",
                  "text": "DaVinci Resolve as a Premiere alternative",
                  "k": ['"DaVinci Resolve" (Premiere OR "Premiere Pro" OR Adobe) -is:retweet lang:en',
                        '"DaVinci Resolve" -is:retweet lang:en'],
                  "spam": '"DaVinci Resolve" -is:retweet -is:nullcast -has:links -giveaway -discount lang:en',
                  "semantic": "people comparing DaVinci Resolve with Premiere Pro or switching between them"},
    "tr-tech-2": {"job": "tool-research", "niche": "tech",
                  "text": "Cursor (the AI code editor)",
                  "k": ['Cursor (IDE OR editor OR "AI editor" OR agent OR composer) -is:retweet lang:en',
                        '("Cursor IDE" OR "cursor.com" OR @cursor_ai) -is:retweet lang:en'],
                  "spam": 'Cursor (IDE OR editor) -is:retweet -is:nullcast -has:links -giveaway -discount lang:en',
                  "semantic": "what developers like or dislike about the Cursor AI code editor"},
    "tr-tech-3": {"job": "tool-research", "niche": "tech",
                  "text": "Claude Code (the AI coding agent)",
                  "k": ['"Claude Code" -is:retweet lang:en',
                        '"Claude Code" (love OR hate OR "switched to" OR vs OR "compared to" OR annoying OR "rate limit" OR pricing) -is:retweet lang:en'],
                  "spam": '"Claude Code" -is:retweet -is:nullcast -has:links -giveaway -discount -course lang:en',
                  "semantic": "developers talking about what they like or dislike about using Claude Code"},
    "tr-comedy-1": {"job": "tool-research", "niche": "comedy",
                    "text": "CapCut among meme and video creators",
                    "k": ['CapCut (meme OR memes OR edit OR edits OR template) -is:retweet lang:en',
                          'CapCut (watermark OR export OR pro OR paywall OR subscription) -is:retweet lang:en'],
                    "spam": 'CapCut -is:retweet -is:nullcast -has:links -template -"capcut pro" lang:en',
                    "semantic": "meme and video creators talking about what they like or dislike about CapCut"},
    "tr-comedy-2": {"job": "tool-research", "niche": "comedy",
                    "text": "Substack among satire and comedy writers",
                    "k": ['Substack (satire OR comedy OR humor OR humour) -is:retweet lang:en',
                          'Substack (writer OR newsletter) (funny OR satire OR jokes) -is:retweet lang:en'],
                    "spam": 'Substack (satire OR comedy) -is:retweet -is:nullcast -"subscribe now" -giveaway lang:en',
                    "semantic": "satire or comedy writers talking about using Substack"},
}
STAGE_JOB = {1: "worth-joining", 2: "demand", 3: "tool-research"}
# Sort order is a reported factor, never pooled (Codex review, High 2): each sort is its own K source.
K_SORTS = {"worth-joining": ("recency",), "demand": ("recency", "relevancy"), "tool-research": ("recency", "relevancy")}
SPAM_TYPES = ("genuine", "account-selling", "promotion", "engagement-bait", "product-marketing", "off-topic", "other")

API_ONLY = re.compile(r"\b(min_likes|min_reposts|is|has|lang):")   # min_replies: is valid in both
WEB_ONLY = re.compile(r"\b(min_faves|min_retweets|filter|within_time|since|until):")
MIN_REPLIES = re.compile(r"\bmin_replies:\d+")
BLOCK_ID = re.compile(r"B\d+")


def check_syntax(query: str, source: str) -> None:
    """X API v2 syntax for K, X website syntax for Grok's keyword tool. Never mixed."""
    bad = WEB_ONLY.search(query) if source == "api" else API_ONLY.search(query)
    if bad:
        raise Stop(f"{source} query uses {bad.group(0)!r}, which belongs to the other syntax: {query}")


def to_web_syntax(query: str, hours: int) -> str:
    q = re.sub(r"\s*lang:\w+", "", query)
    q = re.sub(r"\s*-is:(retweet|nullcast)", "", q)
    q = q.replace("-is:reply", "-filter:replies").replace("min_likes:", "min_faves:").replace("min_reposts:", "min_retweets:")
    q = q.replace("-has:links", "-filter:links")
    q = f"{q} within_time:{hours}h" if hours <= 72 else f"{q} within_time:{hours // 24}d"
    check_syntax(q, "web")
    return q


def frozen_hash() -> str:
    return hashlib.sha256(json.dumps(IDEAS, sort_keys=True).encode()).hexdigest()[:16]


# ---------- prompts ----------

CAP = "Run at most 3 searches, and set limit 10 on every search."
# plan.md: all retrieved posts are scored, none hand-picked. Grok lists everything and flags its own choice.
OUTPUT = ('When you finish, end your answer with one JSON object, {"posts": [{"id": "...", "author": "...", '
          '"created_at": "...", "text": "...", "kept": true}]}, listing every post your searches returned, once each, '
          'with the text exactly as the tool returned it. Set "kept" to true for the posts that fit the request and false '
          "for the rest. A value the tool did not return is null. Never list a post the tool did not return.")
HINT = "Search by meaning, not just keywords; try several phrasings."


def window_words(window: dict) -> tuple[str, str, str]:
    """Semantic dates are UTC days and to_date is exclusive (26 Sep probes: 25→25 empty, 26→27 returned posts
    1 h old from 01:16Z on). So to_date is the day after the window ends; the exact window is applied afterwards."""
    start, end = parse_stamp(window["start"]), parse_stamp(window["end"])
    return (f"Only posts created between {window['start']} and {window['end']} (UTC).",
            start.strftime("%Y-%m-%d"), (end + timedelta(days=1)).strftime("%Y-%m-%d"))


def arm_prompt(arm: str, idea: dict, window: dict, hours: int) -> str:
    words, from_date, to_date = window_words(window)
    dates = f"If you use semantic search, set from_date {from_date} and to_date {to_date}."
    if arm == "steered":
        web = to_web_syntax(idea["k"][0], hours)
        return f"Run x_keyword_search once with this exact query, mode Latest, limit 10: {web}\n{CAP}\n{OUTPUT}"
    if arm == "free":
        return f"Find posts on X by {idea['text']}. {words}\n{CAP}\n{OUTPUT}"
    if arm == "hinted":
        return f"Find posts on X by {idea['text']}. {words} {HINT} {dates}\n{CAP}\n{OUTPUT}"
    if arm == "self":
        # The shape of Grok's own prompt (report §7b), with explicit UTC dates, limit 10 and the shared cap.
        web1 = to_web_syntax(idea["k"][0], hours)
        web2 = to_web_syntax(idea["k"][1], hours)
        return (f"Do both, then keep the overlap.\n\n"
                f"A. x_keyword_search, mode Latest, limit 10, two queries:\n   1. {web1}\n   2. {web2}\n\n"
                f"B. x_semantic_search, limit 10, from_date = {from_date}, to_date = {to_date}, "
                f"min_score_threshold 0.18, query:\n   \"{idea['semantic']}\"\n\n"
                f"Keep a semantic hit only when its returned timestamp is between {window['start']} and {window['end']} (UTC). "
                "If the semantic result has no timestamp, list it under \"time unknown\" and do not treat it as inside the window.\n\n"
                f"Return id, author, time, full text, and engagement only when the tool result included them. Do not paraphrase.\n{CAP}\n{OUTPUT}")
    raise Stop(f"unknown arm {arm!r}")


PILOT_ARMS = {"P7-free": ("free", "high"), "P7-steered": ("steered", "high"), "P7-hinted": ("hinted", "high"),
              "P7-self": ("self", "high"), "P7-free-low": ("free", "low")}
PILOT_IDEA = "demand-tech-1"


PROBE_OUTPUT = ('When you finish, end your answer with one JSON object, {"posts": [{"id": "...", "author": "...", '
                '"created_at": "...", "text": "..."}]}, listing every post the search returned, in the order returned, '
                "including any you would normally leave out. A value the tool did not return is null. Never list a post "
                "the tool did not return.")
PROBE_QUERY = "people asking for a free alternative to a paid app"        # P8-a's query, kept for comparison
BUSY_QUERY = "people talking about artificial intelligence"               # posted about every minute


def probe_prompt(step: str, now: datetime) -> tuple[str, dict]:
    """Semantic date probes. 26 Sep: P8-a (26 Sep to 26 Sep) came back empty; these separate the three
    explanations: end day excluded, US time zone, or an index running behind."""
    utc_today = now.astimezone(timezone.utc).date()
    local_today = now.astimezone(BRISBANE).date()
    yesterday, tomorrow = utc_today - timedelta(days=1), utc_today + timedelta(days=1)

    def one(query, from_date=None, to_date=None):
        dates = f", from_date {from_date}, to_date {to_date}" if from_date else ", with no from_date or to_date"
        return f'Run x_semantic_search exactly once: query "{query}", limit 10{dates}. Run no other search.\n{PROBE_OUTPUT}'

    if step == "P8-a":
        day, case = (local_today, "brisbane-date") if local_today != utc_today else (utc_today, "utc-today")
        return (f'Run x_semantic_search exactly once: query "{PROBE_QUERY}", limit 10, from_date {day}, to_date {day}. '
                f"Run no other search.\n{OUTPUT}", {"case": case, "query": PROBE_QUERY, "from_date": str(day), "to_date": str(day)})
    if step == "P8-b":
        return one(PROBE_QUERY, yesterday, yesterday), {"case": "single-day-yesterday", "query": PROBE_QUERY,
                                                        "from_date": str(yesterday), "to_date": str(yesterday)}
    if step == "P8-d":
        return one(PROBE_QUERY, utc_today, tomorrow), {"case": "to-date-tomorrow", "query": PROBE_QUERY,
                                                       "from_date": str(utc_today), "to_date": str(tomorrow)}
    if step == "P8-e":
        return one(BUSY_QUERY), {"case": "no-dates-busy-topic", "query": BUSY_QUERY, "from_date": None, "to_date": None}
    if step == "P8-f":
        return one(BUSY_QUERY, utc_today, tomorrow), {"case": "to-date-tomorrow-busy-topic", "query": BUSY_QUERY,
                                                      "from_date": str(utc_today), "to_date": str(tomorrow)}
    return (f"Run x_semantic_search exactly twice, each limit 10, from_date {yesterday}, to_date {tomorrow}. "
            f'First query: "{PROBE_QUERY}". Second query: "{PROBE_QUERY} within_time:6h min_faves:5 -filter:replies". '
            f"Run no other search.\n{PROBE_OUTPUT}",
            {"case": "keyword-syntax-in-semantic", "query": PROBE_QUERY, "from_date": str(yesterday), "to_date": str(tomorrow)})


# ---------- pilot ----------

PROBES = ("P8-a", "P8-b", "P8-d", "P8-e", "P8-f", "P8-c")
PILOT_ORDER = ["P0", "P1", "P1b", "P1c", "P1d", "P2", "P3", "P4", "P5", "P9",
               "P7-free", "P7-steered", "P7-hinted", "P7-self", "P7-free-low", *PROBES]
GROK_STEPS = {s for s in PILOT_ORDER if s.startswith(("P7", "P8"))}
P1_BASE = IDEAS[PILOT_IDEA]["k"][0]
P1_QUERY = P1_BASE.replace(" lang:en", " -is:reply lang:en min_likes:5")
WORST = {"P0": 0.0, "P1": 2 * 10 * POST, "P1b": 10 * POST, "P1c": 10 * POST, "P1d": 20 * POST, "P2": 10 * (POST + USER), "P3": 8 * POST,
         "P4": 10 * POST, "P5": 3 * 10 * POST, "P9": None,
         **{s: ARM_VERIFY_CAP * POST for s in PILOT_ARMS}, **{s: PROBE_VERIFY_CAP * POST for s in PROBES}}
DESCRIBE = {
    "P0": "GET /2/usage/tweets (days=7): usage endpoint probe [F11]",
    "P1": f"recent search, 10 posts, all post fields: {P1_QUERY} (rerun without min_likes: if rejected) [F1 F7 F9 F10]",
    "P1b": "P1's query with sort_order=relevancy [F8]",
    "P1c": "P1's base query + min_replies:1 [F7]",
    "P1d": "P1's base query without min_likes:, recency then relevancy [F8]",
    "P2": "P1's query again + expansions=author_id + user fields, same UTC day [F2 F3]",
    "P3": "GET /2/tweets/counts/recent, granularity=day, 7 days, query adds min_replies:1 [F4 F7]",
    "P4": "GET /2/users/:id/timelines/reverse_chronological, 10 posts [F5]",
    "P5": "recent search with 4,097-, 1,025- and 513-character queries, max_results=10 (longest first) [F6]",
    "P9": "look up the post ids from Grok's 26 Sep live run [G3]",
    "P7-free": "Grok arm G-free, effort high; claims checked [G1–G6]",
    "P7-steered": "Grok arm G-steered (keyword query, website syntax), effort high",
    "P7-hinted": "Grok arm G-hinted, effort high",
    "P7-self": "Grok arm G-self (Grok's own prompt §7b, adjusted), effort high",
    "P7-free-low": "Grok arm G-free, effort low (effort comparison)",
    "P8-a": "semantic probe: one calendar day (Brisbane date when it differs from UTC)",
    "P8-b": "semantic probe: from_date = to_date = UTC yesterday (do single-day ranges work?)",
    "P8-d": "semantic probe: UTC today to tomorrow, P8-a's query (is the end day excluded?)",
    "P8-e": "semantic probe: no dates, busy topic (how old is the newest hit: index delay?)",
    "P8-f": "semantic probe: UTC today to tomorrow, busy topic",
    "P8-c": "semantic probe: same query with and without keyword operators (optional; S9 already saw them ignored)",
}
LIVE_RUN = PRIVATE / "grok-insights" / "runs" / "semantic-live-2026-09-26" / "calls"


def live_run_ids(folder: Path = LIVE_RUN) -> dict[str, list[dict]]:
    return {f.name.split(".")[0]: parse_slots(f.read_text(encoding="utf-8"))
            for f in sorted(folder.glob("*.raw.txt"))} if folder.exists() else {}


def worst_case(folder: Path = LIVE_RUN) -> dict:
    ids = {s["id"] for slots in live_run_ids(folder).values() for s in slots if s["id"]}
    table = {s: (len(ids) * POST if s == "P9" else WORST[s]) for s in PILOT_ORDER}
    return {"steps": table, "x_total": round(sum(table.values()), 4), "p9_ids": len(ids),
            "grok_runs": len(GROK_STEPS), "grok_total": round(len(GROK_STEPS) * GROK_RESERVE, 2)}


class Harness:
    def __init__(self, store: Store, client: LoggedClient, grok: GrokRunner,
                 clock: Callable[[], datetime] | None = None, live_folder: Path = LIVE_RUN) -> None:
        self.store, self.client, self.grok, self.live_folder = store, client, grok, live_folder
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    # step bookkeeping
    def step_state(self, name: str) -> dict:
        return self.store.progress()["steps"].get(name, {"status": "pending", "attempts": []})

    def record(self, name: str, status: str, attempt: dict, todo: str = "") -> None:
        data = self.store.progress()
        step = data["steps"].setdefault(name, {"status": "pending", "attempts": []})
        step["status"], step["todo"] = status, todo
        step["attempts"].append(attempt)
        self.store.save_progress(data)

    def next_step(self) -> str | None:
        return next((s for s in PILOT_ORDER if self.step_state(s)["status"] != "done"), None)

    def run_pilot_step(self, name: str, redo: bool = False) -> dict:
        if name not in PILOT_ORDER:
            raise Stop(f"unknown pilot step {name!r}; steps are {', '.join(PILOT_ORDER)}")
        if self.step_state(name)["status"] == "done" and not redo:
            raise Stop(f"{name} is already done; pass --redo to run it again (earlier attempts are kept)")
        now = self.clock()
        attempt = {"started": iso(now)}
        try:
            guard_clock(now)
            block = self.store.block(now)
            ctx = {"stage": "pilot", "step": name, "block": block["id"]}
            attempt["block"] = block["id"]
            result = getattr(self, "_" + name.replace("-", "_"))(ctx, block, now)
        except Stop as exc:
            self.record(name, "blocked-budget" if "ceiling" in str(exc) or "checkpoint" in str(exc) else "pending",
                        {**attempt, "stopped": str(exc)}, todo=str(exc))
            raise
        except x_api.XApiError as exc:
            self.record(name, "failed-x", {**attempt, "error": str(exc)}, todo="look at the error, then retry this step")
            raise
        status = result.pop("status", "done")
        self.record(name, status, {**attempt, **result, "ended": iso(self.clock())}, todo=result.get("todo", ""))
        return {"step": name, "status": status, **result}

    # --- X API steps ---
    def _search(self, ctx, query, window, reserve_posts=10, authors=False, sort="recency", **extra):
        params = {"query": query, "max_results": "10", "tweet.fields": TWEET_FIELDS, "sort_order": sort,
                  "start_time": window["start"], "end_time": window["end"], **extra}
        if authors:
            params |= {"expansions": "author_id", "user.fields": USER_FIELDS}
        reserve = reserve_posts * (POST + (USER if authors else 0))
        return self.client.get("/2/tweets/search/recent", params, kind="posts", reserve=reserve, **{"source": "K", **ctx})

    def _note_posts(self, now, row, body, ctx, source="K", window=None):
        users = {u["id"]: u.get("username") for u in (body.get("includes") or {}).get("users", [])}
        found = []
        for n, p in enumerate(body.get("data") or []):
            ok, why = eligible(p, window) if window else (None, "no window")
            found.append({"post_id": p["id"], "label": "x_api", "x": {**p, "author": users.get(p.get("author_id"))},
                          "sighting": {"source": source, "stage": ctx["stage"], "step": ctx["step"], "idea": ctx.get("idea"),
                                       "rank": n, "call": row["call_id"], "block": ctx["block"],
                                       "eligible": ok, "eligible_reason": why}})
        self.store.upsert_posts(now, found)
        return found

    def _freshness(self, body, now):
        stamps = [parse_stamp(p.get("created_at")) for p in body.get("data") or []]
        stamps = [s for s in stamps if s]
        return {"newest_age_min": round((now - max(stamps)).total_seconds() / 60, 1) if stamps else None,
                "oldest_age_min": round((now - min(stamps)).total_seconds() / 60, 1) if stamps else None}

    def _P0(self, ctx, block, now):
        row, _ = self.client.get("/2/usage/tweets", {"days": "7"}, kind="usage", reserve=0.0, **ctx)
        return {"calls": [row["call_id"]], "http": row["status"],
                "answer_hint": "works with these keys" if row["status"] == 200 else "not with these keys (OAuth 1.0a user)"}

    def _P1(self, ctx, block, now):
        window = block["windows"]["demand"]
        row, body = self._search(ctx, P1_QUERY, window)
        calls, query = [row["call_id"]], P1_QUERY
        if row["status"] == 400 and "min_likes" in json.dumps(row["error_body"]):
            query = P1_QUERY.replace(" min_likes:5", "")
            row, body = self._search(ctx, query, window)
            calls.append(row["call_id"])
        if row["status"] != 200:
            return {"status": "failed-x", "calls": calls, "todo": f"P1 returned HTTP {row['status']}; read {row['raw_path']}"}
        self._note_posts(now, row, body, ctx, window=window)
        data = self.store.progress()
        data["settings"]["p1_query"], data["settings"]["p1_utc_date"] = query, now.date().isoformat()
        self.store.save_progress(data)
        return {"calls": calls, "query": query, "posts": len(body.get("data") or []), "window": window,
                **self._freshness(body, now)}

    def _p1(self):
        settings = self.store.progress()["settings"]
        if "p1_query" not in settings:
            raise Stop("run P1 first")
        return settings

    def _same_utc_day(self, settings, now) -> dict:
        same = settings.get("p1_utc_date") == now.astimezone(timezone.utc).date().isoformat()
        return {} if same else {"warning": "not the same UTC day as P1: repeats may bill again (F3 can't be read)"}

    def _P1b(self, ctx, block, now):
        settings = self._p1()
        row, body = self._search(ctx, settings["p1_query"], block["windows"]["demand"], sort="relevancy")
        self._note_posts(now, row, body, ctx, window=block["windows"]["demand"])
        p1_ids = self._ids_of_step("P1")
        ids = [p["id"] for p in body.get("data") or []]
        return {"calls": [row["call_id"]], "posts": len(ids), "overlap_with_p1": len(set(ids) & p1_ids),
                **self._freshness(body, now), **self._same_utc_day(settings, now)}

    def _P1c(self, ctx, block, now):
        window = block["windows"]["demand"]
        query = P1_BASE + " min_replies:1"
        row, body = self._search(ctx, query, window)
        if row["status"] == 200:
            self._note_posts(now, row, body, ctx, window=window)
        replies = [(p.get("public_metrics") or {}).get("reply_count") for p in body.get("data") or []]
        return {"calls": [row["call_id"]], "http": row["status"], "query": query, "posts": len(replies),
                "reply_counts": replies, "error": row["error_body"] if row["status"] != 200 else None}

    def _P1d(self, ctx, block, now):
        window = block["windows"]["demand"]
        out = {"calls": [], "query": P1_BASE}
        sets = {}
        for sort in ("recency", "relevancy"):
            row, body = self._search(ctx, P1_BASE, window, sort=sort)
            out["calls"].append(row["call_id"])
            if row["status"] != 200:
                return {**out, "status": "failed-x", "todo": f"HTTP {row['status']}; read {row['raw_path']}"}
            self._note_posts(now, row, body, ctx, window=window)
            data = body.get("data") or []
            sets[sort] = [p["id"] for p in data]
            likes = sorted((p.get("public_metrics") or {}).get("like_count", 0) for p in data)
            ages = sorted(round((now - parse_stamp(p["created_at"])).total_seconds() / 3600, 1) for p in data if p.get("created_at"))
            out[sort] = {"posts": len(data), "median_likes": likes[len(likes) // 2] if likes else None,
                         "median_age_h": ages[len(ages) // 2] if ages else None, "max_likes": likes[-1] if likes else None}
        out["overlap"] = len(set(sets["recency"]) & set(sets["relevancy"]))
        out["same_order"] = sets["recency"] == sets["relevancy"]
        return out

    def _ids_of_step(self, step: str) -> set:
        calls = {r["call_id"] for r in self.store.rows(self.store.requests) if r.get("step") == step and r.get("status") == 200}
        ids = set()
        for call in calls:
            body = json.loads((self.store.root / "raw" / f"{call}.json").read_bytes() or b"{}")
            ids |= {p["id"] for p in body.get("data") or []}
        return ids

    def _P2(self, ctx, block, now):
        settings = self._p1()
        row, body = self._search(ctx, settings["p1_query"], block["windows"]["demand"], authors=True)
        self._note_posts(now, row, body, ctx, window=block["windows"]["demand"])
        ids = {p["id"] for p in body.get("data") or []}
        return {"calls": [row["call_id"]], "posts": len(ids), "repeat_of_p1": len(ids & self._ids_of_step("P1")),
                "authors": row["items"]["users"], **self._same_utc_day(settings, now),
                "todo": "compare the console delta with the estimate; then `config --authors on` only if authors didn't bill"}

    def _P3(self, ctx, block, now):
        start = iso(now - timedelta(days=6, hours=23))
        params = {"query": P1_BASE + " min_replies:1", "granularity": "day", "start_time": start, "end_time": iso(now)}
        row, body = self.client.get("/2/tweets/counts/recent", params, kind="counts", reserve=WORST["P3"], source="C", **ctx)
        return {"calls": [row["call_id"]], "http": row["status"], "buckets": row["items"]["data"],
                "total_count": (body.get("meta") or {}).get("total_tweet_count")}

    def _P4(self, ctx, block, now):
        params = {"max_results": "10", "tweet.fields": TWEET_FIELDS}
        row, body = self.client.get(f"/2/users/{x_api.USER_ID}/timelines/reverse_chronological", params,
                                    kind="posts", reserve=WORST["P4"], source="T", **ctx)
        if row["status"] == 200:
            self._note_posts(now, row, body, ctx, source="T")
        return {"calls": [row["call_id"]], "http": row["status"], "posts": row["items"]["data"],
                **self._freshness(body, now)}

    def _P5(self, ctx, block, now):
        calls = []
        for length in (4097, 1025, 513):
            query = pad_query(P1_BASE, length)
            row, body = self._search(ctx, query, block["windows"]["demand"])
            calls.append({"length": len(query), "call": row["call_id"], "http": row["status"], "posts": row["items"]["data"]})
            if row["status"] == 200:
                self._note_posts(now, row, body, ctx, window=block["windows"]["demand"])
        return {"calls": calls}

    def _P9(self, ctx, block, now):
        runs = live_run_ids(self.live_folder)
        claimed = {}
        for call, slots in runs.items():
            for slot in slots:
                if slot["id"]:
                    claimed.setdefault(slot["id"], {**slot, "live_call": call})
        empty = sum(1 for slots in runs.values() for s in slots if not s["id"])
        if not claimed:
            return {"status": "failed-x", "todo": f"no ids found under {self.live_folder}"}
        slots = list(claimed.values())
        window = {"start": "2000-01-01T00:00:00Z", "end": iso(now)}
        results, counts = check_claims(self.client, slots, window, cap=100, authors=False,
                                       claims_from="live_run_transcript", source="G-2609", **ctx)
        self._store_claims(now, results, ctx, source="G-2609", arm=None)
        by_call = {}
        for r in results:
            by_call.setdefault(r["live_call"], {}).setdefault(r["label"], 0)
            by_call[r["live_call"]][r["label"]] += 1
        return {"calls": [results[0]["verify_call"]] if results else [], "ids": len(slots), "empty_slots": empty,
                "counts": counts, "labels_by_live_call": by_call,
                "note": "S2.raw.txt was saved from S1.raw.txt (live README): shared ids are counted once"}

    def _store_claims(self, now, results, ctx, source, arm, window=None, run=None):
        found = [{"post_id": r["id"], "label": r["label"], "x": r["x"], "claimed_text": r.get("text"),
                  "sighting": {"source": source, "arm": arm, "stage": ctx["stage"], "step": ctx["step"],
                               "idea": ctx.get("idea"), "rank": r["slot"], "tool_index": r.get("tool_index"),
                               "in_window": r["in_window"], "eligible": r.get("eligible"),
                               "eligible_reason": r.get("eligible_reason"), "kept_by_grok": r.get("kept_by_grok"),
                               "block": ctx["block"], "call": r.get("verify_call"), "run": run}}
                 for r in results if r["id"]]
        self.store.upsert_posts(now, found)

    # --- Grok steps ---
    def _grok_step(self, ctx, block, now, prompt, effort, cap, window, arm, extra=None,
                   verify_when_tool_output=True):
        settings = self.store.progress()["settings"]
        model = settings.get("model")
        if not model:
            raise Stop("no Grok model set: run `grok models` signed in, then `harness.py config --model <id>`")
        run_id = self.store.next_id(self.store.grok_log, "g")
        run = self.grok.run(run_id, prompt, model=model, effort=effort)
        slots, claims_from = run_claims(run)
        results, counts, verify_error = [], {}, None
        try:
            results, counts = check_claims(self.client, slots, window, cap=cap,
                                           authors=bool(settings.get("authors_on_checks")), claims_from=claims_from,
                                           verify_when_tool_output=verify_when_tool_output,
                                           **{"source": "G", **ctx})
            self._store_claims(now, results, ctx, source="G", arm=arm, window=window, run=run_id)
        except Stop as exc:
            verify_error = str(exc)
        stream, end = run["stream"], run["stream"]["end"] or {}
        fetched = find_key(end, "x_posts_fetched")
        cost, cost_note = grok_cost(run["stream"]["end"], fetched if isinstance(fetched, int) else counts.get("slots", 0))
        row = {**{k: v for k, v in run.items() if k != "stream"},
               "step": ctx["step"], "arm": arm, "block": block["id"], "window": window, **(extra or {}),
               "tool_calls": [{"name": t.get("name"), "input": t.get("input"), "observed_tool": t.get("observed_tool"),
                               "observed_args": t.get("observed_args"),
                               "raw_output_has_posts": bool(parse_slots(text_of(t.get("output"))))}
                              for t in stream["tools"]],
               "session_tools": stream["session_tools"], "project_skills_loaded": stream["project_skills_loaded"],
               "claims_from": claims_from, "partial": run["status"] != "ok",
               "usage": {"num_turns": end.get("num_turns"), "modelUsage": end.get("modelUsage"),
                         "models_seen": sorted((end.get("modelUsage") or {}).keys()), "usage": end.get("usage"),
                         "total_cost_usd": end.get("total_cost_usd"), "stopReason": end.get("stopReason"),
                         "x_posts_fetched": fetched, "x_users_fetched": find_key(end, "x_users_fetched")},
               "api_key_source": stream["api_key_source"], "errors": stream["errors"],
               "cost_usd": cost, "cost_note": cost_note, "counts": counts, "verify_error": verify_error,
               "claims": [{k: r.get(k) for k in ("slot", "id", "author", "created_at", "label", "in_window", "tool_index")}
                          | {"claimed_text": r.get("text"), "x_text": x_api.full_text(r["x"]) if r.get("x") else None}
                          for r in results],
               "unsourced_flag": bool(slots) and counts.get("confirmed", 0) == 0}
        self.store.append(self.store.grok_log, row)
        self.store.log_budget(self.clock(), "grok", run=run_id, step=ctx["step"], cost=f"{cost:.4f}", note=cost_note.split(" (")[0])
        status = run["status"] if run["status"] != "ok" else ("blocked-budget" if verify_error else "done")
        todo = ""
        if status == "blocked-grok-limit":
            todo = "Grok looks rate- or usage-limited; resume with `pilot next` once the limit resets"
        elif status == "blocked-grok-error":
            todo = f"Grok failed; read private/{run['saved']['stderr']['path']} before retrying"
        elif verify_error:
            todo = verify_error
        return {"status": status, "run": run_id, "claims_from": claims_from, "counts": counts,
                "tools": [t.get("observed_tool") or t.get("name") for t in stream["tools"]],
                "args": [t.get("observed_args") for t in stream["tools"]],
                "project_skills_loaded": stream["project_skills_loaded"], "cost_usd": cost, "todo": todo}

    def _arm(self, name, ctx, block, now):
        arm, effort = PILOT_ARMS[name]
        window = block["windows"]["demand"]
        prompt = arm_prompt(arm, IDEAS[PILOT_IDEA], window, WINDOW_HOURS["demand"])
        return self._grok_step({**ctx, "idea": PILOT_IDEA}, block, now, prompt, effort, ARM_VERIFY_CAP, window, arm)

    def _P7_free(self, ctx, block, now):
        return self._arm("P7-free", ctx, block, now)

    def _P7_steered(self, ctx, block, now):
        return self._arm("P7-steered", ctx, block, now)

    def _P7_hinted(self, ctx, block, now):
        return self._arm("P7-hinted", ctx, block, now)

    def _P7_self(self, ctx, block, now):
        return self._arm("P7-self", ctx, block, now)

    def _P7_free_low(self, ctx, block, now):
        return self._arm("P7-free-low", ctx, block, now)

    def _probe(self, name, ctx, block, now):
        prompt, meta = probe_prompt(name, now)
        if meta["from_date"]:
            start = datetime.fromisoformat(meta["from_date"]).replace(tzinfo=timezone.utc)
            end = datetime.fromisoformat(meta["to_date"]).replace(tzinfo=timezone.utc) + timedelta(days=1)
            window = {"start": iso(start), "end": iso(end)}   # the requested calendar days, read as UTC
        else:
            window = {"start": "2006-03-21T00:00:00Z", "end": iso(now + timedelta(minutes=1))}
        result = self._grok_step(ctx, block, now, prompt, "high", PROBE_VERIFY_CAP, window, f"probe:{meta['case']}",
                                 extra={"probe": meta}, verify_when_tool_output=False)
        rows = [r for r in self.store.rows(self.store.grok_log) if r.get("run_id") == result.get("run") and "saved" in r]
        stamps = []
        for claim in (rows[-1]["claims"] if rows else []):
            if claim.get("label", "").startswith("real") and (stamp := parse_stamp(claim.get("created_at"))):
                stamps.append(stamp)
        verified = self.store.load_posts()
        stamps += [parse_stamp(verified[c["id"]]["created_at"]) for c in (rows[-1]["claims"] if rows else [])
                   if c.get("id") in verified and verified[c["id"]]["created_at"] and c.get("label", "").startswith("real")]
        stamps = [x for x in stamps if x]
        result["probe"] = meta
        result["newest_verified"] = iso(max(stamps)) if stamps else None
        result["newest_age_h"] = round((now - max(stamps)).total_seconds() / 3600, 1) if stamps else None
        return result

    def _P8_a(self, ctx, block, now):
        return self._probe("P8-a", ctx, block, now)

    def _P8_b(self, ctx, block, now):
        return self._probe("P8-b", ctx, block, now)

    def _P8_c(self, ctx, block, now):
        return self._probe("P8-c", ctx, block, now)

    def _P8_d(self, ctx, block, now):
        return self._probe("P8-d", ctx, block, now)

    def _P8_e(self, ctx, block, now):
        return self._probe("P8-e", ctx, block, now)

    def _P8_f(self, ctx, block, now):
        return self._probe("P8-f", ctx, block, now)

    # --- stages (built now; run only after the pilot and the operator's yes) ---
    def run_stage(self, stage: int, idea_key: str, only: str | None = None) -> dict:
        idea = IDEAS.get(idea_key)
        if not idea or idea["job"] != STAGE_JOB[stage]:
            keys = [k for k, v in IDEAS.items() if v["job"] == STAGE_JOB[stage]]
            raise Stop(f"stage {stage} ideas are {', '.join(keys)}")
        data = self.store.progress()
        pinned = data["settings"].setdefault("frozen_hash", frozen_hash())
        if pinned != frozen_hash():
            raise Stop("IDEAS changed since the frozen hash was pinned; re-freeze deliberately (config --refreeze)")
        self.store.save_progress(data)
        now = self.clock()
        guard_clock(now)
        block = self.store.block(now)
        window = block["windows"][idea["job"]]
        # K per sort; the Tool research spam-control query is a separate paired ablation, not part of K
        # (Codex review, Medium 6), so K and G both stay at 2 queries / up to 20 posts.
        sources = [f"K-{s}" for s in K_SORTS[idea["job"]]] + ["G"] \
            + (["T"] if idea["job"] == "worth-joining" and idea["niche"] == "tech" else []) \
            + ([f"Kspam-{s}" for s in K_SORTS[idea["job"]]] if "spam" in idea else []) \
            + (["C"] if idea["job"] == "tool-research" else [])
        seed = int(hashlib.sha256(f"{idea_key}|{block['id']}".encode()).hexdigest()[:8], 16)
        random.Random(seed).shuffle(sources)
        if only:
            sources = [s for s in sources if s == only or s.split("-")[0] == only]
        name = f"S{stage}:{idea_key}"
        ctx = {"stage": f"stage{stage}", "step": name, "idea": idea_key, "block": block["id"]}
        out = {"order": sources, "seed": seed, "window": window}
        for source in sources:
            key = f"{name}:{source}:{block['id']}"
            if self.step_state(key)["status"] == "done":
                out[source] = "done already in this block"
                continue
            try:
                kind, _, sort = source.partition("-")
                handler = getattr(self, f"_stage_{kind}")
                args = ({**ctx, "step": key}, block, now, idea, window) + ((sort,) if sort else ())
                result = handler(*args)
            except Stop as exc:
                self.record(key, "pending", {"started": iso(now), "stopped": str(exc)}, todo=str(exc))
                raise
            status = result.pop("status", "done")
            self.record(key, status, {"started": iso(now), **result}, todo=result.get("todo", ""))
            out[source] = {"status": status, **result}
            if status.startswith("blocked"):
                break
        return out

    def _stage_K(self, ctx, block, now, idea, window, sort="recency"):
        return self._k_queries(ctx, now, idea["k"], window, sort, source=f"K-{sort}")

    def _stage_Kspam(self, ctx, block, now, idea, window, sort="recency"):
        """The spam-control variant, run over the same window as K, scored with the union and reported apart."""
        return self._k_queries(ctx, now, [idea["spam"]], window, sort, source=f"Kspam-{sort}")

    def _sent(self, key: str) -> list[dict]:
        return self.step_state(key).get("sent", [])

    def _log_sent(self, key: str, entry: dict) -> None:
        """Each query's call, saved as it happens, so a Stop mid-source doesn't lose which queries already returned."""
        data = self.store.progress()
        data["steps"].setdefault(key, {"status": "pending", "attempts": []}).setdefault("sent", []).append(entry)
        self.store.save_progress(data)

    def _k_queries(self, ctx, now, queries, window, sort, source):
        authors = bool(self.store.progress()["settings"].get("authors_on_checks"))
        key = ctx["step"]   # already per source and block: a re-run skips queries that returned 200 in this block
        calls, notes = [], []
        for n, query in enumerate(queries):
            variant = f"v{n + 1}"
            done = [s for s in self._sent(key) if s["variant"] == variant and s["query"] == query and s["http"] == 200]
            if done:
                calls.append({**done[-1], "reused": True})
                continue
            check_syntax(query, "api")
            sent = query
            row, body = self._search({**ctx, "source": source}, sent, window, authors=authors, sort=sort)
            if row["status"] == 400 and "min_replies:" in query:
                entry = {"variant": variant, "query": query, "sent_query": sent, "call": row["call_id"], "http": 400, "posts": 0}
                self._log_sent(key, entry)
                calls.append(entry)
                notes.append("min_replies rejected; reran without it")
                sent = " ".join(MIN_REPLIES.sub("", query).split())
                check_syntax(sent, "api")
                row, body = self._search({**ctx, "source": source}, sent, window, authors=authors, sort=sort)
            if row["status"] == 200:
                self._note_posts(now, row, body, ctx, source=source, window=window)
            entry = {"variant": variant, "query": query, "sent_query": sent, "call": row["call_id"],
                     "http": row["status"], "posts": row["items"]["data"]}
            self._log_sent(key, entry)
            calls.append(entry)
        return {"calls": calls, "sort": sort, "source": source, **({"notes": notes} if notes else {})}

    def _stage_G(self, ctx, block, now, idea, window):
        settings = self.store.progress()["settings"]
        arm = settings.get("best_arm")
        if not arm:
            raise Stop("no best Grok arm set: after the pilot, `harness.py config --best-arm <free|hinted|steered|self>`")
        prompt = arm_prompt(arm, idea, window, WINDOW_HOURS[idea["job"]])
        return self._grok_step(ctx, block, now, prompt, settings.get("best_effort", "high"), STAGE_VERIFY_CAP, window, arm)

    def _stage_T(self, ctx, block, now, idea, window):
        data = self.store.progress()
        cache = data.setdefault("t_reads", {})
        if block["id"] not in cache:
            params = {"max_results": "100", "tweet.fields": TWEET_FIELDS}
            row, body = self.client.get(f"/2/users/{x_api.USER_ID}/timelines/reverse_chronological", params,
                                        kind="posts", reserve=100 * POST, source="T", **{**ctx, "idea": None})
            data = self.store.progress()
            data.setdefault("t_reads", {})[block["id"]] = row["call_id"]
            self.store.save_progress(data)
        call = self.store.progress()["t_reads"][block["id"]]
        body = json.loads((self.store.root / "raw" / f"{call}.json").read_bytes() or b"{}")
        rules = [re.compile(r, re.I) for r in idea["t_rule"]]
        kept = [p for p in body.get("data") or []
                if all(r.search(x_api.full_text(p)) for r in rules) and in_window(p.get("created_at"), window)][:20]
        self._note_posts(now, {"call_id": call}, {"data": kept}, ctx, source="T", window=window)
        return {"shared_read": call, "read": len(body.get("data") or []), "kept": len(kept), "rule": idea["t_rule"]}

    def _stage_C(self, ctx, block, now, idea, window):
        start = max(parse_stamp(window["start"]), now - timedelta(days=6, hours=23))
        calls = []
        for query in idea["k"] + [idea["spam"]]:
            params = {"query": query, "granularity": "day", "start_time": iso(start), "end_time": window["end"]}
            row, body = self.client.get("/2/tweets/counts/recent", params, kind="counts", reserve=8 * POST, source="C", **ctx)
            calls.append({"query": query, "call": row["call_id"], "http": row["status"],
                          "total": (body.get("meta") or {}).get("total_tweet_count")})
        return {"calls": calls, "note": "how much talk; never ranked on useful posts"}

    def _seen(self, row: dict, sighting: dict | None, calls: dict) -> tuple[datetime, dict]:
        """(when, public_metrics) for one sighting: its call's time and that call's copy of the post.
        Falls back to the row's first_seen and stored metrics when the call isn't logged."""
        call = calls.get((sighting or {}).get("call") or "")
        if call:
            raw = self.store.root / (call.get("raw_path") or f"raw/{call['call_id']}.json")
            body = json.loads(raw.read_bytes() or b"{}") if raw.exists() else {}
            data = body.get("data")
            match = next((p for p in (data if isinstance(data, list) else [data] if data else []) if p.get("id") == row["post_id"]), None)
            return parse_stamp(call["time_utc"]), (match or {}).get("public_metrics") or json.loads(row["metrics"] or "{}")
        return parse_stamp(row["first_seen"]), json.loads(row["metrics"] or "{}")

    def reread(self, min_hours: float = 5.5, block: str | None = None) -> dict:
        """Re-read Worth-joining posts about 6 hours after they were found: did the conversation grow?
        With a block (given, or pinned), only posts with a stage1 sighting in it, timed from that sighting.
        Batches of 100; a post is gone only when its id was sent and the batch's answer lacks it."""
        now = self.clock()
        block = block or self.store.progress()["settings"].get("pinned_block")
        calls = self.store.call_rows()
        due = []
        for row in self.store.load_posts().values():
            sight = next((s for s in json.loads(row["sightings"])
                          if s.get("stage") == "stage1" and (block is None or s.get("block") == block)), None)
            if row["reread"] or not row["created_at"] or sight is None:
                continue
            seen_at, before = self._seen(row, sight, calls) if block else (parse_stamp(row["first_seen"]), json.loads(row["metrics"] or "{}"))
            if now - seen_at >= timedelta(hours=min_hours):
                due.append((row, seen_at, before))
        if not due:
            return {"due": 0, "block": block}
        ctx_block = self.store.block(now)["id"]
        updates, used, failed = [], [], []
        for n in range(0, len(due), 100):
            batch = due[n:n + 100]
            sent = [r["post_id"] for r, _, _ in batch if r["post_id"].isdigit()]
            found, _, call = lookup_ids(self.client, sent, authors=False,
                                        stage="reread", step="reread", source="reread", block=ctx_block)
            status = (self.client.last_row or {}).get("status")
            if status != 200:
                failed.append({"call": call, "http": status})
                continue
            used.append(call)
            for row, seen_at, before in batch:
                if row["post_id"] not in sent:
                    continue
                post = found.get(row["post_id"])
                entry = {"at": iso(now), "call": call, "block": block,
                         "hours_later": round((now - seen_at).total_seconds() / 3600, 1),
                         "before": before, "after": (post or {}).get("public_metrics"), "gone": post is None}
                updates.append({"post_id": row["post_id"], "reread": entry,
                                "sighting": {"source": "reread", "stage": "reread", "call": call}})
                self.store.append(self.store.root / "reread.jsonl", {"post_id": row["post_id"], **entry})
        self.store.upsert_posts(now, updates)
        out = {"due": len(due), "reread": len(updates), "gone": sum(1 for u in updates if u["reread"]["gone"]),
               "calls": used, "block": block}
        if failed:
            out["failed_calls"] = failed
        return out

    # --- blind scoring files: block-named when a block is given; nothing existing is ever overwritten ---
    @staticmethod
    def _suffix(stage, block: str | None) -> str:
        if block is not None and not BLOCK_ID.fullmatch(block):
            raise Stop(f"block ids look like B3, not {block!r}")
        return f"stage{stage}-{block}" if block else f"stage{stage}"

    def _fresh(self, *names: str) -> list[Path]:
        paths = [self.store.root / n for n in names]
        taken = [p.name for p in paths if p.exists()]
        if taken:
            raise Stop(f"refusing to overwrite {', '.join(taken)}; move it aside deliberately if it should be redone")
        return paths

    def _need(self, name: str) -> Path:
        path = self.store.root / name
        if not path.exists():
            raise Stop(f"{name} doesn't exist")
        return path

    def corpus(self, stage: int | str, block: str | None = None, batch: int | None = None) -> dict:
        """Blind scoring corpus: X's own text only, opaque ids, shuffled. Source, query, rank, time withheld.
        stage "pilot" takes the latest attempt of each P7 arm. Only eligible posts (English, not a retweet,
        inside the window) that exist on X go in. With a block, only that block's sightings of the stage.
        Stage 1 lines also carry the reply count and age (hours) when the post was found."""
        suffix = self._suffix(stage, block)
        if block and not any(b["id"] == block for b in self.store.progress()["blocks"]):
            raise Stop(f"no block {block} in progress.json")
        if batch and not block:
            raise Stop("--batch needs --block")
        table = self.store.load_posts()
        if stage == "pilot":
            runs = {self.step_state(s)["attempts"][-1].get("run") for s in PILOT_ARMS if self.step_state(s)["attempts"]}
            pick = lambda s: s.get("run") in runs and (block is None or s.get("block") == block)
        else:
            pick = lambda s: s.get("stage") == f"stage{stage}" and (block is None or s.get("block") == block)
        picked = []
        for row in table.values():
            sights = [s for s in json.loads(row["sightings"]) if pick(s)]
            labels = json.loads(row["labels"])
            ok = any(s.get("eligible", s.get("in_window", True)) not in (False, None) for s in sights)
            if sights and row["text"] and ok and any(l in ("x_api", "mentioned_exists") or l.startswith("real") for l in labels):
                picked.append((row, sights))
        parts = -(-len(picked) // batch) if batch else 0
        names = [f"corpus-{suffix}.jsonl", f"corpus-key-{suffix}.json", f"corpus-brief-{suffix}.md"]
        names += [f"corpus-{suffix}-part{k}.jsonl" for k in range(1, parts + 1)]
        names += [f"corpus-brief-{suffix}-part{k}.md" for k in range(1, parts + 1)]
        out, key_path, brief, *part_paths = self._fresh(*names)
        rng = random.Random(secrets.randbits(64))
        rng.shuffle(picked)
        calls = self.store.call_rows() if stage == 1 else {}
        corpus, key = [], {}
        for row, sights in picked:
            opaque = f"p{secrets.token_hex(4)}"
            sight = next((s for s in sights if s.get("idea") in IDEAS), None)
            idea = sight["idea"] if sight else None
            line = {"id": opaque, "idea": IDEAS[idea]["text"] if idea else None, "text": row["text"]}
            if stage == 1:
                seen_at, metrics = self._seen(row, sight, calls)
                created = parse_stamp(row["created_at"])
                line["replies"] = metrics.get("reply_count")
                line["age_hours"] = round((seen_at - created).total_seconds() / 3600, 1) if created else None
            corpus.append(line)
            key[opaque] = {"post_id": row["post_id"], "sha256": hashlib.sha256(row["text"].encode()).hexdigest(),
                           "conversation_id": row["conversation_id"] or None, "author_id": row["author_id"] or None,
                           "idea_key": idea}
        job = "demand" if stage == "pilot" else STAGE_JOB[stage]
        dump = lambda rows: "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in rows)
        self.store.write_atomic(out, dump(corpus))
        self.store.write_atomic(key_path, json.dumps(key, indent=1))
        self.store.write_atomic(brief, scoring_brief(job, f"research/discovery-test/private/{out.name}"))
        written = [p.name for p in (out, key_path, brief)]
        for k in range(parts):
            part, part_brief = part_paths[k], part_paths[parts + k]
            self.store.write_atomic(part, dump(corpus[k * batch:(k + 1) * batch]))
            self.store.write_atomic(part_brief, scoring_brief(job, f"research/discovery-test/private/{part.name}"))
            written += [part.name, part_brief.name]
        return {"posts": len(corpus), "file": out.name, "brief": brief.name, "parts": parts, "written": written}

    @staticmethod
    def _fail_closed(problems: list[str], what: str) -> None:
        bad = [p for p in problems if p.startswith(("rejected", "duplicate", "missing"))]
        if bad:
            raise Stop(f"{what}: wrote nothing; {len(bad)} problem(s): " + "; ".join(bad[:10]))

    def ingest_scores(self, stage, paths, seed: int | None = None, block: str | None = None, second: str = "rule") -> dict:
        """Check Codex's scores against the corpus, then draw the second scorer's list. Fail-closed: nothing is
        written unless every corpus id is scored exactly once and no row was rejected. Several files are merged."""
        suffix = self._suffix(stage, block)
        paths = [paths] if isinstance(paths, (str, Path)) else list(paths)
        corpus = {c["id"]: c for c in self.store.rows(self._need(f"corpus-{suffix}.jsonl"))}
        out, second_path, mode_path = self._fresh(f"scores-{suffix}.jsonl", f"second-{suffix}.jsonl",
                                                  f"second-mode-{suffix}.json")
        rows = [r for p in paths for r in self.store.rows(Path(p))]
        scores, problems = check_scores(corpus, rows)
        self._fail_closed(problems, "ingest-scores")
        rng = random.Random(seed if seed is not None else secrets.randbits(32))
        if second == "all":
            must = sorted(r["id"] for r in scores)
            sample = list(must)
        else:
            # Second scorer (Codex review, High 4): every positive and every unclear post, plus 20% of the rest.
            must = sorted(r["id"] for r in scores if (r["relevant"] == 2 and r["real"] == 2) or 1 in (r["relevant"], r["real"]))
            rest = sorted(r["id"] for r in scores if r["id"] not in must)
            sample = must + (rng.sample(rest, max(1, round(len(rest) * 0.2))) if rest else [])
        rng.shuffle(sample)
        self.store.write_atomic(out, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in scores))
        self.store.write_atomic(second_path, "".join(json.dumps({"id": i, "idea": corpus[i].get("idea"), "text": corpus[i]["text"]},
                                                                ensure_ascii=False) + "\n" for i in sample))
        self.store.write_atomic(mode_path, json.dumps({"mode": second, "ids": len(sample), "of": len(corpus),
                                                       "inputs": [str(p) for p in paths]}, indent=1) + "\n")
        return {"scored": len(scores), "of": len(corpus), "problems": problems, "second_mode": second,
                "second_score": {"positives_and_unclear" if second == "rule" else "all": len(must),
                                 "random_rest": len(sample) - len(must)},
                "files": [out.name, second_path.name, mode_path.name]}

    def second_mode(self, stage, block: str | None = None) -> str:
        path = self.store.root / f"second-mode-{self._suffix(stage, block)}.json"
        return json.loads(path.read_text(encoding="utf-8"))["mode"] if path.exists() else "rule"

    def second_scores(self, stage, path: Path, block: str | None = None) -> dict:
        """Compare the second scorer with the first: agreement and confusion per axis; list disagreements.
        Fail-closed: every id on the second list scored exactly once, no row rejected."""
        suffix = self._suffix(stage, block)
        corpus = {c["id"]: c for c in self.store.rows(self._need(f"corpus-{suffix}.jsonl"))}
        first = {r["id"]: r for r in self.store.rows(self._need(f"scores-{suffix}.jsonl"))}
        wanted = {r["id"] for r in self.store.rows(self._need(f"second-{suffix}.jsonl"))}
        out, dis_path = self._fresh(f"second-scores-{suffix}.jsonl", f"disagreements-{suffix}.jsonl")
        second, problems = check_scores({i: corpus[i] for i in wanted}, self.store.rows(path))
        self._fail_closed(problems, "second-scores")
        report, disagree = {}, []
        for axis in ("relevant", "real", "useful", "type"):
            pairs = [(first[r["id"]].get(axis), r.get(axis)) for r in second if axis in r]
            matrix: dict[str, int] = {}
            for a, b in pairs:
                matrix[f"{a}->{b}"] = matrix.get(f"{a}->{b}", 0) + 1
            report[axis] = {"agree": sum(1 for a, b in pairs if a == b), "of": len(pairs), "first->second": matrix}
        for r in second:
            f = first[r["id"]]
            diff = {k: [f.get(k), r.get(k)] for k in ("relevant", "real", "useful", "type") if k in r and f.get(k) != r.get(k)}
            if diff:
                disagree.append({"id": r["id"], "text": corpus[r["id"]]["text"], "diff": diff})
        self.store.write_atomic(out, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in second))
        self.store.write_atomic(dis_path, "".join(json.dumps(d, ensure_ascii=False) + "\n" for d in disagree))
        return {"second_scored": len(second), "problems": problems, "agreement": report, "disagreements": len(disagree),
                "files": [out.name, dis_path.name]}

    def finalise_scores(self, stage, adjudicated: Path | None = None, block: str | None = None) -> dict:
        """Final labels: first and second agree, or an adjudication settles it. Refuses while any stays open,
        and under second mode "all" while any post lacks a second score."""
        suffix = self._suffix(stage, block)
        first = {r["id"]: r for r in self.store.rows(self._need(f"scores-{suffix}.jsonl"))}
        second = {r["id"]: r for r in self.store.rows(self.store.root / f"second-scores-{suffix}.jsonl")}
        (out,) = self._fresh(f"final-scores-{suffix}.jsonl")
        if self.second_mode(stage, block) == "all":
            lacking = sorted(set(first) - set(second))
            if lacking:
                raise Stop(f"second mode is all: {len(lacking)} posts have no second score: {', '.join(lacking[:10])}")
        settled = {r["id"]: r for r in self.store.rows(adjudicated)} if adjudicated else {}
        final, open_ids = [], []
        for pid, f in first.items():
            s2 = second.get(pid)
            if s2 is None or all(f.get(k) == s2.get(k) for k in ("relevant", "real", "useful", "type") if k in s2):
                final.append({**f, "source_of_label": "agreed" if s2 else "first only"})
            elif pid in settled:
                final.append({**f, **{k: settled[pid][k] for k in ("relevant", "real", "useful", "type") if k in settled[pid]},
                              "source_of_label": "adjudicated", "adjudication_note": settled[pid].get("why")})
            else:
                open_ids.append(pid)
        if open_ids:
            raise Stop(f"{len(open_ids)} disagreements still need adjudication: {', '.join(open_ids[:10])}")
        self.store.write_atomic(out, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in final))
        return {"final": len(final), "adjudicated": sum(1 for r in final if r["source_of_label"] == "adjudicated"),
                "file": out.name}

    def manifest(self, block: str) -> dict:
        """private/manifest-<block>.csv: one row per sighting in the block, with where it came from.
        Derived from the logs only, so it is rewritten on each run."""
        self._suffix(1, block)
        calls = self.store.call_rows()
        variants = {}
        for key, idea in IDEAS.items():
            for n, q in enumerate(idea["k"]):
                variants[(key, q)] = f"v{n + 1}"
                variants.setdefault((key, " ".join(MIN_REPLIES.sub("", q).split())), f"v{n + 1}-no-min_replies")
            if "spam" in idea:
                variants[(key, idea["spam"])] = "spam"
        cols = ("post_id", "stage", "idea", "source", "sort", "variant", "rank", "call", "result_count", "eligible")
        rows = []
        for post in self.store.load_posts().values():
            for s in json.loads(post["sightings"]):
                if s.get("block") != block:
                    continue
                call = calls.get(s.get("call") or "") or {}
                params = call.get("params") or {}
                source = s.get("source") or ""
                sort = params.get("sort_order") or (source.partition("-")[2] if source.startswith("K") else "")
                variant = variants.get((s.get("idea"), params.get("query")), "") if params.get("query") else ""
                rows.append({"post_id": post["post_id"], "stage": s.get("stage"), "idea": s.get("idea"), "source": source,
                             "sort": sort, "variant": variant, "rank": s.get("rank"), "call": s.get("call"),
                             "result_count": call.get("result_count"), "eligible": s.get("eligible")})
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=cols)
        writer.writeheader()
        writer.writerows(rows)
        path = self.store.root / f"manifest-{block}.csv"
        self.store.write_atomic(path, buf.getvalue())
        return {"rows": len(rows), "file": path.name}

    def recheck(self, hours: float = 24) -> dict:
        """Is each collected post still on X a day later? Recorded as its own signal ('gone', reason unknown),
        never as a spam label (Codex review, High 5)."""
        now = self.clock()
        done = {r["post_id"] for r in self.store.rows(self.store.root / "recheck.jsonl")}
        due = [row for row in self.store.load_posts().values() if row["post_id"] not in done and row["created_at"]
               and now - parse_stamp(row["first_seen"]) >= timedelta(hours=hours)]
        if not due:
            return {"due": 0}
        results = []
        for n in range(0, len(due), 100):
            batch = due[n:n + 100]
            found, errors, call = lookup_ids(self.client, [r["post_id"] for r in batch], authors=False,
                                             stage="recheck", step="recheck", source="recheck", block=self.store.block(now)["id"])
            for row in batch:
                entry = {"post_id": row["post_id"], "at": iso(now), "call": call,
                         "hours_later": round((now - parse_stamp(row["first_seen"])).total_seconds() / 3600, 1),
                         "gone": row["post_id"] not in found, "x_error": errors.get(row["post_id"])}
                self.store.append(self.store.root / "recheck.jsonl", entry)
                results.append(entry)
        return {"due": len(due), "gone": sum(1 for r in results if r["gone"])}

    def reprocess(self, run_id: str) -> dict:
        """Re-read a saved Grok stdout and check ids the first pass missed. Appends a row; never re-runs Grok."""
        rows = [r for r in self.store.rows(self.store.grok_log) if r["run_id"] == run_id and "saved" in r]
        if not rows:
            raise Stop(f"no Grok run {run_id}")
        row = rows[-1]
        stdout = (self.store.root / row["saved"]["stdout"]["path"]).read_text(encoding="utf-8")
        if hashlib.sha256(stdout.encode()).hexdigest() != row["saved"]["stdout"]["sha256"]:
            raise Stop(f"{run_id} stdout no longer matches its hash")
        slots, claims_from = run_claims({"stream": parse_stream(stdout)})
        checked = {c["id"] for c in row.get("claims", []) if c.get("label") not in (None, "unchecked", "empty_slot")}
        new = [s for s in slots if s["id"] and s["id"] not in checked]
        now = self.clock()
        ctx = {"stage": "pilot" if row["step"].startswith("P") else "stage", "step": row["step"],
               "block": row["block"], "idea": PILOT_IDEA if row["step"].startswith("P7") else None}
        settings = self.store.progress()["settings"]
        results, counts = check_claims(self.client, new, row["window"], cap=40,
                                       authors=bool(settings.get("authors_on_checks")), claims_from=claims_from,
                                       **{"source": "G", **ctx})
        self._store_claims(now, results, ctx, source="G", arm=row.get("arm"))
        entry = {"run_id": run_id, "reprocessed_at": iso(now), "step": row["step"], "arm": row.get("arm"),
                 "reprocess_of_sha256": row["saved"]["stdout"]["sha256"], "cost_usd": 0.0, "counts": counts,
                 "claims": [{k: r.get(k) for k in ("id", "label", "in_window", "mentioned_only")} for r in results]}
        self.store.append(self.store.grok_log, entry)
        return {"run": run_id, "new_ids": len(new), "counts": counts}

    # --- status ---
    def status(self) -> str:
        data = self.store.progress()
        lines = [f"X API spent (estimate): ${self.store.x_spent():.4f} total, ${self.store.x_spent('pilot'):.4f} pilot "
                 f"(pilot ceiling ${PILOT_CEILING:.2f}, checkpoint ${X_CHECKPOINT:.2f})",
                 f"Grok spent: ${self.store.grok_spent():.4f} (checkpoint ${GROK_CHECKPOINT:.2f})",
                 f"Settings: {json.dumps(data['settings'])}", "Pilot steps:"]
        for name in PILOT_ORDER:
            step = self.step_state(name)
            todo = f"  ({step.get('todo')})" if step.get("todo") else ""
            lines.append(f"  {name:12} {step['status']:20} attempts={len(step['attempts'])}{todo}")
        others = [k for k in data["steps"] if k not in PILOT_ORDER]
        if others:
            lines.append("Stage steps:")
            lines += [f"  {k:40} {data['steps'][k]['status']}" for k in others]
        arm_blocks = {self.step_state(s)["attempts"][-1]["block"] for s in PILOT_ARMS
                      if self.step_state(s)["status"] == "done" and self.step_state(s)["attempts"]}
        if len(arm_blocks) > 1:
            lines.append(f"Arms ran in different blocks {sorted(arm_blocks)}: re-run P7-free with --redo in the latest block as a bridge.")
        nxt = self.next_step()
        lines.append(f"Next: python3 research/discovery-test/harness.py pilot {nxt}" if nxt else "Pilot complete.")
        return "\n".join(lines)


def pad_query(base: str, length: int) -> str:
    """base plus exclusions of nonsense words, so results match base while the query reaches `length`."""
    parts, n = [base], 0
    while len(" ".join(parts)) < length:
        parts.append(f"-zqxj{n:04d}")
        n += 1
    query = " ".join(parts)
    while len(query) > length:   # trim the last exclusion to land exactly on length
        head, _, last = query.rpartition(" ")
        need = length - len(head) - 1
        query = head if need < 3 else f"{head} {last[:need]}"
    return query if len(query) == length else query + "z" * (length - len(query))


USEFUL = {"demand": "a genuine need or a live reaction someone could usefully answer",
          "worth-joining": "a live conversation a specific or witty reply would add to",
          "tool-research": "actually about the product (how people use, like or dislike it)"}


def scoring_brief(job: str, corpus_path: str) -> str:
    """plan.md §Scoring, as a Codex brief. Blind: text and opaque ids only; each line echoes its opening words."""
    brief = f"""<task>Score every post in {corpus_path} and return one JSON line per post. Done when every id in the file has exactly one line.</task>
<context>
Each line of the file is {{"id", "idea", "text"}}: an X post's text exactly as X returned it, and the idea it was searched for. Read only that file.
Score each post 0-2 on three axes, against its idea:
- relevant: 2 = the post itself is squarely the idea (for demand: its author has the need or the reaction, not someone answering another person's need); 1 = related, including replies that answer the idea; 0 = unrelated.
- real: 2 = a real person in their own voice; 1 = unclear; 0 = spam, promotion, bot, giveaway, farm or product marketing.
- useful for the job: 2 = {USEFUL[job]}; 1 = marginal; 0 = not.
Plus act: true if you would act on this post for the job, else false.
Plus type, exactly one of: genuine, account-selling, promotion, engagement-bait, product-marketing, off-topic, other. Off-topic means a real person on a different subject; the others are kinds of spam or promotion.
For comedy or satire ideas, "useful" judges whether it is a live conversation a witty reply could join, not whether it is funny.
</context>
<constraints>Read-only. Judge from the text alone. Do not search the web or look the posts up.</constraints>
Output: only JSON lines, {{"id": "...", "opening": "<the first 30 characters of the post text, copied exactly>", "relevant": n, "real": n, "useful": n, "act": true|false, "type": "...", "why": "<=12 words"}}, nothing else.
<default_follow_through_policy/>
"""
    if job == "worth-joining":   # Stage 1 lines carry the reply count and age at the time the post was found
        brief = brief.replace('Each line of the file is {"id", "idea", "text"}',
                              'Each line of the file is {"id", "idea", "text", "replies", "age_hours"}')
        brief = brief.replace("Judge from the text alone.",
                              "Judge from the text plus the replies and age_hours fields (the post's reply count and its age "
                              "in hours when it was found).")
    return brief


def _opening(text: str) -> str:
    return " ".join((text or "").split())[:30].casefold()


def check_scores(corpus: dict, rows: list[dict]) -> tuple[list[dict], list[str]]:
    """Each score must name a corpus id once and echo that post's opening. A wrong id whose opening matches
    exactly one post is corrected and flagged (26 Sep: Codex returned p61864f for p61864d)."""
    by_opening: dict[str, list[str]] = {}
    for cid, c in corpus.items():
        by_opening.setdefault(_opening(c["text"]), []).append(cid)
    kept, problems, seen = [], [], set()
    for row in rows:
        cid, opening = row.get("id"), _opening(row.get("opening", ""))
        matches = [i for key, ids in by_opening.items() if opening and (key.startswith(opening[:20]) or opening.startswith(key[:20])) for i in ids]
        if cid in corpus and (not opening or _opening(corpus[cid]["text"]).startswith(opening[:20]) or opening.startswith(_opening(corpus[cid]["text"])[:20])):
            pass
        elif len(matches) == 1:
            problems.append(f"id {cid} corrected to {matches[0]} by its opening words")
            row = {**row, "id": matches[0], "corrected_from": cid}
            cid = matches[0]
        else:
            problems.append(f"rejected {cid}: id and opening words don't identify one post")
            continue
        if cid in seen:
            problems.append(f"duplicate score for {cid}; kept the first")
            continue
        if not all(row.get(k) in (0, 1, 2) for k in ("relevant", "real", "useful")):
            problems.append(f"rejected {cid}: scores must be 0, 1 or 2")
            continue
        seen.add(cid)
        if "type" in row and row["type"] not in SPAM_TYPES:
            problems.append(f"{cid}: unknown type {row['type']!r}, kept as other")
            row = {**row, "type": "other"}
        kept.append({k: row.get(k) for k in ("id", "relevant", "real", "useful", "act", "type", "why", "corrected_from") if k in row})
    problems += [f"missing score for {cid}" for cid in corpus if cid not in seen]
    return kept, problems


# ---------- seeds ----------

PRIVATE_README = """# private/ (gitignored)

Raw data from the Discovery test. Other people's posts: never commit, never share outside this Mac
(except the blind scoring corpus sent to Codex, operator decision 4). **Delete by 26 Mar 2027.**

- requests.jsonl: one row per X API HTTP call (status, headers, params, items, estimated cost)
- raw/: every X API response body, by call id
- grok.jsonl: one row per Grok run (prompt, flags, model, cwd, tool calls, usage, claims and their check)
- grok/: each Grok run's stdout and stderr, untouched (hashes in grok.jsonl)
- grok-cwd/: the empty folders Grok ran in
- posts.csv: one row per unique post, every sighting, labels, X's fields at fetch
- budget.log: running spend and every refusal; the operator's console readings
- progress.json: step ledger (done, blocked and why, pending), settings, time blocks
- facts.md: F1–F11 and G1–G6 with the calls that answered them
- stage-N.md: review note after each stage; corpus-*.jsonl / corpus-key-*.json: blind scoring input and its key
"""

FACTS_SEED = """# Facts (F1–F11, G1–G6)

Each: hypothesis · calls that test it · answer. Answers are written after reviewing the calls.
Per-step X costs are estimates from item counts; only the pilot total is measured (console before/after,
operator decision 26 Sep).

| # | Hypothesis | Calls | Answer |
|---|---|---|---|
| F1 | Search bills per post returned ($0.005) | P1 | |
| F2 | Author expansions bill as user reads ($0.010) | P2 | |
| F3 | Same-UTC-day repeats are free | P1, P1b, P2, P5 | |
| F4 | Counts endpoint works on pay-per-use; its price | P3 | |
| F5 | Following timeline works with OAuth 1.0a keys; owned ($0.001) or standard | P4 | |
| F6 | Real query length limit (512 / 1,024 / 4,096); rejected requests bill? | P5 | |
| F7 | `min_likes:`, `min_replies:`, `-is:reply` accepted on this tier | P1, P3 | |
| F8 | `sort_order` recency vs relevancy: what relevancy favours | P1, P1b | |
| F9 | Age of the newest post found | P1 | |
| F10 | Rate-limit headers and remaining quota per endpoint | all | |
| F11 | A usage endpoint reports billed items | P0 | |
| G1 | What the CLI stream contains (tool calls, raw tool output, counts, citations, tokens, cost) | P7, P8 | |
| G2 | Which search functions Grok chooses given an idea in plain words | P7-free, P7-hinted | |
| G3 | Invented and misquoted rates | P7, P9 | |
| G4 | Posts fetched vs shown | P7 | |
| G5 | Cost per prompt | P7, P8 | |
| G6 | xAI prompting guidance and CLI options | docs | No xAI prompting guidance for X search exists (docs-grok-prompting.md §1, community-grok-prompting.md). CLI 1.0.41 flags used: -m, --effort, --max-turns, --verbatim, --output-format streaming-json, --sandbox read-only; memory off with GROK_MEMORY=0. `--json-schema` forces plain json, so it isn't used. |
"""


# ---------- cli ----------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Discovery test harness")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sp = sub.add_parser("pilot")
    sp.add_argument("step", nargs="?", default="next")
    sp.add_argument("--redo", action="store_true")
    sp.add_argument("--dry-run", action="store_true")
    sp = sub.add_parser("config")
    sp.add_argument("--model")
    sp.add_argument("--authors", choices=("on", "off"))
    sp.add_argument("--best-arm", choices=("free", "hinted", "steered", "self"))
    sp.add_argument("--best-effort", choices=("low", "medium", "high"))
    sp.add_argument("--refreeze", action="store_true")
    sp.add_argument("--new-block", action="store_true", help="start a fresh time block, with windows ending now")
    sp.add_argument("--pin-block", help="reuse this block (its windows) whatever the gap; 'none' clears the pin")
    sp = sub.add_parser("console")
    group = sp.add_mutually_exclusive_group(required=True)
    group.add_argument("--before", type=float)
    group.add_argument("--after", type=float)
    for n in (1, 2, 3):
        sp = sub.add_parser(f"stage{n}")
        sp.add_argument("--idea", required=True)
        sp.add_argument("--source", help="K, G, T, C or Kspam (all sorts), or one of K-recency, K-relevancy, Kspam-recency…")
    sp = sub.add_parser("reread")
    sp.add_argument("--block", help="only posts with a stage1 sighting in this block (default: the pinned block)")
    sp = sub.add_parser("reprocess")
    sp.add_argument("run_ids", nargs="+")
    sp = sub.add_parser("corpus")
    sp.add_argument("--stage", required=True, choices=("1", "2", "3", "pilot"))
    sp.add_argument("--block")
    sp.add_argument("--batch", type=int, help="also write part files of this many posts (needs --block)")
    sp = sub.add_parser("second-scores")
    sp.add_argument("--stage", required=True, choices=("1", "2", "3", "pilot"))
    sp.add_argument("--block")
    sp.add_argument("file")
    sp = sub.add_parser("finalise-scores")
    sp.add_argument("--stage", required=True, choices=("1", "2", "3", "pilot"))
    sp.add_argument("--block")
    sp.add_argument("--adjudicated")
    sp = sub.add_parser("manifest")
    sp.add_argument("--block", required=True)
    sp = sub.add_parser("recheck")
    sp.add_argument("--hours", type=float, default=24)
    sp = sub.add_parser("ingest-scores")
    sp.add_argument("--stage", required=True, choices=("1", "2", "3", "pilot"))
    sp.add_argument("--block")
    sp.add_argument("--second", choices=("rule", "all"), default="rule",
                    help="rule: positives, unclear and 20%% of the rest; all: every post")
    sp.add_argument("files", nargs="+")
    return parser


def dry_run() -> str:
    worst = worst_case()
    lines = ["Pilot, worst case (no network):", f"{'step':12} {'X API':>8}  call"]
    for step in PILOT_ORDER:
        lines.append(f"{step:12} ${worst['steps'][step]:>7.3f}  {DESCRIBE[step]}")
    lines += [f"{'X API total':12} ${worst['x_total']:>7.3f}  (hard stop ${PILOT_CEILING:.2f}; P9 = {worst['p9_ids']} ids)",
              f"{'Grok':12} ${worst['grok_total']:>7.2f}  ({worst['grok_runs']} runs × ${GROK_RESERVE:.2f} reserve; checkpoint ${GROK_CHECKPOINT:.2f})"]
    return "\n".join(lines)


def main(argv: list[str] | None = None, harness: Harness | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "pilot" and args.dry_run:
        print(dry_run())
        return 0
    if harness is None:
        store = Store()
        harness = Harness(store, LoggedClient(store), GrokRunner(store))
    store = harness.store
    try:
        if args.command == "status":
            print(harness.status())
        elif args.command == "config":
            data = store.progress()
            for key, value in (("model", args.model), ("best_arm", args.best_arm), ("best_effort", args.best_effort)):
                if value:
                    data["settings"][key] = value
            if args.authors:
                data["settings"]["authors_on_checks"] = args.authors == "on"
            if args.refreeze:
                data["settings"]["frozen_hash"] = frozen_hash()
            store.save_progress(data)
            if args.pin_block:
                store.pin_block(args.pin_block)
                data = store.progress()
            if args.new_block:
                block = store.block(harness.clock(), new=True)
                print(json.dumps({"new_block": block["id"], "windows": block["windows"]}, indent=1))
                data = store.progress()
            print(json.dumps(data["settings"], indent=1))
        elif args.command == "console":
            label = "before" if args.before is not None else "after"
            store.log_budget(harness.clock(), "console", **{label: args.before if args.before is not None else args.after})
            print(f"logged console {label}")
        elif args.command == "pilot":
            steps = [harness.next_step()] if args.step == "next" else (
                [s for s in PILOT_ORDER if harness.step_state(s)["status"] != "done"] if args.step == "all" else [args.step])
            for step in steps:
                if step is None:
                    print("Pilot complete.")
                    break
                result = harness.run_pilot_step(step, redo=args.redo)
                print(json.dumps(result, indent=1, ensure_ascii=False, default=str))
                if result["status"] != "done":
                    break
        elif args.command.startswith("stage"):
            print(json.dumps(harness.run_stage(int(args.command[-1]), args.idea, args.source), indent=1, default=str))
        elif args.command == "reprocess":
            for run_id in args.run_ids:
                print(json.dumps(harness.reprocess(run_id), indent=1))
        elif args.command == "reread":
            print(json.dumps(harness.reread(block=args.block), indent=1))
        elif args.command in ("second-scores", "finalise-scores"):
            stage = int(args.stage) if args.stage.isdigit() else args.stage
            out = harness.second_scores(stage, Path(args.file), block=args.block) if args.command == "second-scores" \
                else harness.finalise_scores(stage, Path(args.adjudicated) if args.adjudicated else None, block=args.block)
            print(json.dumps(out, indent=1))
        elif args.command == "manifest":
            print(json.dumps(harness.manifest(args.block), indent=1))
        elif args.command == "recheck":
            print(json.dumps(harness.recheck(args.hours), indent=1))
        elif args.command == "ingest-scores":
            stage = int(args.stage) if args.stage.isdigit() else args.stage
            print(json.dumps(harness.ingest_scores(stage, [Path(f) for f in args.files], block=args.block,
                                                   second=args.second), indent=1))
        elif args.command == "corpus":
            stage = int(args.stage) if args.stage.isdigit() else args.stage
            print(json.dumps(harness.corpus(stage, block=args.block, batch=args.batch), indent=1))
    except Stop as exc:
        print(f"STOPPED: {exc}", file=sys.stderr)
        return 2
    except x_api.XApiError as exc:
        print(f"X API error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
