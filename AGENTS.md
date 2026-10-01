# thread-engine

Local factory for @exitzerocode X posts. The loop measures which posts grow the account and writes that into the drafting rules. Drafts are the product. Posting stays manual.

## Operating rules

- The operator does not code or run scripts. Every step is a slash command (skills in `.claude/skills/`); the agent runs the scripts.
- Start non-trivial work in Plan mode.
- One topic per draft folder.
- Every path and claim is sourced. Unverified ones are VERIFY and stay out of cards.
- The account posts by hand only. Never post, schedule, or call an X write API.
- The account's own numbers come from `scripts/x_api.py` (read-only keys in the Keychain; the keys never enter a session). Other people's posts and research come from `scripts/x_read.py` (X API recent search). It is the one route to X evidence: cite a post only from its output. Two lookups stay on `scripts/x_api.py`: `mentions` (replies to the account; their text stays out of reviews) and `user <handle>` (a maker's profile; no post is cited). The global `grok-delegation` route for X evidence does not apply in this repo.
- `APPROVED` is created only by the operator's typed `/approve <slug>` (a hook does it; another hook blocks every agent attempt). Never create, edit or delete it. When a draft needs approval, tell the operator to type `/approve <slug>`.
- Before writing a post, reply or quote, or advising on posting, replying, promotion or maker outreach, read `voice/exit-zero.md`. Before judging a post's lane or audience fit, read `reference/audience.md`. The draft and loop skills already do this.
- Knowledge lookup: read `research/index.md` first, then only the pages it names. Save a multi-source cited answer to `research/<date>-<slug>.md` (quote-or-drop citations, an index line, a `reviews/log.md` line) only after the operator says yes. The parent agent indexes literature-reader reports; the reader never edits the index.
- Loop state (`loop/state.json`, `ledger/*.json`) changes only through `scripts/loop.py`. The generated `experiments.md`, `learnings.md` and `ledger/SUMMARY.md` are never hand-edited.

## What the loop may never change

Approval (`/approve`), the truth budget, fail-closed fact-checks, the shared gate refusals, and the no-X-writes rule. Lessons may change format, length, lane mix, hook style, timing and topic choice, through `/apply` only.

## Current state

Each line holds until its exit condition; skills point here instead of restating it.

- Experiments are paused until 2026-10-08, two weeks of organic X API data from 2026-09-24 (`reviews/audit-2026-09.md`). `/next` proposes posts with no experiment arm. On or after that date `/next` asks the operator whether to lift the pause; the operator's yes rewrites this line to "Experiments are running since <date>".
- Formats are on trial until 2026-10-08: `/next` and `/results` report the `main` and `other` lane share against the target in `reference/audience.md` and do not refuse an `other` post for a low share. The operator's yes to lifting the experiment pause ends the trial; rewrite this line then.
- The `main` lane covers tech broadly since 2026-09-24, until the operator narrows it to building (`reference/audience.md`).

## Layout

- `research/index.md` catalogues `research/`, `reference/`, `reviews/`, `queue/` and `receipts/`; `reviews/log.md` is the append-only log of ingests, decisions and lints.
- `reference/x-algorithm.md` holds verified X ranking facts (cited as A1, A2…); `reference/x-api.md` holds what the X API can read, prices and privacy rules.
- `queue/topics.yaml` is the Queue of Topics; `queue/research-backlog.md` is operator-chosen research to do later; `queue/paid-free-roster.md` lists PAID → FREE claims to check, never copy.
- `drafts/<date>-<slug>/` holds numbered cards (`01-hook.md` …), which are the posts. `shipped/<slug>/NOTES.md` holds post-ship notes.
- `ledger/*.json` and `ledger/activity/` are written only by `loop.py`. `ledger/raw/` is written by `snapshot.py`, `x_api.py` and `/posted`. `loop/inbox/`, `loop/followers/` and `ledger/raw/api/` hold other people's data and are not committed.
- `scripts/post_thread.py` is the gate: it refuses without `APPROVED`, and applies the format and voice checks. Read the script for the exact refusals; `--count` prints X's character counts with no approval.
- Working in `scripts/loop_core`: read `scripts/loop_core/README.md` first.
- `scripts/jev_referee.py` runs as a hook in shadow mode and appends `receipts/decisions.jsonl`. It needs no action; commit the receipt as `chore(data)` when it is the only change.
- Tests: `python3 -m unittest discover -s tests` (it also runs `research/jev-test/test_*.py`, which pin skill sentences by line number: a skill edit that moves one fails there until `conflict_items.json` is re-pinned).

## Cloud session notes

- In a cloud session the X API keys (macOS Keychain) are not available: skip snapshot/metrics that need them and use committed ledger/ and reviews/ instead.

## Git

- Agents commit straight to `main`; this is a solo project with no PR review.
- Analysis and audits go in `reviews/`; cited research goes in `research/` after the operator says yes. Not `docs/` or `claudedocs/`.
- Conventional commits. `loop.py` commits data (`chore(data)`) and applied rules (`feat(rules)`).
- `APPROVED` files are git-ignored. Never commit secrets or X tokens.
