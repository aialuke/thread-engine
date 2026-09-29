---
name: snapshot
description: >
  Read the account's own posts, replies, followers and mentions from the X API
  and record them in the ledger.
disable-model-invocation: true
---

# Snapshot

1. Run `python3 scripts/snapshot.py`.
2. Done when the operator has its lines in plain words, or its failure in one sentence:
   - "The X read failed": nothing was recorded and nothing moved on; the next run picks the same posts up. If the error names the Keychain or credits, the operator has to unlock the Mac or top up credits in the X developer console.
   - "failed while at stage": some records may be partly written. Say so and tell the operator to run /next.
