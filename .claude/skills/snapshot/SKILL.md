---
name: snapshot
description: >
  Read the account's own posts, replies, followers and mentions from the X API
  and record them in the ledger. Runs daily from the scheduled job, and first
  thing inside /next.
disable-model-invocation: true
---

# Snapshot

Run `python3 scripts/snapshot.py` and relay its lines to the operator in plain words. It reads the X API through `scripts/x_api.py` (read-only keys in the Keychain) and records everything through `loop.py`. If it fails, say what failed in one sentence: nothing is recorded from a failed run and nothing moves on, so the next run picks the same posts up. A Keychain or credit error means the operator has to unlock the Mac or top up credits in the X developer console.
