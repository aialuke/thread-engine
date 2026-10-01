# loop_core

Pure functions behind `scripts/loop.py`, which stays the only writer. Read this before changing anything in this folder.

- `reads.py` holds the Read-window rules (the 48h read position, Final and Backfill thresholds, due/missed, due-reads windows) as pure functions; `scripts/loop.py` stays the only writer and calls it.
- `health.py` holds the Daily-run warnings (a run over 26 hours old, a failed last run, a Final read inside its last 48 hours) as pure functions; `loop.py status` reads `ledger/runs.log` and returns them as `health.warnings`, and `/next` says them first.
- `payloads.py` holds what each Payload must look like (validators, defaults, the keys and coercions of the six payload commands) as pure functions; `errors.py` and `times.py` hold `LoopError`/`need` and `parse_time`/`iso`. The messages are part of the CLI.
- `snapshots.py` holds Snapshot admission (`admit_snapshot`: the ordered refusals and skips of record-snapshot); `experiments.py` holds the open states, `TRANSITIONS`, `round_result`, `evaluate_rounds` (a Round's effect on an Experiment, returning new state), `next_slot`, lesson freshness (`lesson_is_stale`, from `last_evidence_at`), `rule_application` (the latest rules entry), membership (outside, or in on treatment or control) and `leave_experiment` (a deviation, or a violation with `leaves`). `rates.score_for` chooses the snapshot a cohort or a round may score. All three are pure. `scripts/loop.py` keeps the reads, the check order relative to them, the saves and the render; what it reads and when is part of the CLI, so move a read only with a test that pins it (`tests/test_decisions_contract.py`).
- `scripts/formats.py` holds each draft Format (root cap, root checks, card bound, the note after card 1) and the ledger name `other`. The gate and `payloads.py` read it.
- `views.py` holds the generated views (`ledger/SUMMARY.md`, `experiments.md`, `learnings.md`) as pure text builders; `loop.py`'s `render` reads the repo and writes what they return.

Tests: `python3 -m unittest discover -s tests`.
