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
| `… run --set stage{N}-B{k}-validation` | Jev on a sealed block set. The `-final` sets are refused until `freeze`. A rerun rebuilds the answers from the cache, but never over answers to other questions (`--replace` keeps the old file as `.bak`) |
| `… repeat --set S --posts 10 --times 3` | Fresh, uncached re-asks: does Jev answer the same way twice? Tries already in the file are skipped |
| `… rank --set S` | One Choice per idea: which post would you most want to join? |
| `… freeze --note "…"` | One-way. Refused until `thresholds.json` has the `coverage_threshold` chosen on validation. Records it, its rule and the question hashes, and unseals final |
| `raters.py brief / ingest / compare` | The LLM raters' brief (same questions as Jev), fail-closed ingest of their answers, and the rater comparison. `--corpus` must be the file for `--set`. Ingest never overwrites a rater's file (`--replace` keeps the old one as `.bak`) |
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

**What is reported instead** is rater agreement, using the Experiment 3 measures below, per set and per idea, with the operator's 60 labels as one rater. Everything is directional.

## Experiment 3: the new pull (written before any read, 28 Sep 2026)

**Data:**
- Discovery block B3: Stage 1 (Worth joining), Stage 3 (Tool research, with Claude Code in place of CapCut), and a fresh Demand window with the two `min_likes:10` floors removed.
- `jev.py split` seals it before any rater sees it:
  - any post whose post or conversation is already in the 298 is dropped;
  - each remaining conversation goes to **validation** or **final** by `sha256` of its ID.
- The split writes both halves and its manifest under temporary names and publishes them only when all three are written. A split with no manifest is not sealed: every reader refuses it and names the leftover files to remove.
- The final set stays unreadable until `jev.py freeze` records that the questions and cut-offs are frozen. The operator samples validation only.
- One guard (`jev.check_block`) is used by every reader of a block set: `jev.py run`, `repeat`, `rank`, `reworded` and `compare`, `raters.py brief`, `ingest` and `compare`, and `labelling.py sample`. It refuses a final set by its name or by its corpus file until the freeze, and after it whenever the questions for that stage's job no longer hash to the frozen ones.

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

**One validator.** Jev's answers and the LLM raters' answers pass the same check (`jev.check_answer`): every question present, probabilities in [0, 1] (true and false are not probabilities), and each score or choice summing to 1 within 0.05, then renormalised. A row that fails is unavailable.

**Measures, all directional:**
1. **Pairwise agreement and kappa** for every pair of raters, with *n*, prevalence, and 90% intervals from resampling conversations. Reported per set and per idea (per idea with the same prevalence and intervals).
   - Kappa is undefined in a resample where both raters say the same thing on every post. Those draws are kept as their own outcome, not dropped: the interval is over the defined draws, the report gives the share undefined, and it marks the interval unstable when more than 10% of draws are undefined.
   - A type counts as the panel's only with at least two votes and a strict majority.
2. **Soft agreement:** each model's distance from the other models' average `p_good`, leaving itself out.
3. **Self-agreement:** each LLM rater re-scores about 50 validation posts in a fresh session. That sets the ceiling for its pairwise figures.
4. **Coverage against agreement** (headline): the share of posts Jev decides at or above each confidence level, and its agreement with the model panel's majority on those. This also tests TypeSafe's claim that "higher confidence means higher accuracy".
   - Each rule has its own confidence. For `p_good ≥ 0.5` it is `max(p_good, 1 − p_good)`. For the most-probable-level rule it is the probability that its verdict is right: `p_good` when the verdict is good, `1 − p_good` when not. A post can be "good" by its most probable levels and still have a low `p_good` (relevant and real 0.25/0.35/0.40, useful 0.30/0.40/0.30 gives 0.112), so it doesn't count as a confident call.
   - The cut-off (`coverage_threshold`, and `coverage_rule` for which curve) is chosen on validation. `freeze` refuses without it. On final, `raters.py compare` applies the frozen cut-off once and reports the share and agreement as `preregistered`, the result. The full curves on final are shown as exploratory.
5. **Diagnostics** (never pass measures):
   - is the author answering someone else's need?
   - is the post outside the idea's domain?
   - is it reply-worthy? (compared with the operator's "reply")
   - can it be judged from the text alone? (the AUC of `text_decidable` for posts the operator answered against the ones marked "unsure")
6. **Ranking:** one Choice per Worth-joining idea, "which post would you most want to join?" (`jev.py rank`).
7. **Jev repeatability:** about 10 posts × 3 fresh calls (`jev.py repeat`).
8. **Unavailable answers** (a missing or out-of-range question) are counted separately and never treated as a no.
9. **The operator's agreement, disputed and random apart.** With `--sample` (the label-sample sidecar the labels came from), every rater's and the panel's agreement with the operator is reported separately for the disputed posts and the random panel-agreed posts. Mixed together, the two samples would hide how each behaves.

**Nothing is overwritten.** `raters.py ingest` refuses when the rater's file for that set exists (`--replace` first moves it to a timestamped `.bak`). `labelling.py ingest-grok` fails closed like it: any row missing, answered twice or rejected, and nothing is written, and an existing Grok file is never replaced.

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

## Experiment 4: the B4 pull, a query-design test (written before any read, 28 Sep 2026)

**Question:** do the five product lessons from B3 ([`../jev-build-time-evaluation-2026-09-27.md`](../jev-build-time-evaluation-2026-09-27.md#tests-for-the-next-pull)) hold on a fresh pull? Each arm runs against the current setup in the same window. Directional only, with no pass or fail.

**Same instrument as Experiment 3:**
- The raters are Jev `jev-1.13.0`, Codex `gpt-5.6-sol`, Claude Opus 5.5 and Grok `grok-4.5`, plus the operator optionally.
- They get the same `questions.json` (hashes unchanged, so the B3 freeze and its 0.8 cut-off still hold), the same `raters.py brief`, and the same validator.
- "Good" is `p_good ≥ 0.5`, read by the Codex/Claude/Grok strict majority, except in arm 5.
- `jev.py split` seals each stage as before. Both halves are rated, and they are reported pooled with each half alongside.

**Arms (all K calls sort by recency, 10 posts, in one pinned block, B4):**

| # | Arm | Control, same window | Cells |
|---|---|---|---|
| 1 | Each K query with ` -has:links` added (source `Knl-recency`) | The same query, plain (`K-recency`) | Demand: `demand-tech-1`, `-tech-2`, `-comedy-1b`, `-comedy-2b`. Tool research: `tr-tech-1`, `-tech-2`, `-tech-3`, `tr-comedy-2`. 2 queries each. `Kspam-recency` runs as a reference |
| 2 | Worth-joining posts ≤1 h and ≤2 h old at read | The full 6 h read | The 4 current Worth-joining cards. Under recency, a 2 h window returns exactly the ≤2 h slice of the 6 h call, so this is a cut on the 6 h read at no cost. The relevancy-sort version (2 h against 6 h) is dropped to fit the budget (operator, 28 Sep) |
| 3 | Replies rated with the post they reply to (`parent`) in the packet | The same replies rated without it | Up to 120 replies from all three stages, the first by `sha256(post id)`. The parents are fetched after the pull with one `GET /2/tweets` per 100 (`harness.py parents`), so the search calls stay identical |
| 4 | New cards `wj-comedy-1b` and `wj-tech-2b` | `wj-comedy-1` and `wj-tech-2`, same window | The idea text is unchanged; only the queries change (below) |
| 5 | Three-question rule: type `genuine` (most probable) AND `outside_domain` < 0.5 AND `reply_worthy` ≥ 0.5 | Current rule, `p_good ≥ 0.5` | Every B4 post, from the same answers; no new calls |

`tr-comedy-1` (CapCut) stays out, as in B3 (Claude Code took its place).

**Arm 4 wording.** On B3, off-domain posts (panel majority on `outside_domain`) were 7 and 8 of 10 per query for `wj-comedy-1`, and 5 and 4 of 10 for `wj-tech-2`. Each fix targets what matched:

| Card | Query | What went wrong on B3 | New query |
|---|---|---|---|
| `wj-comedy-1b` | v1 | "stand up" matched "stand up for" in politics | `("stand-up comedy" OR "standup comedy" OR "comedy special" OR "open mic" OR "tight five" OR comedian OR satire OR satirical) -is:retweet -is:reply lang:en min_replies:5` |
| `wj-comedy-1b` | v2 | "bit" matched "a bit"; "hot take" matched sport and crypto | `(comedian OR comic OR "stand-up" OR standup OR satirist) (joke OR bit OR set OR crowd OR heckler OR special) -is:retweet -is:reply lang:en min_replies:10 min_likes:50` |
| `wj-tech-2b` | v1 | "new model" matched cars, fashion and characters; "just dropped" matched spam | `("just released" OR "just dropped" OR "now available" OR "new model") ("AI model" OR LLM OR "open weights" OR "open source model" OR benchmark OR API) -is:retweet -is:reply lang:en` |
| `wj-tech-2b` | v2 | "Grok" matched replies that mention @grok | `(released OR launched OR announces OR announced) (GPT OR Claude OR Gemini OR Grok OR Llama OR Qwen OR DeepSeek) (model OR AI) -@grok -is:retweet -is:reply lang:en` |

`-is:reply` joins both tech queries, as on every other Worth-joining card (a B3 lesson). The filters (`min_replies:`, `min_likes:`) stay as each original had them, so wording is the only other change. A Codex blind review before `config --refreeze` may change the wording once, and any change is recorded here before the pull.

**Measures, with what B3 suggests (a prediction, not a bar):**

| Arm | Measures | B3 suggests |
|---|---|---|
| 1 | Per query pair: posts returned, good rate, spam share (panel type), unique good posts, good posts only the plain query found, good per estimated $ | Knl's good rate is higher (B3: 29% of posts without a link good, 16% with), and it misses about 20% of the good posts |
| 2 | Good rate, and the share of all good posts, by age at read: ≤1 h, 1–2 h, 2–6 h | A ≤2 h cut keeps at least 90% of good posts and drops at least 30% of posts |
| 3 | Per rater, with and without the parent: `text_decidable` yes-rate, good-or-not flips, the panel's dispute rate (not unanimous), Jev's agreement with the panel | Disputes fall and `text_decidable` rises |
| 4 | New card against old: `outside_domain` rate (panel majority), good rate, unique good posts, posts returned | Off-domain falls to at most 30% for `wj-comedy-1b` and at most 20% for `wj-tech-2b` |
| 5 | Share good under each rule, per job; LLM pairwise agreement and κ per rule; Jev's agreement with the panel per rule; the posts where the rules disagree (count and panel type); the operator's call on those posts if labelled | The three-question rule has higher LLM κ, and Jev's gap on Worth joining narrows |

- **Side measure:** the frozen 0.8 cut-off on B4, a second out-of-sample read of B3's 92.6%.
- **Arm 5 caveat:** for Tool research, "reply-worthy" fits badly, because that job looks for evidence, not leads. It is reported, flagged.
- **Circularity:** B3 derived arms 3 and 5 from these raters' diagnostics. Only the operator's optional labels, on up to 40 posts where the two rules disagree, are independent of them.

**Money:**
- **X API:** US$3.00 estimated. That is 48 search calls (US$2.40) and ≤120 parent posts (US$0.60).
- **The limit:** raised to US$8.70 of cumulative estimate (operator, 28 Sep). US$5.26 was used before B4.
- **Expected bill:** X billed 55–60% of the estimate before (about US$1.65–1.80, or A$2.35–2.55 at 0.703). The console reads AUD and is converted at the ECB rate before any comparison.
- **Other raters:** Grok about US$2.3 as a rater. Jev under US$0.10, inside its US$1 ceiling. Codex and Claude run on subscriptions.
- **Not run:** the Worth-joining re-read.

**Run order:**
1. **Checks:** `harness.py status`, and the console before (`console --before <AUD>`).
2. **Freeze and pin:** `config --refreeze`, then `config --pin-block B4`.
3. **Pull, one sitting, outside 19:30–20:30 Brisbane:**
   1. `stage1 --source K-recency` for `wj-tech-1`, `wj-tech-2`, `wj-tech-2b`, `wj-comedy-1`, `wj-comedy-1b` and `wj-comedy-2`.
   2. `stage2 --source K-recency` and `--source Knl-recency` for the four Demand ideas.
   3. `stage3 --source K-recency`, `--source Knl-recency` and `--source Kspam-recency` for the four tools.
4. **Build and seal:** `corpus --stage N --block B4` and `jev.py split` for each stage. Then `harness.py manifest --block B4` and `harness.py parents --block B4`, and `jev.py parent-set` for each stage and half.
5. **Rate** every set and each `-parent` set with all four raters. Claude subagents return their JSON lines in their final reply; `extract_subagent.py` collects them before `raters.py ingest`.
6. **Console after,** then `arms.py --block B4`, and a write-up of totals and rates only, with no post text.

The daily snapshot job stays paused (until 11 Oct) and untouched.

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

### Experiment 3, 28 Sep 2026: the B3 pull (directional)

- **Pre-registered result:** at the frozen cut-off (0.8 on `max(p_good, 1 − p_good)`), Jev decides 108 of 186 final posts (58.1%) and agrees with the Codex/Claude/Grok majority on 92.6% (random, same share, about 80.6%). Validation gave 96.1%, so the 95% level the cut-off was chosen for didn't carry over.
- **By job:** closest to the LLM raters on Tool research and Demand. Weakest on Worth joining, where the level rule overcalls and 5 of 10 reworded verdicts flipped.
- **Stability:** 0 of 30 repeated calls changed a verdict. Confidence AUROC was 0.75–0.83. Every rater answered every post.
- **Not included:** the operator's labels, by the operator's choice; they can be added to validation later. The Worth-joining re-read hadn't run yet.
- **Full write-up and the AUD/USD correction:** [`../jev-build-time-evaluation-2026-09-27.md`](../jev-build-time-evaluation-2026-09-27.md#results-experiment-3-the-b3-pull-28-september-2026).
