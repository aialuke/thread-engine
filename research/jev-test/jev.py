#!/usr/bin/env python3
"""Jev build-phase experiment runner (research code; nothing in scripts/ imports it).

    python3 research/jev-test/jev.py keys
    python3 research/jev-test/jev.py smoke
    python3 research/jev-test/jev.py run --set synthetic | stage2 | stagespam-demand | stagespam-tool
    python3 research/jev-test/jev.py compare --set <name>
    python3 research/jev-test/jev.py config --real-data on|off | --model <id>
    python3 research/jev-test/jev.py spend

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
import hashlib
import json
import os
import random
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
        spent = self.spent()
        if spent + reserve > CEILING + 1e-12:
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

    def ask(self, state, questions: dict, model: str, label: str = "") -> dict:
        """One request. Returns {"model", "answers", "usage", "cached"}; a cache hit makes no call."""
        body = {"state": state, "model": model, "questions": questions}
        key = cache_key(body)
        path = self.store.cache_path(key)
        if path.exists():
            return {**json.loads(path.read_text(encoding="utf-8"))["response"], "cached": True}
        # reserve: about 3 characters a token, rounded up; the real cost is logged from usage after the call
        reserve = (len(json.dumps(body, ensure_ascii=False)) // 3 + 1) * PRICE_PER_TOKEN
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


def job_of(set_name: str, row: dict) -> str:
    return row.get("job") or ("tool" if set_name in TOOL_SETS else "demand")


# ---------- sets ----------


def load_set(set_name: str, store: Store, discovery: Path = DISCOVERY) -> list[dict]:
    """[{id, idea, text, job, label?}]. Real sets need the operator's go-ahead in private/config.json."""
    if set_name == "synthetic":
        return [{**r, "label": r.get("label")} for r in Store.rows(HERE / "synthetic.jsonl")]
    if set_name not in REAL_SETS:
        raise Stop(f"unknown set {set_name!r}: synthetic or one of {', '.join(REAL_SETS)}")
    if not store.config().get("real_data"):
        raise Stop("Real Discovery posts stay off TypeSafe until the operator allows it "
                   "(config --real-data on, run only on the operator's say-so). Use --set synthetic.")
    corpus = discovery / f"corpus-{set_name}.jsonl"
    if not corpus.exists():
        raise Stop(f"{corpus} is missing (Discovery private data is deleted by 26 Mar 2027)")
    return [{**r, "job": job_of(set_name, r)} for r in Store.rows(corpus)]


def run_set(set_name: str, client: Client, store: Store, model: str, spec: dict | None = None,
            discovery: Path = DISCOVERY, out: Callable[[str], None] = print) -> dict:
    rows = load_set(set_name, store, discovery)
    spec = spec or load_questions()
    results, new, cached = [], 0, 0
    for row in rows:
        state = {"idea": row["idea"], "post": row["text"]}
        response = client.ask(state, questions_for(row["job"], spec), model, label=f"{set_name}:{row['id']}")
        cached, new = cached + response["cached"], new + (not response["cached"])
        results.append({"id": row["id"], "job": row["job"], "model": response.get("model"),
                        "answers": response.get("answers"), "usage": response.get("usage")})
    store.write_atomic(store.root / f"answers-{set_name}.jsonl",
                       "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in results))
    models = sorted({r["model"] for r in results if r["model"]})
    summary = {"set": set_name, "posts": len(results), "new_calls": new, "cached": cached,
               "models": models, "spent_usd": store.spent(), "ceiling_usd": CEILING}
    if any(m != model for m in models) and model != FALLBACK:
        summary["warning"] = f"asked for {model}, served {', '.join(models)}"
    out(json.dumps(summary, indent=1))
    return summary


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
    for name in ("run", "compare"):
        p = sub.add_parser(name)
        p.add_argument("--set", required=True, dest="set_name")
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
            run_set(args.set_name, Client(store), store, store.config().get("model", PINNED))
        elif args.command == "compare":
            print(json.dumps(compare_set(args.set_name, store), indent=1))
    except (Stop, JevError) as exc:
        print(f"stopped: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
