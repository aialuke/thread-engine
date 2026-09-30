#!/usr/bin/env python3
"""Jev judges glossary candidates (research code; nothing in scripts/ imports it).

    python3 research/jev-test/glossary_judge.py build     # write one card per term to private/glossary/cards/
    python3 research/jev-test/glossary_judge.py run       # send the cards, save raw answers (cached)
    python3 research/jev-test/glossary_judge.py report    # calibration verdict, then the candidate table

Each term is one request: {term, proposed_definition, snippets of the repo's own usage} and
about 25 atomic questions. Jev only votes; every threshold and verdict lives here.
Reuses the pinned model, Keychain read and request validation of scripts/jev_design_vote.py.
Snippets are drawn from committed project text only: never loop/inbox, ledger, drafts, or
the third-party Jev articles.
"""

from __future__ import annotations

import json
import random
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from jev_design_vote import CardRefused, check_answers, check_question, post  # noqa: E402
from jev_referee import PINNED_MODEL, CallFailed, read_key  # noqa: E402

OUT = Path(__file__).resolve().parent / "private" / "glossary"
CONTEXT = ROOT / "CONTEXT.md"
SNIPPETS = 8
WINDOW = 160
TIMEOUT = 60.0
SEED = 20260930
ONLY: list[str] = []  # `run <term>` sends just that card

EXCLUDE_DIRS = {".git", "private", "ledger", "receipts", "drafts", "shipped", "__pycache__", "node_modules",
                "jev-articles", "jev-test", "graft"}
EXCLUDE_PARTS = ("loop/inbox", "loop/followers")
EXCLUDE_FILES = {"CONTEXT.md", "Jev cookbooks.md"}
SUFFIXES = {".md"}  # prose only: code identifiers made v1 snippets noisy
MIN_WORDS = 8

# term -> (regex, avoid words when not in the glossary, proposed definition when not in the glossary, group)
CANDIDATES = {
    "Organic": (r"organic", ["natural", "unpaid"],
                "An impression or post that X did not promote or amplify. Only organic numbers are scored.", "candidate"),
    "Retrospective post": (r"retrospective", ["backdated post", "late post"],
                           "A post the operator records after the fact, past its 48h window. It is left out of the 48h read, not marked missed, and its Arm is none.", "candidate"),
    "Ledger": (r"\bledger\b", ["database", "log"],
               "The committed record of Posts and Snapshots, written only by the loop.", "candidate"),
    "Queue": (r"\bqueue\b", ["backlog", "pipeline"],
              "The backlog of Topics, one row per Topic with its status.", "candidate"),
    "Explore and exploit": (r"\bexplor(?:e|ation)\b|\bexploit\b", ["A/B test"],
                            "Explore posts the Treatment. Exploit posts the current best approach.", "candidate"),
    "Voice": (r"\bvoice\b", ["tone", "style"],
              "The shared tone every Card follows, set by the operator's voice rules.", "candidate"),
    "Shout-out": (r"shout-?out", ["credit", "tag", "mention"],
                  "An optional one-line credit to a maker's handle in a Card.", "candidate"),
}
# Hand-audited on 2026-09-30 by reading 8 usages of each (plan: ~/.claude/plans/zazzy-hopping-milner.md).
CLEAN = {  # one sense throughout the sampled usages
    "Cohort": r"\bcohort\b",
    "Roster": r"\broster\b",
    "Truth budget": r"truth budget",
}
MUDDY = {  # Control and Round: 3+ senses seen in the sample; Hook and Topic: the glossary admits a second sense
    "Control": r"\bcontrol\b",
    "Round": r"\brounds?\b",
    "Hook": r"\bhooks?\b",
    "Topic": r"\btopics?\b",
}
EXPLORATORY = {  # real overloads found in v1; reported, outside the pass rule
    "Lane": r"\blane\b",
    "Slot": r"\bslots?\b",
    "Arm": r"\barms?\b",
}
GENERAL = {  # general programming terms: should score low on "specific"
    "regex": (r"\bregex\b", "A pattern written in a compact notation for matching text."),
    "endpoint": (r"\bendpoints?\b", "A URL a client calls to use one function of a web service."),
    "JSON": (r"\bjson\b", "A text format for structured data."),
    "retry": (r"\bretr(?:y|ies)\b", "Trying a failed call again."),
}

SCORE_LEVELS = [
    "No change: only the wording of an explanation differs; no file, number or post is affected.",
    "Mild: an agent would phrase a note or doc differently, but every post, number and file stays the same.",
    "Moderate: an agent would read or edit a different file, section or queue row, with no post's metrics or verdict changed.",
    "Significant: an agent would draft, record or classify a post differently (Format, Lane, Arm, Edit class), changing which posts an Experiment counts.",
    "Severe: an agent would score, threshold or adopt a Lesson on the wrong numbers, or breach a rule the loop may never change (Approval, Truth budget).",
]


# ---------- glossary ----------


def parse_glossary() -> dict[str, dict]:
    entries: dict[str, dict] = {}
    text = CONTEXT.read_text(encoding="utf-8")
    for block in re.split(r"\n(?=\*\*)", text):
        m = re.match(r"\*\*(.+?)\*\*:\n(.*)", block, re.S)
        if not m:
            continue
        body = m.group(2).strip()
        avoid = re.search(r"_Avoid_: (.+)", body)
        definition = re.sub(r"\n?_Avoid_:.*", "", body, flags=re.S).strip()
        entries[m.group(1)] = {
            "definition": definition,
            "avoid": [a.strip() for a in re.sub(r"\(.*?\)", "", avoid.group(1)).split(",") if a.strip()] if avoid else [],
        }
    return entries


def first_sentence(text: str) -> str:
    return re.split(r"(?<=[.])\s", text, maxsplit=1)[0]


# ---------- snippets ----------


def project_files() -> list[Path]:
    files = []
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix not in SUFFIXES or p.name in EXCLUDE_FILES:
            continue
        rel = p.relative_to(ROOT)
        if set(rel.parts) & EXCLUDE_DIRS or any(part in str(rel) for part in EXCLUDE_PARTS):
            continue
        if p.stat().st_size > 400_000:
            continue
        files.append(p)
    return sorted(files)


def gather(pattern: str, files: list[Path], rng: random.Random) -> list[dict]:
    rx = re.compile(pattern, re.I)
    by_file: dict[str, list[dict]] = {}
    for p in files:
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for i, line in enumerate(lines):
            m = rx.search(line)
            if not m or len(line.split()) < MIN_WORDS:
                continue
            start = max(0, m.start() - WINDOW)
            text = line[start:m.end() + WINDOW].strip()
            by_file.setdefault(str(p.relative_to(ROOT)), []).append({"path": f"{p.relative_to(ROOT)}:{i + 1}", "text": text})
    paths = sorted(by_file)
    rng.shuffle(paths)
    for path in paths:
        rng.shuffle(by_file[path])
    picked, round_ = [], 0
    while len(picked) < SNIPPETS and paths:
        progressed = False
        for path in paths:
            if round_ < len(by_file[path]) and len(picked) < SNIPPETS:
                picked.append(by_file[path][round_])
                progressed = True
        if not progressed:
            break
        round_ += 1
    return picked


# ---------- cards ----------

NOUL = {"true": "Yes.", "false": "No."}


def build_card(term: str, pattern: str, definition: str, avoid: list[str], group: str, glossary: dict,
               files: list[Path], rng: random.Random) -> dict:
    snippets = gather(pattern, files, rng)
    rx = re.compile(pattern, re.I)
    entries_using = {k: v["definition"] for k, v in glossary.items() if k != term and rx.search(v["definition"])}
    options = {k: first_sentence(v["definition"]) for k, v in glossary.items()}
    for k, (_, _, d, _) in CANDIDATES.items():
        options.setdefault(k, d)
    options["None of these"] = "The blanked word is a general word with no glossary entry."
    state = {
        "term": term,
        "proposed_definition": definition,
        "snippets": [{"id": i, "path": s["path"], "text": s["text"]} for i, s in enumerate(snippets)],
        "masked_snippets": [{"id": i, "text": rx.sub("____", s["text"])} for i, s in enumerate(snippets)],
        "existing_entries_using_term": entries_using,
        "glossary": {k: v["definition"] for k, v in glossary.items()},
    }
    q: dict[str, dict] = {
        "specific": {"type": "noul", "criteria": NOUL, "instructions":
            "Is `term` a concept specific to the thread-engine project (its workflow of drafting X posts and measuring their results), "
            "rather than a general programming, X or business word that needs no project definition? Judge from `snippets` and `proposed_definition`."},
        "one_sense": {"type": "noul", "criteria": NOUL, "instructions":
            "Do all of `snippets` use `term` in one and the same sense?"},
        "impl_detail": {"type": "noul", "criteria": NOUL, "instructions":
            "Does `proposed_definition` mention an implementation detail, such as a file name, script, command, flag or code identifier?"},
        "self_contained": {"type": "noul", "criteria": NOUL, "instructions":
            "Can `proposed_definition` be fully understood using only the entries in `glossary`, relying on no other project concept that lacks an entry?"},
        "misread_cost": {"type": "score", "criteria": SCORE_LEVELS, "instructions":
            "If an agent working on this project misread `term` as defined in `proposed_definition`, how much would it change what the agent does?"},
    }
    if entries_using:
        q["gap"] = {"type": "noul", "criteria": NOUL, "instructions":
            "Would a reader who has only the glossary entries in `existing_entries_using_term` misread or be unable to follow them without a definition of `term`?"}
    for i in range(len(snippets)):
        q[f"faithful_{i}"] = {"type": "noul", "criteria": NOUL, "instructions":
            f"Is `proposed_definition` true of how `term` is used in `snippets[{i}].text`? Answer no if that usage has a different sense or contradicts the definition."}
        q[f"cloze_{i}"] = {"type": "choice", "criteria": options, "instructions":
            f"In `masked_snippets[{i}].text` a word is replaced by ____. Which entry is the blanked word?"}
    for j, word in enumerate(avoid):
        q[f"avoid_{j}"] = {"type": "noul", "criteria": NOUL, "instructions":
            f"Do any of `snippets` use the word \"{word}\" to mean the same thing as `term`?"}
    for name, question in q.items():
        check_question(name, question)
    return {"model": PINNED_MODEL, "state": state, "questions": q,
            "_meta": {"term": term, "group": group, "expected_cloze": term if group != "general" else "None of these",
                      "avoid": avoid}}


def all_cards() -> list[dict]:
    glossary = parse_glossary()
    files = project_files()
    cards = []
    for term, (pattern, avoid, definition, group) in CANDIDATES.items():
        rng = random.Random(f"{SEED}-{term}")
        cards.append(build_card(term, pattern, definition, avoid, group, glossary, files, rng))
    for group, terms in (("clean", CLEAN), ("muddy", MUDDY), ("exploratory", EXPLORATORY)):
        for term, pattern in terms.items():
            rng = random.Random(f"{SEED}-{term}")
            cards.append(build_card(term, pattern, glossary[term]["definition"], glossary[term]["avoid"], group, glossary, files, rng))
    for term, (pattern, definition) in GENERAL.items():
        rng = random.Random(f"{SEED}-{term}")
        cards.append(build_card(term, pattern, definition, [], "general", glossary, files, rng))
    return cards


def slug(term: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", term.lower()).strip("-")


def cmd_build() -> int:
    (OUT / "cards").mkdir(parents=True, exist_ok=True)
    for card in all_cards():
        n = len(card["state"]["snippets"])
        size = len(json.dumps(card, ensure_ascii=False)) // 4
        (OUT / "cards" / f"{slug(card['_meta']['term'])}.json").write_text(json.dumps(card, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"{card['_meta']['group']:11} {card['_meta']['term']:20} snippets={n} questions={len(card['questions'])} ~{size} tokens")
        if card["_meta"]["group"] in ("clean", "muddy") or "--all" in sys.argv:
            for sn in card["state"]["snippets"]:
                print(f"      {sn['path'][:58]} | {sn['text'][WINDOW - 60:WINDOW + 110]!r}")
    return 0


def cmd_run() -> int:
    (OUT / "answers").mkdir(parents=True, exist_ok=True)
    key = read_key(subprocess.run)
    total = Counter()
    for path in sorted((OUT / "cards").glob("*.json")):
        target = OUT / "answers" / path.name
        if ONLY and path.stem not in ONLY:
            continue
        if target.exists():
            print(f"cached  {path.stem}")
            continue
        card = json.loads(path.read_text(encoding="utf-8"))
        body = {k: card[k] for k in ("model", "state", "questions")}
        try:
            import time, urllib.request
            payload = check_answers(body, post(body, key, TIMEOUT, urllib.request.urlopen, time.sleep))
        except (CallFailed, CardRefused) as exc:
            print(f"FAILED  {path.stem}: {getattr(exc, 'reason', exc)}", file=sys.stderr)
            continue
        target.write_text(json.dumps({"model": payload.get("model"), "usage": payload.get("usage"), "answers": payload["answers"]},
                                     ensure_ascii=False, indent=1), encoding="utf-8")
        usage = payload.get("usage") or {}
        for k, v in usage.items():
            if isinstance(v, (int, float)):
                total[k] += v
        print(f"ok      {path.stem} usage={usage}")
    print("total usage", dict(total))
    return 0


# ---------- report ----------


def load_results() -> list[dict]:
    rows = []
    for path in sorted((OUT / "cards").glob("*.json")):
        ans = OUT / "answers" / path.name
        if not ans.exists():
            continue
        card = json.loads(path.read_text(encoding="utf-8"))
        answers = json.loads(ans.read_text(encoding="utf-8"))["answers"]
        rows.append(summarise(card, answers))
    return rows


def expected_score(answer: dict) -> float:
    probs = answer["probabilities"]
    return sum((int(k) if str(k).isdigit() else i + 1) * p for i, (k, p) in enumerate(probs.items())) if probs else 0.0


def summarise(card: dict, a: dict) -> dict:
    meta = card["_meta"]
    n = len(card["state"]["snippets"])
    faithful = [a[f"faithful_{i}"]["noul"] for i in range(n)]
    cloze_hits, confusions = [], Counter()
    for i in range(n):
        got = a[f"cloze_{i}"]
        cloze_hits.append(got["choice"] == meta["expected_cloze"])
        if got["choice"] != meta["expected_cloze"]:
            confusions[got["choice"]] += 1
    return {
        "term": meta["term"], "group": meta["group"], "n": n,
        "specific": a["specific"]["noul"], "one_sense": a["one_sense"]["noul"],
        "impl_detail": a["impl_detail"]["noul"], "self_contained": a["self_contained"]["noul"],
        "gap": a["gap"]["noul"] if "gap" in a else None,
        "faithful_min": min(faithful) if faithful else None,
        "faithful_low": [i for i, p in enumerate(faithful) if p < 0.5],
        "cloze_acc": sum(cloze_hits) / len(cloze_hits) if cloze_hits else None,
        "confusions": dict(confusions),
        "avoid": {w: a[f"avoid_{j}"]["noul"] for j, w in enumerate(meta["avoid"])},
        "misread": a["misread_cost"],
        "cost_level": max(a["misread_cost"]["probabilities"].items(), key=lambda kv: kv[1])[0],
        "card": card,
    }


def f(x) -> str:
    return "  - " if x is None else f"{x:.2f}"


def cmd_report() -> int:
    rows = load_results()
    by = lambda g: [r for r in rows if r["group"] == g]
    clean, muddy, gen, cand = by("clean"), by("muddy"), by("general"), by("candidate")
    print("term                 group        spec  1sns  faith cloze gap   impl  selfc cost")
    for r in rows:
        print(f"{r['term']:20} {r['group']:11}  {f(r['specific'])}  {f(r['one_sense'])}  {f(r['faithful_min'])}  {f(r['cloze_acc'])}  "
              f"{f(r['gap'])}  {f(r['impl_detail'])}  {f(r['self_contained'])}  {r['cost_level']}")
    have = {r["term"] for r in rows}
    if not ({"Cohort", "Roster", "Truth budget", "Control", "Round", "Hook", "Topic", "JSON", "retry", "regex", "endpoint"} <= have):
        print("\nCalibration incomplete: run every card first.")
        return 1
    mean = lambda xs: sum(xs) / len(xs)
    defined = [r for r in rows if r["term"] in ("Cohort", "Roster", "Truth budget", "Hook", "Topic")]
    gap = mean([r["one_sense"] for r in clean]) - mean([r["one_sense"] for r in muddy])
    checks = {
        "specific >= 0.70 on Cohort, Roster, Truth budget, Hook, Topic": min(r["specific"] for r in defined) >= 0.70,
        "specific <= 0.30 on every general term": max(r["specific"] for r in gen) <= 0.30,
        f"one-sense: mean(clean) - mean(muddy) >= 0.25 (got {gap:.2f})": gap >= 0.25,
        "cloze accuracy: mean over clean >= 0.70": mean([r["cloze_acc"] for r in clean]) >= 0.70,
        "faithful: mean of per-term minimum over clean >= 0.60": mean([r["faithful_min"] for r in clean]) >= 0.60,
    }
    print("\nCalibration (rule declared in README.md before the run):")
    for k, v in checks.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    ok = all(checks.values())
    print("  =>", "trust the candidate table" if ok else "STOP: do not trust the candidate table")
    if not ok:
        return 0
    print("\nCandidates")
    for r in sorted(cand, key=lambda r: -(r["specific"] * (r["gap"] or 0))):
        print(f"\n{r['term']}: specific {f(r['specific'])}, one-sense {f(r['one_sense'])}, gap {f(r['gap'])}, cost level {r['cost_level']}")
        print(f"  faithful min {f(r['faithful_min'])}; low on snippets {r['faithful_low']}; cloze {f(r['cloze_acc'])}; confused with {r['confusions']}")
        print(f"  impl_detail {f(r['impl_detail'])}, self_contained {f(r['self_contained'])}; avoid-word drift {r['avoid']}")
        for i in r["faithful_low"]:
            s = r["card"]["state"]["snippets"][i]
            print(f"    x {s['path']}: {s['text'][:170]!r}")
    return 0


if __name__ == "__main__":
    cmds = {"build": cmd_build, "run": cmd_run, "report": cmd_report}
    if sys.argv[1:2] == ["run"] and len(sys.argv) == 3:  # pilot: run only the named card
        ONLY.append(slug(sys.argv[2]))
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(__doc__)
        sys.exit(1)
    sys.exit(cmds[sys.argv[1]]())
