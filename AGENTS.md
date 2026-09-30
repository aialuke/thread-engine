# thread-engine

Local factory for @exitzerocode X posts, with a learning loop: compelling content → engagement → account growth. Drafts are the product; the loop measures what works and feeds it back into the drafting rules. Posting stays manual.

## Operating rules

- The operator does not code or run scripts. Every step is a slash command (skills in `.claude/skills/`); the agent runs the scripts.
- Start non-trivial work in Plan mode.
- One topic per draft folder.
- Every path and claim is sourced. Unverified ones are VERIFY and stay out of cards.
- The account posts by hand only. Never post, schedule, or call an X write API.
- The account's own numbers come from `scripts/x_api.py` (read-only keys in the Keychain; the keys never enter a session). Other people's posts and research come from Grok's X tools or `scripts/x_read.py`, and only a post that passed its id check may be cited.
- `APPROVED` is created only by the operator's typed `/approve <slug>` (a hook does it; another hook blocks every agent attempt). Never create, edit or delete it.
- Before writing a post, reply or quote, or advising on posting, replying, promotion or maker outreach, read `voice/exit-zero.md`. Before judging a post's lane or audience fit, read `reference/audience.md`. The draft and loop skills already do this.
- Knowledge lookup: read `research/index.md` first, then only the pages it names. Save a multi-source cited answer to `research/<date>-<slug>.md` (quote-or-drop citations, an index line, a `reviews/log.md` line) only after the operator says yes. The parent agent indexes literature-reader reports; the reader never edits the index.
- Loop state (`loop/state.json`, `ledger/*.json`) changes only through `scripts/loop.py`. The generated `experiments.md`, `learnings.md` and `ledger/SUMMARY.md` are never hand-edited.

## What the loop may never change

Approval (`/approve`), the truth budget, fail-closed fact-checks, the shared gate refusals, and the no-X-writes rule. Lessons may change format, length, lane mix, hook style, timing and topic choice, through `/apply` only.

## Layout

- `research/index.md` catalogues `research/`, `reference/`, `reviews/`, `queue/` and `receipts/`; `reviews/log.md` is the append-only log of ingests, decisions and lints.
- `reference/x-algorithm.md` holds verified X ranking facts (cited as A1, A2…); `reference/x-api.md` holds what the X API can read, prices and privacy rules.
- `queue/topics.yaml` is the Queue of Topics; `queue/research-backlog.md` is operator-chosen research to do later; `queue/paid-free-roster.md` lists PAID → FREE claims to check, never copy.
- `drafts/<date>-<slug>/` holds numbered cards (`01-hook.md` …), which are the posts. `shipped/<slug>/NOTES.md` holds post-ship notes.
- `ledger/activity/` and `ledger/raw/` are written only by `loop.py`. `loop/inbox/`, `loop/followers/` and `ledger/raw/api/` hold other people's data and are not committed.
- `scripts/loop_core/reads.py` holds the Read-window rules (48h, Final and Backfill read thresholds, due/missed, due-reads windows) as pure functions; `scripts/loop.py` stays the only writer and calls it.
- `scripts/post_thread.py` is the gate: it refuses without `APPROVED`, and applies the format and voice checks. Read the script for the exact refusals; `--count` prints X's character counts with no approval.
- `scripts/loop_core/health.py` holds the Daily-run warnings (a run over 26 hours old, a failed last run, a Final read inside its last 48 hours) as pure functions; `loop.py status` reads `ledger/runs.log` and returns them as `health.warnings`, and `/next` says them first.
- `scripts/loop_core/payloads.py` holds what each Payload must look like (validators, defaults, the keys and coercions of the six payload commands) as pure functions; `errors.py` and `times.py` hold `LoopError`/`need` and `parse_time`/`iso`. The messages are part of the CLI.
- `scripts/loop_core/snapshots.py` holds Snapshot admission (`admit_snapshot`: the ordered refusals and skips of record-snapshot); `scripts/loop_core/experiments.py` holds the open states, `TRANSITIONS`, `round_result`, `evaluate_rounds` (a Round's effect on an Experiment, returning new state) and `next_slot`. Both are pure. `scripts/loop.py` keeps the reads, the check order relative to them, the saves and the render; what it reads and when is part of the CLI, so move a read only with a test that pins it (`tests/test_decisions_contract.py`).
- Tests: `python3 -m unittest discover -s tests`.

## Cloud session notes

- In a cloud session the X API keys (macOS Keychain) are not available: skip snapshot/metrics that need them and use committed ledger/ and reviews/ instead.

## Git

- Conventional commits. `loop.py` commits data (`chore(data)`) and applied rules (`feat(rules)`).
- `APPROVED` files are git-ignored. Never commit secrets or X tokens.

## Agent skills

- Issues live in GitHub Issues (`aialuke/thread-engine`) via `gh`; see `docs/agents/issue-tracker.md`.
- Triage labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`; see `docs/agents/triage-labels.md`.
- Domain docs: one `CONTEXT.md` and `docs/adr/` at the repo root; see `docs/agents/domain.md`.
- When the user grilling a design card says it is ready for Jev, follow `.claude/skills/jev-card/SKILL.md`.
