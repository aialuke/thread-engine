The plan has the right comparison question, but it is not spend-ready: it would violate the repo’s current research path, cannot reliably attribute spend or Grok retrieval behavior with today’s clients, and leaves too little protected credit for the scheduled snapshots. Fix the high findings before a pilot; otherwise a “winner” could be operationally unusable or the test could impair the account’s core measurement loop.

## High

- **K and T have no permitted or implemented execution path.** The repo contract sends other people’s posts/research through Grok or `x_read.py`, not `x_api.py`; the latter’s CLI has no search, counts, or reverse-chronological-timeline command (`AGENTS.md:20`; `scripts/x_api.py:2-20`, `350-366`). Thus direct X search/timeline calls would both breach the current operating rule and produce a recommendation the factory cannot use.  
  **Fix:** before spending, explicitly authorize this exception, define the allowed endpoints/privacy handling, and add/test a read-only collection command. Otherwise remove K/T from this experiment.

- **The Grok arm cannot record the evidence needed to price or reproduce it.** The plan requires `x_posts_fetched`, cost, and what Grok returned (`discovery-test-plan.md:27,42`), but the current relay discards the CLI envelope except for generated JSON text and `total_cost_usd` (`scripts/grok_read.py:35-45`). xAI documents that raw tool outputs are unavailable, and model text is not a structured retrieval result (`discovery-grok-docs.md:32-38,84-89`).  
  **Fix:** preserve the complete permitted CLI/API envelope in private scratch, including tool usage counts, citations, model/version, prompt, timestamps, and token/tool costs; record the post IDs claimed, verified, and dropped. If those fields cannot be captured, do not claim per-post Grok cost, tool choice, or recall.

- **The $0.20 pilot and $2.50–6 estimate omit known verification and likely expansion costs.** Every Grok candidate is ID-checked with an author expansion; today that costs about $0.005 per post plus $0.010 per returned author (`scripts/x_read.py:10-14`; `scripts/x_api.py:256-268`; `reference/x-api.md:29`). Under the plan’s 10-result assumptions, the pilot’s search, expansion, timeline, filtered-search, Grok fetch, and Grok verification are already roughly $0.45 before counts pricing and Grok tokens—an inference, conditional on ten distinct authors and the documented rates. The plan’s own docs say search and expansion pricing remain unverified (`discovery-xapi-docs.md:63-73,101-113`).  
  **Fix:** make a worst-case call-by-call budget table, including distinct author reads, Grok tool fetches, token cost, ID verification, and unknown counts pricing. Use a $1 pilot ceiling, not $0.20, and stop before each call if its worst case breaches the reserve.

- **The proposed $3 reserve is unsafe for the shared snapshot workload.** The plan permits spending $6 from today’s $9 credit (`discovery-test-plan.md:57-61`), while the scheduled snapshot is daily at 20:00 (`README.md:53-55`; `ops/launchd/com.exitzerocode.thread-engine.snapshot.plist:5-11`) and expected to cost up to about $0.25/day (`reference/x-api.md:52-54`). **Inference:** $3 covers only 12 worst-case days, not the roughly 20 days from 26 September to the stated 16 October read.  
  **Fix:** reserve forecast snapshot spend through the billing-cycle reset or the last protected experiment read, plus a failure/retry buffer; spend only the remainder. Schedule test work outside a documented no-run window around 20:00 and check the console cap immediately before each stage.

- **The privacy gate is not resolved.** The plan sends other people’s post text and numbers to Codex (`discovery-test-plan.md:63-68`), whereas repo privacy practice keeps raw third-party API data local and out of model sessions (`reference/x-api.md:48-50`). The supplied xAI findings further conclude that sending personal data requires ZDR, with non-ZDR content retained up to 30 days (`discovery-grok-docs.md:93-106`).  
  **Fix:** do not send raw post text, handles, IDs, or author signals to Codex unless the applicable service route is confirmed ZDR and this use is approved. Score locally from de-identified excerpts/feature codes, or obtain a specific privacy decision first.

## Medium

- **C cannot answer the stated tool-research job.** Counts can measure volume, but not “how people talk about” a product or whether results are actually about it (`discovery-test-plan.md:6,12,38,49`). It is therefore incomparable with K/G useful-post yield.  
  **Fix:** split this into two outcomes: prevalence (C, with exact query/window) and discourse quality (a fixed sampled post set from K/G). Do not rank C on useful posts per dollar.

- **Source windows and effort are confounded.** K gets 20 candidates per idea, G up to 10, while T gets one shared set of 100 locally filtered posts; G’s “recent” prompt does not enforce the same hour-level window (`discovery-test-plan.md:34-42`; `discovery-grok-docs.md:18-37`). Source order also changes age and engagement during collection.  
  **Fix:** preregister a common UTC start/end window, run each idea in several time blocks with randomized source order, record start/end timestamps, and cap the scored candidate set equally per source/idea. Score the complete retrieved set, not a source-aware hand-picked subset.

- **The scoring is only partly blind and is gameable at selection time.** The judge sees age and engagement, which can reveal T versus search; more importantly, local T filtering and K query-writing can preferentially pass strong candidates before blind scoring (`discovery-test-plan.md:35-53`).  
  **Fix:** freeze idea cards and query templates before collection; have a mechanical eligibility filter; assign randomized opaque IDs; redact source, query, rank, collection time, handle, and author signals. Keep age/metrics only if the rubric truly needs them, and record a source-blind adjudication file before unmasking.

- **The sample cannot distinguish sources.** At most 10–20 candidates per source/idea and a 20% re-score is too small for a reliable “best source” decision, especially after duplicates and spam are removed (`discovery-test-plan.md:34-55`).  
  **Fix:** define a minimum practical difference beforehand, collect repeated blocks until each source/job has a target number of unique scored candidates, and report uncertainty intervals. If the interval overlaps the decision threshold, conclude “inconclusive,” not “winner.”

- **The billing pilot does not cleanly settle its billing questions.** An ~800-character query only brackets the 512/800 disagreement; it cannot establish the claimed “real query length limit” (`discovery-test-plan.md:21-28`; `discovery-xapi-docs.md:18-25`). Billing dashboard lag, 24-hour deduplication, and changing results also make before/after totals ambiguous (`discovery-xapi-docs.md:67-73`).  
  **Fix:** use a written pilot matrix: one isolated hypothesis per UTC day or uniquely attributable resource set; exact post/user IDs and unique-author count; console timestamp and line item; then bounded 513/1025/4096 length tests only after confirming invalid requests are unbilled.

- **“Duplicate across sources” is insufficient provenance.** The plan records cross-source duplication but not a canonical retrieved universe, within-source repeats, parent/quoted posts fetched by Grok, pagination/meta, response errors, or the actual tool/query parameters (`discovery-test-plan.md:40-42`). This weakens both cost attribution and unique-yield claims.  
  **Fix:** store a private row per retrieval event and a canonical post-ID table with first/last seen source, source-specific ranks, request hash, page/token, claimed versus verified status, and billable fetched-versus-returned counts.

## Low

- **The pilot’s operator test is redundant unless it tests tier access.** `min_likes:`, `min_replies:`, and `-is:reply` are already documented; the unresolved part is pay-per-use acceptance (`discovery-xapi-docs.md:33-57,132-142`).  
  **Fix:** combine it with the first K query and state the sole hypothesis as “accepted on this account/tier.”

- **“Every field” is not a free completeness choice.** Author expansions may trigger $0.010 user reads and are explicitly unresolved (`discovery-test-plan.md:40`; `discovery-xapi-docs.md:101-113`).  
  **Fix:** make author enrichment a separately priced optional arm, sampled only after it proves decision-relevant.

What is sound:

- The jobs are distinct and correctly prioritize freshness for reply opportunities.
- A stop-and-review boundary after the pilot is sensible.
- Checking Grok-named posts by X ID is essential and matches the existing fail-closed pattern (`scripts/x_read.py:10-14`).
- Recording age, duplicates, invention rate, and source-specific cost is the right outcome frame once collection is normalized.

Codex session ID: 01a0dc27-6a5a-75e1-a559-49127b94efe0
Resume in Codex: codex resume 01a0dc27-6a5a-75e1-a559-49127b94efe0
