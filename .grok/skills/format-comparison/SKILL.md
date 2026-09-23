---
name: format-comparison
description: >
  Comparison format: new product against the one it replaces. Comparison
  hook, difference cards, comparison closer. Used by /draft-thread.
when-to-use: Use for a product comparison thread, or /format-comparison.
---

# Format: comparison

Use when the villain is that the new product looks like last year's. Shared voice: `voice/exit-zero.md`. Gold: `examples/iphone-18-pro-aperture.md`, read with `shipped/iphone-18-pro-aperture/NOTES.md` (it lists what not to copy).

## Root (comparison hook)

1. **Both products** — the first sentence names them.
2. **Question** — one question a scroller already understands.
3. **✓ matches** — what is the same. Each match on its own line, starting with `✓`.
4. **Count** — how many things differ, and the one that matters most to a buyer. The root must stand alone.
5. **🧵** — the mark alone.

The count and the number of difference cards match.

## Difference card

`N. Plain name`. A product term shares that line with what it does.

1. **Title**
2. **Use** — the next sentence is what a person notices
3. **Spec** — the sourced figures, for the model they apply to
4. **Path** — only when `PATHS.md` has a control for this difference

One difference per post. Numbers run from 1, never repeat, and match the hook's count.

## Closer

- Open with `The full pass`
- One `✓` line per difference, written `name = payoff`, using that card's figure and model
- Reply ask names the fork: which model the reader has now. Never "your thoughts", never 💬.

## Research and fact-check

- `/verify-settings <folder> claims` writes `CLAIMS.md`: every figure with its official source and date. Any control path goes in `PATHS.md`.
- Only official vendor pages or the operator count as sources.

## Images

Own photos, or a labelled illustration. Never vendor press images.

## Checklist

Copy `.grok/skills/format-comparison/checklist.md` to the draft as `CHECKLIST.md`.
