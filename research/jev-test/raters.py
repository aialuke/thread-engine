#!/usr/bin/env python3
"""Peer raters for the Jev test: Jev, three LLM raters (Codex, Claude, Grok) and the operator.

    python3 research/jev-test/raters.py brief --set S --corpus C --job J
    python3 research/jev-test/raters.py ingest --rater R --set S --corpus C [--key K] FILE... [--repeat] [--replace]
    python3 research/jev-test/raters.py compare --set S --corpus C --key K --raters codex claude grok [--operator FILE --sample SIDECAR]

There is no ground truth. Every rater is a peer, and every number here is directional, with its n.
All model raters answer the same typed questions (questions.json, via jev.questions_for), so a
post's verdict is computed the same way for each: good = relevant 2, real 2, useful 1 or more.

`brief` prints what an LLM rater is given. `ingest` checks a rater's JSON lines and fails closed:
one bad row, or one post missing or answered twice, and nothing is written; it never overwrites a
rater's file (--replace moves the old one to a timestamped .bak first). Every command goes through
jev.check_block (a final set stays sealed until the freeze) and binds --corpus to --set. `compare` writes
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

import jev  # noqa: E402  (the shared validator, the job map and the final-set seal live there)

STYLE_TYPES = ("promotion", "product-marketing", "engagement-bait")
SEED = 27
RESAMPLES = 1000
OPENING = 30            # characters of post text a rater copies back
OPENING_MATCH = 20      # characters that must match, case and whitespace ignored
SUM_TOLERANCE = jev.SUM_TOLERANCE
THRESHOLDS = (0.5, 0.6, 0.7, 0.8, 0.9, 0.95)
BUCKETS = ((0.0, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0001))
UNSTABLE_UNDEFINED_PCT = 10.0   # a kappa interval with more undefined draws than this is marked unstable
YES, NO, UNSURE = ("post", "reply"), ("no",), "unsure"
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
    spec = spec or jev.load_questions()
    questions = dict(jev.questions_for(job, spec))
    diag = spec.get("diagnostics") or {}
    if isinstance(diag, dict):
        if all(isinstance(v, dict) and "type" in v for v in diag.values()):
            questions.update(diag)
        elif isinstance(diag.get(job), dict):
            questions.update(diag[job])
    return questions


options = jev.options


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
- `parent` (when present): the post that `text` replies to. Use it only to understand what the post is
  answering; every question is still about `post` itself.

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




ANSWER_KEYS = ("id", "opening", "answers", "relevant", "real", "useful", "type", "act")


def parse_lines(text: str) -> tuple[list[dict], list[str]]:
    """JSON objects from a rater's output, whatever their key order. A Grok envelope {"text": ...} is
    unwrapped; a preamble before the object on the same line is skipped. An answer-like object with no
    id, or answer-like text that isn't valid JSON, is a problem (never silently dropped)."""
    try:
        whole = json.loads(text)
        if isinstance(whole, dict) and isinstance(whole.get("text"), str):
            text = whole["text"]
    except json.JSONDecodeError:
        pass
    decoder = json.JSONDecoder()
    parsed, problems = [], []
    for n, line in enumerate(text.split("\n"), 1):
        brace = line.find("{")
        if brace < 0:
            continue
        obj = None
        for i in (k for k, ch in enumerate(line) if ch == "{" and k >= brace):
            try:
                candidate = decoder.raw_decode(line[i:].strip())[0]
            except json.JSONDecodeError:
                continue
            if isinstance(candidate, dict):
                obj = candidate
                break
        answer_like = any(f'"{k}"' in line for k in ANSWER_KEYS)
        if obj is None:
            if answer_like:
                problems.append(f"line {n}: not JSON")
            continue
        if "id" not in obj:
            if answer_like:
                problems.append(f"line {n}: answer with no id")
            continue
        parsed.append(obj)
    return parsed, problems


def squash(text: str) -> str:
    return " ".join(str(text).split()).lower()


def opening_ok(opening, text: str) -> bool:
    if not isinstance(opening, str):
        return False
    want, got = squash(text[:OPENING]), squash(opening)
    need = min(OPENING_MATCH, len(want))
    return len(got) >= need and got[:need] == want[:need]


# One validator for Jev and every peer rater: it lives in jev.py, which this module imports.
is_prob, check_answer = jev.is_prob, jev.check_answer


# ---------- the seal and the corpus binding ----------


def guard(set_name: str, corpus_path: Path | None, private: Path) -> None:
    """jev.check_block for this module: a final set, by name or by corpus file, stays sealed until the freeze."""
    try:
        jev.check_block(set_name, corpus_path, root=Path(private))
    except jev.Stop as exc:
        raise SystemExit(f"stopped: {exc}") from None


def corpus_set(corpus_path: Path) -> str:
    """The set a corpus file holds: splits/stage1-B3-validation.jsonl -> stage1-B3-validation;
    corpus-stage2.jsonl -> stage2; synthetic.jsonl -> synthetic."""
    stem = Path(corpus_path).stem
    return stem[len("corpus-"):] if stem.startswith("corpus-") else stem


def known_set(name: str) -> bool:
    return bool(jev.BLOCK_SET.match(name)) or name in jev.REAL_SETS or name == "synthetic"


def bind(set_name: str, corpus_path: Path, job: str | None = None) -> None:
    """Refuse a --corpus whose file names another stage, block or half than --set, or a --job the set's
    stage doesn't have (jev.job_of)."""
    got = corpus_set(corpus_path)
    if (known_set(set_name) or known_set(got) or jev.BLOCK_IN.search(got)) and got != set_name:
        raise SystemExit(f"--corpus {Path(corpus_path).name} holds {got!r}, not --set {set_name!r}")
    if job is not None and known_set(set_name) and job != jev.job_of(set_name, {}):
        raise SystemExit(f"--job {job} doesn't match {set_name} (its job is {jev.job_of(set_name, {})})")


def ingest(rater: str, set_name: str, files: list[Path], corpus: dict, questions: dict,
           private: Path = PRIVATE, repeat: bool = False, job: str | None = None,
           corpus_path: Path | None = None, replace: bool = False) -> dict:
    """Fail closed, and never overwrite: an existing file for this rater and set is refused unless
    replace=True, which first moves it to a timestamped .bak."""
    guard(set_name, corpus_path, private)
    if corpus_path is not None:
        bind(set_name, corpus_path, job)
    out = rater_file(Path(private), rater, set_name, repeat)
    if out.exists() and not replace:
        raise ValueError(f"{rater} {set_name}: nothing written, {out.name} already exists "
                         "(--replace keeps the old file as .bak)")
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
    out.parent.mkdir(parents=True, exist_ok=True)
    backed_up = jev.backup(out) if out.exists() else None
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in kept), encoding="utf-8")
    tmp.replace(out)
    return {"rater": rater, "set": set_name, "repeat": repeat, "rows": len(kept), "of": len(corpus),
            "renormalised_answers": renormalised, "file": str(out),
            **({"backup": str(backed_up)} if backed_up else {})}


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


def confidence_p50(pg: float) -> float:
    """Confidence in the p_good >= 0.5 verdict: max(p_good, 1 - p_good), always in [0.5, 1]."""
    return max(pg, 1 - pg)


def confidence_good_level(answers: dict | None) -> float | None:
    """Confidence in the most-probable-level verdict (good_level), in [0, 1]: the probability that this verdict
    is right when relevant, real and useful are read as independent. Good: P(all three reach the good levels)
    = p_good. Not good: 1 - p_good. Unlike max(p_good, 1 - p_good) it follows the verdict actually given, so a
    good_level 'good' with a low p_good has low confidence (it can fall below 0.5). None when either is missing."""
    verdict, pg = good_level(answers), p_good(answers)
    if verdict is None or pg is None:
        return None
    return pg if verdict else 1 - pg


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


def bootstrap_detail(ids: list[str], cluster_of: Callable[[str], str], stat: Callable[[list[str]], float | None],
                     resamples: int = RESAMPLES, seed: int = SEED, level: float = 0.90) -> dict:
    """Conversation-clustered bootstrap that keeps undefined draws. A draw where stat is None (kappa when both
    raters are constant the same way) is its own outcome, never dropped silently: the result gives the
    percentile interval over the defined draws, the share of draws that were undefined, and `unstable` when
    that share passes UNSTABLE_UNDEFINED_PCT (the interval then describes only part of the resamples).
    Deterministic for a seed."""
    clusters = clusters_of(ids, cluster_of)
    if not clusters:
        return {"interval": None, "undefined_pct": None, "unstable": None}
    rng = random.Random(seed)
    draws = [stat(resample(clusters, rng)) for _ in range(resamples)]
    values = sorted(v for v in draws if v is not None)
    undefined = pct(len(draws) - len(values), len(draws))
    unstable = undefined is None or undefined > UNSTABLE_UNDEFINED_PCT
    if not values:
        return {"interval": None, "undefined_pct": undefined, "unstable": True}
    lo, hi = (1 - level) / 2, 1 - (1 - level) / 2
    pick = lambda q: values[min(len(values) - 1, max(0, round(q * (len(values) - 1))))]  # noqa: E731
    return {"interval": [round(pick(lo), 3), round(pick(hi), 3)], "undefined_pct": undefined, "unstable": unstable}


def bootstrap(ids: list[str], cluster_of: Callable[[str], str], stat: Callable[[list[str]], float | None],
              resamples: int = RESAMPLES, seed: int = SEED, level: float = 0.90) -> list[float] | None:
    """Percentile interval of stat over the defined draws (see bootstrap_detail for the undefined share)."""
    return bootstrap_detail(ids, cluster_of, stat, resamples, seed, level)["interval"]


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
        k_boot = bootstrap_detail(ids, cluster_of, lambda s: kappa([(a[i], b[i]) for i in s]), resamples, seed)
        out["kappa_ci90"] = k_boot["interval"]
        out["kappa_undefined_pct"] = k_boot["undefined_pct"]
        out["kappa_ci90_unstable"] = k_boot["unstable"]
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


def type_majority(types: list[str]) -> str | None:
    """The type a strict majority of at least two raters chose; None otherwise."""
    if len(types) < 2:
        return None
    top, n = Counter(types).most_common(1)[0]
    return top if n * 2 > len(types) else None


def majority(votes: list[bool]) -> bool | None:
    """Strict majority of at least two votes; ties give None."""
    if len(votes) < 2:
        return None
    yes = sum(votes)
    return True if yes * 2 > len(votes) else False if yes * 2 < len(votes) else None


def coverage(p: dict[str, float], binary: dict[str, bool], panel: dict[str, bool],
             thresholds=THRESHOLDS, confidence: dict[str, float] | None = None) -> dict:
    """For each threshold: share of posts with confidence c >= t and, on those, agreement of the binary
    verdict with the panel majority. Each rule brings its own confidence: by default c = max(p, 1 - p), the
    p_good >= 0.5 rule's (confidence_p50); the good_level curve passes confidence_good_level's values."""
    conf = dict(confidence) if confidence is not None else {i: confidence_p50(v) for i, v in p.items()}
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


def why_group(why_chosen) -> str | None:
    """label-sample sidecar reasons -> 'disputed' | 'random'."""
    why = str(why_chosen or "")
    return "disputed" if why == "disputed" else "random" if why.startswith("random") else None


def compare(set_name: str, private: Path, corpus_key: dict, idea_of: dict, operator: dict | None,
            raters: list[str], seed: int = SEED, resamples: int = RESAMPLES,
            corpus_path: Path | None = None, sample: dict | None = None) -> dict:
    """sample: the label-sample sidecar (labelling.py) the operator's labels came from; it splits the
    operator's agreement by why each post was chosen (disputed or random). On a final set the frozen cut-off
    is applied once and reported as the pre-registered result; the full curves are exploratory there."""
    private = Path(private)
    guard(set_name, corpus_path, private)
    if corpus_path is not None:
        bind(set_name, corpus_path)

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
            row["jev_vs"][other] = pair_stats({i: v for i, v in binary[JEV].items() if i in ids}, binary[other],
                                              cluster_of, seed, resamples, ("jev", "other"))
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
    styled = {pid for pid, ts in types.items() if type_majority(ts) in STYLE_TYPES}
    def vs_panel(ids: set) -> dict:
        judged = [i for i in ids if i in panel and i in binary[JEV]]
        return {"n": len(judged), "agreement_pct": pct(sum(binary[JEV][i] == panel[i] for i in judged), len(judged))}
    style_slice = {"types": list(STYLE_TYPES), "styled": vs_panel(styled), "rest": vs_panel(set(panel) - styled)}
    # Invalid outputs counted as errors (their checklist item 3), next to the valid-only figure.
    jev_valid = [i for i in panel if i in binary[JEV]]
    invalid_as_error = {"n": len(panel), "valid_only_pct": pct(sum(binary[JEV][i] == panel[i] for i in jev_valid), len(jev_valid)),
                        "invalid_counted_wrong_pct": pct(sum(binary[JEV][i] == panel[i] for i in jev_valid), len(panel))}

    level_conf = {i: c for i, a in answers[JEV].items() if (c := confidence_good_level(a)) is not None}
    curves = {"good_level": coverage(pgood[JEV], binary[JEV], panel, confidence=level_conf),
              "p_good_0.5": coverage(pgood[JEV], binary[JEV_P50], panel)}
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
                         "confidence": {"p_good_0.5": "max(p_good, 1 - p_good)",
                                        "good_level": "p_good when the verdict is good, 1 - p_good when not"},
                         **curves},
    }
    block = jev.BLOCK_SET.match(set_name)
    if block and block.group(3) == "final" and not block.group(4):
        frozen = jev.thresholds(private.parent / "thresholds.json")
        cut, rule = frozen["frozen_coverage_threshold"], frozen.get("frozen_coverage_rule", "p_good_0.5")
        if rule == "good_level":
            point = coverage(pgood[JEV], binary[JEV], panel, (cut,), level_conf)
        else:
            point = coverage(pgood[JEV], binary[JEV_P50], panel, (cut,))
        at = point["curve"][0]
        report["preregistered"] = {"rule": rule, "coverage_threshold": cut, "frozen_at": frozen.get("frozen_at"),
                                   "share_pct": at["share_pct"], "posts": at["posts"], "of": point["posts"],
                                   "n": at["n"], "agreement_pct": at["agreement_pct"],
                                   "note": "the cut-off chosen on validation and frozen, applied once: this is the result"}
        report["jev_coverage"]["status"] = "exploratory: on a final set only 'preregistered' is the result"
    if operator is not None:
        labels = [x for x in operator.get("labels", []) if x.get("label") in YES + NO]
        replies = [x["id"] for x in labels if x["label"] == "reply"]
        op = {"answered": len(labels), "reply_n": len(replies), "reply_pct": pct(len(replies), len(labels))}
        noul = {i: a["reply_worthy"]["noul"] for i, a in answers[JEV].items()
                if isinstance(a.get("reply_worthy"), dict) and a["reply_worthy"].get("noul") is not None}
        if noul:
            pos = [noul[x["id"]] for x in labels if x["label"] == "reply" and x["id"] in noul]
            neg = [noul[x["id"]] for x in labels if x["label"] != "reply" and x["id"] in noul]
            op["jev_reply_worthy_auc"] = {"auc": jev.auc(pos, neg), "n_reply": len(pos), "n_not_reply": len(neg)}
        decidable = {i: a["text_decidable"]["noul"] for i, a in answers[JEV].items()
                     if isinstance(a.get("text_decidable"), dict) and a["text_decidable"].get("noul") is not None}
        if decidable:
            answered = [decidable[x["id"]] for x in labels if x["id"] in decidable]
            unsure = [decidable[x["id"]] for x in operator.get("labels", []) if x.get("label") == UNSURE
                      and x.get("id") in decidable]
            op["jev_text_decidable_auc"] = {
                "auc": jev.auc(answered, unsure), "n_answered": len(answered), "n_unsure": len(unsure),
                "note": "answered (post, reply, no) vs unsure; above 0.5 means Jev's text_decidable is higher "
                        "where the operator could decide"}
        if sample is not None:
            if operator.get("sample") and sample.get("sample") and operator["sample"] != sample["sample"]:
                raise SystemExit(f"operator labels are for sample {operator['sample']}, the sidecar is {sample['sample']}")
            why = {p["id"]: g for p in sample.get("posts", []) if (g := why_group(p.get("why_chosen")))}
            split = {}
            for group in ("disputed", "random"):
                ids = {i for i, g in why.items() if g == group}
                mine = {i: v for i, v in binary[OPERATOR].items() if i in ids}
                vs = {other: pair_stats(binary[other], mine, cluster_of, seed, resamples, ("rater", "operator"))
                      for other in people if other != OPERATOR}
                vs["panel"] = pair_stats(panel, mine, cluster_of, seed, resamples, ("rater", "operator"))
                split[group] = {"posts": len(ids), "operator_answered": len(mine), "vs": vs}
            op["by_why_chosen"] = split
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
    job = jobs.pop()
    if known_set(set_name) and job != jev.job_of(set_name, {}):
        raise SystemExit(f"{set_name}: the corpus rows say {job}, the set's stage says {jev.job_of(set_name, {})}")
    return job


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
    p.add_argument("--replace", action="store_true", help="move the existing file to a timestamped .bak first")
    p.add_argument("--private", default=str(PRIVATE))
    p.add_argument("files", nargs="+")
    p = sub.add_parser("compare")
    p.add_argument("--set", required=True, dest="set_name")
    p.add_argument("--corpus", required=True)
    p.add_argument("--key", required=True)
    p.add_argument("--raters", nargs="+", required=True)
    p.add_argument("--operator")
    p.add_argument("--sample", help="the label-sample sidecar the operator's labels came from")
    p.add_argument("--private", default=str(PRIVATE))
    args = parser.parse_args(argv)

    if args.command == "brief":
        guard(args.set_name, Path(args.corpus), PRIVATE)
        bind(args.set_name, Path(args.corpus), args.job)
        print(rater_brief(args.set_name, spec_questions(args.job), args.corpus, args.job))
    elif args.command == "ingest":
        guard(args.set_name, Path(args.corpus), Path(args.private))
        bind(args.set_name, Path(args.corpus))
        corpus = load_corpus(Path(args.corpus))
        job = set_job(args.set_name, corpus)
        try:
            result = ingest(args.rater, args.set_name, [Path(f) for f in args.files], corpus,
                            spec_questions(job), Path(args.private), args.repeat, job,
                            corpus_path=Path(args.corpus), replace=args.replace)
        except ValueError as exc:
            print(f"stopped: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, indent=1))
    elif args.command == "compare":
        guard(args.set_name, Path(args.corpus), Path(args.private))
        bind(args.set_name, Path(args.corpus))
        corpus = load_corpus(Path(args.corpus))
        operator = json.loads(Path(args.operator).expanduser().read_text(encoding="utf-8")) if args.operator else None
        sample = json.loads(Path(args.sample).expanduser().read_text(encoding="utf-8")) if args.sample else None
        report = compare(args.set_name, Path(args.private), load_key(Path(args.key)),
                         {i: r.get("idea") for i, r in corpus.items()}, operator, args.raters,
                         corpus_path=Path(args.corpus), sample=sample)
        print(json.dumps(report, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
