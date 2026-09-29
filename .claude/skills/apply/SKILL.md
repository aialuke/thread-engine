---
name: apply
description: >
  Make the rule change a weekly review proposed for an adopted lesson.
disable-model-invocation: true
argument-hint: "<lesson id, e.g. L-001>"
---

# Apply

1. Read `learnings.md`. The lesson must be `adopted` with rule `none`. Otherwise say why not and stop.
2. Find the proposal for this lesson in the latest `reviews/week-*.md`. Proceed only with one that names the lesson id, the file and the exact sentence. Otherwise say what is missing and stop. Show it to the operator in one sentence with the file it touches, then make it.
3. Stop if that file has uncommitted changes: the rule commit would take them too. Edit only that file, under `.claude/skills/` or `voice/`. Keep the change to what the review proposed, and check `git diff` shows only that. Never touch `APPROVED`, the gate script, `AGENTS.md`, or the truth budget.
4. Run `python3 scripts/loop.py commit-rule --lesson <id> --files <path>`. On error, say it in one sentence and stop: a commit may already exist, so the fix needs a Claude Code session.
5. After a clean exit, say: "Applied <id>. Drafts follow it from now on. Type /undo-rule <id> to take it back."
