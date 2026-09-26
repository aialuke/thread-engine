# Codex's blind adversarial review of the Discovery proposal and the spam research plan (26 Sep 2026)

gpt-5.6-sol, high effort, read-only. Job task-muichxru-fvlkxb. The brief is kept in the session scratchpad. Codex's own words below; citations spot-checked (harness.py:742-743, plan.md:46-47, harness.py:1284-1286 all match).

Verdict: Do not settle D-A, D-C, D-D, or D-E yet; approve only the narrow architectural direction—stable X API mechanics in code—then finish job-specific, like-for-like tests with a corrected labelling protocol.

## High

1. **Claim attacked: D-A can be settled before the remaining stages, with Stage 2 merely confirming it.**

   **Evidence:** D-A chooses X API for both Demand and Worth joining, while acknowledging that only Stage 2 will confirm Demand (`research/discovery-x-api-search-proposal.md:9-10`) and that Worth joining has no pilot data (`research/discovery-x-api-search-proposal.md:143`). The pilot compared one K query family with five Grok styles and explicitly did not run K’s second frozen variant (`research/discovery-test/private/facts.md:71-76`). The original decision rule spans all six job–niche cells, with Worth joining in Stage 1, Demand in Stage 2, and Tool research in Stage 3 (`research/discovery-test/plan.md:44-56`).

   **Why it matters:** The source decision is being generalized from one idea and one window under unequal retrieval opportunities. **Inference from Plan B’s proposed order:** “settle Plan A, then Stage 2” makes the decision precede its stated confirmation and bypasses the only evidence planned for Worth joining.

   **Fix:** Split D-A by job. Decide Worth joining only after Stage 1, Demand only after Stage 2, and Tool research only after Stage 3. Until then, record “X API + model-built queries” as the preferred hypothesis, not the selected source.

2. **Claim attacked: Stage 2 will test the configuration Plan A proposes.**

   **Evidence:** Plan A proposes newest-first sorting for Demand (`research/discovery-x-api-search-proposal.md:81-85`), but Stage 2 specifies relevancy sorting (`research/discovery-test/plan.md:46-47`) and the harness hard-codes Demand to relevancy (`research/discovery-test/harness.py:742-743`). The pilot’s reported K pool combines recency, relevancy, a reply floor, and an earlier engagement floor (`research/discovery-test/private/facts.md:71`).

   **Why it matters:** Stage 2 cannot confirm the proposed production system if it tests a different ranking. Combining several K variants also gives the pilot K yield that no single proposed production configuration achieved.

   **Fix:** Either align Stage 2 with newest-first, or make sort order a frozen randomized factor and report each sort separately. Do not pool their useful-post counts when judging D-A.

3. **Claim attacked: D-C’s phrase-list shape is the right interface for MJ2 generally.**

   **Evidence:** The proposed shape is specifically `asking`, `alternative`, `products`, and `exclude`, producing two “free alternative” query forms (`research/discovery-x-api-search-proposal.md:91-105`). But Stage 2’s four Demand ideas also include frustration with coding agents, current collective annoyance, and emerging jokes or memes (`research/discovery-test/plan.md:21-26`); their frozen queries use entirely different clause structures (`research/discovery-test/harness.py:678-692`).

   **Why it matters:** D-C does not describe an engine-independent Demand interface; it describes one pilot idea. Implementing it now either excludes three planned demand types or forces code to infer semantics that the model output did not express.

   **Fix:** Test either a generic clause schema—named phrase groups plus explicit AND/OR composition—or separate schemas per demand archetype. Settle D-C only after all four Stage 2 ideas can be represented without special-case prose.

4. **Claim attacked: blind Codex scoring plus a 20% author re-score is adequate ground truth for Plan A or Plan B.**

   **Evidence:** In the first six-post re-score, only two agreed and Codex was more relevance-lenient on four (`research/discovery-test/private/facts.md:63-66`). Even after tightening the brief, three of Grok’s eight “good” posts were off-topic game questions (`research/discovery-test/private/facts.md:71-75`). Nevertheless, the main protocol retains only a 20% re-score (`research/discovery-test/plan.md:52-55`).

   **Why it matters:** The errors are systematic, not random. They directly change the headline comparison from Grok 8 vs K 2 to Grok 5 vs K 1–2. Plan B would then train and evaluate spam rules against labels already known to confuse relevance, off-topic content, promotion, and genuine demand.

   **Fix:** Independently score and adjudicate every positive, every unclear item, and a substantial random sample of negatives. Report agreement and confusion matrices separately for relevance, spam/promotion, and off-topic. A 20% audit can resume only after calibration shows acceptable agreement.

5. **Claim attacked: deletion after one day is ground-truth spam.**

   **Evidence:** **Inference from Plan B step 4:** disappearance does not identify why a post vanished. The existing evidence calls ten already content-identified account-selling posts “likely deleted”; deletion was corroboration, not the basis of their spam label (`research/discovery-test/private/facts.md:20-23`). The harness correctly records an absent re-read only as `gone` (`research/discovery-test/harness.py:1342-1352`).

   **Why it matters:** Treating every deletion as spam will contaminate both the taxonomy and field-rule evaluation with self-deletions, account deletions, moderation for unrelated reasons, and possible lookup failures.

   **Fix:** Preserve `gone_after_24h` as a separate observed outcome with reason unknown. Use it as a candidate predictive feature or secondary metric, never as the spam truth label without independent evidence.

## Medium

1. **Claim attacked: all of D-B belongs in product code as a settled rule.**

   **Evidence:** D-B combines stable API mechanics with “per-job defaults” and “spam control” (`research/discovery-x-api-search-proposal.md:11`), and later makes a shared spam list a rule for everyone (`research/discovery-x-api-search-proposal.md:107-111`). Yet spam research is explicitly pending, and the proposed exclusions remain untested (`research/discovery-x-api-search-proposal.md:128-139`).

   **Why it matters:** Syntax validation, eligibility, limits, and cost caps are invariants; spam heuristics are empirical, job-dependent classifiers. Treating both as universal code rules risks silently suppressing genuine posts.

   **Fix:** Accept D-B only for syntax, window enforcement, eligibility, limits, logging, and cost caps. Keep spam/off-topic rules versioned and job-specific, with an “uncertain/pass through” outcome, until Plan B validates them.

2. **Claim attacked: Plan B’s existing corpus can both produce and validate field-based rules against the proposed pass bar.**

   **Evidence:** **Inference from Plan B steps 3–5:** no held-out set is specified. The current joint corpus contains only 39 eligible posts from one idea and one 24-hour window, with approximately five adjusted good posts (`research/discovery-test/private/facts.md:69-76`). The product test deliberately spans distinct jobs, niches, and windows (`research/discovery-test/plan.md:21-29`).

   **Why it matters:** Rules tuned and evaluated on the same small retrieval-biased corpus will overstate performance. The example “lose at most 1 genuine in 20” cannot even be exercised on the present adjusted positive set, much less estimated reliably per job.

   **Fix:** Pre-register metrics, train on the pilot, and evaluate on temporally held-out Stage data stratified by job, niche, source, and query variant. Require an absolute minimum number of genuine posts and report uncertainty, not only observed percentages.

3. **Claim attacked: the proposed author/post fields will be available to the deployed filter and its labelers.**

   **Evidence:** Author-read cost remains unmeasured, so author checks are currently off (`research/discovery-test/private/facts.md:9-11`). The stage plan includes author fields only if the pilot shows they are affordable (`research/discovery-test/plan.md:47-48`). Existing blind scoring exposes text only (`research/discovery-test/plan.md:52-55`; `research/discovery-test/harness.py:1476-1486`).

   **Why it matters:** A rule based on account age, biography, follower ratios, or verification cannot ship on a tier that does not fetch author expansions. Conversely, text-only adjudicators cannot reliably validate purported author-level spam signals.

   **Fix:** Define the deployable feature vector first. Evaluate post-only and author-enhanced filters separately, including their incremental cost. Give adjudicators a fixed field packet where needed while still hiding source, query, and rank.

4. **Claim attacked: D-E’s recorded variant is enough for the loop to learn which phrase caused success.**

   **Evidence:** Plan A maps a used lead directly to a phrase-family outcome (`research/discovery-x-api-search-proposal.md:113-115`). But three pilot “good” posts appeared under four Grok styles (`research/discovery-test/private/facts.md:57`), and five posts appeared in both K and Grok (`research/discovery-test/private/facts.md:71`). The test storage already anticipates every source and rank, not one attribution (`research/discovery-test/plan.md:60-64`).

   **Why it matters:** **Inference:** an action on a multiply-found lead cannot identify which variant caused discovery. Updating phrase weights from single-touch attribution will reward overlap, query order, and popular posts rather than incremental yield.

   **Fix:** Store every sighting, variant, rank, and retrieval time. Learn through controlled rotation or holdouts, define multi-touch credit explicitly, and require minimum samples before changing a Weight.

5. **Claim attacked: cost evidence is settled enough for the per-dollar source decision.**

   **Evidence:** Plan A concludes the billing estimate “errs high” from one aggregate console delta (`research/discovery-x-api-search-proposal.md:60`). The facts table says per-step costs are estimates, author billing is unseparated, and same-day repeat billing is not measurable (`research/discovery-test/private/facts.md:4-11`). L2-C6 still explicitly depends on confirming per-post billing (`research/layer-2-x-data-tiers.md:491-501`), while the source decision rule is useful posts per dollar (`research/discovery-test/plan.md:52-56`).

   **Why it matters:** The unexplained delta may be deduplication, unbilled failures, or another billing rule. It cannot safely price the product or establish which source wins per dollar.

   **Fix:** Use a cost range and sensitivity analysis until isolated billing measurements exist. Keep subscription-pilot costs separate from expected production API costs.

6. **Claim attacked: the spam-control query can remain inside the ordinary Stage 3 source comparison.**

   **Evidence:** The plan promises 20 K posts per idea from two variants (`research/discovery-test/plan.md:44-48`), but the harness adds a third spam-control query for Tool research (`research/discovery-test/harness.py:1284-1295`).

   **Why it matters:** K gets up to 30 retrieval slots while G gets up to 20. Per-dollar adjustment does not repair comparisons of unique yield, spam share, or recall, and the intervention is no longer a clean paired test.

   **Fix:** Keep the two-query source comparison frozen. Run the spam-control variant as a separate paired ablation over the same window, score the union, and report what it removed and what it newly surfaced.

## Low

1. **Claim attacked: D-D’s bounds are ready to become loop-tunable Weights.**

   **Evidence:** Plan A proposes 2–3 queries, 10–20 results, a reply floor of 1–10, and phrase-family preference (`research/discovery-x-api-search-proposal.md:107-111`), while Worth joining is wholly unmeasured (`research/discovery-x-api-search-proposal.md:141-146`). The pilot established only that `min_replies:` is accepted, not that any floor improves lead quality (`research/discovery-test/private/facts.md:61-62`).

   **Why it matters:** Bounds presented as tunable policy look evidence-based when most have not been compared.

   **Fix:** Treat them as experimental defaults. Promote each to a bounded Weight only after its job-specific stage supplies an outcome and enough observations to tune it.

## What is sound

- Keeping syntax conversion, the 512-character guard, exact-window eligibility, logging, and cost caps in backend code is well supported by the observed API behavior and the product’s fixed-code safety boundary (`research/discovery-test/private/facts.md:14-19`; `reviews/ui-direction.md:52-54`).
- Source-blind, shuffled scoring; frozen queries; scoring every retrieved post; randomized source order; and retaining every sighting are the right experimental foundations (`research/discovery-test/plan.md:44-56`; `research/discovery-test/harness.py:1260-1261`; `research/discovery-test/harness.py:1357-1387`).
- Plan B is directionally right to separate spam from off-topic, define taxonomies per job, fix acceptance criteria before testing, and use a paired live exclusion test. Its order and ground-truth construction need the changes above.
- For this specific free-alternative Demand idea, keeping replies and avoiding an engagement floor are credible hypotheses: five of nine pilot positives were replies and seven had zero likes (`research/discovery-x-api-search-proposal.md:42-50`). They should not yet be generalized to every Demand archetype.

