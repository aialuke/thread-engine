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
| `… split --stage N --block B` | Seals a new block into validation and final before any scoring. It can't be redone |
| `… run --set stage{N}-B{k}-validation` | Jev on a sealed block set. The `-final` sets are refused until `freeze` |
| `… repeat --set S --posts 10 --times 3` | Fresh, uncached re-asks: does Jev answer the same way twice? |
| `… rank --set S` | One Choice per idea: which post would you most want to join? |
| `… freeze --note "…"` | One-way. Records the frozen questions and cut-offs and unseals final |
| `raters.py brief / ingest / compare` | The LLM raters' brief (same questions as Jev), fail-closed ingest of their answers, and the rater comparison |
| `labelling.py sample --sets …-validation` | The operator's labelling page for block sets (validation only). Pages and labels are never overwritten |

- Every answer is cached in `private/cache/`, so a rerun or a re-analysis makes no new calls. An interrupted run resumes for free.
- Calls, costs and refusals go to `private/calls.jsonl` and `private/budget.log`.
- `private/` is gitignored. Answers about real posts are deleted with the Discovery private data by 26 Mar 2027.
- Tests: `python3 -m unittest discover -s research/jev-test`

## How the rubric maps

`questions.json` restates the Discovery scoring brief. Each post is sent as the state `{"idea", "post"}`, plus `replies` and `age_hours` for Worth-joining posts. Every request also carries the four diagnostic questions, which are judged independently of the main ones.

| Brief | Jev question | Read as |
|---|---|---|
| relevant, real, useful (0–2) | Score, 3 levels | The most probable level |
| type (7 kinds) | Choice | The chosen option |
| act | Noul | Yes when the probability is 0.5 or more; the probability is kept |

`useful` has one wording each for Demand, Tool research (`stagespam-tool`, `stage3-*`) and Worth joining (`stage1-*`). Changing any wording makes it a new run, because the cache key changes; record the change here.

## Experiment 1: feasibility (made-up posts only)

**Question:** does the setup work, and do the questions behave sensibly on known traps (video-game "free version" lookalikes, replies that answer someone else's need, marketing phrased as the need)?

**Pass:** every call succeeds, and the served model is recorded. Jev's `act` matches the intended label on at least 24 of 30 posts. Every miss is listed with its trap.

**Limits:** the same author (Claude) wrote the posts, their labels and the questions, so a pass shows feasibility, not quality. Revise the wording **at most once**, and only for a reason that would hold for real posts, never to fit a single made-up case. If it still fails, stop and report.

## Experiment 2: the 298 existing posts, as development data (after the operator's yes)

**Data:** 298 rows already scored by the Discovery test: `stage2` 180, `stagespam-demand` 57 and `stagespam-tool` 61. That's **274 unique posts**: 24 appear in both Stage 2 and the Demand spam set, 17 of them with conflicting labels. This set is for developing and checking the questions, not a test.

**Withdrawn (28 Sep): the `act` pass rule written on 27 Sep.** The harness copies every final `act` label from Codex's first score, and never compares or settles it (`../discovery-test/harness.py:1433`, `:1456`). Measuring Jev against it would measure agreement with Codex. `act` is reported only as a historical field.

**What is reported instead** is rater agreement (see "How raters are compared" below), per set and per idea, with the operator's 60 labels as one rater. Everything is directional.

## Experiment 3: the new pull (written before any read, 28 Sep 2026)

**Data:**
- Discovery block B3: Stage 1 (Worth joining), Stage 3 (Tool research, with Claude Code in place of CapCut), and a fresh Demand window with the two `min_likes:10` floors removed.
- `jev.py split` seals it before any rater sees it:
  - any post whose post or conversation is already in the 298 is dropped;
  - each remaining conversation goes to **validation** or **final** by `sha256` of its ID.
- The final set stays unreadable until `jev.py freeze` records that the questions and cut-offs are frozen. The operator samples validation only.

**Raters, all peers, with no answer key:**
- Jev `jev-1.13.0`, pinned;
- Codex `gpt-5.6-sol`, in batches of about 50 posts;
- Claude Opus 5.5, on every post;
- Grok `grok-4.5`;
- the operator, on a sample of disputed and random validation posts.

The operator's labels are one comparison among the others (operator, 27 Sep).

**One instrument.** Every model rater answers the same questions (`questions.json`) and gives a probability for each level (`raters.py brief`). This follows TypeSafe's own evaluation method: every model runs the same workflow, and the reference is the average of the strongest models. For Worth joining, every rater sees the same packet: the post text, `replies` and `age_hours`, frozen at read time. There's no live link.

**Good-or-not:**
- `p_good = P(relevant=2) × P(real=2) × P(useful≥1)`, good if it is 0.5 or more (`thresholds.json`);
- the most-probable-level version is reported alongside.

**Measures, all directional:**
1. **Pairwise agreement and kappa** for every pair of raters, with *n*, prevalence, and 90% intervals from resampling conversations. Reported per set and per idea.
2. **Soft agreement:** each model's distance from the other models' average `p_good`, leaving itself out.
3. **Self-agreement:** each LLM rater re-scores about 50 validation posts in a fresh session. That sets the ceiling for its pairwise figures.
4. **Coverage against agreement** (headline): the share of posts Jev decides at or above each confidence level, and its agreement with the model panel's majority on those. This also tests TypeSafe's claim that "higher confidence means higher accuracy". The cut-off is chosen on validation and applied once to final.
5. **Diagnostics** (never pass measures):
   - is the author answering someone else's need?
   - is the post outside the idea's domain?
   - is it reply-worthy? (compared with the operator's "reply")
   - can it be judged from the text alone? (compared with the operator's "unsure")
6. **Ranking:** one Choice per Worth-joining idea, "which post would you most want to join?" (`jev.py rank`).
7. **Jev repeatability:** about 10 posts × 3 fresh calls (`jev.py repeat`).
8. **Unavailable answers** (a missing or out-of-range question) are counted separately and never treated as a no.

**Decision:** there's no pass or fail. The report states how much of the other models' scoring Jev could take over, and at what agreement. The operator decides whether it earns a place in build-phase query experiments. A weak result is reported as "not useful at this scale".

## Pull-day checklist (the agent follows this when the operator says go)

The steps below run in order. Every command has a test, and nothing reads from X before step 3.

1. **Checks before the read:**
   - `harness.py status`;
   - the X credit reading from the console (`harness.py console --before <USD>`);
   - the Discovery limit is $7;
   - scorer models are available.
2. **Once:**
   - `harness.py config --refreeze` (new idea cards);
   - `harness.py config --pin-block <new block>`;
   - `jev.py config --real-data on` (the operator has already said yes).
3. **One sitting, outside 19:30–20:30 Brisbane:**
   1. Stage 1 `--source K` for 4 ideas.
   2. `--source T` for `wj-tech-1` and `wj-tech-2`.
   3. Stage 3 `--source K` for DaVinci, Cursor, Claude Code and Substack.
   4. Stage 2 `--source K` for `demand-tech-1`, `demand-tech-2`, `demand-comedy-1b` and `demand-comedy-2b`.
   5. Stage 3 `--source Kspam`.
4. **Build and seal:**
   - `harness.py corpus --stage N --block B` for each stage;
   - then `jev.py split --stage N --block B`.
5. **Validation only:**
   - Jev: `jev.py run`, `repeat` and `rank`;
   - LLM raters: `raters.py brief`, the rater runs, then `raters.py ingest`, with repeats on about 50 posts;
   - `labelling.py sample --sets …-validation`, with Worth-joining posts sent to the operator the same day;
   - `harness.py reread` at least 5.5 hours after the reads, on the same UTC day.
6. **Compare:** `raters.py compare` on validation. Choose the cut-off, then `jev.py freeze --note …`.
7. **Final, once:** Jev and the LLM raters on the final sets, `raters.py compare`, and the write-up. The write-up is committed as totals, with no post text.

## Sources

- **TypeSafe docs and official posts:** docs.typesafe.ai and typesafe.ai/blog.
- **Partner write-ups** (LangChain, Browserbase): used for patterns, not as independent evidence.
- **thejevai.com** says it is "independently operated and not affiliated with TypeSafe". Its design advice is used; its API details (`thejevai.com/v1/systemone`, `JEV_API_KEY`) are not.
- **evals.typesafe.ai** renders in the browser. Only its overview could be read (28 Sep): break a policy into small Noul, Choice and Score questions and combine them in code.
- The five articles are in `../jev-articles/`.

## Results

### Experiment 1, 27 Sep 2026: the setup works (the quality reading doesn't hold)

- **Run:** 30 made-up posts, served by pinned `jev-1.13.0`. 31 calls including the smoke test, $0.0012 in all, about 0.3 s a post.
- **Bar:** `act` matched on 25 of 30 (the bar was 24), with AUC 0.97.
- **Other dimensions:** real 93% exact, relevant 80%, type 80%, useful 60% (87% within one).
- **Every `act` miss said yes when it should have said no.** None were missed genuine posts:
  - Both video-game "free version" lookalikes (y04 at 0.87, y05 at 0.59). Jev called them squarely relevant (2) and `genuine` with 0.99 confidence on y04. This is the same trap the real pilot hit (`../discovery-x-api-search-proposal.md`), and the clearest weakness: a real ask outside the idea's domain reads as on-topic.
  - Replies and advice for someone else's need (y06 at 0.78, y18 at 0.74). Relevance was right (1), but `act` still said yes.
  - A "10 free alternatives" listicle (y10 at 0.52), borderline.
- **Useful runs high:** it often scores 1–2 where the label is 0, including spam and promotion. Treat it as the weakest dimension.
- **Type misses were mostly between neighbouring kinds of spam** (promotion, engagement-bait, product-marketing), which doesn't change `act`.

**Correction, 28 Sep:** the made-up labels were stricter than the real ones. In settled Stage 2 labels, 52 of 54 replies are marked "act", and the operator counts a reply opportunity as useful. So the `act` "misses" on replies (y06, y18) may be right. The relevance rule below is **withdrawn**: it would drop 71 of 126 settled Stage 2 "act" posts.

**Withdrawn hypothesis (27 Sep):** requiring Jev's `relevant` = 2 as well as `act` ≥ 0.5, combined in code, gives 28 of 30 here. The video-game pair still passes it. Test it on the real replay as a secondary rule, never as the pass measure.

The rubric wording is unchanged. The one allowed revision is held back: the real fix for the video-game trap is probably the idea's own wording ("creator or developer **software**"), which is a Discovery change, not a Jev one.
