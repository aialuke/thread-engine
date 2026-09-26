# Grok X-search vs X API keyword search — docs-only discovery

**Scope:** official xAI docs only (docs.x.ai, x.ai), fetched today (26 Sep 2026). No xAI/X API calls, no Grok CLI runs, no Keychain reads made. Private folders (`loop/followers/`, `ledger/raw/api/`, `loop/inbox/`) not opened. Builds on `research/layer-2-x-data-tiers.md` §2.4, which already covered pricing and terms at a summary level; this file re-verifies those and fills the parameter/response-shape/rate-limit gaps that §2.4 left open.

**How each page was reached:** docs.x.ai pages fetched directly (some via WebFetch, some via browser — `.md` raw endpoints 404'd, so pages were read as rendered HTML/text). `x.ai/legal/terms-of-service-enterprise` fetched directly via WebFetch returned 403; read successfully in the browser (matches the prior research note that this page blocks bots). Third-party pricing blogs surfaced by web search are **not used** as sources here except where explicitly marked "(third-party, UNVERIFIED)".

---

## 1. The X search tools — what they are, parameters, response fields

**Key finding: there is no separate documented tool per function.** `x_keyword_search`, `x_semantic_search`, `x_user_search`, `x_thread_fetch` are internal function names the model can call; the *developer-facing* tool is a single `x_search` (or `X Search`) tool with one shared parameter set. xAI's docs do not expose per-function parameters, and Grok itself chooses which of the four to invoke and with what arguments.

- Tool Usage Details page: "`SERVER_SIDE_TOOL_X_SEARCH` … `x_user_search, x_keyword_search, x_semantic_search, x_thread_fetch`" — this is the only place the four names appear, and it's a billing-category → function-name mapping table, not a parameter reference.
  https://docs.x.ai/developers/tools/tool-usage-details
- X Search overview page: "The X Search tool enables Grok to perform keyword search, semantic search, user search, and thread fetch on X (formerly Twitter)."
  https://docs.x.ai/developers/tools/x-search

**Documented parameters (apply to the whole `x_search` tool, not per-function):**

| Parameter | Description (verbatim) |
|---|---|
| `allowed_x_handles` | "Only consider posts from specific X handles (max 20)" |
| `excluded_x_handles` | "Exclude posts from specific X handles (max 20)" |
| `from_date` | "Start date for search range (ISO8601 format)" |
| `to_date` | "End date for search range (ISO8601 format)" |
| `enable_image_understanding` | "Enable analysis of images in posts" |
| `enable_video_understanding` | "Enable analysis of videos in posts" |

"`allowed_x_handles` cannot be set together with `excluded_x_handles` in the same request." Both are capped at 20 handles. Date range: "restrict the date range of search data used by specifying `from_date` and `to_date`. This limits the data to the period from `from_date` to `to_date`, including both dates." ISO8601, e.g. `"YYYY-MM-DD"`.
Source: https://docs.x.ai/developers/tools/x-search

**Not documented anywhere on docs.x.ai (checked x-search, tool-usage-details, citations, tools/overview, tools/advanced-usage, tools/web-search):**
- No `mode` parameter (no "Latest"/"Top" distinction — that terminology appears only in this repo's own `scripts/x_read.py` prompt text, not in xAI's docs).
- No `limit` / result-count parameter.
- No per-post response schema. There is **no documented field list** (text, author, timestamp, engagement numbers, ids) for what a search or thread-fetch call returns.

**Why there's no field list: results aren't returned to the caller as structured data at all.** From Tool Usage Details (verbatim): "Only the tool call invocations are shown — server-side tool call outputs are not returned in the API response. The agent uses these outputs internally to formulate its final response." So the caller sees: (a) the tool-call *arguments* Grok chose (via `tool_calls` / streaming), (b) item **counts** (`x_posts_fetched`, `x_users_fetched`), (c) **citations** (a list of X URLs, e.g. `https://x.com/i/status/…`, `https://x.com/i/user/…`), and (d) the model's own generated text. There is no API-level structured post object (no id/author/text/metrics fields returned directly) — this repo's `x_read.py` pattern of asking Grok to emit a JSON schema with those fields is a prompting convention on top of the model's text output, not a documented tool-result schema.
https://docs.x.ai/developers/tools/tool-usage-details

`x_thread_fetch`: no dedicated parameter page exists; it's inferred to take a post id (used as `x_search()`-style invocation by the model, not something the developer parameterizes directly beyond the shared allow/exclude/date filters).

---

## 2. `x_semantic_search` — how it's documented

**UNVERIFIED / not documented.** Across every X-search-related page fetched (x-search, tool-usage-details, citations, tools/overview, tools/advanced-usage), xAI gives **zero description of how semantic search matches content, its index window, recency, or any quality/limits notes specific to it.** The only place "semantic search" appears is the one-line tool description ("keyword search, semantic search, user search, and thread fetch") and the billing-category function list. No page says what embeddings or ranking it uses, how far back its index reaches, or how its recall/precision compares to keyword search. This is a genuine documentation gap, not something this discovery missed — a live test is the only way to learn this (see open questions).

---

## 3. Pricing

All confirmed live, https://docs.x.ai/developers/pricing (page says "Last updated: September 21, 2026") and https://docs.x.ai/developers/tools/x-search / tool-usage-details (same effective date referenced):

- **Per item:** "$5 / 1k posts" and "$10 / 1k profiles." Verbatim: "X Search is billed per item fetched rather than per call: every post returned by a search or thread fetch, including parent and quoted posts, counts toward the post rate, and every profile returned by a user search counts toward the profile rate."
- **Token costs still apply on top** ("Requests which make use of xAI provided server-side tools are priced based on two components: token usage and server-side tool invocations"). Per-1M-token rates (short / long context, input / cached-input / output):
  - grok-4.7: $2.00 / $0.50 / $6.00 (short); $4.00 / $1.00 / $12.00 (long, ≥200k tokens)
  - grok-4.3: $1.25 / $0.20 / $2.50 (short); $2.50 / $0.40 / $5.00 (long, ≥200k)
  - grok-build-0.1 (the model Grok Build's CLI defaults to): $1.00 / $0.20 / $2.00 (short, ≤256k context); $2.00 / $0.40 / $4.00 (long)
  - US regional endpoint (`us.api.x.ai`) bills all of the above at a 1.1x premium.
- **De-duplication: confirmed no.** Verbatim (x-search page): "Both counts accumulate over every X Search call in the request and are **not de-duplicated; a post returned by two searches counts twice**." Same wording on the pricing page.
- **Usage reporting:** counts surface under `usage.server_side_tool_usage_details.x_posts_fetched` / `x_users_fetched`, effective "as of September 21, 2026" (billed by item, not by call, as of that date — implying this billing model itself is fairly recent).
- **Grok Build CLI vs API billing — UNVERIFIED on official docs.** Confirmed facts:
  - Grok Build's coding model defaults to `grok-build-0.1`, priced as above when called with an `XAI_API_KEY` (https://docs.x.ai/developers/models/grok-build-0.1).
  - The CLI supports two auth paths: "On first launch, Grok opens a browser for authentication. In non-browser environments, use an API key" (https://docs.x.ai/build/overview) — i.e. browser sign-in (implies a consumer subscription) vs. `XAI_API_KEY` (implies per-token API billing), but the docs page doesn't spell out how the browser-auth path is billed.
  - A separate section, "Grok 4.7 Fast pricing (Cursor and Grok Build only)," confirms Grok Build has product-specific pricing/availability outside the general API: "Grok 4.7 Fast is the same Grok 4.7 model served on faster infrastructure, at twice the standard token rates. It is available only through Cursor and Grok Build; it is not available on the public xAI API, and **Grok Build's free tier does not include it**." This confirms a "free tier" exists for Grok Build, but the page doesn't price it or say whether X Search item-fetch costs are included in or excluded from that free tier / any subscription allowance.
  - No official page found stating whether X Search's per-post/per-profile fetch cost is billed differently (or pooled into a subscription quota) when run through the Grok Build CLI's subscription-auth path versus the pay-per-use API. **UNVERIFIED — needs a live test or a page not found in this session** (checked: build/overview, build/settings, build/pricing [404], developers/pricing, developers/models/grok-build-0.1).
  - This repo's own `scripts/grok_read.py` runs the CLI headlessly with `--sandbox read-only` and reads `total_cost_usd` from the CLI's own JSON output — i.e. the repo already treats the CLI as reporting a cost, which only makes sense if the CLI's session is on the API-key/pay-per-use billing path, not a flat subscription. That's an inference from the repo's code, not from xAI's docs.
  - Third-party pricing sites (UNVERIFIED, not xAI's own pages) claim Grok Build requires a SuperGrok/X Premium+ subscription or a pay-per-token API key, and that "all Grok products … draw from one shared weekly usage pool." Not confirmed on any docs.x.ai or x.ai page found this session.

---

## 4. Rate limits

https://docs.x.ai/developers/rate-limits (checked live, "Last updated: September 17, 2026"):

- **No X-Search-specific rate limit is documented anywhere.** The rate-limits page states limits only "for text, embedding, and voice models," organized by tier (Tier 0–4 + Enterprise, based on cumulative API spend since 1 Jan 2026) and by model, as **requests per second (RPS)** and **tokens per minute (TPM)** — not by tool or by search-item count.
- For `grok-build-0.1` specifically (the CLI's default model): Tier 0 = 37 RPS / 10M TPM, scaling to Tier 4 = 208 RPS / 85M TPM.
- For `grok-4.7`: Tier 0 = 150 RPS / 50M TPM, up to Tier 4 = 500 RPS / 100M TPM.
- Exceeding any limit → HTTP 429.
- Nothing on this page (or elsewhere found) caps X Search calls-per-minute, posts-fetched-per-minute, or similar separately from the general per-model RPS/TPM caps.

---

## 5. Structured results vs. model text; citation reliability

- **Confirmed: the caller cannot get raw post ids/fields directly from the tool result.** Server-side tool outputs are never returned to the API caller — only tool-call *arguments* (streamed), item *counts*, and *citations* (URLs) are exposed; the actual post content the tool retrieved is consumed internally by the model and only reaches the caller filtered through the model's generated text (or paraphrase). Verbatim, repeated for emphasis: "server-side tool call outputs are not returned in the API response. The agent uses these outputs internally to formulate its final response." (https://docs.x.ai/developers/tools/tool-usage-details)
- **Citations are not a reliable "what was actually used" list.** Verbatim, Citations page: "Note that not every URL in this list will necessarily be directly referenced in the final answer. The agent may examine a source during its research process and determine it is not sufficiently relevant to the user's query, but the URL will still appear in this list for transparency." (https://docs.x.ai/developers/tools/citations)
- Citations come in two forms: the `citations` list (all sources encountered, e.g. `https://x.com/i/status/1975607901571199086`, `https://x.com/i/user/1912644073896206336`) and inline `[[N]](url)` markdown citations with positional `annotations` (start/end character offsets) — but inline citations are opt-in/opt-out depending on SDK, and "enabling inline citations does not guarantee that the model will cite sources on every answer."
- **Net for this repo's design question:** this confirms and sharpens what `research/layer-2-x-data-tiers.md` already inferred from observed invented posts — xAI's own docs state, independent of that observation, that the model's text is not a verified pass-through of tool data, and citations are a "sources encountered" list, not a "facts used" list. `x_read.py`'s pattern of verifying every Grok-returned id against the X API is the only way documented behavior supports trusting the output; there's no structured, checkable tool-result the repo could read instead.

---

## 6. Terms: storage, display, personal data / zero data retention

Read directly from `x.ai/legal/terms-of-service-enterprise` in the browser ("Last Updated: August 14, 2026" — same version the prior research session read).

- **No clause anywhere in this document addresses X content specifically** — nothing about storing, displaying, or passing on X posts/handles returned by X Search. The only relevant general clauses are about "User Content" (Input + Output) broadly.
- **Zero Data Retention (personal data), verbatim:** "Customer represents and warrants that it will not intentionally submit, and will use reasonable efforts to prevent Permitted Users and End Users from submitting any Personal Data to the Services **except through SpaceXAI's ZDR-Enabled API**. Customer acknowledges and agrees that: (i) when using ZDR, only Customer (and not SpaceXAI) will retain or have access to such Personal Data; (ii) as a result, SpaceXAI will lack the information necessary to fulfill many obligations typically imposed on a subprocessor under a data processing agreement; and (iii) Customer is solely responsible for ensuring that all Personal Data is processed exclusively through the ZDR-Enabled API." — This reads as a **hard requirement**, not an option: personal data (which includes other people's X handles/posts under most privacy laws) may only go through the ZDR-Enabled API.
- **Default (non-ZDR) retention:** "All User Content will be automatically and permanently deleted no later than **30 days** after the end of the interaction or session," unless a different period is agreed, required by law, or "reasonably necessary for safety, security, compliance, moderation, abuse prevention, or investigation."
- **Under ZDR:** "User Content will exist in SpaceXAI systems only transiently and solely to the extent required to generate and return the real-time response; SpaceXAI will delete all such User Content … upon the earlier of (a) one hour after completion of the applicable inference request; or (b) delivery of the response; and no logs, backups, persistent copies, or other durable storage containing User Content will thereafter be retained for any purpose, including safety, debugging, or legal compliance." Also: once deleted, "User Content cannot be recovered or produced by SpaceXAI under any circumstances (including subpoenas, regulatory requests, or legal process)."
- **Training:** "SpaceXAI will not use any User Content to train any foundation models, large language models, or other artificial intelligence systems or to develop any new products, services, or features, subject to disclosures to Customer and Customer-controlled user settings." Customer likewise may not use Output "to train any foundation models … except as may be expressly permitted in an Order Form."
- **De-Identified/Aggregated Data:** "Except when Customer elects to use SpaceXAI's Zero Data Retention-enabled APIs … SpaceXAI may create and use, for any lawful purpose, de-identified and/or aggregated data derived from Customer's use of the Services that is irreversibly anonymized … SpaceXAI will own all right, title, and interest in the De-Identified Data." — i.e. non-ZDR use lets xAI build and own aggregate/de-identified data from the customer's traffic; ZDR turns this off too.
- **Third-Party Services clause:** "Third-Party Services are governed by the terms between Customer and the applicable third-party provider" — no specific carve-out for X as a "third-party service" whose content flows through X Search.
- **Privacy/DPA:** if personal data is submitted, xAI "will process such data as a processor on Customer's behalf" under its DPA, which "shall automatically apply." Consistent with the earlier research's reading that the ZDR sentence and the "processor" sentence sit side by side without fully reconciling how personal data sent outside ZDR is handled if it happens anyway — this document doesn't resolve that; it just makes non-ZDR submission of personal data a "material breach."

This matches and sharpens (with full verbatim text, not paraphrase) what `research/layer-2-x-data-tiers.md` §2.4/§2.5 already flagged: **zero data retention reads as a prerequisite for sending other people's X content/handles to xAI, not an optional privacy upgrade.**

---

## Summary (10 lines)

1. xAI docs describe one `x_search` tool, not four separate tools — `x_keyword_search`/`x_semantic_search`/`x_user_search`/`x_thread_fetch` are internal function names sharing one parameter set: `allowed_x_handles`/`excluded_x_handles` (max 20, mutually exclusive), `from_date`/`to_date` (ISO8601), `enable_image_understanding`, `enable_video_understanding`.
2. No documented `mode` (Latest/Top), `limit`, or per-post field schema (id/author/text/time/engagement) exists anywhere in xAI's docs.
3. Server-side tool outputs are never returned to the caller — confirmed verbatim ("server-side tool call outputs are not returned in the API response"); the caller only gets item counts, citations (URLs), and the model's generated text.
4. `x_semantic_search`'s matching method, index window/recency, and quality are undocumented — UNVERIFIED, a genuine gap, not an oversight in this search.
5. Pricing: $5/1k posts fetched, $10/1k profiles, plus normal per-token costs; counts are explicitly "not de-duplicated" ("a post returned by two searches counts twice").
6. Grok Build CLI's default model is `grok-build-0.1` ($1.00/$0.20/$2.00 per 1M tokens short-context); whether X-Search item costs bill differently (or draw from a subscription pool) under the CLI's browser-auth route vs. the API-key route is UNVERIFIED — no official page states it.
7. No X-Search-specific rate limit exists; only general per-model RPS/TPM tiers (e.g. grok-build-0.1: 37 RPS/10M TPM at Tier 0, up to 208/85M at Tier 4).
8. Citations are explicitly not a "what was used" list: the docs warn a cited source "will still appear in this list" even if judged irrelevant and not referenced.
9. xAI's enterprise terms say nothing about X content specifically; the operative clause is general: Personal Data may be submitted "except through SpaceXAI's ZDR-Enabled API" — worded as a required channel, not an option, with 30-day default deletion vs. ≤1-hour transient handling under ZDR.
10. Non-ZDR traffic can become xAI-owned "de-identified and aggregated data" for any lawful purpose; ZDR turns that off too — reinforcing that ZDR is the only clean path for other people's X data.

## Open questions a live test should settle

- **Semantic vs. keyword recall/precision:** run the same query through `x_keyword_search`-style prompting and semantic-style prompting and compare what's found, since none of this is documented.
- **Indexing freshness:** how recent can a semantic-search hit be (minutes? hours?) versus keyword search's apparent near-real-time behavior — undocumented.
- **Invented posts, quantified:** what fraction of returned posts fail the X-API-id verification this repo already applies in `x_read.py` — the existing invented-post observations are anecdotal (three so far); a live test could get a real rate.
- **Grok Build CLI billing path:** does a CLI session authenticated via browser (subscription) bill X-Search item-fetch costs at all, differently, or not (i.e. included in a flat plan)? Does `grok_read.py`'s `total_cost_usd` reading only work because the CLI here runs on an API key, not a subscription login?
- **max_turns interaction with X Search:** how many x_search sub-calls (keyword + semantic + thread fetch combined) typically happen inside one "turn," since item cost scales with fetched posts/profiles, not turns or calls.
- **Thread-fetch scope:** does `x_thread_fetch` return "every post of a fetched thread" (as the pricing note's phrase "every post of a fetched thread" implies) even for very long threads, and is there a documented or practical cap on thread length before cost balloons?
- **Handle-filter behavior with semantic search:** whether `allowed_x_handles`/`excluded_x_handles` and date filters apply identically across keyword/semantic/thread-fetch, or whether one sub-tool ignores them in practice (the docs say the filters apply to "X Search" as a whole, not to each function individually).
- **X API recent search as the alternative:** not part of this xAI-docs-only pass — `research/layer-2-x-data-tiers.md` already covers `docs.x.com` for that side; a joint live test comparing X API keyword search against Grok's `x_search` on the same queries would show the practical tradeoff this document (line: "We're comparing Grok's X search against X API keyword search") is ultimately about.
