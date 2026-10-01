#!/usr/bin/env python3
"""Jev judges whether two instructions conflict (research code; nothing in scripts/ imports it).

    python3 research/jev-test/conflict_judge.py build             # print every passage pair, write cards
    python3 research/jev-test/conflict_judge.py run [ids] [--wording A|B] [--fresh]
    python3 research/jev-test/conflict_judge.py report            # control verdict first, then the findings

Each pair is one request with one Choice question. Jev only votes; the pass rule lives here and in
research/jev-test/README.md. Reuses the pinned model, Keychain read and request checks of
scripts/jev_design_vote.py. Passages are read from committed text (a git revision or the working tree).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from jev_design_vote import CardRefused, check_answers, check_question, post  # noqa: E402
from jev_referee import PINNED_MODEL, CallFailed, read_key  # noqa: E402

OUT = Path(__file__).resolve().parent / "private" / "conflict"
CACHE = OUT / "cache"
CALLS = OUT / "calls.jsonl"
REQUEST_CAP = 500
TIMEOUT = 60.0
MIN_GAP = 0.30
UNSTABLE_SPAN = 0.30
CONFLICT = "cannot_both_be_followed"

# id -> (kind, A, B). A passage is (revision or None for the working tree, file, first line, last line),
# or ("literal", text) for a planted sentence.
ITEMS = {
    "CX1": ("conflict", ("ffea23c", "AGENTS.md", 36, 36), (None, ".claude/skills/posted/SKILL.md", 13, 13)),
    "CX2": ("conflict", ("ffea23c", "AGENTS.md", 20, 20), ("ffea23c", ".claude/skills/next/experiment-list.md", 19, 19)),
    "CX3": ("conflict", (None, "voice/exit-zero.md", 55, 55),
            ("literal", "When a reader raises a caveat, edit the live post to add it.")),
    "CK1": ("consistent", (None, ".claude/skills/hidden-settings/SKILL.md", 43, 43), (None, ".claude/skills/format-build-log/SKILL.md", 34, 34)),
    "CK2": ("consistent", (None, "AGENTS.md", 8, 8), (None, "README.md", 8, 8)),
    "CK3": ("consistent", (None, "CONTEXT.md", 40, 41), (None, ".claude/skills/results/SKILL.md", 29, 29)),
    "F3": ("finding", (None, "reference/audience.md", 20, 20), (None, "voice/exit-zero.md", 40, 40)),
    "F4": ("finding", (None, ".claude/skills/format-tool-swap/checklist.md", 16, 16), (None, ".claude/skills/draft-thread/SKILL.md", 53, 54)),
    "F5": ("finding", (None, "voice/exit-zero.md", 52, 52), (None, ".claude/skills/format-tool-swap/SKILL.md", 88, 94)),
    "F6": ("finding", ("260bd45", "voice/exit-zero.md", 16, 16), (None, ".claude/skills/format-tool-swap/SKILL.md", 66, 66)),
    "F7": ("finding", (None, ".claude/skills/verify-settings/SKILL.md", 58, 59), (None, ".claude/skills/verify-settings/SKILL.md", 63, 63)),
    "F8": ("finding", (None, ".claude/skills/draft-thread/SKILL.md", 33, 33), (None, "CONTEXT.md", 148, 150)),
    "F10": ("finding", ("260bd45", "voice/exit-zero.md", 34, 34), (None, ".claude/skills/format-tool-swap/SKILL.md", 88, 94)),
    "F11": ("finding", (None, "AGENTS.md", 8, 8), (None, ".claude/skills/draft-thread/SKILL.md", 18, 18)),
}
PILOT = ["CX1", "CK1"]

# E1: pairs built by construction from conflict_items.json. Each base gives a consistent pair
# (original sentence, faithful paraphrase) and a conflict pair (original sentence, paraphrase with one term flipped).
ITEMS_FILE = Path(__file__).resolve().parent / "conflict_items.json"
KEPT_FILE = OUT / "kept.json"
BUILT: dict[str, tuple] = {}

# E3: one sentence stating the practical consequence of each pair Jev called followable.
NOTES = {
    "F10": "The shout-out card is a reply that ends at the thank-you, and the closing-question rule says to end a post with a question.",
    "F11": "If the session is not in Plan mode, passage B tells the agent to continue, while passage A says non-trivial work starts in Plan mode.",
    "CX1": "Passage B has the agent save a file under ledger/raw, a folder passage A says only loop.py writes.",
    "CX2": "The exploit slot posts from adopted lessons in learnings.md, while passage A says a lesson changes the rules only through /apply.",
}

NOUL = {
    "instructions": ("Passage A and passage B are both instructions to an AI agent that drafts social posts in this "
                     "repository. Is there a task in which an agent that obeys one passage would break the other? "
                     "Judge only what the passages say."),
    "criteria": {"true": "Yes, such a task exists.", "false": "No, both can always be obeyed together."},
}


# T1: one task line per pair, written before any answer was seen. T2: a note claiming a conflict.
TASKS = {
    "CX1": "Record a posted thread: read it with x_api.py and store the output.",
    "CX2": "Choose how to draft the next exploit-slot post when learnings.md has an adopted lesson whose rule is none.",
    "CX3": "A reader raises a caveat about a live post and the agent must respond.",
    "CK1": "Write the root post of a build-log.",
    "CK2": "Start a non-trivial drafting session.",
    "CK3": "Judge the lane of a PAID → FREE post.",
    "F3": "Judge the lane of a post that asks a question containing a factual assertion.",
    "F4": "Complete the tool-swap checklist when a revised draft still needs approval.",
    "F5": "Write the shout-out reply under a PAID → FREE post.",
    "F6": "Draft a PAID → FREE post when the operator has tested none of the tools.",
    "F7": "Finish a verify run in which one candidate stays VERIFY.",
    "F8": "Draft a control-arm post.",
    "F10": "Write the maker shout-out card.",
    "F11": "Begin a draft in a session that is not in Plan mode.",
}
TASK_CONFLICT = "no_must_break_one"
TASK_QUESTION = {
    "instructions": ("Passage A and passage B are both instructions to an AI agent that drafts social posts in this "
                     "repository. The task is given in the state. Can the agent complete that task obeying both passages "
                     "fully? Judge only what the passages say."),
    "criteria": {
        "yes_obeys_both": "The agent can finish the task and obey both passages.",
        TASK_CONFLICT: "Finishing the task means breaking one of the passages.",
        "task_not_covered": "The passages do not bear on this task.",
    },
}
FALSE_NOTE = "Passage A tells the agent to do something that passage B forbids, so the agent cannot follow both."
# T3: passage B cut to the disputed sentence(s).
SWAP = ".claude/skills/format-tool-swap/SKILL.md"
TRIMS = {
    "CX1": ("sentence", ".claude/skills/posted/SKILL.md", 13,
            "Save the output to `ledger/raw/<root id>-posted.txt` (it holds only the account's own posts)."),
    "F10": ("sentence", SWAP, 91, "- **Ends at the thank-you.** The card carries nothing about the next post."),
    "F5": ("lines", SWAP, [85, 88]),
}


# T4-T6: extra question shapes. p_break() reads each shape's answer as P(the passages conflict).
_DESC = {"both": "The agent can follow both at once.", "break": "Following one means breaking the other.",
         "silent": "The passages do not bear on each other."}
_INTRO = ("Passage A and passage B are both instructions to an AI agent that drafts social posts in this "
          "repository. Decide whether one agent could follow both in the same task without breaking either. "
          "Judge only what the passages say.")  # identical to WORDINGS["A"]
EXTRA = {
    "names_random": {"type": "choice", "instructions": _INTRO,
                     "criteria": {"k7": _DESC["both"], "q2": _DESC["break"], "m9": _DESC["silent"]}},
    "names_swapped": {"type": "choice", "instructions": _INTRO,
                      "criteria": {"cannot_both_be_followed": _DESC["both"], "both_followable": _DESC["break"],
                                   "silent": _DESC["silent"]}},
    "always": {"type": "noul",
               "instructions": ("Passage A and passage B are both instructions to an AI agent that drafts social posts in "
                                "this repository. Can an agent always obey both passages together, in any task? "
                                "Judge only what the passages say."),
               "criteria": {"true": "Yes, both can always be obeyed together.",
                            "false": "No, in some task obeying one breaks the other."}},
    "probe": {"type": "noul",
              "instructions": "Do passage A and passage B contradict each other? Judge only what the passages say.",
              "criteria": {"true": "Yes, they contradict each other.", "false": "No, they do not contradict each other."}},
}


def p_break(shape: str, answer: dict) -> float:
    """P(the passages conflict) for one saved answer, by the meaning of the option or the polarity of the Noul."""
    if shape == "noul" or shape == "probe":
        return answer["noul"]
    if shape == "always":
        return 1.0 - answer["noul"]
    probs = answer["probabilities"]
    if shape == "task":
        return probs[TASK_CONFLICT]
    if shape == "names_random":
        return probs["q2"]
    if shape == "names_swapped":
        return probs["both_followable"]  # the name says "followable", the description says "break"
    return probs[CONFLICT]


# T7: passages before and after the text that fixed them. The "after" side is pinned to e52e931.
_N, _S = "e52e931", ".claude/skills/next/experiment-list.md"
_POSTED = ".claude/skills/posted/SKILL.md"
_SWAP2 = ".claude/skills/format-tool-swap/SKILL.md"
FIX_BASES = {
    "H1": (("ffea23c", "AGENTS.md", 36, 36), (_N, "AGENTS.md", 36, 36), (_N, _POSTED, 13, 13)),
    "H2": (("ffea23c", "AGENTS.md", 20, 20), (_N, "AGENTS.md", 20, 20), None),
    "H3": (("ffea23c", "CONTEXT.md", 40, 41), (_N, "CONTEXT.md", 40, 41), None),
    "H4": (("ffea23c", "AGENTS.md", 8, 8), (_N, "AGENTS.md", 8, 8), None),
    "H5": (("ffea23c", ".claude/skills/hidden-settings/SKILL.md", 43, 43), (_N, ".claude/skills/hidden-settings/SKILL.md", 43, 43), None),
    "H6": (("260bd45", "voice/exit-zero.md", 16, 16), (_N, "voice/exit-zero.md", 16, 16), (_N, _SWAP2, 62, 62)),
    "H7": (("260bd45", "voice/exit-zero.md", 34, 34), (_N, "voice/exit-zero.md", 34, 34), (_N, _SWAP2, 84, 90)),
    "H8": (("ffea23c", ".claude/skills/jev-card/SKILL.md", 10, 10), (_N, ".claude/skills/jev-card/SKILL.md", 10, 10), (_N, "CONTEXT.md", 69, 71)),
}
# Passage B for the pairs whose other side also changed: (before B, after B).
FIX_B = {
    "H2": (("ffea23c", _S, 19, 19), (_N, _S, 19, 19)),
    "H3": (("ffea23c", ".claude/skills/results/SKILL.md", 29, 29), (_N, ".claude/skills/results/SKILL.md", 29, 29)),
    "H4": (("ffea23c", "README.md", 8, 8), (_N, "README.md", 8, 8)),
    "H5": (("ffea23c", "CONTEXT.md", 13, 14), (_N, "CONTEXT.md", 13, 14)),
}
FIX: dict[str, tuple] = {}
for _k, (_ab, _aa, _b) in FIX_BASES.items():
    _bb, _ba = (_b, _b) if _b else FIX_B[_k]
    FIX[_k + "b"] = ("fix_before", _ab, _bb)
    FIX[_k + "a"] = ("fix_after", _aa, _ba)
FIX_KEPT_FILE = OUT / "fix_kept.json"


def load_built() -> None:
    if not ITEMS_FILE.exists():
        return
    for base in json.loads(ITEMS_FILE.read_text()):
        a = ("sentence", base["file"], base["line"], base["sentence"])
        BUILT[base["id"] + "s"] = ("built_consistent", a, ("nearby", base["file"], base["same"]))
        BUILT[base["id"] + "f"] = ("built_conflict", a, ("nearby", base["file"], base["flip"]))


load_built()


def spec(item_id: str) -> tuple:
    for group in (ITEMS, BUILT, FIX):
        if item_id in group:
            return group[item_id]
    raise KeyError(item_id)

WORDINGS = {
    "A": {
        "instructions": ("Passage A and passage B are both instructions to an AI agent that drafts social posts in this "
                         "repository. Decide whether one agent could follow both in the same task without breaking either. "
                         "Judge only what the passages say."),
        "criteria": {
            "both_followable": "The agent can follow both at once.",
            "cannot_both_be_followed": "Following one means breaking the other.",
            "silent": "The passages do not bear on each other.",
        },
    },
    "B": {
        "instructions": ("Read two passages that an AI agent is told to obey. Do they pull in opposite directions in a "
                         "single drafting task, so that obeying one breaks the other? Use only the words on the page."),
        "criteria": {
            "silent": "Neither passage affects the other.",
            "cannot_both_be_followed": "They pull in opposite directions: obeying one breaks the other.",
            "both_followable": "Both can be obeyed together.",
        },
    },
}


def passage(spec: tuple) -> dict:
    if spec[0] == "literal":
        return {"source": "planted sentence", "text": spec[1]}
    if spec[0] == "lines":
        _, path, numbers = spec
        rows = (ROOT / path).read_text(encoding="utf-8").splitlines()
        return {"source": path, "text": "\n".join(rows[n - 1] for n in numbers)}
    if spec[0] == "nearby":  # a built passage: shown under the same file as its partner so the label is no tell
        return {"source": spec[1], "text": spec[2]}
    if spec[0] == "sentence":
        _, path, line, text = spec
        if text not in (ROOT / path).read_text(encoding="utf-8").splitlines()[line - 1]:
            raise CardRefused(f"{path}:{line} no longer holds the base sentence")
        return {"source": path, "text": text}
    rev, path, first, last = spec
    if rev:
        text = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    else:
        text = (ROOT / path).read_text(encoding="utf-8")
    lines = text.splitlines()[first - 1:last]
    if not lines:
        raise CardRefused(f"{path} has no lines {first}-{last}")
    return {"source": path, "text": "\n".join(lines)}


def card(item_id: str, wording: str, shape: str = "choice", note: bool | str = False, trim: bool = False) -> dict:
    _, a, b = spec(item_id)
    question = {"choice": {"type": "choice", **WORDINGS[wording]}, "noul": {"type": "noul", **NOUL},
                "task": {"type": "choice", **TASK_QUESTION}, **EXTRA}[shape]
    check_question("conflict", question)
    state: dict[str, object] = {"passage_A": passage(a), "passage_B": passage(TRIMS[item_id] if trim else b)}
    if shape == "task":
        state["task"] = TASKS[item_id]  # T1 only: the 14 old pairs have task lines
    if note:
        state["note"] = FALSE_NOTE if note == "false" else NOTES[item_id]
    return {"model": PINNED_MODEL, "state": state, "questions": {"conflict": question}}


def digest(body: dict) -> str:
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:24]


def count_requests() -> int:
    return sum(1 for _ in CALLS.open()) if CALLS.exists() else 0


def ask(item_id: str, wording: str, fresh: bool, key: str, shape: str = "choice", note: bool | str = False, trim: bool = False) -> dict:
    body = card(item_id, wording, shape, note, trim)
    slot = CACHE / f"{digest(body)}.json"
    tries = sorted(CACHE.glob(f"{digest(body)}*.json"))
    if tries and not fresh:
        return json.loads(tries[0].read_text())
    if count_requests() >= REQUEST_CAP:
        raise SystemExit(f"request cap {REQUEST_CAP} reached")
    payload = check_answers(body, post(body, key, TIMEOUT, urllib.request.urlopen, time.sleep))
    CACHE.mkdir(parents=True, exist_ok=True)
    if fresh and slot.exists():
        slot = CACHE / f"{digest(body)}-{len(tries)}.json"
    slot.write_text(json.dumps({"item": item_id, "wording": wording, "shape": shape, "note": note, "trim": trim, "payload": payload}))
    with CALLS.open("a") as handle:
        handle.write(json.dumps({"item": item_id, "wording": wording, "shape": shape, "note": note, "trim": trim, "fresh": fresh}) + "\n")
    return json.loads(slot.read_text())


def scores(item_id: str, wording: str, shape: str = "choice", note=False, trim: bool = False) -> list[dict]:
    """Every saved answer for this item, wording, shape, note and trim: chosen option and P(conflict)."""
    body = card(item_id, wording, shape, note, trim)
    out = []
    for path in sorted(CACHE.glob(f"{digest(body)}*.json")):
        answer = json.loads(path.read_text())["payload"]["answers"]["conflict"]
        row = {"choice": answer.get("choice", "noul"), CONFLICT: p_break(shape, answer)}
        if shape == "names_swapped":
            row["by_name"] = answer["probabilities"]["cannot_both_be_followed"]
        out.append(row)
    return out


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def verdict(p: dict[str, dict[str, float]]) -> dict:
    """p[wording][item_id] = probability of CONFLICT. Pure: the pass rule in README.md."""
    ids = {kind: [i for i, v in ITEMS.items() if v[0] == kind] for kind in ("conflict", "consistent", "finding")}
    gaps = {w: mean([p[w][i] for i in ids["conflict"]]) - mean([p[w][i] for i in ids["consistent"]]) for w in p}
    valid = all(g >= MIN_GAP for g in gaps.values())
    shift = mean([abs(p["A"][i] - p["B"][i]) for i in p["A"]])
    ceiling = {w: max(p[w][i] for i in ids["consistent"]) + shift for w in p}
    flagged = [i for i in ids["finding"] if all(p[w][i] > ceiling[w] for w in p)]
    return {"valid": valid, "gaps": gaps, "shift": shift, "ceiling": ceiling, "flagged": flagged}


def loo(p: dict[str, dict[str, float]], ids: dict[str, list[str]]) -> list[dict]:
    """E0. The control gap in each wording when each control is dropped in turn."""
    out = []
    for drop in ids["conflict"] + ids["consistent"]:
        gap = {}
        for w in p:
            con = [p[w][i] for i in ids["conflict"] if i != drop]
            ok = [p[w][i] for i in ids["consistent"] if i != drop]
            gap[w] = mean(con) - mean(ok)
        out.append({"drop": drop, "gap": gap, "passes": all(g >= MIN_GAP for g in gap.values())})
    return out


def auc(pos: list[float], neg: list[float]) -> float:
    """Chance a random conflict outscores a random consistent pair; ties count half."""
    wins = sum((x > y) + 0.5 * (x == y) for x in pos for y in neg)
    return wins / (len(pos) * len(neg))


def rates(conflict: list[float], consistent: list[float], threshold: float = 0.5) -> dict:
    """E1. Share of kept conflicts flagged, share of kept consistent pairs flagged, and the AUC."""
    return {"sensitivity": sum(x >= threshold for x in conflict) / len(conflict),
            "false_alarm": sum(x >= threshold for x in consistent) / len(consistent),
            "auc": auc(conflict, consistent)}


def cmd_loo() -> None:
    ids = {kind: [i for i, v in ITEMS.items() if v[0] == kind] for kind in ("conflict", "consistent")}
    p = {w: {i: mean([s[CONFLICT] for s in scores(i, w)]) for i in ids["conflict"] + ids["consistent"]} for w in WORDINGS}
    results = loo(p, ids)
    for r in results:
        print(f"drop {r['drop']:4} gap " + "  ".join(f"{w}={g:.2f}" for w, g in r["gap"].items()), "PASS" if r["passes"] else "FAIL")
    print("E0 VERDICT:", "passes" if all(r["passes"] for r in results) else "FAILS with a control removed")


def kept_ids() -> dict[str, list[str]]:
    kept = json.loads(KEPT_FILE.read_text())
    return {"conflict": [i for i in kept if i.endswith("f")], "consistent": [i for i in kept if i.endswith("s")]}


def cmd_rates(args: list[str]) -> None:
    shape = args[args.index("--shape") + 1] if "--shape" in args else "choice"
    kept = kept_ids()
    print(f"kept: {len(kept['conflict'])} conflict, {len(kept['consistent'])} consistent; shape={shape}")
    for w in (WORDINGS if shape == "choice" else ["A"]):
        pos = [mean([s[CONFLICT] for s in scores(i, w, shape)]) for i in kept["conflict"]]
        neg = [mean([s[CONFLICT] for s in scores(i, w, shape)]) for i in kept["consistent"]]
        r = rates(pos, neg)
        ok = r["sensitivity"] >= 0.85 and r["false_alarm"] <= 0.10
        print(f"{w}: sensitivity {r['sensitivity']:.2f}  false alarm {r['false_alarm']:.2f}  AUC {r['auc']:.2f}", "PASS" if ok else "FAIL")
        misses = [i for i, x in zip(kept["conflict"], pos) if x < 0.5]
        alarms = [i for i, x in zip(kept["consistent"], neg) if x >= 0.5]
        print("   missed conflicts:", ", ".join(misses) or "none", "| false alarms:", ", ".join(alarms) or "none")


def cmd_build() -> None:
    for item_id, (kind, _, _) in {**ITEMS, **BUILT}.items():
        state = card(item_id, "A")["state"]
        print(f"\n=== {item_id} ({kind})")
        for side in ("passage_A", "passage_B"):
            print(f"--- {side}: {state[side]['source']}\n{state[side]['text']}")


def cmd_run(args: list[str]) -> None:
    fresh = "--fresh" in args
    note = "false" if "--falsenote" in args else ("--note" in args)
    trim = "--trim" in args
    shape = args[args.index("--shape") + 1] if "--shape" in args else "choice"
    wordings = [args[args.index("--wording") + 1]] if "--wording" in args else list(WORDINGS)
    every = {**ITEMS, **BUILT, **FIX}
    ids = [a for a in args if a in every]
    if "--set" in args:
        which = args[args.index("--set") + 1]
        ids = list(ITEMS) + kept_ids()["conflict"] + kept_ids()["consistent"] if which == "p53" else fix_ids()
    if "--built" in args:
        ids = [i for i in (kept_ids()["conflict"] + kept_ids()["consistent"] if KEPT_FILE.exists() else list(BUILT))]
    ids = ids or list(ITEMS)
    key = read_key()
    for item_id in ids:
        for wording in wordings:
            try:
                got = ask(item_id, wording, fresh, key, shape, note, trim)["payload"]["answers"]["conflict"]
            except CallFailed as exc:
                print(f"{item_id} {wording}: failed ({exc})")
                continue
            shown = got["noul"] if "noul" in got else f"{got['choice']} {json.dumps(got['probabilities'])}"
            print(f"{item_id} {wording}: {shown}")


def fix_ids() -> list[str]:
    kept = json.loads(FIX_KEPT_FILE.read_text()) if FIX_KEPT_FILE.exists() else list(FIX_BASES)
    return [k + s for k in kept for s in ("b", "a")]


def mean_p(item_id: str, wording: str, shape: str) -> float:
    return mean([s[CONFLICT] for s in scores(item_id, wording, shape)])


def cmd_compare(args: list[str]) -> None:
    """compare SHAPE_X SHAPE_Y: mean absolute gap of P(conflict) on the built kept pairs and on the 14 real pairs."""
    x, y = args[0], args[1]
    kept = kept_ids()
    built = kept["conflict"] + kept["consistent"]
    for label, ids in (("built kept", built), ("14 real", list(ITEMS))):
        gaps = [abs(mean_p(i, "A", x) - mean_p(i, "A", y)) for i in ids]
        print(f"{label}: mean |{x} - {y}| = {mean(gaps):.3f}  max {max(gaps):.2f}  n={len(ids)}")


def cmd_complement() -> None:
    """T5: the E2 Noul and the 'always' Noul are opposite polarities, so P(true | breaks) + P(true | always) should be 1."""
    kept = kept_ids()
    for label, ids in (("built kept", kept["conflict"] + kept["consistent"]), ("14 real", list(ITEMS))):
        sums = []
        for i in ids:
            a = scores(i, "A", "noul")[0]["conflict"] if False else mean_p(i, "A", "noul")
            b = 1.0 - mean_p(i, "A", "always")  # P(true | always obey)
            sums.append(a + b)
        print(f"{label}: sum of the two answers mean {mean(sums):.3f} min {min(sums):.2f} max {max(sums):.2f}")


def cmd_fixcheck(args: list[str]) -> None:
    """T7: does the conflict probability fall from the before text to the after text?"""
    shape = args[args.index("--shape") + 1] if "--shape" in args else "choice"
    kept = json.loads(FIX_KEPT_FILE.read_text())
    drops = []
    for k in kept:
        before, after = mean_p(k + "b", "A", shape), mean_p(k + "a", "A", shape)
        drops.append(before - after)
        print(f"  {k}: before {before:.2f}  after {after:.2f}  drop {before - after:+.2f}")
    need = 6 if len(kept) >= 8 else -(-len(kept) * 3 // 4)
    seen = sum(d >= 0.15 for d in drops)
    print(f"{shape}: drop of at least 0.15 on {seen} of {len(kept)} kept pairs (need {need}):", "SEES THE FIX" if seen >= need else "does not")


def cmd_report() -> None:
    p: dict[str, dict[str, float]] = {}
    for wording in WORDINGS:
        p[wording] = {}
        for item_id in ITEMS:
            saved = scores(item_id, wording)
            if not saved:
                raise SystemExit(f"no answer for {item_id} wording {wording}; run first")
            p[wording][item_id] = mean([s[CONFLICT] for s in saved])
    result = verdict(p)
    print("CONTROL VERDICT:", "valid" if result["valid"] else "VOID; quote no finding score")
    print("gap (known conflicts minus known consistent):", {w: round(g, 2) for w, g in result["gaps"].items()})
    print("wording noise:", round(result["shift"], 2), " ceiling:", {w: round(c, 2) for w, c in result["ceiling"].items()})
    for item_id, (kind, _, _) in ITEMS.items():
        print(f"{item_id:5}{kind:11}" + "  ".join(f"{w}={p[w][item_id]:.2f}" for w in p))
    print("Jev flags:", ", ".join(result["flagged"]) if result["valid"] and result["flagged"] else "none")


def main(argv: list[str]) -> int:
    commands = {"build": cmd_build, "report": cmd_report, "loo": cmd_loo, "complement": cmd_complement,
                "rates": lambda: cmd_rates(argv[1:]), "run": lambda: cmd_run(argv[1:]),
                "compare": lambda: cmd_compare(argv[1:]), "fixcheck": lambda: cmd_fixcheck(argv[1:])}
    if not argv or argv[0] not in commands:
        print(__doc__)
        return 1
    commands[argv[0]]()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
