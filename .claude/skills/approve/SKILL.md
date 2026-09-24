---
name: approve
description: >
  Operator only. Registers /approve so the app accepts it; the approve hook
  does the work before the model sees anything.
disable-model-invocation: true
argument-hint: "<slug>"
---

# Approve

This file exists so Claude Code and Grok accept `/approve <slug>` as a command. Without it, Claude Code stops at "Unknown command" and the prompt never reaches `.claude/hooks/approve.py`.

When the operator types `/approve <slug>`, the hook writes the approval and blocks the prompt, so this text is never shown to the model.

If you are reading this, the approval did **not** happen. Do not create, edit or delete the approval marker, and do not try another way to approve. Tell the operator in one sentence: "Nothing was approved: the approve hook didn't run. Type `/approve <slug>` exactly, on its own line, with nothing else in the message."
