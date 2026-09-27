#!/usr/bin/env python3
"""Jev experiment 4: the B4 query-design arms, as totals and rates (README.md, Experiment 4).

    python3 research/jev-test/arms.py --block B4 [--operator FILE]

Reads the rater answers for every sealed set of the block (both halves, and the -parent sets), the
harness's manifest (which query found each post), the stage corpora's keys, the Worth-joining ages and
the parents file. Writes private/arms-<block>.json and prints it. No post text, no ids of other people's
posts in the output. No network.

"Good" is the current product rule, relevant 2, real 2 and useful 1 or more by each question's most
probable level (raters.good_level, is_good here), and the panel is the strict majority of the LLM raters (Codex,
Claude, Grok): the same panel as raters.py compare and B3's lessons. Jev is also read by its frozen rule,
P(relevant 2) x P(real 2) x P(useful >= 1) >= 0.5. Arm 5's three-question rule is type genuine (most
probable) AND outside_domain < 0.5 AND reply_worthy >= 0.5. Directional only: there is no answer key.

Fails closed: a set with a rater file missing, or a rater file that doesn't cover its set, stops the run.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import jev  # noqa: E402
import raters  # noqa: E402

LLM = ("codex", "claude", "grok")
JEV = raters.JEV
STAGE_JOB = {1: "worth-joining", 2: "demand", 3: "tool-research"}
CURRENT_WJ = ("wj-tech-1", "wj-tech-2", "wj-comedy-1", "wj-comedy-2")
CARD_PAIRS = (("wj-comedy-1", "wj-comedy-1b"), ("wj-tech-2", "wj-tech-2b"))
PROMO = ("promotion", "product-marketing", "engagement-bait", "account-selling")
AGE_BUCKETS = (("<=1h", None, 1.0), ("1-2h", 1.0, 2.0), ("over 2h", 2.0, None))   # (lo exclusive, hi inclusive)
LINK = "https://t.co/"
NOTE = ("Directional only. Good = the Codex/Claude/Grok strict majority on the current rule (relevant 2, real 2, "
        "useful >= 1, most probable levels) unless a rule says otherwise; Jev is also read at p_good >= 0.5, its "
        "frozen rule. No ground truth. Totals and rates only.")


class Stop(Exception):
    """A missing or incomplete input. Nothing is written."""


# ---------- per-rater verdicts ----------


def is_good(a: dict | None) -> bool | None:
    """The current product rule: relevant 2, real 2, useful >= 1 by most probable level."""
    return raters.good_level(a)


def good_p50(a: dict | None) -> bool | None:
    """Jev's frozen rule (B3): p_good >= 0.5."""
    pg = raters.p_good(a)
    return None if pg is None else pg >= 0.5


def top_type(a: dict | None) -> str | None:
    t = (a or {}).get("type") or {}
    if t.get("choice"):
        return t["choice"]
    probs = t.get("probabilities") or {}
    return max(probs.items(), key=lambda kv: kv[1])[0] if probs else None


def noul(a: dict | None, qid: str) -> float | None:
    got = ((a or {}).get(qid) or {}).get("noul")
    return got if isinstance(got, (int, float)) and not isinstance(got, bool) else None


def three_q(a: dict | None) -> bool | None:
    """Arm 5: genuine AND in the idea's domain AND reply-worthy, each a concrete yes/no, combined in code."""
    t, out, reply = top_type(a), noul(a, "outside_domain"), noul(a, "reply_worthy")
    if t is None or out is None or reply is None:
        return None
    return t == "genuine" and out < 0.5 and reply >= 0.5


RULES = {"current": is_good, "three_question": three_q}


def pct(n: float, d: int) -> float | None:
    return round(100 * n / d, 1) if d else None


# ---------- loading ----------


def load_block(block: str, private: Path, discovery: Path) -> dict:
    """{opaque id: {stage, half, post_id, conversation, idea, age_hours, answers: {rater: answers}},
    parent: {rater: answers}}}. Every rater must cover every set it has a file for, and every set needs all four."""
    posts: dict[str, dict] = {}
    for stage in (1, 2, 3):
        key_path = discovery / f"corpus-key-stage{stage}-{block}.json"
        if not key_path.exists():
            raise Stop(f"{key_path.name} is missing: build and split stage {stage} first")
        key = json.loads(key_path.read_text(encoding="utf-8"))
        ages = {r["id"]: r.get("age_hours") for r in raters.rows(discovery / f"corpus-stage{stage}-{block}.jsonl")}
        for half in ("validation", "final"):
            for parent in (False, True):
                name = f"stage{stage}-{block}-{half}{'-parent' if parent else ''}"
                corpus = raters.rows(private / "splits" / f"{name}.jsonl")
                if parent and not corpus:
                    continue
                if not corpus:
                    raise Stop(f"splits/{name}.jsonl is missing or empty: run jev.py split first")
                ids = {r["id"] for r in corpus}
                for rater in (JEV,) + LLM:
                    path = raters.rater_file(private, rater, name)
                    got, unavailable, exists = raters.load_rater(path)
                    if not exists:
                        raise Stop(f"{path.name} is missing: every set needs Jev, Codex, Claude and Grok")
                    if set(got) != ids or unavailable:
                        raise Stop(f"{path.name} covers {len(set(got) & ids)} of {len(ids)} posts "
                                   f"({unavailable} unavailable): rerun or re-ingest it")
                    for pid in ids:
                        row = posts.setdefault(pid, {"stage": stage, "half": half, "post_id": key[pid]["post_id"],
                                                     "conversation": key[pid].get("conversation_id") or key[pid]["post_id"],
                                                     "idea": key[pid].get("idea_key"), "age_hours": ages.get(pid),
                                                     "answers": {}, "parent": {}})
                        (row["parent"] if parent else row["answers"])[rater] = got[pid]
    return posts


def load_manifest(block: str, discovery: Path) -> list[dict]:
    path = discovery / f"manifest-{block}.csv"
    if not path.exists():
        raise Stop(f"{path.name} is missing: run harness.py manifest --block {block}")
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_texts(discovery: Path) -> dict[str, str]:
    path = discovery / "posts.csv"
    with path.open(newline="", encoding="utf-8") as fh:
        return {r["post_id"]: r.get("text") or "" for r in csv.DictReader(fh)}


def call_costs(discovery: Path) -> dict[str, float]:
    return {r["call_id"]: r.get("estimated_cost") or 0.0 for r in raters.rows(discovery / "requests.jsonl") if r.get("call_id")}


def opaque_ids(posts: dict) -> dict[tuple[str, str], str]:
    """(stage, X post id) -> opaque id. A post found in two stages has a corpus line, and ratings, in each."""
    return {(f"stage{p['stage']}", p["post_id"]): i for i, p in posts.items()}


def key_of(sighting: dict) -> tuple[str, str]:
    return sighting["stage"], sighting["post_id"]


# ---------- panel ----------


def panel(post: dict, fn, which: str = "answers") -> bool | None:
    return raters.majority([v for r in LLM if (v := fn(post[which].get(r))) is not None])


def panel_type(post: dict) -> str | None:
    return raters.type_majority([t for r in LLM if (t := top_type(post["answers"].get(r)))])


def panel_outside(post: dict) -> bool | None:
    return raters.majority([v >= 0.5 for r in LLM if (v := noul(post["answers"].get(r), "outside_domain")) is not None])


def yield_of(ids: list[str], posts: dict) -> dict:
    """Good (panel, p_good >= 0.5) and the panel's type mix over a set of posts."""
    good = [i for i in ids if panel(posts[i], is_good)]
    types = Counter(panel_type(posts[i]) or "no majority" for i in ids)
    return {"posts": len(ids), "good": len(good), "good_pct": pct(len(good), len(ids)),
            "genuine_pct": pct(types["genuine"], len(ids)),
            "promotion_or_bait_pct": pct(sum(types[t] for t in PROMO), len(ids)),
            "off_topic_pct": pct(types["off-topic"], len(ids))}


def by_half(ids: list[str], posts: dict, fn=yield_of) -> dict:
    out = {"pooled": fn(ids, posts)}
    for half in ("validation", "final"):
        out[half] = fn([i for i in ids if posts[i]["half"] == half], posts)
    return out


# ---------- arms ----------


def arm1(posts: dict, manifest: list[dict], texts: dict, costs: dict) -> dict:
    """-has:links (Knl) against the plain query (K), per query variant, same window and sort."""
    opaque = opaque_ids(posts)
    found: dict[tuple, set] = defaultdict(set)
    calls: dict[tuple, set] = defaultdict(set)
    for m in manifest:
        if m["stage"] not in ("stage2", "stage3") or key_of(m) not in opaque:
            continue
        arm = {"K-recency": "plain", "Knl-recency": "no_links", "Kspam-recency": "spam_reference"}.get(m["source"])
        if arm is None:
            continue
        variant = m["variant"].replace("-no-links", "") if arm != "spam_reference" else "spam"
        found[(m["idea"], variant, arm)].add(opaque[key_of(m)])
        calls[(m["idea"], variant, arm)].add(m["call"])
    cells, totals = [], defaultdict(lambda: {"ids": set(), "calls": set()})
    for (idea, variant, arm) in sorted(found):
        ids = sorted(found[(idea, variant, arm)])
        cost = sum(costs.get(c, 0.0) for c in calls[(idea, variant, arm)])
        entry = {"idea": idea, "variant": variant, "arm": arm, **yield_of(ids, posts), "est_usd": round(cost, 3)}
        if arm == "plain":
            other = found.get((idea, variant, "no_links"), set())
            good = [i for i in ids if panel(posts[i], is_good)]
            entry["good_with_link"] = sum(LINK in texts.get(posts[i]["post_id"], "") for i in good)
            entry["good_only_plain_found"] = sum(i not in other for i in good)
        cells.append(entry)
        job = STAGE_JOB[posts[ids[0]]["stage"]] if ids else "?"
        for scope in (f"{job}:{arm}", f"all:{arm}"):
            totals[scope]["ids"] |= set(ids)
            totals[scope]["calls"] |= calls[(idea, variant, arm)]
    summary = {}
    for scope, t in sorted(totals.items()):
        ids = sorted(t["ids"])
        cost = sum(costs.get(c, 0.0) for c in t["calls"])
        y = by_half(ids, posts)
        y["pooled"]["good_per_usd"] = round(y["pooled"]["good"] / cost, 1) if cost else None
        summary[scope] = y
    for job in ("demand", "tool-research", "all"):
        plain = totals[f"{job}:plain"]["ids"] if f"{job}:plain" in totals else set()
        nl = totals[f"{job}:no_links"]["ids"] if f"{job}:no_links" in totals else set()
        good_plain = {i for i in plain if panel(posts[i], is_good)}
        good_nl = {i for i in nl if panel(posts[i], is_good)}
        summary[f"{job}:overlap"] = {"good_plain": len(good_plain), "good_no_links": len(good_nl),
                                     "good_both": len(good_plain & good_nl),
                                     "good_lost_by_no_links_pct": pct(len(good_plain - good_nl), len(good_plain))}
    return {"cells": cells, "summary": summary}


def arm2(posts: dict, manifest: list[dict]) -> dict:
    """Worth joining: good posts by age at read, on the current cards' 6 h recency read."""
    opaque = opaque_ids(posts)
    ids = sorted({opaque[key_of(m)] for m in manifest if m["stage"] == "stage1" and m["idea"] in CURRENT_WJ
                  and m["source"] == "K-recency" and key_of(m) in opaque})
    good = {i for i in ids if panel(posts[i], is_good)}
    buckets = {}
    for name, lo, hi in AGE_BUCKETS:
        inside = [i for i in ids if (age := posts[i]["age_hours"]) is not None
                  and (lo is None or age > lo) and (hi is None or age <= hi)]
        g = [i for i in inside if i in good]
        buckets[name] = {"posts": len(inside), "good": len(g), "good_pct": pct(len(g), len(inside)),
                         "share_of_good_pct": pct(len(g), len(good))}
    missing = [i for i in ids if posts[i]["age_hours"] is None]
    cuts = {}
    for cut in (1.0, 2.0):
        kept = [i for i in ids if posts[i]["age_hours"] is not None and posts[i]["age_hours"] <= cut]
        cuts[f"<={int(cut)}h"] = {"keeps_good_pct": pct(sum(i in good for i in kept), len(good)),
                                  "drops_posts_pct": pct(len(ids) - len(kept), len(ids)),
                                  "good_pct_kept": pct(sum(i in good for i in kept), len(kept))}
    return {"posts": len(ids), "good": len(good), "no_age": len(missing), "buckets": buckets, "cuts": cuts}


def arm3(posts: dict) -> dict:
    """The same replies with and without the parent post in the packet."""
    ids = sorted(i for i, p in posts.items() if len(p["parent"]) == 1 + len(LLM))
    def side(which: str) -> dict:
        out = {}
        for r in (JEV,) + LLM:
            dec = [noul(posts[i][which][r], "text_decidable") for i in ids]
            dec = [d for d in dec if d is not None]
            out[r] = {"text_decidable_yes_pct": pct(sum(d >= 0.5 for d in dec), len(dec)),
                      "good_pct": pct(sum(bool(is_good(posts[i][which][r])) for i in ids), len(ids))}
        votes = [[is_good(posts[i][which][r]) for r in LLM] for i in ids]
        out["panel_disputed_pct"] = pct(sum(len(set(v)) > 1 for v in votes), len(ids))
        pan = {i: panel(posts[i], is_good, which) for i in ids}
        judged = [i for i in ids if pan[i] is not None and good_p50(posts[i][which][JEV]) is not None]
        out["jev_p50_vs_panel_agreement_pct"] = pct(sum(good_p50(posts[i][which][JEV]) == pan[i] for i in judged), len(judged))
        out["panel_good_pct"] = pct(sum(bool(pan[i]) for i in ids), len(ids))
        return out
    flips = {r: sum(is_good(posts[i]["answers"][r]) != is_good(posts[i]["parent"][r]) for i in ids)
             for r in (JEV,) + LLM}
    flips["jev (p_good>=0.5)"] = sum(good_p50(posts[i]["answers"][JEV]) != good_p50(posts[i]["parent"][JEV]) for i in ids)
    return {"replies": len(ids), "by_stage": dict(Counter(STAGE_JOB[posts[i]["stage"]] for i in ids)),
            "without_parent": side("answers"), "with_parent": side("parent"),
            "good_flips": flips, "good_flips_pct": {r: pct(n, len(ids)) for r, n in flips.items()}}


def arm4(posts: dict, manifest: list[dict]) -> dict:
    """Rewritten Worth-joining cards against the originals, same window and sort."""
    opaque = opaque_ids(posts)
    by_card: dict[str, set] = defaultdict(set)
    for m in manifest:
        if m["stage"] == "stage1" and m["source"] == "K-recency" and key_of(m) in opaque:
            by_card[m["idea"]].add(opaque[key_of(m)])
    out = {}
    for old, new in CARD_PAIRS:
        for card, other in ((old, new), (new, old)):
            ids = sorted(by_card.get(card, set()))
            outside = [i for i in ids if panel_outside(posts[i])]
            good = [i for i in ids if panel(posts[i], is_good)]
            out[card] = {**yield_of(ids, posts), "outside_domain_pct": pct(len(outside), len(ids)),
                         "good_only_this_card": sum(i not in by_card.get(other, set()) for i in good)}
    return out


def arm5(posts: dict, operator: dict | None = None) -> dict:
    """The three-question rule against the current product rule, on the same answers."""
    def cluster_of(pid: str) -> str:
        return str(posts[pid]["conversation"])
    out = {}
    scopes = {"all": list(posts)} | {job: [i for i, p in posts.items() if STAGE_JOB[p["stage"]] == job]
                                     for job in STAGE_JOB.values()}
    op = {x["id"]: x["label"] in raters.YES for x in (operator or {}).get("labels", []) if x.get("label") in raters.YES + raters.NO}
    for scope, ids in scopes.items():
        entry: dict = {"posts": len(ids)}
        verdicts = {}
        for name, fn in RULES.items():
            per = {r: {i: v for i in ids if (v := fn(posts[i]["answers"].get(r))) is not None} for r in (JEV,) + LLM}
            pan = {i: v for i in ids if (v := panel(posts[i], fn)) is not None}
            verdicts[name] = pan
            pairs = {f"{a}~{b}": raters.pair_stats(per[a], per[b], cluster_of, names=("a", "b"))
                     for a, b in (("codex", "claude"), ("codex", "grok"), ("claude", "grok"))}
            judged = [i for i in pan if i in per[JEV]]
            entry[name] = {
                "panel_good_pct": pct(sum(pan.values()), len(pan)), "panel_n": len(pan),
                "by_half_panel_good_pct": {h: pct(sum(v for i, v in pan.items() if posts[i]["half"] == h),
                                                  sum(1 for i in pan if posts[i]["half"] == h)) for h in ("validation", "final")},
                "llm_pairs": {k: {x: v[x] for x in ("n", "agreement_pct", "kappa", "kappa_ci90", "kappa_ci90_unstable")}
                              for k, v in pairs.items()},
                "jev_vs_panel_agreement_pct": pct(sum(per[JEV][i] == pan[i] for i in judged), len(judged)),
                "jev_vs_panel_n": len(judged)}
            if name == "current":
                p50 = [i for i in pan if good_p50(posts[i]["answers"].get(JEV)) is not None]
                entry[name]["jev_p50_vs_panel_agreement_pct"] = pct(
                    sum(good_p50(posts[i]["answers"][JEV]) == pan[i] for i in p50), len(p50))
            if op:
                both = [i for i in op if i in pan]
                entry[name]["operator_agreement_pct"] = pct(sum(pan[i] == op[i] for i in both), len(both))
                entry[name]["operator_n"] = len(both)
        a, b = verdicts["current"], verdicts["three_question"]
        differ = [i for i in ids if i in a and i in b and a[i] != b[i]]
        entry["rules_disagree"] = {"posts": len(differ),
                                   "good_only_under_current": sum(a[i] for i in differ),
                                   "good_only_under_three_question": sum(b[i] for i in differ),
                                   "panel_types": dict(Counter(panel_type(posts[i]) or "no majority" for i in differ))}
        if scope == "tool-research":
            entry["flag"] = "reply_worthy fits Tool research badly: that job looks for evidence, not leads"
        out[scope] = entry
    return out


def side_cutoff(posts: dict, thresholds_path: Path | None = None) -> dict:
    """The frozen B3 cut-off applied to this block, per job and pooled."""
    frozen = jev.thresholds(thresholds_path)
    cut = frozen.get("frozen_coverage_threshold")
    if cut is None:
        return {"skipped": "no frozen cut-off"}
    out = {"cut": cut, "rule": frozen.get("frozen_coverage_rule")}
    scopes = {"all": list(posts)} | {job: [i for i, p in posts.items() if STAGE_JOB[p["stage"]] == job]
                                     for job in STAGE_JOB.values()}
    for scope, ids in scopes.items():
        pg = {i: v for i in ids if (v := raters.p_good(posts[i]["answers"][JEV])) is not None}
        binary = {i: v >= 0.5 for i, v in pg.items()}
        pan = {i: v for i in ids if (v := panel(posts[i], is_good)) is not None}
        point = raters.coverage(pg, binary, pan, (cut,))["curve"][0]
        out[scope] = {"share_pct": point["share_pct"], "posts": point["posts"], "of": len(pg),
                      "agreement_pct": point["agreement_pct"], "random_same_share_pct": point["random_same_share_agreement_pct"]}
    return out


def run(block: str, private: Path = jev.PRIVATE, discovery: Path = jev.DISCOVERY, operator: dict | None = None,
        thresholds_path: Path | None = None) -> dict:
    posts = load_block(block, private, discovery)
    manifest = load_manifest(block, discovery)
    report = {"block": block, "note": NOTE, "posts": len(posts),
              "by_stage": {STAGE_JOB[s]: sum(p["stage"] == s for p in posts.values()) for s in (1, 2, 3)},
              "arm1_no_links": arm1(posts, manifest, load_texts(discovery), call_costs(discovery)),
              "arm2_worth_joining_age": arm2(posts, manifest),
              "arm3_parent": arm3(posts),
              "arm4_cards": arm4(posts, manifest),
              "arm5_rules": arm5(posts, operator),
              "side_frozen_cutoff": side_cutoff(posts, thresholds_path)}
    out = private / f"arms-{block}.json"
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    tmp.replace(out)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Jev experiment 4: the B4 arms as totals and rates.")
    parser.add_argument("--block", required=True)
    parser.add_argument("--operator", help="the operator's labels (labelling.py), optional")
    args = parser.parse_args(argv)
    operator = json.loads(Path(args.operator).expanduser().read_text(encoding="utf-8")) if args.operator else None
    try:
        print(json.dumps(run(args.block, operator=operator), indent=1))
    except (Stop, jev.Stop) as exc:
        print(f"stopped: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
