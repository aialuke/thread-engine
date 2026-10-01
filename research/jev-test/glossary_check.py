#!/usr/bin/env python3
"""Jev checks the new CONTEXT.md definitions against repo usage (research code; see README.md).

    python3 research/jev-test/glossary_check.py build      # cards + printed snippets, nothing sent
    python3 research/jev-test/glossary_check.py run [name] # send (or just one card, as a pilot)
    python3 research/jev-test/glossary_check.py report
"""

from __future__ import annotations

import json
import random
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import glossary_judge as g  # noqa: E402
from jev_design_vote import check_answers, check_question, post  # noqa: E402
from jev_referee import PINNED_MODEL, CallFailed, read_key  # noqa: E402

OUT = g.OUT.parent / "glossary-check"
REPS = (1, 2, 3)
N = 8
EXCLUDE_DIRS = g.EXCLUDE_DIRS | {"jev-design-cards-reading"}
NOUL = g.NOUL

TERMS = {
    "Post": r"\bposts?\b", "Ledger": r"\bledger\b", "Queue": r"\bqueue\b", "Organic": r"organic",
    "Retrospective post": r"retrospective", "Shout-out": r"shout-?out", "Voice": r"\bvoice\b",
}
CONTROLS = {
    "control-wrong-shoutout": ("Shout-out", "An optional one-line credit to a maker's handle in a Card."),
    "control-impl-ledger": ("Ledger", "The files under `ledger/`, written by `scripts/loop.py`: one `<root_id>.json` per post, `activity/`, and `runs.log`."),
    "control-undef-queue": ("Queue", "The list of Topics that the Wibbler keeps, each with its Foozle status."),
}


def files():
    return [p for p in g.project_files()
            if not (set(p.relative_to(g.ROOT).parts) & EXCLUDE_DIRS) and not p.name.startswith("docs-")]


def gather(pattern: str, fs, seed: str) -> list[dict]:
    rx = re.compile(pattern, re.I)
    by_file: dict[str, list[dict]] = {}
    for p in fs:
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for i, line in enumerate(lines):
            if len(line.split()) < g.MIN_WORDS:
                continue
            bare = re.sub(r"`[^`]*`", " ", line)  # a match inside backticks is an identifier or path
            if not rx.search(bare):
                continue
            m = rx.search(line)
            if not m:
                continue
            by_file.setdefault(str(p.relative_to(g.ROOT)), []).append(
                {"path": f"{p.relative_to(g.ROOT)}:{i + 1}", "text": line[max(0, m.start() - g.WINDOW):m.end() + g.WINDOW].strip()})
    rng = random.Random(seed)
    paths = sorted(by_file)
    rng.shuffle(paths)
    for k in paths:
        rng.shuffle(by_file[k])
    picked, seen, r = [], set(), 0
    while len(picked) < N and paths:
        moved = False
        for k in paths:
            if r < len(by_file[k]) and len(picked) < N:
                moved = True
                s = by_file[k][r]
                if s["text"][:60] not in seen:
                    seen.add(s["text"][:60])
                    picked.append(s)
        if not moved:
            break
        r += 1
    return picked


def card(name: str, term: str, definition: str, rep: int, glossary: dict, fs) -> dict:
    sn = gather(TERMS[term], fs, f"{name}-{rep}")
    state = {"term": term, "proposed_definition": definition,
             "snippets": [{"id": i, "path": s["path"], "text": s["text"]} for i, s in enumerate(sn)],
             "glossary": {k: v["definition"] for k, v in glossary.items() if k != term}}
    q = {
        "impl_detail": {"type": "noul", "criteria": NOUL, "instructions":
            "Does `proposed_definition` mention an implementation detail, such as a file name, script, command, flag or code identifier?"},
        "self_contained": {"type": "noul", "criteria": NOUL, "instructions":
            "Can `proposed_definition` be fully understood using only the entries in `glossary`, relying on no other project concept that lacks an entry?"},
    }
    for i in range(len(sn)):
        q[f"faithful_{i}"] = {"type": "noul", "criteria": NOUL, "instructions":
            f"Is `proposed_definition` true of how `term` is used in `snippets[{i}].text`? Answer no if that usage has a different sense or contradicts the definition."}
    for k, v in q.items():
        check_question(k, v)
    return {"model": PINNED_MODEL, "state": state, "questions": q, "_meta": {"name": name, "term": term, "rep": rep}}


def all_cards() -> list[dict]:
    glossary, fs = g.parse_glossary(), files()
    out = []
    for term in TERMS:
        for rep in REPS:
            out.append(card(term, term, glossary[term]["definition"], rep, glossary, fs))
    for name, (term, definition) in CONTROLS.items():
        for rep in REPS:
            out.append(card(name, term, definition, rep, glossary, fs))
    return out


def fname(c) -> str:
    return f"{g.slug(c['_meta']['name'])}-r{c['_meta']['rep']}.json"


def cmd_build() -> int:
    (OUT / "cards").mkdir(parents=True, exist_ok=True)
    for c in all_cards():
        (OUT / "cards" / fname(c)).write_text(json.dumps(c, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"{c['_meta']['name']:24} r{c['_meta']['rep']} snippets={len(c['state']['snippets'])} ~{len(json.dumps(c)) // 4} tokens")
        if c["_meta"]["rep"] == 1 and not c["_meta"]["name"].startswith("control"):
            for s in c["state"]["snippets"]:
                print(f"     {s['path'][:56]} | {s['text'][g.WINDOW - 70:g.WINDOW + 90]!r}")
    return 0


def cmd_run(only: str | None) -> int:
    (OUT / "answers").mkdir(parents=True, exist_ok=True)
    key = read_key(subprocess.run)
    for path in sorted((OUT / "cards").glob("*.json")):
        if only and not path.name.startswith(only):
            continue
        target = OUT / "answers" / path.name
        if target.exists():
            continue
        c = json.loads(path.read_text(encoding="utf-8"))
        body = {k: c[k] for k in ("model", "state", "questions")}
        try:
            payload = check_answers(body, post(body, key, 60.0, urllib.request.urlopen, time.sleep))
        except CallFailed as exc:
            print(f"FAILED {path.name}: {exc.reason}", file=sys.stderr)
            continue
        target.write_text(json.dumps(payload["answers"], ensure_ascii=False), encoding="utf-8")
        print("ok", path.name, payload.get("usage"))
    return 0


def cmd_report() -> int:
    agg: dict[str, dict] = {}
    for path in sorted((OUT / "answers").glob("*.json")):
        c = json.loads((OUT / "cards" / path.name).read_text(encoding="utf-8"))
        a = json.loads(path.read_text(encoding="utf-8"))
        n = len(c["state"]["snippets"])
        d = agg.setdefault(c["_meta"]["name"], {"faithful": [], "impl": [], "self": [], "low": []})
        fs = [a[f"faithful_{i}"]["noul"] for i in range(n)]
        d["faithful"].append(sum(fs) / n)
        d["impl"].append(a["impl_detail"]["noul"])
        d["self"].append(a["self_contained"]["noul"])
        d["low"] += [(c["state"]["snippets"][i]["path"], c["state"]["snippets"][i]["text"][60:230]) for i, p in enumerate(fs) if p < 0.4]
    mean = lambda x: sum(x) / len(x)
    span = lambda x: max(x) - min(x)
    print("name                     faithful  selfcont  impl   spans(f/s/i)")
    for k, d in agg.items():
        print(f"{k:24} {mean(d['faithful']):.2f}      {mean(d['self']):.2f}      {mean(d['impl']):.2f}   "
              f"{span(d['faithful']):.2f}/{span(d['self']):.2f}/{span(d['impl']):.2f}  reps={len(d['faithful'])}")
    need = {"control-wrong-shoutout", "control-impl-ledger", "control-undef-queue"}
    if not need <= set(agg) or any(len(agg[c]["faithful"]) < 3 for c in need):
        print("controls incomplete")
        return 1
    ctl = {
        "wrong Shout-out: mean faithful <= 0.50": mean(agg["control-wrong-shoutout"]["faithful"]) <= 0.50,
        "impl-laden Ledger: impl_detail >= 0.60": mean(agg["control-impl-ledger"]["impl"]) >= 0.60,
        "undefined-word Queue: self_contained <= 0.40": mean(agg["control-undef-queue"]["self"]) <= 0.40,
    }
    for k, v in ctl.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    if not all(ctl.values()):
        print("  => STOP: controls failed; ignore the new-definition results")
        return 0
    print("  => controls pass\n")
    for term in TERMS:
        d = agg.get(term)
        if not d:
            continue
        fails = []
        if mean(d["faithful"]) < 0.75: fails.append(f"faithful {mean(d['faithful']):.2f} < 0.75")
        if mean(d["self"]) < 0.60: fails.append(f"self_contained {mean(d['self']):.2f} < 0.60")
        if mean(d["impl"]) > 0.40: fails.append(f"impl_detail {mean(d['impl']):.2f} > 0.40")
        unstable = [n for n, v in (("faithful", d["faithful"]), ("self_contained", d["self"]), ("impl_detail", d["impl"])) if span(v) > 0.30]
        print(f"{term}: {'OK' if not fails else 'REVISE: ' + '; '.join(fails)}" + (f"  UNSTABLE: {unstable}" if unstable else ""))
        for path, text in d["low"][:4]:
            print(f"    low: {path[:52]} | {text!r}")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    sys.exit({"build": cmd_build, "run": lambda: cmd_run(sys.argv[2] if len(sys.argv) > 2 else None), "report": cmd_report}.get(cmd, lambda: print(__doc__) or 1)())
