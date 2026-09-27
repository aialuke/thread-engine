#!/usr/bin/env python3
"""Jev build-phase experiment runner (research code; nothing in scripts/ imports it).

    python3 research/jev-test/jev.py keys
    python3 research/jev-test/jev.py smoke
    python3 research/jev-test/jev.py run --set synthetic | stage2 | stagespam-demand | stagespam-tool
    python3 research/jev-test/jev.py compare --set <name>
    python3 research/jev-test/jev.py config --real-data on|off | --model <id>
    python3 research/jev-test/jev.py spend
    python3 research/jev-test/jev.py split --stage N --block B      (seal validation/final before scoring)
    python3 research/jev-test/jev.py run --set stage{N}-B{k}-validation [--replace]   (final only after freeze)
    python3 research/jev-test/jev.py repeat --set S [--posts 10 --times 3]   (fresh, uncached)
    python3 research/jev-test/jev.py rank --set S                   (one Choice per idea)
    python3 research/jev-test/jev.py freeze --note "..."            (one-way; needs the cut-off; unseals final)

Asks Jev (TypeSafe's System One model) the Discovery scoring rubric, one request per post, and
compares its answers with the labels the Discovery test already settled. The plan and the pass
and stop rules are README.md in this folder; the case for testing is
research/jev-build-time-evaluation-2026-09-27.md.

The key comes from the macOS Keychain (service thread-engine-typesafe, account api_key) and is
never printed. Every call is cached, logged and priced in private/ (gitignored). Calls stop at a
hard spend ceiling. Real Discovery posts are refused until the operator allows them
(`config --real-data on`); only made-up posts in synthetic.jsonl go out before that.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIVATE = HERE / "private"
DISCOVERY = HERE.parent / "discovery-test" / "private"

SERVICE, ACCOUNT = "thread-engine-typesafe", "api_key"
ENDPOINT = "https://api.typesafe.ai/v1/systemone"
PINNED, FALLBACK = "jev-1.13.0", "jev-latest"
PRICE_PER_TOKEN = 0.042 / 1_000_000       # input tokens; output is free (docs.typesafe.ai/models, 27 Sep 2026)
CEILING = 1.00                            # USD across every call this experiment makes
TIMEOUT = 10.0
MAX_RETRIES = 2
RETRY_STATUSES = {408, 429} | set(range(500, 600))
SCORES = ("relevant", "real", "useful")
REAL_SETS = ("stage2", "stagespam-demand", "stagespam-tool")
TOOL_SETS = {"stagespam-tool"}


class JevError(Exception):
    """A failed call or a missing key. Messages never contain the key."""


class Stop(Exception):
    """A deliberate stop: budget ceiling, real-data gate, missing file. Never retried."""


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------- key ----------


def keychain(runner: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> str:
    result = runner(["security", "find-generic-password", "-s", SERVICE, "-a", ACCOUNT, "-w"],
                    capture_output=True, text=True, check=False)
    if result.returncode != 0 or not result.stdout.strip():
        raise JevError(f"Keychain has no {ACCOUNT} under {SERVICE}, or the Keychain is locked")
    return result.stdout.strip()


def key_present(runner: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> bool:
    """Whether the key exists, without reading its value (no -w)."""
    result = runner(["security", "find-generic-password", "-s", SERVICE, "-a", ACCOUNT],
                    capture_output=True, text=True, check=False)
    return result.returncode == 0


# ---------- private/ store ----------


class Store:
    """private/: config, the call log, the budget log and the response cache."""

    def __init__(self, root: Path = PRIVATE) -> None:
        self.root = root
        (root / "cache").mkdir(parents=True, exist_ok=True)
        ignore = root / ".gitignore"
        if not ignore.exists():
            ignore.write_text("*\n!.gitignore\n", encoding="utf-8")
        self.calls, self.budget, self.config_path = root / "calls.jsonl", root / "budget.log", root / "config.json"

    @staticmethod
    def rows(path: Path) -> list[dict]:
        if not path.exists():
            return []
        # split on \n only: str.splitlines() also breaks on U+2028/U+0085 inside post text
        return [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line.strip()]

    @staticmethod
    def append(path: Path, row: dict) -> None:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def write_atomic(self, path: Path, text: str) -> None:
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)

    def config(self) -> dict:
        return json.loads(self.config_path.read_text(encoding="utf-8")) if self.config_path.exists() else {}

    def set_config(self, **values) -> dict:
        config = {**self.config(), **values}
        self.write_atomic(self.config_path, json.dumps(config, indent=1) + "\n")
        return config

    def spent(self) -> float:
        return round(sum(r.get("cost_usd") or 0 for r in self.rows(self.calls)), 6)

    def log_budget(self, event: str, **detail) -> None:
        extra = " ".join(f"{k}={v}" for k, v in detail.items())
        with self.budget.open("a", encoding="utf-8") as fh:
            fh.write(f"{now_iso()} spent={self.spent():.6f} {event} {extra}".rstrip() + "\n")

    def check_budget(self, reserve: float, what: str) -> None:
        """Refuses when the reserve would pass the ceiling, and always once a call has already pushed the
        spend over it (the real cost can exceed the reserve): nothing more goes out after an overshoot."""
        spent = self.spent()
        if spent > CEILING + 1e-12 or spent + reserve > CEILING + 1e-12:
            self.log_budget("REFUSED", what=what, reserve=f"{reserve:.6f}", ceiling=CEILING)
            raise Stop(f"Jev spend ceiling: ${spent:.4f} spent + ${reserve:.4f} reserve passes ${CEILING:.2f}. "
                       "Report what's learned and ask the operator before going on.")

    def cache_path(self, key: str) -> Path:
        return self.root / "cache" / f"{key}.json"


def cache_key(body: dict) -> str:
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


# ---------- client ----------


def retry_delay(attempt: int, headers, rand: Callable[[], float] = random.random) -> float:
    """Retry-After / retry-after-ms when the server sends one, else jittered backoff (0.5 s start, 5 s cap)."""
    if headers is not None:
        ms = headers.get("retry-after-ms")
        if ms:
            try:
                return min(float(ms) / 1000, 30.0)
            except ValueError:
                pass
        seconds = headers.get("Retry-After") or headers.get("retry-after")
        if seconds:
            try:
                return min(float(seconds), 30.0)
            except ValueError:
                pass
    base = min(0.5 * 2 ** attempt, 5.0)
    return base * (0.75 + 0.5 * rand())


def error_message(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", "replace")[:500]
    except Exception:  # noqa: BLE001 - the body is best-effort context only
        body = ""
    return f"HTTP {exc.code}: {body}".strip()


class Client:
    """POST to the System One endpoint with retries, a budget gate and a response cache."""

    def __init__(self, store: Store, key: str | None = None,
                 opener: Callable = urllib.request.urlopen, sleep: Callable[[float], None] = time.sleep,
                 runner: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> None:
        self.store, self._key, self.opener, self.sleep, self.runner = store, key, opener, sleep, runner

    @property
    def key(self) -> str:
        if self._key is None:
            self._key = keychain(self.runner)
        return self._key

    def post(self, body: dict) -> dict:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        for attempt in range(MAX_RETRIES + 1):
            request = urllib.request.Request(ENDPOINT, data=data, method="POST", headers={
                "Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
            try:
                with self.opener(request, timeout=TIMEOUT) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                if exc.code not in RETRY_STATUSES or attempt == MAX_RETRIES:
                    raise JevError(error_message(exc)) from None
                self.sleep(retry_delay(attempt, exc.headers))
            except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
                if attempt == MAX_RETRIES:
                    raise JevError(f"connection failed: {getattr(exc, 'reason', exc)}") from None
                self.sleep(retry_delay(attempt, None))
        raise JevError("unreachable")

    def ask(self, state, questions: dict, model: str, label: str = "", fresh: bool = False) -> dict:
        """One request. Returns {"model", "answers", "usage", "cached"}; a cache hit makes no call.
        fresh=True skips the cache both ways (repeatability checks) but is still logged and priced."""
        body = {"state": state, "model": model, "questions": questions}
        key = cache_key(body)
        path = self.store.cache_path(key)
        if path.exists() and not fresh:
            return {**json.loads(path.read_text(encoding="utf-8"))["response"], "cached": True}
        # reserve: 2 characters a token, rounded up (conservative; tokens usually run 3-4 characters). The real
        # cost is logged from usage after the call; if it overshoots the ceiling, check_budget refuses every later call.
        reserve = (len(json.dumps(body, ensure_ascii=False)) // 2 + 1) * PRICE_PER_TOKEN
        self.store.check_budget(reserve, label or key[:12])
        started = time.monotonic()
        try:
            response = self.post(body)
        except JevError as exc:
            self.store.log_budget("FAILED", what=label or key[:12], error=str(exc)[:120].replace(" ", "_"))
            raise
        elapsed = round(time.monotonic() - started, 3)
        usage = response.get("usage") or {}
        cost = round((usage.get("input_tokens") or 0) * PRICE_PER_TOKEN, 8)
        if not fresh:
            self.store.write_atomic(path, json.dumps({"request": body, "response": response}, ensure_ascii=False) + "\n")
        self.store.append(self.store.calls, {
            "at": now_iso(), "label": label, "cache_key": key, "model_requested": model,
            "model": response.get("model"), "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"), "cost_usd": cost, "elapsed_s": elapsed})
        self.store.log_budget("call", what=label or key[:12], model=response.get("model"), cost=f"{cost:.8f}")
        return {**response, "cached": False}


# ---------- questions ----------


def load_questions(path: Path = HERE / "questions.json") -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def questions_for(job: str, spec: dict | None = None) -> dict:
    """The rubric for one job: the shared questions plus that job's `useful`."""
    spec = spec or load_questions()
    if job not in spec["useful"]:
        raise Stop(f"no `useful` question for job {job!r}")
    return {**spec["shared"], "useful": spec["useful"][job]}


def request_questions(job: str, spec: dict | None = None) -> dict:
    """What a Jev request asks: the rubric plus the diagnostics (judged independently, never a pass measure)."""
    spec = spec or load_questions()
    return {**questions_for(job, spec), **spec.get("diagnostics", {})}


def questions_hash(questions: dict) -> str:
    """The version of a question set; every answer records it."""
    return hashlib.sha256(json.dumps(questions, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]


def job_of(set_name: str, row: dict) -> str:
    """stage1 -> worth-joining; stage3 and stagespam-tool -> tool; everything else -> demand."""
    if row.get("job"):
        return row["job"]
    if set_name in TOOL_SETS or set_name.startswith("stage3-"):
        return "tool"
    if set_name.startswith("stage1-"):
        return "worth-joining"
    return "demand"


def state_of(row: dict) -> dict:
    """The packet every rater sees: idea and post text, plus reply count and age for Worth-joining posts."""
    state = {"idea": row["idea"], "post": row["text"]}
    for field in ("replies", "age_hours"):
        if row.get(field) is not None:
            state[field] = row[field]
    return state


# One validator for Jev and the peer raters (raters.py imports these), so every rater's answer passes
# the same checks: booleans are not probabilities, and a score or choice must sum to 1 within SUM_TOLERANCE.
SUM_TOLERANCE = 0.05


def is_prob(p) -> bool:
    return isinstance(p, (int, float)) and not isinstance(p, bool) and 0.0 <= p <= 1.0


def options(question: dict) -> list[str]:
    """The levels of a score ("0", "1", "2") or the options of a choice."""
    criteria = question.get("criteria")
    if question["type"] == "score":
        return [str(n) for n in range(len(criteria) if isinstance(criteria, list) else 3)]
    return list(criteria) if isinstance(criteria, dict) else list(criteria or [])


def check_answer(qid: str, question: dict, answer) -> tuple[dict | None, str | None]:
    """A cleaned answer (probabilities renormalised to sum to 1; a choice's pick recomputed), or a problem."""
    if not isinstance(answer, dict):
        return None, f"{qid}: missing"
    if question["type"] == "noul":
        p = answer.get("noul")
        return ({"noul": float(p)}, None) if is_prob(p) else (None, f"{qid}: noul must be in [0, 1]")
    probs = answer.get("probabilities")
    want = options(question)
    if not isinstance(probs, dict) or set(map(str, probs)) != set(want):
        return None, f"{qid}: probabilities must cover exactly {want}"
    if not all(is_prob(p) for p in probs.values()):
        return None, f"{qid}: every probability must be in [0, 1]"
    total = sum(probs.values())
    if abs(total - 1.0) > SUM_TOLERANCE:
        return None, f"{qid}: probabilities sum to {total:.3f}"
    clean = {o: probs[o] / total for o in want}
    out = {"probabilities": clean}
    if question["type"] == "choice":
        best = max(want, key=lambda o: (clean[o], -want.index(o)))
        out.update(choice=best, confidence=clean[best])
    return out, None


def clean_answers(answers: dict | None, questions: dict) -> tuple[dict | None, list[str]]:
    """(cleaned answers, problems). Any problem makes the whole row unavailable, never a no."""
    if not isinstance(answers, dict):
        return None, ["no answers"]
    clean, problems = {}, []
    for qid, question in questions.items():
        got, problem = check_answer(qid, question, answers.get(qid))
        if problem:
            problems.append(problem)
        else:
            clean[qid] = {**answers[qid], **got}
    return (None if problems else clean), problems


def answer_problems(answers: dict | None, questions: dict) -> list[str]:
    """Every expected question present and in range; anything else makes the row unavailable, never a no."""
    return clean_answers(answers, questions)[1]


# ---------- sets ----------


BLOCK_SET = re.compile(r"^stage([123])-(B\d+)-(validation|final)$")
BLOCK_IN = re.compile(r"stage([123])-(B\d+)-(validation|final)$")      # a set name or a corpus file stem
COVERAGE_RULES = ("p_good_0.5", "good_level")                           # the two curves raters.py compare reports


def thresholds(path: Path | None = None) -> dict:
    path = path or HERE / "thresholds.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def split_files(stage, block: str, splits: Path) -> tuple[dict, Path]:
    """({half: path}, manifest path) for one block's split."""
    halves = {h: splits / f"stage{stage}-{block}-{h}.jsonl" for h in ("validation", "final")}
    return halves, splits / f"split-stage{stage}-{block}.json"


def split_leftovers(stage, block: str, splits: Path) -> list[Path]:
    """Halves or temp files of a split that never wrote its manifest."""
    halves, manifest = split_files(stage, block, splits)
    paths = [*halves.values(), manifest]
    return [p for p in [*paths, *(p.with_name(p.name + ".tmp") for p in paths)] if p.exists() and p != manifest]


def check_block(set_name: str | None = None, corpus: Path | None = None, root: Path = PRIVATE,
                spec: dict | None = None) -> None:
    """The one seal every reader of block sets goes through (jev load_set, raters brief/ingest/compare,
    labelling panel_typed). A block set, named or given as a corpus file, must have its split manifest (no
    manifest means not sealed). A final set is refused until thresholds.json (next to root) is frozen with a
    cut-off, and then whenever the questions its job would ask now hash differently from the frozen ones."""
    targets = []
    if set_name:
        targets.append((set_name, root / "splits"))
    if corpus is not None:
        corpus = Path(corpus)
        targets.append((corpus.stem, corpus.parent))
    for name, splits in targets:
        block = BLOCK_IN.search(name)
        if not block:
            if name.endswith("-final"):
                raise Stop(f"{name!r} looks like a final set but isn't stage{{N}}-B{{k}}-final; refused")
            continue
        stage, b, half = block.groups()
        _, manifest = split_files(stage, b, splits)
        if not manifest.exists():
            leftovers = split_leftovers(stage, b, splits)
            detail = (" A partial split is there with no manifest; remove these files and split again: "
                      + ", ".join(str(p) for p in leftovers)) if leftovers else ""
            raise Stop(f"stage{stage}-{b} is not sealed: {manifest} is missing.{detail}")
        if half != "final":
            continue
        frozen = thresholds(root.parent / "thresholds.json")
        if not frozen.get("frozen"):
            raise Stop("the final set stays sealed until thresholds.json is frozen (freeze --note ...)")
        if frozen.get("frozen_coverage_threshold") is None:
            raise Stop("thresholds.json is frozen without a cut-off; the final set stays sealed")
        job = job_of(f"stage{stage}-{b}-{half}", {})
        now = questions_hash(request_questions(job, spec or load_questions()))
        if (frozen.get("questions") or {}).get(job) != now:
            raise Stop(f"the {job} questions changed after the freeze ({now} now, "
                       f"{(frozen.get('questions') or {}).get(job)} frozen); the final set stays sealed")


def load_set(set_name: str, store: Store, discovery: Path = DISCOVERY) -> list[dict]:
    """[{id, idea, text, job, label?}]. Real sets need the operator's go-ahead in private/config.json.
    Block sets (stage{N}-B{k}-validation|final) come from private/splits/; final needs frozen thresholds."""
    if set_name == "synthetic":
        return [{**r, "label": r.get("label")} for r in Store.rows(HERE / "synthetic.jsonl")]
    block = BLOCK_SET.match(set_name)
    if set_name not in REAL_SETS and not block:
        raise Stop(f"unknown set {set_name!r}: synthetic, one of {', '.join(REAL_SETS)}, or stage{{N}}-B{{k}}-validation|final")
    if not store.config().get("real_data"):
        raise Stop("Real Discovery posts stay off TypeSafe until the operator allows it "
                   "(config --real-data on, run only on the operator's say-so). Use --set synthetic.")
    if block:
        check_block(set_name, root=store.root)
        corpus = store.root / "splits" / f"{set_name}.jsonl"
        if not corpus.exists():
            raise Stop(f"{corpus} is missing: run split --stage {block.group(1)} --block {block.group(2)} first")
    else:
        corpus = discovery / f"corpus-{set_name}.jsonl"
        if not corpus.exists():
            raise Stop(f"{corpus} is missing (Discovery private data is deleted by 26 Mar 2027)")
    return [{**r, "job": job_of(set_name, r)} for r in Store.rows(corpus)]


def backup(path: Path) -> Path:
    """Move a file aside to <name>.<UTC time>.bak (never overwriting an earlier backup)."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target, n = path.with_name(f"{path.name}.{stamp}.bak"), 1
    while target.exists():
        target, n = path.with_name(f"{path.name}.{stamp}-{n}.bak"), n + 1
    os.replace(path, target)
    return target


def run_set(set_name: str, client: Client, store: Store, model: str, spec: dict | None = None,
            discovery: Path = DISCOVERY, out: Callable[[str], None] = print, replace: bool = False) -> dict:
    """answers-{set}.jsonl is rebuilt from the cache on every run, so a rerun may rewrite it; but never over
    answers asked with other questions: that needs a new set name, or replace=True (old file kept as .bak)."""
    rows = load_set(set_name, store, discovery)
    spec = spec or load_questions()
    path = store.root / f"answers-{set_name}.jsonl"
    want = {row["id"]: questions_hash(request_questions(row["job"], spec)) for row in rows}
    changed = [r.get("id") for r in Store.rows(path) if r.get("questions") != want.get(r.get("id"))]
    if changed and not replace:
        raise Stop(f"{path.name} has {len(changed)} row(s) asked with other questions or not in this set "
                   f"(first: {changed[0]}); run under a new set name, or --replace to keep the old file as .bak")
    if changed:
        backup(path)
    results, new, cached, unavailable = [], 0, 0, 0
    for row in rows:
        questions = request_questions(row["job"], spec)
        response = client.ask(state_of(row), questions, model, label=f"{set_name}:{row['id']}")
        cached, new = cached + response["cached"], new + (not response["cached"])
        clean, problems = clean_answers(response.get("answers"), questions)
        unavailable += bool(problems)
        results.append({"id": row["id"], "job": row["job"], "model": response.get("model"),
                        "questions": questions_hash(questions), "answers": clean, "usage": response.get("usage"),
                        **({"unavailable": True, "reason": "; ".join(problems)} if problems else {})})
    store.write_atomic(path, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in results))
    models = sorted({r["model"] for r in results if r["model"]})
    summary = {"set": set_name, "posts": len(results), "new_calls": new, "cached": cached,
               "unavailable": unavailable, "models": models, "spent_usd": store.spent(), "ceiling_usd": CEILING}
    if any(m != model for m in models) and model != FALLBACK:
        summary["warning"] = f"asked for {model}, served {', '.join(models)}"
    out(json.dumps(summary, indent=1))
    return summary


# ---------- split, repeat, rank, freeze ----------


DEV_KEYS = ("stage2", "stagespam-demand", "stagespam-tool")


def posts_table(discovery: Path = DISCOVERY) -> dict:
    """post_id -> {conversation_id, author_id} from the harness's post table."""
    path = discovery / "posts.csv"
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as fh:
        return {r["post_id"]: {"conversation_id": r.get("conversation_id") or "", "author_id": r.get("author_id") or ""}
                for r in csv.DictReader(fh)}


def group_of(post_id: str, conversation_id: str | None) -> str:
    """Posts in one conversation stay together; a post with no conversation id is its own group."""
    return f"c:{conversation_id}" if conversation_id else f"p:{post_id}"


def half_of(group: str) -> str:
    return "validation" if int(hashlib.sha256(group.encode("utf-8")).hexdigest()[:8], 16) % 2 == 0 else "final"


def split(stage: int, block: str, store: Store, discovery: Path = DISCOVERY) -> dict:
    """Seal a new block into validation and final, before any scoring. Drops posts whose post or
    conversation is already in development (the 298 existing rows); reports author overlap."""
    out_dir = store.root / "splits"
    names, manifest = split_files(stage, block, out_dir)
    if manifest.exists():
        raise Stop(f"split for stage{stage}-{block} already exists; it is sealed")
    leftovers = split_leftovers(stage, block, out_dir)
    if leftovers:
        raise Stop(f"a partial split for stage{stage}-{block} is here with no manifest, so it is not sealed. "
                   "Remove these files, then split again: " + ", ".join(str(p) for p in leftovers))
    corpus_path = discovery / f"corpus-stage{stage}-{block}.jsonl"
    key_path = discovery / f"corpus-key-stage{stage}-{block}.json"
    if not corpus_path.exists() or not key_path.exists():
        raise Stop(f"build the block corpus first (harness corpus --stage {stage} --block {block})")
    table = posts_table(discovery)
    dev_posts, dev_convs, dev_authors = set(), set(), set()
    for name in DEV_KEYS:
        path = discovery / f"corpus-key-{name}.json"
        if path.exists():
            for v in json.loads(path.read_text(encoding="utf-8")).values():
                meta = table.get(v["post_id"], {})
                dev_posts.add(v["post_id"])
                if meta.get("conversation_id"):
                    dev_convs.add(meta["conversation_id"])
                if meta.get("author_id"):
                    dev_authors.add(meta["author_id"])
    key = json.loads(key_path.read_text(encoding="utf-8"))
    halves: dict[str, list] = {"validation": [], "final": []}
    dropped = Counter()
    authors_seen = 0
    for row in Store.rows(corpus_path):
        k = key[row["id"]]
        meta = table.get(k["post_id"], {})
        conv = k.get("conversation_id") or meta.get("conversation_id") or ""
        author = k.get("author_id") or meta.get("author_id") or ""
        if k["post_id"] in dev_posts:
            dropped["post already in development"] += 1
            continue
        if conv and conv in dev_convs:
            dropped["conversation already in development"] += 1
            continue
        authors_seen += bool(author and author in dev_authors)
        g = group_of(k["post_id"], conv)
        halves[half_of(g)].append({**row, "group": g})
    out_dir.mkdir(parents=True, exist_ok=True)
    info = {"stage": stage, "block": block, "created": now_iso(), "rule": "sha256(group) % 2: 0 validation, 1 final",
            "validation": len(halves["validation"]), "final": len(halves["final"]),
            "dropped": dict(dropped), "authors_also_in_development": authors_seen,
            "groups": {h: len({r["group"] for r in rows}) for h, rows in halves.items()}}
    # all three go to temp names first; published only once every one is written, the manifest last
    texts = {**{names[h]: "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows) for h, rows in halves.items()},
             manifest: json.dumps(info, indent=1) + "\n"}
    for path, text in texts.items():
        path.with_name(path.name + ".tmp").write_text(text, encoding="utf-8")
    for path in texts:
        os.replace(path.with_name(path.name + ".tmp"), path)
    return info


def repeat(set_name: str, client: Client, store: Store, model: str, n: int = 10, times: int = 3,
           spec: dict | None = None, discovery: Path = DISCOVERY) -> dict:
    """Fresh (uncached) re-asks of a fixed subset: does Jev give the same answers twice?"""
    rows = sorted(load_set(set_name, store, discovery), key=lambda r: hashlib.sha256(r["id"].encode()).hexdigest())[:n]
    spec = spec or load_questions()
    out = store.root / f"repeats-{set_name}.jsonl"
    done = {(r.get("id"), r.get("try")): r.get("questions") for r in Store.rows(out)}
    skipped = 0
    for row in rows:
        questions = request_questions(row["job"], spec)
        qhash = questions_hash(questions)
        for t in range(times):
            if (row["id"], t) in done:
                if done[(row["id"], t)] != qhash:
                    raise Stop(f"{out.name} already has {row['id']} try {t} asked with other questions; "
                               "use a new set name")
                skipped += 1
                continue
            response = client.ask(state_of(row), questions, model, label=f"repeat:{set_name}:{row['id']}:{t}", fresh=True)
            clean, problems = clean_answers(response.get("answers"), questions)
            store.append(out, {"id": row["id"], "try": t, "model": response.get("model"), "questions": qhash,
                               "answers": clean, **({"unavailable": True, "reason": "; ".join(problems)} if problems else {})})
    return {"set": set_name, "posts": len(rows), "times": times, "skipped_already_done": skipped,
            "file": out.name, "spent_usd": store.spent()}


def rank(set_name: str, client: Client, store: Store, model: str, discovery: Path = DISCOVERY) -> dict:
    """One Choice per idea over its posts: which would you most want to join? (Worth-joining sets, 2-255 posts.)"""
    rows = load_set(set_name, store, discovery)
    by_idea: dict[str, list] = {}
    for r in rows:
        by_idea.setdefault(r["idea"], []).append(r)
    results = {}
    for idea, posts in sorted(by_idea.items()):
        if not 2 <= len(posts) <= 255:
            results[idea] = {"skipped": f"{len(posts)} posts"}
            continue
        # Asked in both candidate orders and averaged: order changed 3-11% of Jev's picks (Li et al.).
        runs = []
        for order in (posts, list(reversed(posts))):
            # a list, not a dict: the cache key sorts dict keys, which would make both orders one request
            state = {"idea": idea, "candidates": [{"id": p["id"], **{k: v for k, v in state_of(p).items() if k != "idea"}}
                                                  for p in order]}
            question = {"best": {"type": "choice",
                                 "instructions": "Which post in `candidates` would you most want to join with a specific or witty reply, for `idea`?",
                                 "criteria": {p["id"]: None for p in order}}}
            response = client.ask(state, question, model, label=f"rank:{set_name}:{idea[:30]}")
            runs.append(((response.get("answers") or {}).get("best") or {}).get("probabilities") or {})
        ids = [p["id"] for p in posts]
        averaged = {i: round(sum(r.get(i, 0.0) for r in runs) / len(runs), 4) for i in ids}
        top = sorted(ids, key=lambda i: -averaged[i])
        results[idea] = {"probabilities": averaged, "top3": top[:3],
                         "orders_agree_on_best": len({max(r, key=r.get) for r in runs if r}) == 1}
    store.write_atomic(store.root / f"ranks-{set_name}.json", json.dumps(results, indent=1, ensure_ascii=False) + "\n")
    return {"set": set_name, "ideas": len(results), "spent_usd": store.spent()}


def reworded(set_name: str, client: Client, store: Store, model: str, n: int = 30,
             spec: dict | None = None, alt_path: Path | None = None, discovery: Path = DISCOVERY) -> dict:
    """Rewording check: a second wording of relevant, real and useful (questions-reworded.json) on a fixed
    subset. Reworded rubrics moved Jev more than repeats did (Li et al.), so report how often good flips."""
    spec = spec or load_questions()
    alt = json.loads((alt_path or HERE / "questions-reworded.json").read_text(encoding="utf-8"))
    rows = sorted(load_set(set_name, store, discovery), key=lambda r: hashlib.sha256(r["id"].encode()).hexdigest())[:n]
    flips, compared, out = 0, 0, []
    for row in rows:
        base = questions_for(row["job"], spec)
        swapped = {**base, **{k: v for k, v in alt["shared"].items() if k in base}}
        if "useful" in alt and row["job"] in alt["useful"]:
            swapped["useful"] = alt["useful"][row["job"]]
        a = clean_answers(client.ask(state_of(row), base, model, label=f"reword-base:{set_name}:{row['id']}").get("answers"), base)[0]
        b = clean_answers(client.ask(state_of(row), swapped, model, label=f"reword-alt:{set_name}:{row['id']}").get("answers"), swapped)[0]
        good = [None if not x else all(level(x.get(k)) == v for k, v in (("relevant", 2), ("real", 2)))
                and (level(x.get("useful")) or 0) >= 1 for x in (a, b)]
        if None not in good:
            compared += 1
            flips += good[0] != good[1]
        out.append({"id": row["id"], "good_base": good[0], "good_reworded": good[1]})
    store.write_atomic(store.root / f"reworded-{set_name}.jsonl", "".join(json.dumps(r) + "\n" for r in out))
    return {"set": set_name, "posts": len(rows), "compared": compared, "flips": flips,
            "flip_pct": round(100 * flips / compared, 1) if compared else None, "spent_usd": store.spent()}


def freeze(note: str, path: Path | None = None) -> dict:
    """Record that the rubric and cut-offs are frozen: unseals the final sets. One-way. Refused until
    thresholds.json has the coverage cut-off chosen on validation; the cut-off and its rule are recorded
    with the question hashes, and raters.py compare applies them once to final."""
    path = path or HERE / "thresholds.json"
    data = thresholds(path)
    if data.get("frozen"):
        raise Stop(f"already frozen on {data.get('frozen_at')}")
    cut = data.get("coverage_threshold")
    if isinstance(cut, bool) or not isinstance(cut, (int, float)) or not 0.5 <= cut <= 1:
        raise Stop("set coverage_threshold in thresholds.json first: the confidence cut-off chosen on "
                   "validation, between 0.5 and 1. The final set stays sealed until then")
    rule = data.get("coverage_rule", "p_good_0.5")
    if rule not in COVERAGE_RULES:
        raise Stop(f"coverage_rule must be one of {', '.join(COVERAGE_RULES)}")
    spec = load_questions()
    data.update(frozen=True, frozen_at=now_iso(), note=note, frozen_coverage_threshold=cut, frozen_coverage_rule=rule,
                questions={job: questions_hash(request_questions(job, spec)) for job in spec["useful"]})
    path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    return data


# ---------- compare ----------


def level(answer: dict | None) -> int | None:
    """The most probable Score level (ties go to the lower level)."""
    probs = (answer or {}).get("probabilities") or {}
    if not probs:
        return None
    return min(((-p, int(k)) for k, p in probs.items()))[1]


def auc(pos: list[float], neg: list[float]) -> float | None:
    """Probability a random positive outranks a random negative (ties count half)."""
    if not pos or not neg:
        return None
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in pos for n in neg)
    return round(wins / (len(pos) * len(neg)), 3)


def pct(hits: int, total: int) -> float | None:
    return round(100 * hits / total, 1) if total else None


def agreement(pred: dict, truth: dict, ids: list[str]) -> dict:
    """pred/truth: id -> {relevant, real, useful, type, act}. Only ids both sides have count."""
    out = {}
    for dim in SCORES:
        pairs = [(pred[i].get(dim), truth[i].get(dim)) for i in ids
                 if i in pred and pred[i].get(dim) is not None and truth[i].get(dim) is not None]
        out[dim] = {"n": len(pairs), "exact_pct": pct(sum(a == b for a, b in pairs), len(pairs)),
                    "within_one_pct": pct(sum(abs(a - b) <= 1 for a, b in pairs), len(pairs))}
    for dim in ("type", "act"):
        pairs = [(pred[i].get(dim), truth[i].get(dim)) for i in ids
                 if i in pred and pred[i].get(dim) is not None and truth[i].get(dim) is not None]
        out[dim] = {"n": len(pairs), "exact_pct": pct(sum(a == b for a, b in pairs), len(pairs))}
    return out


def jev_labels(answers: list[dict]) -> dict:
    labels = {}
    for row in answers:
        a = row.get("answers") or {}
        act_p = (a.get("act") or {}).get("noul")
        labels[row["id"]] = {
            **{dim: level(a.get(dim)) for dim in SCORES},
            "type": (a.get("type") or {}).get("choice"),
            "type_confidence": (a.get("type") or {}).get("confidence"),
            "act_p": act_p, "act": None if act_p is None else act_p >= 0.5}
    return labels


def compare_set(set_name: str, store: Store, discovery: Path = DISCOVERY) -> dict:
    check_block(set_name, root=store.root)
    answers = Store.rows(store.root / f"answers-{set_name}.jsonl")
    if not answers:
        raise Stop(f"no answers for {set_name}: run it first")
    jev = jev_labels(answers)
    if set_name == "synthetic":
        truth = {r["id"]: r["label"] for r in Store.rows(HERE / "synthetic.jsonl") if r.get("label")}
        groups, baselines = {"all": list(truth)}, {}
    else:
        final = {r["id"]: r for r in Store.rows(discovery / f"final-scores-{set_name}.jsonl")}
        truth = final
        settled = [i for i, r in final.items() if r.get("source_of_label") in ("agreed", "adjudicated")]
        groups = {"settled (agreed or adjudicated)": settled,
                  "adjudicated only": [i for i in settled if final[i]["source_of_label"] == "adjudicated"],
                  "first only (Codex's own label)": [i for i, r in final.items() if r.get("source_of_label") == "first only"]}
        # both baselines voted on the final labels, so their agreement is inflated; Jev never voted
        baselines = {"first scorer (Codex, voted)": {r["id"]: r for r in Store.rows(discovery / f"scores-{set_name}.jsonl")},
                     "second scorer (Claude, voted)": {r["id"]: r for r in Store.rows(discovery / f"second-scores-{set_name}.jsonl")}}
    report = {"set": set_name, "models": sorted({str(r["model"]) for r in answers if r.get("model")}), "groups": {}}
    for name, ids in groups.items():
        entry = {"posts": len(ids), "jev": agreement(jev, truth, ids)}
        for label, rows in baselines.items():
            entry[label] = agreement(rows, truth, ids)
        act_true = [jev[i]["act_p"] for i in ids if i in jev and truth[i].get("act") is True and jev[i]["act_p"] is not None]
        act_false = [jev[i]["act_p"] for i in ids if i in jev and truth[i].get("act") is False and jev[i]["act_p"] is not None]
        entry["jev"]["act_auc"] = auc(act_true, act_false)
        misses = Counter((truth[i].get("type"), jev[i]["type"]) for i in ids
                         if i in jev and truth[i].get("type") != jev[i]["type"])
        entry["jev"]["type_confusions"] = [f"{t} -> {p}: {n}" for (t, p), n in misses.most_common(5)]
        report["groups"][name] = entry
    if set_name != "synthetic":
        # do contested posts look contested to Jev? distance of act_p from 0.5, adjudicated vs agreed
        def spread(source: str) -> float | None:
            vals = [abs(jev[i]["act_p"] - 0.5) for i, r in truth.items()
                    if r.get("source_of_label") == source and i in jev and jev[i]["act_p"] is not None]
            return round(sum(vals) / len(vals), 3) if vals else None
        report["act_certainty"] = {"agreed": spread("agreed"), "adjudicated": spread("adjudicated"),
                                   "note": "mean |act_p - 0.5|; lower on adjudicated posts means Jev finds them harder too"}
    store.write_atomic(store.root / f"compare-{set_name}.json", json.dumps(report, indent=1) + "\n")
    return report


# ---------- smoke ----------


SMOKE_STATE = {"idea": "people asking for a free alternative to a paid creator or developer tool",
               "post": "Is there anything free that does what Loom does? Our team can't justify another subscription."}
SMOKE_QUESTIONS = {"asks": {"type": "noul", "instructions": "Is the author of `post` asking for a free alternative to a paid tool?"}}


def smoke(client: Client, store: Store) -> dict:
    """One made-up Noul. Tries the pinned version first and falls back to the alias if it's refused."""
    result = {}
    for model in (PINNED, FALLBACK):
        try:
            response = client.ask(SMOKE_STATE, SMOKE_QUESTIONS, model, label=f"smoke:{model}")
        except JevError as exc:
            result[model] = {"error": str(exc)}
            continue
        result[model] = {"served_by": response.get("model"), "noul": response["answers"]["asks"]["noul"],
                         "usage": response.get("usage"), "cached": response["cached"]}
        store.set_config(model=model, model_checked=now_iso())
        result["pinned_held"] = model == PINNED and response.get("model") == PINNED
        break
    result["spent_usd"] = store.spent()
    return result


# ---------- CLI ----------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Jev build-phase experiment runner.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("keys")
    sub.add_parser("smoke")
    sub.add_parser("spend")
    for name in ("run", "compare", "rank"):
        p = sub.add_parser(name)
        p.add_argument("--set", required=True, dest="set_name")
        if name == "run":
            p.add_argument("--replace", action="store_true",
                           help="rewrite answers asked with other questions (the old file is kept as .bak)")
    p = sub.add_parser("reworded")
    p.add_argument("--set", required=True, dest="set_name")
    p.add_argument("--posts", type=int, default=30)
    p = sub.add_parser("repeat")
    p.add_argument("--set", required=True, dest="set_name")
    p.add_argument("--posts", type=int, default=10)
    p.add_argument("--times", type=int, default=3)
    p = sub.add_parser("split")
    p.add_argument("--stage", type=int, required=True, choices=(1, 2, 3))
    p.add_argument("--block", required=True)
    p = sub.add_parser("freeze")
    p.add_argument("--note", required=True)
    p = sub.add_parser("config")
    p.add_argument("--real-data", choices=("on", "off"))
    p.add_argument("--model")
    args = parser.parse_args(argv)

    if args.command == "keys":
        print(json.dumps({"service": SERVICE, "account": ACCOUNT, "present": key_present()}))
        return 0
    store = Store()
    try:
        if args.command == "config":
            changes = {}
            if args.real_data:
                changes.update(real_data=args.real_data == "on", real_data_changed=now_iso())
            if args.model:
                changes["model"] = args.model
            print(json.dumps(store.set_config(**changes) if changes else store.config(), indent=1))
        elif args.command == "spend":
            print(json.dumps({"spent_usd": store.spent(), "ceiling_usd": CEILING,
                              "calls": len(store.rows(store.calls))}))
        elif args.command == "smoke":
            print(json.dumps(smoke(Client(store), store), indent=1))
        elif args.command == "run":
            run_set(args.set_name, Client(store), store, store.config().get("model", PINNED), replace=args.replace)
        elif args.command == "compare":
            print(json.dumps(compare_set(args.set_name, store), indent=1))
        elif args.command == "split":
            print(json.dumps(split(args.stage, args.block, store), indent=1))
        elif args.command == "repeat":
            print(json.dumps(repeat(args.set_name, Client(store), store, store.config().get("model", PINNED),
                                    args.posts, args.times), indent=1))
        elif args.command == "reworded":
            print(json.dumps(reworded(args.set_name, Client(store), store, store.config().get("model", PINNED), args.posts), indent=1))
        elif args.command == "rank":
            print(json.dumps(rank(args.set_name, Client(store), store, store.config().get("model", PINNED)), indent=1))
        elif args.command == "freeze":
            print(json.dumps(freeze(args.note), indent=1))
    except (Stop, JevError) as exc:
        print(f"stopped: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
