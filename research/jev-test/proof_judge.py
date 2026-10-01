#!/usr/bin/env python3
"""Jev judges whether "Proof" is used in one sense (research code; see README.md, "Proof judge").

    python3 research/jev-test/proof_judge.py build          # write new cards (a saved card is never overwritten); nothing is sent
    python3 research/jev-test/proof_judge.py run [prefix]   # send (or only cards whose name starts with prefix: the pilot)
    python3 research/jev-test/proof_judge.py report         # calibration verdict first, then the Proof verdict

Jev only votes; every threshold lives in report().
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
from jev_design_vote import CardRefused, check_answers, check_question, post  # noqa: E402
from jev_referee import PINNED_MODEL, CallFailed, read_key  # noqa: E402

OUT = g.OUT.parent / "proof"
REPS = (1, 2, 3)
N = 8
NOUL = g.NOUL
EXCLUDE = {"jev-design-cards-reading", "discovery-test"}

# path:line -> sense, hand-labelled 2026-09-30 and kept as run. A evidence attached or shown; B the proof line of a
# PAID -> FREE post; C what I took for ordinary English (layer-1 :27 and :219 are the approval-test sense, and
# format-tool-swap/SKILL.md:67 uses both A and B: see the README's second-rater notes). Outside sources are left out.
LABELS: dict[str, str] = {}
for _label, _lines in {
    "A": """.claude/skills/draft-thread/SKILL.md:34 .claude/skills/draft-thread/SKILL.md:35
        .claude/skills/format-build-log/SKILL.md:11 .claude/skills/format-build-log/SKILL.md:20
        .claude/skills/format-build-log/SKILL.md:22 .claude/skills/format-build-log/SKILL.md:29
        .claude/skills/format-build-log/checklist.md:4 .claude/skills/format-tool-swap/SKILL.md:67
        reference/audience.md:8 reference/audience.md:20 reference/x-algorithm.md:28
        research/layer-1-switches-profiles.md:78 research/layer-1-switches-profiles.md:279
        research/layer-1-switches-profiles.md:413 research/x-rules.md:118
        reviews/skill-review-2026-09/draft-thread.md:96 reviews/skill-review-2026-09/draft-thread.md:151
        reviews/ui-build-handoff/screens.md:900 reviews/ui-build-handoff/screens.md:901
        reviews/ui-build-handoff/screens.md:997 reviews/ui-build-handoff/system-today.md:146
        reviews/ui-build-handoff/system-today.md:175 reviews/ui-build-handoff/system-today.md:179
        voice/exit-zero.md:47""",
    "B": """.claude/skills/format-tool-swap/SKILL.md:41 .claude/skills/format-tool-swap/checklist.md:9
        reviews/paid-free-session-2026-09.md:34 reviews/paid-free-session-2026-09.md:45
        reviews/paid-free-session-2026-09.md:116 reviews/paid-free-session-2026-09.md:176
        reviews/paid-free-session-2026-09.md:184 reviews/paid-free-session-2026-09.md:503
        reviews/paid-free-session-2026-09.md:504""",
    "C": """research/layer-1-switches-profiles.md:27 research/layer-1-switches-profiles.md:206
        research/layer-1-switches-profiles.md:219 research/layer-2-x-data-tiers.md:251
        research/layer-2-x-data-tiers.md:255""",
}.items():
    for _p in _lines.split():
        LABELS[_p] = _label

DEF_A = "Evidence a Card points at or the operator attaches: a screenshot, recording, output file, figure or named source."
DEF_B = "The one sentence under a swap in a PAID → FREE post, giving a sourced reason the free tool does the job."
DEF_BOTH = f"Proof: {DEF_A} Proof line: {DEF_B}"
CTL_IMPL = ("The files a reader attaches under `drafts/<slug>/`, such as `PATHS.md`, `CLAIMS.md` and `images/`, "
            "checked by `scripts/post_thread.py`.")
CTL_UNDEF = "The Wibbler evidence that a Foozle attaches to a Card."
OPTIONS = {"Proof": DEF_A, "Proof line": DEF_B, "A general word": "The blanked word is ordinary English, not a project term."}
EXPECTED = {"A": "Proof", "B": "Proof line", "C": "A general word"}
PHRASE = re.compile(r"proof lines?", re.I)
WORD = re.compile(r"\bproofs?\b", re.I)


def snippet(path_line: str) -> dict:
    path, ln = path_line.rsplit(":", 1)
    line = (g.ROOT / path).read_text(encoding="utf-8").splitlines()[int(ln) - 1]
    bare = re.sub(r"`[^`]*`", lambda m: " " * len(m.group(0)), line)  # keep offsets; ignore matches inside backticks
    m = WORD.search(bare)
    if not m:
        raise SystemExit(f"label {path_line} no longer matches 'proof' outside backticks; re-audit")
    text = line[max(0, m.start() - g.WINDOW):m.end() + g.WINDOW].strip()
    return {"path": path_line, "text": text, "masked": WORD.sub("____", PHRASE.sub("____", text)), "label": LABELS[path_line]}


# Known-split control (README, "Follow-up control"): 4 Hook as the opening Card / hook style (P) and 4 Hook as a
# tool hook that acts on a typed prompt (T). Each line was printed in full and read before labelling.
HOOK = {
    "P": [".claude/skills/format-settings/checklist.md:12", "reviews/paid-free-session-2026-09.md:108",
          "README.md:49", "reviews/ui-build-handoff/mock-only.md:43"],
    "T": [".claude/skills/approve/SKILL.md:14", ".claude/skills/draft-thread/SKILL.md:51",
          "AGENTS.md:13", "reviews/x-tools-pilot.md:37"],
}
HOOK_WORD = re.compile(r"\bhooks?\b", re.I)


def hook_snippet(path_line: str, label: str) -> dict:
    path, ln = path_line.strip("`").rsplit(":", 1)
    line = (g.ROOT / path).read_text(encoding="utf-8").splitlines()[int(ln) - 1]
    bare = re.sub(r"`[^`]*`", lambda m: " " * len(m.group(0)), line)
    m = HOOK_WORD.search(bare)
    if not m:
        raise SystemExit(f"hook label {path_line} no longer matches 'hook' outside backticks; re-audit")
    return {"path": f"{path}:{ln}", "text": line[max(0, m.start() - g.WINDOW):m.end() + g.WINDOW].strip(), "label": label}


def hook_card(rep: int, parenthetical: bool = False) -> dict:
    rng = random.Random(f"{g.SEED}-hook-{rep}")
    snips = [hook_snippet(p, lab) for lab, ps in HOOK.items() for p in ps]
    rng.shuffle(snips)
    word = "the word 'hook' (alone or in 'hook style')" if parenthetical else "the word 'hook'"
    q = {"one_sense": {"type": "noul", "criteria": NOUL, "instructions":
         f"Do all of `snippets` use {word} in one and the same sense?"}}
    check_question("one_sense", q["one_sense"])
    return {"model": PINNED_MODEL,
            "state": {"term": "Hook", "snippets": [{"id": i, "path": s["path"], "text": s["text"]} for i, s in enumerate(snips)]},
            "questions": q, "_meta": {"name": "hook-mixed-p" if parenthetical else "hook-mixed", "rep": rep, "kind": "ctl-hook",
                                      "expected": [s["label"] for s in snips]}}


def neutral_card(base: dict) -> dict:
    q = {"one_sense": {"type": "noul", "criteria": NOUL, "instructions":
         "Do all of `snippets` use the word 'proof' in one and the same sense?"}}
    check_question("one_sense", q["one_sense"])
    m = base["_meta"]
    return {"model": PINNED_MODEL, "state": {"term": "Proof", "snippets": base["state"]["snippets"]}, "questions": q,
            "_meta": {"name": "neutral-" + m["name"].removeprefix("proof-"), "rep": m["rep"], "kind": "neutral", "expected": m["expected"]}}


def pool(label: str) -> list[dict]:
    return [snippet(p) for p, lab in LABELS.items() if lab == label]


def base_questions(snips: list[dict], defn: str, faithful: bool) -> dict:
    q = {
        "one_sense": {"type": "noul", "criteria": NOUL, "instructions":
            "Do all of `snippets` use the word 'proof' (alone or in 'proof line') in one and the same sense?"},
        "specific": {"type": "noul", "criteria": NOUL, "instructions":
            "Is `term` a concept specific to the thread-engine project (its workflow of drafting X posts and measuring their results), "
            "rather than a general programming, X or business word that needs no project definition? Judge from `snippets` and `proposed_definition`."},
        "impl_detail": {"type": "noul", "criteria": NOUL, "instructions":
            "Does `proposed_definition` mention an implementation detail, such as a file name, script, command, flag or code identifier?"},
        "self_contained": {"type": "noul", "criteria": NOUL, "instructions":
            "Can `proposed_definition` be fully understood using only the entries in `glossary`, relying on no other project concept that lacks an entry?"},
    }
    for i in range(len(snips)):
        q[f"cloze_{i}"] = {"type": "choice", "criteria": OPTIONS, "instructions":
            f"In `masked_snippets[{i}].text` a word or phrase is replaced by ____. Which entry is the blanked word?"}
        if faithful:
            q[f"faithful_{i}"] = {"type": "noul", "criteria": NOUL, "instructions":
                f"Is `proposed_definition` true of how `term` is used in `snippets[{i}].text`? Answer no if that usage has a different sense or contradicts the definition."}
    for k, v in q.items():
        check_question(k, v)
    return q


def proof_card(name: str, snips: list[dict], defn: str, faithful: bool, rep: int, glossary: dict) -> dict:
    state = {"term": "Proof", "proposed_definition": defn,
             "snippets": [{"id": i, "path": s["path"], "text": s["text"]} for i, s in enumerate(snips)],
             "masked_snippets": [{"id": i, "text": s["masked"]} for i, s in enumerate(snips)],
             "glossary": {k: v["definition"] for k, v in glossary.items()}}
    return {"model": PINNED_MODEL, "state": state, "questions": base_questions(snips, defn, faithful),
            "_meta": {"name": name, "rep": rep, "kind": "proof", "expected": [s["label"] for s in snips]}}


def all_cards() -> list[dict]:
    glossary = g.parse_glossary()
    A, B, C = pool("A"), pool("B"), pool("C")
    files = [p for p in g.project_files() if not (set(p.relative_to(g.ROOT).parts) & EXCLUDE)]
    cards = []
    for rep in REPS:
        rng = random.Random(f"{g.SEED}-proof-{rep}")
        a, b = rng.sample(A, N), rng.sample(B, N)
        mixed = rng.sample(A, N // 2) + rng.sample(B, N // 2)
        rng.shuffle(mixed)
        cards += [proof_card("proof-a", a, DEF_A, True, rep, glossary),
                  proof_card("proof-b", b, DEF_B, True, rep, glossary),
                  proof_card("proof-mixed", mixed, DEF_BOTH, False, rep, glossary),
                  proof_card("ctl-impl", a, CTL_IMPL, True, rep, glossary),
                  proof_card("ctl-undef", a, CTL_UNDEF, True, rep, glossary),
                  proof_card("ctl-wrong", a, DEF_B, True, rep, glossary)]
    cards.append(proof_card("proof-c", C, DEF_A, False, 1, glossary))
    cards += [neutral_card(c) for c in cards if c["_meta"]["name"] in ("proof-a", "proof-b", "proof-mixed")]
    cards += [hook_card(rep) for rep in REPS] + [hook_card(rep, parenthetical=True) for rep in REPS]
    for group, terms in (("clean", g.CLEAN), ("muddy", g.MUDDY)):
        for term, pattern in terms.items():
            for rep in REPS:
                rng = random.Random(f"{g.SEED}-{term}-proof-cal-{rep}")
                c = g.build_card(term, pattern, glossary[term]["definition"], glossary[term]["avoid"], group, glossary, files, rng)
                c["_meta"].update({"name": f"cal-{g.slug(term)}", "rep": rep, "kind": "cal"})
                cards.append(c)
    return cards


def fname(c: dict) -> str:
    return f"{c['_meta']['name']}-r{c['_meta']['rep']}.json"


def cmd_build() -> int:
    (OUT / "cards").mkdir(parents=True, exist_ok=True)
    for c in all_cards():
        if (OUT / "cards" / fname(c)).exists():  # a card that already has answers must not change under them
            continue
        (OUT / "cards" / fname(c)).write_text(json.dumps(c, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"{c['_meta']['name']:26} r{c['_meta']['rep']} snippets={len(c['state']['snippets'])} "
              f"questions={len(c['questions'])} ~{len(json.dumps(c, ensure_ascii=False)) // 4} tokens")
        if c["_meta"]["rep"] == 1 and c["_meta"]["kind"] == "proof" and c["_meta"]["name"] in ("proof-a", "proof-b", "proof-mixed", "proof-c"):
            for s, lab in zip(c["state"]["snippets"], c["_meta"]["expected"]):
                print(f"     [{lab}] {s['path'][:52]} | {s['text'][g.WINDOW - 60:g.WINDOW + 90]!r}")
    return 0


def cmd_run(prefix: str | None) -> int:
    (OUT / "answers").mkdir(parents=True, exist_ok=True)
    key = read_key(subprocess.run)
    failed = 0
    for path in sorted((OUT / "cards").glob("*.json")):
        if prefix and not path.name.startswith(prefix):
            continue
        target = OUT / "answers" / path.name
        if target.exists():
            print("cached", path.name)
            continue
        c = json.loads(path.read_text(encoding="utf-8"))
        body = {k: c[k] for k in ("model", "state", "questions")}
        try:
            payload = check_answers(body, post(body, key, g.TIMEOUT, urllib.request.urlopen, time.sleep))
        except (CallFailed, CardRefused) as exc:
            print(f"FAILED {path.name}: {getattr(exc, 'reason', exc)}", file=sys.stderr)
            failed += 1
            continue
        target.write_text(json.dumps({"usage": payload.get("usage"), "answers": payload["answers"]}, ensure_ascii=False, indent=1), encoding="utf-8")
        print("ok", path.name, payload.get("usage"))
    return 1 if failed else 0


def load() -> dict[str, list[tuple[dict, dict]]]:
    out: dict[str, list] = {}
    for path in sorted((OUT / "answers").glob("*.json")):
        c = json.loads((OUT / "cards" / path.name).read_text(encoding="utf-8"))
        a = json.loads(path.read_text(encoding="utf-8"))["answers"]
        out.setdefault(c["_meta"]["name"], []).append((c, a))
    return out


mean = lambda xs: sum(xs) / len(xs)
span = lambda xs: max(xs) - min(xs)


def cloze_acc(c: dict, a: dict) -> float:
    n = len(c["state"]["snippets"])
    if c["_meta"]["kind"] == "cal":
        return mean([a[f"cloze_{i}"]["choice"] == c["_meta"]["expected_cloze"] for i in range(n)])
    return mean([a[f"cloze_{i}"]["choice"] == EXPECTED[c["_meta"]["expected"][i]] for i in range(n)])


def faithful(c: dict, a: dict) -> float:
    return mean([a[f"faithful_{i}"]["noul"] for i in range(len(c["state"]["snippets"]))])


def cmd_report() -> int:
    r = load()
    def col(name, fn):
        return [fn(c, a) for c, a in r.get(name, [])]
    one = lambda c, a: a["one_sense"]["noul"]
    impl = lambda c, a: a["impl_detail"]["noul"]
    clean = [n for n in r if n.startswith("cal-") and r[n][0][0]["_meta"]["group"] == "clean"]
    muddy = [n for n in r if n.startswith("cal-") and r[n][0][0]["_meta"]["group"] == "muddy"]
    need = {"proof-a", "proof-b", "proof-mixed", "ctl-impl"}
    if len(clean) < 3 or len(muddy) < 4 or not need <= set(r) or any(len(v) < 3 for k, v in r.items() if k != "proof-c"):
        print("Incomplete: run every card (3 reps) first.")
        return 1
    print("term/card            one_sense  span   cloze  impl   self   faithful")
    for name in sorted(r):
        if r[name][0][0]["_meta"]["kind"] in ("ctl-hook", "neutral"):
            continue
        o, cl = col(name, one), col(name, cloze_acc)
        print(f"{name:20} {mean(o):.2f}      {span(o):.2f}   {mean(cl):.2f}   {mean(col(name, impl)):.2f}   "
              f"{mean(col(name, lambda c, a: a['self_contained']['noul'])):.2f}   "
              + (f"{mean(col(name, faithful)):.2f}" if r[name][0][0]['_meta']['kind'] == 'proof' and 'faithful_0' in r[name][0][1] else " - "))
    gap = mean([mean(col(n, one)) for n in clean]) - mean([mean(col(n, one)) for n in muddy])
    cal = {
        f"one-sense: mean(clean) - mean(muddy) >= 0.25 (got {gap:.2f})": gap >= 0.25,
        "cloze: mean over clean terms >= 0.70": mean([mean(col(n, cloze_acc)) for n in clean]) >= 0.70,
        "impl_detail: laden control >= 0.60": mean(col("ctl-impl", impl)) >= 0.60,
        "impl_detail: real Proof definitions (A, B) <= 0.40": max(mean(col("proof-a", impl)), mean(col("proof-b", impl))) <= 0.40,
        "stability: no calibration term one_sense span > 0.30": max(span(col(n, one)) for n in clean + muddy) <= 0.30,
    }
    print("\nCalibration (rule in README.md, written before the run):")
    for k, v in cal.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    if not all(cal.values()):
        print("  => STOP: ignore the Proof results; change no threshold or term to pass.")
        return 0
    print("  => calibration passes\n")
    A, B, M = (mean(col(n, one)) for n in ("proof-a", "proof-b", "proof-mixed"))
    spans = max(span(col(n, one)) for n in ("proof-a", "proof-b", "proof-mixed"))
    cA, cB = mean(col("proof-a", cloze_acc)), mean(col("proof-b", cloze_acc))
    print(f"one_sense: A-only {A:.2f}, B-only {B:.2f}, mixed {M:.2f} (max rep span {spans:.2f}); cloze A {cA:.2f}, B {cB:.2f}")
    if min(A, B) < 0.60 or spans > 0.30:
        verdict = "INCONCLUSIVE: a pure card is below 0.60 or a rep span exceeds 0.30. Change nothing."
    elif M <= min(A, B) - 0.25:
        verdict = "Jev sees two senses: propose two entries, Proof and Proof line."
    else:
        verdict = ("Jev does not see an overload under the parenthetical wording. A blind Codex found four senses "
                   "(README): the entry decision is the operator's.")
    cleanm = mean([mean(col(n, one)) for n in clean])
    if "hook-mixed" not in r or len(r["hook-mixed"]) < 3:
        verdict = "VOID until the known-split control (hook-mixed, 3 reps) has run."
    else:
        h = mean(col("hook-mixed", one))
        detects = h <= cleanm - 0.25
        print(f"Known-split control hook-mixed one_sense {h:.2f} (span {span(col('hook-mixed', one)):.2f}); "
              f"detects a 4-and-4 split if <= {cleanm - 0.25:.2f}: {'YES' if detects else 'NO'}")
        if not detects:
            verdict = "VOID: one_sense cannot detect a 4-and-4 split of one word, so it says nothing about A/B."
    print("Cloze:", "senses separable by context" if min(cA, cB) >= 0.70 else "inconclusive (not evidence for one sense)")
    print("Verdict:", verdict)
    fu = ("neutral-a", "neutral-b", "neutral-mixed", "hook-mixed-p")
    if all(len(r.get(k, [])) == 3 for k in fu):
        hp = mean(col("hook-mixed-p", one))
        blunt = hp > cleanm - 0.25
        nA, nB, nM = (mean(col(k, one)) for k in fu[:3])
        nspan = max(span(col(k, one)) for k in fu[:3])
        print(f"\nWording follow-up: hook-mixed-p {hp:.2f} against threshold {cleanm - 0.25:.2f}: "
              f"the parenthetical {'BLUNTS split detection, so the parenthetical Proof result is VOID' if blunt else 'does not blunt split detection'}")
        print(f"  neutral wording one_sense: A {nA:.2f}, B {nB:.2f}, mixed {nM:.2f} (max rep span {nspan:.2f})")
        if min(nA, nB) < 0.60 or nspan > 0.30:
            print("  neutral verdict: INCONCLUSIVE (a pure card is below 0.60 or a span exceeds 0.30)")
        elif nM <= min(nA, nB) - 0.25:
            print("  neutral verdict: Jev sees two senses (overturns the fold)")
        else:
            print("  neutral verdict: fold confirmed")
    else:
        print("\nWording follow-up not run yet (neutral-a, neutral-b, neutral-mixed, hook-mixed-p at 3 reps each).")
    wrong, undef = mean(col("ctl-wrong", faithful)), mean(col("ctl-undef", lambda c, a: a["self_contained"]["noul"]))
    print(f"\nUnvalidated signals: faithful on wrong definition {wrong:.2f} (control passes if <= 0.50; real A {mean(col('proof-a', faithful)):.2f}, "
          f"B {mean(col('proof-b', faithful)):.2f}); self_contained on undefined-word control {undef:.2f} (passes if <= 0.40).")
    for name in ("proof-a", "proof-b"):
        for c, a in r[name]:
            for i, s in enumerate(c["state"]["snippets"]):
                got = a[f"cloze_{i}"]["choice"]
                if got != EXPECTED[c["_meta"]["expected"][i]] and c["_meta"]["rep"] == 1:
                    print(f"  miss ({name}): {s['path']} -> {got}")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    sys.exit({"build": cmd_build, "run": lambda: cmd_run(sys.argv[2] if len(sys.argv) > 2 else None), "report": cmd_report}.get(cmd, lambda: print(__doc__) or 1)())
