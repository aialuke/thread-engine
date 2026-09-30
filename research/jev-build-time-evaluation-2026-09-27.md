# Jev for build-time research and tuning

Research date: 27 September 2026. Status of the sections up to "Decision to revisit after evaluation": an assessment and proposed evaluation, written before any Jev call. Later sections record results from 28 and 30 September 2026.

## Recommendation

**Evaluate Jev as a development-time judge for Discovery search and filtering.** Its potential value is making repeated semantic evaluation cheap enough to compare query recipes, filters, weights, and thresholds against independently reviewed examples. Code should perform optimisation and measurement; the operator's judgments should anchor what “useful” means.

The strongest first test is whether Jev can help evaluate the existing Demand, Worth joining, and Tool research experiments. Predicting engagement or choosing account strategy is a much weaker starting point: the account has little outcome data, and relevance is not growth.

This is a proposal, not evidence that Jev outperforms our current models. No measured savings or quality improvements for thread-engine are claimed.

## What the project already establishes

The [Discovery proposal](discovery-x-api-search-proposal.md) records the decision to use X API search for the product, with query phrasings, sorts, and spam control still under evaluation. Its experimental settings include queries per search, results per query, the Worth joining reply floor, and phrase-group preference. These settings are not all ordinary numerical ranking coefficients; each needs an appropriate experiment.

The factory implementation still uses a Grok relay followed by X API verification in [x_read.py](../scripts/x_read.py). The [factory migration plan](../reviews/factory-drop-grok-plan.md) explicitly describes the move to direct X API reads as unfinished. Our earlier conversation described that older implementation; the build-time recommendations here follow the newer Discovery direction.

The [spam research plan](discovery-test/spam-research-plan.md) already supplies valuable evaluation discipline:

- Spam and off-topic posts have separate labels, and usefulness depends on the job. A launch announcement can be unsuitable for Demand and useful for Worth joining.
- Every positive and unclear example receives a second independent score, with disagreements resolved and agreement reported.
- Filters must preserve genuine posts. Its existing held-out pass bar requires at least 30 genuine posts per job, at most one genuine loss in twenty with an upper 90% bound no greater than 10%, and removal of at least a third of spam.
- Worth joining needs useful results in its top three. Uncertain posts pass through for review.

Jev should be tested inside this framework, rather than introducing a competing definition of success. The earlier pilot's relevance-scoring errors also mean another model cannot simply be treated as ground truth.

## What is distinctive about Jev

Jev takes text or structured context and bounded questions. Choice selects among options; Score evaluates ordered rubric levels; Noul estimates whether a proposition holds. Several questions can be evaluated independently in one request. This fits repeated questions such as “does this post describe a concrete problem?” better than an open-ended request to design a search strategy. [Official introduction](https://docs.typesafe.ai/introduction)

Choice and Score return distributions plus a confidence statistic derived from those distributions. Noul has no separate confidence field. Confidence describes how concentrated an answer is; it is not independently measured accuracy on our task. Domain-specific evaluation must determine useful thresholds. [Confidence](https://docs.typesafe.ai/confidence)

The model documentation currently lists `jev-1.13.0`, text-only input, $0.042 per million input tokens, free output tokens, a 64k total request budget, and a 32k budget for state plus the longest question. Version aliases can move. Pin a version and record the returned model for comparisons. TypeSafe does not offer customer fine-tuning or LoRA: customisation is through state, questions, criteria, and downstream code or models. It says customer requests and responses are not used for training; this does not establish zero retention for an ordinary account. [Models and data handling](https://docs.typesafe.ai/models)

TypeSafe's advertised speed and cost multipliers come from its own workflows and comparison methods. They are not expected savings for this project. Its schema guarantee prevents invalid output shapes, not incorrect semantic judgments. [Launch explanation and benchmark qualifications](https://typesafe.ai/blog/introducing-system-one-models-and-jev)

## Potential use cases

All project benefits below are hypotheses to test, not vendor benchmarks.

| Priority and application | Inputs and Jev's contribution | Benefit to measure | Boundary or dependency |
|---|---|---|---|
| First: query-recipe evaluation | A job brief and retrieved posts; blind assessments of relevance, genuine demand, and usefulness | Useful unique leads per search dollar; coverage within the evaluated pool | It cannot find content the queries never retrieved. Static winning recipes can ship without Jev. |
| First: spam and off-topic filter evaluation | Fixed per-job labels and candidate rule outputs; independent semantic assessments | Spam removed versus genuine posts lost, separately per job | Test simple exclusions and field rules first. Keep uncertain examples for review. Static rules need no runtime Jev. |
| First: ranking-weight tuning | Candidate posts, rubric scores, and exact features calculated by code | Agreement with human shortlists and top-three usefulness | Code searches weight combinations. New posts need semantic scores if the deployed ranker uses them. |
| Next: threshold and review-policy tuning | Scores, distributions, human labels, and asymmetric error costs | Quality at different review workloads; missed genuine leads | Do not transfer thresholds across rewritten rubrics, question types, or versions without retesting. |
| Next: feature discovery | A labelled development set; a generative model proposes questions and Jev evaluates them | Whether additional semantic dimensions improve held-out results | Requires enough independent labels. More features can overfit a small dataset. |
| Next: informative review selection | Model disagreement, uncertain answers, and audited errors | More useful corrections per minute of operator review | Include random sampling so the audit does not see only difficult cases; confident errors matter too. |
| Next: regression and robustness checks | A fixed labelled set, revised prompts, altered input fields, and model upgrades | Detection of quality regressions and brittle decisions | Labels, model version, rubric and input packets must be versioned. |
| Next: failure diagnosis | Misclassified or poorly ranked development examples; bounded labels for off-topic matches, promotion, missing context, or unsuitable conversations | Faster identification of changes worth testing | Error labels are hypotheses to audit. A generative model or engineer proposes changes; final-test errors must not feed tuning. |
| Later: query-overlap analysis | Every query sighting plus a useful/not-useful label | Incremental useful leads added by each query family | Code handles deduplication and attribution. Jev does not establish which query caused downstream use. |
| Later: content and experiment labels | Our posts or drafts, with results hidden while labelling | Better hypotheses about proof, hooks, specificity, and treatment consistency | Observational associations are not causal effects or reliable growth predictions. Existing loop rules remain authoritative. |
| Secondary: evidence-support triage | A claim and its supplied source passage | Fewer unsupported statements reaching deeper review | Flags support relationships; it does not establish source authenticity or replace fact checks. |

### Weight tuning and reusable evaluation

The official [composite-scoring pattern](https://docs.typesafe.ai/patterns/composite-scoring) separates semantic dimensions, normalises them, and combines them with explicit code weights. For us, relevance and contribution potential could be model judgments, while post age, counts, and cost remain exact calculations.

Cache the feature outputs once, then run weight sweeps, threshold sweeps, and feature-removal comparisons locally. Changing a coefficient need not incur another model call. Correlated features can double-count the same signal, so test whether each dimension adds independent value rather than assuming more dimensions improve ranking.

Test **sensitivity**, not just the highest observed score. On development and validation data, perturb weights and thresholds within their allowed ranges, repeat comparisons on resampled conversation groups, and examine alternative labels for unresolved cases. Record how often the preferred configuration changes and how much its shortlist changes. A broad range of similarly good settings is stronger support for a default than a narrow peak that disappears after a minor adjustment. Resolve disputed reference labels independently before final evaluation; do not change them to favour a configuration.

**An important correction to the earlier discussion:** a ranker using Jev-derived features still needs those features for new posts. Removing Jev requires selecting deployable static rules or separately validating another way to produce the features. Offline caching removes repeated experimental inference, not the dependency on scoring unseen inputs.

### Feature discovery: an overlooked close fit

TypeSafe's [autoresearch cookbook](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery) demonstrates a generative model proposing questions, Jev converting text into numerical features, and a separate supervised learner evaluating them. Errors and feature usage inform later proposals. Its example uses wine reviews and a held-out test set, not social-media engagement; it demonstrates a method, not transferable performance.

For Discovery, candidate questions could distinguish an explicit request from promotion, a concrete obstacle from vague dissatisfaction, or a substantive conversation from engagement bait. Start with a small hand-defined rubric. Add automated feature search only after the basic evaluation works, and never reveal final-test errors to the proposal loop.

### Retrieval quality and ranking quality are different

The [official reranking example](https://docs.typesafe.ai/cookbooks/rerank_typesafe) scores query–candidate pairs after initial retrieval. Reranking can improve ordering but cannot recover candidates omitted by retrieval.

Our query experiments should therefore measure both what each query finds and how useful the final shortlist is. Score the deduplicated union of compared queries, retaining every sighting. That permits coverage comparisons within this pool; it does not measure recall across all of X. Include an absolute “none useful” outcome so selecting the best of a poor shortlist is not scored as success.

Also assess **shortlist diversity**. Three relevant posts from the same conversation may offer only one useful opportunity. Report distinct useful conversations alongside top-three relevance; use exact conversation IDs where available and independently checked semantic duplication judgments where necessary. For Demand and Tool research, define diversity around distinct needs or evidence as appropriate to the job. Do not add irrelevant results merely to make a shortlist look varied.

### Search-setting interactions

Query phrasing, sort order, reply floors, and result limits may affect one another. A phrase that works with recency sorting may behave differently with relevancy sorting; a reply floor may remove the useful results of an otherwise productive query. Testing each setting alone cannot establish that their combination works.

Preselect a small set of plausible combinations on development data, compare them under matching windows and budgets, and record the full configuration for every run. Test important pairs before expanding the search; avoid an exhaustive combination search on a small corpus. Jev supplies the semantic assessments, while code compares configurations. Treat differences in available retrieval slots and truncation as part of the experiment, rather than crediting all improvement to the wording.

### Diagnosing failures to guide the next experiment

Use Jev to classify development-set errors into explicit categories such as off-topic match, promotion, insufficient context, or a relevant conversation with no useful contribution opportunity. Keep an unknown category and allow multiple causes where appropriate. Audit these labels against the source material: they are observations about examples, not proof of why a retrieval system behaved as it did.

An engineer or generative model can use the error pattern to propose a more precise phrase group, a field check, or a revised rubric. Test the proposed change against the unchanged baseline, including genuine posts it might lose. For example, repeated game-related matches could motivate a query refinement, but do not justify a blanket exclusion without testing. Use development errors for this loop; final-test errors can inform a later study only with a new untouched evaluation set.

## Proposed pilot

This section specifies a future evaluation, not work authorised or performed by this document. **Under current project rules, start with synthetic examples only.** Real Discovery content must not be sent to Jev unless the operator explicitly authorises that use and the project policy records the permitted fields, provider handling, and retention requirements. Merely having access to local research data does not authorise its transmission. Synthetic tests can establish feasibility and expose rubric failures; they cannot establish real-world search quality or satisfy the existing held-out adoption bar.

1. **Reuse the existing jobs and label definitions.** Begin with synthetic examples reflecting the Discovery taxonomy, adjudication process, and stage boundaries. Steps below describe the eventual real-data comparison, conditional on the explicit policy decision above. Confirm availability and retention before that comparison; do not move private raw API responses or follower data out of their local-only storage.
2. **Establish independent reference judgments.** Resolve positive and unclear cases through the existing second-score process, with operator adjudication for unresolved preferences. Sample rejected cases too. Keep Jev and the existing model blind to query identity, candidate configuration, and outcomes they should not use.
3. **Separate development, validation, and final evaluation.** Develop rubrics and candidate rules on pilot material; use validation to choose weights and thresholds. Reserve untouched later-stage examples for final testing. Group duplicate posts and related conversations together to avoid leakage; check author overlap where feasible. If samples are insufficient, report directional findings and ship nothing on their strength.
4. **Compare useful baselines.** Evaluate the current process, simple deterministic rules, and Jev-assisted evaluation. For ranking, compare against a simple fixed ordering as well as the existing model. Use identical permitted input fields; assess author-enhanced variants separately with their extra cost.
5. **Freeze the evaluation contract.** Before paid collection or comparative tuning, record the primary measure per job, minimum worthwhile improvement, acceptable quality loss for a savings claim, required sample, candidate-trial limit, spending cap, and operator-time budget. Set these against the baseline and existing stage budgets; this assessment does not invent or authorise new limits. Preserve the existing spam acceptance bar. If these choices are unset, limit work to synthetic feasibility checks.
6. **Separate offline and live tests.** Reuse cached feature outputs for ranking and sensitivity experiments. Query exclusions and selected setting combinations require actual retrieval comparisons in the same frozen window with equal budgets and preserved truncation/pagination information; deleting rows from an old result set does not reproduce the changed retrieval pool.
7. **Report the tradeoff.** Show per-job top-three usefulness, distinct useful opportunities, useful unique yield, genuine-post losses, spam removed, unresolved cases, agreement, configuration stability, review time, and end-to-end cost. Audit random cases plus disagreements and confident errors. Use development-error categories to guide bounded revisions. Keep source coverage, label quality, ranking quality, and user outcomes distinct.
8. **Stop and decide.** Stop when the preregistered trial or resource limit is reached, or when the planned evaluation is complete. Select on validation data, then evaluate the frozen candidate once on the final set. A static query change or code filter is preferable when it achieves comparable held-out quality without ongoing inference. Retain semantic scoring only if its incremental benefit clears the agreed adoption criteria. Report insufficient evidence rather than extending the search until something wins.

Record model version, rubric, field packet, query/window/sort, configuration, evaluation split, token usage, elapsed time, and cached responses subject to the project's retention rules. Replaying cached results supports reproducibility; it does not demonstrate that fresh calls are bit-for-bit deterministic.

## Cost and feasibility

Illustration only: 1,000 requests averaging 2,000 billable input tokens would use two million tokens. At the published $0.042 per million, inference would cost **$0.084**. This is arithmetic using an assumed workload, not a measured quote. Request overhead, question text, repeated context, retries, and the actual token usage determine the bill.

The [project's search proposal](discovery-x-api-search-proposal.md) estimates X reads separately and records unresolved billing details. Retrieval and human labelling may dominate Jev inference. Post-retrieval classification cannot refund the cost of fetched spam; a validated query exclusion can potentially avoid fetching it. Report both cost per useful lead and operator time rather than celebrating cheap model calls alone.

At today's small scale, integration and rubric maintenance may cost more time than Jev saves. Include initial setup, adjudication, and recurring maintenance when estimating savings over a stated period. The pilot needs separate caps for API spend and operator time: cheap inference does not make an unlimited search inexpensive. A small evaluation should establish value before building a general optimisation system.

## Failure modes and boundaries

TypeSafe documents weaknesses in numerical precision, dates, literal interpretation, indirect reasoning, distracting context, and adversarial content. It also warns that related questions need not obey expected probability identities. Keep arithmetic and time comparisons in code, minimise irrelevant context, and test posts that try to influence their classification. A Choice between candidates is relative; it does not show that any candidate is suitable. [Known limitations](https://docs.typesafe.ai/model-jaggedness/jev-1.13)

Additional project risks and responses:

- **Optimising for the judge:** if Jev creates both the labels and the success verdict, improvements may only reflect its preferences. Independent labels and an untouched final set are essential.
- **Adaptive overfitting:** repeated query, rubric, and weight searches can exploit validation noise. Limit candidate complexity and trial count, record every trial, and do not repeatedly tune against the final set. A marginal winner that is unstable under sensitivity checks is not a reliable default.
- **Confounding and missing outcomes:** topic, timing, account growth, and distribution affect engagement. Neither semantic labels nor scarce observations establish which content caused follows.
- **Job and niche drift:** evaluate tech and comedy, and the three Discovery jobs, separately. A single global “spam” or “good post” score can erase useful distinctions.
- **Unsupported identity judgments:** text can show promotional patterns; it cannot prove that an author is a bot or a genuine person. Keep unobservable identity claims out of reference labels.
- **Data handling:** the repo's [privacy rules](../reference/x-api.md#privacy) keep follower IDs and raw API responses local. The spam research plan also specifies a private-data deletion deadline, extended by the operator on 27 September 2026 to 26 March 2027 (180 days). Provider non-training statements do not override those constraints. Synthetic examples are the current default; real-content evaluation remains deferred pending the operator's explicit policy decision. This document grants no permission to export data.
- **No model authority over gates:** Jev must not replace approval, fact verification, X read-only restrictions, or deterministic experiment scoring. Any proposed loop rule adoption still follows the existing `/apply` process.

## Decision to revisit after evaluation

Adopt Jev for build-time evaluation only if it clears one of the two routes specified before the pilot: an independently assessed quality improvement large enough to justify its cost, or an effort/cost reduction with quality inside the agreed tolerance. Both routes must preserve the existing job-specific acceptance criteria. Report uncertainty and sensitivity alongside the result; nominally better scores alone are insufficient.

The minimum worthwhile improvement and resource limits remain **decisions to make before running the pilot**, not established findings. If the budget ends before the required evidence exists, conclude “inconclusive”; if the completed comparison misses the agreed bar, do not adopt. Any extension needs a new explicit scope and must not reuse an exposed final set as an untouched test.

Publish the comparison even if the answer is “not useful at this scale.” The useful deliverable is a better-supported search or filtering decision, not a Jev integration for its own sake.

Primary sources are linked beside the claims they support. Vendor examples are evidence of available techniques; every thread-engine application and expected benefit remains a proposal until tested locally.

## Results: experiment 3, the B3 pull (28 September 2026)

Directional only. There is no answer key: Jev, Codex `gpt-5.6-sol`, Claude `claude-opus-5-5` and Grok `grok-4.5` (billed `grok-4.5-build`) are peers, and "the panel" is the strict majority of the three LLM raters. Totals and rates only; no post text. Pre-registration, measures and commands: [`jev-test/README.md`](jev-test/README.md), Experiment 3.

### The data

- **Pull:** Discovery block B3, 02:18–02:24 Brisbane, 28 Sep. Stage 1 K for 4 ideas, T for `wj-tech-1`/`-2`, Stage 3 K for 4 tools (both sorts), Stage 2 K for 4 Demand ideas (both sorts), Stage 3 Kspam. 49 calls returned 200, with 554 posts (464 unique). `min_replies:` was accepted on this tier. The following timeline read 100 posts, and its keyword rule kept 1.
- **A harness bug, fixed mid-pull:** B3's Tool research window began exactly 7 days before the block opened, so X refused all 16 Stage 3 calls a minute later (HTTP 400, nothing billed), and the steps were still marked done. Fix and tests: commit `d08ba19`. Stage 3 was then rerun cleanly.
- **Sealed split:** 364 unique posts (1 dropped: its conversation was already in the 298-post development set). Validation 178 (Worth joining 30, Demand 73, Tool research 75); final 186 (42, 63, 81).
- **Every rater answered every post** in both halves. No answer was unavailable or rejected by the shared validator, so "unavailable counted as wrong" and "valid only" are identical.
- **Operator labels:** not used. The operator chose to run the comparison without them (28 Sep). A 60-post labelling page (40 disputed, 20 random) is built and can be added to validation later. Measure 9 and the two operator-based diagnostics are therefore not reported.
- **Worth-joining re-read:** not yet run at the time of writing.

### The pre-registered result

The cut-off was chosen on validation. The rule was the widest coverage with pooled agreement of at least 95%, which gave 0.8 on `max(p_good, 1 − p_good)`: 57.3% of 178 posts at 96.1%, against 88.3% for the same share picked at random. It was frozen at 21:11 UTC (commit `ec3aeaa`) and applied once to final:

| Final set | Jev decides | Agreement with the panel | Random, same share |
|---|---|---|---|
| Worth joining | 23 of 42 (54.8%) | 95.7% | 83.3% |
| Demand | 37 of 63 (58.7%) | 91.9% | 81.0% |
| Tool research | 48 of 81 (59.3%) | 91.7% | 79.0% |
| **All** | **108 of 186 (58.1%)** | **92.6%** | about 80.6% |

The cut-off kept its coverage but not its agreement: 96.1% on validation became 92.6% on final. That is the transfer failure the CMU paper warns about. Read at face value, Jev could take over a little under three-fifths of the LLM panel's good-or-not calls, at roughly one disagreement in fourteen.

### Around it (final sets unless stated)

- **Jev against each LLM rater (p_good ≥ 0.5):**
  - Worth joining: 81.0–83.3% agreement, κ 0.36–0.46. The LLM raters agree with each other on 95.2–97.6% (κ 0.73–0.88).
  - Demand: 77.8–85.7%, κ 0.45–0.46. LLM pairs: 76.2–90.5%, κ 0.35–0.77.
  - Tool research: 75.3–84.0%, κ 0.41–0.46. LLM pairs: 79.0–90.1%, κ 0.53–0.79.
  - Jev sits inside the LLM range on Demand and just below it on Tool research. On Worth joining it is clearly the outlier.
- **The most-probable-level rule overcalls Worth joining.** Under it, Jev calls 42.9% of final Worth-joining posts good, against 7–12% for the LLM raters. The p_good rule gives 26.2%, and it is the rule that was frozen.
- **Soft agreement** (distance from the other raters' mean p_good; lower is closer): Jev 0.223 on Worth joining, against 0.090–0.113 for the LLM raters. On Demand, 0.152 against 0.068–0.147. On Tool research, 0.127 against 0.061–0.172.
- **Does higher confidence mean higher agreement?** TypeSafe's claim held directionally. The confidence AUROC against panel agreement was 0.759 (Worth joining), 0.745 (Demand) and 0.832 (Tool research) on final; validation gave 0.727, 0.764 and 0.831. Agreement rises with the cut-off in every set, and nothing is near the 0.5 that would mean confident disagreement.
- **Promotion and bait:** on posts the panel types as promotion, product marketing or engagement bait, Jev agreed with the panel more than on the rest: 76.9% against 62.1%, 95.8% against 64.1%, and 96.4% against 73.6% (level rule). Jev's disagreements are on the genuine-looking posts, not on polished promotion, which is the opposite of the style trap the CMU paper found. These are obvious-promotion posts, though, not an adversarial test.
- **Per idea, level rule:** the weak spots are "builders sharing progress" (28.6% agreement, n=7), the comedian-riffing idea (58.3%, n=12) and "what people are collectively reacting to" (50–75%, n=16). The strongest is "people asking for a free alternative" (90–100%, n=10).
- **Stability:**
  - Jev asked the same thing again (10 posts × 3 fresh calls) changed 0 good-or-not calls, and p_good moved by at most 0.051.
  - Jev with the questions reworded (30 validation posts) changed 7: 5 of 10 in Worth joining, 2 of 10 in Demand, 0 of 10 in Tool research.
  - The LLM raters re-run in a fresh session (30 Worth-joining posts, whole sets only, so fewer than the planned 50): Grok 100% (κ 1.0), Claude 93.3% (κ 0.63), Codex 90.0% (κ 0.77).
- **Ranking:** Jev picked the same best post for 3 of the 4 Worth-joining ideas with the candidates in both orders, on validation and on final.

### Costs

- **Jev:** US$0.024 for experiment 3 (US$0.025 including experiment 1), against the US$1 ceiling.
- **Grok raters:** about US$1.42 in all (validation US$0.60, repeat US$0.11, final US$0.70).
- **Codex and Claude:** ran on subscriptions, so there is no per-call figure.
- **X API:** the harness estimated US$2.77 for this pull, making US$5.26 of the US$7 limit.
  - The console went from A$17.55 to A$15.23, a drop of A$2.32. At 0.70302 US$ per A$ (ECB reference rate for 25 Sep, the latest before the pull, via frankfurter.app), that is about **US$1.63**, 59% of the estimate. The daily snapshot job was paused, so nothing else was billed.

### Correction: the earlier "$0.34 against the $0.455 estimate"

`discovery-test/HANDOFF.md` and `discovery-x-api-search-proposal.md` compare the pilot's console drop, $19.20 to $18.86 ($0.34), with the harness's US$0.455 estimate. The console shows AUD (operator, 28 Sep), so that comparison probably set AUD against USD. Converted at the same rate, A$0.34 is about US$0.24, 53% of the estimate, not 75%. The snapshot job's share of that pilot drop is still unknown.

Both readings now point the same way: X billed about half to three-fifths of what the harness estimates. Deduplication of posts read more than once on the same UTC day doesn't fully explain it here: 464 unique posts at US$0.005 would be about US$2.32. The cause is unverified. Candidates are the timeline's price (the estimate reserves US$0.50 for it), deduplication rules we haven't read, and the rate the console uses for AUD. Treat the harness estimate as a conservative ceiling, not a bill.

### What this says

- **Tool research and Demand:** a cheap Jev first pass could plausibly settle a little over half the posts at about 92% agreement with the LLM panel, and send the rest to an LLM. That is about 12 points better than picking the same share at random.
- **Worth joining:** Jev is unreliable. The level rule overcalls, a rewording flips half the verdicts, and its agreement with the other raters is weakest there, even though the confident slice looked good (95.7%, n=23).
- **The cut-off:** the 95% level set on validation did not hold on final. Any deployment would need a stricter cut-off, or re-checking per job.

Directional only. The decision on whether Jev earns a place in build-phase query experiments is the operator's.

## What we learnt for the product (from the B3 raters' answers)

The experiment asked what Jev's decisions, and the LLM raters' answers alongside them, teach us about search and filtering. It did not ask whether to ship Jev. Every post's typed answers were joined back to the query, sort and rank that found it. "Good" means the Codex/Claude/Grok majority, not ground truth: 364 posts, one night, directional. The diagnostic figures are partly circular, because the same raters gave both the diagnostic and the verdict. The Jev-only gates are not.

### X API search

- **Most of what X returns isn't usable.** Only 24% of posts (89 of 364) were good. 55% were promotion, product marketing, engagement bait or off-topic. Filtering, not retrieval, is where the product's value is.
- **Query wording matters far more than sort order or rank.**
  - One Demand idea under two phrasings gave 20% good with 42% spam, against 33% good with 5% spam.
  - Rank barely mattered: positions 0–2 were 24% good, 3–5 were 27%, 6–9 were 22%. Take all 10 results and filter, rather than trusting the top few.
- **Keep several phrasings per idea.** Most good posts were found by only one query, so dropping a phrasing loses leads, not duplicates.
- **Posts with a link are half as likely to be good** (16% against 29%). The spam-control query (`-has:links -giveaway …`) had the best Tool research yield (32–36%). Excluding links outright would have lost 20 of the 89 good posts, so treat a link as a ranking penalty, not a filter.
- **Keep replies for Demand and Tool research.** In Tool research, replies were good 42% of the time against 24% for original posts. `-is:reply` belongs on Worth joining only.
- **Worth joining is about freshness, not reply counts.** Every good Worth-joining post was under an hour old (10 of 51, against 0 of 21 older), and reply count predicted nothing (3–9 replies: 0 of 8). A shorter window is worth testing, and `min_replies:` floors look unhelpful. The samples are small.
- **Some idea cards need rewriting.**
  - 65% of `wj-comedy-1`'s results and 40% of `wj-tech-2`'s were outside the idea's domain.
  - The healthiest cards were `demand-comedy-1b` (49% good) and `tr-tech-3`, Claude Code (43%).

### Filtering

- **Good is almost entirely genuine.** 53% of the posts the panel typed genuine were good, and about 0% of every other type (2 of 199). The first question for any filter is "is this a real person talking about this subject?"
- **Jev's post type alone makes a strong first pass.** Dropping what Jev types as not genuine removes 35% of posts (126) and loses 5 of the 89 good ones.
- **Outside the idea's domain rules a post out.** None of the 49 posts flagged that way were good; the video-game trap is real. Every card needs that check, in its wording or as a question.
- **"Is this reply-worthy?" beats "is this useful?".** Reply-worthy posts were 61% good, the rest 4%. The graded "useful" (0–2) was the unstable question: it drove the rewording flips, and Jev scored it about half a level above the LLM raters.
- **A post answering someone else's need is mostly not a lead** (8% good), but not never.
- **Candidate product rule:** genuine AND in the idea's domain AND reply-worthy. Three concrete yes/no questions, combined in code.

### Building the judging step, with any model

- **Concrete yes/no questions are stable; graded ones drift.** Repeating a question changed 0 of 30 verdicts, while rewording the graded ones changed 7 of 30. Version every question's wording.
- **Replies need their parent post.** Posts the raters marked "can't judge from the text" were disputed more often (33% against 20%). Fetch the post a reply answers (`referenced_tweets` expansion) and include it in the packet.
- **Use confidence to route.** Higher confidence meant higher agreement (AUROC 0.75–0.83). Auto-accept the confident calls and queue the rest.
- **Even strong models disagree on about 1 post in 5** (22% disputed). That disputed slice is the natural human-review queue.
- **Set cut-offs per job and re-check them after any change.** 96% on validation became 93% on final.

### Cost

X billed about 55–60% of the harness estimate, in both the pilot and B3. Treat the estimate as a ceiling.

### Tests for the next pull

1. A `-has:links` query variant against the plain one, in the same window.
2. Worth joining with a 1–2 hour window instead of 6.
3. The parent post included in the packet for replies.
4. Rewritten `wj-comedy-1` and `wj-tech-2` cards.
5. The three-question rule against the current product rule.

All five can be measured with the same raters and harness.

## Judging text with Jev (glossary, placement and Proof runs, 30 September 2026)

Four runs asked Jev to judge repo text: glossary candidates against how the repo uses each term (two runs), where a set of learnings should live (one run), and whether the word "Proof" carries one sense (one run, with a known-split control and a wording follow-up). Protocol, controls and pass rules are in `research/jev-test/README.md`; the procedure is the `jev-judge-run` skill.

### Which question types held up

| Question | Control result | Use it? |
|---|---|---|
| Implementation detail in a definition | 0.98 on a file-name-laden definition against 0.16-0.33 on the real entries | Yes |
| Project-specific term or general word | General terms scored 0.08-0.14, defined terms 0.79-0.95 | Yes |
| Used in one sense | Clean terms 0.76-0.91, muddy terms 0.09-0.18 on a hand-audited set (gap 0.69). Proof run: clean 0.75-0.81, muddy 0.09-0.19; a known 4-and-4 split of one word (Hook as the opening Card against Hook as a tool hook) scored 0.21, and 0.18 with a parenthetical added to the question | Yes, with a hand-audited calibration set and a known-split control asked in the judged question's own wording |
| Cloze: which glossary entry fits a blanked usage | 1.00 on clean terms; separated overlapping entries (Explore and exploit against Slot) | Yes |
| Definition faithful to a usage (yes/no) | Wrong Shout-out definition 0.52 against 0.53 for the right one. Proof run: wrong definition 0.14 against 0.79 for the right one | No: one separation does not overturn one failure; repeat first |
| Definition self-contained | Real entries 0.24-0.56, the undefined-word control 0.24. Proof run: control 0.19 against 0.41-0.42 on the real definitions | No: a gap, not a clean split |
| Where should this learning live (Choice of six documents) | 2 of 5 controls right, confidently wrong (0.79-0.90) | No |
| Cost of misreading (Score, five levels) | Answers split between the extremes (0.25 at level 0, 0.29 at level 4) | Not as one Score question |

### What we learnt

- **The calibration set decides the run.** The first run failed because Lane and Slot were labelled clean unread. Reading 8 usages of each term found real overloads (Slot as clock time, feed position and Experiment Slot; Voice as tone, voice notes and voice samples). The reruns used a hand-audited set.
- **Snippet quality moves scores.** Code identifiers and field names (`"cohort": []`, `retrospective: false`), a code-graph folder and third-party notes pulled faithful scores down. Prose only, no matches inside backticks and a provenance filter fixed most of it.
- **A yes/no on a tangential snippet sits near 0.5.** Most usages mention a term without saying enough to confirm or refute a definition. Untested next step: a Choice of consistent, contradicts or silent per snippet, on snippets where the term is the subject.
- **Jev did catch a wrong definition once** (Shout-out as a line in a Card, faithful 0.29 in the first run), but not under the second run's sampling. One catch is not validation.
- **Placement is a convention judgment.** Choosing between documentation homes depends on what each file is for, which the state could not carry. Not a fit for Jev.
- **Rankings held across runs** (Voice and Explore and exploit low on one-sense in both), though the snippets differed. Repeats with different samples show the variance; one run does not.
- **Cost:** about $0.01 per full battery of 17 requests; the placement run was 2 requests.
- **Proof run: Jev gave no usable signal, and a blind Codex disagreed with its first reading.** Under the question's first wording Jev saw no overload (one-sense: evidence-only 0.76, proof-line-only 0.81, mixed 0.64) and a known-split control (Hook, 0.21 and 0.18) showed that wording can catch a large split. Under a neutral wording the same snippets were inconclusive (0.56, 0.71, 0.44; a pure card under the 0.60 floor). A blind Codex, given the 38 usages unlabelled, found four senses and said more than one glossary entry was needed. The operator settled it on 30 September with two glossary entries (Proof and Proof line), decided from the repo's own usage and Codex's reading, not from Jev. Reading (untested): one-sense catches a domain split (post copy against tool plumbing) and may miss a smaller difference inside one domain (an attached file against a sentence of copy).
- **A control must use the judged question's wording.** The first known-split control omitted the "alone or in 'proof line'" parenthetical the Proof cards carried, so it validated a different question; a blind Grok review caught this. The neutral Proof wording lowered all three Proof cards by 0.1-0.2 while the Hook control did not move, which fits the parenthetical having lifted the Proof scores (inference).
- **List what is in each card's state, not only the snippets.** The Proof and calibration cards carried the 36 glossary definitions from `CONTEXT.md`, and the run's disclosure said `CONTEXT.md` was not sent.
- **Jev cannot find a sense the card does not offer.** My cards tested two senses; Codex found two more (a standard of evidence for a claim, and a test that an agent cannot reach approval). Cluster the usages blind first, then build the cloze options from what it finds.
- **Label from full lines, not grep cuts.** Labels made from truncated hits misfiled two lines of the approval-test sense as plain English and missed one line using two senses. The five lines I called ordinary English scored 0.00 on cloze, which was the warning: I verified two of them were mislabelled, and Codex put the other three in a third sense (unverified).
- **Definition noise was about 0.1 on the Proof run.** The same evidence-only snippets scored 0.64-0.66 under three control definitions and 0.76 under the real one. A mixed-against-pure gap of 0.12 is inside that; the `jev-judge-run` skill asks for the shift to be measured and treats a gap inside it as no finding.
- **Proof run cost:** 55 requests (40 main run, 3 hook control, 12 wording follow-up), about $0.02 at the documented $0.042 per million input tokens (466,957 input tokens; arithmetic, not a bill). Count requests from the saved answer files.
