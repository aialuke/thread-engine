---
name: format-tool-swap
description: >
  PAID → FREE series: a fixed two-line header, then 2 to 5 swaps from one
  roster category, each a named paid tool, a free tool, and one sourced
  proof line. Optional one-handle maker shout-out. Use for a PAID → FREE
  post, a paid-to-free swap list, free alternatives, or /format-tool-swap.
disable-model-invocation: true
when-to-use: Use for a PAID → FREE post, a paid-to-free swap list, free alternatives, or /format-tool-swap.
---

# Format: tool-swap (the PAID → FREE series)

A series with a fixed header. Each post covers one category of the roster (`queue/paid-free-roster.md`). Shared voice: `voice/exit-zero.md`. Post 1 (`2102737637346095128`, notes in `shipped/paid-to-free-tools/`) is the shape reference only: it was boosted, its "No watermark" had no source, and it went out before these rules. The decisions behind the series are in `reviews/paid-free-session-2026-09.md`.

## Root

```
PAID → FREE
Finding free <word> tools that actually hold up.

Paid product → Free tool
▷ One proof line.
```

- **Header.** The two lines are fixed; the gate refuses a root that doesn't open with them. The caps label is the series' one exception to sentence case. `<word>` by roster category:

  | Category | Word |
  |---|---|
  | Creative & Motion Graphics | creator |
  | Productivity & Office Suites | productivity |
  | Developer Tools | developer |
  | Network Security & Privacy | privacy |
  | System Utilities | system |
  | Cloud Storage | storage |
  | Diagrams & Vector | diagram |
  | Finance | finance |
  | Local AI | local AI |
  | Self-Hosting | self-hosting |
  | Product Analytics & Support | support |

The word for Product Analytics is support until the operator names another. PostHog is analytics.

- **Rows.**
  - 2 to 5 swaps, all from one category. Each is `Paid → Free`, then `▷ ` and one proof line.
  - Strongest rows first: the feed shows the start of a long post and hides the rest behind "Show more".
  - At most 600 characters as X counts them (`→` and `▷` count 2). That 600 is tool-swap's `root_limit` in `scripts/formats.py`. Check with `python3 scripts/post_thread.py <folder> --count`.
- **A single.** One swap with up to three `▷` lines, only for a tool held back for one: OBS, Krita, KeePassXC, Pi-hole.
- **Paid side.**
  - One named product per row, never a description ("Paid chat apps", "Paid VPN mesh").
  - When the roster names several, pick the one people on X actually talk about: check with `python3 scripts/x_read.py search "<query>"`.
  - If the paid product has a free plan, name the paid tier ("Streamlabs Ultra", "Copilot Pro") or cut the row.
- **Free side.**
  - Say "free".
  - Say "open source" only when `CLAIMS.md` shows it.
- **Proof lines.**
  - Positive, specific, short, and true as written for the task they name.
  - Written from the sources (and the operator's test, if there is one), never paraphrased from the roster.
  - Name the job the free tool does, never "replaces" or a promised 1:1 swap.
  - Plain words on the one job the tool does. Feature lists, changelog wording and LTS wording stay out, and so do negatives: limits live in `CLAIMS.md` and `REPLIES.md`.
- **No @handles, hashtags or `1/5`** in the root; the gate refuses them.
- **The payoff stands alone.** A stranger who sees only the root gets every swap.

## Research, and an optional test

Research is enough: every row stands on the vendors' own pages (below). Testing isn't a gate, and `background.md` says why.

A test adds value when it's easy. Offer it once per draft, never as a condition. When the operator already uses a swap's free tool, a quick test (for example "open a layered file in <tool>") gives the post a real screenshot, a `tested` row and first-hand proof.

A test matters in one case: when the vendor's page doesn't state a claim (post 1's "No watermark" is the example), a test is the only way that claim reaches a card. Otherwise the claim, not the row, is cut.

## Research and fact-check

`/verify-settings <folder> claims` writes `CLAIMS.md` in its usual table. Each swap needs these rows:

- **The task it does:** from the free tool's own feature page ("opens and saves PSDs"). `vendor-stated`, or `tested` with a screenshot when the operator tried it.
- **Free tier covers the task:** from the free tool's own pricing or feature page, checked in this verify run.
- **The paid side is paid:** from the paid product's pricing page. If it has a free plan, the row says so and the card names the paid tier.
- **The limit that matters:** quota, resolution cap, watermark, ads, platform, account needed. It feeds `REPLIES.md`.
- **The shout-out:** its claim, with a recent source, and "handle checked with `python3 scripts/x_api.py user <handle>` on <date>": the right account, posting recently.

A swap with no official page for its task is cut, not softened.
- "Settled" choices below are editorial. They never excuse a claim: every line still goes through `CLAIMS.md` and `/approve`, and a line with no source is cut.

## Shout-out card (optional, the one card allowed)

- **One line, one handle:** a free tool's **organisation** account. Never a person, never a premium vendor.
- **A short thank-you** that is true now ("still ships features and answers people"). Not a changelog, no version numbers, no em-dash stack. Its claim gets a `CLAIMS.md` row with a recent source.
- **Never reused:** post 1's five-tag block is never reused, and no two shout-outs share wording (A13).
- **Posted 10–20 minutes after the root,** as a reply to it. The run sheet and `/ready` say so, and `/posted` waits until it's live.
- **Ends at the thank-you.** The card carries nothing about the next post.

Check every handle with `python3 scripts/x_api.py user <handle>` in the post's own verify run; accounts change. Earlier checks are in `shipped/paid-to-free-tools/NOTES.md`.

## REPLIES.md

Talking points for replies under the post, with sources (`voice/exit-zero.md` → Replies).

- One point per `CLAIMS.md` limit, and one per paid side that has a free plan ("Streamlabs Desktop is free; Ultra is the paid layer").
- Answer the row the person raised, in one or two sentences. Don't defend all five.
- Never edit the root to add a caveat.

## Images

Optional. A real screenshot from the operator's own use is the best image the post can carry. Never vendor logos or press images, never anything in `images/sources/`.

## Series operations and judging

Cadence, pinning, maker and boosting rules, and how the series is judged are in `.claude/skills/format-tool-swap/background.md`. Read it when scheduling or pinning a post or reading results; drafting doesn't need it.

## Settled (don't reopen unless the operator does)

- After Effects over Cinema 4D for Blender's row, and Streamlabs Ultra over Camtasia for OBS's.
- "Finding" over "I found".
- Hooks open on the category header, so the root leads with the header, never a job question.
- The category word, not the roster's long category titles.

## Checklist

Copy `.claude/skills/format-tool-swap/checklist.md` to the draft as `CHECKLIST.md`.
