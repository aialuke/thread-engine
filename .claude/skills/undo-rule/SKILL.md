---
name: undo-rule
description: >
  Revert the rule change made for a lesson.
disable-model-invocation: true
argument-hint: "<lesson id, e.g. L-001>"
---

# Undo

1. Run `python3 scripts/loop.py undo --lesson <id>`.
2. On success say: "Reverted <id>. Drafts are back to the rule before it."
3. On error, explain in one plain sentence, then stop:
   - "Uncommitted edits": someone changed that rule file since. Ask the operator whether to keep those edits, and run the command again only after they answer.
   - "Conflicted": a later change touched the same lines; nothing was changed, and the fix needs a Claude Code session.
   - "no lesson" or "no applied rule": say which, and that there is nothing to revert.
