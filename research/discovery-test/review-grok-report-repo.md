# Review: repo-file claims in x-search-tools-report.md

Scope: every claim labelled `CONFIG`, `SCRIPT` or `SESSION-RULE` in
`research/discovery-test/private/grok-insights/x-search-tools-report.md` that names a repo
file, checked against the actual files (`AGENTS.md`, `CLAUDE.md`,
`.claude/skills/next/SKILL.md`, `.claude/skills/format-tool-swap/SKILL.md`,
`.claude/settings.json`, `scripts/x_read.py`, `scripts/grok_read.py`,
`reviews/x-tools-pilot.md`, `reference/x-algorithm.md`, `reference/x-api.md`).

That set, per the report's own claim index: `C25`, `C118`, `C150`–`C154`, `C172`–`C177`,
`C184`–`C185`, `C192`–`C208`. 30 claims. No CONFIG/SCRIPT/SESSION-RULE claim outside this
range names a repo file (checked the full index).

## Per-claim result

| ID | Mark | Note |
|---|---|---|
| C25 | KEEP | `scripts/x_read.py`, `scripts/grok_read.py`, `scripts/x_api.py` all exist as named. |
| C118 | KEEP | Matches AGENTS.md: "invented or misquoted posts are dropped and listed, and nothing is returned if the check can't run... Never cite a post that didn't pass this check." |
| C150 | KEEP | Matches AGENTS.md: "Never post, schedule, or call an X write API... Other people's posts and research go through Grok's X tools or `scripts/x_read.py`, which make one read-only Grok call." |
| C151 | KEEP | Same AGENTS.md line as C118/C150, accurately summarised. |
| C152 | KEEP | Matches AGENTS.md layout line: "`scripts/x_api.py` — read-only X API client for the account's own posts (whole text, from `note_tweet`), mentions, followers and profile; `user <handle>` checks an account before a post tags it; GET only; `keys` checks the Keychain without reading values." |
| C153 | KEEP | AGENTS.md layout line names `reference/x-api.md`: "what the X API can and cannot read, prices, and the privacy rules." |
| C154 | KEEP | Matches CLAUDE.md's cloud note ("Drafts are the product. Do not post. Do not write to X." / "X API keys live in macOS Keychain and are not available here."). Minor paraphrase drift: the report says keys "are not for this kind of answer"; the file's actual reason is that they're technically unavailable in this cloud session, not that they're unsuitable for the question. Not a contradiction, just a softer reason than the file gives. |
| C172 | KEEP | Exact match to `scripts/x_read.py`'s `search_prompt`: `"Read-only. Run x_keyword_search once with this exact query, mode Latest, limit 10: {query}\nReturn every post it gives..."`. |
| C173 | KEEP | Consistent with C172; `search_prompt` never names `x_semantic_search`. |
| C174 | KEEP | Matches `scripts/grok_read.py` docstring ("The only way this repo reads X"; read-only sandbox, no shell/edit/write) and its subprocess call (`--json-schema`, `--output-format json`, `--effort low`, `--sandbox read-only`, `--deny Bash/Edit/Write`). |
| C175 | KEEP | Same file: `--effort low` is a flag on the command line, separate from the prompt text that names `x_keyword_search`. |
| C176 | KEEP | Consistent with C174/C175. |
| C177 | KEEP | Matches `x_read.py`'s `same_text` docstring ("Grok may shorten or reflow a post; a real match shares its opening or most of its words") and `EVIDENCE` string ("a value you could not read is null. created_at is ISO 8601 UTC ending in Z. author is the handle without @"). |
| C184 | KEEP | Matches AGENTS.md layout line: "`scripts/grok_read.py` — the one read-only structured Grok call every X read goes through." |
| C185 | KEEP | Confirmed by grep: no file in `.claude/`, `scripts/`, `reference/`, `AGENTS.md`, `CLAUDE.md` contains the string "semantic". `x_read.py` calls only `x_keyword_search` / `x_thread_fetch`. |
| C192 | KEEP | Matches AGENTS.md's "or" wording and the layout line "for sessions without X tools." |
| C193 | KEEP (with a note) | Section 6 of `next/SKILL.md` ("Replies worth making today") does say "Find 2 or 3 conversations... with `python3 scripts/x_read.py search "<query>"`" and lists "a builder's progress post in the lane (AI tools, agents, video pipelines, shipping), preferring verified accounts and existing mutuals" — matches. But the sentence "The skill says not to use `x_keyword_search` directly, because that skips the id check" is not in section 6; that exact language ("don't use `x_keyword_search` directly, because it skips that check") is in section 4 (Demand), not section 6. The claim doesn't explicitly say "section 6 contains this sentence," so I did not mark it CONTRADICT, but the paragraph reads as if it's all describing section 6. |
| C194 | KEEP | Matches `next/SKILL.md` §4 ("Demand: run one or two searches for recent questions in the lane (for example `"how do I" free video editor lang:en -filter:replies`) with `python3 scripts/x_read.py search "<query>"`") and `format-tool-swap/SKILL.md` ("check with `python3 scripts/x_read.py search "<query>"`, never a raw Grok search"). |
| C195 | KEEP | `next/SKILL.md` frontmatter, line 7: `disable-model-invocation: true`. |
| C196 | KEEP | Inferential summary, consistent with C172–C177, C193–C194. |
| C197 | KEEP | `next/SKILL.md` §4 uses `lang:en` in its demand-query example, exactly as claimed. |
| C199 | **CONTRADICT** | Claim: "`/next` caps its demand search and its reply search at one or two `x_read.py` searches." `next/SKILL.md` §4 (Demand) does say "run one or two searches." But §6 (Replies), line: "Find 2 or 3 conversations from the last few hours worth a reply, with `python3 scripts/x_read.py search "<query>"`" caps the number of **conversations kept**, not the number of search calls — no "one or two" (or any) call cap appears in §6. The "one or two" number belongs only to the demand step; extending it to the reply step misstates the file. |
| C201 | **CONTRADICT** | Claim: "`/next` section 6 forbids that direct call [`x_keyword_search`] and asks for 2 or 3 checked conversations, verified accounts and mutuals when possible..." The "2 or 3 checked conversations, verified accounts and mutuals" part matches §6 exactly. But the forbidding sentence — "don't use `x_keyword_search` directly, because it skips that check" — is in §4 (Demand), not §6 (Replies); §6 contains no such sentence, only the `x_read.py` command itself. Attributing the explicit prohibition to section 6 is not supported by that section's text. |
| C202 | KEEP | `next/SKILL.md` §4: "Timing: propose a posting time in Australia/Brisbane." |
| C203 | KEEP | `next/SKILL.md` §6: "preferring verified accounts and existing mutuals." |
| C204 | KEEP | `reference/x-algorithm.md` is entirely about home-timeline ranking (A1–A22); it never defines keyword-search `Top`/`Latest`. |
| C205 | KEEP | Matches AGENTS.md ("Start non-trivial work in Plan mode.") and CLAUDE.md's cloud note (same sentence, last bullet). |
| C206 | KEEP | Matches CLAUDE.md cloud note: "X API keys live in macOS Keychain and are not available here. Skip snapshot/metrics that need them. Use committed ledger/ and reviews/ instead." |
| C207 | KEEP | `.claude/settings.json` allowlists exactly `scripts/loop.py`, `scripts/snapshot.py`, `scripts/x_read.py`, `scripts/x_api.py`, `scripts/post_thread.py` (plus `WebFetch(domain:github.com)`); no deny rule blocks native X tools. |
| C208 | KEEP | Consistent with C193–C196, C201, C195 (session-history claim, not independently file-checkable beyond those). |

## Counts

- Checked: 30
- KEEP: 28 (one, C193, KEEP with a note on a blurred section boundary)
- CONTRADICT: 2 (`C199`, `C201`)
- UNRESOLVED: 0

Both contradictions are the same underlying error, made twice: the report attributes
`next/SKILL.md` §4's explicit instruction ("don't use `x_keyword_search` directly, because
it skips that check" / "run one or two searches") to §6 ("Replies worth making today"),
which has neither sentence — it only names the `x_read.py` command and caps the number of
kept **conversations** (2 or 3), not the number of **searches**. `C193` shows the same
blur but is phrased ambiguously enough ("the skill says," not "section 6 says") that it
isn't a clean contradiction.

## What the checked files show about Grok's X search that the report didn't capture

1. **The reply-author search undercounts in practice.** `reviews/x-tools-pilot.md` says
   `conversation_id:` search is "complete for these two threads; capped at 10 per call,
   page with `since_id` / `max_id`" — i.e. paging exists as a documented workaround. A
   separate repo file outside the checked set, `reviews/prompt-audit-2026-09-24/REPORT.md`
   (finding H3), reports that in a real run the loop's reply-author count came back 9
   authors against 32 actual replies on one pinned post — the `since_id`/`max_id` paging
   the pilot describes is not exercised anywhere in `scripts/loop.py`'s snapshot path, so
   keyword search's 10-per-call cap silently produces an undercount rather than a
   complete list. This is a concrete, current gap in how the factory's only exercised X
   search tool (`x_keyword_search` via `x_read.py`) behaves at scale, and it isn't in the
   report's discussion of pagination (`C40`, `C107`).
2. **`x_read.py`'s cost path is per-call, and doubles the read cost of every search.**
   `x_read.py` combines one Grok call (`grok_read.run_structured`, billed by xAI) with one
   X-API lookup per returned post (`x_api.lookup`, "about $0.005 a post" per its own
   docstring) to verify ids. The report's discussion of cost is confined to section 11's
   public-API pricing (`C221`); it never notes that the factory's own scripted path pays
   twice — once to Grok for the search, once to the X API for the verification — for
   every post it keeps.
3. **`.claude/settings.json` has no PreToolUse restriction on the X-search tool names
   themselves** — only a `UserPromptSubmit` approve-hook and a `PreToolUse` guard hook,
   neither of which mentions `x_keyword_search`/`x_semantic_search`/`x_thread_fetch`/
   `x_user_search`. `C207` says this correctly (settings.json "does not block this chat's
   native X tools"), but the report doesn't note that the guard hook (`guard_approved.py`)
   and approve hook (`approve.py`) are unrelated to search at all — they exist only to
   protect the `APPROVED` marker and loop state, so there is no repo-level gate on native
   X-tool use beyond the skill-level prose in `next` and `format-tool-swap`.

## Note on file-path claims about the moved folder

Per the task's instruction, claims that give a path under "Grok Insights" as it stood
before the move to `research/discovery-test/private/grok-insights/` are not treated as
errors here.
