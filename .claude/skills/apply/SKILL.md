---
name: apply
description: >
  Make the rule change a weekly review proposed for an adopted lesson, and
  commit it so /undo-rule can revert it.
disable-model-invocation: true
argument-hint: "<lesson id, e.g. L-001>"
---

# Apply

1. Read `learnings.md`. The lesson must be `adopted` with rule `none`. Otherwise say why not and stop.
2. Find the proposed change for this lesson in the latest `reviews/week-*.md`. Show it to the operator in one sentence and the file it touches.
3. Edit only that file, under `.claude/skills/` or `voice/`. Keep the change to what the review proposed. Never touch `APPROVED`, the gate script, `AGENTS.md`, or the truth budget.
4. Run `python3 scripts/loop.py commit-rule --lesson <id> --files <path>`.
5. Say: "Applied <id>. Drafts follow it from now on. Type /undo-rule <id> to take it back."
