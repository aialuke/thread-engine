# Review: docs claims in x-search-tools-report.md

Scope: every claim labelled `FETCHED` or `OTHER-SURFACE` in
`research/discovery-test/private/grok-insights/x-search-tools-report.md`, checked against
(1) this repo's own docs research — `research/discovery-test/docs-grok.md`,
`docs-grok-prompting.md`, `community-grok-prompting.md` — and (2) the live official pages
those claims cite (docs.x.ai, fetched today via `curl` with a browser user agent and via the
WebFetch tool, both live).

That set, per the report's own claim index: `C178`, `C186`–`C191`, `C209`–`C225`. 24 claims.
No CONTRADICT/UNRESOLVED claim outside this range names an xAI doc page (checked the index).

Method note: `docs.x.ai` is a Next.js app that serves an identical `.md` alternate at each
page's URL plus `.md`. The WebFetch tool used in this review reproduces the report's own
404 on that alternate; a plain `curl` with a browser `User-Agent` gets `200` with the raw
markdown. Both were tried below so a "404" claim isn't wrongly flagged as false just
because a different client succeeds.

## Per-claim result

| ID | Mark | Note |
|---|---|---|
| C178 | KEEP | `research/discovery-test/community-grok-prompting.md` §2 quotes Hermes Agent's docs verbatim: "`degraded` — `true` when any narrowing filter (`allowed_x_handles`, `excluded_x_handles`, `from_date`, `to_date`) was set AND both citation channels came back empty," with the consequence "xAI's X index returned no matching posts but Grok still produced a synthesized answer from its own training data. The answer is unsourced — do not treat it as a real X result." That file itself frames this as "this team's own detection logic layered on top of `x_search`, not a guaranteed field in xAI's raw response" — exactly what C178 says. |
| C186 | KEEP | `docs-grok.md` line 3: "Scope: official xAI docs only (docs.x.ai, x.ai), fetched today (26 Sep 2026). No xAI/X API calls, no Grok CLI runs, no Keychain reads made." Matches exactly. |
| C187 | KEEP | `docs-grok.md` §1: "there is no separate documented tool per function. `x_keyword_search`, `x_semantic_search`, `x_user_search`, `x_thread_fetch` are internal function names the model can call; the *developer-facing* tool is a single `x_search` … with one shared parameter set." Matches exactly. |
| C188 | KEEP | `docs-grok.md`'s parameter table and prose match: `allowed_x_handles`/`excluded_x_handles` "max 20," "cannot be set together," `from_date`/`to_date` ISO8601 "including both dates," `enable_image_understanding`, `enable_video_understanding`. Confirmed live on `https://docs.x.ai/developers/tools/x-search` (fetched 2026-09-26): "`allowed_x_handles` … cannot be set together with `excluded_x_handles` in the same request," "`to_date` … including both dates." |
| C189 | KEEP | `docs-grok.md` §1: caller gets "(a) tool-call *arguments* …, (b) item **counts** …, (c) **citations** …, and (d) the model's own generated text." Confirmed live on `https://docs.x.ai/developers/tools/tool-usage-details`: "Only the tool call invocations are shown — server-side tool call outputs are not returned in the API response. The agent uses these outputs internally to formulate its final response." |
| C190 | KEEP | Structural conclusion, not itself a docs fact to fetch. It follows validly from C188/C189 plus the in-chat schema the report quotes at `C10`–`C17`/`C162`–`C170` (which do include a `limit`, a `min_score_threshold`, and `usernames`/`exclude_usernames` — none of which appear in the public `x_search` table verified live below at C218). Nothing in either docs research file or the live pages contradicts this. |
| C191 | KEEP | `docs-grok.md` §2: "xAI gives **zero description of how semantic search matches content, its index window, recency**, or any quality/limits notes specific to it." Matches; confirmed no such language appears on the live x-search, tool-usage-details, or citations pages either. |
| C209 | KEEP | Procedural claim about the report's own actions (no tool call made); nothing in either docs file or the live pages bears on it either way. |
| C210 | UNRESOLVED | Names specific web-search hits (Hermes Agent, OpenClaw, and the two docs.x.ai URLs). The two docs.x.ai URLs are real and exist; `community-grok-prompting.md` independently cites Hermes Agent, so that hit is plausible. But a web search's exact result set for one past query can't be independently reproduced or verified from here — treated as unresolved rather than confirmed or denied. |
| C211 | KEEP | Confirmed live, `https://docs.x.ai/developers/tools/x-search` (curl, 2026-09-26): opening line "The X Search tool enables Grok to perform keyword search, semantic search, user search, and thread fetch on X (formerly Twitter). This powerful tool allows the model to access real-time social media content…" and footer "Last updated: September 22, 2026." Both phrases match C211 verbatim. |
| C212 | KEEP | `https://docs.x.ai/developers/tools/x-search.md` returns `404` when fetched with this session's WebFetch tool today (reproduced live), matching the report's own method. (A plain `curl` with a browser `User-Agent` instead gets `200` with the raw markdown — the site content-negotiates the `.md` alternate differently by client/headers — but that doesn't contradict what the report observed with its own fetch method.) |
| C213 | KEEP | Confirmed live: `https://docs.x.ai/docs/guides/live-search` 308-redirects and the resolved page's `<title>` is "Web Search \| SpaceXAI Docs" — the Web Search page, not a separate X live-search guide. |
| C214 | KEEP | Confirmed live, `https://docs.x.ai/developers/tools/tool-usage-details`: "**Note**: Only the tool call invocations are shown — **server-side tool call outputs are not returned** in the API response. The agent uses these outputs internally to formulate its final response." Exact match. |
| C215 | KEEP | Confirmed live, `https://docs.x.ai/developers/tools/citations`: "Note that not every URL in this list will necessarily be directly referenced in the final answer... but the URL will still appear in this list for transparency," and "Enabling inline citations does not guarantee that the model will cite sources on every answer." Both match. |
| C216 | KEEP | Confirmed live, `https://docs.x.ai/developers/models`: "Grok has no knowledge of current events or data beyond what was present in its training data. To incorporate realtime data with your request, enable server-side search tools (Web Search / X Search)," and "The knowledge cut-off date of Grok 4.7 is May 2026." Both match exactly. |
| C217 | KEEP | Confirmed live: the x-search page's SDK example uses the prompt "What are people saying about xAI on X?" with `xai.tools.xSearch()` and no extra parameters, no forcing switch. `tool-usage-details` confirms the mapping: "`SERVER_SIDE_TOOL_X_SEARCH` → `x_user_search`, `x_keyword_search`, `x_semantic_search`, `x_thread_fetch`." |
| C218 | KEEP | Confirmed live: the x-search parameter table has only `allowed_x_handles`, `excluded_x_handles`, `from_date`, `to_date`, `enable_image_understanding`, `enable_video_understanding`. No `mode`, `limit`, or `min_score_threshold` string appears anywhere on the page (checked directly against the raw HTML). |
| C219 | KEEP | Confirmed live, verbatim on the x-search page: "Setting `enable_video_understanding` to true allows the agent to analyze videos in X posts. This is only available for X Search (not Web Search)," and "Setting `enable_image_understanding` to true allows the agent to analyze images in X posts encountered during the search process." Both match. |
| C220 | KEEP | Confirmed live on two pages. Web Search page (`developers/tools/web-search`): "Enabling this parameter for Web Search will also enable the image understanding for X Search tool if it's also included in the request," and "Setting `enable_image_understanding` to true equips the agent with access to the `view_image` tool… When enabled, you will see `SERVER_SIDE_TOOL_VIEW_IMAGE`…" Tool Usage Details page confirms the `view_x_video` / `SERVER_SIDE_TOOL_VIEW_X_VIDEO` pairing the same way it pairs `view_image` / `SERVER_SIDE_TOOL_VIEW_IMAGE`. |
| C221 | KEEP | Confirmed live. x-search page: "X Search is billed at $5 per 1k posts fetched and $10 per 1k user profiles fetched." Same page: "`x_thread_fetch`, including parent and quoted posts and every post of a fetched thread" for `x_posts_fetched`, and "Both counts accumulate over every X Search call in the request and are not de-duplicated; a post returned by two searches counts twice." Tool Usage Details page: "As of September 21, 2026, X Search is billed per post and per user profile fetched rather than per call." All match. |
| C222 | KEEP | Confirmed live, Tool Usage Details page: "If `max_turns` is not specified, the server applies a global default cap. When the agent reaches the limit, it will stop making additional tool calls and generate a final response based on information gathered so far," and a table: "Quick lookups 1-2 … Balanced research 3-5 … Deep research 10+ or unset." Report says "10 or more," page says "10+ or unset" — same meaning. |
| C223 | KEEP | Confirmed live, Tool Usage Details page: "Failed attempts are not charged. X Search is billed per post and per user profile fetched rather than per call." Matches. |
| C224 | KEEP | Structural comparison; both halves it rests on are independently confirmed above (in-chat schema at `C10`–`C17` vs. the live public table at C218; the API caller not receiving posts at C214/C218). Nothing found contradicts it. |
| C225 | KEEP | Confirmed by omission: none of the fetched pages (x-search, tool-usage-details, citations, models) states the semantic matching method, index start, hit freshness, reply/language mix, or filter-before-cut order — same gap `docs-grok.md` §2 independently found. |

## Counts

- Checked: 24
- KEEP: 23
- CONTRADICT: 0
- UNRESOLVED: 1 (`C210`)

No contradictions were found between the report's `FETCHED`/`OTHER-SURFACE` claims and
either this repo's prior docs research or the live docs.x.ai pages fetched today
(2026-09-26). Every direct quote in the report that could be checked against a live page —
the x-search opening line and "last updated" date, the parameter table, the pricing line,
the billing/output-shape note, the citations caveat, the models-page knowledge-cutoff note,
the `max_turns` table, and the image/video-understanding cross-tool note — reproduced
verbatim. The one `UNRESOLVED` (`C210`) is a claim about a past web search's exact hit list,
which can't be replayed to confirm or deny; nothing found makes it implausible.

## The structural question: does the in-chat tool set differ from the public API's?

**Plain English: partly confirmed, partly just undocumented — and nothing found contradicts
the report.**

What's confirmed, straight from xAI's own live pages:

- The public, developer-facing surface is one tool, `x_search`, with exactly six
  parameters: `allowed_x_handles`, `excluded_x_handles` (max 20 each, mutually exclusive),
  `from_date`, `to_date` (ISO8601, both dates inclusive), `enable_image_understanding`,
  `enable_video_understanding`. No `limit`, no `mode`, no `min_score_threshold`, no
  `usernames`/`exclude_usernames` — checked directly against the live page's HTML, not just
  the visible text.
- `x_keyword_search`, `x_semantic_search`, `x_user_search`, `x_thread_fetch` are documented
  only as internal function names Grok picks between (the Tool Usage Details billing
  table). No xAI page gives any of the four its own parameter list.
- The public API caller genuinely does not get the raw post data back: "server-side tool
  call outputs are not returned in the API response." The caller gets tool-call arguments,
  item counts, and citations (URLs) — the model's own text is what carries any content
  through. This is stated once, in exactly those words, and nothing anywhere qualifies it
  by client type (chat product vs. raw API vs. CLI).

What's *not* confirmed by anything official or community-sourced, because it isn't
addressed at all:

- Nobody — not xAI's docs, not the Rod Trent blog post, not the Hermes Agent wrapper docs,
  not the Grok Build CLI's own `--help` text — documents a separate, richer parameter set
  (`limit`, `min_score_threshold`, `usernames`, `exclude_usernames`) for the in-chat/CLI
  surface the report was run in. That schema is this session's own direct observation
  (quoted verbatim in the report at `C05`–`C23`), not something published anywhere this
  review could check it against. `docs-grok-prompting.md` explicitly tried to find CLI-level
  tool configuration (`grok --help`, `--tools`/`--disallowed-tools`) and came back empty:
  the CLI's help text "does not enumerate what those names are (no confirmation `x_search`
  is a nameable value from `--help` text alone)."
- Nothing found explains *why* a chat-style session would see richer parameters and get
  the tool's result while the API doesn't. The one architectural fact that's confirmed —
  "the agent uses these outputs internally to formulate its final response" — is consistent
  with either explanation: a genuinely different, client-side-style tool-calling
  implementation in the chat/CLI product (result handed back into context, so the
  transcript shows it), or simply the same server-side mechanism with the chat product
  choosing to surface more of what the model saw. Neither this report nor anything found in
  this pass distinguishes those two possibilities.

So the report's own care in labelling this section (`OTHER-SURFACE`, and C190's explicit
warning against "copying `C188` or `C189` onto this chat's `x_semantic_search`") is
justified: the "API caller gets no raw output" half is solidly confirmed by xAI's own
wording; the "in-chat tool set is richer and its output is visible" half remains this
session's unconfirmed, uncontradicted, first-hand observation.
