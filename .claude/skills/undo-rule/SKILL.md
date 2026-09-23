---
name: undo-rule
description: >
  Revert the rule change made for a lesson, using the commit recorded when
  it was applied.
disable-model-invocation: true
argument-hint: "<lesson id, e.g. L-001>"
---

# Undo

1. Run `python3 scripts/loop.py undo --lesson <id>`.
2. On success say: "Reverted <id>. Drafts are back to the rule before it."
3. On error, explain in one plain sentence. "Uncommitted edits" means someone changed that rule file since; ask the operator whether to keep those edits before trying again. "Conflicted" means a later change touched the same lines; nothing was changed, and the fix needs a Claude Code session.
