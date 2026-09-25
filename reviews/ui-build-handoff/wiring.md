# Wiring: every UI action to what it must run

How each button in the mock connects to the system that exists today. `system-today.md` holds the full detail of each command (steps, files, exit codes), and `screens.md` holds each control's IDs. This file is the join between them: for each action, what it runs, what it needs from the operator, how the UI learns progress and outcome, what it costs, and what doesn't exist yet.

## 1. Principles (MUST)

1. **The UI is a client of the existing commands.** Every change to posts, drafts, the queue, the ledger or loop state goes through the skill or script that owns it. The UI MUST NOT write `APPROVED`, `loop/state.json`, `ledger/*.json`, `ledger/SUMMARY.md`, `experiments.md` or `learnings.md` itself; the guard hook blocks those paths for agents today (`.claude/hooks/guard_approved.py:34`).
2. **The gate is the source of truth for "can this post go".** The mock's JavaScript copy of the refusals (`gateRefusals` in `ui/mock/src/main_script.js`) is for demonstration only. The real UI shows what `scripts/post_thread.py` returns: exit 0 ready, 1 refused (`REFUSED:` lines), 2 "human gate", meaning not approved.
3. **Approve is the operator's alone** (D13, D24). See §3: this is the hardest wiring problem in the build.
4. **One writer at a time, across processes.** The UI's runner, the 20:00 launchd snapshot and interactive CLI sessions all run read-modify-write `loop.py` commands (`scripts/loop.py:99-112`); atomic writes prevent torn files, not lost updates. One cross-process lock or queue must cover all three, and the UI shows a second request as waiting or refused.
5. **Nothing reaches X except reads.** No write endpoint exists in the code: `post_thread.py --no-dry-run` exits 1, and a test forbids HTTP imports in the gate (`tests/test_scripts.py`).

## 2. Action table

**Cost:** X API pay-per-use, from `reference/x-api.md` and `ledger/runs.log`. Owned reads are US$0.001 an item, user reads US$0.010. Recent daily snapshots cost US$0.036–0.09.

**New:** needs backend work that doesn't exist today.

| UI action (control) | Runs today | Needs the operator | Progress signal | Outcome signal | Cost | New / gaps |
|---|---|---|---|---|---|---|
| **Plan the next post** (Today) | `/next` → `snapshot.py`, `loop.py status`, `loop.py next-slot`, `x_read.py search` ×1–2 (demand) and ×2–3 (replies) | accept / edit / pick another; yes/no on an experiment once the pause lifts (~8 Oct) | none structured; the scripts emit JSON and lines, the skill emits prose | a proposal (topic, format, arm, time) and a `queue/topics.yaml` row set to `planned` on accept | snapshot ≈ US$0.04–0.09, plus one Grok call per search, plus ≈ US$0.005 a post to verify each post Grok returns | the proposal must come back structured (fields, not prose); Worth joining results aren't stored (**new**) |
| **Accept / Pick another** (proposal) | `/next` continues: writes the queue row / re-plans | the choice itself | – | row `status: planned` | – | the UI must write the choice back into the same `/next` run, or run a second step |
| **Draft** (Posts queue) | `/draft-thread <slug>` → format skill, `/verify-settings` (research), `post_thread.py --count` | **build-log / tool-verdict:** the four material questions (`format-build-log/SKILL.md:16-20`) or the tool-verdict run questions; **tool-swap:** one optional test offer | new files appearing under `drafts/<slug>/`; nothing structured during research | the fixed closing line "Read the cards… type /approve <slug>…" and the queue row `status: drafted` | research: Grok and web; no X API | the working line needs real phases; fact-check outcomes (the `factcheck` tweak) come from `CLAIMS.md` / `PATHS.md` VERIFY rows |
| **Change something / Edit a card** (Post, editor) | nothing: edit the card file in `drafts/<slug>/NN-*.md` | – | – | the file saved; `APPROVED` is now stale (the digest no longer matches) | – | recording the edit as a preference signal before approval is **new**; today `/posted` records only live-vs-draft differences (`edits` in the ledger) |
| **Choose a hook** (Posts, hook sheet; D26) | nothing: format skills don't offer hook options | the pick | – | the draft's `01-hook.md` uses it | – | `/draft-thread` producing 2–3 hooks, and storing the pick as a preference, are **new** |
| **Hold to approve** (Post) | the operator types `/approve <slug>` → `UserPromptSubmit` hook `approve.py` writes `APPROVED` (`cards-sha256`, `approved-at`, `approved-by: operator, typed /approve`) | the hold is the operator's act | instant | `APPROVED` exists and its digest matches the cards | – | **the key open problem**, see §3 |
| **Start posting** (Today / Post) | `/ready <slug>` → `post_thread.py <folder>` (writes `POST.txt`) | – | – | exit 0 ready → the Posting steps; 1 → show the `REFUSED:` reasons; 2 → not approved | – | none, as long as the runner returns the exit code and stdout/stderr |
| **Copy the post / Copy again** (Posting 1) | `post_thread.py <folder> --copy 1` (`pbcopy` + Finder reveal via `open -R`) | – | – | clipboard set | – | **Mac-only.** The phone needs the card text sent to it and copied with the phone's own clipboard; attachments need a phone path too |
| **I've posted it / Check again / It's up** (Posting 1) | nothing automatic. Today the operator pastes the link into `/posted <link>`, which runs `x_api.py thread <id>` | – | – | found: root id and `created_at`; not found; found but different; found twice | own timeline ≈ US$0.001 an item | an automatic "find my latest post and match it to the approved cards" is **new** (D17); `created_at` must drive the Wait timer |
| **Wait / shout-out window** (Posting 2–3) | the `wait:` line from `post_thread.py --copy 1` (tool-swap: "Wait 10–20 minutes…") | – | clock | the window opens at +10 min and closes at +20 | – | the nudge at 10 min (D17, D35) needs push (**new**) |
| **Copy the shout-out** (Posting 3) | `post_thread.py <folder> --copy 2` | – | – | clipboard set | – | same phone-clipboard gap; detecting the shout-out on X is **new** |
| **Done / Skip the shout-out** (Posting 4) | `/posted <link>` → `x_api.py thread`, diff live vs draft, `loop.py record-post` | "Roughly how many minutes did this one take, start to finish?"; which slug if unsure | – | `ledger/<id>.json` with the cards' text and `production_minutes`; queue row `posted`; any `violation` edits listed. Not recorded: the shout-out, the first like | ≈ US$0.001 an item | the UI's first-hour minutes chips (D34) answer the minutes question, stored as `production_minutes` (the field exists and is null on all 11 posts today) |
| **First-hour card** (Today; D29) | nothing | – | – | first like time; replies to answer now | a mentions/timeline read | **new**: time to first like isn't stored, and live reads in the first hour need a poller |
| **Write this week's review** (Results) | `/results` → `loop.py record-export` (CSV from `~/Downloads`), `record-eligibility`, `status`, `evaluate`, writes `reviews/week-*.md`, `mark-reviewed`, `commit-data` | the weekly CSV export (X → Premium → Analytics → Content → Export); the eligibility numbers (verified followers, qualified impressions), which the operator may decline | per review section (13) | the review file, `last_review_at`, a commit | `x_api.py mentions`, `me` | **Mac-only CSV path:** the phone needs a file import; the mock's needs-you question maps to the eligibility step |
| **Results figures** (Results tabs) | read `ledger/SUMMARY.md`, `ledger/activity/*.json`, `loop.py status` | – | – | – | – | see `data.md`; the `render()` two-read bug affects SUMMARY rows |
| **Waiting for you: Answered / Not answering / Undo** (Replies) | nothing | – | – | – | a mentions read ≈ US$0.06–0.10 for the first read each UTC day (24 Sep review, part C) | **new**: store `referenced_tweets` in the snapshot, a fresh mentions read on open, and a store for each reply's outcome |
| **Worth joining / Builders** (Replies) | Worth joining comes from `/next`'s reply leads (printed, not saved); Builders has nothing | – | – | – | Grok calls | **new**: persist the leads; a builders/mutuals model built from followers and interactions (`loop/followers/`, private) |
| **Ask Cortex / chat** (everywhere; D9, D14) | nothing | – | the `ask` working line | an answer | model usage | **new**: backend model, read-only data access, never writes a reply (D14, A12), never creates action buttons from its own text (24 Sep review A6), treats others' replies as untrusted input, and needs a data policy for third-party reply text: the repo keeps it local (`AGENTS.md:46`), so sending it to an external model is a privacy decision (`build-questions.md` Q11) |
| **Queue for about 8 Oct** (Cortex) | `/next` → `loop.py open-experiment --json …` once the pause lifts | yes to the experiment | – | an experiment row | – | experiment rules are still to be written (due ~8 Oct) |
| **Apply / Undo** (Cortex lessons) | `/apply <id>` → edit one file under `.claude/skills/` or `voice/`, then `loop.py commit-rule`; `/undo-rule <id>` → `loop.py undo` | confirm the change shown | – | commit SHA; "Applied…" / "Reverted…"; errors "uncommitted edits" or "conflicted" | – | none; no lessons exist yet |
| **Weights / Guardrails** (Cortex) | read the skills' prose; `loop/state.json.rules` is empty | – | – | – | – | Weights as structured data is **new** (24 Sep review C8) |
| **Capture: Save / Turn into a post** (Capture; D25) | nothing | the note, the kind, the media | upload | a stored capture, queued as a build log or tool verdict | storage | **new**: upload, storage, transcription, a route into `/draft-thread`; privacy |
| **Run it now / Run the daily check now** (health) | `snapshot.py` (or the `/snapshot` skill) | – | its printed lines | `ledger/runs.log`: `snapshot ok …` or `snapshot failed error=…` | ≈ US$0.04–0.09 a run; a second run in the same UTC day re-reads | watch the double charge across the UTC day boundary (10:00 Brisbane, 24 Sep review C7) |
| **Health rows** (Settings) | `ledger/runs.log` tail, `x_api.py keys` (presence only), the reference status in `loop.py status` | – | – | – | – | "Keys working" only checks the keys exist (C6); spend doesn't include Grok or CLI usage |
| **Notifications switches, Remind me** (Settings, Today; D35) | nothing | – | – | – | – | **new**: settings store and push |
| **Theme** (Settings, sidebar; D23) | local | – | – | – | – | store it on the device |

## 3. The approve path (read this before designing anything)

**This is a contract conflict, not only a wiring task.** `AGENTS.md:14` allows only the operator's typed `/approve <slug>` to create `APPROVED`, and nothing may create, edit or delete it otherwise. D2, D13 and D24 want a hold button too. A button path needs the operator to change that rule first, with a design no agent can reach; until then it can't be wired. Synthesising the typed prompt from a button doesn't solve it: the hook proves no human identity, so an agent that can click the button or call what it calls can approve.

Today, approval can only happen one way: the operator's typed prompt `/approve <slug>`, caught by the `UserPromptSubmit` hook before any model sees it (`.claude/hooks/approve.py`). The guard hook blocks every agent tool call that touches a path named `APPROVED`, and any agent that starts a CLI with an `/approve` prompt (`guard_approved.py:37-44`, tested in `tests/test_hooks.py`).

A UI button is a new path that bypasses both hooks unless it's designed not to. A script the button calls could write `APPROVED` directly; anything an agent can call, an agent can call. D24 kept the hold with no Touch ID or Face ID, and the build note in `reviews/ui-direction.md` requires the build to stop agents reaching the button *or what it calls*. Headless agents on this Mac have computer-use and browser tools.

`build-questions.md` has the options; this handoff doesn't choose. Whatever is chosen must keep:

- the digest check;
- the `approved-by` line, recording how the approval was made;
- the typed `/approve` as a backup and as the accessible route (screen readers can't press and hold).

## 4. Progress and outcome signals that exist today

| Source | Signal | Machine-readable? |
|---|---|---|
| `scripts/post_thread.py` | exit 0 / 1 / 2, `REFUSED:` lines, `wait:` line, `POST.txt` | yes |
| `scripts/loop.py` (every subcommand) | JSON on stdout; exit 1 with `{"error": …}` | yes |
| `scripts/snapshot.py` | plain-English lines; the `ledger/runs.log` line `snapshot ok read48=… final=… followers=… api_items=… cost_usd=…` or `snapshot failed error=…` | the log line, yes |
| `scripts/x_api.py`, `x_read.py` | JSON | yes |
| skills (`/next`, `/draft-thread`, `/results`, `/verify-settings`) | prose; fixed closing lines (`/draft-thread`) | no: a UI needs the skills to emit phase markers, or it has to watch the scripts and files they touch |

The working line (D4) promises "the real step". Real phases will need either phase markers added to the skills or instrumentation of the scripts they call. The mock's per-command step lists (`Thinking.dc.html` `STEPS`) are the intended wording.

## 5. Questions commands stop to ask (each becomes a "needs you" state)

| Command | Question | Mock |
|---|---|---|
| `/next` | accept, edit or pick another; open the proposed experiment? | Accept / Pick another |
| `/draft-thread` (build-log) | "What did you build, run or change? What came out?" and three more (`format-build-log/SKILL.md:16-20`) | not shown (only tool-swap drafts exist) |
| `/draft-thread` (tool-verdict) | which tools, which task, same input, how many runs, what each produced | not shown |
| `/draft-thread` (tool-swap) | one optional test offer | not shown |
| `/ready` | "next" between cards | the Posting steps |
| `/posted` | "Roughly how many minutes did this one take, start to finish?"; which slug if unsure | first-hour minutes chips |
| `/results` | export the CSV; the eligibility numbers | the review's needs-you question |
| `/apply` | confirm the change shown | example lesson's Apply (disabled) |
| `/undo-rule` | keep uncommitted edits? | – |

## 6. Mac-only dependencies a phone path must replace

- `pbcopy` and `open -R` in `post_thread.py --copy`.
- `~/Downloads/account_analytics_content_*.csv` for `/results`.
- The Keychain, and the launchd 20:00 job, which runs on wake if the Mac was asleep at 20:00.
- The agent CLIs themselves (Claude Code, Grok Build) run on the Mac, under the operator's subscription limits.
