---
name: format-tool-swap
description: >
  Paid-to-free tool swap format: paid tool, free replacement, one line on
  what it does, each swap checked against a concrete task. Used by
  /draft-thread.
when-to-use: Use for a paid-to-free swap list, free alternatives, or /format-tool-swap.
---

# Format: tool-swap

A list of swaps: `Paid → Free`, then one line on what the free tool does for a concrete task. Shared voice: `voice/exit-zero.md`. Reference post: `2102737637346095128`, for shape only. Its "No watermark" line had no source, which is what `CLAIMS.md` now prevents.

## Root

- Line 1 names the payoff: what the reader stops paying for.
- 3 to 6 swaps, each on its own two lines: `Paid → Free`, then `▷ ` plus the concrete task it handles.
- The root carries every swap. It must be worth bookmarking with no replies.
- Optional one self-reply card: why each free tool is trustworthy (maintained, recent release). Never more than one card.

## Research and fact-check

For every swap, `/verify-settings <folder> claims` writes a `CLAIMS.md` row:

| Swap | Task | Free tier covers it? | Limit that matters | Source URL | Date | Vendor-stated or tested |

- **Task:** one concrete job, for example "export a 1080p video without a watermark".
- **Free tier covers it:** yes, only from the vendor's own pricing or feature page, checked this session.
- **Limit that matters:** quota, resolution cap, watermark, platform, account needed.
- A swap with no official page for the task is cut, not softened.
- "Tested" only when the operator says they ran it.

## Images

None needed. Never vendor logos or press images.

## Checklist

Copy `.grok/skills/format-tool-swap/checklist.md` to the draft as `CHECKLIST.md`.
