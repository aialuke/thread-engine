---
name: format-build-log
description: >
  Build-log format: one standalone post on what the pipeline did, with
  real proof attached, how, and what broke. Used by /draft-thread.
when-to-use: Use for a build-in-public update, what the pipeline did today, or /format-build-log.
---

# Format: build-log

One post from the build: what the idea-to-video pipeline (or another tool the operator made) actually did, shown with real proof. Shared voice: `voice/exit-zero.md`. Audience: `reference/audience.md`.

## Material

The material comes from the operator, not from research. Before any card, ask in plain words:

1. What did you build, run or change? What came out?
2. Which step or tool made it work (which agent did what)?
3. What broke, surprised you, or is still bad?
4. What real proof can you attach: a screenshot, screen recording or output file?

No real proof, no build log. Offer a different format instead.

## Root

1. **Result**: sentence 1 says what came out, concretely ("idea in, 90-second script and voiceover out").
2. **How**: one or two sentences on the step or tool that made it work.
3. **Broke**: one honest line on what didn't work or what's next.
4. **Proof**: the attachment. The text points at it without overselling it.

Under 280 characters when possible, never over 600. The root stands alone.

Optional: one self-reply card with the detail a builder would ask for (the prompt, the numbers, the agent setup). Never more than one card.

## Research and fact-check

`/verify-settings <folder> claims`. Every figure (time, cost, count) is an operator-run row with its artifact; see the claims-mode rule for the operator's own run. Any claim about a vendor's product is a normal claims row with an official source.

## Images

Required: real screenshots, screen recordings or output of the actual run. AI-made images never stand in for the output.

## Checklist

Copy `.claude/skills/format-build-log/checklist.md` to the draft as `CHECKLIST.md`.
