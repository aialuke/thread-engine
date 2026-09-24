#!/usr/bin/env python3
"""Deterministic state for the learning loop. Grok calls this; the operator never does.

Every command prints JSON on stdout. Errors print {"error": ...} on stderr and exit 1.
Each command writes at most one data file, atomically, then re-renders the
readable views (experiments.md, learnings.md, ledger/SUMMARY.md).

No network access. Git is used only by commit-rule, undo and commit-data.

X API data (from snapshot.py) lands in three places:
- ledger/activity/YYYY-MM.json: one row per post, reply and quote, with its reads.
- ledger/activity/account.json: daily follower counts and follow credit.
- loop/followers/: follower ids and who interacted with the account. Other
  people's data: gitignored, never committed, never rendered.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_ROOT = Path(__file__).resolve().parent.parent
LOCAL_TZ = ZoneInfo("Australia/Brisbane")

SNAPSHOT_MIN_H = 36.0
SNAPSHOT_MAX_H = 60.0
EXPLORE_ALTERNATE_DAYS = 28
REVIEW_EVERY_DAYS = 7
STALE_AFTER_DAYS = 42
LANE_WINDOW = 15
MIN_COHORT = 3
FINAL_MIN_DAYS = 26
FOLLOWER_FILES_KEPT = 2
INTERACTION_DAYS = 7
CONVERSATION_DAYS = 30

FORMATS = {"settings", "comparison", "tool-swap", "single-tip", "build-log", "tool-verdict", "other"}
ARMS = {"treatment", "control", "none"}
EDIT_CLASSES = {"preference", "correction", "deviation", "violation"}
METRICS = ("views", "likes", "reposts", "quotes", "replies", "bookmarks")
# Stored, but never an experiment's primary: they cannot tell a better post from a worse one.
UNSCORABLE = {
    "views": "views include paid (boosted) reach and say nothing about follows",
    "replies": "a root's replies count the account's own thread cards",
}
OPEN_STATES = {"testing", "promising", "unclear"}
ITEM_KINDS = {"original", "quote", "reply", "thread_card", "repost"}
READ_STAGES = {"backfill", "48h", "final"}
PUBLIC_KEYS = ("impressions", "likes", "replies", "reposts", "quotes", "bookmarks")
ORGANIC_KEYS = ("impressions", "likes", "replies", "reposts", "profile_visits", "url_clicks")
POST_ID_RE = re.compile(r"^[0-9]{5,25}$")
LESSON_RE = re.compile(r"^L-[0-9]{3}$")


class LoopError(Exception):
    pass


# ---------- time and io ----------


def parse_time(value: str) -> datetime:
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LoopError(f"bad time {value!r}; use ISO 8601 with a timezone") from exc
    if stamp.tzinfo is None:
        raise LoopError(f"time {value!r} has no timezone")
    return stamp.astimezone(timezone.utc)


def iso(stamp: datetime) -> str:
    return stamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def local(stamp_iso: str) -> str:
    return parse_time(stamp_iso).astimezone(LOCAL_TZ).strftime("%a %d %b %H:%M")


def now_arg(value: str | None) -> datetime:
    return parse_time(value) if value else datetime.now(timezone.utc)


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def write_json(path: Path, data: dict) -> None:
    atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LoopError(f"missing {path}") from exc
    except json.JSONDecodeError as exc:
        raise LoopError(f"{path} is not valid JSON: {exc}") from exc


# ---------- repository ----------


class Repo:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.state_path = root / "loop" / "state.json"
        self.ledger_dir = root / "ledger"

    # state

    def state(self) -> dict:
        if not self.state_path.is_file():
            raise LoopError("loop not initialised; run init")
        return read_json(self.state_path)

    def save_state(self, state: dict) -> None:
        write_json(self.state_path, state)

    # ledger

    def post_path(self, root_id: str) -> Path:
        if not POST_ID_RE.fullmatch(root_id):
            raise LoopError(f"bad post id {root_id!r}")
        return self.ledger_dir / f"{root_id}.json"

    def posts(self) -> list[dict]:
        if not self.ledger_dir.is_dir():
            return []
        found = [read_json(p) for p in sorted(self.ledger_dir.glob("*.json"))]
        return sorted(found, key=lambda p: p["posted_at"])

    def post(self, root_id: str) -> dict:
        return read_json(self.post_path(root_id))

    def save_post(self, post: dict) -> None:
        write_json(self.post_path(post["root_id"]), post)

    # X API data

    @property
    def activity_dir(self) -> Path:
        return self.ledger_dir / "activity"

    @property
    def account_path(self) -> Path:
        return self.activity_dir / "account.json"

    @property
    def private_dir(self) -> Path:
        return self.root / "loop" / "followers"

    def activity(self) -> dict[str, dict]:
        rows: dict[str, dict] = {}
        if self.activity_dir.is_dir():
            for path in sorted(self.activity_dir.glob("????-??.json")):
                rows.update(read_json(path)["items"])
        return rows

    def account(self) -> dict:
        return read_json(self.account_path) if self.account_path.is_file() else {"days": []}

    def interactions(self) -> dict:
        path = self.private_dir / "interactions.json"
        return read_json(path) if path.is_file() else {"mentions_since_id": None, "people": {}, "conversations": {}}

    def git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=self.root, capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            raise LoopError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
        return result.stdout


# ---------- validation ----------


def need(cond: bool, message: str) -> None:
    if not cond:
        raise LoopError(message)


def check_count(value, field: str) -> None:
    need(value is None or (isinstance(value, int) and not isinstance(value, bool) and value >= 0),
         f"{field} must be a non-negative integer or null")


def validate_post(post: dict) -> None:
    need(POST_ID_RE.fullmatch(str(post.get("root_id", ""))) is not None, "root_id missing or bad")
    need(isinstance(post.get("slug"), str) and post["slug"], "slug required")
    need(post.get("format") in FORMATS, f"format must be one of {sorted(FORMATS)}")
    need(post.get("lane") in {"main", "other"}, "lane must be main or other")
    parse_time(post.get("posted_at", ""))
    need(isinstance(post.get("retrospective"), bool), "retrospective must be true or false")
    need(isinstance(post.get("made_in_repo"), bool), "made_in_repo must be true or false")
    need(post.get("arm", "none") in ARMS, f"arm must be one of {sorted(ARMS)}")
    need(isinstance(post.get("cards", []), list), "cards must be a list")
    for card in post.get("cards", []):
        need(POST_ID_RE.fullmatch(str(card.get("id", ""))) is not None, "card id bad")
        need(isinstance(card.get("text", ""), str), "card text must be text")
    for edit in post.get("edits", []):
        need(edit.get("class") in EDIT_CLASSES, f"edit class must be one of {sorted(EDIT_CLASSES)}")
    check_count(post.get("production_minutes"), "production_minutes")
    mark = post.get("nonorganic")
    need(mark is None or (isinstance(mark, dict) and isinstance(mark.get("reason"), str)),
         "nonorganic must be null or {reason, at}")
    for snap in post.get("snapshots", []):
        validate_snapshot(snap)


def validate_snapshot(snap: dict) -> None:
    parse_time(snap.get("observed_at", ""))
    need(snap.get("kind") in {"valid", "late", "early", "final"}, "snapshot kind bad")
    for metric in METRICS:
        check_count(snap.get("root", {}).get(metric), f"root.{metric}")
    for key, value in (snap.get("organic") or {}).items():
        need(key in ORGANIC_KEYS, f"unknown organic measure {key!r}")
        check_count(value, f"organic.{key}")
    check_count(snap.get("followers"), "followers")
    for card in snap.get("cards", []):
        check_count(card.get("views"), "card views")


def validate_item(item: dict) -> None:
    need(POST_ID_RE.fullmatch(str(item.get("id", ""))) is not None, "item id missing or bad")
    need(item.get("kind") in ITEM_KINDS, f"item kind must be one of {sorted(ITEM_KINDS)}")
    parse_time(item.get("created_at", ""))
    need(POST_ID_RE.fullmatch(str(item.get("conversation_id", ""))) is not None, "item conversation_id bad")
    for group, keys in (("public", PUBLIC_KEYS), ("organic", ORGANIC_KEYS)):
        for key, value in (item.get(group) or {}).items():
            need(key in keys, f"unknown {group} measure {key!r}")
            check_count(value, f"{group}.{key}")


# ---------- helpers ----------


def age_hours(post: dict, at: datetime) -> float:
    return (at - parse_time(post["posted_at"])).total_seconds() / 3600


def snapshot_kind(hours: float) -> str:
    if hours < SNAPSHOT_MIN_H:
        return "early"
    if hours <= SNAPSHOT_MAX_H:
        return "valid"
    return "late"


def best_snapshot(post: dict) -> dict | None:
    snaps = post.get("snapshots", [])
    for kind in ("valid", "late"):
        chosen = [s for s in snaps if s["kind"] == kind]
        if chosen:
            return chosen[0] if kind == "valid" else chosen[-1]
    return None


def valid_snapshot(post: dict) -> dict | None:
    for snap in post.get("snapshots", []):
        if snap["kind"] == "valid":
            return snap
    return None


def primary_value(snap: dict | None, metric: str) -> int | None:
    if snap is None:
        return None
    return snap.get("root", {}).get(metric)


def open_experiment(state: dict) -> dict | None:
    for exp in state["experiments"]:
        if exp["status"] in OPEN_STATES:
            return exp
    return None


def next_id(prefix: str, items: list[dict]) -> str:
    return f"{prefix}-{len(items) + 1:03d}"


# ---------- commands ----------


def cmd_init(repo: Repo, args) -> dict:
    if repo.state_path.is_file():
        raise LoopError("already initialised")
    handles = [h.strip().lstrip("@").lower() for h in args.self_handles.split(",") if h.strip()]
    need(bool(handles), "--self-handles needs at least one handle")
    state = {
        "version": 1,
        "started_at": iso(now_arg(args.now)),
        "self_handles": handles,
        "last_review_at": None,
        "reference": {"status": "current", "checked_at": iso(now_arg(args.now)), "changed_files": []},
        "experiments": [],
        "lessons": [],
        "rules": [],
    }
    repo.save_state(state)
    return {"initialised": True, "started_at": state["started_at"]}


def cmd_record_post(repo: Repo, args) -> dict:
    repo.state()
    payload = read_json(Path(args.json))
    post = {
        "root_id": str(payload.get("root_id", "")),
        "slug": payload.get("slug"),
        "format": payload.get("format"),
        "lane": payload.get("lane"),
        "posted_at": payload.get("posted_at", ""),
        "retrospective": payload.get("retrospective", False),
        "made_in_repo": payload.get("made_in_repo", True),
        "experiment": payload.get("experiment"),
        "arm": payload.get("arm", "none"),
        "hypothesis": payload.get("hypothesis"),
        "cards": payload.get("cards", []),
        "media": payload.get("media", []),
        "ai_media": payload.get("ai_media", False),
        "production_minutes": payload.get("production_minutes"),
        "edits": payload.get("edits", []),
        "draft": payload.get("draft"),
        "snapshots": [],
        "missed": False,
        "auto": bool(payload.get("auto", False)),
    }
    validate_post(post)
    path = repo.post_path(post["root_id"])
    if path.exists():
        existing = read_json(path)
        if not (existing.get("auto") and not post["auto"]):
            return {"recorded": False, "reason": "already recorded", "root_id": post["root_id"]}
        # The daily run recorded this post on its own; the operator's /posted record replaces it.
        for key in ("snapshots", "missed", "nonorganic", "amendments"):
            if key in existing:
                post[key] = existing[key]
    state = repo.state()
    if post["experiment"] is not None:
        exp = next((e for e in state["experiments"] if e["id"] == post["experiment"]), None)
        if exp is None:
            raise LoopError(f"no experiment {post['experiment']}")
        need(exp["status"] in OPEN_STATES, f"experiment {exp['id']} is closed")
        need(post["arm"] != "none", "a post in an experiment needs arm treatment or control")
        need(not post["retrospective"], "retrospective posts cannot join an experiment")
    else:
        need(post["arm"] == "none", "arm set without an experiment")
    repo.save_post(post)
    return {"recorded": True, "root_id": post["root_id"]}


def cmd_due(repo: Repo, args) -> dict:
    at = now_arg(args.now)
    due, missed, pending = [], [], []
    for post in repo.posts():
        if post["missed"] or valid_snapshot(post):
            continue
        hours = age_hours(post, at)
        if post["retrospective"] and hours > SNAPSHOT_MAX_H:
            continue
        row = {"root_id": post["root_id"], "slug": post["slug"], "age_hours": round(hours, 1),
               "card_ids": [c["id"] for c in post.get("cards", [])]}
        if hours < SNAPSHOT_MIN_H:
            pending.append(row)
        elif hours <= SNAPSHOT_MAX_H:
            due.append(row)
        else:
            missed.append(row)
    return {"due": due, "missed": missed, "pending": pending,
            "window_hours": [SNAPSHOT_MIN_H, SNAPSHOT_MAX_H]}


def cmd_record_snapshot(repo: Repo, args) -> dict:
    state = repo.state()
    payload = read_json(Path(args.json))
    root_id = str(payload.get("root_id", ""))
    post = repo.post(root_id)
    observed = parse_time(payload.get("observed_at", ""))
    hours = age_hours(post, observed)
    need(hours >= 0, "observed before the post existed")
    kind = snapshot_kind(hours)
    if payload.get("stage") == "final":
        need(hours >= FINAL_MIN_DAYS * 24, f"a final read needs a post at least {FINAL_MIN_DAYS} days old")
        kind = "final"
        if any(s["kind"] == "final" for s in post["snapshots"]):
            return {"recorded": False, "reason": "final read already exists", "root_id": root_id}
    if kind == "valid" and valid_snapshot(post):
        return {"recorded": False, "reason": "valid snapshot already exists", "root_id": root_id}
    need(not (kind == "valid" and post["missed"]), "post already marked missed")
    if payload.get("repliers") is not None:
        self_handles = set(state["self_handles"])
        repliers = [str(h).lstrip("@").lower() for h in payload["repliers"]]
        outside = [h for h in repliers if h not in self_handles]
        outside_count, outside_names = len(outside), sorted(set(outside))
    else:
        # X API reads count outside replies by id; names of other accounts are not stored.
        outside_count, outside_names = payload.get("outside_replies"), []
        check_count(outside_count, "outside_replies")
    root = {m: payload.get("root", {}).get(m) for m in METRICS}
    snap = {
        "observed_at": iso(observed),
        "age_hours": round(hours, 1),
        "kind": kind,
        "source": payload.get("source", "grok"),
        "root": root,
        "cards": payload.get("cards", []),
        "outside_replies": outside_count,
        "outside_repliers": outside_names,
        "repliers_complete": payload.get("repliers_complete"),
        "followers": payload.get("followers"),
        "raw_file": payload.get("raw_file"),
        "missing": [m for m in METRICS if root[m] is None],
    }
    if payload.get("organic") is not None:
        snap["organic"] = {k: payload["organic"].get(k) for k in ORGANIC_KEYS}
    validate_snapshot(snap)
    post["snapshots"].append(snap)
    repo.save_post(post)
    return {"recorded": True, "root_id": root_id, "kind": kind, "age_hours": snap["age_hours"],
            "missing": snap["missing"]}


def cmd_record_activity(repo: Repo, args) -> dict:
    """One row per post, reply and quote, with a read per stage. Advances the read cursors last."""
    state = repo.state()
    payload = read_json(Path(args.json))
    stage = payload.get("stage")
    need(stage in READ_STAGES, f"stage must be one of {sorted(READ_STAGES)}")
    observed = parse_time(payload.get("observed_at", ""))
    months: dict[str, dict] = {}
    recorded = 0
    for item in payload.get("items", []):
        validate_item(item)
        month = item["created_at"][:7]
        if month not in months:
            path = repo.activity_dir / f"{month}.json"
            months[month] = read_json(path) if path.is_file() else {"month": month, "items": {}}
        row = months[month]["items"].setdefault(item["id"], {"id": item["id"]})
        row.update({k: item[k] for k in ("kind", "created_at", "conversation_id")})
        row["topics"] = item.get("topics", [])
        row["text"] = item.get("text", "")
        hours = (observed - parse_time(item["created_at"])).total_seconds() / 3600
        label = snapshot_kind(hours) if stage == "48h" else stage
        reads = row.setdefault("reads", {})
        if stage == "48h" and reads.get("48h", {}).get("label") == "valid" and label != "valid":
            continue
        reads[stage] = {"at": iso(observed), "age_hours": round(hours, 1), "label": label,
                        "public": {k: (item.get("public") or {}).get(k) for k in PUBLIC_KEYS},
                        "organic": {k: (item.get("organic") or {}).get(k) for k in ORGANIC_KEYS}}
        recorded += 1
    for month, data in months.items():
        data["items"] = dict(sorted(data["items"].items(), key=lambda kv: kv[1]["created_at"]))
        write_json(repo.activity_dir / f"{month}.json", data)
    api = state.setdefault("api", {})
    for key in ("read48_until", "final_until"):
        if (payload.get("cursor") or {}).get(key):
            api[key] = iso(parse_time(payload["cursor"][key]))
    repo.save_state(state)
    return {"recorded": recorded, "stage": stage, "cursors": api}


def _note_person(people: dict, user_id: str, item_id: str, at: str, how: str) -> None:
    """Keep each account's most recent interaction with us."""
    seen = people.get(user_id)
    if seen is None or parse_time(at) >= parse_time(seen["at"]):
        people[user_id] = {"item": item_id, "at": iso(parse_time(at)), "how": how}


def cmd_record_interactions(repo: Repo, args) -> dict:
    """Who replied to us, and who we replied to. Private: loop/followers/, gitignored."""
    repo.state()
    payload = read_json(Path(args.json))
    observed = parse_time(payload.get("observed_at", ""))
    self_ids = {str(i) for i in payload.get("self_ids", [])}
    data = repo.interactions()
    for mention in payload.get("mentions", []):
        author = str(mention.get("author_id", ""))
        if not author or author in self_ids:
            continue
        conv = data["conversations"].setdefault(str(mention["conversation_id"]),
                                                {"at": mention["created_at"], "replies": []})
        if mention["id"] not in conv["replies"]:
            conv["replies"].append(mention["id"])
        _note_person(data["people"], author, str(mention.get("replied_to") or mention["conversation_id"]),
                     mention["created_at"], "replied")
    for target in payload.get("reply_targets", []):
        user = str(target.get("user_id", ""))
        if user and user not in self_ids:
            _note_person(data["people"], user, str(target["item_id"]), target["at"], "replied_to")
    since = payload.get("since_id")
    if since and (not data["mentions_since_id"] or int(since) > int(data["mentions_since_id"])):
        data["mentions_since_id"] = str(since)
    people_cut = observed - timedelta(days=INTERACTION_DAYS)
    conv_cut = observed - timedelta(days=CONVERSATION_DAYS)
    data["people"] = {u: p for u, p in data["people"].items() if parse_time(p["at"]) >= people_cut}
    data["conversations"] = {c: v for c, v in data["conversations"].items() if parse_time(v["at"]) >= conv_cut}
    write_json(repo.private_dir / "interactions.json", data)
    return {"people": len(data["people"]), "mentions_since_id": data["mentions_since_id"],
            "outside_replies": {c: len(v["replies"]) for c, v in data["conversations"].items()}}


def cmd_record_followers(repo: Repo, args) -> dict:
    """Compare today's follower ids with the last earlier day's and credit new followers.

    Ids stay in loop/followers/ (gitignored). Only counts and per-item credit reach
    ledger/activity/account.json. A new follower is credited once, to their most
    recent interaction; anyone with none stays unattributed, so credit is a lower bound.
    """
    repo.state()
    payload = read_json(Path(args.json))
    observed = parse_time(payload.get("observed_at", ""))
    self_ids = {str(i) for i in payload.get("self_ids", [])}
    ids = sorted({str(i) for i in payload.get("ids", [])} - self_ids)
    day = observed.date().isoformat()
    earlier = [p for p in sorted(repo.private_dir.glob("followers-*.json")) if p.stem[len("followers-"):] < day]
    previous = set(read_json(earlier[-1])["ids"]) if earlier else None
    write_json(repo.private_dir / f"followers-{day}.json", {"at": iso(observed), "ids": ids})
    for old in sorted(repo.private_dir.glob("followers-*.json"))[:-FOLLOWER_FILES_KEPT]:
        old.unlink()
    row = {"date": day, "at": iso(observed), "followers": payload.get("total", len(ids))}
    if previous is None:
        row["baseline"] = True
    else:
        new, lost = set(ids) - previous, previous - set(ids)
        people = repo.interactions()["people"]
        credit: dict[str, int] = {}
        for user in new:
            if user in people:
                item = people[user]["item"]
                credit[item] = credit.get(item, 0) + 1
        row.update({"new": len(new), "lost": len(lost), "attributed": dict(sorted(credit.items())),
                    "unattributed": len(new) - sum(credit.values())})
    account = repo.account()
    account["days"] = sorted([d for d in account["days"] if d["date"] != day] + [row], key=lambda d: d["date"])
    write_json(repo.account_path, account)
    return row


def cmd_set_lane(repo: Repo, args) -> dict:
    need(args.lane in {"main", "other"}, "--lane must be main or other")
    need(bool(args.reason.strip()), "--reason required")
    post = repo.post(args.root_id)
    if post["lane"] == args.lane:
        return {"changed": False, "root_id": args.root_id, "lane": args.lane}
    post.setdefault("amendments", []).append({"at": iso(now_arg(args.now)), "field": "lane", "from": post["lane"],
                                              "value": args.lane, "reason": args.reason.strip()})
    post["lane"] = args.lane
    repo.save_post(post)
    return {"changed": True, "root_id": args.root_id, "lane": args.lane}


def cmd_mark_nonorganic(repo: Repo, args) -> dict:
    """Mark a post whose reach is mostly paid or otherwise non-organic. It never enters a cohort or a round."""
    need(bool(args.reason.strip()), "--reason required")
    post = repo.post(args.root_id)
    if post.get("nonorganic"):
        return {"marked": False, "reason": "already marked", "root_id": args.root_id}
    post["nonorganic"] = {"reason": args.reason.strip(), "at": iso(now_arg(args.now))}
    repo.save_post(post)
    return {"marked": True, "root_id": args.root_id}


def cmd_set_repliers_complete(repo: Repo, args) -> dict:
    """Correct whether a post's reply-author list was complete. Logged on the post."""
    need(args.value in {"true", "false"}, "--value must be true or false")
    need(bool(args.reason.strip()), "--reason required")
    post = repo.post(args.root_id)
    need(bool(post["snapshots"]), f"{args.root_id} has no snapshots")
    value = args.value == "true"
    changed = 0
    for snap in post["snapshots"]:
        if snap.get("repliers_complete") is not value:
            snap["repliers_complete"] = value
            changed += 1
    if changed:
        post.setdefault("amendments", []).append({
            "at": iso(now_arg(args.now)), "field": "repliers_complete",
            "value": value, "snapshots": changed, "reason": args.reason.strip()})
        repo.save_post(post)
    return {"root_id": args.root_id, "repliers_complete": value, "snapshots_changed": changed}


def cmd_mark_missed(repo: Repo, args) -> dict:
    at = now_arg(args.now)
    marked = []
    for post in repo.posts():
        if post["missed"] or valid_snapshot(post) or best_snapshot(post):
            continue
        if age_hours(post, at) > SNAPSHOT_MAX_H:
            post["missed"] = True
            repo.save_post(post)
            marked.append(post["root_id"])
    return {"marked_missed": marked}


def cmd_open_experiment(repo: Repo, args) -> dict:
    state = repo.state()
    need(open_experiment(state) is None, "an experiment is already open; one at a time")
    payload = read_json(Path(args.json))
    metric = str(payload.get("primary") or "")
    need(metric in METRICS, f"primary must be one of {METRICS}")
    need(metric not in UNSCORABLE, f"primary {metric!r} cannot be scored: {UNSCORABLE.get(metric, '')}")
    effect = float(payload.get("effect", 1.5))
    need(effect > 1.0, "effect must be above 1.0")
    cohort = [str(c) for c in payload.get("cohort", [])]
    need(len(cohort) >= MIN_COHORT, f"cohort needs at least {MIN_COHORT} posts")
    values, used = [], []
    for root_id in cohort:
        post = repo.post(root_id)
        need(not post.get("nonorganic"),
             f"{root_id} is marked non-organic ({(post.get('nonorganic') or {}).get('reason')}); it cannot be in a cohort")
        snap = best_snapshot(post)
        value = primary_value(snap, metric)
        if snap is not None and value is not None:
            values.append(value)
            used.append({"root_id": root_id, "value": value, "kind": snap["kind"]})
    need(len(values) >= MIN_COHORT, f"only {len(values)} cohort posts have a {metric} snapshot")
    for field in ("question", "treatment", "control"):
        need(isinstance(payload.get(field), str) and payload[field].strip(), f"{field} required")
    median = statistics.median(values)
    need(median > 0, f"the cohort's median {metric} is 0, so every post would clear the bar; "
                     "pick a measure the cohort actually has")
    exp = {
        "id": next_id("E", state["experiments"]),
        "question": payload["question"],
        "treatment": payload["treatment"],
        "control": payload["control"],
        "reference_facts": payload.get("reference_facts", []),
        "primary": metric,
        "effect": effect,
        "size": 3,
        "cohort": used,
        "cohort_median": median,
        "threshold": median * effect,
        "opened_at": iso(now_arg(args.now)),
        "status": "testing",
        "rounds": [],
        "closed_at": None,
    }
    state["experiments"].append(exp)
    repo.save_state(state)
    return {"opened": exp["id"], "cohort_median": median, "threshold": exp["threshold"]}


TRANSITIONS = {
    ("testing", "pass"): "promising",
    ("testing", "mixed"): "unclear",
    ("testing", "fail"): "no_effect",
    ("promising", "pass"): "adopted",
    ("promising", "mixed"): "not_replicated",
    ("promising", "fail"): "not_replicated",
    ("unclear", "pass"): "promising",
    ("unclear", "mixed"): "no_effect",
    ("unclear", "fail"): "no_effect",
}


def round_result(passes: int, size: int) -> str:
    if passes == size:
        return "pass"
    if passes >= size - 1:
        return "mixed"
    return "fail"


def cmd_evaluate(repo: Repo, args) -> dict:
    state = repo.state()
    exp = open_experiment(state)
    if exp is None:
        return {"evaluated": False, "reason": "no open experiment"}
    consumed = {pid for rnd in exp["rounds"] for pid in rnd["posts"]}
    ready = []
    for post in repo.posts():
        if post.get("experiment") != exp["id"] or post.get("arm") != "treatment":
            continue
        if post["root_id"] in consumed or post.get("nonorganic"):
            continue
        snap = valid_snapshot(post)
        value = primary_value(snap, exp["primary"])
        if value is not None:
            ready.append((post["root_id"], value))
    events = []
    at = iso(now_arg(args.now))
    while exp["status"] in OPEN_STATES and len(ready) >= exp["size"]:
        batch, ready = ready[: exp["size"]], ready[exp["size"]:]
        passes = sum(1 for _, value in batch if value >= exp["threshold"])
        result = round_result(passes, exp["size"])
        before = exp["status"]
        exp["status"] = TRANSITIONS[(before, result)]
        exp["rounds"].append({"posts": [pid for pid, _ in batch],
                              "values": [value for _, value in batch],
                              "passes": passes, "result": result, "at": at})
        events.append({"from": before, "result": result, "to": exp["status"]})
        if exp["status"] not in OPEN_STATES:
            exp["closed_at"] = at
            evidence = [pid for rnd in exp["rounds"] for pid in rnd["posts"]]
            state["lessons"].append({
                "id": next_id("L", state["lessons"]),
                "experiment": exp["id"],
                "statement": exp["treatment"],
                "status": exp["status"],
                "evidence": evidence,
                "reference_facts": exp.get("reference_facts", []),
                "created_at": at,
                "last_evidence_at": at,
                "rule_state": "none",
            })
    waiting = exp["size"] - len(ready) if exp["status"] in OPEN_STATES else 0
    repo.save_state(state)
    return {"evaluated": True, "experiment": exp["id"], "status": exp["status"],
            "events": events, "posts_needed_for_next_round": waiting}


def cmd_next_slot(repo: Repo, args) -> dict:
    state = repo.state()
    at = now_arg(args.now)
    started = parse_time(state["started_at"])
    live = [p for p in repo.posts() if not p["retrospective"] and parse_time(p["posted_at"]) >= started]
    count = len(live)
    alternating = at - started < timedelta(days=EXPLORE_ALTERNATE_DAYS)
    explore = count % 2 == 0 if alternating else count % 3 == 0
    exp = open_experiment(state)
    slot = {"slot": "explore" if explore else "exploit", "posts_since_start": count,
            "rule": "alternate" if alternating else "one in three explores"}
    if explore:
        slot["experiment"] = exp["id"] if exp else None
        slot["arm"] = "treatment" if exp else None
        slot["action"] = "post the treatment" if exp else "open an experiment first"
    else:
        adopted = [l for l in state["lessons"] if l["status"] == "adopted"]
        slot["experiment"] = exp["id"] if exp else None
        slot["arm"] = "control" if exp else None
        slot["action"] = "post the current best approach"
        slot["adopted_lessons"] = [l["id"] for l in adopted]
    return slot


def cmd_lane_share(repo: Repo, args) -> dict:
    recent = repo.posts()[-LANE_WINDOW:]
    main = sum(1 for p in recent if p["lane"] == "main")
    return {"window": len(recent), "main": main,
            "share": round(main / len(recent), 2) if recent else None}


def cmd_review_due(repo: Repo, args) -> dict:
    state = repo.state()
    at = now_arg(args.now)
    last = state["last_review_at"]
    due = last is None or at - parse_time(last) >= timedelta(days=REVIEW_EVERY_DAYS)
    return {"review_due": due, "last_review_at": last}


def cmd_mark_reviewed(repo: Repo, args) -> dict:
    state = repo.state()
    at = now_arg(args.now)
    stale = []
    for lesson in state["lessons"]:
        if lesson["status"] == "adopted" and at - parse_time(lesson["last_evidence_at"]) > timedelta(days=STALE_AFTER_DAYS):
            lesson["status"] = "stale"
            stale.append(lesson["id"])
    state["last_review_at"] = iso(at)
    repo.save_state(state)
    return {"reviewed_at": state["last_review_at"], "newly_stale": stale}


def cmd_set_reference(repo: Repo, args) -> dict:
    state = repo.state()
    need(args.status in {"current", "stale"}, "status must be current or stale")
    files = [f for f in (args.files or "").split(",") if f]
    state["reference"] = {"status": args.status, "checked_at": iso(now_arg(args.now)), "changed_files": files}
    repo.save_state(state)
    return {"reference": state["reference"]}


def cmd_add_preference(repo: Repo, args) -> dict:
    """An operator edit repeated on three or more posts becomes an adopted lesson."""
    state = repo.state()
    need(bool(args.statement.strip()), "--statement required")
    evidence = [e for e in args.evidence.split(",") if e]
    need(len(set(evidence)) >= 3, "a preference needs at least 3 different posts as evidence")
    for root_id in evidence:
        post = repo.post(root_id)
        need(any(e.get("class") == "preference" for e in post.get("edits", [])),
             f"{root_id} has no recorded preference edit")
    at = iso(now_arg(args.now))
    lesson = {
        "id": next_id("L", state["lessons"]),
        "experiment": None,
        "statement": args.statement.strip(),
        "status": "adopted",
        "evidence": sorted(set(evidence)),
        "reference_facts": [],
        "source": "operator edits",
        "created_at": at,
        "last_evidence_at": at,
        "rule_state": "none",
    }
    state["lessons"].append(lesson)
    repo.save_state(state)
    return {"lesson": lesson["id"], "status": "adopted"}


def find_lesson(state: dict, lesson_id: str) -> dict:
    need(LESSON_RE.fullmatch(lesson_id) is not None, f"bad lesson id {lesson_id!r}")
    for lesson in state["lessons"]:
        if lesson["id"] == lesson_id:
            return lesson
    raise LoopError(f"no lesson {lesson_id}")


def cmd_commit_rule(repo: Repo, args) -> dict:
    state = repo.state()
    lesson = find_lesson(state, args.lesson)
    need(lesson["status"] == "adopted", f"{lesson['id']} is {lesson['status']}; only adopted lessons change rules")
    files = [f for f in args.files.split(",") if f]
    need(bool(files), "--files required")
    for name in files:
        need(not name.startswith(("/", "..")), f"file {name} must be inside the repo")
        need(name.startswith((".claude/skills/", "voice/")), f"{name} is not a rule file")
    changed = repo.git("status", "--porcelain", "--", *files).strip()
    need(bool(changed), "none of those files has changes to commit")
    repo.git("add", "--", *files)
    message = f"feat(rules): apply {lesson['id']}\n\n{lesson['statement']}\nEvidence: {', '.join(lesson['evidence'])}"
    repo.git("commit", "-m", message, "--", *files)
    sha = repo.git("rev-parse", "HEAD").strip()
    state["rules"].append({"lesson": lesson["id"], "commit": sha, "files": files,
                           "applied_at": iso(now_arg(args.now)), "undone": False, "revert_commit": None})
    lesson["rule_state"] = "applied"
    repo.save_state(state)
    return {"committed": sha, "lesson": lesson["id"], "files": files}


def cmd_undo(repo: Repo, args) -> dict:
    state = repo.state()
    lesson = find_lesson(state, args.lesson)
    rule = next((r for r in reversed(state["rules"]) if r["lesson"] == lesson["id"] and not r["undone"]), None)
    if rule is None:
        raise LoopError(f"no applied rule for {lesson['id']}")
    dirty = repo.git("status", "--porcelain", "--", *rule["files"]).strip()
    need(not dirty, "those rule files have uncommitted edits; nothing was reverted")
    try:
        repo.git("revert", "--no-edit", rule["commit"])
    except LoopError:
        subprocess.run(["git", "revert", "--abort"], cwd=repo.root, capture_output=True, check=False)
        raise LoopError(f"revert of {rule['commit'][:8]} conflicted with a later change; nothing was reverted")
    rule["undone"] = True
    rule["revert_commit"] = repo.git("rev-parse", "HEAD").strip()
    lesson["rule_state"] = "reverted"
    repo.save_state(state)
    return {"reverted": rule["commit"], "revert_commit": rule["revert_commit"], "lesson": lesson["id"]}


def cmd_commit_data(repo: Repo, args) -> dict:
    paths = [p for p in ("ledger", "loop", "reviews", "experiments.md", "learnings.md", "queue", "reference")
             if (repo.root / p).exists()]
    repo.git("add", "--", *paths)
    staged = repo.git("diff", "--cached", "--name-only").strip()
    if not staged:
        return {"committed": None, "reason": "nothing changed"}
    repo.git("commit", "-m", f"chore(data): {args.message}", "--", *paths)
    return {"committed": repo.git("rev-parse", "HEAD").strip()}


def cmd_status(repo: Repo, args) -> dict:
    state = repo.state()
    exp = open_experiment(state)
    return {
        "due": cmd_due(repo, args),
        "review": cmd_review_due(repo, args),
        "slot": cmd_next_slot(repo, args),
        "lane": cmd_lane_share(repo, args),
        "open_experiment": exp,
        "reference": state["reference"],
        "api": state.get("api", {}),
        "stale_lessons": [l["id"] for l in state["lessons"] if l["status"] == "stale"],
    }


def cmd_validate(repo: Repo, args) -> dict:
    repo.state()
    problems = []
    count = 0
    for path in sorted(repo.ledger_dir.glob("*.json")) if repo.ledger_dir.is_dir() else []:
        count += 1
        try:
            post = read_json(path)
            validate_post(post)
            need(path.stem == post["root_id"], "file name does not match root_id")
        except LoopError as exc:
            problems.append(f"{path.name}: {exc}")
    return {"posts": count, "problems": problems}


# ---------- readable views ----------


def fmt_replies(snap: dict | None) -> str:
    if snap is None or snap.get("outside_replies") is None:
        return "–"
    prefix = "≥" if snap.get("repliers_complete") is False else ""
    return f"{prefix}{snap['outside_replies']}"


def fmt(value) -> str:
    return "–" if value is None else (f"{value:g}" if isinstance(value, float) else str(value))


MIN_RATE_IMPRESSIONS = 50


def best_read(row: dict | None) -> dict | None:
    """An item's organic read to show: the 36-60h one, else the backfill."""
    if not row:
        return None
    reads = row.get("reads", {})
    return reads.get("48h") or reads.get("backfill")


def nonorganic_pct(read: dict | None) -> str:
    public = (read or {}).get("public", {}).get("impressions")
    organic = (read or {}).get("organic", {}).get("impressions")
    if not public or organic is None:
        return "–"
    return f"{max(0, public - organic) * 100 // public}%"


def credited_follows(root_id: str, rows: dict[str, dict], days: list[dict]) -> int:
    """Follows credited to a post, its thread cards, or replies in its conversation."""
    total = 0
    for day in days:
        for item, count in day.get("attributed", {}).items():
            if item == root_id or rows.get(item, {}).get("conversation_id") == root_id:
                total += count
    return total


def account_lines(rows: dict[str, dict], days: list[dict]) -> list[str]:
    if not days:
        return []
    anchor = parse_time(days[-1]["at"])
    week = [d for d in days if parse_time(d["at"]) > anchor - timedelta(days=7)]
    new = sum(d.get("new") or 0 for d in week)
    lost = sum(d.get("lost") or 0 for d in week)
    credited = sum(sum(d.get("attributed", {}).values()) for d in week)
    recent = [r for r in rows.values() if anchor - timedelta(days=7) < parse_time(r["created_at"]) <= anchor]
    lines = ["\n## Account\n\n",
             f"Followers: {days[-1]['followers']} on {days[-1]['date']}. In the 7 days to then: {new} new, {lost} lost; "
             f"{credited} of the new credited to a post or reply they engaged with (a lower bound).\n\n"]
    visits = sum((best_read(r) or {}).get("organic", {}).get("profile_visits") or 0 for r in recent)
    if visits:
        lines.append(f"Follows per profile visit, items from those 7 days: {new} / {visits}.\n\n")
    lines += ["| Kind | Items | Organic impressions | Profile visits | Likes | Visits per 1,000 |\n",
              "|---|---:|---:|---:|---:|---:|\n"]
    topics: dict[str, int] = {}
    for kind in ("original", "quote", "reply", "thread_card"):
        group = [r for r in recent if r["kind"] == kind]
        reads = [best_read(r)["organic"] for r in group if best_read(r)]
        if not group:
            continue
        impressions = sum(o.get("impressions") or 0 for o in reads)
        visited = sum(o.get("profile_visits") or 0 for o in reads)
        likes = sum(o.get("likes") or 0 for o in reads)
        rate = f"{visited * 1000 / impressions:.1f}" if impressions >= MIN_RATE_IMPRESSIONS else "–"
        lines.append(f"| {kind.replace('_', ' ')} | {len(group)} | {impressions} | {visited} | {likes} | {rate} |\n")
    for r in recent:
        organic = (best_read(r) or {}).get("organic", {}).get("impressions") or 0
        for topic in r.get("topics", []):
            topics[topic] = topics.get(topic, 0) + organic
    top = sorted(topics.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    if top:
        lines.append("\nTop topics by organic impressions (X's own labels, a proxy): "
                     + ", ".join(f"{name} ({count})" for name, count in top) + ".\n")
    return lines


def render(repo: Repo) -> None:
    if not repo.state_path.is_file():
        return
    state = repo.state()
    posts = repo.posts()
    rows = repo.activity()
    days = repo.account()["days"]
    head = "<!-- Generated by scripts/loop.py. Do not edit; it is rewritten after every loop command. -->\n\n"

    lines = [head, "# Ledger summary\n\n",
             "Times are Australia/Brisbane. Views and Snapshot come from the 36–60 hour snapshot, else the latest late one. "
             "Organic, Non-organic and Visits come from the X API read at 36–60 hours, else the September backfill. "
             "Follows are new followers credited to the post or its conversation, a lower bound. "
             "A leading ≥ means X search returned fewer reply authors than the reply count.\n\n",
             "| Posted | Slug | Format | Lane | Experiment | Views | Organic | Non-organic | Visits | Bookmarks | "
             "Outside replies | Follows | Snapshot |\n",
             "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|\n"]
    for post in posts:
        snap = best_snapshot(post)
        root = snap["root"] if snap else {}
        read = best_read(rows.get(post["root_id"]))
        organic = (read or {}).get("organic", {})
        where = f"{snap['kind']} {snap['age_hours']:g}h" if snap else ("missed" if post["missed"] else "pending")
        exp = f"{post['experiment']} {post['arm']}" if post.get("experiment") else ("retro" if post["retrospective"] else "–")
        if post.get("nonorganic"):
            exp += ", non-organic"
        lines.append(f"| {local(post['posted_at'])} | {post['slug']} | {post['format']} | {post['lane']} | {exp} | "
                     f"{fmt(root.get('views'))} | {fmt(organic.get('impressions'))} | {nonorganic_pct(read)} | "
                     f"{fmt(organic.get('profile_visits'))} | {fmt(root.get('bookmarks'))} | "
                     f"{fmt_replies(snap)} | {credited_follows(post['root_id'], rows, days)} | {where} |\n")
    lines += account_lines(rows, days)
    atomic_write(repo.ledger_dir / "SUMMARY.md", "".join(lines))

    lines = [head, "# Experiments\n\n", "One runs at a time. Rules are fixed when it opens.\n\n"]
    if not state["experiments"]:
        lines.append("None yet.\n")
    for exp in reversed(state["experiments"]):
        lines.append(f"## {exp['id']}: {exp['question']}\n\n")
        lines.append(f"- **Status:** {exp['status']}\n")
        lines.append(f"- **Treatment:** {exp['treatment']}\n")
        lines.append(f"- **Compared with:** {exp['control']}\n")
        lines.append(f"- **Primary outcome:** root {exp['primary']} at the 36–60 hour snapshot\n")
        lines.append(f"- **Bar to beat:** {fmt(exp['threshold'])} ({exp['effect']:g} × cohort median {fmt(exp['cohort_median'])})\n")
        lines.append(f"- **Cohort, frozen {exp['opened_at'][:10]}:** "
                     + ", ".join(f"{c['root_id']} ({c['value']}, {c['kind']})" for c in exp["cohort"]) + "\n")
        for i, rnd in enumerate(exp["rounds"], start=1):
            lines.append(f"- **Round {i}:** {rnd['passes']} of {len(rnd['posts'])} beat the bar "
                         f"({', '.join(map(str, rnd['values']))}), {rnd['result']}\n")
        lines.append("\n")
    atomic_write(repo.root / "experiments.md", "".join(lines))

    lines = [head, "# Learnings\n\n",
             "A lesson changes the drafting rules only when it is `adopted` and the operator types `/apply`.\n\n",
             "| Lesson | Status | Rule | Claim | Evidence | Last evidence |\n", "|---|---|---|---|---|---|\n"]
    for lesson in state["lessons"]:
        lines.append(f"| {lesson['id']} | {lesson['status']} | {lesson['rule_state']} | {lesson['statement']} | "
                     f"{', '.join(lesson['evidence'])} | {lesson['last_evidence_at'][:10]} |\n")
    if not state["lessons"]:
        lines.append("| – | – | – | No lessons yet | – | – |\n")
    atomic_write(repo.root / "learnings.md", "".join(lines))


# ---------- cli ----------


COMMANDS = {
    "init": cmd_init,
    "record-post": cmd_record_post,
    "due": cmd_due,
    "record-snapshot": cmd_record_snapshot,
    "mark-missed": cmd_mark_missed,
    "set-repliers-complete": cmd_set_repliers_complete,
    "mark-nonorganic": cmd_mark_nonorganic,
    "record-activity": cmd_record_activity,
    "record-interactions": cmd_record_interactions,
    "record-followers": cmd_record_followers,
    "set-lane": cmd_set_lane,
    "open-experiment": cmd_open_experiment,
    "evaluate": cmd_evaluate,
    "next-slot": cmd_next_slot,
    "lane-share": cmd_lane_share,
    "review-due": cmd_review_due,
    "mark-reviewed": cmd_mark_reviewed,
    "set-reference": cmd_set_reference,
    "add-preference": cmd_add_preference,
    "commit-rule": cmd_commit_rule,
    "undo": cmd_undo,
    "commit-data": cmd_commit_data,
    "status": cmd_status,
    "validate": cmd_validate,
}
READ_ONLY = {"due", "next-slot", "lane-share", "review-due", "status", "validate"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Learning-loop state. Prints JSON. No network.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="repo root (tests only)")
    parser.add_argument("--now", default=None, help="ISO time to use instead of the clock")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in COMMANDS:
        sp = sub.add_parser(name)
        if name == "init":
            sp.add_argument("--self-handles", required=True)
        if name in {"record-post", "record-snapshot", "open-experiment", "record-activity",
                    "record-interactions", "record-followers"}:
            sp.add_argument("--json", required=True, help="payload file")
        if name == "set-reference":
            sp.add_argument("--status", required=True)
            sp.add_argument("--files", default="")
        if name in {"commit-rule", "undo"}:
            sp.add_argument("--lesson", required=True)
        if name == "commit-rule":
            sp.add_argument("--files", required=True)
        if name == "set-repliers-complete":
            sp.add_argument("--root-id", required=True)
            sp.add_argument("--value", required=True, help="true or false")
            sp.add_argument("--reason", required=True)
        if name in {"mark-nonorganic", "set-lane"}:
            sp.add_argument("--root-id", required=True)
            sp.add_argument("--reason", required=True)
        if name == "set-lane":
            sp.add_argument("--lane", required=True)
        if name == "add-preference":
            sp.add_argument("--statement", required=True)
            sp.add_argument("--evidence", required=True, help="comma-separated post ids")
        if name == "commit-data":
            sp.add_argument("--message", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo = Repo(args.root.resolve())
    try:
        result = COMMANDS[args.command](repo, args)
        if args.command not in READ_ONLY:
            render(repo)
    except LoopError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
