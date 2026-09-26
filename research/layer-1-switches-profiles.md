# Layer 1 research: switches, the gate split, and profiles

**Update 26 Sep (D88):** Grok is dropped from the product. Where this document names Grok as the X reader (N12, MJ2, N18, MJ3, W10, F6), read X API recent search with code-built queries (`research/discovery-x-api-search-proposal.md`). Rows describing today's factory are unchanged until the factory moves off Grok (`reviews/factory-drop-grok-plan.md`).

**For:** the build-strategy session, which grills the operator from this document and logs the decisions. This document decides nothing.
**Scope:** D56. Switches (every step of every command), the gate's rules (for everyone or a profile's), and profiles (contents, and capturing a voice at first run). Out of scope: engines and models (layer 3), X data tiers (layer 2), stack, platforms, pricing, and the build notes' "Open for later stages".
**Read on 25 Sep 2026** (additions made the same day after the operator asked what was overlooked: §2.11–§2.16, new choices L1-C17 to L1-C23, and Codex's second read of them in §4): `reviews/ui-direction.md` (D1–D57 and the build notes), `reviews/ui-build-handoff/` (README, system-today, wiring, decisions, build-questions), `AGENTS.md`, `voice/exit-zero.md`, `reference/*.md`, every `.claude/skills/*/SKILL.md` and checklist, `scripts/*.py`, `.claude/hooks/*.py`, `tests/`. No private folder was opened (`loop/followers/`, `ledger/raw/api/`, `loop/inbox/`). Nothing was run that writes, including the tests (running them writes cache files); "124 tests" below is a count of test functions, not a pass.
**Sources:** every claim cites `file:line` or a URL. Where the handoff and the repo disagree, the repo wins, and §2.10 lists each case.

**Words used here**

- **Switch:** a fixed piece of code that does one consequential thing (writes loop state, approves, reads X, copies a card). A model can't call it. Only the operator's press in the app, or the app's own schedule, starts one.
- **Model job:** a step that needs an AI model. The backend builds its prompt from files, the model writes only into its output folder (**the box**), and the backend checks what comes out before using it (D44).
- **Made impossible:** there is no path to the bad outcome at all (D53), as opposed to "tested" (a path exists and a test watches it).
- **The lock:** the one-writer lock across processes (C15, `reviews/ui-build-handoff/build-questions.md:28`).
- **Operator-only:** a switch that needs the same protection as Approve (how that works is parked for layer 3). This document only marks which ones.

---

## 1. One-page summary

- **Already switches.** The daily snapshot needs no model from end to end (`scripts/snapshot.py:179-215`), though a failure partway through recording leaves partial state. The gate (`scripts/post_thread.py`), approval (`.claude/hooks/approve.py`), every `loop.py` command, the read-only X client (`scripts/x_api.py`) and the check on Grok's posts (`scripts/x_read.py:68-86`) are switches too. In the product the backend runs them, not a model.
- **Can become switches.** About 65 of the commands' 85 or so steps (§2.2) and most new app actions (§2.11). That means finding rows, choosing experiments and cohorts, posting times, queue writes, the `FORMAT` file, explaining refusals, matching and diffing a live post, the violations the gate can detect, about nine of the weekly review's fourteen sections, applying a stored rule change, finding the post, timers, and answered/unanswered replies.
- **Must stay model jobs** (§2.3, §2.12): topic choice and its reason; Grok research (*product: X API search with model-supplied phrases, D88*); draft research; the fact-check table; cards and hook options; talking points; preference against correction; the review's judgement sections; the Cortex chat; turning a capture into a post; drafting a voice profile.
- **Where failure stays possible** (§2.4). The biggest is **the truth budget, which depends on a model**: the gate only refuses the word `VERIFY` (`scripts/post_thread.py:195-196`). A figure check and a source-quote check narrow it. Also: engagement bait the English phrase lists miss; wrong edit labels; talking points turning into ready replies; X and network failures; partial snapshot state; a short gap between the gate's check and the copy.
- **The box has to be more than a folder** (§2.13). Read-only X keys stop API writes, not a model driving the user's signed-in browser. Model jobs need no browser or screen-control tools, no key access, and web access only through the backend. D49 asks what each mechanism needs from the operating system; §2.13 answers it.
- **Headless `/approve`** (`reviews/ui-direction.md:85`) can be made impossible in the product, if these controls ship and pass D37's proof test together with layer 3's operator-only design: prompts come from a template that refuses a leading `/`; model jobs run where no hooks or skills exist; and approval is a switch, not a prompt hook. §2.14 lists the structural checks that keep this and every other "impossible" path impossible (D53).
- **Operator-only:** Approve, Apply, Undo. Six other operator yeses, including editing Weights, are choice L1-C2.
- **The lock** covers every `loop.py` write command (`scripts/loop.py:1201`), the whole snapshot run, `commit-data` (which sweeps `ledger loop reviews experiments.md learnings.md queue reference`, `scripts/loop.py:928-936`) and queue writes. A separate per-draft lock covers editing, approval, the gate and each copy.
- **The gate split** (§2.7). **For everyone:** approval and unchanged cards, no X writes, X's engagement-instruction rule, `VERIFY`, sources-folder media, structural checks, X's counting, and (proposed) the 280 limit without Premium. **A profile's:** "Most ", root caps, the PAID → FREE header rules, banned phrases, 💬, "your thoughts". AGENTS.md's "may never change" line would freeze the profile rules as written (X4).
- **Profiles** (§2.9, §2.15): identity, audience and topic tests, voice, formats and their settings, cadence, reply habits. Loop-tunable Weights sit apart. Voice samples must pass the rules for everyone before use, and lessons stay within one profile. For first run: import the user's own posts, draft an editable voice card, add a few "which sounds like you?" picks, then learn from edits.
- **For this repo now** (§2.16): seven findings for a loop session. Two bear directly on the ~8 Oct and 16 Oct dates.
- **Choices:** L1-C1 to L1-C23 in §5, with a suggested order.

---

## 2. Detail

### 2.1 How the tables read

- **Label:** `S` already a switch; `C` can become a switch; `M` needs a model; `M+S` a model job whose output a switch checks.
- **Who:** `Op-only` needs Approve-grade protection; `Op` a press by the operator that is harmless if something else triggers it; `Op-yes` acts on the operator's yes today (protection is choice L1-C2); `App` any part of the app, including the schedule.
- **Lock:** `Lock` writes loop state or commits; `Lock(q)` writes the queue (committed by `commit-data`); blank means neither.

### 2.2 Every step of every command

#### `/next` (`.claude/skills/next/SKILL.md`)

| # | Step | Source | Label | Who | Lock | Notes |
|---|---|---|---|---|---|---|
| N1 | Run the daily snapshot | `next/SKILL.md:16` | S | App | Lock | The whole snapshot (below). A rerun near 10:00 Brisbane crosses the UTC day and can bill twice (`reference/x-api.md:18`, P5). |
| N2 | `loop.py status` | `next/SKILL.md:17` | S | App | | Read-only (`scripts/loop.py:1201`). Reading while the snapshot writes can mix states; each file is written whole (`scripts/loop.py:99-108`), but not all files at once. |
| N3 | Health: last run failed, or over 30 hours old | `next/SKILL.md:18` | C | App | | A fixed rule over the last `ledger/runs.log` line (format at `scripts/snapshot.py:196, 210`). |
| N4 | Say what changed, plus the Rewards line | `next/SKILL.md:19` | C | App | | Facts come from `status` and `ledger/SUMMARY.md`; a template can say them. A model adds only wording. |
| N5 | Weekly review if due | `next/SKILL.md:23` | see `/results` | | | |
| N6 | Algorithm check: compare the cited files' blob SHAs with `main` | `next/SKILL.md:24`; `reference/x-algorithm.md:45-47` | C | App | Lock | A fixed comparison. It uses `gh` today, a CLI (D54). For a product the X algorithm reference is shared by everyone, so the vendor maintains it once, not each user. `set-reference` writes state. |
| N7 | Experiments paused until two weeks of organic data | `next/SKILL.md:28` | C | App | | A prose rule today; a date or count check in code. |
| N8 | `loop.py next-slot` | `next/SKILL.md:30` | S | App | | Fixed code over post count, time since start and experiment state (`scripts/loop.py:789-810`). Following adopted lessons on an exploit slot is judgement. |
| N9 | Pick the next experiment from the fixed list of six; pick the cohort | `next/SKILL.md:32-39` | C | App | | "First one not yet run" and "same lane, same format, a valid or late snapshot, at least 3" are queries over the ledger. **Repo bug:** line 39 says `primary "views"`, line 28 says `primary` is never views, and `open-experiment` refuses views (`scripts/loop.py:52-55, 677`). A model that follows line 39 is refused, which fails safe. |
| N10 | Operator says yes; write `experiment.json`; `open-experiment` | `next/SKILL.md:39` | S (after C builds the file) | Op-yes | Lock | |
| N11 | Lane share | `next/SKILL.md:45` | S | App | | `lane-share`. |
| N12 | Demand searches (1–2) | `next/SKILL.md:46` | M+S | App | | *Product (D88): the model returns phrase groups; code builds and runs X API recent search, no check needed.* Today: the model writes the query and Grok reads X (`scripts/grok_read.py:35-45`); `x_read.py` drops any post X doesn't have (`scripts/x_read.py:68-86`). Fixed shape: `SEARCH_SCHEMA` (`scripts/x_read.py:36-37`). |
| N13 | Queue order: PAID → FREE in queue order, one every other day | `next/SKILL.md:47` | C | App | | Deterministic from `queue/topics.yaml` and the last posting date. |
| N14 | Timing: at most two originals a day, hours apart; US-overlap slots | `next/SKILL.md:48` | C | App | | Computable once "hours apart" is a number (the skill doesn't give one). The values belong to the profile. |
| N15 | Propose one post (topic, format, arm, time) and why | `next/SKILL.md:52` | M (topic when the queue doesn't decide it; the "why") / C (the rest) | App | | See model job MJ1. |
| N16 | Operator accepts, edits or picks another | `next/SKILL.md:52` | – | Op | | Harmless if triggered by something else: a planned row posts nothing, and approval still gates. |
| N17 | Write or update the queue row | `next/SKILL.md:52-65` | C | App | Lock(q) | Today the model edits YAML by hand, and nothing guards the file (`.claude/hooks/guard_approved.py:34-35`). A switch writes the row from the accepted proposal's fields and validates it. |
| N18 | Replies worth making (2–3 leads, one line each) | `next/SKILL.md:69-74` | M+S | App | | MJ3. Other people's posts go to a model: a privacy question for layer 3 (build-questions Q11). |
| N19 | Closing line | `next/SKILL.md:76` | C | App | | Fixed text. |

#### `/draft-thread` (`.claude/skills/draft-thread/SKILL.md`) and `/verify-settings`

| # | Step | Source | Label | Who | Lock | Notes |
|---|---|---|---|---|---|---|
| D1 | Read the contract files | `draft-thread/SKILL.md:24` | C | App | | The backend builds the prompt from them (D44). |
| D2 | Find the queue row | `draft-thread/SKILL.md:20, 27` | C | App | | Named slug, else `planned`, else first `queued`. |
| D3 | Read the format skill, gold examples, arm override | `draft-thread/SKILL.md:30-31` | C | App | | Prompt assembly. |
| D4 | Material questions (build-log, tool-verdict) | `format-build-log/SKILL.md:15-22`; `format-tool-verdict/SKILL.md:15` | C | Op | | A fixed form in the app. "No real proof, no build log" becomes a check that a file is attached. Whether the file is really the output stays unproven. |
| D5 | Offer one optional test (tool-swap) | `format-tool-swap/SKILL.md:63-70` | C | Op | | Fixed offer. |
| D6 | Research | `draft-thread/SKILL.md:34` | M | App | | MJ4. |
| D7 | Tool-swap: check which paid product people on X talk about | `format-tool-swap/SKILL.md:48` | M+S | App | | Through `x_read.py` only. |
| D8 | Check a handle before tagging (`x_api.py user`) | `format-tool-swap/SKILL.md:80, 93-107`; `voice/exit-zero.md:70` | S | App | | New gate check possible: refuse any `@handle` that the X-read switch didn't look up in this draft's run. Needs the API tier (layer 2). |
| D9 | Fact-check: write `PATHS.md` / `CLAIMS.md` | `draft-thread/SKILL.md:37`; `verify-settings/SKILL.md` | M+S | App | | MJ5. Today it is prose research by the model (`reviews/ui-build-handoff/system-today.md:161-163`). |
| D10 | Write the cards | `draft-thread/SKILL.md:40-46` | M+S | App | | MJ6. The model writes into the box; a switch moves checked cards into `drafts/`. |
| D11 | `FORMAT` file | `draft-thread/SKILL.md:41` | C | App | | The backend writes it from the queue row, so the model can't choose a format the gate treats differently. |
| D12 | `REPLIES.md` (tool-swap) | `draft-thread/SKILL.md:43` | M | App | | MJ7. |
| D13 | `images.md` | `draft-thread/SKILL.md:44` | M+S | App | | The gate already refuses `images/sources/` media (`scripts/post_thread.py:216-218`). |
| D14 | `CHECKLIST.md`, boxes ticked | `draft-thread/SKILL.md:45` | C | App | | A box the model ticks itself proves nothing. Replace with backend checks where they exist, and show the rest to the operator as things to look at (L1-C12). |
| D15 | 2–3 hook options (D26) | `reviews/ui-direction.md:36` | M+S | App | | New. Same checks as the cards. |
| D16 | Queue row to `drafted` | `draft-thread/SKILL.md:48` | C | App | Lock(q) | |
| D17 | Never create `APPROVED` | `draft-thread/SKILL.md:51` | made impossible | – | | Today a hook denies it (`.claude/hooks/guard_approved.py:83-85`). In the product the model can't write outside the box, and the switch that moves box output into `drafts/` accepts only card files and the named companions. |
| D18 | Preview with X's counts; closing line | `draft-thread/SKILL.md:54-55` | S + C | App | | `post_thread.py --count` needs no approval (`scripts/post_thread.py:372-378`). New: run the gate's refusals here too, not only at `/ready` (L1-C7). |

`/verify-settings` on its own is D9. Neither skill sets `disable-model-invocation`, so a model can start them itself today (`.claude/skills/draft-thread/SKILL.md:1-12`, `.claude/skills/verify-settings/SKILL.md:1-12`; build note `reviews/ui-direction.md:89`). In the product only the backend starts a model job, so this stops mattering.

#### `/approve`

| # | Step | Source | Label | Who | Lock | Notes |
|---|---|---|---|---|---|---|
| A1 | The operator's act (typed today; the hold in the app, D37) | `AGENTS.md:14`; `reviews/ui-direction.md:47` | – | **Op-only** | | Protection: layer 3. |
| A2 | Find the one matching draft folder; refuse none or several | `.claude/hooks/approve.py:26-31, 47-52` | S | – | | |
| A3 | Digest the cards (names and bytes, in order) | `scripts/post_thread.py:158-163` | S | – | | |
| A4 | Write `APPROVED` with digest, time and `approved-by` | `.claude/hooks/approve.py:57-62` | S | – | | Not loop state, but it needs its own per-draft lock against the card editor (25 Sep review #1: editing must lock while checks run; `reviews/ui-build-handoff/decisions.md:41`). |
| A5 | Any error approves nothing | `.claude/hooks/approve.py:69-77` | S | – | | |

#### `/ready`

| # | Step | Source | Label | Who | Lock | Notes |
|---|---|---|---|---|---|---|
| R1 | Find the folder | `ready/SKILL.md:12` | C | Op | | |
| R2 | Run the gate: exit 0, 1 (`REFUSED:` lines) or 2 (`human gate`) | `scripts/post_thread.py:380-414` | S | Op | | |
| R3 | Turn each refusal into a plain sentence | `ready/SKILL.md:15` | C | Op | | The refusal strings are fixed (`scripts/post_thread.py:171-218`), so each maps to fixed plain text. No model needed. |
| R4 | Run sheet | `scripts/post_thread.py:264-286` | S | Op | | Writes `POST.txt` only. |
| R5 | Copy card N | `scripts/post_thread.py:419-427` | S | Op | | Each copy reruns the digest and every refusal first (`scripts/post_thread.py:404-410`), so a card edited after approval is refused, except in the window between that check and the copy (§2.6). `pbcopy` and `open -R` are Mac-only (D49). |
| R6 | Shout-out wait (10–20 minutes) | `scripts/post_thread.py:49, 323-324` | S + C | App | | The timer is new (D17). |
| R7 | Offer to fix card problems | `ready/SKILL.md:15` | M (optional) | Op | | Any fix changes the digest, so it needs a fresh approval. |

#### `/posted`

| # | Step | Source | Label | Who | Lock | Notes |
|---|---|---|---|---|---|---|
| P1 | Root id from the link (D17: find the post itself) | `posted/SKILL.md:12` | C | Op / App | | Finding it means reading the own timeline after approval and matching the text to the approved cards. |
| P2 | Read the live thread; save `ledger/raw/<id>-posted.txt` | `posted/SKILL.md:13` | S + C | App | Lock | `x_api.py thread` exists; today the model writes the raw file. `ledger/raw/*.txt` is committed by the sweep. |
| P3 | Match the queue row | `posted/SKILL.md:14` | C | App | | Compare the live text to each draft's cards. **Repo inconsistency:** it looks for `status: approved`, which isn't a queue status (`queue/topics.yaml:1`). |
| P4 | Compare every live card with its draft card | `posted/SKILL.md:15` | C | App | | A text diff. |
| P5 | Class each difference: preference, correction, deviation, violation | `posted/SKILL.md:16-20` | M / C | App | | **Part** of violation can be computed by running the gate's refusals over the live text. An unsourced or loosened figure, or vendor media, still needs judgement. **Deviation** can be computed only where the arm's rule is structured (card count, length); a free-text treatment can't be (Codex, §4). Preference against correction needs judgement (MJ8, L1-C8). |
| P6 | "Roughly how many minutes…?" | `posted/SKILL.md:21` | C | Op | | App chips (D34). |
| P7 | Write the payload; `record-post` | `posted/SKILL.md:22-32` | C + S | App | Lock | Built from structured data. Replaces an auto record and keeps its reads (`scripts/loop.py:355-361`). |
| P8 | Queue row to `posted`, with `root_id` | `posted/SKILL.md:33` | C | App | Lock(q) | |
| P9 | Say when the snapshot is due; list violations | `posted/SKILL.md:34` | C | App | | |

#### `/results` and the weekly review (`.claude/skills/results/SKILL.md`)

| # | Step | Source | Label | Who | Lock | Notes |
|---|---|---|---|---|---|---|
| Q1 | Find the analytics CSV in `~/Downloads`, move it, `record-export` | `results/SKILL.md:15` | C + S | Op | Lock | A file import in the app. `record-export` requires only the `Post id` and `New follows` columns (`scripts/loop.py:494-495`); any other missing column becomes 0 (`scripts/loop.py:509`). An import switch should check every column it uses. |
| Q2 | Eligibility numbers; `record-eligibility` | `results/SKILL.md:16` | C + S | Op-yes | Lock | Operator-entered. Only checks that they're whole numbers (`scripts/loop.py:602-604`). |
| Q3 | `status`, `evaluate` | `results/SKILL.md:17` | S | App | Lock | `evaluate` writes. |
| Q4 | Numbers-only table | `results/SKILL.md:18` | C | App | | |
| Q5 | Rewards progress; posts table; followers; experiment; lane; spacing; runway | `results/SKILL.md:20-26, 33` | C | App | | Arithmetic and tables over the ledger. |
| Q6 | Replies: counts, reach, visits, duplicate text, busiest 24 hours | `results/SKILL.md:23` | C (M for topic grouping) | App | | Exact duplicate text is a string match. Topics can come from X's own labels (`reference/x-api.md:24`, P12). |
| Q7 | Your edits: group preference edits by kind; propose; `add-preference` on yes | `results/SKILL.md:27` | M + S | Op-yes | Lock | Grouping is judgement (MJ9). `add-preference` needs 3 different posts with preference edits (`scripts/loop.py:850-876`), and creates an **adopted** lesson directly, without an experiment. |
| Q8 | Reader questions (mentions) | `results/SKILL.md:28` | M + S | App | | Other people's text goes to a model: privacy, layer 3. |
| Q9 | Lanes to review; `set-lane` on yes | `results/SKILL.md:29` | M + S | Op-yes | Lock | |
| Q10 | Rule changes proposed (at most two) | `results/SKILL.md:30` | M+S | App | | Checks: the lesson is adopted with rule state `none`; the target is a tunable Weight, not a guardrail; at most two. Stored as an exact patch (L1-C5). |
| Q11 | Reverts proposed | `results/SKILL.md:31` | C | App | | "Next 3 posts all below their bar or cohort median" is computable. |
| Q12 | Profile check: bio and pin against the audience promise | `results/SKILL.md:32` | M + S | App | | `x_api.py me` is a switch. |
| Q13 | Write `reviews/week-*.md` | `results/SKILL.md:19` | C (assembly) | App | Lock | The sweep commits `reviews/`. |
| Q14 | `mark-reviewed`, `commit-data` | `results/SKILL.md:34` | S | App | Lock | |
| Q15 | Three-sentence summary | `results/SKILL.md:35` | M | App | | Picking "the three things that matter most" needs a ranking, or a model. |

#### `/apply` and `/undo-rule`

| # | Step | Source | Label | Who | Lock | Notes |
|---|---|---|---|---|---|---|
| AP1 | Lesson must be adopted with rule `none` | `apply/SKILL.md:12` | C | – | | `commit-rule` checks "adopted" (`scripts/loop.py:889`) but not rule state `none`, so the same lesson can be applied twice today. |
| AP2 | Find the proposed change in the latest review | `apply/SKILL.md:13` | C | – | | If the review stored an exact patch. |
| AP3 | Edit the one rule file | `apply/SKILL.md:14` | M today → C | – | | Today the model edits the file freely. `commit-rule` only checks the path starts with `.claude/skills/` or `voice/` (`scripts/loop.py:892-894`), so it would commit an edit to the truth budget (`voice/exit-zero.md:41-43`) or to `.claude/skills/approve/SKILL.md`. The check also doesn't clean up the path, so `.claude/skills/../../scripts/post_thread.py` passes it and would commit the gate itself (inference from the code, not run; Codex, §4). "Never touch the truth budget" is prose (`apply/SKILL.md:14`). |
| AP4 | `commit-rule` | `apply/SKILL.md:15` | S | **Op-only** | Lock | git commit plus state. |
| AP5 | Say it's applied | `apply/SKILL.md:16` | C | – | | |
| U1 | `loop.py undo` | `undo-rule/SKILL.md:12` | S | **Op-only** | Lock | `git revert`; refuses dirty files and aborts a conflict (`scripts/loop.py:908-925`). |
| U2 | On "conflicted": "needs a Claude Code session" | `undo-rule/SKILL.md:14` | – | | | A person fixing git by hand. Product users have no terminal (D54): Conflict X3. |

#### The daily snapshot (`scripts/snapshot.py`, `.claude/skills/snapshot/SKILL.md`)

| # | Step | Source | Label | Who | Lock | Notes |
|---|---|---|---|---|---|---|
| SN1 | Read cursors from `status` | `scripts/snapshot.py:181` | S | App | **Lock from here** | |
| SN2 | Read followers, the 36–60 hour window, the final window, mentions | `scripts/snapshot.py:189-194` | S | App | Lock | A failed **read** records nothing and moves no cursor (`scripts/snapshot.py:195-199`; `tests/test_snapshot.py:141`). This covers the reads only. |
| SN3 | Save raw responses (private, gitignored) | `scripts/snapshot.py:200-204`; `.gitignore` | S | App | Lock | |
| SN4 | Record interactions, followers, auto posts, snapshots, non-organic marks, activity and cursors, missed reads; `evaluate` | `scripts/snapshot.py:98-172` | S | App | Lock | Eight kinds of `loop.py` call, each a separate process (`scripts/snapshot.py:38-43`). This runs outside the `try` block (`scripts/snapshot.py:208`): if one call fails, the earlier ones stay written, nothing rolls back, and no failure line is logged. A product version would stage everything, check it, then write once (L1-C16). |
| SN5 | Log the run and its cost | `scripts/snapshot.py:210-211` | S | App | Lock | |
| SN6 | `commit-data` | `scripts/snapshot.py:212` | S | App | **Lock to here** | Sweeps anything half-written in the swept folders; it did on 25 Sep (`d5616ba`; `reviews/ui-build-handoff/system-today.md:1022`). |
| SN7 | Relay the lines in plain words | `snapshot/SKILL.md:12` | C | App | | The script already prints plain English. |

The snapshot is the model for every other command: no model, fixed reads, one commit. It still needs to become all-or-nothing (SN4).

### 2.3 Model jobs

Each job: what the backend gives it, the fixed shape it must return, what the backend checks before using it, what can be made impossible, and what stays possible. The shapes are proposals for the grilling session.

| Job | Given | Returns (fixed shape) | Backend checks | Made impossible | Stays possible |
|---|---|---|---|---|---|
| **MJ1 Propose the next post** (N15) | Queue rows, `status`, lane share, allowed slots (computed), the profile's audience tests, demand leads that passed the check | `{slug, format, lane, arm, post_at, why}` | Slug format; format is switched on in the profile; lane is `main` or `other`; arm fits the open experiment; `post_at` is one of the computed slots; a queue-decided series row wasn't skipped | Proposing a time outside the cadence rule or a format that's switched off | A weak topic choice (quality) |
| **MJ2 Demand search** (N12) | The lane, the profile's topics | *Product (D88): phrase groups with AND/OR composition, a hypothesis (proposal D-C); code builds X API queries.* Today: search query → Grok returns `SEARCH_SCHEMA` | Every post looked up by id and loosely text-matched: the first 40 characters, or 60% similar (`scripts/x_read.py:60-86`); nothing returned if the check can't run (`tests/test_x_read.py:93`) | Citing a post X doesn't have | A real post misread as demand; a loosely matched quote; model-supplied `media` kept (`scripts/x_read.py:81`) |
| **MJ3 Reply leads** (N18) | Same, plus the reply rules | `[{post_id, point}]` with `point` under ~25 words | Ids pass the check; point length; no copy button for points in the app | Pasting a point with one tap (no copy control) | A point written as a ready reply (A12, `reference/x-algorithm.md:25`) |
| **MJ4 Research** (D6) | Queue row, format contract, roster (tool-swap, "claims to check, never copy", `AGENTS.md:43`), allowed source kinds | `[{item, source_url, note}]` | URLs are live; a tool-swap row has both a paid and a free source | – | Wrong or stale reading of a page |
| **MJ5 Fact-check** (D9) | Candidate claims, the verify-settings table shapes (`verify-settings/SKILL.md:38-47, 70-76`) | The `PATHS.md` / `CLAIMS.md` rows, plus (new) a verbatim quote from the page for each row | Table parses; each row has URL, today's date, confidence in `high`/`medium`/`VERIFY`; `tested` rows name an artifact that exists; **new:** the backend fetches each URL and finds the quote. The figure check (every digit, $, % or dB in the cards has a checked row) has to run **after** the cards exist, so it belongs to MJ6's checks (Codex, §4) | A row whose quote isn't on its page | A claim in words with no figure that was never listed; a quote taken out of context |
| **MJ6 Cards and hook options** (D10, D15) | The contract, the checked rows, the profile's voice | Card files named `NN-name.md`, and 2–3 alternative `01-hook.md` texts | Names match `^[0-9]{2}-.+\.md$` (`scripts/post_thread.py:19`); card count fits the format (new: `draft-thread/SKILL.md:42`); the gate's refusals pass before Approve is offered; figure coverage as in MJ5; (new) no long word-for-word overlap with the voice samples | A card count the format doesn't allow; approving a refused draft; writing anything outside the box | Off-voice or dull copy (quality); a claim with no figure |
| **MJ7 `REPLIES.md`, `images.md`** (D12, D13) | `CLAIMS.md`, the image rules | Talking points; attach list | Attach files exist; the **resolved** path isn't in a sources folder | Attaching sources-folder media (once the check uses resolved paths) | Talking points that read as paste-ready |
| **MJ8 Edit classes** (P5) | Diffs (computed), the four class definitions | Per diff: `preference` or `correction` | The gate-detectable violations and structured-arm deviations computed by code first; the operator can relabel in one tap | Labelling a gate-detectable violation as a preference | A correction learned as a preference (teaches the loop the wrong thing, L1-C8) |
| **MJ9 Review judgement** (Q7–Q10, Q12, Q15) | Ledger numbers (computed), own reply text, mentions (privacy, layer 3), the audience tests | Sections as short text; proposals as `{lesson, weight_key, old, new}` | A proposal targets an adopted lesson with rule `none`, a tunable Weight, at most two; lane proposals are `main`/`other` | A rule change to a guardrail | Wrong grouping or lane judgement (the operator says yes or no) |
| **MJ10 Voice draft at first run** (new, §2.9) | The user's own past posts, their answers | A short voice description, trait list, suggested banned phrases | Nothing from other people's posts; length limits; the user edits before saving | Using other people's posts as voice samples | A description that misses the voice (quality) |

**Generic checks for every job:** other people's posts, mentions and replies go into a prompt only as marked data, never as instructions, and only where the privacy choice allows (threat T2, `reviews/ui-build-handoff/build-questions.md:59`; layer 3); output only in the box; complete and valid or rejected whole (no partial writes); nothing in the output is run as a command; no button is ever made from model text (24 Sep review A6, `reviews/ui-build-handoff/wiring.md:38`).

### 2.4 Where failure stays possible

| # | What can still go wrong | Why it can't be made impossible | What narrows it |
|---|---|---|---|
| F1 | A claim the fact-check never listed reaches a card | Only a model reads meaning; the gate sees the word `VERIFY` only (`scripts/post_thread.py:195-196`) | Figure coverage check; a second, independent claim extraction; the operator reads before Approve |
| F2 | A source that doesn't say what the row says | Same | Backend fetch plus quote match |
| F3 | Engagement bait phrased in a way the lists miss, or not in English | The lists are English phrases (`scripts/post_thread.py:55-66`) | Add phrases as found (tests at `tests/test_scripts.py:484`); a model second check can only advise; state the language limit (L1-C11) |
| F4 | Wrong edit label teaches the loop a wrong preference | Judgement | Code computes violation and deviation; the operator confirms `add-preference` |
| F5 | Talking points drift into ready-made replies | Judgement | Length cap, no copy button, operator writes replies (A12) |
| F6 | Grok misreads a real post (*gone in the product with D88: X API returns X's own text*) | Grok's reading | The id and text check; leads are "not proof of demand" (`next/SKILL.md:46`) |
| F7 | X, network or Keychain failures; spend | Outside the app | Reads fail closed (`scripts/snapshot.py:195-199`), but a failure while recording leaves partial state (SN4); the $10 cap (`reference/x-api.md:54`); a read budget (build-questions Q10) |
| F8 | Two writers at once | Processes are independent | The lock, held for a whole command, with stale-lock recovery (L1-C3) |
| F9 | The commit sweep takes half-written files | It stages whole folders (`scripts/loop.py:929-931`) | The lock, and committing named files only |
| F10 | An agent reaches an operator-only switch | Parked | Layer 3 |
| F11 | A revert conflicts | git can conflict | Whole-version history instead of git reverts (L1-C4) |
| F12 | A model job hangs or returns half an answer | Engines vary | Time limit; the switch takes only a complete, valid output |
| F13 | A profile set up badly (a needed word banned, wrong time zone) | Operator's input | Show the effect at setup; profile edits are reversible |
| F16 | A model with the user's signed-in browser or screen control posts to X (read-only keys don't stop this) | Only if the box lets it | The box has no browser or screen tools (§2.13, L1-C17) |
| F17 | The 280-without-Premium and other structural refusals depend on the profile being right | Operator input | Read Premium status from X where the tier allows (layer 2) |
| F15 | Instructions hidden in someone's post or reply steer a model job (T2) | A model reads the text | Marked data only; outputs are shapes and checks, never commands; no buttons from model text |
| F14 | The operator's own repo keeps the headless `/approve` hole (any non-agent program can run `claude -p "/approve …"` or write the file) | Today's design (`reviews/ui-direction.md:85`) | Out of the product by construction (below); in this repo, only by D37's future change |

**The `/approve` prompt rule.** Nothing that runs model jobs may pass a prompt starting `/approve`. In the product this can be made impossible rather than tested, once these ship and pass D37's proof test (the operator-only route itself is layer 3):
1. Prompts are built from a fixed template around the job's inputs; the builder refuses any prompt whose first non-blank character is `/` (a one-line structural test, D53).
2. Model jobs run in a folder with no `.claude/`, no hooks and no skills, so a slash command there has nothing to fire.
3. Approval in the product is a switch, not a `UserPromptSubmit` hook, so no prompt anywhere can approve.

**What the lock must cover** (C15):
- every `loop.py` command outside `READ_ONLY` (`scripts/loop.py:1201`), including the `render()` each one runs (`scripts/loop.py:1250-1251`);
- the snapshot as one unit, from SN1 to SN6, because it reads cursors first and moves them later;
- `commit-data` and `commit-rule`/`undo` (git);
- queue writes, since the sweep commits `queue/`;
- ideally one writer process owns all of these, with other callers queued (L1-C3).
Reads (`status`) should wait for a running writer, or accept a slightly stale view.

### 2.5 Operator-only switches

| Switch | Why operator-only | Today |
|---|---|---|
| Approve | Only the operator approves (`AGENTS.md:14`, D37) | Typed prompt and hook |
| Apply a rule | Changes what every later draft follows; "through `/apply` only" (`AGENTS.md:20`) | Skill with `disable-model-invocation` (`.claude/skills/apply/SKILL.md:6`) |
| Undo a rule | Same, in reverse | `.claude/skills/undo-rule/SKILL.md:6` |
| *Open an experiment; adopt a preference; change a lane; record eligibility numbers; edit the profile* | Act on the operator's yes; they change what the loop learns or reports | Prose "on the operator's yes" (`next/SKILL.md:39`; `results/SKILL.md:16, 27, 29`). Protection level is L1-C2 |

### 2.6 Things that are already made impossible today

- The gate has no network code, kept so by a test (`tests/test_scripts.py:74`), and never reads the environment (`tests/test_scripts.py`, `test_post_thread_does_not_read_environ`).
- `loop.py` has no network code (`scripts/loop.py:8`; `tests/test_loop.py:540`).
- The X client sends GET only and stops if X reports anything but read access (`scripts/x_api.py:155-176`; `tests/test_x_api.py:76, 83`). The keys are Read-scoped at X (`reference/x-api.md:13`, P1): the real no-writes guarantee.
- A card edited after approval fails the gate (`scripts/post_thread.py:166-177, 404-410`; `tests/test_scripts.py:620`). This is **nearly** impossible, not fully: an edit landing between the digest check and the clipboard write (`scripts/post_thread.py:404-423`), or between approval's digest and its write (`.claude/hooks/approve.py:57-62`), gets through (Codex, §4). A per-draft lock over output promotion, editing, approval, the gate and copy closes it (L1-C3).

### 2.7 The gate's rules: for everyone or a profile's

**In `scripts/post_thread.py`** (G1–G17 are enforced today; G5b and G18 are proposals):

| # | Rule | Source | Split | Why |
|---|---|---|---|---|
| G1 | Needs `APPROVED` (exit 2) | `:380-382` | Everyone | Approval |
| G2 | Cards unchanged since approval (digest; old approvals by file time) | `:166-177` | Everyone | Approval |
| G3 | `FORMAT`, if present, must be known; a missing file silently counts as `settings` (`:151-155`) | `:184-185` | Everyone (the check); profile (which formats are switched on) | |
| G4 | Settings hook can't open on "Most " | `:188-189`, `:237-238` | Profile | A settings-format style rule (`format-settings/SKILL.md:18`) |
| G5 | Root over 600 characters refused in five formats | `:190-192`, `:32-33` | Profile (a format setting) | The 600 figure is editorial; the idea behind it (the root stands alone, A1/A2) is advice for everyone |
| G5b | *(new)* Over 280 characters refused for an account without Premium | `:34`, `:24-27` notes it only | Everyone, set by the profile's Premium field | X won't post it (`scripts/post_thread.py:25-26`) |
| G6 | Tool-swap root opens with the PAID → FREE header and a category word | `:86-92`, `:41-45` | Profile (a series) | |
| G7 | Tool-swap root: no `@handle`, hashtag or `1/5` | `:93-101` | Profile (a series) | |
| G8 | `VERIFY` in a card | `:195-196` | Everyone | Fail-closed fact-checks (`AGENTS.md:20`) |
| G9 | 💬 in a card | `:197-198` | Profile | A house style (`format-comparison/SKILL.md:38`); X's rules don't name it |
| G10 | "your thoughts" | `:199-200` | Profile | A farm tell in this voice (`voice/exit-zero.md:32`), and a question, not an instruction |
| G11 | Instructions to engage ("drop a hi", "reply with", "follow for more" …) | `:52-63`, `:201-204` | Everyone | X's rewards rule, quoted at `voice/exit-zero.md:36` |
| G12 | Banned phrases: a fixed list (game changer, 🚨🔥👇, juggernaut, drop-in replacement …) | `:64-66`, `:205-207` | Profile | D51 names "banned brochure words" as profile. The gate doesn't refuse the voice file's general brochure examples ("elite", "amazing", "seamless", `voice/exit-zero.md:32`); only the listed phrases |
| G13 | A card number used twice | `:208-215` | Everyone | Correctness, not style |
| G14 | Media from `images/sources/` | `:144-148`, `:216-218` | Everyone | Rights: copied vendor media (A15, `reference/x-algorithm.md:28`). **Weak today:** it compares text, not the resolved path, so `images/Sources/x.png` reaches the same folder on a Mac's default case-insensitive disk but isn't matched. It also can't recognise vendor media stored anywhere else (Codex, §4) |
| G15 | X's character counting (arrows and emoji count 2, a link 23). A counting rule, not a refusal by itself | `:35-39`, `:69-74` | Everyone | A platform fact, checked against a real cut (`tests/test_scripts.py`, `test_post_one_cut_point_matches_x`) |
| G17 | Not a draft folder; no numbered cards; no such card to copy | `:368-370`, `:384-387`, `:400-402` | Everyone | Structural |
| G18 | *(proposed)* Required `FORMAT` and root card; consecutive card numbers; card count allowed by the format and the arm; attachments exist | `draft-thread/SKILL.md:41-46` | Everyone (the check); profile (the counts) | Not enforced today |
| G16 | No network in the gate | `tests/test_scripts.py:74` | Everyone | No X writes |

**Rules outside the gate** (voice and formats):

| # | Rule | Source | Split | Enforced today by |
|---|---|---|---|---|
| V1 | Truth budget: every figure sourced this session | `voice/exit-zero.md:41-43` | Everyone | The model; G8 only for the word VERIFY |
| V2 | AI images are illustration only, never proof | `voice/exit-zero.md:47` | Everyone | The model |
| V3 | No vendor press images | `voice/exit-zero.md:49` | Everyone | G14 for the sources folder only |
| V4 | Never the same reply twice; no bulk replies | `voice/exit-zero.md:53-54`; A12, A13 | Everyone | Not enforceable: replies happen on X. The app can refuse to suggest one twice |
| V5 | The operator writes every reply; nothing paste-ready | `voice/exit-zero.md:55`; D14 | Everyone | The model |
| V6 | Posting stays manual ("automated means") | `voice/exit-zero.md:16`; build notes `reviews/ui-direction.md:92` | Everyone | No write code, read-only keys |
| V7 | Vendor prices keep the vendor's currency | D36 | Everyone (a truth-budget consequence) | Not enforced. `voice/exit-zero.md:12` still says "Prices in AUD" (Conflict X8) |
| V8 | Don't boost; >10% non-organic reach kept out of comparisons | `voice/exit-zero.md:80-81`; `scripts/snapshot.py:158-161` | Everyone (the loop's measurement); the advice is advice | The snapshot |
| V9 | Pin a post with no link (A14) | `reference/x-algorithm.md:27` | Everyone (advice) | The review |
| V10 | Experiment rules: never score views; cohort of 3; one at a time | `scripts/loop.py:52-55, 671-718` | Everyone | `loop.py` |
| V11 | Short sentences; verb stem once a line; one villain; root stands alone | `voice/exit-zero.md:7-11` | Profile | The model |
| V12 | Locale: Australia, Brisbane time | `voice/exit-zero.md:12`; `scripts/loop.py:33` | Profile | Code constant |
| V13 | Emoji budget, hook beats, card shapes | `hidden-settings/SKILL.md:22-69`; format skills | Profile (format settings) | The model |
| V14 | Politics stance; connect post at most 1 in 15 | `voice/exit-zero.md:56, 64` | Profile | The model |
| V15 | Makers: tag organisations only; one maker touch a day | `voice/exit-zero.md:70-72` | Profile | The model |
| V16 | Handle checked that session before a tag | `voice/exit-zero.md:70` | Everyone (on tiers that can check, layer 2) | The model runs `x_api.py user` |
| V17 | Topic share 12 of the last 15 | `reference/audience.md:33` | Profile (editorial, "not a proven algorithm threshold") | Reported only |
| V18 | Cadence: one PAID → FREE every other day; two originals a day | `format-tool-swap/SKILL.md:123` | Profile | The model |
| V19 | Keep other people's data private | `AGENTS.md:46`; `reference/x-api.md:50` | Everyone | gitignore; model discipline |

### 2.8 How "What the loop may never change" maps

`AGENTS.md:20`: "The `/approve` gate, the truth budget, fail-closed fact-checks, the shared gate refusals, and the no-X-writes rule."

| AGENTS.md item | For-everyone rules | Fit |
|---|---|---|
| The `/approve` gate | G1, G2, the approve switch | Clean |
| The truth budget | V1, V7 | Clean as a rule. Enforcement is by model today (F1, F2) |
| Fail-closed fact-checks | G8, MJ5 checks | Clean as a rule. Only the word `VERIFY` is enforced |
| The shared gate refusals | Today: everything `AGENTS.md:51` lists, which includes G4, G6, G7, G9, G10, G12 | **Doesn't fit D51.** Under D51 only G3, G5b, G8, G11, G13–G16 are shared. The phrase needs narrowing, or profile rules become frozen (Conflict X4) |
| The no-X-writes rule | G16, V6, the X client | Clean |
| *Not listed, for everyone under D51 or the repo* | G11 (X's engagement rule) is covered only by "shared gate refusals"; V4/V5 (reply rules); V19 (privacy); the one-writer lock | Suggest the product's own "never changes" list is the for-everyone set in §2.7, stated in the product, not in a profile |

A second gap: the loop can already edit rule text it may never change. `/apply` edits files under `voice/` and `.claude/skills/`, and `commit-rule` accepts any file there (`scripts/loop.py:892-894`), including the truth budget and the approve skill. Only prose stops it (`.claude/skills/apply/SKILL.md:14`). And the banned-phrase list lives twice, in `voice/exit-zero.md:28` and in `BANNED_RE` (`scripts/post_thread.py:64-66`), so a lesson could change one copy and not the other.

### 2.9 Profiles

#### What a profile contains

| Part | Today's source | Set by | Loop may tune it (Weight)? |
|---|---|---|---|
| Handle, X user id | `scripts/x_api.py:47-48`; `scripts/x_read.py:28`; `loop/state.json` `self_handles` (`scripts/loop.py:314`) | First run | No |
| Time zone, language, locale | `scripts/loop.py:33`; `voice/exit-zero.md:12` | First run | No |
| Premium or not (sets G5b) | `scripts/post_thread.py:24-27` | First run | No |
| Audience promise, on-topic tests, off-topic definition, target share | `reference/audience.md` | First run | Share target: maybe |
| Voice description and rules | `voice/exit-zero.md:5-22` | First run (drafted, then edited) | Yes, within bounds |
| Example posts (gold) | `examples/`, `hidden-settings/examples.md` | First run (imported) | Added, not rewritten |
| Banned phrases and farm tells | `voice/exit-zero.md:24-32`; `scripts/post_thread.py:64-66` | First run (starter list); the user may add or remove | The loop may add only |
| Formats switched on, and their settings (root cap, card counts, hook rules, emoji budget) | `.claude/skills/format-*`; `hidden-settings/SKILL.md` | First run | Yes (length, count, hook style: `AGENTS.md:20`) |
| Series (header, category words, roster, cadence) | `format-tool-swap/SKILL.md`; `scripts/post_thread.py:40-45`; `queue/paid-free-roster.md` | The user | Cadence: yes |
| Cadence and posting times | `next/SKILL.md:48`; `format-tool-swap/SKILL.md:123` | First run | Yes (timing) |
| Reply, maker and networking habits | `voice/exit-zero.md:51-76` | First run | Yes |
| Experiment list | `next/SKILL.md:32-38` | Product default | The order: maybe |

Rules for everyone (§2.7) are product code, never profile fields. Weights (what the loop tunes, D11) and the user's own setup could live in one file with a field marking which is which, or two files (L1-C9).

#### How existing tools capture voice and audience

Researched 25 Sep 2026. General tools publish real help pages. The X and LinkedIn ghostwriting tools mostly don't: their "learns your voice" claims come from marketing or reviews and are marked unconfirmed. Some official pages blocked a direct fetch; those details come from the search engine's copy of the official URL, marked "(search copy)".

| Tool | What the user gives | How many | What it makes | Can the user see and edit it? | Keeps learning? | Source |
|---|---|---|---|---|---|---|
| Claude Styles | Writing examples pasted or uploaded, or a description | No minimum stated | Written style instructions | Yes | No | https://support.claude.com/en/articles/10181068-configure-and-use-styles (search copy) |
| ChatGPT personalisation | Free-text instructions, a tone preset, sliders (brevity, emoji) | No samples | Plain-text instructions and memories | Yes; memories can be deleted | Yes, memories update themselves | https://help.openai.com/en/articles/8096356 ; https://help.openai.com/en/articles/8590148-memory-faq |
| Jasper Brand Voice | Text, files or a URL (crawled) | Up to 8 | A written voice description plus sample excerpts; a preview with and without the voice | Yes | Not documented | https://help.jasper.ai/hc/en-us/articles/18618693085339-Brand-Voice (search copy) |
| Writer | Examples in up to 8 boxes | At least 300 words, 500+ advised; one content type | A voice profile: overview, characteristics, adjectives | Yes | No | https://support.writer.com/article/250-how-to-calibrate-voice-for-your-content |
| Copy.ai Brand Voice | Published content pasted | 50–500 words | A description of tone, style, language, audience | Yes | No | https://support.copy.ai/en/articles/10059100 (search copy; now redirects) |
| Grammarly voice | Nothing; built from what you write, plus role and dialect | – | A description and a list of traits | You can remove traits | Yes, continuously | https://support.grammarly.com/hc/en-us/articles/23153676821773-Introducing-voice-features |
| Supergrow | Posts pasted or picked; an optional 10–15 minute voice interview | Not stated (reviews say 10–20, unconfirmed) | A saved style | By changing samples | Unconfirmed | https://help.supergrow.ai/en/articles/9104117-getting-started-with-content-style (search copy) |
| Taplio / Tweet Hunter | A form: language, role, target audience, topics; reference posts; a "Conservative ↔ Wild" slider | Not stated | Settings fields | Yes | Claimed on the home page, no mechanism | https://intercom.help/TaplioAndTweetHunter/en/articles/10639824 (search copy) |
| Typefully | Nothing explicit; past posts used to find topics | – | Topic idea lists | Per-command instructions | Undocumented | https://typefully.com/content-ideas |
| Postwise | "Who I am, what I do, who I help", or the X bio, or past tweets | Not stated | Daily tweet batches | Yes | Unconfirmed | https://help.postwise.ai/article/31-using-ai-ghostwriter-feature |
| Buffer AI Assistant | A tone choice per prompt | – | Nothing saved | – | No | https://support.buffer.com/article/583-using-buffers-ai-assistant |
| Spiral (Every) | Samples, connected channels, documents | Not stated | A "writing fingerprint" (sentence length, punctuation, word choice); custom rules as a final pass; guards against AI tells | Metrics shown; rules editable | Claims to | https://every.to/on-every/spiral-4-0-goes-agent-native |

**What the research says about samples and risks**

- **About five good, varied samples is the plateau.**
  - A study of 400+ real authors (Wang et al., EMNLP 2025 Findings, https://arxiv.org/abs/2509.14543) used a small number of each author's samples. The research agent reports it tested 2 to 10 and that more "affects the four metrics very little". That is from the paper body, not checked here; the abstract was checked.
  - Anthropic's prompting guidance recommends 3–5 examples (https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/multishot-prompting).
  - Writer advises keeping the samples to one kind of content.
- **Informal writing is imitated worst.** The abstract: models "struggle with nuanced, informal writing in blogs and forums" (checked). The research agent's figure of about 17–21% authorship match is from the paper body and not checked. X posts are informal, so expect quality to vary by model: that's D44's disclaimer.
- **Models drift to their own voice.** "The LLM's own authorship fingerprint dominates" (https://arxiv.org/abs/2608.19746). The same paper found LLM judges unreliable for scoring voice match, so a model can't be the check on voice.
- **Copying samples word for word:** no study measuring it was found. It can still be checked by code: refuse or flag a long run of identical words shared with a sample.
- **Learning from edits:** one research design turns each edit into a short written preference that the user can read and change (CIPHER, https://arxiv.org/abs/2404.15269). That fits D26 and the loop's `add-preference`. No shipping tool clearly documents doing this.
- **Picking between drafts at setup:** no tool was found that calibrates voice by asking "which sounds like you?". The closest are Jasper's with/without preview and Taplio's slider. It would be new.
- **Banned words:** Writer has a "Don't use" term bank linked to a voice (https://support.writer.com/article/69-adding-terms); Jasper lists off-limits words and has a Business-plan style guide. None of the X tools documents one.
- **Audience and topics:** always a short form (Taplio's "target audience" and "topics" fields) or inferred from past posts, never a long document.

#### First-run capture without a style guide (a proposal to grill)

1. **Who you are:** handle (checked on X where the tier allows), time zone and language from the computer, X Premium or not.
2. **Your own posts in:** on the API tier, the last few weeks of originals; on the CSV-only tier, the analytics export, which carries a "Post text" column (`reference/x-api.md:33`). The app preselects about 5–10 varied originals across formats, and the user unticks any that aren't them. Only the user's own posts, never anyone else's.
3. **A voice card:** a model (MJ10) drafts a short description, a list of traits and suggested "never say" phrases. The user keeps or strikes each line, the way Grammarly lets you remove traits, and never writes from blank.
4. **Three quick picks (new, untested elsewhere):** two versions of the same short post, "which sounds more like you?". The answers adjust the card.
5. **Who it's for:** a short form: who reads you, 3–5 topics, topics you avoid. The app turns this into the on-topic and off-topic tests (D19), shown back for a yes.
6. **Never say:** the everyone rules shown locked; the profile's starter list prefilled and editable.
7. **Formats:** switch on from the library; each starts with its defaults (caps, card counts).
8. **Keeps learning:** every card edit before approval (D26) becomes a signal. Repeated ones become readable preference lessons through the loop, adopted only on the operator's yes.

The Exit Zero setup becomes the first profile and the worked example: `voice/exit-zero.md`, `reference/audience.md`, the gold examples and the format settings map onto the parts in the table above.

### 2.10 Where the handoff and the repo disagree, and repo inconsistencies

| # | Handoff says | Repo says (wins) |
|---|---|---|
| H1 | The guard blocks agents writing loop state (threat T6, `build-questions.md:63`) | Only for non-shell tools. A shell command that writes `loop/state.json` passes: the shell branch checks only the approval marker, nested approve and Keychain reads (`.claude/hooks/guard_approved.py:75-82`) |
| H2 | Typed `/approve` stays the accessible route (C2, C12; `wiring.md:60`; README rule 11) | D57 supersedes it: the operator's CLI only; product users have none |
| H3 | `/posted` matches a row with `status: approved` or `drafted` (`system-today.md:290`) | The skill says so (`posted/SKILL.md:14`), but `approved` isn't a queue status (`queue/topics.yaml:1`) |
| H4 | `grok_read.py` is used by `snapshot.py` (its own docstring, `scripts/grok_read.py:5`) | `snapshot.py` imports only `x_api` (`scripts/snapshot.py:29-30`) |
| R1 | – | `/next` says `primary "views"` (`next/SKILL.md:39`) and "never views" (`next/SKILL.md:28`); `loop.py` refuses views (`scripts/loop.py:52-55`) |
| R2 | – | `commit-rule` doesn't check rule state `none` (`scripts/loop.py:886-905`), though `/apply` requires it (`apply/SKILL.md:12`) |
| R3 | – | `loop.py` accepts `--root` and `--now` from any caller, though `--root` is "tests only" (`scripts/loop.py:1206-1207`). A product must not expose them |

Test count: the handoff's 124 matches the repo (124 `def test_` across `tests/`).

### 2.11 App actions beyond today's commands (D12–D35)

The mock adds actions no command covers today (`reviews/ui-build-handoff/wiring.md:19-46`). Same labels as §2.2.

| # | Action | Source | Label | Who | Lock | Notes |
|---|---|---|---|---|---|---|
| W1 | Edit a card before approval | D26; `wiring.md:24` | – | Op | per-draft | Voids approval through the digest. Editing locks while checks run (`decisions.md:41`). |
| W2 | Record each edit and hook pick as a learning signal | D26, D42; `wiring.md:24-25` | C | App | Lock | A new `loop.py` command (D42), after 16 Oct in a loop session (D39). The operator's own edit, so no model is needed to store it. |
| W3 | Choose one of 2–3 hooks | D26; `wiring.md:25` | – | Op | per-draft | The options are MJ6. |
| W4 | "I've posted it": find the post | D17; `wiring.md:29` | C | App | | Own-timeline read, then match the text to the approved cards: found, not found, found but different, found twice. Needs the API tier (layer 2). |
| W5 | Wait timer and the 10-minute nudge | D17, D35; `wiring.md:30` | C | App | | Runs from the post's real `created_at`. |
| W6 | Shout-out found, or Done | D17; `wiring.md:32` | C / Op | App | Lock | Detect the account's own reply under the root; record through `record-post`. Done is the fallback. |
| W7 | First-hour card: time of first like, replies to answer | D29; `wiring.md:33` | C | App | Lock (to store) | The exact first-like time isn't readable today: `liking_users` isn't called and its price is unknown (`reference/x-api.md:46`). Polling the like count gives a proxy. Layer 2. |
| W8 | Minutes chips | D34 | C | Op | Lock | One write path with `/posted`'s `production_minutes` (`decisions.md:49`). |
| W9 | Waiting for you: list, answered, not answering, undo | D12; `wiring.md:36` | C | Op | Lock (outcome); private store (reply text) | Answered means the account replied to that reply. The snapshot reads `replied_to` for mentions (`scripts/snapshot.py:110`) but keeps only the user id for the account's own replies (`scripts/snapshot.py:106-107`), so it can't tell answered from unanswered yet (`reviews/ui-direction.md:103`). Greeting against substance: a code rule (length, emoji only) or a model reading other people's text (privacy; L1-C23). |
| W10 | Worth joining | D12; `wiring.md:37` | M+S | App | Lock | As N18, but the leads are kept. D42 names both the answered/not-answering outcomes and these leads as learning data that goes through `loop.py` (`reviews/ui-direction.md:52`); only other people's text stays in private files (Codex). |
| W11 | Builders list | D28; `wiring.md:37` | C | App | private store | Mutuals from follower ids and interactions (`loop/followers/`, private). Never sent to a model unless the privacy choice allows. |
| W12 | Capture: save a screenshot, recording or voice note | D25; `wiring.md:42` | C | Op | capture folder | Stored where the sweep never reaches (D42). |
| W13 | Capture: transcribe a voice note | D25 | M | App | | Speech to text is a model job (layer 3). On-device or not is a privacy choice (build-questions Q12). |
| W14 | Capture: turn into a post | D25 | M + C | Op | Lock(q) | A model drafts answers to the build-log questions from the capture, and the operator confirms. The capture file is real proof for D4's check. |
| W15 | Ask Cortex | D9, D14; `wiring.md:38` | M | Op | | §2.12. |
| W16 | View or edit Weights | D11; `wiring.md:41` | C | Op-yes | Lock | Editing a Weight changes the rules, the same class as Apply (L1-C2). |
| W17 | Run the daily check now | `wiring.md:43` | S | Op | Lock | Can bill twice across the UTC day boundary (`reference/x-api.md:18`). |
| W18 | Health rows | `wiring.md:44` | C | App | | Read-only. |
| W19 | Notifications, theme | D23, D35; `wiring.md:45-46` | C | Op | app settings | The app's own settings file, not loop state (D42). |
| W20 | Backfill and ingest | `scripts/x_api.py:325-348`; `scripts/snapshot.py:218-228` | S | Op | Lock | Ingest runs the same recording step as the snapshot, so it has the same partial-state gap. |

### 2.12 The Cortex chat as a model job (D9, D14, D31)

| Given | Returns | Backend checks | Made impossible | Stays possible |
|---|---|---|---|---|
| A read-only view of the ledger, results, Weights, lessons, and the post or result it's asked about. Other people's reply text only if the privacy choice allows (build-questions Q11) | Text only | Runs with no tools and no write access; any figure in the answer is checked against the data it was given, and flagged if absent (truth budget, build-questions C4); vendor prices keep their currency (D36) | Changing anything: no write path, no buttons made from its text (`wiring.md:38`), so every change goes through a switch the operator presses | Wrong explanations; a ready-made reply written as prose (D14, A12) — the app offers no copy button on Cortex text about a reply; instructions hidden in reply text (F15) |

### 2.13 What each safety mechanism needs from the operating system (D49)

D49 asks for the needs, not a Mac-only answer. The examples in the last column are names to check at the build stage; none was tested here.

| Mechanism | What it needs from the OS | Why | Examples to check at build stage |
|---|---|---|---|
| The box: files | A model process that can write only its output folder, and read only the copies of inputs it was given | D44 | Per-app sandboxes; Linux file-access limits; Windows app containers |
| The box: tools | No shell, no other programs started, no browser, no screen or input control, no access to the user's browser profile or cookies | Read-only keys stop API writes only (`reference/x-api.md:13`). A model driving a signed-in browser could post to X. Today's Grok read uses the harness's own flags (`scripts/grok_read.py:39-40`), which D44 says not to rely on | The same sandbox mechanisms, plus the harness's settings as a second layer |
| The box: network | Web access only through a fetch the backend controls (logged, and no X write hosts) | Research needs the web; open network lets prompt contents leave the machine | A local fetch service the model calls, or an outgoing-traffic filter |
| Keys | A secure store only the X-read switch process can read; keys never in a model process's environment or files | C8, T5 (`build-questions.md:22, 62`) | Mac Keychain with per-app access; Windows Credential Manager; Linux Secret Service |
| Locks | A lock across processes that clears itself if its holder crashes, or one writer service | C15; F8 | File locks tied to the process; a single background service |
| Operator-only switches | An input path model processes can't produce | T1; layer 3 | Parked for layer 3 |
| Schedule | Run at a set time, and on wake if missed | The snapshot (`ops/launchd/…plist`) | launchd, Task Scheduler, systemd timers |
| Clipboard | The app writes the clipboard itself | R5 (`scripts/post_thread.py:303-304` uses `pbcopy`) | Each OS's clipboard interface |

### 2.14 Checks that keep the impossible paths impossible (D53)

Small checks run on every change. The first four exist today; the rest are proposals.

| # | Check | Status |
|---|---|---|
| T1 | The gate has no network code | Exists (`tests/test_scripts.py:74`) |
| T2 | The gate never reads the environment | Exists (`tests/test_scripts.py`, `test_post_thread_does_not_read_environ`) |
| T3 | `loop.py` has no network code or environment reads | Exists (`tests/test_loop.py:540`) |
| T4 | The X client sends GET only and stops on anything but read access | Exists (`tests/test_x_api.py:76, 83`) |
| T5 | No X write endpoint or method anywhere in the product code | New |
| T6 | The prompt builder refuses a prompt starting with `/` | New |
| T7 | The model-job folder contains no `.claude/`, hooks or skills | New |
| T8 | Moving box output into a draft accepts only card files and the named companions, never a file named `APPROVED` | New |
| T9 | The prompt builder's inputs come from an allowlist that never includes keys or private data (unless the privacy choice allows) | New |
| T10 | A rule change resolves its path first and refuses anything outside the Weights files | New (fixes AP3) |
| T11 | The sources-media check uses the resolved, case-folded path | New (fixes G14) |
| T12 | Model output is only ever shown as text, never as a button or action | New |
| T13 | The job launcher starts model jobs with no shell, browser or screen tools and no keys in the environment | New |
| T14 | A snapshot that fails at any stage writes nothing | New (extends `tests/test_snapshot.py:141`) |
| T15 | Only the operator's path reaches an operator-only switch | Layer 3 |

### 2.15 Profiles: rules found on the second pass

- **Voice samples must pass the rules for everyone first.** Imported posts teach what they contain. The operator's history includes the "Drop a hi" post (`voice/exit-zero.md:64`), repeated reply lines (`voice/exit-zero.md:53`), and gold settings closers with "Reply with…" lines that predate the rule (`.claude/skills/hidden-settings/SKILL.md:60`). Samples that fail the gate's for-everyone checks, or the profile's banned list, are left out (L1-C20). Replies probably shouldn't be voice samples at all.
- **Lessons belong to one profile.** Experiments, lessons, Weights and the ledger are per profile. The X algorithm reference is shared, and kept by the vendor (N6). Pooling what the loop learns across users would send one user's results elsewhere: a privacy decision not assumed here (L1-C21; privacy is build-stage, `reviews/ui-direction.md:92`).
- **Several accounts per person** isn't covered by any decision (L1-C22).
- **Operator data sits in shared files today.** The checked-handles table is in a format file (`.claude/skills/format-tool-swap/SKILL.md:93-107`), and the post-1 notes are in `results/SKILL.md:29`. Both are profile data.
- **"Automated means" applies to every user.** X's rewards rules exclude posts "created or posted using automated means", and the voice file answers by keeping the operator's judgement visible in every post (`voice/exit-zero.md:16`). A product that drafts for many people could make one human act on the text a rule for everyone before Approve, such as a hook pick, an edit or a "my take" line (D26) (L1-C19).

### 2.16 For this repo now: findings for a loop session

D47's scope note keeps this repo's own loop sessions, and D39 routes script changes before 16 Oct through a loop session with tests. These findings affect the live factory. This document changes none of them.

| Finding | Where | Bears on | Suggested handling |
|---|---|---|---|
| `/next` says experiments score views; `loop.py` refuses views | `next/SKILL.md:39` against `:28` and `scripts/loop.py:52-55` | The ~8 Oct experiment-rules session: `open-experiment` will refuse, which is safe, but it stalls the session | Fix the skill line in that session |
| A failure partway through recording leaves partial state and logs no failure | `scripts/snapshot.py:208` | The 16 Oct final read, which can't be retaken | A failure line in `runs.log` for recording errors now; the all-or-nothing rewrite later (L1-C16) |
| `commit-rule` accepts a `..` path and doesn't check rule state `none` | `scripts/loop.py:886-905` | The first `/apply` (no lessons exist yet) | Resolve paths and check rule state before the first lesson is applied |
| The sources-folder check misses `images/Sources/` | `scripts/post_thread.py:144-148` | Any draft with media | Next loop session |
| The guard doesn't block shell writes to loop state | `.claude/hooks/guard_approved.py:75-82` | Any agent session | Next loop session |
| `/posted` looks for `status: approved`; `grok_read.py`'s docstring names the snapshot | `posted/SKILL.md:14`; `scripts/grok_read.py:5` | Clarity | Tidy-up |
| "Prices in AUD" against D36 | `voice/exit-zero.md:12` | Any draft with a price | The operator's call |

---

## 3. Conflicts with settled decisions (D37–D57)

Listed as found, not worked around.

| # | Decision | What strains it | Evidence |
|---|---|---|---|
| X1 | **D44 / D53** (safety never depends on a model obeying) against **D51 / `AGENTS.md:20`** (fail-closed fact-checks and the truth budget are rules for everyone) | The fact-check is a model job. The gate enforces only the word `VERIFY`. If the truth budget is a safety rule, part of it depends on a model obeying; if it's quality, D44's disclaimer covers it, but then a rule "the loop may never change" rests on the disclaimer. | `scripts/post_thread.py:195-196`; `verify-settings/SKILL.md`; `system-today.md:161-163` |
| X2 | **D44** (the model writes only into its output folder; consequential actions are switches) | `/apply` has the model edit rule files in place, and `commit-rule` accepts any file under `voice/` or `.claude/skills/`, including the truth budget and the approve skill, and, through a `..` path, any file in the repo. | `apply/SKILL.md:14`; `scripts/loop.py:892-894` |
| X3 | **D54** (nobody opens a terminal) | A conflicted undo "needs a Claude Code session" (`undo-rule/SKILL.md:14`). `commit-rule`, `undo` and `commit-data` need git, and the scripts need Python; on a Mac without the command line tools, both prompt an install. (Third-party sources say running `git` or `python3` on a Mac without the tools triggers the install prompt: https://mac.install.guide/commandlinetools/ ; https://developer.apple.com/forums/thread/666584. Not tested here: confirm at the build stage, D49.) | `scripts/loop.py:8, 190-196` |
| X4 | **D51** (the gate splits into everyone's rules and a profile's) | `AGENTS.md:20` freezes "the shared gate refusals", and `AGENTS.md:51` lists profile rules among them ("Most ", the header, brochure words). Read literally, profile rules could never change, even by the user. | `AGENTS.md:20, 51` |
| X5 | **D51** (each user sets voice, audience and locale) | Profile values are constants in shared code: handle and user id (`scripts/x_api.py:47-48`; `scripts/x_read.py:28`), time zone (`scripts/loop.py:33`), category words and banned phrases (`scripts/post_thread.py:42-45, 64-66`). (Codex points out the Keychain service name and launchd label are deployment settings, not profile data; they're dropped here.) Expected work (C16), but it means today's scripts can't be reused as they are. | as cited |
| X6 | **D44** (the backend builds prompts from the skill files) | The skills mix model instructions with switch steps ("Run `python3 scripts/loop.py …`", "write the queue row"). Passed as they are, a model tries to run scripts it shouldn't have; each skill has to split into a model part and a switch part. | e.g. `next/SKILL.md:16-17, 52`; `posted/SKILL.md:32-33`; `results/SKILL.md:34` |
| X7 | **D57** (no accessible route in v1; typed `/approve` is for the operator's CLI only) | The handoff still calls typed `/approve` the accessible route. | `build-questions.md:16, 26`; `wiring.md:60`; `README.md` rule 11 |
| X8 | **D36** (vendor prices keep the vendor's currency; outside D37–D57 but it shapes the profile) | `voice/exit-zero.md:12` says "Prices in AUD". | as cited |
| X9 | **D50** (public v1 for everyone) | The for-everyone phrase lists (G11) and the profile ones are English only. A non-English user gets no engagement-rule check. | `scripts/post_thread.py:55-66` |
| X10 | **D46** (switches before X tiers) | Several switches assume the X API: the handle check (D8), finding the post (P1), the snapshot, mentions. Layer 2 has to say which switches fall back, and how, on the CSV-only tier. | `reviews/ui-direction.md:90` |
| X11 | **D42** (learning data through `loop.py`) | Queue writes have no owning script; the model edits `queue/topics.yaml` by hand and the sweep commits it. D42 doesn't name the queue. | `next/SKILL.md:52-65`; `scripts/loop.py:929` |

---

## 4. Codex's second read

### First read (sections 1–3)

Codex (gpt-5.6-terra, high effort, read-only, job `task-mugz32mu-43p6vw`) read sections 1–3 against the cited files. It wasn't given this session's reasoning, only the document and the repo, and was told not to open the private folders. Three of its citations were spot-checked against the code before being accepted: `scripts/snapshot.py:189-208`, `scripts/loop.py:892-894` and `scripts/post_thread.py:144-148`.

**Where it agreed:**
- The switch / model-job framing fits D44 and D53.
- The existing switches: snapshot, gate, approve hook, `loop.py`, the read-only X client.
- The `primary "views"` bug, `approved` not being a queue status, `commit-rule` not checking rule state, and `snapshot.py` not using `grok_read.py`.
- The queue needing the same lock as commits.
- Which steps need a model.
- The broad everyone/profile split where D51 is explicit.
- The headless `/approve` hole, the hard-coded profile values, and the currency conflict.

**Disagreements, and what happened to each:**

| # | Codex's point | This document's position now |
|---|---|---|
| 1 | The snapshot isn't fail-closed as a whole: recording runs outside the `try` block and can leave partial state (`scripts/snapshot.py:189-215`) | **Accepted.** Fixed in §1, SN2, SN4, F7; new choice L1-C16 |
| 2 | "Can't be copied after an edit" has a timing gap between the check and the copy, and between approval's digest and its write | **Accepted.** §2.6 and R5 corrected; the per-draft lock added to L1-C3 |
| 3 | The sources-media check compares text, not the resolved path, and can't see vendor media elsewhere | **Accepted**, with different evidence: Codex's `..` example still contains `/images/sources/` and would be caught, but `images/Sources/` on a case-insensitive Mac disk would not. G14 and MJ7 corrected |
| 4 | A missing `FORMAT` silently counts as `settings` | **Accepted.** G3 corrected; G18 proposes requiring it |
| 5 | The gate doesn't refuse general brochure words, only a fixed list | **Accepted.** G12 corrected |
| 6 | Code can't compute all violations or deviations | **Accepted.** P5 and MJ8 narrowed to what the gate detects and structured arms |
| 7 | The figure check can't run in the fact-check job, which comes before the cards | **Accepted.** Moved to MJ6 |
| 8 | `next-slot` depends on more than post count; "hours apart" has no number; picking the three things that matter is judgement | **Accepted.** N8, N14, Q15 corrected |
| 9 | `record-export` checks only two columns; other missing columns become 0 | **Accepted.** Q1 corrected (`scripts/loop.py:509`) |
| 10 | `commit-rule`'s path check can be passed with `..` to reach any repo file; operator-only isn't authenticated today | **Accepted** as an inference from the code (not run). AP3 and X2 extended. The authentication gap is layer 3's |
| 11 | The gate list missed structural refusals, and counting isn't a refusal | **Accepted.** G15 relabelled; G17 and G18 added |
| 12 | X4 (AGENTS.md freezing profile rules) is an ambiguity to clarify, not a conflict | **Not accepted, recorded.** This document: read as written, `AGENTS.md:20` with `:51` freezes profile rules, and the grilling session should settle it (L1-C15). Codex: D51 already defines the split, so "shared" can simply mean the universal subset once the split exists |
| 13 | X3 (terminal) is overstated: D54 binds the product, and the operator's CLI isn't the product | **Partly accepted.** Agreed that today's scripts aren't in breach. The strain stands for the product: the current undo design (git revert, "needs a Claude Code session") can't carry over as it is (L1-C4) |
| 14 | The Keychain service and launchd label are deployment settings, not profile data | **Accepted.** Removed from X5 |
| 15 | X6, X10, X11 are expected design work, not conflicts | **Not accepted, recorded.** They stay listed as strains, since the brief asked for anything that "contradicts or strains" D37–D57. Codex: D44 allows prompt assembly, D46 schedules the tier fallbacks, and D42 is about learning data, not the queue |
| 16 | X9 (English only) is a release-scope risk, not a D50 contradiction | **Accepted** as a strain. It was already choice L1-C11 |
| 17 | Banned phrases were "add only" in the profile table but editable at first run | **Accepted.** The user may add or remove; the loop may only add |
| 18 | The Grok-post check is loose (first 40 characters or 60% similar) and keeps model-supplied media | **Accepted.** MJ2 corrected |

**Codex's additions, all taken in:** an all-or-nothing snapshot (L1-C16); a per-draft lock (L1-C3); structural draft checks before approval (G18); other people's text as untrusted data in prompts (F15 and the generic checks); marking which gate rows are enforced today and which are proposals (§2.7 header).


### Second read (sections 1, 2.11–2.16 and 5)

Codex (gpt-5.6-terra, high effort, read-only, job `task-mugzkil1-p6gibr`), fresh session, same limits.

**Where it agreed:** the switch and model-job split; the per-draft lock; the gate split; the all-or-nothing snapshot target, with near-term repo work kept to a tested loop session; fixed formats, English-only scope stated before sale, editable first-run voice capture, no pooled learning, one profile per install; a text-only Cortex.

| # | Codex's point | This document's position now |
|---|---|---|
| 1 | L1-C1 misses figures the app and Cortex show, and the operator as a source; option (b) weakens C4 rather than being a real choice | **Partly accepted.** (a) now covers app and Cortex figures, operator-tested entries, provenance and failing closed. **Not accepted:** (b) stays listed, marked with Codex's objection, because whether C4 is safety or quality under D44 is the open question |
| 2 | Waiting-for-you outcomes and Worth joining leads are learning data that D42 routes through `loop.py`, not a private store | **Accepted.** W9 and W10 corrected |
| 3 | L1-C15 reached into the live factory's AGENTS.md, which D55 keeps separate; the real question is the product's contract | **Accepted.** L1-C15 reframed; this repo's AGENTS.md is the operator's separate call |
| 4 | The order put L1-C15 before the choice it depended on | **Accepted.** L1-C15 no longer depends on L1-C6; L1-C6 depends on it |
| 5 | The gate can't run on live text as it is (it needs approval and a folder) | **Accepted.** L1-C8 now calls for the gate's content checks as one shared function |
| 6 | L1-C18 (b) reverses an accepted fix | **Accepted.** Labelled as such |
| 7 | The summary called headless approval "impossible" when it depends on controls not yet built and on layer 3 | **Accepted.** Reworded in §1 and §2.4 |
| 8 | Whole-version undo can silently overwrite a later edit | **Accepted.** L1-C4 now undoes field by field and asks first |
| 9 | Refusing on eight shared words is unsupported | **Accepted.** L1-C14 now recommends a warning first |
| 10 | L1-C17 is a layer 1 requirement for layer 3 to test against, and (b)/(c) depart from D44 | **Accepted.** Reframed and moved to the front of the order |
| 11 | "Four findings" didn't match §2.16's seven | **Accepted.** Corrected |

**Codex's additions, taken in:** voiding or re-checking approvals when a profile's gate settings change (in L1-C6); a provenance record for figures (in L1-C1); a definition of the human act (in L1-C19); an "unsure" outcome for reply sorting (in L1-C23). **Noted but not developed here:** the profile's lifecycle (export, deletion, backup, moving keys, going from one profile to several). It matters for D50's public release; it's listed for the build stage.

---

## 5. Choices for the operator

Each choice has an ID, the question, the options, a recommendation and what it depends on. None is decided here. L1-C17 to L1-C23 were added on the second pass.

**L1-C1. Is the truth budget a safety rule or a quality rule?** (Conflict X1)
- (a) **Safety.** Add the checks that can be code: every figure in a card must appear in a checked row; the backend fetches each source and finds a quoted sentence; any figure the app or the Cortex chat shows carries where it came from, or is flagged. The operator counts as a source only through an explicit "I tested this" entry with its artifact (`verify-settings/SKILL.md:80`). Anything without provenance fails closed. What still gets through (a claim in words that was never listed) is named in the release as a known limit.
- (b) **Quality.** It's covered by D44's disclaimer, and the gate keeps only the `VERIFY` check. *Codex's position: this isn't a real option, because the handoff's C4 already makes every figure a sourced-in-session rule (`build-questions.md:18-19`). This document keeps it listed, because whether C4 is safety or quality under D44 is exactly what hasn't been decided.*
- (c) Safety, plus a second model independently listing claims and comparing lists.
- Trade-offs: (a) catches invented numbers and fake sources, the worst cases, at the cost of a page fetch per row and a provenance record to design (source, time fetched, quote, what happens when a page changes or disappears). (b) is cheapest, but leaves a "may never change" rule resting on a model. (c) adds cost and still can't prove completeness.
- **Recommend (a).** It keeps `AGENTS.md:20` and C4 honest under D44 and D53. (c) can be added later.
- Depends on: nothing.

**L1-C2. Which operator yeses need Approve-grade protection?**
- (a) Approve only.
- (b) Approve, Apply and Undo.
- (c) Every operator yes: also open an experiment, adopt a preference, change a lane, record the eligibility numbers, edit the profile.
- Trade-offs: each protected switch adds whatever layer 3 builds for Approve. The unprotected ones change what the loop learns or reports, but never what gets posted.
- **Recommend (b), plus profile edits that change gate rules.** Rules and approval decide what reaches X; the rest is visible and reversible.
- Depends on: layer 3's Approve design.

**L1-C3. How wide are the locks?**
- (a) A lock per `loop.py` call.
- (b) A lock per whole command: the snapshot run, `/posted`, the weekly review, including their commits.
- (c) One writer process owns every write, and other requests queue behind it.
- Trade-offs: (a) is too narrow, because the snapshot reads cursors and moves them later (§2.4). (b) fits today's scripts. (c) is the cleanest for a product: no stale locks and a clear "waiting" state in the app.
- **Recommend (c) in the product and (b) for this repo's CLI.**
- Also a **per-draft lock**, separate from the loop lock, covering moving model output into the draft, editing, approval, the gate, the run sheet and each copy. It closes the timing gap in §2.6.
- Depends on: stack (after the layers, D47).

**L1-C4. How do rule changes get versioned and undone in the product?**
- (a) git, as today.
- (b) The app keeps saved versions of the rules and profile, each with an id and an audit trail. Undo restores a change field by field, and asks before overwriting a later edit to the same field.
- Trade-offs: (a) needs git on every user's machine and can conflict, and a conflict "needs a Claude Code session" (Conflict X3). (b) needs no git and has no merge step. Restoring a whole old version could silently undo a later, unrelated edit (Codex), so undo has to work per field and confirm.
- **Recommend (b).** A conflicted undo can't strand the user; an overlapping one asks them instead.
- Depends on: L1-C5.

**L1-C5. What does a lesson change?**
- (a) Prose in the skill files, edited by a model (today).
- (b) An exact patch stored with the weekly review's proposal, applied by a switch.
- (c) Named, bounded Weights (for example "root cap: 280–600", "cards: 3–7") that the prompt builder turns into instructions. Lessons change only those.
- Trade-offs: (a) lets a model edit guardrail text (Conflict X2). (b) is an easy bridge. (c) matches D11's Weights and Guardrails, and makes a guardrail change impossible.
- **Recommend (c), with (b) as the bridge.**
- Depends on: L1-C9.

**L1-C6. Can lessons change a profile's gate settings (root cap, hook rule, banned list)?**
- (a) No, only the user in Settings.
- (b) Yes, within fixed bounds, through Apply.
- (c) Yes, freely.
- Trade-offs: `AGENTS.md:20` lets lessons change length and hook style, but today those rules sit in gate code the loop can't touch.
- **Recommend (b).** Rules for everyone are never reachable.
- Also (Codex): an approval covers the cards' digest, not the profile. If Apply or Settings changes a gate setting after approval, affected approvals must be voided, or the approval records the profile version and the gate re-checks against it before each copy.
- Depends on: L1-C5, L1-C15.

**L1-C7. Run the gate while drafting, and hold back Approve until it passes?**
- (a) Yes: Approve stays unavailable while any refusal stands.
- (b) Show refusals but allow approval, as today (the gate catches them at Post).
- **Recommend (a).** Approving a draft the gate will refuse is a path to nothing useful, and editing voids approval anyway.
- Depends on: nothing.

**L1-C8. Who labels the differences between the live post and the draft?**
- (a) A model labels all four classes (today).
- (b) Code labels the violations the gate's content checks detect and deviations from structured arm rules. This needs the gate's content checks available on their own, without the approval and folder checks: one shared function, not a second copy of the gate (Codex). A model suggests preference or correction, and the operator can relabel with one tap.
- (c) The operator labels each one.
- Trade-offs: a wrong label teaches the loop a wrong preference (F4). (c) costs the operator time at posting.
- **Recommend (b).**
- Depends on: nothing.

**L1-C9. Profile shape: one file or two?**
- (a) One structured profile with a flag on each field saying whether the loop may tune it.
- (b) Two files: the user's setup, and the Weights the loop tunes.
- Both keep rules for everyone in product code.
- **Recommend (b).** It makes "the loop can only touch Weights" a file boundary instead of a flag check, and Undo restores one file.
- Depends on: nothing. Informs L1-C5.

**L1-C10. Formats: a fixed library, or can users make their own?**
- (a) A fixed library with settings per format, plus a "series" option (header, category words, cadence) that generalises PAID → FREE.
- (b) Users write their own formats.
- Trade-offs: (b) means user-written instructions go into model prompts and gate rules, which is much harder to check.
- **Recommend (a) for v1.** D51 says users "pick or switch off formats".
- Depends on: nothing.

**L1-C11. The engagement-rule phrases are English only.** (Conflict X9)
- (a) v1 supports English posts only, and the release says so.
- (b) Phrase lists for each supported language.
- (c) A model check for other languages, advisory only.
- **Recommend (a).** Say it before anyone buys, as D57 does for accessibility. (c) can't carry safety under D44.
- Depends on: nothing.

**L1-C12. Replace the self-ticked `CHECKLIST.md`?**
- (a) Yes: the backend checks what code can check, and the rest appears to the operator as "look at these" before Approve.
- (b) Keep it as today.
- **Recommend (a).** A box a model ticks itself is not evidence.
- Depends on: L1-C7.

**L1-C13. First-run voice capture.**
- (a) Import the user's own posts, then a drafted voice card they strike or keep, three "which sounds like you?" picks, and a short audience form (§2.9).
- (b) A questionnaire only.
- (c) Paste samples only.
- Trade-offs: (a) avoids a blank page and matches what Claude, Writer and Jasper do; the picks are untested anywhere. A new account with few posts needs (b) or (c) as a fallback.
- **Recommend (a), falling back to (b) for new accounts.**
- Depends on: layer 2 (the CSV-only tier imports posts from the export).

**L1-C14. Word-for-word overlap with voice samples.**
- (a) Refuse a draft that shares a long run of words (for example 8 or more) with a sample.
- (b) Warn only.
- (c) No check.
- **Recommend (b) to start**, then refusal once the false-positive rate on real drafts is known. Common phrases and a user's deliberate reuse of their own wording would trip a hard refusal, and no research measures the risk (Codex; this document first recommended (a)).
- Depends on: L1-C13.

**L1-C15. What is the product's "never changes" list?**
- (a) The for-everyone set in §2.7, written into the product's own contract and code, and stated to users. This repo's `AGENTS.md` is a separate question for the operator's factory (D55).
- (b) Copy `AGENTS.md:20` as it stands, with "the shared gate refusals" meaning today's whole list.
- Trade-offs: (b) freezes profile rules (Conflict X4). Codex points out D55 keeps this factory separate, so nothing here needs `AGENTS.md` changed; the product needs its own contract either way.
- **Recommend (a).**
- Depends on: nothing (the split is §2.7).

**L1-C16. Should the snapshot be all-or-nothing?** (SN4, Codex)
- (a) Yes: read, work out every change, check them all, then write once. On any failure nothing is written and the failure is logged.
- (b) Keep today's sequence of separate writes, and add a failure log line for recording errors.
- Trade-offs: (a) makes partial state impossible and means a new write path in the loop, which D39 says goes through a loop session with tests before 16 Oct. (b) is small but leaves partial state possible.
- **Recommend (a) for the product; (b) now for this repo**, since the 16 Oct final read mustn't be put at risk.
- Depends on: L1-C3.

**L1-C17. Adopt the full box as a layer 1 requirement?** (§2.13, F16)
- (a) Yes: files only in the output folder; no shell, browser or screen tools; no keys; web access only through a fetch the backend controls. Layer 3 tests engines against it.
- (b) Allow open network access inside the box.
- (c) Rely on each harness's own settings.
- Trade-offs: (a) is the only option where "no X writes" holds even if a harness has browser tools. Some engines may not run that way, and they go in the "not supported" column, as D54 does for hand setup. (b) and (c) are departures from D44, not ordinary trade-offs: (b) lets data leave, and (c) rests on a harness obeying (Codex).
- **Recommend (a),** decided before layer 3, since D46 has engines tested against the switches (Codex).
- Depends on: nothing. D49's build-stage research confirms how each OS provides it.

**L1-C18. Can the Cortex chat start anything?**
- (a) Text only. The operator presses the app's existing buttons.
- (b) It may suggest actions, shown as buttons the operator confirms. **This would reverse an accepted fix**: the 24 Sep review's part A was accepted as a fix list (`reviews/ui-direction.md:71`), and it includes "never creates action buttons from its own text" (`wiring.md:38`).
- Trade-offs: (b) is more convenient, but reply text could inject a button.
- **Recommend (a).**
- Depends on: L1-C2; layer 3's privacy choice (Q11).

**L1-C19. Must every post carry one human act before Approve?** (automated means, §2.15)
- (a) Yes: a hook pick, an edit, or a "my take" line counts.
- (b) No: advice only.
- Trade-offs: (a) keeps the operator's judgement visible for every user, at the cost of one tap or line. X doesn't define "automated means", so neither option is proven safe.
- **Recommend (a).** Record which act happened; a default left untouched doesn't count, and a hook pick must be a real choice between options. It can't be claimed to guarantee rewards eligibility while "automated means" is undefined (Codex).
- Depends on: L1-C7.

**L1-C20. Filter voice samples before use?**
- (a) Leave out any sample that fails the rules for everyone or the profile's banned list.
- (b) Trim the failing lines and keep the rest.
- (c) No filter.
- **Recommend (a).** Simple, and it can't teach what the gate refuses.
- Depends on: L1-C13.

**L1-C21. Does learning stay within one profile?**
- (a) Yes: experiments, lessons and Weights are per profile, and there is no pooling in v1.
- (b) Pool anonymised results across users.
- **Recommend (a).** Pooling is a privacy decision for the build stage.
- Depends on: nothing.

**L1-C22. Several accounts per person in v1?**
- (a) One profile per install, with a data layout that allows more later.
- (b) Several fully separate profiles, each with its own ledger, keys and locks.
- **Recommend (a).** No decision asks for more, and each profile doubles keys, locks and schedules.
- Depends on: L1-C9.

**L1-C23. How are greetings told from substantive replies?** (D12, W9)
- (a) A code rule: very short, emoji only, or a greeting word.
- (b) A model reading the replies.
- (c) (a) first, then a model only on what's left, if the privacy choice allows.
- Trade-offs: (b) sends other people's text to a model.
- **Recommend (a) for v1, with an "unsure" outcome that shows as a card.** Only clear greetings collapse, so a misread can't hide a real reply (Codex: without this, a wrong "greeting" hides it).
- Depends on: layer 3's privacy choice.

### Suggested order

1. **L1-C1** (truth budget) and **L1-C17** (the box): the two safety boundaries everything else sits inside.
2. **L1-C15**, then **L1-C9**: what is fixed for everyone, and the profile's file boundary.
3. **L1-C5**, **L1-C6**, **L1-C4**: what lessons change, and how changes are undone.
4. **L1-C2**: which switches need protection, handed to layer 3.
5. **L1-C3**, then **L1-C16**: the locks and the all-or-nothing snapshot.
6. **L1-C7**, **L1-C12**, **L1-C8**: the draft and posting checks.
7. **L1-C10**, **L1-C11**: formats and language scope.
8. **L1-C18**: the chat's limits, handed to layer 3 with L1-C2.
9. **L1-C19**, **L1-C21**, **L1-C22**: rules every profile shares, and the profile's reach.
10. **L1-C13**, **L1-C20**, **L1-C14**: first-run capture, after layer 2's tiers are known.
11. **L1-C23**: reply sorting, with layer 3's privacy choice.
