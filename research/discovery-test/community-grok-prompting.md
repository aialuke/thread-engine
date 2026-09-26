# Community and developer sources on prompting Grok for X search

**Scope:** web research only — no paid API calls, no Grok or X API calls made from this session. Looked beyond xAI's own docs (already covered in `docs-grok.md` and `docs-grok-prompting.md`, which found **no official prompting guidance exists**) at xAI's GitHub, the xai-sdk and Grok Build CLI repos and their issues, third-party MCP servers that wrap `x_search`, developer blog posts, a security researcher's wire-level analysis of the Grok Build CLI, and search-engine snippets of Reddit/Hacker News/X-developer-forum threads (this session cannot read X or Reddit/HN pages that require a live session; where a search snippet is the only thing reachable, that is noted). No files opened other than this folder's existing `.md` files for context; `loop/followers/`, `ledger/raw/api/` and `loop/inbox/` were not touched.

**Headline: still no one has published a tested "how to prompt Grok's `x_search` well" guide.** What exists instead is (1) one plain-English example prompt from a working script, (2) real developers' cost logs from the pricing change, and (3) one serious CLI security finding that bears directly on the plan's "run from a clean folder" rule. Nothing found here shows semantic search being deliberately triggered by wording, and nothing shows reasoning effort changing search depth — both remain untested, same as the docs-only pass found.

---

## 1. A real example prompt (developer with evidence)

**Source:** [Building a Python Tool to Fetch X (Twitter) Threads: Overcoming API Hurdles with xAI's Grok](https://rodtrent.substack.com/p/building-a-python-tool-to-fetch-x) — Rod Trent, published 9 Dec 2025. **Reliability: developer with evidence** (working script shown, using `xai_sdk`, `model="grok-4-fast"`). **Possibly stale** — predates the 21 Sep 2026 pricing change and the current CLI/model lineup, so treat the model name and cost assumptions as outdated, but the prompting pattern itself is still the clearest example found.

Verbatim system prompt used to drive `x_search`:

> "You are a helpful assistant that fetches the latest X (Twitter) threads on a given topic. Use the x_search tool to find recent posts that start threads (non-replies)."

Notes:
- It names the tool generically (`x_search`), not the internal functions our own docs pass found (`x_keyword_search`/`x_semantic_search`/`x_user_search`/`x_thread_fetch`) — consistent with the docs finding that those four are Grok's own internal choice, not something a caller names directly.
- It states the desired *behaviour* in plain English ("posts that start threads (non-replies)") rather than a query syntax, and reports this worked well enough to ship a tool on.
- The author's stated reason for using Grok instead of the X API directly was avoiding X API rate limits (429s on the free tier) — a "why Grok" reason, not a search-quality claim.
- No documented failure modes (invented posts, stale data) in this piece — the author didn't report checking for them.

**xAI's own SDK example** (already in `docs-grok.md`'s territory, repeated here because it's the only other example prompt found anywhere): the TypeScript doc snippet at `docs.x.ai/developers/tools/x-search` uses the prompt `"What are people saying about xAI on X?"` with `xai.tools.xSearch()` and no extra parameters — an illustration of syntax, not a tested "best" prompt. **Reliability: official**, but explicitly not prompting guidance (confirms the existing docs-pass finding, doesn't add to it).

## 2. Failure mode found nowhere in official docs: the "degraded" answer

**Source:** [Hermes Agent docs — X (Twitter) Search](https://hermes-agent.nousresearch.com/docs/user-guide/features/x-search) — Nous Research, no date shown on the page (fetched today). **Reliability: developer with evidence** — this describes Hermes Agent's own wrapper around `x_search`, not an xAI-documented API field; the page cites xAI's docs generally but not for this specific behaviour, so treat "degraded" as this team's own detection logic layered on top of `x_search`, not a guaranteed field in xAI's raw response.

Verbatim:

> "`degraded` — `true` when any narrowing filter (`allowed_x_handles`, `excluded_x_handles`, `from_date`, `to_date`) was set AND both citation channels came back empty."

And the consequence, in a WebSearch snippet of the same page:

> "xAI's X index returned no matching posts but Grok still produced a synthesized answer from its own training data. The answer is unsourced — do not treat it as a real X result."

This is a concrete, named mechanism for exactly the plan's G3 "invented rate": when a narrowing filter (date range, handle allow/deny list) returns nothing, Grok can still answer fluently from its training data instead of saying "no results." **This directly matters for the pilot (P1/P2/P5 use filters like `min_likes:`/`min_replies:`, and the idea cards use date windows)** — if the harness ever adds `from_date`/`to_date` or handle filters to a Grok arm (it currently doesn't; those are X-API-only filters in the plan), a narrow window with zero real matches is a plausible trigger for invented posts, distinct from ordinary hallucination.

Same page, on a second failure mode:

> "Some active accounts intermittently fail to surface in `x_search` even when they post regularly. Retry after a few minutes, or use the `xurl` skill for direct X API reads when you need an exact handle's timeline."

This is an anecdote from one team's troubleshooting notes, not a measured rate — worth testing live (does a retry actually change results?) rather than trusting outright.

## 3. Pricing changed 21 Sep 2026, and real teams already hit it (developer with evidence, current)

This is the single most load-bearing finding for the plan's budget, and it sits right at the edge of what `docs-grok.md` already covered (that file confirmed the official pricing page itself: $5/1k posts fetched, $10/1k profiles, "not de-duplicated," effective 21 Sep 2026). What the docs pass couldn't show is what actually happens to a real workload — three independent small projects hit the change within days and published their numbers:

- **[miyaryo1212/trend-system issue #8](https://github.com/miyaryo1212/trend-system/issues/8)**, miyaryo1212, 24 Sep 2026. **Reliability: developer with evidence, current.** Over 7 days (18–24 Sep): 335 search calls, 1,000 posts fetched, total cost $9.15, with posts fetched alone $5.19 — "over half of costs" — and costs "sharply increasing after 9/23" (i.e., once the new billing started). Root cause named explicitly: **duplicate posts aren't de-duplicated, so re-fetching the same post across searches bills every time** — the same fact `docs-grok.md` found on the pricing page, now confirmed by an actual bill.
- **[miyaryo1212/trend-system PR #9](https://github.com/miyaryo1212/trend-system/pull/9)**, same author, 24 Sep 2026. The fix: capped `x_search` to **one call per search with a 6-post maximum**, prioritised which topics get searched first, and logged calls/posts/cost per run. Before: "2–3 searches and 10–20 posts per feature (~$0.10/feature)." After: "~$0.039/feature" — **about a 60% cost cut from constraining the prompt/parameters alone**, no change to what was being searched for.
- **[Booyaka101/grokscope PR #19](https://github.com/Booyaka101/grokscope/pull/19)**, Booyaka101, 25 Sep 2026. Added cost visibility by reading `usage.server_side_tool_usage_details.x_posts_fetched` / `x_users_fetched` straight out of the API response and printing e.g. `"X Search 184 posts, 3 profiles (~$0.95)"` per call. Confirms the plan's own P0/P7 instinct to log fetched-vs-shown counts — this is exactly the field the plan should read for G4, and it's a documented, working field name to read from the response, not a guess.
- **[RuntimeWire: "xAI is changing the economics of X Search"](https://runtimewire.com/article/xai-is-changing-the-economics-of-x-search-runtimewire-was-built-for-a-narrower-r)**, Ryan Merket, 10 Sep 2026 (published ahead of the 21 Sep cutover, describing the announced change). **Reliability: developer with evidence.** Worked cost examples: 20 posts = $0.10, 100 posts = $0.50, 1,000 posts = $5.00 (matches the official rate). Strategic takeaway, verbatim-paraphrased: the new model "puts a direct price on breadth" — open-ended, exploratory search got much more expensive relative to narrow, targeted search, because cost now scales with what's *retrieved*, not with how many calls are made.

**Practice with the most support:** tell Grok explicitly how many posts to return and to search once, not "search X for relevant posts" with no ceiling. Every real cost-control fix found here was a hard cap on posts-per-call and calls-per-topic, not a cleverer query. This is a testable, cheap thing to add to the plan's G-steered/G-free/G-hinted arms as a **shared constraint across all three** (e.g. "fetch at most 20 posts total") rather than something that should vary between arms — otherwise a difference in results between arms could just be a difference in how many posts each one happened to pull, not prompting style.

## 4. Grok Build CLI: a security finding that bears directly on the plan's isolation rule

**Source:** [cereblab's wire-level analysis](https://gist.github.com/cereblab/dc9a40bc26120f4540e4e09b75ffb547) (gist, 12–13 Jul 2026) and its [reproduction repo](https://github.com/cereblab/grok-build-exfil-repro), corroborated independently by [The Hacker News](https://thehackernews.com/2026/07/grok-build-uploads-entire-git.html), [TheNextWeb](https://thenextweb.com/news/grok-build-uploaded-entire-git-repositories-secrets), and [Tech Times](https://www.techtimes.com/articles/320671/20260716/grok-build-open-sourced-after-covert-upload-code-exfiltrate-repos-stays.htm). **Reliability: developer with evidence, corroborated by multiple independent outlets** — this is the strongest-sourced finding in this file, though it concerns Grok Build CLI's file-handling, not `x_search` prompting per se.

Findings, on Grok Build CLI **version 0.2.93** (mitmproxy capture): on a 12 GB test repo, model-turn traffic (`/v1/responses`) was about 192 KB, while a separate storage channel (`/v1/storage`) uploaded **5.10 GiB of the whole tracked repo plus full git history** — about 27,800× more data than the task needed — to a `grok-code-session-traces` Google Cloud Storage bucket controlled by xAI. Files the CLI was explicitly told not to read (a `deny` rule, and a canary `.env` with fake secrets) were still shipped, because **the upload channel packages the git working tree independent of what the model actually read** — a `deny` rule blocks the model from reading a file, not from the file leaving the machine in the repo bundle. xAI's response, per the same reporting: disabled the upload path server-side and open-sourced the CLI within 48 hours (15 Jul 2026), added a `disable_codebase_upload` config option, and Musk stated (on X, not independently verified) that uploaded data would be deleted.

**Why this matters for the plan:** the plan already says to "run every Grok arm from a clean folder outside the repo," reasoning about skill/`AGENTS.md` contamination (the `format-tool-swap` skill nearly matching Demand idea 1). This finding gives a second, independent, harder reason for that same rule: as recently as July 2026 the CLI shipped an entire working tree — commit history and any secret-bearing files included, regardless of read permissions — to xAI's own cloud storage. **Two open questions this doesn't answer, worth testing before the pilot:** (1) whether the patch (server-side disable + `disable_codebase_upload`) is still in effect on the CLI version this project actually has (`grok 1.0.40`, per `repo-grok-setup-audit.md` — over a year of version numbers past 0.2.93, so likely patched, but not confirmed by any source found here); (2) the plan's own step of running one arm *from inside the repo* to compare tool-call logs against a clean folder would, if the old behaviour ever recurred, upload this repo's `.env`-equivalents and git history — worth checking there is no `.env` or credential file sitting in the repo working tree before that comparison run, not just relying on the patch having held.

## 5. What's still not shown anywhere (confirms the docs-only pass, doesn't add to it)

- **No source, official or community, shows a wording that reliably triggers semantic over keyword search.** Every blog/guide found (ContextBolt, APIYI, tryprofound, datastudios.org) restates the same four-capability list (keyword, semantic, user, thread) from xAI's own page without ever describing how to steer between them. The plan's G-hinted arm ("search by meaning, not just keywords; try several phrasings") remains genuinely untested — no one has published trying it.
- **No source shows reasoning effort or model choice changing search depth or tool-call count.** Same conclusion as `docs-grok-prompting.md`'s §2: nothing beyond the one documentation phrase about low effort suiting "simple tool calling."
- **X's own native search (not Grok's `x_search`) is reported broken/shallow** — a WebSearch snippet attributes to Ethan Mollick (via an X post, unverifiable directly from this session) a complaint that X's built-in search "doesn't work at all anymore" and he now goes to Grok for every search. **Reliability: anecdote, unverified, tangential** — this is about X's own search box, not the `x_search` API tool, but it's the closest thing found to an independent "why use Grok for X search at all" data point, and it lines up with the plan's own premise.
- **X API vs. `x_search` comparisons found are all "cost-efficiency" marketing framing** (e.g. `grok-x-insights-mcp`'s README: "powered by Grok's live search capabilities instead of the expensive X API"), never an accuracy or freshness comparison. No source measures whether `x_search`-found posts are as real/fresh as X-API-found posts for the same query — which is exactly what the plan's own Stage 1–3 scoring is set up to measure, because nobody else has published it.

---

## Summary for the operator (10 lines)

1. No one — official or community — has published tested guidance on wording a prompt to trigger Grok's semantic vs. keyword X search; the plan's G-free/G-hinted arms are still genuinely first-of-a-kind tests.
2. The one real example prompt found (Rod Trent, Dec 2025) just states the goal in plain English and names `x_search` generically — no query syntax, no internal function names.
3. xAI changed `x_search` billing on 21 Sep 2026 to $5/1k posts + $10/1k profiles fetched, not de-duplicated; three independent small projects hit real bill spikes within days and confirmed this by their own logs.
4. The strongest, most-supported prompting practice found anywhere: cap posts-per-call and calls-per-topic explicitly in the prompt/parameters — one team cut cost ~60% doing only that, no query changes.
5. `usage.server_side_tool_usage_details.x_posts_fetched` / `x_users_fetched` is a real, working response field to log for G4 (fetched vs. shown) — confirmed by a shipped tool reading it, not just the pricing page.
6. A documented failure mode (from Nous Research's Hermes Agent, not xAI): when a narrowing filter returns zero real posts, Grok can still answer fluently from training data — a named, plausible mechanism for invented posts, worth testing if any Grok arm ever adds date/handle filters.
7. Some real, active accounts reportedly drop out of `x_search` intermittently (one team's anecdote) — worth a live retry test, not yet evidence of a rate.
8. A corroborated, multi-outlet security finding (Jul 2026, CLI v0.2.93): Grok Build CLI uploaded entire repos plus git history to xAI's cloud regardless of read permissions; patched within 48 hours, but not confirmed fixed on the CLI version this project runs (1.0.40) — supports the plan's "clean folder" rule with a sharper reason, and flags the in-repo comparison run as worth a credential check first.
9. Nothing found shows reasoning effort or model choice changing how much Grok searches — same gap the docs-only pass already found.
10. Contradicts nothing structural in `plan.md`; it strengthens the case for the isolation rule already there and gives P7/Stage-1 two new, cheap things to log (fetched-post counts from the real field name, and whether any arm's answer looks unsourced/degraded).
