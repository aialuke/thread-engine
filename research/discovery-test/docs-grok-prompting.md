# Grok prompting for X search, and the Grok Build CLI's search-relevant options

**Scope:** docs-only, no paid calls, no live Grok/X-API runs. Fetched today (26 Sep 2026) from docs.x.ai and x.ai (browser/WebFetch; some via web-search snippets marked accordingly), plus one local, free command: `grok --help` and its subcommand help (no prompt was sent, no search ran). Answers plan.md's G6 ("Docs step... Record in facts.md as G6"). Builds on `research/discovery-test/docs-grok.md`, which already covers the `x_search` tool's parameters, billing, and the "outputs aren't returned as structured data" fact in depth — this file does not repeat that detail except where it bears on prompting, and instead adds: (1) whether xAI publishes any prompting/best-practice guidance for X search, and (2) the Grok Build CLI's actual flags, checked by running the CLI's own `--help`.

No files opened other than `plan.md` and `docs-grok.md` for context. `loop/followers/`, `ledger/raw/api/`, `loop/inbox/` were not touched.

---

## 1. xAI prompting guidance for X search

**Finding: none exists.** Every page that could plausibly hold it was fetched and checked specifically for prompting language (phrasing, tool naming, semantic-vs-keyword triggers, date ranges, handles, result counts, multiple searches, effort/depth):

| Page | URL | Prompting guidance found |
|---|---|---|
| X Search | https://docs.x.ai/developers/tools/x-search | None. Only the parameter reference (`allowed_x_handles`/`excluded_x_handles`, `from_date`/`to_date`, `enable_image_understanding`, `enable_video_understanding`) — already documented in `docs-grok.md` §1. |
| Tools overview | https://docs.x.ai/docs/guides/tools/overview | None. "The content focuses on tool types, pricing, implementation examples, and next steps" — no strategic prompting language, no advice on tool calls per turn or `max_turns` interaction. |
| Search tools guide | https://docs.x.ai/docs/guides/tools/search-tools | None. Configuration only (e.g. `allowed_domains`/`excluded_domains` for web search); no phrasing or semantic-vs-keyword guidance. |
| Web Search | https://docs.x.ai/developers/tools/web-search and https://docs.x.ai/docs/guides/live-search | None. Only example queries shown as usage illustrations ("What is xAI?", "Show me images of Starship on the launch pad") — not phrasing advice. No page-updated date visible on the live-search page. |
| Tool Usage Details | https://docs.x.ai/developers/tools/tool-usage-details | Already covered in `docs-grok.md`: this is a billing/output-shape page, not a prompting page. |

So: **there is no xAI documentation saying whether to name `x_keyword_search`/`x_semantic_search`/`x_user_search`/`x_thread_fetch` explicitly, how to word a request to trigger semantic over keyword search, or how many searches per request is normal.** Grok choosing among the four internally (as `docs-grok.md` already established) is not addressed from the prompting side anywhere in xAI's docs — this is a documentation gap, not something this pass missed.

**One correction to a stray web-search snippet, checked and ruled out:** a `WebSearch` snippet claimed a `"retrieval_mode": {"type": "keyword"|"semantic"}` parameter existed for X search. Checked directly: `retrieval_mode` (values include `"hybrid"`) belongs to the **Collections Search** tool (`https://docs.x.ai/developers/tools/collections-search`, for searching a customer's own uploaded documents/knowledge base), not X Search. **X Search has no `retrieval_mode` or equivalent mode switch** — this confirms `docs-grok.md`'s existing finding that there is no documented `mode` parameter for X search.

## 2. Reasoning effort and tool/search depth

`https://docs.x.ai/docs/guides/reasoning` (fetched today):

- `reasoning_effort` takes `"low"`, `"medium"`, `"high"` (default), `"xhigh"`.
- grok-4.7 and grok-4.6 support all four; grok-4.5 supports only low/medium/high ("treats `xhigh` as `high`"); grok-4.20-multi-agent's `reasoning.effort` controls **agent count**, not reasoning depth, for that model specifically.
- Verbatim, on low effort: **"Uses some reasoning tokens, but still fast"**, described as optimal for **"Latency-sensitive agentic use and simple tool calling."**
- **No page states that `reasoning_effort` changes how many X-search calls Grok makes, how many posts it fetches, or whether it prefers keyword over semantic search.** The "simple tool calling" framing for low effort is the only hint in official docs that effort level and tool-use thoroughness are related at all, and it is a hint, not a stated mechanism — UNVERIFIED beyond that one phrase.
- Separately, `presencePenalty`, `frequencyPenalty` and `stop` are explicitly disallowed with reasoning models — not search-relevant, noted only because it appeared on the same page.

**Net: nothing in xAI's docs says structured/JSON-schema output or low effort caps tool use or search depth.** `docs-grok.md` already established that structured output (this repo's `x_read.py` JSON-schema pattern) is a prompting convention layered on top of the model's free-text answer, not a documented tool-result schema — there is no stated interaction between `--json-schema` and how much X search happens before that JSON is produced.

## 3. The Grok Build CLI's own options (from `grok --help`, run locally, no prompt sent)

CLI version installed here: `grok 1.0.40 (eb1a2256660d)`, at `/Applications/cmux.app/Contents/Resources/bin/grok`.

Flags relevant to this test, verbatim from `grok --help`:

| Flag | What it does |
|---|---|
| `-m, --model <MODEL>` | Model ID to use |
| `--reasoning-effort <EFFORT>` (alias `--effort`) | "Reasoning effort for reasoning models" |
| `--max-turns <N>` | "Maximum number of agent turns" |
| `--json-schema <SCHEMA>` | "JSON Schema for structured output. When set, the model is constrained to produce JSON matching this schema. Implies `--output-format json`." |
| `--output-format <FORMAT>` | `plain` (default), `json`, `streaming-json`, `streaming-messages-json` |
| `--sandbox <PROFILE>` | "Sandbox profile for filesystem and network access" (env `GROK_SANDBOX`) — this is what `scripts/grok_read.py` sets to `read-only` per `docs-grok.md`'s existing note |
| `--tools <TOOLS>` | "Built-in tools to allow (comma-separated)" — **no enumerated tool-name list appears in `--help` itself**; it does not spell out `x_search`/`x_keyword_search` etc. as an allowed value |
| `--disallowed-tools <TOOLS>` | Built-in tools to remove (comma-separated) — same caveat, no enumerated names shown |
| `--disable-web-search` | "Disable web search and web fetch tools" — **named for web search specifically; nothing named `--disable-x-search` or similar exists in the top-level help.** Whether this flag also gates `x_search` (X Search is a distinct, separate tool per `docs-grok.md`) is UNVERIFIED from `--help` text alone — the flag's own wording only claims "web search and web fetch." |
| `--allow` / `--deny` (aliases `--allowedTools`/`--disallowedTools`) | Permission allow/deny rules — generic permission syntax, not search-specific |
| `-p, --single <PROMPT>` | Single-turn prompt, prints to stdout and exits (what a scripted/headless read would use) |
| `--verbatim` | "Send the prompt exactly as given" — relevant to the steered/free/hinted arms: without this flag, the CLI may be wrapping or modifying the prompt before sending it, which matters for reproducing exact wording across arms |
| `--rules <RULES>` | "Extra rules to append to the system prompt" |
| `--system-prompt-override <PROMPT>` (alias `--system-prompt`) | Replaces the agent's system prompt entirely |

`grok agent headless --help` and `grok agent stdio --help` (the two headless-run subcommands) expose no additional search- or model-specific flags beyond what's inherited from the top-level agent options (`-m/--model`, `--reasoning-effort`, `--always-approve`, debug flags). Neither subcommand's help text mentions X search, `x_search`, or tool-specific configuration.

**No CLI flag enables/disables/configures X Search specifically.** The only search-adjacent flag in the entire `--help` tree is `--disable-web-search`, whose own description names web search and web fetch, not X search.

## 4. Which models the CLI offers, and coding vs. search fit

Running `grok models` locally (no auth, no network search — just prints the CLI's built-in model list) returned:

```
You are not authenticated.

Default model: grok-4.6

Available models:
  - grok-4.7
  - grok-4.7-build-fast
  * grok-4.6 (default)
  - grok-4.5
```

**This list was captured unauthenticated** (this session has no login/API key), so it may not be the full list the operator's subscription unlocks — flagged as a limitation, not a docs fact. It does **not** list `grok-build-0.1` (the model `docs-grok.md` found documented at `https://docs.x.ai/developers/models/grok-build-0.1` as the CLI's default coding model) or `grok-4.3`. `grok-4.7-build-fast` is very likely the CLI-facing name for the "Grok 4.7 Fast (Cursor and Grok Build only)" product `docs-grok.md` already found priced on `docs.x.ai/developers/pricing` — same "Build" naming pattern, same fast/coding framing — but the two names have not been matched by any single doc page that uses both terms together, so treat that mapping as a reasonable inference, not a confirmed fact.

**Coding vs. search fit, per docs.x.ai:**
- `grok-build-0.1` (https://docs.x.ai/developers/models/grok-build-0.1): described only as **"an intelligent coding model for agentic software, engineering, and workflow tasks."** No mention of search, X Search, or research use anywhere on that page.
- `https://docs.x.ai/build/overview` (the Grok Build product page) calls Grok Build itself **"a powerful and extensible coding agent"** — the product's own framing is coding-first, not research-first. The page does not compare models for search/research tasks and does not mention X Search or web search being enabled/configured from the CLI at all.
- No page found anywhere that recommends a specific model **for X search or research** over another. **UNVERIFIED / not documented:** whether grok-4.7, grok-4.6 or grok-4.5 differ in X-search quality, recall, or tool-choice behavior. The only documented differentiator across models found this session is reasoning-effort support (§2) and general per-token pricing/rate-limit tiers (already in `docs-grok.md` §3–4).

## Summary (10 lines)

1. xAI publishes no prompting guidance anywhere for X search: checked x-search, tools/overview, search-tools, web-search and live-search pages — all give parameters/pricing/example queries, never phrasing advice, never whether to name `x_keyword_search`/`x_semantic_search`/`x_user_search`/`x_thread_fetch` explicitly or let Grok choose.
2. A web-search snippet claiming a `retrieval_mode` (keyword/semantic) switch for X search was checked and ruled out: that parameter belongs to the separate Collections Search tool, not X Search, which has no documented mode switch.
3. `reasoning_effort` (`low`/`medium`/`high`/`xhigh`, high default) is documented only generically; the sole search-adjacent hint is low effort's description as "optimal for latency-sensitive agentic use and simple tool calling" — no doc states effort changes X-search call count, post yield, or keyword-vs-semantic choice.
4. No doc states that JSON-schema-constrained output (`--json-schema`) reduces tool use or search depth before the JSON is produced.
5. The Grok Build CLI (`grok --help`, v1.0.40, checked locally, no prompt sent) exposes `-m/--model`, `--reasoning-effort`/`--effort`, `--max-turns`, `--json-schema`, `--sandbox`, `--tools`/`--disallowed-tools`, `--verbatim`, and `--rules`/`--system-prompt-override`.
6. The only search-related toggle in the whole CLI help tree is `--disable-web-search` ("Disable web search and web fetch tools"); its own wording names web search, not X search, so whether it also gates X Search is UNVERIFIED.
7. `--tools`/`--disallowed-tools` accept "comma-separated" built-in tool names but `--help` does not enumerate what those names are (no confirmation `x_search` is a nameable value from `--help` text alone).
8. `grok models`, run unauthenticated, listed only `grok-4.7`, `grok-4.7-build-fast`, `grok-4.6` (default) and `grok-4.5` — no `grok-build-0.1`, contradicting the assumption in `docs-grok.md` that the CLI defaults to `grok-build-0.1`; this needs re-checking once logged in with the operator's subscription (this session ran unauthenticated by design — no paid calls).
9. `grok-build-0.1` is documented only as a coding model ("agentic software, engineering, and workflow tasks"); no docs.x.ai page recommends any specific model for X-search/research quality over another.
10. Net: every parameter in plan.md's prompting question (semantic vs keyword phrasing, date ranges, handles, result counts, multi-search, effort/depth) is either a plain API parameter with no prompting advice attached (handles, dates — see `docs-grok.md`) or entirely undocumented (semantic-triggering phrasing, result counts, effort-vs-depth) — the pilot's G-steered/G-free/G-hinted arms are the only way to learn what actually works.

## Recommendations for the three prompt arms and CLI flags

**Prompt arms (plan.md P7):**
- **G-steered:** keep today's exact-keyword-query style (`scripts/x_read.py`'s current pattern), but run it with `--verbatim` so the CLI is confirmed not to be rewording the prompt before sending it — otherwise "steered" isn't actually testing what it claims to.
- **G-free:** give the idea in plain words with no tool names and no search-strategy hints at all, letting Grok pick among the four internal functions. Since nothing in the docs says how it decides, this arm is the only source of evidence for G2.
- **G-hinted:** add "search by meaning, not just keywords; try several phrasings" as planned. Since `retrieval_mode` is not a real X-search parameter, this framing can only work by influencing the model's choice of internal function (`x_semantic_search` vs `x_keyword_search`), not by setting a documented switch — worth stating in `facts.md` so a null result doesn't look like a broken hint.
- On all three arms, avoid `--json-schema` for the arm-comparison pass itself (or run it both ways once): since no doc rules out structured output affecting tool-use depth, and this pilot is specifically trying to see how much Grok searches, adding a schema constraint introduces a second undocumented variable at the same time as the arm variable. If budget allows, run one arm with and without `--json-schema` to isolate that effect before Stage 1 locks in a format.

**CLI flags to fix vs. vary:**
- Fix across all arms: `--sandbox read-only` (as `grok_read.py` already does), `--output-format json` (implied automatically once `--json-schema` is set, or set explicitly), `-p/--single` for a scripted one-shot call.
- Vary deliberately: `--reasoning-effort low` vs `--reasoning-effort high` on one idea, as plan.md already specifies for G6 — given low effort's documented framing as "simple tool calling," the a priori expectation is fewer/shallower X-search calls at low effort, but this is only a hint from the docs, not a stated fact, so treat the pilot's actual tool-call counts (from the CLI envelope) as the real answer, not the docs quote.
- Pick a model explicitly with `-m`/`--model` rather than relying on the CLI default: log in with the operator's subscription first and re-run `grok models` (free, local) to see the authenticated list before choosing, since the unauthenticated list here (§4) may not match what the subscription actually offers, and `docs-grok.md`'s assumption that the default is `grok-build-0.1` is now in question.
- Do not rely on `--disable-web-search` to isolate X-search-only behavior — its own description only claims to cover web search and web fetch, not X search, so leaving it off (default) is the safer choice unless a live test confirms it also disables `x_search`.
- Log the exact flags used per arm in `grok.jsonl` (plan.md already requires the full CLI envelope), including whether `--verbatim` was set, since that affects whether "G-steered" is testing the intended exact wording.
