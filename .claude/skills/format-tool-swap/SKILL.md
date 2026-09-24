---
name: format-tool-swap
description: >
  PAID → FREE series: a fixed two-line header, then 2 to 5 swaps from one
  roster category, each a named paid tool, a free tool, and one sourced
  proof line. Optional one-handle maker shout-out.
  Used by /draft-thread.
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
  | Product Analytics & Support | support (revisit before that post: PostHog is analytics) |

- **Rows.**
  - 2 to 5 swaps, all from one category. Each is `Paid → Free`, then `▷ ` and one proof line.
  - Strongest rows first: the feed shows the start of a long post and hides the rest behind "Show more".
  - At most 600 characters as X counts them (`→` and `▷` count 2). Check with `python3 scripts/post_thread.py <folder> --count`.
- **A single.** One swap with up to three `▷` lines, only for a tool held back for one: OBS, Krita, KeePassXC, Pi-hole.
- **Paid side.**
  - One named product per row, never a description ("Paid chat apps", "Paid VPN mesh").
  - When the roster names several, pick the one people on X actually talk about: check with `python3 scripts/x_read.py search "<query>"`, never a raw Grok search.
  - If the paid product has a free plan, name the paid tier ("Streamlabs Ultra", "Copilot Pro") or cut the row.
- **Free side.**
  - Say "free".
  - Say "open source" only when `CLAIMS.md` shows it. Photopea isn't, and neither are Raycast or OrbStack.
- **Proof lines.**
  - Positive, specific, short, and true as written for the task they name.
  - Written from the sources (and the operator's test, if there is one), never paraphrased from the roster.
  - Name the job the free tool does, never "replaces" or a promised 1:1 swap.
  - No feature sheets ("3D Modeling, Sculpting and printing, …"), no changelog or LTS wording, no negatives. Limits live in `CLAIMS.md` and `REPLIES.md`.
- **No @handles, hashtags or `1/5`** in the root; the gate refuses them.
- **The payoff stands alone.** A stranger who sees only the root gets every swap.

## Research, and an optional test

Research is enough: every row stands on the vendors' own pages (below). Testing isn't a gate (operator, 24 Sep 2026: "I don't need to test something to research and understand it").

A test adds value when it's easy. Offer it once per draft, never as a condition. The operator already uses Photopea, DaVinci Resolve, OBS and Obsidian, and a quick test (for example "open a layered PSD in Photopea") gives the post:
- a real screenshot;
- a `tested` row;
- first-hand proof. X's rewards program counts content "you have personally created" and not "aggregated summaries" ([X Help Center](https://web.archive.org/web/20260916150107/https://help.x.com/en/using-x/original-content-rewards)). What makes a PAID → FREE post the operator's own is the choice of swaps and the judgement in the proof lines; a test or screenshot adds to that.

A test matters in one case: when the vendor's page doesn't state a claim (post 1's "No watermark" is the example), a test is the only way that claim reaches a card. Otherwise the claim, not the row, is cut.

## Research and fact-check

`/verify-settings <folder> claims` writes `CLAIMS.md` in its usual table. Each swap needs these rows:

- **The task it does:** from the free tool's own feature page ("opens and saves PSDs"). `vendor-stated`, or `tested` with a screenshot when the operator tried it.
- **Free tier covers the task:** from the free tool's own pricing or feature page, checked this session.
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
- **No "Next one is…" teaser.**

Handles checked with `x_api.py user` on 24 Sep 2026:

| Handle | Account | Verified | Last post |
|---|---|---|---|
| `@photopeacom` | Photopea | no | 9 Sep |
| `@Blackmagic_News` | Blackmagic Design (news account; help lives on its forum) | business | 20 Sep |
| `@Blender` | Blender | blue | 23 Sep |
| `@OBSProject` | OBS | business | 19 Sep |
| `@use_bruno` | Bruno | blue | 23 Sep |
| `@obsdmd` | Obsidian (not `@Obsidian`, a game studio) | blue | 16 Sep |
| `@ollama` | ollama | business | 23 Sep |
| `@kritaartists` | Krita Artists, the community account that posts Krita releases (confirm it speaks for the project before tagging) | no | 16 Sep |
| `@Krita_Painting` | **doesn't exist.** Post 1 tagged it | – | – |

Re-check a handle in the post's own session; accounts change.

## REPLIES.md

Talking points for replies under the post, with sources. Never paste-ready: the operator writes every reply (`voice/exit-zero.md`, and the reply scorer sees pasted text, A12).

- One point per `CLAIMS.md` limit, and one per paid side that has a free plan ("Streamlabs Desktop is free; Ultra is the paid layer").
- Answer the row the person raised, in one or two sentences. Don't defend all five.
- Never edit the root to add a caveat.

## Images

Optional. A real screenshot from the operator's own use is the best image the post can carry. Never vendor logos or press images, never anything in `images/sources/`.

## Series operations

- **Cadence:** one PAID → FREE parent every other day, inside the account's cap of two originals a day, hours apart (operator, 24 Sep 2026). Categories go in `queue/topics.yaml` order.
- **Pin:** pin the newest PAID → FREE post that's live, sourced and unboosted, with no link (A14). The operator pins on X.
- **Makers:** the rules in `voice/exit-zero.md` → Makers. One maker touch a day; repost only makers' release posts; quote only makers' news; never quote a premium vendor to pick a fight.
- **Never boost** (`voice/exit-zero.md` → Boosting).

## How it's judged

Root only, on organic engagement and visits per organic impression at the 36–60 hour read (the loop's rules). Bookmarks aren't a ranking weight (A19); copy-link shares are (A9) but aren't visible (`queue/research-backlog.md` item 2). With the header and shape fixed, category can be the one variable in an experiment once experiments resume.

## Settled (don't reopen unless the operator does)

- After Effects over Cinema 4D for Blender's row, and Streamlabs Ultra over Camtasia for OBS's.
- "Finding" over "I found".
- No job-first hooks ("Need to open a PSD without Photoshop?").
- The category word, not the roster's long category titles.

## Checklist

Copy `.claude/skills/format-tool-swap/checklist.md` to the draft as `CHECKLIST.md`.
