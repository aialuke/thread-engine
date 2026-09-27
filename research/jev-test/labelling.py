#!/usr/bin/env python3
"""Operator labelling for the Jev test: the answer key where the AI scorers disagree.

    python3 research/jev-test/labelling.py ingest-grok --set <name> --file <grok json envelope>
    python3 research/jev-test/labelling.py panel
    python3 research/jev-test/labelling.py sample [--disputed 40] [--random 20]
    python3 research/jev-test/labelling.py ingest-labels --file ~/Downloads/jev-labels-*.json

The panel is three blind scorers of the same Discovery brief: Codex (first score), Claude (second
score, a subset), Grok (all posts, scored for this test). Each scorer's verdict is Discovery's
useful-post rule: relevant 2, real 2, useful 1 or more (discovery-test/private/stage-2.md).
`sample` picks the posts the panel disagrees on, spread across sets and ideas, plus a random
sample of posts it agrees on, and writes private/label.html: a page that shows one post at a
time, never the scorers' answers, and exports the operator's labels as JSON.

Everything written stays in private/ (gitignored; other people's posts; delete by 26 Mar 2027).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIVATE = HERE / "private"
DISCOVERY = HERE.parent / "discovery-test" / "private"
sys.path.insert(0, str(HERE.parent / "discovery-test"))

SETS = ("stage2", "stagespam-demand", "stagespam-tool")
TOOL_SETS = {"stagespam-tool"}
SEED = 27
QUESTIONS = {
    "demand": "Would you want this surfaced for this idea: something to post about, or a conversation to reply to?",
    "tool": "Would you want this surfaced: does it show how people use, like or dislike the product, or is it a conversation to reply to?",
}
ANSWERS = ("post", "reply", "no", "unsure")      # post and reply both count as yes


def rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line.strip()]


def good(r: dict | None) -> bool | None:
    """Discovery's useful-post rule. None when the scorer didn't score the post."""
    if not r or any(r.get(k) is None for k in ("relevant", "real", "useful")):
        return None
    return r["relevant"] == 2 and r["real"] == 2 and r["useful"] >= 1


# ---------- Grok ----------


def ingest_grok(set_name: str, envelope: Path, private: Path = PRIVATE, discovery: Path = DISCOVERY) -> dict:
    """Parse Grok's JSON lines, validate them with the harness's own checker, save grok-scores-<set>.jsonl."""
    import harness  # the Discovery harness's validator: id + echoed opening, 0-2 scores, known types

    text = json.loads(envelope.read_text(encoding="utf-8"))["text"]
    parsed = []
    for line in text.split("\n"):
        # Grok can put a preamble sentence on the same line as the first answer
        start = line.find('{"id"')
        if start < 0:
            continue
        try:
            parsed.append(json.loads(line[start:].strip()))
        except json.JSONDecodeError:
            continue
    corpus = {c["id"]: c for c in rows(discovery / f"corpus-{set_name}.jsonl")}
    kept, problems = harness.check_scores(corpus, parsed)
    private.mkdir(parents=True, exist_ok=True)
    (private / f"grok-scores-{set_name}.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in kept), encoding="utf-8")
    return {"set": set_name, "kept": len(kept), "of": len(corpus), "problems": problems}


# ---------- panel ----------


def panel(private: Path = PRIVATE, discovery: Path = DISCOVERY) -> list[dict]:
    """One row per post: set, idea, job, text, and each scorer's good/not verdict."""
    out = []
    for s in SETS:
        corpus = rows(discovery / f"corpus-{s}.jsonl")
        scorers = {"codex": {r["id"]: r for r in rows(discovery / f"scores-{s}.jsonl")},
                   "claude": {r["id"]: r for r in rows(discovery / f"second-scores-{s}.jsonl")},
                   "grok": {r["id"]: r for r in rows(private / f"grok-scores-{s}.jsonl")}}
        for c in corpus:
            votes = {name: good(scores.get(c["id"])) for name, scores in scorers.items()}
            cast = [v for v in votes.values() if v is not None]
            out.append({"id": c["id"], "set": s, "idea": c["idea"], "text": c["text"],
                        "job": "tool" if s in TOOL_SETS else "demand", "votes": votes,
                        "scorers": len(cast), "disputed": len(set(cast)) > 1})
    return out


def panel_summary(posts: list[dict]) -> dict:
    by_set = defaultdict(lambda: {"posts": 0, "disputed": 0, "all_three_scored": 0})
    for p in posts:
        by_set[p["set"]]["posts"] += 1
        by_set[p["set"]]["disputed"] += p["disputed"]
        by_set[p["set"]]["all_three_scored"] += p["scorers"] == 3
    return dict(by_set)


# ---------- sample ----------


def choose(posts: list[dict], disputed_n: int = 40, random_n: int = 20, seed: int = SEED) -> list[dict]:
    """Disputed posts spread across (set, idea) groups in proportion, at least one per group that has
    any; then a random sample of undisputed posts. Deterministic for a given seed."""
    rng = random.Random(seed)
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for p in posts:
        if p["disputed"]:
            groups[(p["set"], p["idea"])].append(p)
    total = sum(len(g) for g in groups.values())
    picked: list[dict] = []
    if total <= disputed_n:
        picked = [p for g in groups.values() for p in g]
    else:
        quota = {k: max(1, round(disputed_n * len(g) / total)) for k, g in groups.items()}
        while sum(quota.values()) > disputed_n:          # trim the largest quotas first
            k = max(quota, key=lambda key: (quota[key], len(groups[key])))
            quota[k] -= 1
        while sum(quota.values()) < disputed_n:          # top up where there is room
            k = max((key for key in quota if quota[key] < len(groups[key])),
                    key=lambda key: len(groups[key]) - quota[key])
            quota[k] += 1
        for k in sorted(groups):
            picked += rng.sample(sorted(groups[k], key=lambda p: p["id"]), quota[k])
    for p in picked:
        p["why_chosen"] = "disputed"
    rest = sorted((p for p in posts if not p["disputed"] and p["scorers"] >= 2), key=lambda p: p["id"])
    extra = rng.sample(rest, min(random_n + max(0, disputed_n - len(picked)), len(rest)))
    for p in extra:
        p["why_chosen"] = "random (panel agreed)"
    sample = picked + extra
    rng.shuffle(sample)
    return sample


def sample_hash(sample: list[dict]) -> str:
    return hashlib.sha256("|".join(p["id"] for p in sample).encode("utf-8")).hexdigest()[:12]


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Post Labelling</title>
<style>
:root{--bg:#f7f7f5;--card:#fff;--ink:#1c1c1a;--muted:#6b6b66;--line:#e2e2dc;--yes:#1f7a4d;--no:#b3261e;--unsure:#8a6d00;--accent:#2b59c3}
@media (prefers-color-scheme:dark){:root{--bg:#141413;--card:#1e1e1c;--ink:#ecece8;--muted:#a3a39c;--line:#33332f;--yes:#5cc28f;--no:#f08a82;--unsure:#e0c060;--accent:#8fb0ff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,-apple-system,sans-serif}
main{max-width:720px;margin:0 auto;padding:24px 16px 48px}
header{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
h1{font-size:18px;margin:0}.muted{color:var(--muted);font-size:14px}
.bar{height:6px;background:var(--line);border-radius:3px;margin:12px 0 20px;overflow:hidden}.bar>div{height:100%;background:var(--accent);width:0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px}
.idea{font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin:0 0 4px}
.ideatext{font-weight:600;margin:0 0 16px}
.post{white-space:pre-wrap;word-break:break-word;border-left:3px solid var(--line);padding:4px 0 4px 14px;margin:0 0 18px}
.q{font-weight:600;margin:0 0 12px}
.btns{display:flex;gap:8px;flex-wrap:wrap}
button{font:inherit;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:8px;padding:10px 16px;cursor:pointer}
button kbd{font:12px ui-monospace,monospace;color:var(--muted);margin-left:6px}
button.sel.yes,button.sel.post,button.sel.reply{background:var(--yes);color:#fff;border-color:var(--yes)}button.sel.no{background:var(--no);color:#fff;border-color:var(--no)}button.sel.unsure{background:var(--unsure);color:#fff;border-color:var(--unsure)}
input[type=text]{width:100%;font:inherit;padding:10px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);margin-top:14px}
nav{display:flex;justify-content:space-between;align-items:center;margin-top:16px;gap:8px;flex-wrap:wrap}
.help{margin-top:20px;font-size:14px;color:var(--muted)}
.done{display:none;margin-top:16px}.done.show{display:block}
</style></head><body><main>
<header><h1>Post labelling</h1><span class="muted" id="count"></span></header>
<div class="bar"><div id="fill"></div></div>
<div class="card">
<p class="idea">Search idea</p><p class="ideatext" id="idea"></p>
<div class="post" id="post"></div>
<p class="q" id="q"></p>
<div class="btns">
<button data-v="post" class="yes">Yes, to post about<kbd>P</kbd></button>
<button data-v="reply" class="yes">Yes, to reply to<kbd>R</kbd></button>
<button data-v="no" class="no">No<kbd>N</kbd></button>
<button data-v="unsure" class="unsure">Unsure<kbd>U</kbd></button>
</div>
<input type="text" id="why" placeholder="Optional: one line on why">
</div>
<nav><button id="prev">&larr; Back</button><span class="muted" id="saved"></span><button id="next">Skip &rarr;</button></nav>
<div class="done card" id="done"><p><strong>All done.</strong> Click Export and tell Claude. The file lands in Downloads.</p></div>
<nav><span class="muted">Answers save in this browser as you go.</span><button id="export">Export labels</button></nav>
<p class="help">Judge only what the post says, as if it turned up in your search for that idea. Yes: you'd want this surfaced, to post about or to reply to (if both, pick the stronger). No: you'd skip it. Unsure: you can't tell from the text. Keys: P / R / N / U to answer and move on; &larr; &rarr; to move.</p>
</main>
<script>
const DATA = __DATA__;
const KEY = "jev-labels-" + DATA.sample;
let labels = {};
try { labels = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { labels = {}; }
let i = DATA.posts.findIndex(p => !labels[p.id]); if (i < 0) i = 0;
const $ = id => document.getElementById(id);
function save() { try { localStorage.setItem(KEY, JSON.stringify(labels)); $("saved").textContent = "Saved"; } catch (e) { $("saved").textContent = "Not saved: export before closing"; } }
function render() {
  const p = DATA.posts[i], l = labels[p.id] || {};
  $("idea").textContent = p.idea; $("post").textContent = p.text; $("q").textContent = p.question;
  $("why").value = l.why || "";
  document.querySelectorAll("[data-v]").forEach(b => { b.classList.toggle("sel", b.dataset.v === l.label); });
  const n = Object.values(labels).filter(x => x.label).length;
  $("count").textContent = "Post " + (i + 1) + " of " + DATA.posts.length + " · " + n + " answered";
  $("fill").style.width = (100 * n / DATA.posts.length) + "%";
  $("done").classList.toggle("show", n === DATA.posts.length);
}
function answer(v) {
  const p = DATA.posts[i];
  labels[p.id] = { label: v, why: $("why").value.trim() };
  save(); if (i < DATA.posts.length - 1) i++; render();
}
document.querySelectorAll("[data-v]").forEach(b => b.onclick = () => answer(b.dataset.v));
$("why").oninput = () => { const p = DATA.posts[i]; labels[p.id] = { ...(labels[p.id] || {}), why: $("why").value.trim() }; save(); };
$("prev").onclick = () => { if (i > 0) i--; render(); };
$("next").onclick = () => { if (i < DATA.posts.length - 1) i++; render(); };
document.addEventListener("keydown", e => {
  if (e.target === $("why")) { if (e.key === "Enter") $("why").blur(); return; }
  const k = e.key.toLowerCase();
  if (k === "p") answer("post"); else if (k === "r") answer("reply"); else if (k === "n") answer("no"); else if (k === "u") answer("unsure");
  else if (e.key === "ArrowLeft") $("prev").click(); else if (e.key === "ArrowRight") $("next").click();
});
$("export").onclick = () => {
  const out = { sample: DATA.sample, exported_at: new Date().toISOString(),
    labels: DATA.posts.map(p => ({ id: p.id, label: (labels[p.id] || {}).label || null, why: (labels[p.id] || {}).why || "" })) };
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(out, null, 1)], { type: "application/json" }));
  a.download = "jev-labels-" + DATA.sample + ".json"; a.click();
};
render();
</script></body></html>
"""


def write_page(sample: list[dict], private: Path = PRIVATE) -> Path:
    h = sample_hash(sample)
    data = {"sample": h, "posts": [{"id": p["id"], "idea": p["idea"], "text": p["text"],
                                    "question": QUESTIONS[p["job"]]} for p in sample]}
    # </ inside post text must not close the script tag
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    page = private / "label.html"
    page.write_text(PAGE.replace("__DATA__", blob), encoding="utf-8")
    manifest = {"sample": h, "seed": SEED, "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "rule": "good = relevant 2, real 2, useful >= 1; disputed = the scorers who scored it disagree",
                "posts": [{k: p[k] for k in ("id", "set", "idea", "job", "votes", "why_chosen")} for p in sample]}
    (private / "label-sample.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return page


def ingest_labels(path: Path, private: Path = PRIVATE) -> dict:
    data = json.loads(path.expanduser().read_text(encoding="utf-8"))
    manifest = json.loads((private / "label-sample.json").read_text(encoding="utf-8"))
    if data.get("sample") != manifest["sample"]:
        raise SystemExit(f"labels are for sample {data.get('sample')}, the current sample is {manifest['sample']}")
    answered = [x for x in data["labels"] if x.get("label")]
    (private / "operator-labels.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    counts = defaultdict(int)
    for x in answered:
        counts[x["label"]] += 1
    return {"answered": len(answered), "of": len(data["labels"]), "counts": dict(counts)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Operator labelling for the Jev test.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("ingest-grok")
    p.add_argument("--set", required=True, dest="set_name", choices=SETS)
    p.add_argument("--file", required=True)
    sub.add_parser("panel")
    p = sub.add_parser("sample")
    p.add_argument("--disputed", type=int, default=40)
    p.add_argument("--random", type=int, default=20, dest="random_n")
    p = sub.add_parser("ingest-labels")
    p.add_argument("--file", required=True)
    args = parser.parse_args(argv)
    if args.command == "ingest-grok":
        print(json.dumps(ingest_grok(args.set_name, Path(args.file)), indent=1))
    elif args.command == "panel":
        print(json.dumps(panel_summary(panel()), indent=1))
    elif args.command == "sample":
        sample = choose(panel(), args.disputed, args.random_n)
        page = write_page(sample)
        kinds = defaultdict(int)
        for s in sample:
            kinds[s["why_chosen"]] += 1
        print(json.dumps({"page": str(page), "posts": len(sample), "chosen": dict(kinds),
                          "sample": sample_hash(sample)}, indent=1))
    elif args.command == "ingest-labels":
        print(json.dumps(ingest_labels(Path(args.file)), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
