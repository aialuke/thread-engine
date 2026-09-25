# thread-engine: the system as it exists today

Written for an Opus agent planning a button UI (iPhone first, then Mac) on top of this
command-line system. Everything below is read from the repo at
`/Users/lukemckenzie/src/thread-engine` as of 2026-09-25, plus operator notes explicitly
given to the writer (marked **[operator note]**). No file was changed to produce this.

---

## 1. Runtime topology today

**Everything runs on one Mac**, in a normal user login session (not headless, not a server).
There is no backend, no daemon except the launchd job below, no database except flat JSON
files and git.

**Two agent CLIs read the same project**, both driven by the operator typing slash commands
(`AGENTS.md:9` — "The operator does not code or run scripts. Every step is a slash command,
typed in Grok or Claude Code. Scripts exist, but the agent runs them."):

| Tool | Reads | Runs |
|---|---|---|
| Claude Code | `.claude/skills/*/SKILL.md`, `.claude/settings.json`, `AGENTS.md` | Any skill/command. Has Bash access gated by `.claude/settings.json` permissions and the `PreToolUse` hook. |
| Grok Build | same `.claude/skills/` and `AGENTS.md` (`AGENTS.md:41`: "Grok and Claude Code both load `.claude/skills/`") | Same skills. Grok is also the only path to reading *other people's* X posts (`scripts/x_read.py` → `scripts/grok_read.py`, which shells out to a local `grok` binary at `~/.grok/bin/grok` in a read-only sandbox with `--deny Bash --deny Edit --deny Write`). |

Both tools' hooks are configured once, in `.claude/settings.json` (`.claude/settings.json:1-28`):
a `UserPromptSubmit` hook (`approve.py`) and a `PreToolUse` hook (`guard_approved.py`), plus a
Bash allowlist for the five scripts and `WebFetch(domain:github.com)`.

**The one scheduled job** is a macOS `launchd` `StartCalendarInterval` agent
(`ops/launchd/com.exitzerocode.thread-engine.snapshot.plist:24-30`): runs `scripts/snapshot.py`
daily at **20:00 local time** (Hour 20, Minute 0), `RunAtLoad=false` (does not fire on
install/login, only at the scheduled time or on wake if the Mac was asleep at 20:00 — comment
at plist:8-9). It `cd`s into the repo and shells out via `/bin/zsh -lc`. Output and errors both
go to `~/Library/Logs/thread-engine-snapshot.log` (plist:31-34). README.md:54 says the operator
must ask Claude Code to install it (copy to `~/Library/LaunchAgents/` and `launchctl load`) —
**this is a one-time manual/agent-driven install step, not something the repo does itself.**

**The Keychain.** X API keys live in macOS Keychain, service `thread-engine-x`
**[operator note]**, accounts `consumer_key`, `consumer_secret`, `access_token`,
`access_token_secret`, `bearer_token` **[operator note]** (the code only names four:
`scripts/x_api.py:46` `KEY_NAMES = ("consumer_key", "consumer_secret", "access_token",
"access_token_secret")` — `bearer_token` exists in the Keychain per the operator but is not
read by any script found in this repo). Only `scripts/x_api.py` reads them
(`scripts/x_api.py:84-89`, via `security find-generic-password -s thread-engine-x -a <name> -w`),
in its own subprocess; the hook never sees them (`.claude/hooks/guard_approved.py:8`).
`python3 scripts/x_api.py keys` checks presence only, no values
(`scripts/x_api.py:92-99`, no `-w` flag). Access level is **read-only**: X returns
`x-access-level: read` on every response and the client raises if it ever sees anything else
(`scripts/x_api.py:171-175`). The guard hook additionally blocks any shell command matching
`security find-(generic|internet)-password|dump-keychain` outright
(`.claude/hooks/guard_approved.py:36,79-81`), so an agent cannot try to read the keys itself
even via a raw `security` call.

**What needs the network:**
- `scripts/x_api.py` — the account's own X data. HTTPS to `api.x.com` (`scripts/x_api.py:44`).
- `scripts/grok_read.py` — shells out to a local `grok` binary, which itself needs network to
  reach Grok/X (this repo has no visibility into what Grok's own network calls look like).
- `scripts/loop.py` — **no network** (module docstring, `scripts/loop.py:8`: "No network
  access. Git is used only by commit-rule, undo and commit-data.").
- `scripts/post_thread.py` — **no network in v1**. It writes `POST.txt` and copies to the
  clipboard via `pbcopy` (`scripts/post_thread.py:303-304`); posting to X is commented-out
  future code (`post_thread.py:389-399`) and `--no-dry-run` currently just prints
  "v1 does not call the X API" and exits 1 (`post_thread.py:412-414`). A test enforces this has
  no HTTP imports (`tests/test_scripts.py:74` `test_post_thread_has_no_http_imports`).
- `scripts/draft.py` — no network; it only prints a `grok -p "..."` command string
  (`scripts/draft.py:30`) and does not invoke it (module docstring: "does not start grok").

**What the iPhone can do today: nothing.** There is no mobile app, no remote API, no web
server, no push mechanism. The entire system is local scripts run by an agent CLI on the
Mac, triggered by the operator typing on that Mac (or, for Grok, presumably also local). Any
iPhone UI is new work with no existing surface to attach to except by remoting into the Mac
session (e.g. driving Claude Code/Grok CLI remotely) or building a new API layer in front of
these scripts. `pbcopy`/Finder-reveal (`post_thread.py:307-308`, `open -R`) are Mac-only
UI affordances the current `/ready` flow depends on (see §5).

---

## 2. Command table

All commands are skills under `.claude/skills/<name>/SKILL.md`, invoked as `/name arg` by the operator, in either Claude Code or Grok. `disable-model-invocation: true` is set on `next`, `ready`, `posted`, `results`, `apply`, `undo-rule` and `snapshot`, so the model can't start those on its own. **It is not set on `draft-thread` or `verify-settings`**, so a model can invoke those itself. A headless runner can't rely on the flag as its authorisation model; it needs its own rule for which commands a trigger may start.

### CMD-NEXT — `/next`
**Does:** Catches up snapshots and the weekly review, then proposes one post.
**Steps** (`.claude/skills/next/SKILL.md`):
1. Run `python3 scripts/snapshot.py` unconditionally (idempotent same-UTC-day, §1:16).
2. Run `python3 scripts/loop.py status`.
3. Read tail of `ledger/runs.log`; if last run failed or is >30h old, say so with likely cause
   (Mac off/locked, or API credits exhausted).
4. Summarize changes in 2-3 lines, plus one line of Rewards progress from `ledger/SUMMARY.md`.
5. **If `review.review_due` is true:** runs the whole CMD-RESULTS flow (§ below), then an
   algorithm-freshness check against `reference/x-algorithm.md`, calling
   `python3 scripts/loop.py set-reference --status stale --files <paths>` or `--status current`.
6. **Slot selection:** experiments are paused (operator rule, until 2 weeks of organic data).
   Runs `python3 scripts/loop.py next-slot`. Proposes the next unopened experiment from a fixed
   ordered list of 6 candidate experiments (skill:32-38) *only once the pause lifts*; until then
   skips straight to proposing a post with no experiment arm.
7. **Topic pick:** reads `reference/audience.md` for lane share; runs 1-2
   `python3 scripts/x_read.py search "<query>"` calls for demand leads; checks
   `queue/topics.yaml` `status: queued` rows; proposes a posting time in
   Australia/Brisbane (cap: 2 originals/day, hours apart).
8. **Proposes** one post in 4 lines (topic, format, experiment arm, posting time) + one-sentence
   why. On operator accept/edit, writes/updates the `queue/topics.yaml` row with fields: slug,
   status: planned, format, lane, experiment, arm, treatment, hypothesis, post_at, leads.
9. **Replies section:** finds 2-3 reply-worth conversations via `x_read.py search`, each with a
   link + one-line talking point — **never paste-ready text** (skill:74, algorithm fact A12).
10. Ends with literal text: `Next: /draft-thread <slug> (start with /plan if you want to review the plan first).`

**Scripts run:** `snapshot.py` (no args), `loop.py status`, `loop.py next-slot`,
`x_read.py search "<query>"` (1-2x, plus 2-3x for replies), and conditionally
`loop.py set-reference`, `loop.py open-experiment --json loop/inbox/experiment.json` (only on
operator "yes" to a proposed experiment, once pause lifts).

**Files read:** `ledger/runs.log`, `ledger/SUMMARY.md`, `reference/audience.md`,
`reference/x-algorithm.md`, `queue/topics.yaml`.
**Files written:** `queue/topics.yaml` (row update — **this file is committed** but not via
`loop.py`; the skill just edits it directly. No hook blocks this — `queue/topics.yaml` is not
in the `LOOP_STATE` regex, `.claude/hooks/guard_approved.py:34-35`). If opening an experiment,
also `loop/inbox/experiment.json` (scratch).
**Operator questions:** implicit yes/no/edit on the proposed post and, if applicable, on the
proposed experiment and on each reply lead. No literal quoted question string in the skill text
itself beyond the two composed by CMD-RESULTS if a review runs this cycle (see below).
**Exit codes / refusals:** none of its own; inherits `snapshot.py`'s exit 1 on API failure
(reported in prose, not surfaced as a raw exit code to the operator).
**Network:** `snapshot.py` → X API (cost logged, see §6 runs.log); `x_read.py search` → one
Grok call each, plus an X API lookup-by-id to verify every returned post
(`scripts/x_read.py:68-86`, ~$0.005/post via `x_api.lookup`).
**Duration:** not stated in repo; involves a full snapshot run plus up to ~5 Grok calls, so
likely tens of seconds to a few minutes depending on Grok latency.
**UI observation points (D4 working line / completion):** the natural progress beats are
(a) "running daily snapshot" → parse `snapshot.py` stdout lines (it prints
human-readable progress lines, see §3), (b) "checking loop status", (c) "searching for demand
leads" (N of ~5 Grok calls), (d) "here's the proposed post" (final proposal text) as the
completion signal. There is no structured/JSON "phase" marker emitted by the skill itself —
a UI would need to parse the prose the agent produces, or instrument the underlying script
calls (which *do* emit JSON — see §3) as the true progress signal.

### CMD-DRAFT — `/draft-thread <slug>`
**Does:** Writes the draft in its format into `drafts/YYYY-MM-DD-slug/`.
**Steps** (`.claude/skills/draft-thread/SKILL.md`):
1. Read contract files: `AGENTS.md`, `voice/exit-zero.md`, `reference/audience.md`,
   `reference/x-algorithm.md`, `queue/topics.yaml`.
2. Find the queue row (bare arg → `status: planned` row, else first `status: queued`).
3. Read `.claude/skills/format-<format>/SKILL.md` and everything it points to (for `settings`,
   also `.claude/skills/hidden-settings/examples.md` and gold `examples/*.md`).
4. **Research** per the format's rule; **stops and asks the operator** for `build-log` /
   `tool-verdict` Material questions (quoted below, §"Format tables") if no real proof exists.
   For `tool-swap`, offers an optional test **once**, never as a gate.
5. Runs `/verify-settings <folder> [paths|claims|both]` (a separate skill, invoked as a
   sub-step) — writes `PATHS.md` and/or `CLAIMS.md`.
6. Writes the draft folder: `FORMAT`, `01-hook.md` + `NN-name.md` cards, `REPLIES.md` (tool-swap
   only), `images.md`, `CHECKLIST.md` (copied from the format skill's `checklist.md` with boxes
   ticked).
7. Sets the queue row `status: drafted`, `draft:` to the folder path.
8. **Never creates/edits/deletes `APPROVED`** — enforced by the guard hook regardless.
9. **Preview:** prints every card, `---`-separated, with `python3 scripts/post_thread.py
   <folder> --count` character counts, leftover `VERIFY` rows, and `images.md` asks. Ends with
   exactly: `Read the cards. If you change any, that's fine. When they're right, type /approve
   <slug>. Then /ready <slug>.`

**Scripts run:** `post_thread.py <folder> --count` (needs no approval, writes nothing).
`verify-settings` is itself a skill, not a script — it's a research/fact-check procedure the
agent follows by hand (opening vendor pages), writing `PATHS.md`/`CLAIMS.md` as markdown by
hand. No script does the fact-checking.
**Files read:** the five contract files, the format skill, `examples/*.md` (settings only),
existing draft folder if reused.
**Files written:** `drafts/YYYY-MM-DD-slug/{FORMAT, 01-hook.md, ..., REPLIES.md, images.md,
CHECKLIST.md, PATHS.md, CLAIMS.md}`; `queue/topics.yaml` row (`status: drafted`, `draft:` path).
**Git commits:** none directly (drafts aren't committed by this skill; `APPROVED` is
gitignored, `AGENTS.md:63`).
**Questions to operator:** for `build-log`/`tool-verdict`, quoted verbatim
(`.claude/skills/format-build-log/SKILL.md:16-20`):
> "1. What did you build, run or change? What came out?
> 2. Which step or tool made it work (which agent did what)?
> 3. What broke, surprised you, or is still bad?
> 4. What real proof can you attach: a screenshot, screen recording or output file?"

and for `tool-verdict` (`.claude/skills/format-tool-verdict/SKILL.md:15`): "which tools, which
task, same input to each, how many runs, and what each produced." "No run, no verdict" /
"No real proof, no build log" are the hard stops if unanswered — the skill "offer[s] a
different format instead."
**Exit codes / refusals:** none of its own (the skill is prose-driven); `post_thread.py --count`
always exits 0 if the folder exists and has cards, 1 if not (`post_thread.py:372-378`).
**Network:** whatever `verify-settings` needs (WebFetch to vendor pages — the only allowlisted
domain in `.claude/settings.json` is `github.com`; other domains would need per-call approval
in Claude Code, or are open in Grok).
**Duration:** unbounded — real research/fact-check work, likely minutes.
**UI observation points:** natural phases are (1) reading contract, (2) researching/verifying
(the longest, most opaque phase — no intermediate machine-readable output), (3) writing files
(observable as new files appearing under `drafts/<slug>/`), (4) the printed preview + exact
closing sentence as completion signal (a fixed string, good for a UI to pattern-match on:
`"Read the cards. If you change any, that's fine. When they're right, type /approve <slug>. Then /ready <slug>."`).

### CMD-APPROVE — `/approve <slug>`
**Does:** Operator-only. Approves the cards exactly as they are now. **This is not a skill the
model executes** — it is intercepted entirely by the `UserPromptSubmit` hook
`.claude/hooks/approve.py` before the model ever sees the prompt
(`.claude/hooks/approve.py:2-8`; the `approve/SKILL.md` file exists only so Claude Code accepts
`/approve` as a known command instead of erroring "Unknown command" — `.claude/skills/approve/SKILL.md:12`).
**Mechanism** (`.claude/hooks/approve.py:34-77`):
1. Regex-matches the raw prompt text against `^/approve\s+([A-Za-z0-9-]+)\s*$` exactly
   (`approve.py:18`) — nothing else in the message.
2. Resolves the draft folder: exact `drafts/<slug>` dir, else glob `drafts/*-<slug>` excluding
   `_`-prefixed dirs (template). Zero matches or >1 match → **blocks** with a reason (no file
   written).
3. Computes `post_thread.cards_digest()` — SHA-256 over every numbered card's filename+bytes,
   in order (`post_thread.py:158-163`).
4. Writes `drafts/<slug>/APPROVED`:
   ```
   cards-sha256: <64-hex digest>
   approved-at: <UTC ISO stamp>
   approved-by: operator, typed /approve
   ```
5. Blocks the prompt (so the model never sees it) with the confirmation text:
   `"Approved {draft.name}: {N} card(s) as they are now. If any card changes, approve again. Next: /ready {slug}"`
6. On any exception, fails closed: blocks with `"Approval failed, nothing was approved: <detail>"` and approves nothing (`approve.py:74-77`).

**Files written:** only `drafts/<slug>/APPROVED`, always by this hook, never by the model
(the `PreToolUse` guard hook additionally denies any tool call whose path basename is
`APPROVED`, or whose shell command writes/touches/`>` to a path ending `/APPROVED`, or that
invokes `grok`/`claude`/`codex` with a prompt starting `/approve` — `guard_approved.py:37-44,
83-85`, tested by `tests/test_hooks.py:41-56`). **Note for a UI:** the guard's shell regex
`SHELL_MARKER_WRITE` matches *any* occurrence of `/APPROVED` in a shell command string, not just
write verbs — even `cat drafts/x/APPROVED` was blocked when this doc's author tried it live.
A UI/agent that needs to *read* `APPROVED`'s existence/contents should use a non-shell file-read
tool (e.g. `Read`, which is in the hook's `NO_WRITE` set, `guard_approved.py:28-32`) or `Path.is_file()`
in Python, never a shell `cat`/`ls`-with-glob-on-that-name via Bash.
**Exit codes:** N/A (hook prints JSON `{"decision": "block", "reason": ...}` to stdout and
exits 0 always — `approve.py:22-23`; this is a *prompt* block, distinct from the `PreToolUse`
hook's `deny` which for Claude Code exits 2, `.claude/hooks/guard_approved.py:47-50`).
**Network:** none. **Duration:** instant (regex + hash + file write).
**UI observation points:** trivial — an Approve button's entire job is to synthesize the literal
prompt text `/approve <slug>` and submit it as a real operator-typed prompt through whatever
channel the hook listens on (`UserPromptSubmit`). **D24 implication:** the build must ensure no
agent-driven path (a "fake" approve triggered by a button that isn't going through the real
`UserPromptSubmit` hook path, or an agent spawning a nested CLI invocation with `/approve` in
its prompt) can create this file — the hook already defends the CLI-nesting case
(`SHELL_NESTED_APPROVE`, `guard_approved.py:43-44`) but a *new* UI surface (e.g. a button that
calls some script directly) would bypass the hook entirely unless it is wired through the same
`UserPromptSubmit` mechanism.

### CMD-READY — `/ready <slug>`
**Does:** Runs the gate on an approved draft and copies its cards to the clipboard one at a
time.
**Steps** (`.claude/skills/ready/SKILL.md`):
1. Find draft folder (`drafts/*-<slug>` or the queue row's `draft:`).
2. Run `python3 scripts/post_thread.py <folder>` (no `--copy`, so it also (re)writes `POST.txt`).
   - **Exit 2** (`"human gate"` printed to stdout) → say "Not approved yet. Read the cards, then
     type /approve <slug>." and stop.
   - **Exit 1** → turn each `REFUSED:` stderr line into plain English (what's wrong, which card,
     the fix); "cards changed after approval" → re-read and retype `/approve <slug>`; never
     touch `APPROVED`; stop.
   - **Exit 0** → continue.
3. Show the run sheet (post count, each card's X-counted length, attachments).
4. Run `python3 scripts/post_thread.py <folder> --copy 1`. Tell operator card 1 is on the
   clipboard, to post as a new post; name any attachment (Finder has it selected via `open -R`).
5. On each operator `"next"`, run `--copy N` for the next card, framed as "post as a reply to
   card N-1". For tool-swap, when `--copy 1`'s output includes a `wait:` line, tell the operator
   to wait 10-20 minutes before the shout-out.
6. After the last card: "When it's all live, type /posted <link to the first post>."

**Scripts run:** `post_thread.py <folder>` (writes `POST.txt`), then `post_thread.py <folder>
--copy N` once per card (N=1..len(cards)), each of which **re-writes `POST.txt`** too
(`post_thread.py:416-417` runs unconditionally before the `--copy` branch).
**Files read:** every numbered card file, `APPROVED`, `FORMAT`, `images.md`.
**Files written:** `POST.txt` (every invocation, even `--copy`). No git commit.
**Operator prompts quoted verbatim above.** No question asked except waiting for `"next"`.
**Exit codes:** 2 = human gate (no `APPROVED`); 1 = refused (see §5 for the full refusal list,
shared with this gate) or bad `--copy N` (`post_thread.py:400-402`) or missing folder
(`post_thread.py:368-370`) or no numbered cards (`post_thread.py:385-387`); 0 = success.
**Network:** none. `--copy` uses **`pbcopy`** (macOS clipboard, `post_thread.py:303-304`,
`subprocess.run(["pbcopy"], ...)`) and **`open -R`** to reveal a media file in Finder
(`post_thread.py:307-308`, `subprocess.run(["open", "-R", str(path)])`). **Both are macOS-only
system calls with no iOS equivalent** — a mobile UI needs its own clipboard/share-sheet
mechanism to replace these two calls; they are the concrete blocker for "the same script works
on iPhone."
**Duration:** near-instant per `--copy` call; the whole flow is paced by the operator manually
pasting into X between calls (minutes, human-paced).
**UI observation points:** exit code from `post_thread.py <folder>` (no `--copy`) is the
canonical readiness signal (0/1/2 — cleanly machine-checkable, unlike most of this system). Per
card: which card number is "on the clipboard" now, and whether a `wait:` line was present
(tool-swap shout-out timer — a UI could literally implement a 10-20 min countdown timer off
this signal, `post_thread.py:322-324`, string `SHOUTOUT_WAIT` at `post_thread.py:49`).

### CMD-POSTED — `/posted <link>`
**Does:** Records a live post in the ledger.
**Steps** (`.claude/skills/posted/SKILL.md`):
1. Extract root id from URL (`/status/<id>`).
2. Run `python3 scripts/x_api.py thread <root id>` — the root + the account's own thread cards
   in order (id, time, text, media). Save raw output to `ledger/raw/<root id>-posted.txt`.
3. Match the queue row (`status: approved` or `drafted` whose cards best match); ask the
   operator if unsure which slug.
4. Diff every live card vs draft card; classify each difference as `preference` / `correction`
   / `deviation` / `violation` (definitions quoted in skill).
5. Ask operator: `"Roughly how many minutes did this one take, start to finish?"`
6. Write `loop/inbox/post-<root id>.json` (exact JSON shape quoted in the skill, `posted/SKILL.md:23-30`):
   fields `root_id, slug, format, lane, posted_at, made_in_repo, retrospective, experiment, arm,
   hypothesis, cards[{id,text}], media, ai_media, production_minutes, edits[{class,card,note}],
   draft`.
7. Run `python3 scripts/loop.py record-post --json loop/inbox/post-<root id>.json`. If it says
   "already recorded" (because the daily snapshot auto-recorded it first under slug `x-<id>`,
   this record **replaces** it and keeps its existing snapshots — `loop.py:355-361`), say so and
   stop; otherwise this call also **commits data implicitly? No** — `record-post` itself does
   not commit; commits happen via `commit-data` elsewhere (see loop.py table, §3).
8. Set queue row `status: posted`, `root_id: <id>`.
9. Tell operator when the 36-60h snapshot is due, and list any `violation` (never learned as a
   preference).

**Scripts run:** `x_api.py thread <root_id>`, `loop.py record-post --json <file>`.
**Files read:** the queue row candidates, the live thread via API.
**Files written:** `ledger/raw/<root_id>-posted.txt`, `loop/inbox/post-<root_id>.json`,
`ledger/<root_id>.json` (via `loop.py record-post`, which also triggers `render()` — rewrites
`ledger/SUMMARY.md`, `experiments.md`, `learnings.md`, since `record-post` is not in
`loop.py`'s `READ_ONLY` set, `loop.py:1201,1250-1251`), `queue/topics.yaml` (status/root_id).
**Git commits:** none directly from this skill (data commits happen via the daily snapshot's
`commit-data` or the weekly review's `commit-data`, not per-post).
**Exit codes:** `loop.py record-post` exits 1 with `{"error": ...}` on validation failure (bad
format, bad lane, arm/experiment mismatch, etc. — `loop.py:212-230`), 0 + JSON otherwise.
**Network:** one `x_api.py thread` call (owned-read-rate, $0.005/post + $0.010/author scale per
`reference/x-api.md` P3/P14 — actually `thread()` internally calls `timeline()`, an **owned**
read at $0.001/item, `x_api.py:242-253`, `OWNED` rate).
**Duration:** seconds (one API call) plus operator's one-word answer.
**UI observation points:** completion = queue row `status: posted`; the "violation" list is the
one thing a UI should surface prominently, since violations block future adoption as preference
rules.

### CMD-RESULTS — `/results`
**Does:** Shows numbers now, or writes the weekly review when due.
**Steps** (`.claude/skills/results/SKILL.md`, 7 top-level steps, each with sub-detail):
1. If a fresh X analytics export CSV exists in `~/Downloads`
   (`account_analytics_content_*.csv`), move newest into `loop/inbox/` and run
   `python3 scripts/loop.py record-export --csv loop/inbox/<file>`. If none from last 7 days,
   ask operator once to export it (quoted path: "X on a computer → Premium → Analytics →
   Content → Export, last 7 days").
2. Weekly: ask operator for X's eligibility-screen numbers (verified followers, qualified
   impressions), record via `loop.py record-eligibility --verified-followers <n>
   --qualified-impressions <n>`. Operator may decline and fall back to daily-read numbers.
3. Run `loop.py status` and `loop.py evaluate`; read `ledger/SUMMARY.md`, `experiments.md`,
   `learnings.md`, last `reviews/week-*.md`.
4. If operator only wanted numbers (no review due): print last 7 days of `ledger/SUMMARY.md` as
   a table and stop.
5. Otherwise, **writes `reviews/week-YYYY-Www.md`** with 13 named sections (Rewards progress,
   Posts this week, Followers, Replies, Experiment, Lane, Spacing, Your edits, Reader questions,
   Lanes to review, Rule changes proposed [max 2], Reverts proposed, Profile, PAID → FREE
   runway) — full detail in the skill file; each ties to specific `loop.py` read/write calls
   documented inline (`add-preference`, `set-lane`, `mark-nonorganic` implicitly via violation
   review, etc.).
6. Run `python3 scripts/loop.py mark-reviewed`, then `python3 scripts/loop.py commit-data
   --message "weekly review YYYY-Www"`.
7. Tell operator the three most important things in three sentences + where the full review is.

**Scripts run:** `loop.py record-export`, `record-eligibility`, `status`, `evaluate`,
`mark-reviewed`, `commit-data`; `x_api.py mentions`, `x_api.py me`; potentially `add-preference`,
`set-lane` on operator yes.
**Files read:** `~/Downloads/account_analytics_content_*.csv` (Mac-only path — **an iPhone UI
has no equivalent local Downloads folder to poll**, so this step needs a re-think for mobile —
e.g. a file picker / share-sheet import of the CSV), `ledger/SUMMARY.md`, `experiments.md`,
`learnings.md`, `reviews/week-*.md`, `ledger/activity/*`.
**Files written:** `reviews/week-YYYY-Www.md` (new file, git-committed via `commit-data`),
`loop/state.json` (`last_review_at`, via `mark-reviewed`), `ledger/SUMMARY.md` /
`experiments.md` / `learnings.md` (regenerated by `render()` as a side effect of any non-read-only
`loop.py` command in this flow).
**Git commits:** yes — `loop.py commit-data --message "weekly review YYYY-Www"` stages
`ledger, loop, reviews, experiments.md, learnings.md, queue, reference` (whichever exist) and
commits as `chore(data): weekly review YYYY-Www` (`loop.py:928-936`).
**Exit codes:** each `loop.py` subcommand: 1 + `{"error":...}` on `LoopError`, else 0 + JSON.
**Network:** `x_api.py mentions` (owned read), `x_api.py me` (user read, $0.010).
**Duration:** the full weekly path is the longest single command in the system — reading
several files, computing multiple sections, writing a multi-hundred-line markdown review;
likely minutes.
**UI observation points:** best granularity is per numbered section (13 sections is a good
progress-bar cardinality); completion = the review file exists at
`reviews/week-YYYY-Www.md` + `loop/state.json.last_review_at` updated + the commit SHA from
`commit-data`.

### CMD-APPLY — `/apply <lesson id>`
**Does:** Makes the rule change a weekly review proposed for an `adopted` lesson.
**Steps** (`.claude/skills/apply/SKILL.md`):
1. Read `learnings.md`; lesson must be `adopted` with `rule: none`, else say why not and stop.
2. Find the proposed change in the latest `reviews/week-*.md`; show operator the change + file.
3. Edit **only** that one file, restricted to `.claude/skills/` or `voice/`
   (enforced by `loop.py commit_rule`'s own check, `loop.py:892-894`, not just the skill's
   self-restraint) — "Never touch APPROVED, the gate script, AGENTS.md, or the truth budget."
4. Run `python3 scripts/loop.py commit-rule --lesson <id> --files <path>`.
5. Say: `"Applied <id>. Drafts follow it from now on. Type /undo-rule <id> to take it back."`

**Scripts run:** `loop.py commit-rule --lesson <id> --files <comma-separated>`.
**Files written:** the one rule file (edited directly by the agent, not via loop.py), then
committed by `loop.py` itself via `git add`/`git commit`.
**Git commits:** `feat(rules): apply <lesson id>\n\n<statement>\nEvidence: <ids>`
(`loop.py:898`), SHA recorded into `loop/state.json.rules[]`.
**Exit codes:** `commit-rule` raises `LoopError` (exit 1) if: lesson not `adopted`
(`loop.py:889`), `--files` empty (`loop.py:891`), a file path escapes the repo or isn't under
`.claude/skills/`/`voice/` (`loop.py:893-894`), or there's nothing to commit
(`git status --porcelain` on those files is empty, `loop.py:895-896`).
**Network:** none. **Duration:** seconds.
**UI observation points:** completion = new commit SHA + `loop/state.json.rules[]` entry with
`undone: false`.

### CMD-UNDO — `/undo-rule <lesson id>`
**Does:** Reverts the rule change made for a lesson.
**Steps** (`.claude/skills/undo-rule/SKILL.md`):
1. Run `python3 scripts/loop.py undo --lesson <id>`.
2. Success → `"Reverted <id>. Drafts are back to the rule before it."`
3. Error → plain sentence: "Uncommitted edits" (someone changed the rule file since — ask
   whether to keep those edits first) or "Conflicted" (a later change touched the same lines —
   nothing changed; needs a Claude Code session to fix by hand).

**Scripts run:** `loop.py undo --lesson <id>`.
**Mechanism** (`loop.py:908-925`): finds the most recent non-undone `rules[]` entry for that
lesson; refuses if the rule files have uncommitted changes (`git status --porcelain` non-empty
→ `LoopError("... uncommitted edits ...")`); else `git revert --no-edit <commit>`; on revert
conflict, runs `git revert --abort` and raises `LoopError("revert of <sha> conflicted with a
later change; nothing was reverted")`; on success, marks `rule.undone=True`,
`lesson.rule_state="reverted"`.
**Git commits:** a `git revert` commit of the original apply commit.
**Exit codes:** 1 + `{"error":...}` on either failure mode; 0 + JSON with `reverted`,
`revert_commit`, `lesson` on success.
**Network:** none. **Duration:** seconds.

### CMD-SNAPSHOT — daily snapshot (`ops/launchd` job; also step 1 of `/next`)
**Does:** Reads the account's own posts, replies, followers and mentions from the X API and
records them in the ledger.
**Skill wrapper** (`.claude/skills/snapshot/SKILL.md`): run `python3 scripts/snapshot.py`,
relay its lines in plain words; failures are reported with cause (Keychain/credit error →
operator must unlock Mac or top up credits).
**Full mechanism** (`scripts/snapshot.py`, `run()` at line 179):
1. Read `loop.py status`'s `api` cursors (`read48_until`, `final_until`).
2. Compute three windows: 36-60h-old items (`read_from`/`read_to`), 26+-day-old items
   (`final_from`/`final_to`), and mentions since the last mention id.
3. Fetch followers, the 48h-window timeline, the final-window timeline, mentions — **all via
   one `x_api.Client()`** instance so usage/cost accumulate together.
4. **On any `XApiError`/`RuntimeError`:** logs `"<ts> snapshot failed error=<msg>"` to
   `ledger/runs.log`, prints `"The X read failed, so nothing was recorded and nothing moved on:
   <exc>. The next run picks the same posts up."`, returns exit 1. **Nothing is written, no
   cursor moves** — this is the load-bearing idempotency/safety property of the whole daily job.
5. On success, writes the raw API response to `ledger/raw/api/run-<timestamp>.json` (gitignored
   per `AGENTS.md:46` — "other people's data").
6. Calls `process()` (line 98) which, per item: auto-records any post/reply/quote not yet in the
   ledger as a retrospective `x-<id>` row (lane `other`, format `other`) via `loop.py
   record-post`; records a snapshot via `loop.py record-snapshot`; flags non-organic posts
   (>10% gap between public and organic impressions) via `loop.py mark-nonorganic`; records
   activity rows via `loop.py record-activity`; marks missed snapshots via `loop.py mark-missed`;
   runs `loop.py evaluate` for any open experiment.
7. Logs success line: `"<ts> snapshot ok read48=<n> final=<n> followers=<n> api_items=<n>
   cost_usd=<n>"` to `ledger/runs.log`.
8. Runs `loop.py commit-data --message "snapshots <date>"` — **this commits `ledger/`, `loop/`
   (but `loop/inbox`, `loop/followers` are gitignored so effectively only `loop/state.json`),
   `reviews/`, `experiments.md`, `learnings.md`, `queue/`, `reference/` if they have staged
   changes**.
9. Prints all accumulated plain-English lines + estimated cost.

**Also supports `--ingest <path>`:** records a one-time backfill file (from
`x_api.py backfill`) as a single "backfill" read, sets cursors from it, logs
`"<ts> snapshot ingest <path> items=<n>"`, commits.

**Scripts run:** `x_api.py` (via `x_api.Client`, not subprocess — imported directly,
`snapshot.py:30`), `loop.py` (via `subprocess.run([sys.executable, "scripts/loop.py", ...])`,
`snapshot.py:38-43` — every `loop.py` call from `snapshot.py` is a genuine subprocess, not an
import).
**Files written:** `ledger/raw/api/run-<ts>.json`, `ledger/<id>.json` (new auto-recorded posts),
per-post snapshot arrays inside those files, `ledger/activity/YYYY-MM.json`,
`ledger/activity/account.json`, `loop/followers/followers-<date>.json` (keeps only last 2,
`loop.py:575-576`), `loop/followers/interactions.json`, `loop/state.json.api` cursors,
regenerated `ledger/SUMMARY.md`/`experiments.md`/`learnings.md`.
**Git commits:** `chore(data): snapshots <date>` or `chore(data): ingest <filename>`.
**Exit codes:** 0 success, 1 on API failure (nothing recorded).
**Network:** yes — this is the main network-cost driver. Per `reference/x-api.md`: owned reads
(own timeline, mentions, followers) at $0.001/item; user reads at $0.010; costs logged per run
in `ledger/runs.log` (see actual numbers in §6). **Observed runs.log costs:** $0.265 (initial
backfill, 256 items), then daily runs of $0.037, $0.047, $0.036, $0.036 — i.e. **well under the
README's "$0.25/day" estimate** in steady state (`README.md:55`).
**Duration:** not logged explicitly; bounded by X API pagination (`MAX_PAGES=50`,
`x_api.py:50`) and one `RETRY_SECONDS=20` backoff on transient errors
(`x_api.py:51,163-169`) — likely well under a minute for the item counts seen so far (tens of
items/day).
**UI observation points:** the `ledger/runs.log` line format is the single best
machine-parseable progress/health signal in the whole system — a UI's "last sync" status
widget should tail this file. Pattern: `snapshot (ok|failed) read48=N final=N followers=N
api_items=N cost_usd=N.NNN` or `error=<msg>`.

### CMD-VERIFY — `/verify-settings <slug> [paths|claims]`
**Does:** Fact-checks a draft against current official pages; fails closed.
**Steps** (`.claude/skills/verify-settings/SKILL.md`) — a **prose research procedure**, not a
script:
- **Paths mode** (default): version-assumption pass over candidates → open official vendor docs
  → write `drafts/<slug>/PATHS.md` as a table (`Setting | Path | Source URL | Date checked |
  Confidence | Notes`, confidence ∈ {high, medium, VERIFY}) → gated controls noted in prose →
  unconfirmed stays `VERIFY` and out of cards.
- **Claims mode:** list every claim → find official source → write `drafts/<slug>/CLAIMS.md`
  (`Claim | Card | Task/model | Source URL | Date checked | Vendor-stated or tested | Confidence
  | Notes`) → `VERIFY` claims dropped from cards, never softened.
**Scripts run:** none directly — this is entirely agent research + hand-written markdown. It
may internally use `WebFetch`/`WebSearch`/browser tools (not scripted).
**Files written:** `drafts/<slug>/PATHS.md` and/or `CLAIMS.md`; ticks boxes in `CHECKLIST.md`
if present.
**Exit codes:** N/A (no script). **Network:** yes, arbitrary vendor pages (Claude Code's
`WebFetch` is domain-restricted to `github.com` per `.claude/settings.json:9` unless the
operator grants more per-call; Grok's browsing scope is not defined in this repo).
**Duration:** unbounded, real research.
**UI observation points:** the produced table itself (`PATHS.md`/`CLAIMS.md`) is the
progress/completion artifact — a UI could show row-count and VERIFY-count as a live checklist
if it polls the file, but there is no intermediate machine signal before the file is written.

### Other skills not in the operator command table but load-bearing

- **`format-{settings,comparison,tool-swap,single-tip,build-log,tool-verdict}`** — not
  independently invoked by the operator; loaded by `/draft-thread` step 3. Each is a pure
  markdown contract (shape, research rule, image rule, checklist path); no scripts.
  `user-invocable: false` on `format-settings` (`.claude/skills/format-settings/SKILL.md:7`) —
  the others don't set this flag explicitly but are described as "Used by /draft-thread," i.e.
  not meant for direct operator invocation either, though not hard-blocked like `approve`.
- **`hidden-settings`** — the settings format's detailed beat-by-beat contract
  (`user-invocable: true`, can be called directly as `/hidden-settings [hook|card|closer|emoji]`
  for reference). No scripts, no writes.

---

## 3. Script table

All five committed scripts live in `scripts/`. `loop.py`'s docstring is the authoritative
statement of its own contract (`scripts/loop.py:1-16`).

### `scripts/loop.py`
**Purpose:** deterministic state machine for the learning loop: posts, snapshots, experiments,
lessons, rule commits. Every command prints JSON to stdout; errors print `{"error": ...}` to
stderr and exit 1. Writes at most one data file per command, atomically
(`atomic_write`, `loop.py:99-108`, tempfile + `os.replace`), then re-renders `experiments.md`,
`learnings.md`, `ledger/SUMMARY.md` via `render()` (line 1106) for every non-read-only command.
**No network** anywhere in this file. Git used only by `commit-rule`, `undo`, `commit-data`.

**Subcommands** (`COMMANDS` dict, `loop.py:1173-1200`; `READ_ONLY = {"due", "next-slot",
"lane-share", "review-due", "status", "validate"}`, line 1201 — these six never call `render()`):

| Subcommand | Flags | Purpose |
|---|---|---|
| `init` | `--self-handles` (required) | One-time: creates `loop/state.json`. Refuses if already initialised. |
| `record-post` | `--json <file>` | Records a post to `ledger/<root_id>.json`. Idempotent (returns `recorded:false` if already there, unless replacing an `auto` record with a real one). Validates format/lane/arm/experiment consistency. |
| `due` | — | Lists posts due/missed/pending for a snapshot (36-60h window). Read-only. |
| `record-snapshot` | `--json <file>` | Appends a snapshot (kind: early/valid/late/final) to a post's `snapshots[]`. |
| `mark-missed` | — | Marks posts whose 36-60h window closed with no snapshot. |
| `set-repliers-complete` | `--root-id --value --reason` | Corrects whether a post's reply-author list was known-complete. |
| `mark-nonorganic` | `--root-id --reason` | Flags a post as non-organic (excludes it from cohorts/experiments permanently). |
| `record-activity` | `--json <file>` | Writes/merges rows into `ledger/activity/YYYY-MM.json` per item; advances read cursors (`read48_until`, `final_until` in `loop/state.json.api`). |
| `record-interactions` | `--json <file>` | Writes `loop/followers/interactions.json` — who replied to us / who we replied to, pruned to 7/30-day windows. Private, ungenerated. |
| `record-followers` | `--json <file>` | Diffs today's follower ids against the last earlier day's file; credits new followers to their most recent interaction; writes `loop/followers/followers-<date>.json` (keeps only last 2) and appends a day-row to `ledger/activity/account.json`. |
| `set-lane` | `--root-id --lane --reason` | Amends a post's lane (main/other) with an audit trail. |
| `record-export` | `--csv <file>` | Merges an X analytics CSV export's per-post numbers into activity rows (latest export wins — X's numbers are cumulative). |
| `record-eligibility` | `--verified-followers --qualified-impressions` | Appends an operator-read eligibility-screen snapshot to `ledger/activity/account.json`. |
| `open-experiment` | `--json <file>` | Opens one experiment (refuses if one is already open). Validates cohort ≥3, non-nonorganic, median primary metric >0, primary metric scorable (not `views`/`replies`). Freezes cohort median × effect as the pass bar. |
| `evaluate` | — | Batches ready treatment-arm posts (size 3) against the bar; transitions experiment status via a fixed state machine (testing→promising/unclear/no_effect→adopted/not_replicated); creates a `lessons[]` entry when an experiment closes. |
| `next-slot` | — | Pure function of post count since `loop/state.json.started_at`: alternates explore/exploit for 28 days, then explore 1-in-3. |
| `lane-share` | — | Main-lane fraction of the last 15 posts. Read-only. |
| `review-due` | — | True if ≥7 days since `last_review_at`. Read-only. |
| `mark-reviewed` | — | Sets `last_review_at`; marks lessons stale if unreviewed for 42 days. |
| `set-reference` | `--status --files` | Records whether `reference/x-algorithm.md`'s cited facts are current or stale. |
| `add-preference` | `--statement --evidence` | Turns 3+ repeated operator preference-class edits into an `adopted` lesson (`rule_state: none` until `/apply`). |
| `commit-rule` | `--lesson --files` | Applies an adopted lesson's rule change: `git add`+`git commit` the named `.claude/skills/`/`voice/` files as `feat(rules): apply <id>`. |
| `undo` | `--lesson` | `git revert`s the commit `commit-rule` made. Refuses on dirty files or a revert conflict (auto-aborts the revert). |
| `commit-data` | `--message` | `git add`s `ledger loop reviews experiments.md learnings.md queue reference` (whichever exist) and commits `chore(data): <message>` if anything staged. |
| `status` | — | Aggregates `due`, `review-due`, `next-slot`, `lane-share`, open experiment, reference status, api cursors, stale lessons. Read-only — **the single best "what's going on" call for a UI**. |
| `validate` | — | Re-validates every `ledger/*.json` post against the schema; reports problems, doesn't fix. Read-only. |

**Exit codes:** 0 + JSON result on success (after any non-read-only command, `render()` also
runs, silently rewriting the three generated markdown files); 1 + `{"error": "<message>"}` to
stderr on any `LoopError`.
**Side effects (writes):** every command above except the six read-only ones. **All writes are
atomic** (tempfile + rename) but **there is no cross-file transaction** — e.g. `record-followers`
writes `account.json` and a followers-id file as two separate atomic writes; a crash between
them is possible in principle, though not observed in `runs.log`.
**Network:** none, confirmed by module docstring and by `tests/test_scripts.py` import-gate
tests for other scripts (loop.py itself isn't in that specific test but its docstring is
authoritative and no `urllib`/`requests` import exists in the file).

### `scripts/post_thread.py`
**Purpose:** writes the run sheet (`POST.txt`) for an approved draft; copies one card at a time
to the clipboard. **v1 never calls the X API** — the write path (`--no-dry-run`) is stubbed to
always fail with `"v1 does not call the X API"` (line 412-414); the real posting code is
written out as comments (lines 389-399) documenting the intended v2 X API calls
(`POST /2/media/upload*`, `POST /2/tweets` with `reply.in_reply_to_tweet_id` chaining) but is
**not implemented**.
**Flags** (`main()`, lines 332-365): positional `draft` (path); `--dry-run`/`--no-dry-run`
(BooleanOptionalAction, default True); `--json` (print JSON payload, still writes `POST.txt`);
`--count` (character counts only, needs no approval, writes nothing); `--copy N` (copy card N,
reads the card fresh, not `POST.txt`).
**Inputs:** the draft folder's `FORMAT` file, numbered card files (`^[0-9]{2}-.+\.md$`),
`APPROVED` (digest/mtime check), `images.md`.
**Outputs:** `POST.txt` (unless `--count`); stdout run sheet, JSON payload, or copy-confirmation
line depending on flags; clipboard content via `pbcopy` on `--copy`.
**Exit codes:** 2 = no `APPROVED` (`"human gate"`, stdout, only checked when not `--count`);
1 = not a directory (line 368-370), no cards (385-387), bad `--copy N` (400-402), any
`REFUSED:` line from `card_refusals`/`approval_refusal` (404-410, printed to stderr,
newline-joined), or `--no-dry-run` (412-414); 0 = success.
**The full refusal rule set** (`card_refusals`, lines 180-219, and `approval_refusal`,
166-177) — see §5 for the exhaustive gate description, since this *is* the gate.
**Side effects:** writes `POST.txt`; on `--copy`, writes to clipboard (`pbcopy` subprocess) and
runs `open -R <media file>` for each media hint that resolves to a real file
(`reveal_in_finder`, line 307-308) — **macOS-only, no git commit ever**.
**Network:** none (`tests/test_scripts.py:74` explicitly enforces no HTTP imports;
`tests/test_scripts.py:86` enforces it never reads `os.environ`, i.e. no token could leak via
env var even in principle).

### `scripts/snapshot.py`
Documented fully in §2 CMD-SNAPSHOT. **Flags:** `--ingest <path>` (backfill mode) or no args
(daily run mode). **Exit codes:** 0 success, 1 on `XApiError`/`RuntimeError` during the fetch
phase (nothing written). **Side effects/network:** see §2.

### `scripts/x_api.py`
**Purpose:** read-only X API client for the account's own data. GET only; enforced three ways:
(1) `Client.request()` raises if `method != "GET"` (line 156-157); (2) it checks the
`x-access-level` response header equals `read` on every call and raises otherwise
(171-175); (3) `tests/test_x_api.py:76` `test_refuses_anything_but_get_before_sending` and
`:83` `test_stops_when_x_reports_write_access` assert both mechanically.
**Subcommands** (`build_parser`, lines 350-367):

| Subcommand | Args | Purpose | Rate |
|---|---|---|---|
| `keys` | — | Presence-only Keychain check (no `-w`, never reads a value) | free |
| `me` | — | Own profile (`created_at, description, pinned_tweet_id, public_metrics`) | USER $0.010 |
| `timeline` | `--start --end` | Own posts/replies/quotes in `[start,end)` with organic metrics; refuses windows >29 days old | OWNED $0.001/item |
| `followers` | — | Follower ids/handles/verified flag | OWNED $0.001/item |
| `mentions` | `--since-id` | Mentions since a given id | OWNED $0.001/item |
| `thread` | `root_id` | Root + own thread cards, read via a 6-hour timeline window around the post's snowflake-derived timestamp | OWNED (internally a `timeline()` call) |
| `user` | `handle` | Check a handle before tagging it: verified status, follower count, most recent post time | USER $0.010, `partial_ok=True` so a not-found handle raises a clean error instead of crashing |
| `backfill` | `--since` | One-time full read: `me`+`timeline`+`followers`+`mentions`, saved raw to `ledger/raw/api/backfill-<ts>.json`, logs to `runs.log` | mixed |

**Exit codes:** 1 + `{"error":..., **usage}` on `XApiError`; 0 + JSON result + usage otherwise.
**Side effects:** `backfill` writes a raw JSON dump and appends to `ledger/runs.log`; all other
subcommands are pure reads with no file writes (though callers like `snapshot.py` write files
using the returned data).
**Network:** HTTPS GET to `api.x.com`, OAuth 1.0a HMAC-SHA1 user-context signing
(`oauth_header`, lines 106-115). One retry with a 20s sleep on 429/500/502/503/504
(`_retryable`, `RETRY_SECONDS`, lines 51, 142-146, 163-169); non-retryable errors raise
immediately.
**Secrets discipline:** `tests/test_x_api.py:211` `test_success_and_failure_never_print_keys`
and `:218` `test_missing_key_message_names_key_not_value` assert the client never echoes key
values in any output path, including error messages.

### `scripts/x_read.py`
**Purpose:** the one path to reading *other people's* X posts for sessions without native X
tools (i.e. Claude Code). Wraps `grok_read.run_structured` + verifies every returned post
against the real X API before use.
**Subcommands:** `search "<query>"` (limit 10, mode Latest — the query text is passed verbatim
into the Grok prompt, `x_read.py:44-46`), `thread <root_id>` (root + the account's own replies
under it).
**Verification** (`verify()`, lines 68-86): looks up every claimed post id via
`x_api.lookup()` ($0.005/post + $0.010/author); a post is **dropped** if X has no such id, or if
its claimed text doesn't fuzzy-match the real text (`same_text()`: first-40-chars prefix match
or `SequenceMatcher` ratio ≥0.6, lines 60-65); kept posts have every field **replaced** with
X's own ground truth (author, created_at, text, metrics) — Grok's claims are never trusted
verbatim.
**Exit codes:** 1 on bad root_id format (`re.fullmatch(r"[0-9]{5,25}", ...)`, doesn't even call
Grok, lines 99-101), Grok/JSON failure (`RuntimeError`/`ValueError`, 119-121), or "could not
check Grok's posts against X, so none are returned" if the X-API verification step itself fails
(`x_api.XApiError`, 122-125 — **fails closed**: if verification can't run, nothing is returned,
even if Grok's claims might have been real). 0 + JSON otherwise.
**Output shape:** always includes `dropped: [{id, claimed_author, reason}]` alongside kept
`posts`/`root`/`own_replies`, plus `cost_usd` (Grok) and `verify_cost_usd` (X API).
**Network:** one Grok call (via `grok_read.py`) + N X-API lookups for verification.

### `scripts/grok_read.py`
**Purpose:** the single chokepoint through which this repo ever talks to Grok. One function,
`run_structured(prompt, schema, timeout=900, runner=subprocess.run)`.
**Mechanism:** shells `~/.grok/bin/grok -p <prompt> --json-schema <schema> --output-format json
--sandbox read-only --deny Bash --deny Edit --deny Write --effort low` (lines 38-41) — Grok
itself is sandboxed at the CLI level to be read-only with no shell/edit/write tools for this
specific call, independent of the repo's own hooks. Parses the **last complete JSON object** out
of Grok's structured stdout (`last_json_object`, lines 20-32, handles partial objects mid-stream).
**Exit codes / errors:** raises `RuntimeError` if the subprocess exits non-zero (embeds last
300 chars of stderr); raises `ValueError` if no JSON object is found in stdout.
**Timeout:** 900s (15 min) default.
**Network:** whatever the `grok` binary itself does (opaque to this repo).

### `scripts/draft.py`
**Purpose:** trivial — prints the `grok -p "/draft-thread {slug}"` command string. **Does not
run grok.** Explicitly does not pass any flag that skips Plan mode (module docstring, line 4-5).
**Flags:** positional `slug`, validated against `^[a-z0-9]+(?:-[a-z0-9]+)*$`.
**Exit codes:** 1 on bad slug format (with `REFUSED:` prefix to stderr), 0 + printed command
otherwise.
**Side effects:** none. **Network:** none. `tests/test_scripts.py:78,82` assert no HTTP imports
and no `subprocess` import at all — i.e. this file is guaranteed inert.

---

## 4. Hooks and guard

Both hooks are registered in `.claude/settings.json:12-27` and (per `AGENTS.md:42`) are meant
to protect **both** Claude Code and Grok, though the actual wiring shown here
(`.claude/settings.json`) is Claude-Code-specific config format; Grok's own hook registration
isn't visible in this repo pass but the hook scripts themselves are written to accept either
tool's event field names (`toolName`/`tool_name`, `toolInput`/`tool_input`,
`guard_approved.py:12-14, 69, 72`).

### `UserPromptSubmit` → `.claude/hooks/approve.py`
Fires on **every** operator prompt, but only acts on prompts matching
`^/approve\s+([A-Za-z0-9-]+)\s*$` exactly (`approve.py:18,39`) — any other text passes through
untouched (`sys.exit(0)` at line 41). Full mechanism already detailed in §2 CMD-APPROVE. **This
is the only mechanism in the whole repo that creates `APPROVED`.**

### `PreToolUse` → `.claude/hooks/guard_approved.py`
Fires on every tool call, from either tool, including tool calls made *by subagents*
(explicitly noted, docstring lines 8: "Subagent tools are included because their own tool calls
pass through this hook too.").

**Exempt tool names** (`NO_WRITE`, lines 28-32 — matched exactly, quoted verbatim):
```
{"read_file", "grep", "list_dir", "spawn_subagent",                     # Grok
 "Read", "Grep", "Glob", "LS", "ListDir", "WebFetch", "WebSearch",       # Claude Code
 "Agent", "Task", "Skill", "ToolSearch", "TodoWrite", "AskUserQuestion"}
```
plus any tool name starting with `x_` or `web_` (line 70-71) — i.e. Grok's native X-reading
tools are pre-exempted from this write-guard (they're read tools by nature).

**Two tool-name buckets it inspects further:**
- `SHELL = {"run_terminal_command", "Bash"}` — command-string regex checks (below).
- Everything else — path-value regex checks over every string value in the tool input that
  "looks like a single path" (`path_values()`, lines 53-61: any dict/list is recursed; a bare
  string with no whitespace and length <400 counts as a path candidate).

**Shell-command checks** (exact regexes, quoted verbatim):
```python
SHELL_KEYCHAIN = re.compile(r"\bsecurity\s+(find-(generic|internet)-password|dump-keychain)\b")
SHELL_MARKER_WRITE = re.compile(
    rf"/{MARKER}\b"                                                   # any path ending in the marker
    rf"|\b(touch|tee|cp|mv|rm|ln|install|truncate)\b[^;&|\n]*\b{MARKER}\b"
    rf"|>{{1,2}}\s*\S*\b{MARKER}\b")
SHELL_NESTED_APPROVE = re.compile(
    rf"(^|[\s;&|/])(grok|claude|codex)(\s+-{{1,2}}[\w-]+(\s+[^\s\"'-]\S*)?)*\s+[\"']?{re.escape(APPROVE_CMD)}\b")
```
where `MARKER = "APPROVE" + "D"` and `APPROVE_CMD = "/appro" + "ve"` (deliberately
string-concatenated, presumably so a naive text-search of the hook file for the literal string
"APPROVED" or "/approve" doesn't trivially find the guard logic — worth knowing if instrumenting
this file for a UI).

**Behavior verified live by this doc's author:** `SHELL_MARKER_WRITE`'s first alternative
(`/{MARKER}\b`) matches **any occurrence of `/APPROVED` in a shell command string at all**, not
just write verbs — a plain `cat drafts/2026-09-22-smart-tv/APPROVED` via the Bash tool was
denied. **Implication for the build:** any agent/automation wanting to *check whether a draft is
approved* must not do so via a shell command referencing the literal path; use a non-shell
file-read (Claude Code's `Read` tool, or Python's own `Path.is_file()`/`open()` inside a script
that isn't invoked as a raw shell command with that path string in it — `post_thread.py` itself
reads `APPROVED` fine because it's Python code, not a shell command line containing the string).

If `SHELL_MARKER_WRITE` or `SHELL_NESTED_APPROVE` matches → `deny()` with the reason:
`"The APPROVED file is created only by the operator typing /approve <slug>. Ask the operator to
review the draft and approve it."`
If `SHELL_KEYCHAIN` matches → `deny()` with:
`"X API keys stay in the Keychain and never enter a session. Check them with python3
scripts/x_api.py keys; the client reads them itself."`

**Path-value checks** (non-shell tools — e.g. Write, Edit):
```python
LOOP_STATE = re.compile(r"(^|/)(loop/state\.json|ledger/[0-9]+\.json|ledger/SUMMARY\.md|experiments\.md|learnings\.md"
                        r"|ledger/activity/[^/]+|loop/followers/[^/]+)$")
```
- If any path's basename equals `MARKER` (`APPROVED`) → same approval-reason deny.
- If any path matches `LOOP_STATE` → deny: `"Loop state and its generated views change only
  through python3 scripts/loop.py."` **Note the regex explicitly covers individual numbered
  ledger post files (`ledger/[0-9]+\.json`) and any file under `ledger/activity/` or
  `loop/followers/`, but *not* `queue/topics.yaml`** — confirmed by direct observation that
  `/next` and `/draft-thread` edit `queue/topics.yaml` directly with no hook interference. If a
  future UI wants queue-file writes to also be gated through a script, that would need a new
  hook rule; today they are not.

**On deny:** prints the JSON decision `{"decision": "deny", "reason": ...}` to stdout, the
reason again to stderr, and **exits 2** (Claude Code reads stderr on exit 2 per the module
docstring, line 14).

**Test coverage confirming this behavior:** `tests/test_hooks.py:41`
`test_marker_writes_denied_in_both_tools`, `:51` `test_loop_state_edits_denied_for_edit_tools`,
`:58` `test_new_loop_data_folders_denied_for_edit_tools`, `:62`
`test_keychain_reads_denied_in_both_shells`, `:70` `test_prose_mentions_stay_editable` (docs/
skills that merely *mention* these filenames in prose stay editable — the check is path-based,
never content/prose-based, docstring line 9-10), `:80` `test_normal_work_allowed`.

**What this means for a UI or a headless agent runner (D24):**
1. **No agent-driven path may create `APPROVED`.** This is enforced structurally (not by
   convention): the guard hook denies every tool-based write attempt, and the approve hook only
   fires from a `UserPromptSubmit` event matching the exact regex. A UI's "Approve" button must
   route through the real `UserPromptSubmit` mechanism of whichever CLI session is running — it
   cannot shortcut by having an agent write the file, run a shell command, or nest a CLI
   invocation with `/approve` in its own prompt (that specific nesting attack is explicitly
   covered by `SHELL_NESTED_APPROVE`).
2. **Whatever the UI's other buttons call must go through the same script entry points this
   table documents**, or a new guard rule is needed. Today only `APPROVED`, loop-state files,
   and the Keychain-read shell command are structurally blocked; everything else (e.g. writing
   directly into `ledger/*.json` bypassing `loop.py`, or writing into `drafts/` cards after
   `APPROVED` exists) is only *policy* (stated in `AGENTS.md`/skills), not hook-enforced, except
   where `post_thread.py`'s own digest check catches a post-approval card edit (§5).
3. Any new UI-invoked write path (e.g. a button that calls a new script directly, bypassing both
   the CLI and its skills) is **not automatically covered by these hooks**, since hooks fire on
   `PreToolUse`/`UserPromptSubmit` events inside a CLI session, not on arbitrary process
   execution. If the UI ends up shelling out to Python scripts itself (outside a Claude
   Code/Grok session), none of this guard logic applies at all — the safety here is entirely a
   property of running *inside* one of these two CLIs.

---

## 5. The gate — `scripts/post_thread.py`

The gate is the same script for both "check if a draft can go out" (`/ready`) and "print card
lengths" (`/draft-thread`'s preview, via `--count`). It is invoked as
`python3 scripts/post_thread.py <draft-folder> [flags]`.

### The approval mechanism
- `APPROVED` absent → exit 2, prints `human gate` to stdout (checked before any card content is
  even read, except for `--count` which needs no approval and is checked first — line 372-378
  vs 380-382).
- `APPROVED` present: reads its `cards-sha256: <hex>` line via `DIGEST_RE`
  (`^cards-sha256:\s*([0-9a-f]{64})\s*$`, line 50). If present and doesn't match a fresh
  `cards_digest()` of the current cards → `REFUSED: cards changed after approval. Type /approve
  again after re-reading them` (line 171). If the digest line is somehow absent (e.g. an
  old-format `APPROVED`), falls back to an mtime check: any card file modified after
  `APPROVED`'s own mtime → `REFUSED: edited after approval: <files>. Type /approve again after
  re-reading them` (lines 173-177).
- `cards_digest()` = SHA-256 over each card's `name.encode()+b"\0"+bytes()+b"\0"` in sorted
  filename order (lines 158-163) — **order-sensitive and filename-sensitive**: renaming a card
  or reordering changes the digest even if content is byte-identical.

### Every refusal rule (`card_refusals`, lines 180-219, run for every card in the draft)
1. **Unknown `FORMAT`:** `FORMAT` file content not in `{settings, comparison, tool-swap,
   single-tip, build-log, tool-verdict}` → `REFUSED: unknown FORMAT '<fmt>'; expected one of ...`
2. **Settings hook opens on `Most `:** for `fmt == "settings"` and `01-hook.md`, first
   non-blank line starts with `"Most "` → `REFUSED: hook opens on the setup-day line`.
3. **Root length cap:** for `01-hook.md` in `ROOT_LIMIT_FORMATS = {settings, single-tip,
   build-log, tool-verdict, tool-swap}` (i.e. **every format except `comparison`**), if
   `x_length(text) > 600` → `REFUSED: 01-hook.md is <n> characters as X counts them; the <fmt>
   format caps the root at 600`.
4. **Tool-swap root shape** (`swap_root_refusals`, lines 86-102), only for `01-hook.md` when
   `fmt == "tool-swap"`:
   - Must open with exactly two lines: `PAID → FREE` then `Finding free <word> tools that
     actually hold up.` where `<word>` is one of the 11 category words (creator, productivity,
     developer, privacy, system, storage, diagram, finance, local AI, self-hosting, support) —
     else `REFUSED: a tool-swap root opens with the series header: ...`.
   - Any `@handle` present → `REFUSED: @<handle> in the tool-swap root; handles go in the
     shout-out card only`.
   - Any `#hashtag` present → `REFUSED: hashtag #<tag> in the tool-swap root`.
   - Any thread counter like `1/5` (via `thread_part()`, which correctly excludes date-like
     `24/7`) → `REFUSED: thread counter '<match>' in the tool-swap root`.
5. **`VERIFY` anywhere in a card's text** → `REFUSED: VERIFY in <card.name>`.
6. **`💬` anywhere** → `REFUSED: 💬 in <card.name>`.
7. **"your thoughts" (case-insensitive)** → `REFUSED: thoughts CTA in <card.name>`.
8. **Engagement-solicitation phrases** (`SOLICIT_RE`, lines 55-63, quoted verbatim):
   ```python
   r"\bdrop (?:a|an) (?:hi|hello|comment|reply|link|👋)"
   r"|\bdrop (?:it|them|yours|your \w+) (?:below|here|in the comments)"
   r"|\bfollow (?:me )?for (?:more|part)"
   r"|\blike (?:and|&|\+) (?:repost|retweet|share|follow|comment)"
   r"|\b(?:repost|retweet|bookmark) this\b"
   r"|\bsave this (?:post|thread|tweet|for later|before)"
   r"|\bcomment below\b|\breply with\b|\btag (?:a friend|someone|your)"
   ```
   Match → `REFUSED: asks for engagement ('<matched text>') in <card.name>; ask a real question
   instead (X's rewards rules ban engagement solicitation)`.
9. **Banned phrases** (`BANNED_RE`, lines 64-66, quoted verbatim):
   ```python
   r"game changer|most people don['’]?t know|wait for it|🚨|🔥|👇"
   r"|juggernaut|neural graph|zero server dependenc(?:y|ies)|hollywood[- ]grade"
   r"|drop-in replacement|let['’]?s grow together"
   ```
   (`"unlock"` is deliberately **not** in this regex — the voice doc bans it as guidance only,
   `voice/exit-zero.md`, since it's also a real settings word.) Match →
   `REFUSED: banned phrase '<match>' in <card.name>`.
10. **Duplicate leading numbers:** a card whose first line matches `LEAD_NUMBER_RE`
    (`^(?:Setting\s+(\d+)\b|(\d+)\.\s)`) with a number already seen on an earlier card →
    `REFUSED: duplicate <n> on <earlier card> and <card.name>`.
11. **Media from `images/sources/`:** any media hint resolving under `images/sources/` (checked
    via `sources_media()`, lines 144-148, path-normalized) → `REFUSED: sources media in
    <card.name>: <hint>`.

### Character counting (X's weighted length, `x_length()`, lines 69-74)
URLs are stripped and each counted as a flat **23** (`X_URL_LENGTH`); every remaining code point
counts **1** if it falls in one of these Unicode ranges, **2** otherwise:
```python
X_ONE_WEIGHT = ((0, 4351), (8192, 8205), (8208, 8223), (8242, 8247))
```
This means `→`, `▷`, and emoji (outside those ranges) count 2, matching X's twitter-text v3
behavior (module comment, lines 35-36). The comment notes a real observed discrepancy: "X cut
post 1 of PAID → FREE at 277 by this count, 270 by Python's [len()]" — i.e. this weighting is a
deliberate re-implementation of X's actual counting, not Python's native string length, and it's
been checked against a real X cut point.
- **SHORT_LIMIT = 280** — a free-account post limit; exceeding it is noted (not refused) in the
  run sheet as "Long posts. X Premium can send these (up to 25,000 characters). A free account
  stops at 280."
- **ROOT_LIMIT = 600** — refusal-level cap on `01-hook.md` for the formats listed above.

### `POST.txt` (the run sheet)
Written by every non-`--count` invocation that passes the gate (`run_sheet()`, lines 264-286).
Format: a header (`"Run sheet. Do not paste this file. Re-run post_thread.py after a card
edit."` + the copy command), optional `LONG_POST` note, optional `SHOUTOUT_WAIT` note for
tool-swap drafts with >1 card, then one row per card: `<index>  <x_length>  <card.name>` plus
`  attach <hints>` if the card has media hints. **This file is never itself posted — it's
purely an operator/agent reference** ("Do not paste this file").

### `--copy N`
Reads card N fresh from disk (not from `POST.txt`), computes media hints, copies the card's
**raw text** (not the run sheet) to the clipboard via `pbcopy`, prints a confirmation
(`copy_message()`, lines 311-329): `copied post N of <total> from <card.name>`, plus (for card
1) `open: <first line>`, plus (for tool-swap card 1 with >1 card) `wait: Wait 10–20 minutes
after card 1, then post card 2 as a reply (the shout-out).`, plus `next: python3
scripts/post_thread.py <draft> --copy <N+1>` or `next: none` on the last card. For every media
hint resolving to a real file, runs `open -R <path>` to select it in Finder. **`pbcopy` and
`open -R` are the two macOS-specific calls a mobile UI must replace** (a share-sheet /
in-app "copy this card" affordance, and some other way to surface an attachment, respectively).

### `--count`
Needs no `APPROVED`, writes nothing, just prints `count_sheet()` (lines 289-300): one line per
card, `<x_length>  <card.name>`, with inline notes when a card exceeds 280 (with the "Show
more"/free-account caveat) or exceeds the format's 600-char root cap.

---

## 6. Data stores

| Path | Written by | Committed? | Privacy class | Shape / notes |
|---|---|---|---|---|
| `ledger/<root_id>.json` | `loop.py record-post` (direct) or `record-snapshot` (appends `snapshots[]`), `mark-nonorganic`, `set-lane`, `set-repliers-complete` | Yes (via `commit-data`) | Own data (the account's own posts) | One file per posted root. Fields: `root_id, slug, format, lane, posted_at, retrospective, made_in_repo, experiment, arm, hypothesis, cards[{id,text}], media, ai_media, production_minutes, edits[{class,card,note}], draft, snapshots[], missed, auto`, plus optional `nonorganic{reason,at}`, `amendments[]`. Schema enforced by `validate_post()` (`loop.py:212-233`). |
| `ledger/activity/YYYY-MM.json` | `loop.py record-activity`, `record-export` (merges into `reads.export`) | Yes | Own data | `{"month": "YYYY-MM", "items": {<id>: {id, kind, created_at, conversation_id, topics[], text, reads: {backfill\|48h\|final\|export: {...}}}}}`. `kind` ∈ `{original, quote, reply, thread_card, repost}`. |
| `ledger/activity/account.json` | `loop.py record-followers`, `record-eligibility` | Yes | Own data (aggregate counts only — no individual follower identities) | `{"days": [{date, at, followers, verified_followers, new, lost, attributed{item_id:count}, unattributed, baseline?}], "eligibility": [{at, verified_followers, qualified_impressions}]}`. |
| `ledger/SUMMARY.md` | `loop.py render()` (auto, every non-read-only command) | Yes | Generated view | **Never hand-edit** (`AGENTS.md:16`). Table columns: Posted, Slug, Format, Lane, Experiment, Views, Organic, Non-organic, Visits, Bookmarks, Outside replies, Follows, Snapshot — plus "Original Content Rewards" and "Account" sections. **See §8 for a known bug in this file's generation.** |
| `ledger/raw/` | `scripts/loop.py`? No — actually `posted/SKILL.md` step 2 (`<root_id>-posted.txt`) and `snapshot.py`/`x_api.py backfill` (`raw/api/run-<ts>.json`, `raw/api/backfill-<ts>.json`) | `ledger/raw/*.txt` committed (contains only the account's own posts per `AGENTS.md:45`); `ledger/raw/api/*.json` is **gitignored** (`reference/x-api.md`: "Follower IDs (loop/followers/) and raw API responses (ledger/raw/api/) contain other people's data. Both are gitignored and stay on this Mac.") | `ledger/raw/*.txt` = own data; `ledger/raw/api/*.json` = **other people's data, never committed** | Raw tool text / raw API JSON. |
| `loop/state.json` | `loop.py init`, and every subsequent write command that touches `experiments`, `lessons`, `rules`, `reference`, `last_review_at`, or `api` cursors | Yes (small file, no PII) | Own operational state | Shape observed live (§ above): `{version, started_at, self_handles[], last_review_at, reference{status,checked_at,changed_files[]}, experiments[], lessons[], rules[], api{read48_until,final_until}}`. `experiments[]` entries: `{id, question, treatment, control, reference_facts[], primary, effect, size, cohort[{root_id,value,kind}], cohort_median, threshold, opened_at, status, rounds[{posts[],values[],passes,result,at}], closed_at}`, status ∈ `{testing, promising, unclear, no_effect, adopted, not_replicated}` per the `TRANSITIONS` state machine (`loop.py:720-730`). `lessons[]`: `{id, experiment, statement, status, evidence[], reference_facts[], created_at, last_evidence_at, rule_state}`, `rule_state` ∈ `{none, applied, reverted}`. `rules[]`: `{lesson, commit, files[], applied_at, undone, revert_commit}`. |
| `loop/inbox/` | every skill, as scratch payload files before calling a `loop.py --json` subcommand | **No — gitignored** (`AGENTS.md:46`) | Scratch (own-data payloads, transient) | Observed contents: `post-<id>.json`, `snap-<id>.json`, `activity-{48h,backfill}.json`, `followers.json`, `interactions.json`, `experiment.json`, plus operator-dropped exports like `account_analytics_content_*.csv`. Not durable — a UI should not read state from here, only from `ledger/`/`loop/state.json`. |
| `loop/followers/` | `loop.py record-followers` (`followers-<date>.json`, keeps only the last 2), `record-interactions` (`interactions.json`) | **No — gitignored** (`AGENTS.md:46`) | **Other people's data** — described here, contents never copied into this doc | `followers-<date>.json`: `{"at": iso, "ids": [<follower ids>]}`. `interactions.json`: `{"mentions_since_id", "people": {<user_id>: {item, at, how}}, "conversations": {<conv_id>: {at, replies[]}}}`, pruned to 7-day (people) / 30-day (conversations) windows. |
| `experiments.md`, `learnings.md` | `loop.py render()` | Yes | Generated view | **Never hand-edit.** `experiments.md`: one section per experiment (question, status, treatment, compared-with, primary outcome, bar-to-beat, frozen cohort, each round's pass count). `learnings.md`: one table row per lesson (id, status, rule_state, statement, evidence ids, last-evidence date). |
| `drafts/<date>-<slug>/` | `/draft-thread` (most files), `/approve` hook (`APPROVED` only), `post_thread.py` (`POST.txt`) | **No** — drafts are not committed by any script in this repo (not in `commit-data`'s path list, `loop.py:929`); `APPROVED` is explicitly gitignored (`AGENTS.md:63`) | Own data (draft content, pre-publication) | Files: `FORMAT` (one word), `01-hook.md`…`NN-name.md` (numbered cards, the posts themselves), `REPLIES.md` (tool-swap only — "talking points, never paste-ready"), `images.md` (what to attach; `Attach: none` when nothing), `CHECKLIST.md` (copied from the format's `checklist.md`, boxes ticked), `PATHS.md` and/or `CLAIMS.md` (from `/verify-settings`), `POST.txt` (from `post_thread.py`, regenerated on every gate run), `APPROVED` (operator-hook-only), plus format-specific extras observed (`sources.md`, `thread.md`, an `images/` subfolder for actual media files). `drafts/_template/` holds blank `checklist.md`/`sources.md`/`thread.md` starters. |
| `queue/topics.yaml` | `/next` (adds/updates rows to `planned`), `/draft-thread` (→ `drafted`), `/posted` (→ `posted`) | Yes | Own data (backlog/plan) | One row per topic/post: `slug, status ∈ {queued,planned,drafted,posted,shipped,killed}, format?, lane?, experiment?, arm?, treatment?, hypothesis?, post_at?, leads[]?, draft?, root_id?, note?, example?, category?` (tool-swap only), `drafted_note?`. **Not hook-protected** — any Edit/Write tool can touch it (confirmed: not matched by `LOOP_STATE` regex in the guard hook). |
| `queue/paid-free-roster.md` | operator (manually authored, 23 Sep 2026 per its own header) | Yes | Reference data — explicitly "claims to check, never copy" (`AGENTS.md:43`) | Static markdown; not written by any script. |
| `queue/research-backlog.md` | operator | Yes | Reference | Static markdown; not written by any script. |

**Summary of the privacy boundary:** everything under `loop/inbox/`, `loop/followers/`, and
`ledger/raw/api/` is gitignored and holds either scratch payloads or other people's data
(follower ids, raw API responses that may include other accounts' content via expansions).
Everything else described above is either generated-and-committed or operator-authored-and-committed.
**A UI reading "current state" should read only the committed files** (`ledger/*.json`,
`ledger/SUMMARY.md`, `loop/state.json`, `queue/topics.yaml`, `experiments.md`, `learnings.md`) —
these are stable, schema-validated (for the ledger, via `loop.py validate`), and don't carry
privacy risk. It should never need to read `loop/inbox/`, `loop/followers/`, or
`ledger/raw/api/`.

---

## 7. Tests

**Run:** `python3 -m unittest discover -s tests` (per `AGENTS.md:58`, `README.md:65`). Verified
live during this research pass: **124 tests, all passing, 5.68s.**

**Files and rough coverage** (from `class`/`def test_` names, full list captured live):
- `tests/test_hooks.py` — `Guard` (6 tests: marker-write denial in both tool vocabularies, loop-state edit denial, new-loop-data-folder denial, Keychain-read denial in both shells, prose-mention pass-through, normal-work pass-through) and `Approve` (3 tests: digest-write + prompt-block on typed `/approve`, command registered for the operator only, other prompts pass through untouched).
- `tests/test_loop.py` — `LoopCase` (base fixture), `PostsAndSnapshots` (9), `Experiments` (15: cohort freezing, cohort-too-small, one-experiment-at-a-time, pass→adopt, fail→no_effect, mixed→fail, promising→not_replicated, wait-for-three, control posts excluded, unscorable metrics refused, zero-median cohort refused, nonorganic exclusion, arm-without-experiment refused, slot alternation, review-due/staleness, lane-share), `ApiData` (8: activity labeling/cursors, follow-credit lower bound, export exact-follows, eligibility both thresholds, interaction pruning, auto-post replacement, set-lane amendment logging, full snapshot+final-read cycle).
- `tests/test_scripts.py` — `ImportGate` (4: no HTTP imports in post_thread/draft, no subprocess in draft, no os.environ read in post_thread), `ScriptBehavior` (16: draft command printing/rejection, gate refusal without APPROVED, missing folder, no-cards refusal, run-sheet writing, long-post note, JSON payload, dry-run equivalence, no-dry-run refusal, media hints + hook fallback, copy + Finder reveal, "Most " open detection scoped to settings only, copy-past-end, thoughts/mark detection, duplicate card numbers, sources-media refusal, `Attach: none` override), `FormatAndApproval` (10: "Most " refusal scoping, root-over-600 scoping by format, engagement-solicitation vs real-question distinction, banned phrases vs "unlock" allowed, X-weighted-length root cap, exact X cut-point match, tool-swap header requirement, tool-swap handle/hashtag/counter refusal, banned-phrase coverage across every format, tool-swap run-sheet/copy shout-out wait message, `--count` needing no approval).
- `tests/test_snapshot.py` — `FakeReader`/`DailyRun` (4: first-run whole-account record with no private-data commit, failed-read records-nothing, cursor continuation + follow-credit on day 2, final read at 26 days, backfill ingest sets cursors) and `Normalize` (1: whole-text-without-handles).
- `tests/test_x_api.py` — `Signing` (OAuth1 example match), `ReadOnly` (3: GET-only enforcement, write-access-header stop, missing-access-header logged not fatal), `Reads` (8: timeline paging/cost, 29-day window refusal, retry-once-on-5xx-not-on-auth-error, thread root+cards, lookup cost, long-post note_tweet reconstruction, user-handle check, kind/nonorganic-share classification), `NoSecretsInOutput` (3: keys never printed on success or failure, missing-key message names key not value, `keys` subcommand never requests values).
- `tests/test_x_read.py` — `GrokRead` (3: read-only run + final-object/cost parsing, partial-object handling, nonzero-exit raises) and `XRead` (5: query/limit/cost assembly, invented-and-misquoted posts dropped + real ones replaced with X data, nothing returned when the check can't run, bad-id rejected without calling Grok, Grok failure reported not raised).

**What a build must keep passing:** all 124, especially (a) every `Guard`/`Approve` hook test —
these are the structural safety net the build's D24 concern depends on; (b) `ImportGate` and
`NoSecretsInOutput` — these are the tests that would catch a refactor accidentally adding
network calls to `post_thread.py`/`draft.py` or leaking key values; (c) the `post_thread.py`
`FormatAndApproval` suite — this *is* the spec for the gate's refusal behavior; any UI that
re-implements card-length display or refusal messaging should stay byte-compatible with what
these tests assert, since the tests are the closest thing to a formal spec this repo has.

**No test invokes the network, git commits with side effects on the real repo, or the real
Keychain** — they use fakes (`FakeResponse`, `FakeOpener`, `FakeReader`) and a `--root` override
on `loop.py` to point at temp directories (`LoopCase` fixture, confirmed by `build_parser()`
exposing `--root` at `loop.py:1206` "repo root (tests only)").

---

## 8. Known issues relevant to a build

**`loop.py render()` mixes two different reads in one `ledger/SUMMARY.md` row.** Per
`reviews/ui-review-2026-09-25.md` §6 (quoted in full):

> "`ledger/SUMMARY.md` shows macbook-battery at 151 organic views against 149 total. Both
> numbers are real reads, about six hours apart. `render()` in `scripts/loop.py` (about lines
> 1124–1136) takes Views from the post's snapshot and Organic from the later activity read.
> The same happens on connect-pin (849 against 856) and iphone-18-pro-aperture (464 against
> 509). The mock isn't affected: its figures come from single reads. Fix `render()` to take
> both numbers from the same read, in a loop session."

Confirmed by direct code read: in `render()` (`loop.py:1106-1139`), the `Views` column comes
from `best_snapshot(post)["root"]["views"]` (a `ledger/<id>.json` snapshot, written by
`record-snapshot`) while the `Organic` column comes from `best_read(rows.get(post["root_id"]))`
where `rows = repo.activity()` — i.e. `ledger/activity/YYYY-MM.json`, written separately by
`record-activity`. These two reads happen at different times within the same `snapshot.py` run
(the per-item `record-snapshot` call at line 157 vs. the per-window `record-activity` call at
line 163-164 of `snapshot.py`, both inside `process()` but reading X at slightly different
moments since impressions can tick up between the two internal reads), so the two numbers in one
SUMMARY.md row can legitimately disagree even though both are real. **This is a data-consistency
bug in the generated summary, not a data-collection bug** — the underlying per-source numbers
are each internally correct, only their cross-referencing in the rendered table is inconsistent.
Live-verified against the current `ledger/SUMMARY.md` (this doc's author read it directly):
macbook-battery row shows `Views 149 | Organic 151` (§6 above cites 151/149, i.e. the same pair,
order-swapped in the review's prose vs. the table's column order — the discrepancy itself is
real and matches).

**Implication for a UI:** any dashboard/progress view built on top of `ledger/SUMMARY.md` (or
directly on the two underlying data sources it merges) should either (a) pick one canonical
source per metric consistently, or (b) wait for the fix described above (a `loop.py` session
task, not yet done as of this pass) before treating Views/Organic as a matched pair. Do not
build new UI logic that assumes these two columns are always drawn from the same snapshot.

**Other things worth a build's attention, observed directly during this research pass (not
from the cited review, so flagged separately from the required §8 item above):**
- `queue/topics.yaml` is the one "loop-adjacent" file **not** protected by the guard hook's
  `LOOP_STATE` regex — a UI feature that writes to it directly (as `/next`/`/draft-thread`
  already do, by hand, not via `loop.py`) is consistent with today's behavior, but it also means
  nothing stops a bug from corrupting it the way `loop.py`'s schema validation stops ledger
  corruption. `loop.py` has no `validate`-equivalent for `queue/topics.yaml`.
  - **`pbcopy` / `open -R` are macOS-only** and are the literal mechanism `/ready`'s clipboard
  workflow depends on (`scripts/post_thread.py:303-308`) — an iPhone build needs its own
  clipboard/share mechanism; there is no cross-platform abstraction in this codebase to reuse.
- `~/Downloads/account_analytics_content_*.csv` polling in `/results` step 1 assumes a Mac
  Downloads folder; an iPhone UI has no equivalent without a new import mechanism (file
  picker / share sheet / manual paste).
- The daily launchd job's install step is manual/agent-driven (README.md:54: "Ask Claude Code to
  install it"), not something any script in this repo automates end-to-end — worth confirming
  it is actually installed and loaded on the Mac this build will run against
  (`launchctl list | grep exitzerocode` would confirm; not run during this read-only pass per
  the task's constraints).
- **`commit-data` sweeps in unrelated work.** It stages all of `ledger`, `loop`, `reviews`, `experiments.md`, `learnings.md`, `queue` and `reference` (`scripts/loop.py:928-936`). On 25 Sep the 20:00 snapshot committed three half-written files from this handoff (`d5616ba chore(data): snapshots 2026-09-25`). A UI or runner writing into those folders will have its work committed by the next snapshot; the cross-process lock (build-questions C15) should cover commits too.
