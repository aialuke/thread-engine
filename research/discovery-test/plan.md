# Discovery test plan, v3 (after Codex's review and the operator's answers, 26 Sep)

**v3 changes (operator, 26 Sep):** (1) Grok runs through the Grok Build CLI on the operator's subscription, as `scripts/grok_read.py` does; record the model and billing route the CLI reports, and pick the strongest non-coding model the CLI offers if `grok --help` shows a model flag (log which). (2) Every Worth-joining post is re-read about 6 hours after it was found (same UTC day where possible, which should be free: F3) to record whether the conversation grew (replies, likes). (3) Raw data is kept in `research/discovery-test/private/` (gitignored) until the layer 2 decisions are made, at most 4 weeks (delete by 24 Oct 2026). **Amended 27 Sep (operator): kept 180 days, delete by 26 Mar 2027.** (4) **Nothing runs until the operator says go**; the run happens the same day, at whatever time the operator gives the go-ahead; record the time block. The operator tops up X credit before the pilot and reads X's developer console before and after it.

**Scope (operator):** fact-finding and experimental testing of X search, the X API and Grok, not only "which source wins". Every call is logged so the data answers questions we haven't thought of yet. `AGENTS.md`'s "other people's posts only through Grok/x_read" rule is set aside for this test (operator). Codex judges raw post text as returned (operator). The operator manages credit; the X API **checkpoint is $6** of estimated spend.

## Questions this answers

**Facts about X's API** (each a row in `facts.md`: hypothesis, the call that tests it, the answer):
F1 search bills per post returned ($0.005?) · F2 author expansions bill as user reads ($0.010?) · F3 same-day repeats are free · F4 the counts endpoint works on pay-per-use, and its price · F5 the following timeline works with the factory's OAuth 1.0a keys, and whether it's owned ($0.001) or standard · F6 the real query length limit (512 / 1,024 / 4,096) and whether rejected requests bill · F7 `min_likes:`, `min_replies:`, `-is:reply` accepted on this tier · F8 `sort_order` recency vs relevancy: what relevancy favours · F9 how fresh the newest results are (age of newest post found) · F10 the rate-limit headers and remaining quota per endpoint · F11 whether a usage endpoint reports billed items.
**Facts about Grok:** G1 what the CLI envelope contains (tool calls, fetched counts, citations, tokens, cost) · G2 which search functions it chooses when given an idea in plain words · G3 invented and misquoted rates · G4 posts fetched vs posts shown (billing vs yield) · G5 cost per prompt.
**Comparison:** per job and niche, useful posts, useful per dollar, unique useful posts, spam share, freshness.

## Sources

- **K** X API recent search, from queries frozen before collection.
- **G** Grok given the idea in plain words, free to choose its functions; every claimed post checked by id on the X API.
- **T** the account's following timeline (tech niche only; it's a tech account), Worth joining only.
- **C** X API counts, Tool research only, reported as "how much talk", not ranked on useful posts.

## Idea cards (frozen now)

| Job | Tech | Satire / comedy |
|---|---|---|
| Demand | 1. People asking for a free alternative to a paid creator or developer tool. 2. People stuck getting results from AI coding agents (Claude Code, Codex, Cursor). | 1. What people are collectively reacting to or annoyed by today. 2. Running jokes or memes forming around a current event. |
| Worth joining | 1. Builders sharing progress on an AI app or tool. 2. Discussion of an AI model or tool released in the last day. | 1. A satirist's or comedian's post with an active thread of people riffing. 2. An absurd news story with people joking in the replies. |
| Tool research | 1. DaVinci Resolve (as a Premiere alternative). 2. Cursor. | 1. CapCut among meme and video creators. 2. Substack among satire and comedy writers. |

Windows: Worth joining, the last 6 hours; Demand, the last 24 hours; Tool research, 7 days. The same window for every source on an idea, recorded in UTC.

## Stage 0: pilot (ceiling $2.50 with P7 and the ~60-id check; worst case about $2)

| # | Call | Settles | Worst case |
|---|---|---|---|
| P0 | Usage endpoint probe (if documented) | F11 | ~$0 |
| P1 | Recent search, 10 posts, all post fields, filters `-is:retweet lang:en min_likes:5` | F1, F7, F9, F10 | $0.05 |
| P2 | The same query again with `expansions=author_id` + user fields | F2, F3 (posts repeat free; delta is authors) | $0.10 |
| P3 | Counts for one query | F4 | ≤$0.05 (unknown) |
| P4 | Following timeline, 10 posts | F5 | $0.05 |
| P5 | Queries of 513, 1,025 and 4,097 characters, `max_results=10` | F6 | ≤$0.15 |
| P6 | One Grok idea prompt; claimed posts checked | G1–G5 | $0.15 X API + Grok |
Stop after the pilot, update the plan to what it showed (e.g. whether author details are affordable), and report.

## Stages 1–3 (one job each, review between)

Order: Worth joining (at the time the operator gives the go-ahead; a second block later the same day if budget allows), Demand, Tool research.
Per idea, **20 posts per source**: K as 2 frozen query variants × 10 (recency for Worth joining, relevancy for Demand; both logged); G asked for up to 20; T one shared read of 100, filtered by a frozen keyword rule. Source order randomised per idea. All retrieved posts are scored, none hand-picked.
Every call asks for every post field; author fields only if the pilot shows they're affordable. No runs 19:30–20:30 Brisbane (the daily check).

**Worst case:** K $0.30 and G check $0.30 per idea (with authors) × 14 idea-runs ≈ $8.40, plus T ≈ $1.20 and C ≤ $0.40. The **$6 checkpoint** will likely come mid-way through Stage 2 or 3 if author reads bill; stages are ordered so the most important data comes first. Without author reads, about half. Grok's own cost is separate (checkpoint $3).

## Scoring (written before results)

Codex, blind to source: each post's text as returned, shuffled, with opaque ids; source, query, rank and time withheld. Per post, 0–2 each: **relevant** to the idea; **real** (a person, not spam, promotion, bot or farm); **useful for the job** (Demand: a genuine need or a live reaction; Worth joining: a live conversation a specific or witty reply would add to; Tool research: actually about the product). Plus "would you act on this?". Useful = 2, 2, ≥1. For comedy, "useful" judges whether it's a live conversation a witty reply could join, not whether it's funny.
Computed: freshness, duplicates, invented rate. I re-score 20% and report disagreements.
Before scoring, the gap that counts as a real difference is fixed: **a source must find at least 50% more useful posts per dollar, on at least 3 of the 6 job-niche cells**. Whatever the verdict, the report gives the full data per cell so the operator decides. The operator's tie-breaker: **simplicity favours dropping Grok** (fewer outside keys and subscriptions, less infrastructure: CSV and CSV + X API only). So the report has a section "What dropping Grok would cost": the useful posts only Grok found, per job and niche, with examples, and whether an X API query variant could have found them.

## Observability (all private, in `research/discovery-test/private/`, gitignored; deleted by 26 Mar 2027)

- `requests.jsonl`: one row per HTTP call: time, stage, idea, source, endpoint, full parameters, status, latency, rate-limit headers (limit, remaining, reset), access level, `result_count`, `meta` (newest/oldest id, next token), items by type, estimated cost, error body.
- `raw/`: every full response body.
- `grok.jsonl`: prompt, model, the full CLI envelope (tool calls and arguments, fetched counts, citations, tokens, cost), claimed posts, and each one's check result (real, invented, misquoted).
- `posts.csv`: one row per unique post: first and last seen, every source and rank that found it, verification status, fields at fetch.
- `budget.log`: running X API estimate, plus billed usage where readable; the operator's console reading before and after the pilot.
- `facts.md`: F1–F11 and G1–G5, each with the call ids that answered it.
- `stage-N.md`: what each stage showed and what changed next.

## Tooling

A harness at `research/discovery-test/harness.py` (research code, not factory code; never imported by `scripts/`) that uses `scripts/x_api.py`'s client for signing and GET-only calls, wraps every call with the logging above, and refuses anything but GET. Grok runs through the Grok CLI as `scripts/grok_read.py` does, with the whole envelope kept.

## Output

`research/discovery-search.md`: the facts learned (F, G), the per-source tables, what each job should use, costs at product scale, and choices for the operator.


## Grok prompting (added 26 Sep, operator)

The earlier research never covered how best to prompt Grok for X search. Today's relay (`scripts/x_read.py` `search_prompt`) steers hard: "Run x_keyword_search once with this exact query, mode Latest, limit 10", with `--effort low` and a strict JSON schema (`scripts/grok_read.py`). That rules out semantic search entirely, so **nothing so far shows semantic search is weak; it has never been tried.**
- **Docs step (free, before the pilot):** read xAI's guidance on prompting with X Search (docs.x.ai: tools, x-search, prompting or best-practice pages) and the Grok Build CLI's options (`grok --help`: model, effort, turns). Record in `facts.md` as G6.
- **Prompt arms, tested on the same ideas in the pilot (P7) and, if they differ, in Stage 1:**
  - **G-steered:** today's style, an exact keyword query forced through keyword search.
  - **G-free:** the idea in plain words; Grok chooses its own functions and queries.
  - **G-hinted:** the idea in plain words, plus "search by meaning, not just keywords; try several phrasings".
  - Effort low vs high on one idea, to see whether effort changes what it searches.
- Log each arm's tool calls from the CLI envelope (which functions, what arguments), posts fetched vs shown, invented rate and cost.
- Each arm's claimed posts are checked on the X API as usual (about $0.15 per 10 posts with authors), so budget P7 at up to $0.50 of X API.
- The Grok arm in Stages 1–3 uses whichever prompt arm the pilot shows works best; the report shows all arms' pilot results.

## Controls from the setup audit (26 Sep; `repo-grok-setup-audit.md`, `docs-grok-prompting.md`)

- **Run every Grok arm from a clean folder outside the repo** (`--cwd` to an empty directory). In the repo, Grok loads `AGENTS.md`, `CLAUDE.md`, 17 skills and 2 hooks (checked with `grok inspect`), and may invoke a skill unasked: `format-tool-swap` ("free alternatives", "never a raw Grok search") nearly matches Demand idea 1. Record the working folder for every run (evidence, not assumption). There is no in-repo comparison run.
- **Don't inherit the relay's limits:** no forced `x_keyword_search`, no "Latest", no limit 10, no `--effort low` unless it's the arm being tested. Keep `--sandbox read-only` (filesystem only, not network) and `--output-format json` the same across arms.
- **Model:** run `grok models` while signed in; pick the strongest general model (not the coding model), pass it with `-m` on every arm, and log it. Check whether X search follows the session model (`~/.grok/config.toml` routes `web_search` to another model).
- **Use `--verbatim`** on the steered arm, to confirm the exact wording sent.
- **"Invented" vs "misquoted":** `x_read.py`'s text match (60% similar or the first 40 characters) can drop a real, paraphrased post. Record every dropped post with its reason; a post that exists on X but fails the text match counts as "misquoted", never "invented".
- **Cross-session memory:** the Grok config has memory enabled. Note it in the log, and check whether it can be turned off for the test runs; if not, run the arms in a fixed order and say so in the report.

## From the community research (26 Sep; `community-grok-prompting.md`)

- **Every Grok arm tells Grok how many posts to fetch** ("fetch at most 20 posts across at most 3 searches"): shared across arms, not a variable. One team cut Grok's X-search cost about 60% this way.
- **Log `usage.server_side_tool_usage_details.x_posts_fetched` and `x_users_fetched`** from the CLI envelope if present (G4).
- **Watch for unsourced answers:** when a filter returns nothing, Grok can answer from memory. Record any arm whose posts don't verify alongside the filters it used.
- **The in-repo comparison run is dropped.** A July 2026 Grok CLI version uploaded whole repositories to xAI regardless of permissions (reported by several outlets; patched, per reports). Whether the operator's version (1.0.41) is clean isn't confirmed. All Grok runs happen from the clean folder only; the repo's effect is judged from the setup audit instead.


## From Grok's own report and live run, and its reviews (26 Sep)

Sources: `private/grok-insights/` (Grok's report C01–C240 and its runs), `review-grok-report-observed.md`, `review-grok-report-repo.md` (28 of 30 repo claims correct), `review-grok-report-docs.md` (23 of 24 docs claims correct), `review-grok-report-codex.md`.

**What Grok's in-session tools look like** (Grok's own reading of its tool definitions; not in xAI's public docs, so confirm in the pilot):
- `x_semantic_search`: `query` (one string), `limit` (default **3**, max 10), `min_score_threshold` (default 0.18), `usernames` / `exclude_usernames`, `from_date` / `to_date` (calendar days, YYYY-MM-DD). No hours, language, reply, engagement or sort parameter.
- `x_keyword_search`: `query` in **X's website search syntax** (`min_faves:`, `-filter:replies`, `within_time:6h`, `since:`/`until:`, `filter:links` …; `lang:` and `-is:reply` not listed), `limit` (default 3, max 10), `mode` Top (default) or Latest.
- So: **every Grok prompt sets limit 10**; semantic prompts **always set from_date/to_date**; the K arm (X API) uses API v2 syntax (`-is:reply`, `min_likes:`), the Grok keyword arm uses website syntax. Never mix them.

**What one live run showed** (directional; one idea, one product):
- Semantic search found on-point posts where keyword `Latest` returned 10 of 10 spam.
- Without dates, semantic returned posts from 2018–2025; with dates it stayed inside them.
- A rewording of the same idea returned a completely different set: use several phrasings per idea.
- Some semantic results are empty slots (no id, no text).
- Keyword operators pasted into a semantic query did nothing.
- **Provenance problem:** one "raw" file (S2) was reconstructed from another, not captured. Grok's saved files are transcriptions until proven otherwise.

**Changes to the test (Codex's review of the run, accepted):**
1. **Capture with provenance first (pilot P7).** Save the untouched CLI stdout/stderr and envelope, requested and observed tool arguments, model, working folder, time, byte count and a hash, before any processing. Find out whether the CLI exposes per-tool output at all; don't assume it.
2. **Count in four steps:** result slots → numeric ids → ids confirmed on the X API → confirmed posts inside the exact UTC window. Empty slots are counted but never scored. Out-of-window posts are reported as retrieval waste, not dropped silently.
3. **The shared window is an eligibility rule,** applied after retrieval by each post's timestamp, since semantic search can only filter by day.
4. **Repeat the semantic probes in the pilot:** UTC-midnight edges, each date endpoint, time zone, and queries with and without keyword syntax. Record as observations, never as schema facts.
5. **Tool research gets a frozen spam-control query variant per cell,** and spam share is reported per query.
6. **Scoring corpus is separate from raw:** Codex gets text with opaque ids (the operator chose raw text, so no stripping beyond leaving out the profile and media blocks the rendering adds); the raw stays private and hashed.
7. **Verify the ~60 ids from Grok's 26 Sep live run on the X API in the pilot** (about $0.30 plus authors): the first real invented-rate figure for semantic search.
8. **A fourth prompt arm, G-self:** Grok's own recommended prompts from its report (section 7), adjusted to set limit 10 and dates.

## Harness changes for the next X pull (27 Sep)

- **X API checkpoint raised to $7.00** of estimated spend (operator, 27 Sep; was $6). The pilot ceiling stays $2.50.
- New idea cards, added without editing any old one: `tr-tech-3` (Claude Code, Tool research), and `demand-comedy-1b` / `demand-comedy-2b` (the comedy Demand ideas with `min_likes:10` taken off the first query). They change the frozen hash, so stages refuse until `config --refreeze`.
- `config --pin-block <B>` keeps one block's windows for a pull that spans more than 2 hours; `config --pin-block none` clears it.
- A K source that stops part-way resumes without resending queries that already returned 200 in that block. A K query whose `min_replies:` is rejected (HTTP 400) is rerun once without it, and the step notes it.
- Scoring files for a new block are block-named (`corpus-stage{N}-{B}.jsonl` and so on), and no scoring command overwrites an existing file. `ingest-scores` and `second-scores` write nothing unless every id is scored exactly once. `--second all` sends every post to the second scorer.
- Stage 1 corpus lines carry `replies` and `age_hours` when the post was found, and the Stage 1 brief says to use them.
- `reread` works in batches of 100 and marks a post gone only when its id was sent and X's answer lacked it. `manifest --block B` lists every sighting in a block with its source, sort, query variant, rank and call.
