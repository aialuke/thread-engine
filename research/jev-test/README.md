# Jev build-phase test

Does Jev, TypeSafe's typed-judgement model, earn a place as a cheap, repeatable judge while we tune Discovery search and filtering? This is build-phase research only. Nothing in the factory (`scripts/`, skills, hooks, `ledger/`, `loop/`) uses it. The case for testing, and its limits, are in [`../jev-build-time-evaluation-2026-09-27.md`](../jev-build-time-evaluation-2026-09-27.md).

## Setup (operator, once)

1. Create a key at https://console.typesafe.ai/keys. If the console offers a spend cap, set a low one. `jev.py` also stops itself at $1.
2. In Claude Code, type the line below and paste the key when macOS asks for it. It stays out of shell history and the chat:
   ```
   ! security add-generic-password -s thread-engine-typesafe -a api_key -w
   ```
   Don't export `TYPESAFE_API_KEY`, even though TypeSafe's docs suggest it. The key lives only in the Keychain, and sessions can't read it (the guard hook blocks Keychain reads).

## Commands (the agent runs these)

| Command | Does |
|---|---|
| `python3 research/jev-test/jev.py keys` | Is the key in the Keychain? It never reads the value |
| `… smoke` | One made-up question. Checks whether a pinned `jev-1.13.0` is accepted, else falls back to `jev-latest`, and records the result |
| `… run --set synthetic` | Asks the rubric (`questions.json`) about the 30 made-up posts in `synthetic.jsonl` |
| `… run --set stage2 \| stagespam-demand \| stagespam-tool` | The same for real Discovery posts. Refused until the operator allows it |
| `… compare --set <name>` | Jev against the settled labels, with Codex and Claude alongside |
| `… config --real-data on` | Run only after the operator says yes in chat. The date is recorded |
| `… spend` | Spend so far against the $1 ceiling |

- Every answer is cached in `private/cache/`, so a rerun or a re-analysis makes no new calls. An interrupted run resumes for free.
- Calls, costs and refusals go to `private/calls.jsonl` and `private/budget.log`.
- `private/` is gitignored. Answers about real posts are deleted with the Discovery private data by 24 Oct 2026.
- Tests: `python3 -m unittest discover -s research/jev-test`

## How the rubric maps

`questions.json` restates the Discovery scoring brief. Each post is sent as the state `{"idea", "post"}`.

| Brief | Jev question | Read as |
|---|---|---|
| relevant, real, useful (0–2) | Score, 3 levels | The most probable level |
| type (7 kinds) | Choice | The chosen option |
| act | Noul | Yes when the probability is 0.5 or more; the probability is kept |

`useful` has one wording for demand jobs and another for tool research (`stagespam-tool`), as in the briefs. Changing any wording makes it a new run, because the cache key changes; record the change here.

## Experiment 1: feasibility (made-up posts only)

**Question:** does the setup work, and do the questions behave sensibly on known traps (video-game "free version" lookalikes, replies that answer someone else's need, marketing phrased as the need)?

**Pass:** every call succeeds, and the served model is recorded. Jev's `act` matches the intended label on at least 24 of 30 posts. Every miss is listed with its trap.

**Limits:** the same author (Claude) wrote the posts, their labels and the questions, so a pass shows feasibility, not quality. Revise the wording **at most once**, and only for a reason that would hold for real posts, never to fit a single made-up case. If it still fails, stop and report.

## Experiment 2: replay against settled labels (after the operator's yes)

**Data:** 298 real posts already scored by the Discovery test: `stage2` 180, `stagespam-demand` 57, `stagespam-tool` 61. Final labels are in `../discovery-test/private/final-scores-*.jsonl`.

**Provenance matters.** Codex (the first scorer) and Claude (the second) both voted on these labels, so their agreement with them is inflated. Jev never voted. `compare` reports three groups separately:
- **settled**: posts where the first two scorers agreed, or a three-way majority decided;
- **adjudicated only**: the contested posts;
- **first only**: Codex's own label, never checked. Not used for the decision.

**Written before the run (27 Sep 2026).** On settled posts, pooled across the three sets:
- **Pass:** Jev's `act` agreement is within 5 points of Codex's first-pass `act` agreement on the same posts, **and** Jev's `act` AUC is 0.80 or higher. The 5-point allowance exists because Codex's figure is inflated by its vote.
- **Also reported, not pass/fail:**
  - `type` accuracy and the main confusions;
  - relevant/real/useful exact and within-one agreement;
  - how many genuine `act` posts Jev would drop;
  - whether contested posts get less certain `act` probabilities;
  - cost and time per post.
- **Stop:** if it fails, write "not useful at this scale" in the evaluation document and stop. A pass justifies scoping the evaluation's larger pilot. It does not justify putting Jev in any product path.

**Cost:** about 300 posts × about 1,000 tokens ≈ 300k input tokens ≈ $0.013 at $0.042 per million.

## Results

### Experiment 1, 27 Sep 2026: pass

- **Run:** 30 made-up posts, served by pinned `jev-1.13.0`. 31 calls including the smoke test, $0.0012 in all, about 0.3 s a post.
- **Bar:** `act` matched on 25 of 30 (the bar was 24), with AUC 0.97.
- **Other dimensions:** real 93% exact, relevant 80%, type 80%, useful 60% (87% within one).
- **Every `act` miss said yes when it should have said no.** None were missed genuine posts:
  - Both video-game "free version" lookalikes (y04 at 0.87, y05 at 0.59). Jev called them squarely relevant (2) and `genuine` with 0.99 confidence on y04. This is the same trap the real pilot hit (`../discovery-x-api-search-proposal.md`), and the clearest weakness: a real ask outside the idea's domain reads as on-topic.
  - Replies and advice for someone else's need (y06 at 0.78, y18 at 0.74). Relevance was right (1), but `act` still said yes.
  - A "10 free alternatives" listicle (y10 at 0.52), borderline.
- **Useful runs high:** it often scores 1–2 where the label is 0, including spam and promotion. Treat it as the weakest dimension.
- **Type misses were mostly between neighbouring kinds of spam** (promotion, engagement-bait, product-marketing), which doesn't change `act`.

**Hypothesis for experiment 2, found after seeing these results, so not evidence:** requiring Jev's `relevant` = 2 as well as `act` ≥ 0.5, combined in code, gives 28 of 30 here. The video-game pair still passes it. Test it on the real replay as a secondary rule, never as the pass measure.

The rubric wording is unchanged. The one allowed revision is held back: the real fix for the video-game trap is probably the idea's own wording ("creator or developer **software**"), which is a Discovery change, not a Jev one.
