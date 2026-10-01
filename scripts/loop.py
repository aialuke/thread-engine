#!/usr/bin/env python3
"""Deterministic state for the learning loop. The agent calls this; the operator never does.

Every command prints JSON on stdout. Errors print {"error": ...} on stderr and exit 1.
Each command writes at most one data file, atomically, then re-renders the
readable views (experiments.md, learnings.md, ledger/SUMMARY.md).

No network access. Git is used only by commit-rule, undo and commit-data.
The Read-window rules (36-60h, 26 days, missed, due-reads windows) live in loop_core/reads.py.
Whether a Read becomes a Snapshot (the ordered refusals and skips) lives in loop_core/snapshots.py.
How a Round moves an Experiment, what a closed one teaches, when a Lesson is stale, and which rules entry is in force live in loop_core/experiments.py.
What each Payload must look like (validation, defaults, keys) lives in loop_core/payloads.py.

X API data (from snapshot.py) lands in three places:
- ledger/activity/YYYY-MM.json: one row per post, reply and quote, with its reads.
- ledger/activity/account.json: daily follower counts and follow credit.
- loop/followers/: follower ids and who interacted with the account. Other
  people's data: gitignored, never committed, never rendered.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from loop_core.errors import LoopError, need
from loop_core.payloads import (MIN_COHORT, ORGANIC_KEYS, POST_ID_RE, PUBLIC_KEYS, activity_header, activity_items,
                                cursor_updates, experiment_terms, experiment_texts, follower_inputs, follower_total,
                                interaction_inputs, newer_since_id, post_from_payload, snapshot_from_payload, snapshot_is_final,
                                snapshot_observed, snapshot_root_id, validate_post, verified_count)
from loop_core import health, rates, views
from loop_core.experiments import (OPEN_STATES, evaluate_rounds, leave_experiment, lesson_basis, lesson_is_stale,
                                   lesson_outcome, newly_stale, next_id, next_slot, open_experiment)
from loop_core.reads import (FINAL_MAX_DAYS, SNAPSHOT_MAX_H, SNAPSHOT_MIN_H, backfill_cursor, best_snapshot, due_stage,
                             final_at_risk, need_final_age, past_window, read_windows, snapshot_kind, valid_snapshot)
from loop_core.snapshots import admit_snapshot
from loop_core.times import iso, parse_time

DEFAULT_ROOT = Path(__file__).resolve().parent.parent

REVIEW_EVERY_DAYS = 7
LANE_WINDOW = 15
FOLLOWER_FILES_KEPT = 2
INTERACTION_DAYS = 7
CONVERSATION_DAYS = 30

# X's analytics export (Analytics → Content → Export): organic, per post, with the follows and
# shares the pay-per-use API cannot read (reference/x-api.md P11).
EXPORT_COLUMNS = {"Impressions": "impressions", "Likes": "likes", "Replies": "replies", "Reposts": "reposts",
                  "Bookmarks": "bookmarks", "Shares": "shares", "New follows": "new_follows",
                  "Profile visits": "profile_visits"}
LESSON_RE = re.compile(r"^L-[0-9]{3}$")


# ---------- time and io ----------


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


# ---------- helpers ----------


def age_hours(post: dict, at: datetime) -> float:
    return (at - parse_time(post["posted_at"])).total_seconds() / 3600


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
    post = post_from_payload(payload)
    path = repo.post_path(post["root_id"])
    if path.exists():
        existing = read_json(path)
        if not (existing.get("auto") and not post["auto"]):
            return {"recorded": False, "reason": "already recorded", "root_id": post["root_id"]}
        # The daily run recorded this post on its own; the operator's /posted record replaces it.
        for key in ("snapshots", "missed", "nonorganic", "amendments"):
            if key in existing:
                post[key] = existing[key]
    left = leave_experiment(post)
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
    recorded = {"recorded": True, "root_id": post["root_id"]}
    if left:
        recorded["left_experiment"] = True
    return recorded


def cmd_due(repo: Repo, args) -> dict:
    at = now_arg(args.now)
    due, missed, pending = [], [], []
    for post in repo.posts():
        if post["missed"] or valid_snapshot(post):
            continue
        hours = age_hours(post, at)
        stage = due_stage(hours, post["retrospective"])
        if stage is None:
            continue
        row = {"root_id": post["root_id"], "slug": post["slug"], "age_hours": round(hours, 1),
               "card_ids": [c["id"] for c in post.get("cards", [])]}
        {"pending": pending, "due": due, "missed": missed}[stage].append(row)
    return {"due": due, "missed": missed, "pending": pending,
            "window_hours": [SNAPSHOT_MIN_H, SNAPSHOT_MAX_H]}


def cmd_due_reads(repo: Repo, args) -> dict:
    """The X reads the daily run should make now, and where each one moves the read cursors.

    Not `due`, which lists ledger posts awaiting a snapshot. Writes nothing: record-activity moves the cursors.
    The organic-metrics horizon is X's, so the caller passes it in (--horizon-days).
    """
    state = repo.state()
    handles = state["self_handles"]
    if args.backfill:
        need(args.fetched_at and args.since, "--backfill needs --fetched-at and --since")
        cursor = backfill_cursor(parse_time(args.fetched_at), parse_time(args.since))
        return {"stage": "backfill", "self_handles": handles,
                "cursor": {key: iso(at) for key, at in cursor.items()}}
    need(args.horizon_days is not None, "--horizon-days is required: X's organic-metrics horizon in days")
    # Whole seconds: iso() drops fractions, so a fractional clock would put the floor outside the horizon.
    now = now_arg(args.now).replace(microsecond=0)
    api = state.get("api", {})
    saved = {key: parse_time(api[key]) if api.get(key) else None for key in ("read48_until", "final_until")}
    windows = [{**w, "start": iso(w["start"]), "end": iso(w["end"]),
                "cursor": {key: iso(at) for key, at in w["cursor"].items()}}
               for w in read_windows(now, saved, args.horizon_days)]
    return {"now": iso(now), "windows": windows, "self_handles": handles}


def cmd_record_snapshot(repo: Repo, args) -> dict:
    state = repo.state()
    payload = read_json(Path(args.json))
    root_id = snapshot_root_id(payload)
    post = repo.post(root_id)
    observed = snapshot_observed(payload)
    hours = age_hours(post, observed)
    admission = admit_snapshot(post, hours, snapshot_is_final(payload))
    if admission.skip is not None:
        return {"recorded": False, "reason": admission.skip, "root_id": root_id}
    kind = admission.kind
    snap = snapshot_from_payload(payload, observed, hours, kind, state["self_handles"])
    post["snapshots"].append(snap)
    repo.save_post(post)
    return {"recorded": True, "root_id": root_id, "kind": kind, "age_hours": snap["age_hours"],
            "missing": snap["missing"]}


def cmd_record_activity(repo: Repo, args) -> dict:
    """One row per post, reply and quote, with a read per stage. Advances the read cursors last."""
    state = repo.state()
    payload = read_json(Path(args.json))
    stage, observed = activity_header(payload)
    months: dict[str, dict] = {}
    recorded = 0
    for item in activity_items(payload):
        month = item["created_at"][:7]
        if month not in months:
            path = repo.activity_dir / f"{month}.json"
            months[month] = read_json(path) if path.is_file() else {"month": month, "items": {}}
        row = months[month]["items"].setdefault(item["id"], {"id": item["id"]})
        row.update({k: item[k] for k in ("kind", "created_at", "conversation_id")})
        row["topics"] = item.get("topics", [])
        row["text"] = item.get("text", "")
        hours = (observed - parse_time(item["created_at"])).total_seconds() / 3600
        if stage == "final":
            need_final_age(hours)
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
    api.update(cursor_updates(payload))
    repo.save_state(state)
    return {"recorded": recorded, "stage": stage, "cursors": api}


def cmd_record_export(repo: Repo, args) -> dict:
    """Add an X analytics export's per-post numbers to the activity rows. The latest export wins,
    because X's numbers are cumulative per post."""
    path = Path(args.csv)
    need(path.is_file(), f"missing {path}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    need(bool(rows) and "Post id" in rows[0] and "New follows" in rows[0],
         "not an X analytics content export: no 'Post id' or 'New follows' column")
    at = iso(now_arg(args.now))
    months: dict[str, dict] = {}
    for month_path in sorted(repo.activity_dir.glob("????-??.json")) if repo.activity_dir.is_dir() else []:
        months[month_path.stem] = read_json(month_path)
    recorded, unknown = 0, 0
    for row in rows:
        item_id = str(row.get("Post id", "")).strip()
        month = next((m for m, data in months.items() if item_id in data["items"]), None)
        if month is None:
            unknown += 1
            continue
        numbers = {}
        for column, key in EXPORT_COLUMNS.items():
            raw = (row.get(column) or "0").replace(",", "").strip()
            need(raw.isdigit(), f"{item_id}: {column} is not a whole number")
            numbers[key] = int(raw)
        months[month]["items"][item_id].setdefault("reads", {})["export"] = {"at": at, "file": path.name, **numbers}
        recorded += 1
    for month, data in months.items():
        write_json(repo.activity_dir / f"{month}.json", data)
    return {"recorded": recorded, "not_in_activity": unknown, "file": path.name}


def _note_person(people: dict, user_id: str, item_id: str, at: str, how: str) -> None:
    """Keep each account's most recent interaction with us."""
    seen = people.get(user_id)
    if seen is None or parse_time(at) >= parse_time(seen["at"]):
        people[user_id] = {"item": item_id, "at": iso(parse_time(at)), "how": how}


def cmd_record_interactions(repo: Repo, args) -> dict:
    """Who replied to us, and who we replied to. Private: loop/followers/, gitignored."""
    repo.state()
    payload = read_json(Path(args.json))
    observed, mentions, targets, since = interaction_inputs(payload)
    data = repo.interactions()
    for author, conversation, mention_id, created_at, item in mentions:
        conv = data["conversations"].setdefault(conversation, {"at": created_at, "replies": []})
        if mention_id not in conv["replies"]:
            conv["replies"].append(mention_id)
        _note_person(data["people"], author, item, created_at, "replied")
    for user, item, at in targets:
        _note_person(data["people"], user, item, at, "replied_to")
    newest = newer_since_id(since, data["mentions_since_id"])
    if newest is not None:
        data["mentions_since_id"] = newest
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
    observed, ids = follower_inputs(payload)
    total = follower_total(payload, ids)
    day = observed.date().isoformat()
    earlier = [p for p in sorted(repo.private_dir.glob("followers-*.json")) if p.stem[len("followers-"):] < day]
    previous = set(read_json(earlier[-1])["ids"]) if earlier else None
    write_json(repo.private_dir / f"followers-{day}.json", {"at": iso(observed), "ids": ids})
    for old in sorted(repo.private_dir.glob("followers-*.json"))[:-FOLLOWER_FILES_KEPT]:
        old.unlink()
    row = {"date": day, "at": iso(observed), "followers": total}
    verified = verified_count(payload)
    if verified is not None:
        row["verified_followers"] = verified
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


def cmd_record_eligibility(repo: Repo, args) -> dict:
    """The two numbers on X's Original Content Rewards eligibility screen, as the operator reads them."""
    repo.state()
    for value, name in ((args.verified_followers, "--verified-followers"),
                        (args.qualified_impressions, "--qualified-impressions")):
        need(value.isdigit(), f"{name} must be a whole number")
    at = iso(now_arg(args.now))
    account = repo.account()
    account.setdefault("eligibility", []).append({
        "at": at, "verified_followers": int(args.verified_followers),
        "qualified_impressions": int(args.qualified_impressions)})
    write_json(repo.account_path, account)
    return account["eligibility"][-1]


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
        if past_window(age_hours(post, at)):
            post["missed"] = True
            repo.save_post(post)
            marked.append(post["root_id"])
    return {"marked_missed": marked}


def post_visits(post: dict) -> int:
    """A cohort post's organic profile visits, from the Snapshot the cohort used."""
    return (best_snapshot(post) or {}).get("organic", {}).get("profile_visits") or 0


def cmd_open_experiment(repo: Repo, args) -> dict:
    state = repo.state()
    need(open_experiment(state) is None, "an experiment is already open; one at a time")
    payload = read_json(Path(args.json))
    metric, effect, cohort = experiment_terms(payload)
    values, used = [], []
    for root_id in cohort:
        post = repo.post(root_id)
        need(not post.get("nonorganic"),
             f"{root_id} is marked non-organic ({(post.get('nonorganic') or {}).get('reason')}); it cannot be in a cohort")
        snap = best_snapshot(post)
        score = rates.score_primary(snap, metric)
        if score.value is not None and not score.below_floor:
            values.append(score.value)
            used.append({"root_id": root_id, "value": score.value, "kind": snap["kind"]})
    if metric in rates.PRIMARIES:
        need(len(values) >= MIN_COHORT, f"only {len(values)} cohort posts have {'an' if metric[0] in 'aeiou' else 'a'} {metric} "
                                        f"snapshot with {rates.MIN_IMPRESSIONS} or more organic impressions")
    else:
        need(len(values) >= MIN_COHORT, f"only {len(values)} cohort posts have a {metric} snapshot")
    if metric == "visit_rate":
        reason = rates.visit_screen([post_visits(repo.post(u["root_id"])) for u in used])
        need(reason is None, reason)
    texts = experiment_texts(payload)
    median = statistics.median(values)
    need(median > 0, f"the cohort's median {metric} is 0, so every post would clear the bar; "
                     "pick a measure the cohort actually has")
    exp = {
        "id": next_id("E", state["experiments"]),
        "question": texts["question"],
        "treatment": texts["treatment"],
        "control": texts["control"],
        "reference_facts": texts["reference_facts"],
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


def cmd_evaluate(repo: Repo, args) -> dict:
    state = repo.state()
    exp = open_experiment(state)
    if exp is None:
        return {"evaluated": False, "reason": "no open experiment"}
    consumed = {pid for rnd in exp["rounds"] for pid in rnd["posts"]}
    ready, notes = [], {}
    for post in repo.posts():
        if post.get("experiment") != exp["id"] or post.get("arm") != "treatment":
            continue
        if post["root_id"] in consumed or post.get("nonorganic"):
            continue
        score = rates.score_primary(valid_snapshot(post), exp["primary"])
        if score.value is None:
            continue
        if score.below_floor:
            notes[post["root_id"]] = "below_floor"
        ready.append((post["root_id"], score.value))
    at = iso(now_arg(args.now))
    state, result = evaluate_rounds(state, ready, at, notes)
    repo.save_state(state)
    return result


def cmd_next_slot(repo: Repo, args) -> dict:
    state = repo.state()
    at = now_arg(args.now)
    started = parse_time(state["started_at"])
    return next_slot(state, started, repo.posts(), at)


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
    last = parse_time(state["last_review_at"]) if state["last_review_at"] else None
    stale = [lesson["id"] for lesson in state["lessons"] if newly_stale(lesson, at, last)]
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
    need(lesson_outcome(lesson) == "adopted",
         f"{lesson['id']} is {lesson_outcome(lesson)}; only adopted lessons change rules")
    files = [f for f in args.files.split(",") if f]
    need(bool(files), "--files required")
    for name in files:
        need(not name.startswith(("/", "..")), f"file {name} must be inside the repo")
        need(name.startswith((".claude/skills/", "voice/")), f"{name} is not a rule file")
    changed = repo.git("status", "--porcelain", "--", *files).strip()
    need(bool(changed), "none of those files has changes to commit")
    repo.git("add", "--", *files)
    message = (f"feat(rules): apply {lesson['id']}\n\n{lesson['statement']}\nEvidence: {', '.join(lesson['evidence'])}\n"
               f"{lesson_basis(lesson, state['experiments'])}")
    repo.git("commit", "-m", message, "--", *files)
    sha = repo.git("rev-parse", "HEAD").strip()
    state["rules"].append({"lesson": lesson["id"], "commit": sha, "files": files,
                           "applied_at": iso(now_arg(args.now)), "undone": False, "revert_commit": None})
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


def daily_run_health(repo: Repo, at: datetime) -> dict:
    """Warnings from ledger/runs.log and the ledger: a stale or failed Daily run, a Final read about to be lost. Reads only."""
    log = repo.root / "ledger" / "runs.log"
    lines = log.read_text(encoding="utf-8").splitlines() if log.is_file() else []
    rows = repo.activity()
    at_risk = [(post["root_id"], parse_time(post["posted_at"]) + timedelta(days=FINAL_MAX_DAYS))
               for post in repo.posts()
               if final_at_risk(age_hours(post, at)) and not rows.get(post["root_id"], {}).get("reads", {}).get("final")]
    return {"warnings": health.warnings(at, health.last_runs(lines), at_risk)}


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
        "health": daily_run_health(repo, now_arg(args.now)),
        "stale_lessons": [l["id"] for l in state["lessons"] if lesson_is_stale(l, now_arg(args.now))],
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


def render(repo: Repo, now: str | None) -> None:
    if not repo.state_path.is_file():
        return
    at = now_arg(now)
    state = repo.state()
    posts = repo.posts()
    rows = repo.activity()
    account = repo.account()
    atomic_write(repo.ledger_dir / "SUMMARY.md", views.summary_text(posts, rows, account))
    atomic_write(repo.root / "experiments.md", views.experiments_text(state))
    atomic_write(repo.root / "learnings.md", views.learnings_text(state, at))


# ---------- cli ----------


COMMANDS = {
    "init": cmd_init,
    "record-post": cmd_record_post,
    "due": cmd_due,
    "due-reads": cmd_due_reads,
    "record-snapshot": cmd_record_snapshot,
    "mark-missed": cmd_mark_missed,
    "set-repliers-complete": cmd_set_repliers_complete,
    "mark-nonorganic": cmd_mark_nonorganic,
    "record-activity": cmd_record_activity,
    "record-interactions": cmd_record_interactions,
    "record-followers": cmd_record_followers,
    "set-lane": cmd_set_lane,
    "record-export": cmd_record_export,
    "record-eligibility": cmd_record_eligibility,
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
READ_ONLY = {"due", "due-reads", "next-slot", "lane-share", "review-due", "status", "validate"}


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
        if name == "due-reads":
            sp.add_argument("--horizon-days", type=float, help="how far back X still returns organic metrics")
            sp.add_argument("--backfill", action="store_true", help="the cursors for a backfill file instead")
            sp.add_argument("--fetched-at", help="with --backfill: when the file was fetched")
            sp.add_argument("--since", help="with --backfill: the earliest time the file covers")
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
        if name == "record-eligibility":
            sp.add_argument("--verified-followers", required=True)
            sp.add_argument("--qualified-impressions", required=True)
        if name == "record-export":
            sp.add_argument("--csv", required=True, help="X analytics content export")
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
            render(repo, args.now)
    except LoopError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
