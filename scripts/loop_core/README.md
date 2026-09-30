# loop_core

Pure functions behind `scripts/loop.py`, which stays the only writer. Read this before changing anything in this folder.

- `reads.py` holds the Read-window rules (48h, Final and Backfill read thresholds, due/missed, due-reads windows) as pure functions; `scripts/loop.py` stays the only writer and calls it.
- `health.py` holds the Daily-run warnings (a run over 26 hours old, a failed last run, a Final read inside its last 48 hours) as pure functions; `loop.py status` reads `ledger/runs.log` and returns them as `health.warnings`, and `/next` says them first.
- `payloads.py` holds what each Payload must look like (validators, defaults, the keys and coercions of the six payload commands) as pure functions; `errors.py` and `times.py` hold `LoopError`/`need` and `parse_time`/`iso`. The messages are part of the CLI.
- `snapshots.py` holds Snapshot admission (`admit_snapshot`: the ordered refusals and skips of record-snapshot); `experiments.py` holds the open states, `TRANSITIONS`, `round_result`, `evaluate_rounds` (a Round's effect on an Experiment, returning new state) and `next_slot`. Both are pure. `scripts/loop.py` keeps the reads, the check order relative to them, the saves and the render; what it reads and when is part of the CLI, so move a read only with a test that pins it (`tests/test_decisions_contract.py`).

Tests: `python3 -m unittest discover -s tests`.
