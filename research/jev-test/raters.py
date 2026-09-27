#!/usr/bin/env python3
"""Peer raters for the Jev test: Jev, three LLM raters (Codex, Claude, Grok) and the operator.

    python3 research/jev-test/raters.py brief --set S --corpus C --job J
    python3 research/jev-test/raters.py ingest --rater R --set S --corpus C [--key K] FILE... [--repeat]
    python3 research/jev-test/raters.py compare --set S --corpus C --key K --raters codex claude grok [--operator FILE]

There is no ground truth. Every rater is a peer, and every number here is directional, with its n.
All model raters answer the same typed questions (questions.json, via jev.questions_for), so a
post's verdict is computed the same way for each: good = relevant 2, real 2, useful 1 or more.

`brief` prints what an LLM rater is given. `ingest` checks a rater's JSON lines and fails closed:
one bad row, or one post missing or answered twice, and nothing is written. `compare` writes
private/compare-raters-<set>.json: pairwise agreement and Cohen's kappa with 90% bootstrap
intervals that resample conversations, soft agreement on p_good, self-agreement from repeat runs,
per-idea agreement, Jev's coverage curve against the panel majority, and the operator's labels.

Files (private/, gitignored; other people's posts; delete by 26 Mar 2027):
    answers-<set>.jsonl                 Jev (jev.py run)
    raters/<rater>-<set>.jsonl          an LLM rater (ingest)
    raters/<rater>-<set>-repeat.jsonl   the same rater run again (ingest --repeat)
No network, no Keychain.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Callable
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIVATE = HERE / "private"
sys.path.insert(0, str(HERE))

try:
    import jev  # noqa: E402
except ImportError:  # pragma: no cover - jev.py lives next to this file
    jev = None

STYLE_TYPES = ("promotion", "product-marketing", "engagement-bait")
SEED = 27
RESAMPLES = 1000
OPENING = 30            # characters of post text a rater copies back
OPENING_MATCH = 20      # characters that must match, case and whitespace ignored
SUM_TOLERANCE = 0.05
THRESHOLDS = (0.5, 0.6, 0.7, 0.8, 0.9, 0.95)
BUCKETS = ((0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0001))
YES, NO = ("post", "reply"), ("no",)
JEV, JEV_P50, OPERATOR = "jev", "jev (p_good>=0.5)", "operator"
DIRECTIONAL = "Directional only: no ground truth, every rater is a peer, and n is small. Read agreement, not accuracy."


# ---------- files ----------


def rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    # split on \n only: str.splitlines() also breaks on U+2028/U+0085 inside post text
    return [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line.strip()]


def load_corpus(path: Path) -> dict:
    return {r["id"]: r for r in rows(Path(path))}


def load_key(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def ensure_private(private: Path) -> None:
    private.mkdir(parents=True, exist_ok=True)
    ignore = private / ".gitignore"
    if not ignore.exists():
        ignore.write_text("*\n!.gitignore\n", encoding="utf-8")


def rater_file(private: Path, rater: str, set_name: str, repeat: bool = False) -> Path:
    if rater == JEV and not repeat:
        return private / f"answers-{set_name}.jsonl"
    return private / "raters" / f"{rater}-{set_name}{'-repeat' if repeat else ''}.jsonl"


# ---------- questions ----------


def spec_questions(job: str, spec: dict | None = None) -> dict:
    """The main questions for a job plus any diagnostics (flat, or keyed by job)."""
    if jev is None:  # pragma: no cover
        raise SystemExit("jev.py is not importable next to raters.py")
    spec = spec or jev.load_questions()
    questions = dict(jev.questions_for(job, spec))
    diag = spec.get("diagnostics") or {}
    if isinstance(diag, dict):
        if all(isinstance(v, dict) and "type" in v for v in diag.values()):
            questions.update(diag)
        elif isinstance(diag.get(job), dict):
            questions.update(diag[job])
    return questions


def options(question: dict) -> list[str]:
    """The levels of a score ("0", "1", "2") or the options of a choice."""
    criteria = question.get("criteria")
    if question["type"] == "score":
        return [str(n) for n in range(len(criteria) if isinstance(criteria, list) else 3)]
    return list(criteria) if isinstance(criteria, dict) else list(criteria or [])


def answer_shape(question: dict) -> str:
    if question["type"] == "noul":
        return '{"noul": p}'
    return '{"probabilities": {' + ", ".join(f'"{o}": p' for o in options(question)) + "}}"


def example_answer(question: dict) -> dict:
    """A well-formed placeholder answer (even spread) for the brief's example line."""
    if question["type"] == "noul":
        return {"noul": 0.5}
    opts = options(question)
    share = round(1 / len(opts), 2)
    return {"probabilities": {o: share if n < len(opts) - 1 else round(1 - share * (len(opts) - 1), 2)
                              for n, o in enumerate(opts)}}


# ---------- brief ----------


def rater_brief(set_name: str, questions: dict, corpus_file: str, job: str) -> str:
    listing = "\n".join(f"- `{qid}` ({q['type']}): answer as {answer_shape(q)}" for qid, q in questions.items())
    example = {"id": "<id>", "opening": "<first 30 characters of text, copied exactly>",
               "answers": {qid: example_answer(q) for qid, q in questions.items()}}
    return f"""# Rater brief: set {set_name}, job {job}

You are one of several independent raters of X posts. Rate every post in `{corpus_file}` (one JSON
object per line) against the questions below. Other raters answer the same questions; you will not
see their answers and they will not see yours.

## Each post's fields

- `id`: the post's id. Copy it exactly.
- `idea`: what the search was for. Questions call it `idea`.
- `text`: the post itself. Questions call it `post`.
- `replies` (when present): replies already under the post. Use them only to judge whether the
  conversation is live and worth joining.
- `age_hours` (when present): how old the post was when collected. Use it only to judge whether
  the conversation is still worth joining.

Judge only from these fields. Do not search, open links, or look anything up.

## Questions (verbatim JSON: ids, types, instructions and criteria)

```json
{json.dumps(questions, indent=1, ensure_ascii=False)}
```

Score questions have levels "0", "1", "2", in the order of their criteria. A choice's options are
the keys of its criteria. A noul is one probability that the statement is true.

{listing}

## Output

One JSON line per post, and nothing else: no preamble, no code fences, no commentary.

```
{json.dumps(example, ensure_ascii=False)}
```

- `opening` is the first {OPENING} characters of the post's `text`, copied exactly.
- Every question id appears in `answers` for every post.
- For each score and choice, `probabilities` covers every level or option, each between 0 and 1,
  summing to 1. Put your uncertainty in the probabilities; do not round to 0 and 1 unless sure.
- A noul is `{{"noul": p}}` with p between 0 and 1.
- Every post in the file gets exactly one line.
"""


# ---------- ingest ----------


LINE_START = re.compile(r'\{\s*"id"')


def parse_lines(text: str) -> tuple[list[dict], list[str]]:
    """JSON lines from a rater's output. A Grok envelope {"text": ...} is unwrapped; a preamble on
    the same line as the first answer is skipped. Lines with no answer are ignored."""
    try:
        whole = json.loads(text)
        if isinstance(whole, dict) and isinstance(whole.get("text"), str):
            text = whole["text"]
    except json.JSONDecodeError:
        pass
    parsed, problems = [], []
    for n, line in enumerate(text.split("\n"), 1):
        match = LINE_START.search(line)
        if not match:
            continue
        chunk = line[match.start():].strip()
        try:
            parsed.append(json.JSONDecoder().raw_decode(chunk)[0])
        except json.JSONDecodeError as exc:
            problems.append(f"line {n}: not JSON ({exc.msg})")
    return parsed, problems


def squash(text: str) -> str:
    return " ".join(str(text).split()).lower()


def opening_ok(opening, text: str) -> bool:
    if not isinstance(opening, str):
        return False
    want, got = squash(text[:OPENING]), squash(opening)
    need = min(OPENING_MATCH, len(want))
    return len(got) >= need and got[:need] == want[:need]


def is_prob(p) -> bool:
    return isinstance(p, (int, float)) and not isinstance(p, bool) and 0.0 <= p <= 1.0


def check_answer(qid: str, question: dict, answer) -> tuple[dict | None, str | None]:
    """A cleaned answer in Jev's shape, or a problem."""
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


def ingest(rater: str, set_name: str, files: list[Path], corpus: dict, questions: dict,
           private: Path = PRIVATE, repeat: bool = False, job: str | None = None) -> dict:
    parsed, problems = [], []
    for f in files:
        got, bad = parse_lines(Path(f).read_text(encoding="utf-8"))
        parsed += got
        problems += [f"{Path(f).name} {b}" for b in bad]
    seen: dict[str, int] = defaultdict(int)
    kept, renormalised = [], 0
    for row in parsed:
        pid = row.get("id")
        seen[pid] += 1
        if pid not in corpus:
            problems.append(f"{pid}: not in the corpus")
            continue
        if seen[pid] > 1:
            continue
        if not opening_ok(row.get("opening"), corpus[pid].get("text", "")):
            problems.append(f"{pid}: opening does not match the post")
            continue
        answers, bad = {}, []
        for qid, question in questions.items():
            clean, problem = check_answer(qid, question, (row.get("answers") or {}).get(qid))
            if problem:
                bad.append(problem)
            else:
                answers[qid] = clean
                raw = ((row.get("answers") or {}).get(qid) or {}).get("probabilities")
                renormalised += bool(raw) and abs(sum(raw.values()) - 1.0) > 1e-9
        if bad:
            problems.append(f"{pid}: " + "; ".join(bad))
            continue
        kept.append({"id": pid, "job": job, "rater": rater, "answers": answers})
    problems += [f"{pid}: answered {n} times" for pid, n in seen.items() if n > 1 and pid in corpus]
    problems += [f"{pid}: missing" for pid in corpus if pid not in seen]
    if problems:
        raise ValueError(f"{rater} {set_name}: nothing written, {len(problems)} problem(s):\n" + "\n".join(problems))
    ensure_private(private)
    out = rater_file(private, rater, set_name, repeat)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in kept), encoding="utf-8")
    tmp.replace(out)
    return {"rater": rater, "set": set_name, "repeat": repeat, "rows": len(kept), "of": len(corpus),
            "renormalised_answers": renormalised, "file": str(out)}


# ---------- goodness ----------


def _probs(answers: dict, qid: str) -> dict | None:
    probs = (answers.get(qid) or {}).get("probabilities")
    return {str(k): v for k, v in probs.items()} if probs else None


def p_good(answers: dict | None) -> float | None:
    """P(relevant = 2) * P(real = 2) * P(useful >= 1)."""
    if not answers:
        return None
    rel, real, use = (_probs(answers, q) for q in ("relevant", "real", "useful"))
    if not (rel and real and use):
        return None
    return rel.get("2", 0.0) * real.get("2", 0.0) * (use.get("1", 0.0) + use.get("2", 0.0))


def most_probable(answer: dict | None) -> int | None:
    """The most probable Score level (ties go to the lower level)."""
    probs = (answer or {}).get("probabilities") or {}
    if not probs:
        return None
    return min((-p, int(k)) for k, p in probs.items())[1]


def good_level(answers: dict | None) -> bool | None:
    if not answers:
        return None
    levels = [most_probable(answers.get(q)) for q in ("relevant", "real", "useful")]
    if any(v is None for v in levels):
        return None
    return levels[0] == 2 and levels[1] == 2 and levels[2] >= 1


# ---------- statistics ----------


def pct(hits: float, total: int) -> float | None:
    return round(100 * hits / total, 1) if total else None


def kappa(pairs: list[tuple[bool, bool]]) -> float | None:
    """Cohen's kappa for two binary raters. None when chance agreement is 1 (both constant, same way)."""
    n = len(pairs)
    if not n:
        return None
    po = sum(a == b for a, b in pairs) / n
    pa, pb = sum(a for a, _ in pairs) / n, sum(b for _, b in pairs) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    if pe >= 1 - 1e-12:
        return None
    return (po - pe) / (1 - pe)


def agree_pct(pairs: list[tuple[bool, bool]]) -> float | None:
    return 100 * sum(a == b for a, b in pairs) / len(pairs) if pairs else None


def clusters_of(ids: list[str], cluster_of: Callable[[str], str]) -> list[list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for i in sorted(ids):
        groups[cluster_of(i)].append(i)
    return [groups[k] for k in sorted(groups)]


def resample(clusters: list[list[str]], rng: random.Random) -> list[str]:
    """One bootstrap draw: whole conversations, with replacement."""
    return [i for _ in clusters for i in rng.choice(clusters)]


def bootstrap(ids: list[str], cluster_of: Callable[[str], str], stat: Callable[[list[str]], float | None],
              resamples: int = RESAMPLES, seed: int = SEED, level: float = 0.90) -> list[float] | None:
    """Percentile interval of stat over conversation-clustered resamples. Deterministic for a seed."""
    clusters = clusters_of(ids, cluster_of)
    if not clusters:
        return None
    rng = random.Random(seed)
    values = sorted(v for v in (stat(resample(clusters, rng)) for _ in range(resamples)) if v is not None)
    if not values:
        return None
    lo, hi = (1 - level) / 2, 1 - (1 - level) / 2
    pick = lambda q: values[min(len(values) - 1, max(0, round(q * (len(values) - 1))))]  # noqa: E731
    return [round(pick(lo), 3), round(pick(hi), 3)]


def pair_stats(a: dict, b: dict, cluster_of: Callable[[str], str] | None = None, seed: int = SEED,
               resamples: int = RESAMPLES, names: tuple[str, str] = ("a", "b")) -> dict:
    """a, b: id -> bool. Agreement, kappa and each side's yes rate on the posts both have."""
    ids = sorted(set(a) & set(b))
    pairs = [(a[i], b[i]) for i in ids]
    k = kappa(pairs)
    out = {"n": len(ids), "agreement_pct": None if not pairs else round(agree_pct(pairs), 1),
           "kappa": None if k is None else round(k, 3),
           f"yes_pct_{names[0]}": pct(sum(x for x, _ in pairs), len(pairs)),
           f"yes_pct_{names[1]}": pct(sum(y for _, y in pairs), len(pairs))}
    if cluster_of is not None and ids:
        out["agreement_ci90"] = bootstrap(ids, cluster_of, lambda s: agree_pct([(a[i], b[i]) for i in s]),
                                          resamples, seed)
        out["kappa_ci90"] = bootstrap(ids, cluster_of, lambda s: kappa([(a[i], b[i]) for i in s]), resamples, seed)
        out["conversations"] = len(clusters_of(ids, cluster_of))
    return out


def soft_agreement(p: dict[str, dict[str, float]]) -> dict:
    """p: rater -> id -> p_good. For each rater, mean |own p_good - mean of the others'| on posts all have."""
    names = sorted(p)
    if len(names) < 2:
        return {"n": 0, "raters": {}}
    ids = sorted(set.intersection(*(set(p[r]) for r in names)))
    out = {}
    for r in names:
        others = [o for o in names if o != r]
        gaps = [abs(p[r][i] - sum(p[o][i] for o in others) / len(others)) for i in ids]
        out[r] = round(sum(gaps) / len(gaps), 3) if gaps else None
    return {"n": len(ids), "raters": out, "note": "mean |p_good - mean p_good of the other model raters|; lower is closer"}


def majority(votes: list[bool]) -> bool | None:
    """Strict majority of at least two votes; ties give None."""
    if len(votes) < 2:
        return None
    yes = sum(votes)
    return True if yes * 2 > len(votes) else False if yes * 2 < len(votes) else None


def coverage(p: dict[str, float], binary: dict[str, bool], panel: dict[str, bool],
             thresholds=THRESHOLDS) -> dict:
    """Confidence c = max(p, 1 - p). For each threshold: share of posts with c >= t and, on those,
    agreement of the binary verdict with the panel majority."""
    conf = {i: max(v, 1 - v) for i, v in p.items()}
    total = len(conf)
    curve = []
    for t in thresholds:
        covered = [i for i, c in conf.items() if c >= t - 1e-12]
        judged = [i for i in covered if i in panel and i in binary]
        curve.append({"threshold": t, "share_pct": pct(len(covered), total), "posts": len(covered),
                      "n": len(judged), "agreement_pct": pct(sum(binary[i] == panel[i] for i in judged), len(judged))})
    calibration = []
    for lo, hi in BUCKETS:
        judged = [i for i, c in conf.items() if lo - 1e-12 <= c < hi and i in panel and i in binary]
        calibration.append({"confidence": f"{lo:.1f}-{min(hi, 1.0):.1f}", "n": len(judged),
                            "mean_confidence": round(sum(conf[i] for i in judged) / len(judged), 3) if judged else None,
                            "agreement_pct": pct(sum(binary[i] == panel[i] for i in judged), len(judged))})
    # Baselines (Li et al., JEV-as-a-Judge): taking the same share of posts at random agrees at the overall
    # rate; and the AUROC of confidence against agreement says whether confident means right (0.5 = no signal).
    judged_all = [i for i in conf if i in panel and i in binary]
    agree = {i: binary[i] == panel[i] for i in judged_all}
    random_pct = pct(sum(agree.values()), len(judged_all))
    for point in curve:
        point["random_same_share_agreement_pct"] = random_pct
    right = [conf[i] for i in judged_all if agree[i]]
    wrong = [conf[i] for i in judged_all if not agree[i]]
    auroc = (round(sum(1.0 if r > w else 0.5 if r == w else 0.0 for r in right for w in wrong) / (len(right) * len(wrong)), 3)
             if right and wrong else None)
    return {"posts": total, "curve": curve, "calibration": calibration,
            "confidence_auroc": {"auroc": auroc, "n_agree": len(right), "n_disagree": len(wrong),
                                 "note": "near 0.5 means confident disagreements: the take-over idea fails"}}


# ---------- compare ----------


def load_rater(path: Path) -> tuple[dict, int, bool]:
    """(id -> answers for available rows, unavailable count, file exists)."""
    answers, unavailable = {}, 0
    for r in rows(path):
        if r.get("unavailable") or r.get("answers") is None:
            unavailable += 1
            continue
        answers[r["id"]] = r["answers"]
    return answers, unavailable, path.exists()


def operator_binary(operator: dict) -> dict[str, bool]:
    return {x["id"]: x["label"] in YES for x in operator.get("labels", []) if x.get("label") in YES + NO}


def compare(set_name: str, private: Path, corpus_key: dict, idea_of: dict, operator: dict | None,
            raters: list[str], seed: int = SEED, resamples: int = RESAMPLES) -> dict:
    private = Path(private)

    def cluster_of(pid: str) -> str:
        k = corpus_key.get(pid) or {}
        return str(k.get("conversation_id") or k.get("post_id") or pid)

    model = [JEV] + [r for r in raters if r != JEV]
    answers, files = {}, {}
    for r in model:
        answers[r], unavailable, exists = load_rater(rater_file(private, r, set_name))
        files[r] = {"available": len(answers[r]), "unavailable": unavailable, "file_found": exists}
    binary = {r: {i: v for i, a in answers[r].items() if (v := good_level(a)) is not None} for r in model}
    pgood = {r: {i: v for i, a in answers[r].items() if (v := p_good(a)) is not None} for r in model}
    binary[JEV_P50] = {i: v >= 0.5 for i, v in pgood[JEV].items()}
    people = model + [JEV_P50]
    if operator is not None:
        binary[OPERATOR] = operator_binary(operator)
        people.append(OPERATOR)
        files[OPERATOR] = {"available": len(binary[OPERATOR]),
                           "excluded_unsure_or_blank": len(operator.get("labels", [])) - len(binary[OPERATOR])}

    selfs = {}
    for r in model:
        path = rater_file(private, r, set_name, repeat=True)
        if path.exists():
            again, unavailable, _ = load_rater(path)
            second = {i: v for i, a in again.items() if (v := good_level(a)) is not None}
            selfs[r] = {**pair_stats(binary[r], second, cluster_of, seed, resamples, ("first", "repeat")),
                        "repeat_unavailable": unavailable}

    pairwise = []
    for a, b in combinations(people, 2):
        if {a, b} == {JEV, JEV_P50}:
            continue
        entry = {"a": a, "b": b, **pair_stats(binary[a], binary[b], cluster_of, seed, resamples, ("a", "b"))}
        ceiling = {x: selfs[x]["agreement_pct"] for x in (a, b) if x in selfs}
        if ceiling:
            entry["self_agreement_ceiling_pct"] = ceiling
        pairwise.append(entry)

    ideas: dict[str, list[str]] = defaultdict(list)
    for pid, idea in idea_of.items():
        ideas[idea].append(pid)
    per_idea = []
    for idea in sorted(ideas):
        ids = set(ideas[idea])
        row = {"idea": idea, "posts": len(ids), "jev_vs": {}}
        for other in [p for p in people if p not in (JEV, JEV_P50)]:
            s = pair_stats({i: v for i, v in binary[JEV].items() if i in ids}, binary[other])
            row["jev_vs"][other] = {k: s[k] for k in ("n", "agreement_pct", "kappa")}
        per_idea.append(row)

    llm = [r for r in model if r != JEV]
    panel = {}
    for pid in set().union(*(binary[r] for r in llm)) if llm else set():
        verdict = majority([binary[r][pid] for r in llm if pid in binary[r]])
        if verdict is not None:
            panel[pid] = verdict

    # Promotion written to look genuine is the style-adversarial case (Li et al.): report Jev on it apart.
    types: dict[str, list] = defaultdict(list)
    for r in llm:
        for pid, a in answers[r].items():
            t = (a.get("type") or {}).get("choice") if isinstance(a.get("type"), dict) else None
            if t is None and isinstance(a.get("type"), dict) and a["type"].get("probabilities"):
                t = max(a["type"]["probabilities"].items(), key=lambda kv: kv[1])[0]
            if t:
                types[pid].append(t)
    styled = {pid for pid, ts in types.items() if Counter(ts).most_common(1)[0][0] in STYLE_TYPES
              and Counter(ts).most_common(1)[0][1] * 2 > len(ts)}
    def vs_panel(ids: set) -> dict:
        judged = [i for i in ids if i in panel and i in binary[JEV]]
        return {"n": len(judged), "agreement_pct": pct(sum(binary[JEV][i] == panel[i] for i in judged), len(judged))}
    style_slice = {"types": list(STYLE_TYPES), "styled": vs_panel(styled), "rest": vs_panel(set(panel) - styled)}
    # Invalid outputs counted as errors (their checklist item 3), next to the valid-only figure.
    jev_valid = [i for i in panel if i in binary[JEV]]
    invalid_as_error = {"n": len(panel), "valid_only_pct": pct(sum(binary[JEV][i] == panel[i] for i in jev_valid), len(jev_valid)),
                        "invalid_counted_wrong_pct": pct(sum(binary[JEV][i] == panel[i] for i in jev_valid), len(panel))}

    report = {
        "set": set_name, "note": DIRECTIONAL,
        "jev_vs_panel": {"invalid_as_error": invalid_as_error, "style_adversarial": style_slice},
        "rule": "good = relevant 2, real 2, useful >= 1 by each question's most probable level (ties to the lower); "
                f"'{JEV_P50}' uses P(good) = P(relevant 2) * P(real 2) * P(useful >= 1) >= 0.5 instead",
        "raters": files,
        "bootstrap": {"resamples": resamples, "seed": seed, "interval": "90% percentile",
                      "unit": "conversation (conversation_id; missing gives the post its own)"},
        "pairwise": pairwise,
        "self_agreement": selfs,
        "soft_agreement": soft_agreement({r: pgood[r] for r in model if pgood[r]}),
        "per_idea": per_idea,
        "jev_coverage": {"panel": llm, "panel_rule": "strict majority of the LLM raters' verdicts, at least two; ties excluded",
                         "good_level": coverage(pgood[JEV], binary[JEV], panel),
                         "p_good_0.5": coverage(pgood[JEV], binary[JEV_P50], panel)},
    }
    if operator is not None:
        labels = [x for x in operator.get("labels", []) if x.get("label") in YES + NO]
        replies = [x["id"] for x in labels if x["label"] == "reply"]
        op = {"answered": len(labels), "reply_n": len(replies), "reply_pct": pct(len(replies), len(labels))}
        noul = {i: a["reply_worthy"]["noul"] for i, a in answers[JEV].items()
                if isinstance(a.get("reply_worthy"), dict) and a["reply_worthy"].get("noul") is not None}
        if noul:
            pos = [noul[x["id"]] for x in labels if x["label"] == "reply" and x["id"] in noul]
            neg = [noul[x["id"]] for x in labels if x["label"] != "reply" and x["id"] in noul]
            op["jev_reply_worthy_auc"] = {"auc": jev.auc(pos, neg) if jev else None,
                                          "n_reply": len(pos), "n_not_reply": len(neg)}
        report["operator"] = op
    ensure_private(private)
    out = private / f"compare-raters-{set_name}.json"
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(out)
    return report


# ---------- CLI ----------


def set_job(set_name: str, corpus: dict) -> str:
    jobs = {jev.job_of(set_name, r) for r in corpus.values()}
    if len(jobs) != 1:
        raise SystemExit(f"{set_name}: expected one job across the corpus, found {sorted(jobs)}")
    return jobs.pop()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Peer raters for the Jev test (directional, no ground truth).")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("brief")
    p.add_argument("--set", required=True, dest="set_name")
    p.add_argument("--corpus", required=True)
    p.add_argument("--job", required=True)
    p = sub.add_parser("ingest")
    p.add_argument("--rater", required=True)
    p.add_argument("--set", required=True, dest="set_name")
    p.add_argument("--corpus", required=True)
    p.add_argument("--key")
    p.add_argument("--repeat", action="store_true")
    p.add_argument("--private", default=str(PRIVATE))
    p.add_argument("files", nargs="+")
    p = sub.add_parser("compare")
    p.add_argument("--set", required=True, dest="set_name")
    p.add_argument("--corpus", required=True)
    p.add_argument("--key", required=True)
    p.add_argument("--raters", nargs="+", required=True)
    p.add_argument("--operator")
    p.add_argument("--private", default=str(PRIVATE))
    args = parser.parse_args(argv)

    if args.command == "brief":
        print(rater_brief(args.set_name, spec_questions(args.job), args.corpus, args.job))
    elif args.command == "ingest":
        corpus = load_corpus(Path(args.corpus))
        job = set_job(args.set_name, corpus)
        try:
            result = ingest(args.rater, args.set_name, [Path(f) for f in args.files], corpus,
                            spec_questions(job), Path(args.private), args.repeat, job)
        except ValueError as exc:
            print(f"stopped: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, indent=1))
    elif args.command == "compare":
        corpus = load_corpus(Path(args.corpus))
        operator = json.loads(Path(args.operator).expanduser().read_text(encoding="utf-8")) if args.operator else None
        report = compare(args.set_name, Path(args.private), load_key(Path(args.key)),
                         {i: r.get("idea") for i, r in corpus.items()}, operator, args.raters)
        print(json.dumps(report, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
