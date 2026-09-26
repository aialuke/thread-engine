# Repo/Grok setup audit — could the factory's own config make Grok look weaker than it is?

Read-only audit for the discovery test (`research/discovery-test/plan.md`, "Grok prompting" section, added 26 Sep). No files edited but this one. No Grok search calls, no X API calls made. `loop/followers/`, `ledger/raw/api/` and `loop/inbox/` were not opened.

Marked **[inference]** where I reasoned from documented behaviour rather than reading it stated outright. Everything else is read directly from the cited file or command output.

---

## 1. `scripts/x_read.py` and `scripts/grok_read.py`

**The prompt forces one keyword call, "Latest" mode, limit 10, no reformulation.**
`scripts/x_read.py:44-46` (`search_prompt`):
```
return (f"Read-only. Run x_keyword_search once with this exact query, mode Latest, limit 10: {query}\n"
        f"Return every post it gives, with metrics from its Engagement line. {EVIDENCE}")
```
This is an instruction, not a tool restriction — Grok's tool set isn't narrowed at the CLI level (see below), so the model *could* ignore it and search differently, but a compliant model does exactly what it's told: one `x_keyword_search` call, recency-sorted, ≤10 results, on the exact query string handed in. That rules out: semantic/meaning-based search, relevancy sort, multiple phrasings, and any query Grok might otherwise choose from a plain-language idea. The plan's own "Grok prompting" section already names this as the G-steered arm and flags that semantic search "has never been tried" — this file is the source of that arm.

`scripts/x_read.py:49-52` (`thread_prompt`) does the same for threads: forces exactly one `x_thread_fetch` call.

**Schema is a filter after the fact, not (on its face) a turn limiter.** `scripts/x_read.py:29-39` defines `POST`, `SEARCH_SCHEMA`, `THREAD_SCHEMA` — required fields `id`, `author`, `created_at`, `text`, an `error` string, nested `metrics`. `scripts/grok_read.py:39` passes this schema via `--json-schema`, which (per `grok --help`, confirmed below) "implies `--output-format json`" and "constrains the model to produce JSON matching this schema." **[inference]** A schema this shallow (flat list of posts, no `tool_calls_made` or `queries_tried` field) gives the model no structured place to report that it tried several searches or reformulated — it only has to emit a `posts` array. Whether this actually *shortens* Grok's tool-use loop (fewer turns) versus just shaping the final answer is not shown by anything I read; `~/.grok/docs/user-guide/14-headless-mode.md:295` documents `error_max_structured_output_retries` as a distinct failure mode from `error_max_turns`, meaning schema conformance and turn budget are handled as separate mechanisms in the CLI — so the schema is not documented as a turn cap. Flagged as G1/G6 work for the docs step, not resolved here.

**The id + text-match check is strict enough to legitimately drop good paraphrase, and this is a scoring artifact, not a search-behaviour bias.** `scripts/x_read.py:60-65` (`same_text`): a claimed post is kept only if its first 40 characters (casefolded, URLs stripped) appear verbatim in the real post's text, **or** `difflib.SequenceMatcher` ratio ≥ 0.6. `scripts/x_read.py:68-86` (`verify`) drops anything that fails this, or whose id X doesn't have. This doesn't change what Grok searches for, but it does mean: if Grok legitimately finds a real post and paraphrases or truncates it more than this threshold allows, `x_read.py` will report it as "dropped … text does not match," inflating the apparent invented-post rate (G3) without Grok having invented anything. **Control:** when scoring G3 in the pilot, keep the raw claimed text next to the dropped reason, and manually check a sample of "text does not match" drops — don't take the drop count as an honest invention rate.

**`grok_read.py` fixes cwd, sandbox, denied tools, and effort — but not the model or turn count.**
`scripts/grok_read.py:16-17`: `ROOT = Path(__file__).resolve().parent.parent` (the repo root); `GROK = ~/.grok/bin/grok`.
`scripts/grok_read.py:38-41`:
```
[str(GROK), "-p", prompt, "--json-schema", json.dumps(schema), "--output-format", "json",
 "--sandbox", "read-only", "--deny", "Bash", "--deny", "Edit", "--deny", "Write", "--effort", "low"],
cwd=ROOT, ...
```
- `cwd=ROOT`: every call runs with the repo as working directory. This is the mechanism behind finding 2 below — it's why AGENTS.md, CLAUDE.md and all 17 project skills load automatically on every `x_read.py`/`grok_read.py` call, including ones that have nothing to do with the factory's posting rules.
- `--sandbox read-only`: per `~/.grok/docs/user-guide/18-sandbox.md:15-16`, this profile means "read everywhere, write only to `~/.grok/` + temp dirs" — it is a **filesystem** restriction. Nothing in the sandbox doc ties `read-only` to a network restriction (that's `strict`, which explicitly notes "no child network" at `18-sandbox.md:19`). **[inference, fairly confident]** so `--sandbox read-only` should not itself block the network calls `x_keyword_search`/`x_thread_fetch` need — the sandbox isn't why a search would fail or come back thin.
- `--deny Bash/Edit/Write`: removes tools irrelevant to search; shouldn't affect search behaviour.
- `--effort low`: passed on every call, with no arm that varies it. The docs (`~/.grok/docs/user-guide/14-headless-mode.md:36`) list `none, minimal, low, medium, high, xhigh, max` as the reasoning-effort tiers. `low` is near the bottom. **[inference]** A low-effort setting plausibly makes the model less likely to try multiple query phrasings, multiple tool calls, or notice a bad first result and retry — that's exactly the G-effort arm the plan already proposes, so this is expected, not a hidden bug. The point for the test: **today's tool has never been run above `low`**, and every prior "Grok is weak at X search" impression from this repo's normal factory use was formed at `low` effort.
- No `-m/--model` is passed, so `x_read.py`/`grok_read.py` run whatever the CLI treats as its default model for a `-p` session. `~/.grok/config.toml:6` sets `[models] default = "grok-build"`. **[inference]** "grok-build" reads as an agentic/coding-oriented model, not necessarily the strongest model at open-ended X search or semantic reasoning — the plan's own instruction ("pick the strongest non-coding model … if `grok --help` shows a model flag") already anticipates overriding this. Worth noting `~/.grok/config.toml:7` also sets a *separate* `web_search = "grok-4.5"` model — i.e., the CLI already routes at least one built-in search-adjacent tool to a different model than the session default. Whether `x_keyword_search`/`x_thread_fetch` (X's own search, not generic `web_search`) also get routed to `grok-4.5` regardless of session model, or run on the "grok-build" default, is not shown by anything read-only here — that's a concrete question for the docs step (G6), not answered by this audit.

**Control for section 1:** run the pilot's prompt arms (G-steered / G-free / G-hinted) through `grok_read.py`'s exact flags but with the prompt text swapped, and separately re-run at `--effort high`/`max` and with an explicit `-m` model flag, so effort and model choice aren't silently held at today's defaults while "prompt style" is the only thing that changes.

---

## 2. What Grok loads automatically at cwd = repo root

Verified directly with `grok inspect`, run once from `/Users/lukemckenzie/src/thread-engine` and once from an empty scratch directory, for comparison (both read-only; no prompt sent, no network search performed).

**From the repo root, Grok auto-loads:**
```
Project Instructions (4)
 /Users/lukemckenzie/.grok/rules/skill-paths.md (global, ~113 tokens)
 /Users/lukemckenzie/.claude/Claude.md (global, ~12 tokens) [claude]
 /Users/lukemckenzie/src/thread-engine/Agents.md (project, ~1753 tokens)
 /Users/lukemckenzie/src/thread-engine/Claude.md (project, ~143 tokens)

Skills (117) — includes all 17 project skills: apply, approve, draft-thread,
 format-build-log, format-comparison, format-settings, format-single-tip,
 format-tool-swap, format-tool-verdict, hidden-settings, next, posted,
 ready, results, snapshot, undo-rule, verify-settings   [project, claude]

Hooks (10) — 2 more than the clean-dir run (8), both "project [claude]":
 the repo's UserPromptSubmit and PreToolUse hooks from .claude/settings.json
```
From the **empty scratch dir**: `Project Instructions (2)` (only the two global/user files), `Skills (100)` (only user/bundled/plugin skills, zero project ones), `Hooks (8)` (only user-level hooks). This confirms `grok --cwd <clean folder>` (or literally running from outside the repo) is the control the plan should use for a "no project config" baseline — I found no dedicated flag for it; see below.

This matters for every planned arm (G-steered, G-free, G-hinted) because `grok_read.py:41` always sets `cwd=ROOT` — **the full AGENTS.md, CLAUDE.md and all 17 skills load on every call the factory makes**, not just the ones about drafting or posting.

**Could any loaded file steer or block search specifically?**
- `AGENTS.md:13`: "Other people's posts and research go through Grok's X tools or `scripts/x_read.py`, which make one read-only Grok call." This is project instruction text sitting in Grok's context on every run in this repo (system-prompt-adjacent, per `~/.grok/docs/user-guide/12-project-rules.md`, "Auto-Loading Behavior": loaded automatically at session start, repo root to cwd). **[inference]** A model that has just read "one read-only Grok call" as a project convention is primed toward exactly the single-call, keyword-search pattern `x_read.py`'s prompt also enforces — reinforcing rather than contradicting the steering in section 1, so the two combine rather than being independent factors.
- `AGENTS.md:54` repeats "for sessions without X tools" and "never cite a post that didn't pass this check" — again reinforcing the drop/verify pattern, not blocking search itself.
- **Skill auto-invocation is the concrete risk, and it's already been observed once.** `reviews/ui-direction.md:119`: "**Grok ran a skill on its own.** In the same scratch test, a plain prompt ('Reply with the word ok.') led Grok to invoke the test skill unasked. `/draft-thread` and `/verify-settings` don't set `disable-model-invocation` … so a model can start them itself today." I checked every skill's frontmatter directly (`.claude/skills/*/SKILL.md`): `apply`, `approve`, `next`, `posted`, `ready`, `results`, `snapshot`, `undo-rule` all set `disable-model-invocation: true` and cannot auto-fire. But **`draft-thread`, `format-build-log`, `format-comparison`, `format-settings`, `format-single-tip`, `format-tool-swap`, `format-tool-verdict`, `hidden-settings`, `verify-settings` do not set it**, so per `~/.grok/docs/user-guide/08-skills.md:110-111,186,188`, Grok can invoke any of these on its own whenever the prompt matches their `description`/`when-to-use` text.
  - The sharpest overlap with the discovery test: `.claude/skills/format-tool-swap/SKILL.md:8` — `when-to-use: Use for a PAID → FREE post, a paid-to-free swap list, free alternatives, or /format-tool-swap.` The plan's own **Demand** idea card 1 (`plan.md`, Idea cards table) is "People asking for a free alternative to a paid creator or developer tool" — nearly verbatim overlap with "free alternatives." A discovery-test prompt built from that idea card, run with `cwd` inside this repo, risks Grok auto-invoking `format-tool-swap`, which itself says at `.claude/skills/format-tool-swap/SKILL.md:48`: "check with `python3 scripts/x_read.py search \"<query>\"`, **never a raw Grok search**." That instruction would push a "G-free" arm straight back into the G-steered pattern the test is trying to distinguish it from — silently, since nothing in the test's own prompt asked for it.
  - Good news for the `next` skill specifically: because it sets `disable-model-invocation: true` (`.claude/skills/next/SKILL.md:7`), its stronger wording (`.claude/skills/next/SKILL.md:46`: "don't use `x_keyword_search` directly, because it skips that check") can't fire on its own from a bare prompt — only an explicit `/next` invocation would load it.
- **The PreToolUse guard does not touch search tools.** `.claude/hooks/guard_approved.py:70-71`:
  ```
  if tool in NO_WRITE or tool.startswith(("x_", "web_")):
      sys.exit(0)
  ```
  Any tool whose name starts with `x_` (i.e. `x_keyword_search`, `x_thread_fetch`) or `web_` exits the hook immediately with no decision — it is explicitly exempted, not evaluated. The guard's actual concerns (`.claude/hooks/guard_approved.py:23-45`) are the `APPROVED` marker file, loop-state files, and shell commands that write them or nest an `/approve` prompt. **Conclusion: the guard hook is not a confound for this test** — it can't deny, delay, or otherwise shape an X search call.
- **The UserPromptSubmit hook (`approve.py`) only fires on an exact `/approve <slug>` prompt.** `.claude/hooks/approve.py:18`: `APPROVE_RE = re.compile(r"^/approve\s+([A-Za-z0-9-]+)\s*$")`; anything else falls through at `.claude/hooks/approve.py:39-41` with no effect. A discovery-test prompt (an idea in plain words, or a keyword query) will never match this regex, so this hook is inert for the test.
- **Hooks fail open, not closed**, which matters for interpreting any anomaly: `~/.grok/docs/user-guide/10-hooks.md:166`: "All hook failures (timeouts, crashes, malformed output, missing required env vars) are fail-open … Only an explicit `deny` decision returned by the hook blocks a tool call." So if a hook errors out mid-test, the effect is "hook did nothing," not "tool call silently blocked." Combined with the point above, there is no fail-closed hook in this repo that could make an X search vanish without an explicit, visible deny reason in stderr.

**Is there a way to run `grok -p` with no project config?** I did not find a dedicated flag (checked the full `grok --help` output; no `--no-project-config`, `--isolated`, or similar). The practical control, already validated above with `grok inspect`, is **`--cwd <path outside the repo>`** (or literally invoking from a scratch/empty directory) — that alone drops Project Instructions from 4 to 2, project Skills from 17 to 0, and project Hooks from 2 to 0. `~/.grok/docs/user-guide/08-skills.md:186-188` also documents `--system-prompt-override`/`--system-prompt` as a way to replace the whole system prompt (skipping the default prompt and any `--rules`), but that is a blunter tool — the doc does not describe it as suppressing AGENTS.md/skill discovery specifically (Project Instructions are loaded and injected as part of session start, described separately in `12-project-rules.md`, not solely as "the system prompt"), so `--cwd` to a clean folder is the cleaner, already-precedented control (`reviews/ui-direction.md:115`: "Tested on a throwaway copy in a scratch folder").

**Control for section 2:** for every prompt arm in the pilot (P7) and Stage 1, run it twice — once at `cwd=ROOT` (today's real setup, what the factory actually uses) and once at `cwd=<clean scratch dir>` — and diff the tool calls each makes. If `format-tool-swap` (or any other un-gated skill) fires in the ROOT run and not the clean run, that's the confound made visible, not inferred.

---

## 3. Skills that tell agents how to search — keyword-only or website-syntax pushes

- `.claude/skills/next/SKILL.md:46`: `"how do I" free video editor lang:en -filter:replies` is given as an example query, then: "with `python3 scripts/x_read.py search \"<query>\"`. It checks every post Grok returns against X and drops invented or misquoted ones; never cite a post it dropped, and **don't use `x_keyword_search` directly**, because it skips that check." This teaches two things at once: (a) build queries with X's own search operators (`lang:en`, `-filter:replies`) — syntax written for X's web/API search grammar, not necessarily how `x_keyword_search`'s underlying tool parses free text — and (b) always go through the wrapper, never call the tool directly. Because `next` has `disable-model-invocation: true` (`.claude/skills/next/SKILL.md:7`), this only applies when a session explicitly runs `/next`, not to a bare discovery-test prompt — but the discovery test's own harness (`scripts/x_read.py`) *is* this wrapper, so if the test calls `x_read.py` for its "G-steered" arm, it inherits this exact operator-syntax style by construction, and it's worth checking in the docs step (G6) whether `x_keyword_search`'s query parser actually honours `-filter:replies`/`lang:en`-style operators or silently treats them as plain keywords — if the latter, queries built this way may already be quietly worse than they look. **[inference — unverified whether the tool accepts these operators; that's exactly G6/G7 territory.]**
- `.claude/skills/format-tool-swap/SKILL.md:48`: "check with `python3 scripts/x_read.py search \"<query>\"`, **never a raw Grok search**." As covered in section 2, this skill is model-invocable and its trigger phrase overlaps the plan's own Demand idea card wording.
- `.claude/skills/format-tool-swap/checklist.md:5`: "checked with `x_read.py search`" — same pattern, in a checklist copied into drafts; lower risk since checklists aren't loaded as skills Grok would auto-invoke mid-search, but shows the convention is repeated in multiple places a future session might read.
- I did not find any other skill (`draft-thread`, `verify-settings`, `format-build-log`, `format-comparison`, `format-single-tip`, `format-tool-verdict`, `hidden-settings`, `posted`, `ready`, `results`, `snapshot`, `undo-rule`, `apply`, `approve`) that mentions `x_read`, `grok`, `x_keyword_search`, or `x_thread_fetch` — the grep across `.claude/skills/` came back with only the four hits already quoted above (plus one incidental mention of "Grok" in `format-tool-verdict` describing it as an example tool being reviewed, not an instruction about search).

**Control for section 3:** for the pilot, don't let the discovery-test prompts reuse the exact idea-card wording verbatim in a way that collides with `format-tool-swap`'s `when-to-use` string — either phrase the Demand-1 prompt differently, or explicitly run that one arm from a clean `cwd` to rule the skill out, or check the tool-call log for a `Skill`/`format-tool-swap` invocation before trusting the result as "G-free."

---

## 4. Other settings that could affect results

- `~/.grok/config.toml:6-7`: `[models] default = "grok-build"`, `web_search = "grok-4.5"`. No API keys or secrets present in this file (confirmed by full read — only these two model ids, marketplace source, UI prefs, and an ack timestamp). As discussed in section 1, the session default model is not necessarily the model used for X-specific search tools; unresolved, flagged for the docs step.
- `~/.grok/config.toml:20,22`: `yolo = false`, `permission_mode = "ask"` — these are TUI defaults; `grok_read.py` doesn't rely on them since it runs headless with explicit `--sandbox`/`--deny` flags and no interactive approval needed for read-only tools.
- `~/.grok/config.toml:33`: `[memory_v2] enabled = true` — cross-session memory is on. **[inference]** If Grok's memory feature persists anything from earlier factory sessions (e.g. prior `/next` or `/draft-thread` runs where it was told "don't use x_keyword_search directly" or saw the "never a raw Grok search" line), a later discovery-test prompt in the same account's memory scope could be influenced by that even outside this repo's cwd. I did not read the memory store itself (out of scope / not one of the excluded-but-also-not-requested directories, but reading its contents wasn't necessary to flag the mechanism) — worth a "run with memory disabled / fresh account" check if results look inconsistent between sessions.
- No `.grok/` directory exists inside the thread-engine repo itself (`.grok/config.toml`, `.grok/skills/`, `.grok/hooks/` etc. per `~/.grok/docs/user-guide/08-skills.md`'s location table) — confirmed by listing the repo root; the project only carries `.claude/`. So every project-level effect documented above comes through Grok's **Claude-compatibility** scanning (`[claude]` tags throughout the `grok inspect` output), not a Grok-native project config. That compatibility scanning is on by default per `~/.grok/docs/user-guide/08-skills.md` and is what makes `.claude/skills/*`, `.claude/settings.json` hooks, and `CLAUDE.md`/`AGENTS.md` all visible to Grok even though this is nominally a Claude Code project.
- Environment variables: I did not print any (per "read only; do not print secrets" and to avoid exposing `XAI_API_KEY`/session tokens). `~/.grok/docs/user-guide/05-configuration.md:806` documents `GROK_SANDBOX` as an env var that can override the sandbox profile — if that variable happens to be set in the shell the test runs from, it would override the `--sandbox read-only` flag `grok_read.py` passes explicitly (env vars sit below CLI flags in the precedence order per `05-configuration.md:11-14`, so a CLI `--sandbox` flag wins regardless — low risk, noted for completeness).

---

## 10-line summary

1. `scripts/x_read.py`'s `search_prompt` (line 44) forces exactly one `x_keyword_search` call, "Latest" mode, limit 10, on the literal query given — ruling out semantic search, relevancy sort, and reformulation. This is the source of the bias the plan's "Grok prompting" section already suspects.
2. `scripts/grok_read.py` (line 38-41) also pins `--effort low` on every call and never sets a model, so every past "Grok is weak" impression from this repo was formed at low effort and on the CLI's default `grok-build` model, not necessarily its best search model.
3. `--sandbox read-only` is a filesystem restriction, not a network one (per `~/.grok/docs/user-guide/18-sandbox.md`) — it should not be blocking or throttling X search calls.
4. `x_read.py`'s id + text-match check (`same_text`, line 60) can drop a real, paraphrased post as "invented" — treat a high drop rate as a possible scoring artifact, not proof Grok fabricated posts.
5. Because `grok_read.py` runs with `cwd` = repo root, every call auto-loads AGENTS.md, CLAUDE.md, and all 17 `.claude/skills/*` (verified with `grok inspect`); a clean/empty `cwd` drops that to 2 instructions and 0 project skills — that's the control to run in parallel.
6. Most command skills (`next`, `apply`, `snapshot`, etc.) set `disable-model-invocation: true` and can't fire unasked; but `format-tool-swap` and 8 other format/verify/draft skills do not, so Grok can invoke them on its own — already observed once (`reviews/ui-direction.md:119`).
7. `format-tool-swap`'s trigger phrase ("free alternatives") nearly matches the plan's own Demand idea card 1 wording, and that skill explicitly says "never a raw Grok search" — a real risk of silently steering a "G-free" test prompt back into keyword-only search.
8. The PreToolUse guard hook explicitly exempts every `x_`/`web_`-prefixed tool (line 70) and only ever fires as a deny, never a silent block — it is not a confound for search behaviour.
9. No CLI flag suppresses project config outright; the working control is `--cwd` to a directory outside the repo (or a scratch copy), which is already how the one prior CLI test in this repo was done.
10. `~/.grok/config.toml` (no secrets found) shows a separate model routing for the built-in `web_search` tool (`grok-4.5`) versus the session default (`grok-build`) — whether X-specific search tools follow the same or the session-default model is unresolved and belongs in the planned docs step (G6).
