---
name: format-tool-verdict
description: >
  Tool-verdict format: which tool won a real task the operator ran, the
  test, the evidence, and where the result stops. Used by /draft-thread.
when-to-use: Use for a verdict from real use of two or more AI tools on the same task, or /format-tool-verdict.
---

# Format: tool-verdict

A verdict from the operator's own use: two or more tools given the same task, and what each did. Example: Claude, Codex and Grok as blind reviewers of the same plan. Shared voice: `voice/exit-zero.md`. Different from `comparison` (spec differences that change a purchase) and `tool-swap` (paid to free).

## Material

From the operator's actual runs. Ask: which tools, which task, same input to each, how many runs, and what each produced. No run, no verdict.

## Root

1. **Verdict**: sentence 1 names the winner and the task it won ("For blind code review, Grok caught the most bugs").
2. **Test**: the task and how it was run: same input, how many runs.
3. **Evidence**: 2 to 4 short lines, one per tool, each with what it did (a count, a catch, a miss).
4. **Limit**: where the result stops (one task, n runs, the date and model versions), or where a losing tool still wins.

Under 280 characters when possible, never over 600. The root stands alone.

Optional: one self-reply card with the raw numbers or a screenshot of the outputs side by side. Never more than one card.

## Research and fact-check

`/verify-settings <folder> claims`:
- Every result is an operator-run row with its artifact.
- Model names and versions come from the run itself.
- Prices and plan limits need the vendor's own page, checked this session.
- Never claim a tool is "best" beyond the task and runs tested.

## Images

Real screenshots of the outputs or the run. Never vendor logos or press images.

## Checklist

Copy `.claude/skills/format-tool-verdict/checklist.md` to the draft as `CHECKLIST.md`.
