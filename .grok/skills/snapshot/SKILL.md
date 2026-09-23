---
name: snapshot
description: >
  Take the 36-60 hour snapshots that are due and record them in the ledger.
  Runs daily from the scheduled job, and first thing inside /next.
disable-model-invocation: true
---

# Snapshot

Run `python3 scripts/snapshot.py` and relay its lines to the operator in plain words. It makes one read-only Grok call for the X numbers and does the rest in code. If it fails, say what failed in one sentence; nothing is recorded from a failed run, and posts stay due until their window closes.
