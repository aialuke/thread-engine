# Thread Engine mock — design system (build handoff)

Source: mock version 22 (`ui/mock/project/Main.dc.html` = iPhone, `ui/mock/project/Mac.dc.html` = Mac). Both files are **generated** — `ui/mock/src/build.py` assembles them from `ui/mock/src/build_body.py` (iPhone body + shared style constants), `ui/mock/src/build_mac.py` (Mac layout wrapping the same body pieces), and `ui/mock/src/main_script.js` (shared state/interaction logic, templated with `__DEVICE__` = `phone` or `mac`). The `<helmet><style>` block is byte-identical in both files (tokens, global rules, keyframes). Citations below use paths relative to the repo root; line numbers are from the source files (the generated `.dc.html` files carry the same content, since the `<helmet>` is copied verbatim and the body strings are copied verbatim with `{{`/`}}` unescaped).

Decision citations: `reviews/ui-direction.md` (`D#`). Review citations: `reviews/ui-review-2026-09-24.md` (24-Sep review, parts A/B/C/D) and `reviews/ui-review-2026-09-25.md` (25-Sep review, findings #1–47, fixed in mock v22).

---

## 1. Colour tokens

All tokens are CSS custom properties on `.te-root`, three blocks, byte-identical in `Main.dc.html` and `Mac.dc.html`:

- **Light** (default): `.te-root{color-scheme:light; --token:#value; …}` — `ui/mock/project/Main.dc.html:23`
- **Dark** (`data-theme="dark"`, explicit choice): `.te-root[data-theme="dark"]{color-scheme:dark; …}` — `ui/mock/project/Main.dc.html:24`
- **System** (`data-theme="system"`, the default, follows the OS): `@media (prefers-color-scheme: dark){.te-root[data-theme="system"]{…}}` — `ui/mock/project/Main.dc.html:25`. Values here are **identical** to the dark block — system mode is "dark values gated by a media query," not a third palette. In light OS, `data-theme="system"` simply keeps the light block's values (no override needed since the light block already applies to `.te-root` unconditionally, and only the dark media query is conditional).

Per D21, dark is a **separately authored palette**, not an inversion filter: `--btn` flips from near-black to near-white (so the primary button is light-on-dark, not a darkened black), `--hold-fill` swaps from the link blue to the light blue, `--chart-on`/`--chart-off` are re-picked hues (not just lightened), and text/border ramps use warm charcoal, not a literal `invert()`.

| Token | Light | Dark | Meaning / used by |
|---|---|---|---|
| `--paper` | `#F3F1EA` | `#15140F` | Page background ("warm paper" D20 → "warm charcoal" D21). `body` bg and `.te-root` bg. |
| `--card` | `#FFFFFF` | `#201F19` | Card/article surface. `CARD` constant (`ui/mock/src/build_body.py:5`). |
| `--raised` | `#FBFAF6` | `#1B1A15` | Slightly-lifted surface: `SECONDARY` button bg, Mac sidebar bg, popover bg, textarea surrounds. |
| `--btn` | `#17160F` | `#ECE8DE` | Primary button / avatar badge / hold-button fill. The "light primary button" in dark (D21). |
| `--on-btn` | `#F3F1EA` | `#17160F` | Text/icon colour on `--btn`. |
| `--ink` | `#17160F` | `#EDEAE2` | Primary text; `.te-root` `color`. |
| `--text2` | `#4A473F` | `#C8C2B5` | Secondary body text (card copy, chat bot lines, `NOTE`). |
| `--muted` | `#5B584F` | `#A8A294` | Tertiary text (`EYEBROW`, sub-labels, meta rows). |
| `--faint` | `#6E6A5F` | `#99938A` | Quietest text: placeholder colour (`input::placeholder`), completed-step "done" lines in the working line, disabled captions. |
| `--line` | `#DCD7CB` | `#36342C` | Default hairline: `CARD` border, `SECONDARY` border. |
| `--line2` | `#ECE8DE` | `#2B2A23` | Row dividers inside lists/cards; active-tab background wash (Mac sidebar, iPhone tab bar). |
| `--axis` | `#C3BDAF` | `#4D4A41` | Chart baseline/axis rule; bar-list left border; off-topic legend swatch outline. |
| `--dash` | `#CFC8B8` | `#4D4A41` | Dashed rules: the card fold line, Capture's dashed border, "still to post" chart swatch outline, underline under a swappable line in a card. |
| `--blue` | `#2340A8` | `#9DB3FF` | **The one "live" blue** (D20): link colour (`a{color:var(--blue)}`), focus-visible ring, current-step colour/label, `CHIP_BLUE` text, selected chip/hook border. |
| `--blue-fill` | `#2340A8` | `#4E6FE6` | Filled-progress blue, distinct from `--blue` so dark mode keeps a mid-tone fill: Wait-timer bar, Notifications toggle "on" track. |
| `--blue-deep` | `#172C78` | `#D2DCFF` | Link **hover** colour (`a:hover{color:var(--blue-deep)}`, `ui/mock/project/Main.dc.html:14`). |
| `--blue-soft` | `#E6EAF7` | `#1F2849` | Light wash: `CHIP_BLUE` background, selected minute-chip/hook background, "Approved" chip background, card-line highlight when its Source sheet is open. |
| `--blue-line` | `#BFC9EA` | `#3B4B8A` | Border of "live" outlined cards: First-hour card, Proposed-post card (`ui/mock/src/build_body.py:62,162`). |
| `--track-blue` | `#E3E8F7` | `#262F52` | Progress-bar track (Verified-followers / Qualified-impressions bars). |
| `--amber` | `#8A4B00` | `#F2B866` | **"Needs you" amber, and only that** (D20): `AMBER` block text, `CHIP_AMBER` text, error/needs-you Thinking states, hold-help "Run it now" link. |
| `--amber-soft` | `#F7E9CC` | `#3A2B12` | Background for `AMBER` blocks, `CHIP_AMBER`, the "waiting for you" banner, error/needs-you alerts. |
| `--amber-line` | `#C99A4B` | `#8E6A2F` | Border of amber-outlined cards: a waiting reply's article, the error state's "Try again" button border. |
| `--amber-fill` | `#8A4B00` | `#F2B866` | Solid amber dot/badge fill: the health-alert dot on the avatar, the Replies "waiting" count badge. |
| `--on-amber` | `#FFFFFF` | `#17160F` | Text/icon on `--amber-fill` (the badge's digit colour). |
| `--hold-fill` | `#2340A8` | `#9DB3FF` | The sweep that fills the hold-to-approve button as it charges. Equals `--blue` in dark (post-25-Sep-review fix). |
| `--ok` | `#2F7A4F` | `#53B882` | "Healthy" status dot: Settings health rows, avatar/tab-bar dot when nothing needs attention. |
| `--seg` | `#E7E3D8` | `#2B2A23` | Track background of a segmented control (Results Growth/Posts/Replies tabs; Appearance Light/Dark/Match). |
| `--seg-sel` | `#7F7A6E` | `#77736A` | Border colour of the **selected** pill inside a segmented control (`segOn()`, `ui/mock/src/main_script.js:438`). |
| `--chip-bg` | `#FBF6FD` | `#261E2C` | Background of the "Ask Cortex about…" pill button (`ASK()`, `ui/mock/src/build_body.py:33-34`). |
| `--chip-line` | `#E2D6EE` | `#463852` | Border of the Ask-Cortex chip and chat suggestion chips. |
| `--chip-glass` | `rgba(255,255,255,.7)` | `rgba(255,255,255,.08)` | Translucent background of chat suggestion chips (sit on the gradient sheet, not the page). |
| `--glass` | `rgba(255,255,255,.82)` | `rgba(38,34,46,.86)` | `.te-glass` translucent + blurred (`backdrop-filter:blur(18px)`) background: the chat text-input row, the sheet surface. |
| `--scrim` | `rgba(23,22,15,.38)` | `rgba(0,0,0,.55)` | Dimming layer behind every sheet / modal / drawer. |
| `--sheet-top` | `#FBF3FF` | `#241B2E` | Top stop of the purple-glow gradient background used only for Cortex chat surfaces (D20). |
| `--sheet-mid` | `#F7F1F6` | `#1C1920` | Mid stop of the same gradient (chat sheet, Mac docked Cortex aside, Mac Ask-Cortex drawer), fading to `--paper`. |
| `--shimmer-hi` | `#7A7466` | `#FFFFFF` | Bright sweep colour in the working-line shimmer text (everywhere **except** the chat sheet). |
| `--shimmer-hi-sheet` | `#6B6558` | `#FFFFFF` | A separately-tuned, **darker** shimmer peak used only inside the chat/Cortex sheet, via `--shimmer-hi: var(--shimmer-hi-sheet)` override on the chat log (`ui/mock/src/build_body.py:674`). Needed because the sheet's lighter gradient background made the ordinary `--shimmer-hi` fall to ~4.1:1 there (review finding #47, `reviews/ui-review-2026-09-25.md:95`); computed contrast of `--shimmer-hi-sheet` against `--sheet-mid`/`--sheet-top` is **5.20–5.34:1** in light (matches the review's "5.1–5.3" claim). |
| `--chart-on` | `#3A5FD0` | `#6A88EE` | "On topic" fill in every chart: Results bars/columns, followers column, on-topic share strip. |
| `--chart-off` | `#15936A` | `#1FAE7B` | "Off topic" colour — used only as a 1.5px **outline** and a small legend swatch fill, never as text. Chart colours checked with a colour-blindness validator (D22). |
| `--on-fill` | `#FFFFFF` | `#FFFFFF` | Defined in both palettes but **never referenced** by `var(--on-fill)` anywhere in `build_body.py`, `build_mac.py` or `main_script.js` — dead token. See §8. |

### Colour rules to carry into the build
- **One blue for anything live** (D20): current step, links, focus ring, "approved"/selected states. Never introduce a second "active" hue.
- **Amber only for "needs you"** (D20): approval pending, health failure, error/needs-you working states, waiting replies. Do not reuse amber for "in progress" or decorative warmth.
- **Purple glow only for Cortex** (D20): the `.te-glow` gradient (`linear-gradient(90deg,#F79AD3,#B59CFF,#7FB8FF,#FFC58A,#F79AD3)`, `ui/mock/project/Main.dc.html:26`) and the `--sheet-top`/`--sheet-mid` gradient wrap only the Ask-Cortex floating pill (iPhone Cortex tab), the chat text input, and the chat sheet/drawer/docked-aside surface. It never appears elsewhere.
- Dark mode is a full re-author (D21), not `filter:invert()` — every token above has an independently chosen dark hex, not a computed inverse.

---

## 2. Typography

**Families** (all loaded from Google Fonts, `<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">`, `ui/mock/project/Main.dc.html:11` / `Mac.dc.html:11`):

| Constant | Stack | Loaded weights | Role |
|---|---|---|---|
| `SERIF` | `'Instrument Serif', Georgia, serif` (`ui/mock/src/build_body.py:3`) | 400 only | Headlines: page H1s, the Mac 44px headline, "The cards ·" / "Posting" Mac sub-headers, Results' two-line lead, Cortex H1. **Always** paired with explicit `font-weight: 400` since no bold is loaded. |
| `SANS` | `'IBM Plex Sans', system-ui, sans-serif` (`ui/mock/src/build_body.py:4`) | 400, 500, 600 | Default body (`body{font-family:...}`, `ui/mock/project/Main.dc.html:13`), all H2s, buttons, card/chat copy, inputs/textareas. |
| `MONO` | `'IBM Plex Mono', monospace` (`ui/mock/src/build_body.py:2`) | 400, 500 | Eyebrows, avatar initials ("EZ"), timestamps, character counts, KPI values, step counters, `⌘K` hint. |

`Thinking.dc.html` loads only Mono + Sans (no headline in that canvas). `WorkingStates.dc.html` loads all three.

**Sizes.** Minimum in the app screens is **12px**. Two exceptions remain below that floor (see §8): the working-line step counter at **11px** (`ui/mock/project/Thinking.dc.html:73`, live inside the real app via `<dc-import name="Thinking">`) and the gallery-only command labels at **11.5px** (`ui/mock/project/WorkingStates.dc.html:27`, a dev canvas, not a real screen). All sizes are fixed `px`; there is no `rem`/`clamp` scaling, so iOS Dynamic Type has no effect (deferred to the build, `reviews/ui-direction.md:65`).

Named style constants (`ui/mock/src/build_body.py:5-17`), reused everywhere:

| Constant | Size | Weight | Line-height | Colour | Role |
|---|---|---|---|---|---|
| `EYEBROW` | 12px | 400, `letter-spacing:0.08em`, uppercase | — | `--muted` | Section/screen eyebrow ("Next post", "Results · week of…"). Mono. |
| `H1` | 36px | 400 | 1.05 | `--ink` | iPhone page headline (Today, Capture). Overridden to **34px** on Post/Ready headers (`build_body.py:186,258`), **40px** on Cortex (`build_body.py:549`). Mac overrides its own headline to **44px/1.08** (D32, `build_mac.py:29`) and uses a **30px/1 (no explicit line-height set)** serif H2 for "The cards ·" / "Posting" (`build_mac.py:40,45`). |
| `H2` | 15px | 600 | — | `--ink` (or overridden per-context) | Base section/card heading. Commonly bumped to **16px** (Approve heading) or **17px** (First hour, Waiting/Builders headers, sheet titles). |
| `PRIMARY` (button text) | 16px | 600 | — | `--on-btn` | Primary button label. |
| `SECONDARY` (button text) | 15px | 600 | — | `--ink` | Secondary button label. |
| `LINKBTN` | 14px | 500 | — | `--blue` | Text-only link button ("‹ Today", "Change something", "Undo"). |
| `AMBER` block | 14px | 400 | 1.45 | `--amber` | Alert/callout body text. |
| `NOTE` | 13.5px | 400 | 1.45 | `--text2` | Neutral callout body text. |
| `SUB` | 12.5px | 400 | 1.4 | `--muted` | Captions under a control or row. |
| `CHIP_AMBER` / `CHIP_BLUE` / `CHIP_NEUTRAL` | 12px | 600 | — | `--amber` / `--blue` / `--text2` | Small status pills ("Needs your approval", "Approved at…", "example"). |

Other recurring sizes (inline overrides layered on the families above, not named constants):

| Size | Representative role | Citation |
|---|---|---|
| 13px | Card meta ("@exitzerocode · time"), table cells, chart legend labels, date-range chips | `build_body.py:197,441,472` |
| 13.5px | Mac health line (D32), suggestion chips, Settings row name variants, "answer now" text | `build_mac.py:30`; `build_body.py:687` |
| 14px | Reply preview/short text, hook take input, capture textarea placeholder text | `build_body.py:142,357,663` |
| 14.5px | Card/chat body copy, Settings row name, Weights value | `build_body.py:199,578,716` |
| 15px | SECONDARY label size reused for hook text, chat bubbles, X card meta name, waiting-card "said" text | `build_body.py:196,218,677-678` |
| 16px | PRIMARY label size reused for Approve section heading, save buttons | `build_body.py:225` |
| 17px | Sheet/section sub-headings (First hour, Waiting, Builders, Worth joining, Change-something, Hook, Settings) | `build_body.py:63,405,411,423,655,738` |
| 18px | Next-post card title ("PAID → FREE: developer tools") | `build_body.py:81` |
| 20px | Cortex pipeline count | `build_body.py:554` |
| 22px | Results headline (phone), Mac override bumps this to **27px** (`build_mac.py:75`) | `build_body.py:462` |
| 24px | Results KPI tile value | `build_body.py:483` |
| 26px | Builders "mutuals on topic" big number | `build_body.py:412` |
| 28px | Wait-timer clock (mm:ss) | `build_body.py:276` |
| 30px | Lesson example big numbers; Mac "The cards ·"/"Posting" sub-header | `build_body.py:565-566`; `build_mac.py:40,45` |
| 34px | Post/Ready screen H1 override | `build_body.py:186,258` |
| 36px | Default `H1` | `build_body.py:7` |
| 40px | Cortex H1 override | `build_body.py:549` |
| 44px | Mac headline (D32) | `build_mac.py:29` |

Weights used throughout: **400** (body default, serif always), **500** (mono numbers/labels, LINKBTN), **600** (headings, button labels, chip text, bold emphasis). No 700 anywhere (Plex Sans/Mono bold isn't even loaded).

---

## 3. Spacing, radii, borders, shadows, sizes

**Canvas sizes.** iPhone: **390 × 844** (`ui/mock/src/build_body.py:758`). Mac: **1440 × 900** (`ui/mock/src/build_mac.py:150`). Both fixed — no responsive breakpoints; a smaller window is explicitly deferred to the build (`reviews/ui-direction.md:65`).

**Spacing scale** (from `gap`/`padding` usage across `build_body.py`/`build_mac.py`): predominantly even numbers — **2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 32, 36, 40, 44px**. Most common: 8, 10, 12px (inter-element gaps within a card), 16–18px (card internal padding), 20–22px (section-to-section gaps). Not a strict 8pt grid — 3px, 6px, 14px, 18px, 22px all recur — but everything is a multiple of 2px.

**Radii in use:** 2, 3, 4, 6, 9, 10, 11, 12, 14, 15, 16, 18, 20, 22, 24px, plus **999px** (full pill — chips, segmented-control pills, date-range/hook/minute chips, the glow pill). Compound radii: sheet top corners only `26px 26px 0 0` (bottom sheet, `sheet()`, `ui/mock/src/build_body.py:631`), chat bubble `18px 18px 4px 18px` (user bubble, flat corner toward the sender edge, `build_body.py:677`), chart column top `4px 4px 0 0`. Card (`CARD`) radius is **18px** (`build_body.py:5`); buttons are **10–12px**; the standard sheet/modal/popover shell is **20–26px**; the avatar/badge/knob circles use **50%**.

**Borders:** default hairline `1px solid var(--line)` (cards, `SECONDARY`); dividers `1px solid var(--line2)` (list rows); dashed `1px dashed var(--dash)` (fold line, source-sheet rules) or `1.5px dashed var(--dash)` (Capture card, "still to post" chart swatch); coloured 1–1.5px borders for state (`--blue-line`, `--amber-line`, `--blue`, `--seg-sel`).

**Shadows** (only 7 in the whole system):
| Shadow | Used for | Citation |
|---|---|---|
| `0 0 0 2px var(--paper)` / `var(--raised)` | Ring around the amber health dot on an avatar, separating it from the badge behind it | `build_body.py:22`; `build_mac.py:115` |
| `0 1px 3px rgba(0,0,0,.25)` | Settings switch knob | `build_body.py:718` |
| `0 24px 60px rgba(23,22,15,.25)` | Mac centred dialog (modal) | `build_mac.py:126` |
| `0 18px 50px rgba(23,22,15,.18)` | Mac popover (Settings/health) | `build_mac.py:143` |
| `-12px 0 40px rgba(120,60,160,.16)` | Mac drawer (Ask Cortex from another page) — purple-tinted, matching the Cortex glow | `build_mac.py:135` |
| `0 -10px 40px rgba(120,60,160,.18)` | iPhone chat bottom sheet — same purple tint | `build_body.py:692` |
| `0 0 22px rgba(190,120,255,.45), 0 0 44px rgba(255,150,200,.22)` | `.te-glow` outer glow (Cortex only) | `ui/mock/project/Main.dc.html:26` |

**Fixed layout widths/heights:**
| Element | Size | Citation |
|---|---|---|
| iPhone canvas | 390 × 844 | `build_body.py:758` |
| Mac canvas | 1440 × 900 | `build_mac.py:150` |
| Mac sidebar | 248px wide | `build_mac.py:98` |
| Mac two-column Today | 440px (left, Today content) + `minmax(0,1fr)` (right, cards/posting), 40px gap | `build_mac.py:50` |
| Mac single-column pages (Posts, Capture, Replies, Results) | `max-width: 820px` default via `narrow()`; Replies 880px; Results 960px | `build_mac.py:64,69-72` |
| Mac Cortex page | `minmax(0,1fr) 400px` grid, docked chat 400px wide, 820px tall sticky aside | `build_mac.py:80-82` |
| Mac drawer (Ask Cortex, off-Cortex pages) | 440px wide, full height | `build_mac.py:135` |
| Mac centred dialog (Source / Change something / Choose a hook) | 540 / 640 / 560px, `max-height:820px` | `build_mac.py:161-163` |
| Mac popover (Settings/health) | 400px wide, `max-height:780px`, anchored `left:16px; bottom:80px` | `build_mac.py:143` |
| iPhone bottom nav | height 80px | `build_body.py:620` |
| iPhone bottom sheet | `max-height:90%` default, chat sheet `height:88%` | `build_body.py:627-635,692` |
| Avatar sizes | 44px (header), 40px (X card preview), 52px (Settings sheet header), 36px (Mac sidebar profile) | `build_body.py:19,196,705`; `build_mac.py:115` |
| Settings switch | 48 × 30px track, 26px knob | `build_body.py:718` |
| Replies badge | `min-width:18px, height:18px` (phone tab) / `min-width:22px, height:22px` (Mac sidebar) | `build_body.py:618`; `build_mac.py:94` |

**Touch targets — 44px minimum (D2/D13, Apple HIG).** All interactive constants (`PRIMARY` 52px, `SECONDARY` 48px, `LINKBTN` 44px, minute/capture/hook chips, tab/nav buttons, the hold-to-approve button 54px) declare `min-height: 44px` or larger. Two exceptions fall under 44px but above WCAG 2.2's 24px minimum, confirmed already reviewed and accepted (`reviews/ui-review-2026-09-24.md:98`, "All pass WCAG's 24px minimum"): the Settings switch (48 × **30px**) and small decorative badges/legend swatches (12–28px, non-interactive).

---

## 4. Component catalogue

### Buttons
- **Primary** (`PRIMARY`, `build_body.py:9`): `min-height:52px; border-radius:12px; border:none; background:var(--btn); color:var(--on-btn); font-size:16px; font-weight:600`. Disabled: `opacity` driven by a `*Opacity` prop (e.g. `0.45` when `busy`) plus native `disabled`. No separate hover/active style beyond the browser default; focus uses the global `:focus-visible` ring. Used for: Read and approve / Start posting / Copy / I've posted it / Save / Accept.
- **Secondary** (`SECONDARY`, `build_body.py:10`): `min-height:48px; padding:0 16px; border-radius:12px; border:1px solid var(--line); background:var(--raised); font-size:15px; font-weight:600`. Same disabled/opacity pattern. Used for: Change something / Edit a card / Copy again / Draft / Cancel proposal.
- **Link button** (`LINKBTN`, `build_body.py:11`): `min-height:44px; border:none; background:none; color:var(--blue); font-size:14px; font-weight:500; text-align:left`. Used for back links, Undo, Cancel, Withdraw approval, Start posting early anyway.
- **Outline "ghost" button** (inline, not a named constant): `min-height:50px; border:1px solid var(--ink); background:transparent; font-size:15px; font-weight:600` — Plan the next post, Write this week's review (`build_body.py:156,538`).

All buttons: `button:focus-visible{outline:2px solid var(--blue); outline-offset:2px}` (`ui/mock/project/Main.dc.html:19`). `button{font:inherit;color:inherit}` resets are global (`Main.dc.html:15`).

### Chips
- **Status chips** (`CHIP_AMBER`/`CHIP_BLUE`/`CHIP_NEUTRAL`, `build_body.py:15-17`): `font-size:12px; font-weight:600; padding:4px 10px; border-radius:999px`, non-interactive (no role, decorative status labels — "Needs your approval", "Approved at…", "example", "Drafted · next in line").
- **Radio chips** (minute-taken, capture kind, appearance, hooks): `role="radio"` inside `role="radiogroup"`, `aria-checked`, `min-height:44px+`, selected state = coloured border + tinted background (e.g. minute chip: `border:var(--blue)` / `background:var(--blue-soft)` when on, `var(--line)` / `var(--raised)` off — `main_script.js:512-513`). Capture kind chips: 48px min-height, 2-col grid (`build_body.py:354`).
- **Ask-Cortex chip** (`ASK()`, `build_body.py:33-34`): pill with the small orb icon + label, `border:1px solid var(--chip-line); background:var(--chip-bg)`, `min-height:44px`. Appears under: a post, a proposal, a waiting reply, Results.

### Cards
`CARD` (`build_body.py:5`): `background:var(--card); border:1px solid var(--line); border-radius:18px`. Universal container for sections, list rows, KPI tiles (radius reduced to 14px), the X-card preview, chat/lesson panels. Variant borders swap `--line` for `--blue-line` (live/proposed) or `--amber-line` (needs-you).

### Amber alert / Note
- `AMBER` (`build_body.py:12`): `color:var(--amber); background:var(--amber-soft); border-radius:14px; padding:12px 14px`. Used with `role="alert"` when it announces a new problem (health failure, gate refusal, copy failure) and plain `<div>` when it's a persistent caveat (e.g. "You changed a card after approving it").
- `NOTE` (`build_body.py:13`): `color:var(--text2); background:var(--line2); border-radius:14px; padding:12px 14px`. Neutral, non-urgent callouts; `role="status"` when it confirms a just-completed save.

### Stepper (5-step "Plan → Draft → Approve → Post → Measure")
`ui/mock/src/build_body.py:85-92` + `main_script.js:334-340`. An `<ol>` of 5 `<li aria-current="step"|"false">`, each a 4px coloured bar over a label. Colours: done = `--ink` bar / `--ink` text, current = `--blue` bar/text + `font-weight:600`, upcoming = `--line` bar / `--muted` text. Done items get a `✓ ` prefix in the visible label **and** a screen-reader-only suffix (`<span class="te-sr">, done</span>` etc, `.te-sr` = visually-hidden clip, `Main.dc.html:18`) so state isn't colour-only (fixes 24-Sep finding B5).

### Countdown
Inline mono text (`countdown`), colour `--blue` normally, `--amber` when late/missed (`main_script.js:319-329`). Computed live every second (`this.tick = setInterval(...,1000)`, `main_script.js:248`), states: "in H h M m" / "N min late, still inside the HH:MM–HH:MM slot" / "missed the slot".

### Hold-to-approve button
`build_body.py:228-233`. A relatively-positioned button containing an absolutely-positioned fill `<span>` whose `width` is the hold percentage (`var(--hold-fill)` background) under a label `<span>`. Handlers: `onPointerDown/Up/Leave/Cancel`, `onLostPointerCapture`, `onBlur` all call `holdEnd` (cancels on any interruption — fixes 25-Sep blocker/finding #2); `onKeyDown`/`onKeyUp` bind Space/Enter to the same start/end (`main_script.js:539-540`); `aria-describedby="te-hold-help"` points at a caption explaining the hold. Hold fills at 4%/40ms tick → ~1s to complete (`main_script.js:384-388`); reaching 100% approves and moves focus to the next primary action (`focusButton(...)`, `main_script.js:380`). Also ends the hold on `visibilitychange` (tab hidden, `main_script.js:249`). **No Face ID/Touch ID step** (D13/D24 — deliberate).

### X card preview (with fold line)
`build_body.py:194-212`. `<article aria-label="Card 1, as it will look on X">` with a fake X header (avatar circle "EZ", name, `@exitzerocode · time`), then the card body as a stack of lines. Each line can be: blank spacer, plain text, or a "swap" line (an underlined `<button>` that opens the Source sheet for that claim — `text-decoration-color:var(--dash)`). The fold is **computed from the real card text** using X's own weighted character count (`xLength()`, `main_script.js:181-191`, mirrors `scripts/post_thread.py`'s counting: code points ≤0x10FF and most punctuation count 1, everything else counts 2, a link counts 23) — the dashed "Strangers stop here unless they tap Show more" divider is inserted at the line where the running count crosses 280, and every line after it renders at `opacity:0.6`. Footer shows the live character count against the 600 cap, colour flips to `--amber` over the limit.

### Source sheet
`SOURCE_INNER`, `build_body.py:639-650`. Bottom sheet (iPhone) / centred dialog (Mac, 540px). Mono-set fact card: `SOURCE · SWAP N OF 3` / `CHECKED 24 SEP` eyebrow, paid→free header, dashed rules separating **Paid side** (fact + source), **Free side — the vendor's own words** (a direct quote + source), **If someone pushes back** (the limitation). Every fact traces to a session-checked source (truth budget, `voice/exit-zero.md`).

### Bottom sheet (iPhone) vs Mac centred dialog vs drawer vs popover
Four distinct chrome patterns share one state model but render differently per device — all in `build_mac.py`:
- **iPhone sheet** (`sheet()`, `build_body.py:627-635`): slides up from the bottom, `border-radius:26px 26px 0 0`, drag handle (`HANDLE`, a 40×4px bar), `max-height:90%` (chat: `height:88%`). Used for Source, Change something, Ask Cortex, Settings, Choose a hook.
- **Mac centred dialog** (`modal()`, `build_mac.py:122-130`): fixed width (540/640/560px per §3), centred via flex, `border-radius:22px`, no handle (stripped via `.replace(bb.HANDLE,'')`), `box-shadow:0 24px 60px rgba(23,22,15,.25)`. Used for Source, Change something, Choose a hook.
- **Mac drawer** (`DRAWER`, `build_mac.py:132-139`): slides from the right, 440px, full height, purple gradient background, used only for Ask Cortex opened from a page **other than** Cortex itself.
- **Mac popover** (`POPOVER`, `build_mac.py:141-146`): anchored near the sidebar profile button (`left:16px; bottom:80px`), 400px, `border-radius:20px`, used only for Settings/health.
- On the **Mac Cortex page itself**, the chat is not a sheet/drawer at all — it's permanently **docked** as a sticky 400px-wide `<aside>` beside the page content (`CORTEX`, `build_mac.py:79-86`).

All four modal variants share: `role="dialog" aria-modal="true" aria-label="…"`, `onKeyDown={{sheetKey}}` (Escape closes), a scrim (`onClick` closes, `aria-hidden="true"`), entrance animation `.te-sheet-in` (`te-up`, §5), focus moved in on open and returned to the trigger on close (`openSheet()`/`restoreFocus()`, `main_script.js:260-271`), and the page behind is `inert` while any sheet/drawer/popover/editor is open (`inertOn`, `main_script.js:468`, rendered on both `<main>` and `<nav>`) — this was a 25-Sep fix: `inert` must be a **string** ("true"/omitted), not a boolean, because React drops a boolean `inert` attribute (finding #24, `reviews/ui-review-2026-09-25.md:67`).

### Tab bar (iPhone bottom nav)
`NAV`/`tab()`, `build_body.py:613-625`. `<nav aria-label="Sections">` with 5 `<button aria-current="page"|"false"> aria-label>`, icon + 12px label, colour `--ink` when active / `--faint` inactive (`tabOn()`, `main_script.js:444`), label weight 600/500. The Replies tab gets a badge (see below) and its `aria-label` becomes "Replies, N waiting" (colour **and** text carry the state, not colour alone). Height 80px, `border-top:1px solid var(--line)`.

### Sidebar nav with active bar and badge (Mac)
`SIDEBAR`/`nav()`, `build_mac.py:88-120`. Vertical list of 44px-min-height buttons; active state = `background:var(--line2)` wash **plus** a 3px left accent bar (`position:absolute; left:0; ...; background:var(--nav{K}Bar)`, `--ink` when active / `transparent` inactive) **plus** `aria-current="page"`, `font-weight:600` — four redundant active signals, none colour-only. Cortex row also shows a static `⌘K` hint (`KBD`, `build_mac.py:96`, Mac-only). `<nav aria-label="Sections" inert="{{navInert}}">` — the sidebar itself goes inert while a sheet is open, same as `<main>`.

### Badge (waiting-reply count)
`BADGE`, `build_body.py:618` (phone, on the tab icon, `top:-5px;right:-10px`) and `build_mac.py:94` (sidebar, inline `margin-left:auto`). `background:var(--amber-fill); color:var(--on-amber)`, mono digits, `aria-hidden="true"` (the count is carried in the tab's own `aria-label`, not duplicated for assistive tech).

### Segmented tabs (Results Growth/Posts/Replies)
`build_body.py:465-469` + `rtKey()`/`seg()` in `main_script.js:625-632,439`. `role="tablist"`/`role="tab" aria-selected aria-controls="te-rt-panel" tabindex` + one shared `role="tabpanel" id="te-rt-panel"`. **Roving tabindex**: only the selected tab is `tabindex="0"`, others `"-1"`; arrow-left/right/Home/End move selection and move focus to the newly active tab (`this.shown('[role=tab]')[j].focus()`). Visual: pill inside a `--seg` track, selected pill = `background:var(--card); border:1px solid var(--seg-sel)`.

### Radio chips (Appearance Light/Dark/Match)
`seg_radio()`, `build_body.py:699-700`. Same visual pattern as segmented tabs but `role="radio"` in a `role="radiogroup"`, not `role="tab"` (it's a preference choice, not a view switch) — no arrow-key roving is implemented for this group (browser default radio behaviour isn't wired since these are `<button role="radio">`, not native radios; flag in §8).

### Switch (Notifications toggles)
`build_body.py:718`. `<button role="switch" aria-checked aria-label>`, 48×30px track (`background:var(--blue-fill)` on / `var(--line)` off), 26px white knob sliding `left:2px→20px`, `box-shadow:0 1px 3px rgba(0,0,0,.25)`.

### KPI tile
`build_body.py:483` (phone, 2-col grid) / `build_mac.py:73-74` (Mac, forced 4-col grid, value bumped 24px→27px). `CARD` at 14px radius, `label` (12px muted) / `value` (24-27px/600) / `sub` (12px muted).

### Bar list + table view
`barlist()`/`table()`, `build_body.py:438-456`. Every chart has a matching `<table>`: `showChart`/`showTable` are mutually exclusive booleans toggled by one "Show as table" button per Results tab (D22, fixed 25-Sep finding #21 — previously not every chart had one). Bars: CSS width percentage + a left border acting as the y-axis (`border-left:1px solid var(--axis)`), fill `background:var(--chart-on)`. Table: `<caption>`-less `<table>` with `scope="col"` headers, `font-variant-numeric:tabular-nums` on data cells.

### On-topic strip
`build_body.py:507-510`. `role="img"` 15-cell grid (`aria-label` gives the full sentence, e.g. "On topic: 5 of your last 11 posts, 4 still to post. Target 12 of 15." — `main_script.js:642`), each cell **filled** (on-topic), **outlined** (off-topic, `--axis` solid border), or **dashed-outlined** (still to post) — colour plus shape, never colour alone. A text legend with swatches sits below. A `showTable` variant exists too (`table([('Post','left'),('On topic','left')], …)`).

### Weights / Guardrails lists
`build_body.py:573-588`. Weights: a `CARD` list, each row = name (12.5px muted) + right-aligned source (mono, `font-style:italic` when it's a guess — `w.guess` flag, `main_script.js:650`) over the value (14.5px/500). Guardrails: a fixed list, each row prefixed with a closed-`LOCK` icon (`build_body.py:37`) — visually distinct from Weights (never editable, D11).

### Chat log + suggestion chips + glass input with glow
`CHAT_INNER`, `build_body.py:669-691`. Log: `<div role="log" aria-live="polite" aria-label="Conversation">`, user bubbles right-aligned (`--btn` fill, `border-radius:18px 18px 4px 18px`), bot replies left-aligned with a small orb icon, no bubble chrome. A `Thinking` import (`cmd="ask"`) appears while answering. Suggestion chips: pill buttons, `disabled` while `asking`, wrap (fixed 25-Sep finding #42, previously cut off with no overflow affordance). Input row: `.te-glow` wrapper (the purple gradient, animated 2 loops then static) around a `.te-glass` pill containing the orb icon, a 44px-tall `<input aria-label="Ask Cortex">`, and a round 44px send button. `.te-glow:focus-within{outline:2px solid var(--blue)}` — the focus ring was previously suppressed by an inline `outline:none` on the input (25-Sep finding #45); fixed to use the wrapper's focus-within ring instead.

### Working line (Thinking component) and its states
`ui/mock/project/Thinking.dc.html`. A live region (`role="status" aria-live="polite"` while running) showing a moving icon + shimmering text naming the real step, a "Step N of M" mono counter, and a list of completed steps (plain checkmark rows, `--faint`). Three end states, controlled by the `show` prop:
- **live** (default): loops or runs once through `STEPS[cmd]` (per-command step lists: `next`, `draft`, `ready`, `find`, `posted`, `record`, `ask`, `results` — `Thinking.dc.html:91-135`), one step per 1.5s tick.
- **error** (`role="alert"`): "**Stopped at: {step}.** {reason}" + Try again / Cancel buttons.
- **needs** (`role="alert"`): "**Needs you.** {question}" + two named-answer buttons (e.g. "Use 24 Sep's" / "Leave them out").
Icon set (7 kinds, each its own inline SVG + CSS animation class — see §5): sync, read, search, write, count, clock, check (+ copy, defined but not in the default STEPS lists — used by canvas tweaks). Used throughout the app via `<dc-import name="Thinking" cmd="…" on-done="…">`.

### Toggle (theme sun/moon)
`THEME_TOGGLE`, `build_body.py:694-697`. One 44px round icon button, `aria-label`/`title` state the **target** state ("Switch to dark mode"), a swap-in animation (`.te-swap`) plays when the icon changes. Two states only (D23) — Light/Dark/Match stays in Settings as a separate 3-way `seg_radio` group.

---

## 5. Motion

All keyframes are in `ui/mock/project/Main.dc.html`/`Mac.dc.html` (helmet, identical) and `ui/mock/project/Thinking.dc.html`/`WorkingStates.dc.html`.

| Class / keyframe | Duration / easing | Effect | Used by | Reduced motion |
|---|---|---|---|---|
| `.te-swap` / `@keyframes te-swap` | 0.35s `cubic-bezier(.2,.8,.2,1)` | Rotate-in from -90°/scale .6/opacity 0 → identity | Theme toggle icon swap | `animation:none` |
| `.te-glow` / `@keyframes te-glow` | 6s linear, **2 iterations** (not infinite) | Gradient background position sweep 0%→300% | The purple Cortex glow (pill wrapper, chat input wrapper) | Not explicitly listed in the `@media (prefers-reduced-motion: reduce)` rule at `Main.dc.html:31` — **it is** listed (`.te-glow,.te-sheet-in{animation:none}`) |
| `.te-sheet-in` / `@keyframes te-up` | 0.28s `cubic-bezier(.2,.8,.2,1)` | translateY(40px)→0, opacity 0→1 | Every sheet/dialog/drawer/popover entrance | `animation:none` |
| `.te-shimmer` / `@keyframes te-sh` | 2.2s linear infinite | Background-position sweep on a text-clip gradient (`text2 → shimmer-hi → text2`), background-size 250% | The working-line's current-step text | `animation:none; background:none; color:var(--text2)` (falls back to flat colour) |
| `.te-spin` / `@keyframes te-spin` | 1.4s linear infinite | `rotate(360deg)` | "sync" icon (refresh arrows) | `animation:none` |
| `.te-bob` / `@keyframes te-bob` | 1.2s ease-in-out infinite | translateY 0→-2px→0 | "read" icon (open book), "copy" icon | `animation:none` |
| `.te-sweep` / `@keyframes te-sweep` | 1.6s ease-in-out infinite | translate(-2px,0)→(2px,1px), `transform-box:fill-box` | "search" icon (magnifying glass moves within its own box) | `animation:none` |
| `.te-write` / `@keyframes te-write` | 0.9s ease-in-out infinite | rotate(-6deg)↔rotate(5deg) + slight translateX, `transform-origin:20% 80%` | "write" icon (pencil) | `animation:none` |
| `.te-bar1/2/3` / `@keyframes te-bar` | 1.1s ease-in-out infinite, staggered `animation-delay` .18s/.36s | `scaleY(.45)↔scaleY(1)`, `transform-origin:50% 100%` | "count" icon (3 bars) | `animation:none` |
| `.te-pulse` / `@keyframes te-pulse` | 1.3s ease-in-out infinite | `opacity .4↔1` | "check" icon (shield-check) | `animation:none` |
| `.te-hand` / `@keyframes te-spin` (reused) | 2.4s linear infinite | Clock hand rotates, `transform-origin:12px 12px` | "clock" icon | `animation:none` |
| `.te-holddemo` / `@keyframes te-hold` | 3.2s ease-in-out infinite | width 0%→(hold 12%→62%)→100%, holds at 100% | `WorkingStates.dc.html` gallery-only demo of the hold-to-approve fill (not the real interactive control) | `animation:none; width:60%` (freezes mid-fill so the concept still reads) |

**Reduced-motion coverage** is applied per-file: `Main.dc.html:22,31` (`.te-swap`; `.te-glow,.te-sheet-in`), `Thinking.dc.html:32` (all 9 Thinking animations, with the shimmer additionally falling back to a flat `--text2` colour so the text stays legible without motion), `WorkingStates.dc.html:16` (the hold demo). The 24-Sep and 25-Sep reviews both confirm reduced motion is "covered everywhere" (`reviews/ui-review-2026-09-24.md:99`; `reviews/ui-review-2026-09-25.md:140`).

Note: the **real** hold-to-approve button (`build_body.py:228-233`) has **no CSS animation at all** — its fill width is driven by JS state (`holdWidth: s.hold + '%'`) updated every 40ms while held, so it isn't a `prefers-reduced-motion` concern in the same way; it stops immediately on release/cancel regardless of the setting.

---

## 6. Accessibility (WCAG 2.2 AA target)

**Contrast.** Figures below are computed from the token hexes in §1 (relative-luminance formula, sRGB), against the background each text/graphic actually sits on:

| Pair | Light | Dark | Note |
|---|---|---|---|
| `--ink` / `--paper` (body text) | 16.0:1 | 15.3:1 | |
| `--text2` / `--paper` | 8.2:1 | 10.4:1 | |
| `--muted` / `--paper` | 6.3:1 | 7.3:1 | |
| `--faint` / `--paper` | 4.8:1 | 6.1:1 | Passes AA (4.5:1) by a narrow margin in light. |
| `--blue` / `--card` (links, focus text) | 8.9:1 | — | |
| `--amber` / `--amber-soft` (alert text) | 5.7:1 | 7.7:1 | |
| `--on-amber` / `--amber-fill` (badge digits) | 6.8:1 | 10.2:1 | |
| `--on-btn` / `--btn` (button labels) | 16.0:1 | 14.8:1 | |
| `--shimmer-hi` / `--card` (working-line peak, general) | 4.6:1 | 18.4:1 | Peak of an animated sweep, not the resting colour (resting is `--text2`, 8.2:1/10.4:1) — see §8. |
| `--shimmer-hi-sheet` / `--sheet-mid` (working-line peak, chat sheet) | 5.2–5.3:1 | 17.4:1 | Matches the 25-Sep review's "5.1–5.3" fix note (`reviews/ui-review-2026-09-25.md:95`). |
| `--seg-sel` / `--card` (selected-segment border, non-text) | 4.3:1 | 3.5:1 | Non-text UI component threshold is 3:1 (WCAG 1.4.11) — passes both; the 24-Sep review's earlier "1.28/1.15" failure (`reviews/ui-review-2026-09-24.md:81`) read the border against the wrong (track, not card) background — computed against `--seg` the ratio is lower (3.33:1 light / 3.05:1 dark) but still ≥3:1. |
| `--chart-off` / `--paper` (off-topic outline/legend, non-text) | 3.4:1 | 6.5:1 | Used only as a 1.5px outline/small swatch, never as text — passes the 3:1 graphics threshold. |
| `--ok` / `--paper` (health dot, non-text) | 4.6:1 | 7.5:1 | |

**Colour + shape, never colour alone:** the stepper (bar height/weight/✓-prefix/`.te-sr` state text, not just colour — `build_body.py:89`), the on-topic chart strip (fill vs. solid outline vs. dashed outline), the active tab/nav (weight + `aria-current` + background wash + accent bar, not just colour), the selected segment (border + weight + background, not just colour), reply outcomes ("Answered" vs "Not answering" render as different text, each with its own Undo — 25-Sep fix #38).

**Focus-visible rule:** global, one rule for every interactive element — `button:focus-visible, a:focus-visible, input:focus-visible, textarea:focus-visible{outline:2px solid var(--blue); outline-offset:2px}` (`ui/mock/project/Main.dc.html:19`); the `.te-glow` wrapper additionally gets `outline:2px solid var(--blue); outline-offset:3px` on `:focus-within` (`Main.dc.html:17`) so the Ask-Cortex input's ring isn't swallowed by the glow chrome.

**Icon-only buttons are labelled:** avatar/settings button (`aria-label="{{avatarLabel}}"`, which itself changes to append ", something needs you" when health is bad — `main_script.js:487`), theme toggle (`aria-label`/`title` state the target mode), chat context-clear "×" (`aria-label="Stop asking about this"`), send button (`aria-label="Send"`). Decorative icons (step/status glyphs, chart swatches, the orb) are `aria-hidden="true"`.

**Live regions:** working line = `role="status" aria-live="polite"` while running, `role="alert"` on error/needs-you (`Thinking.dc.html:44,77,83`); health-check-missed banner = `role="alert"` (`build_body.py:58`); chat log = `role="log" aria-live="polite" aria-label="Conversation"` (`build_body.py:674`); save/copy confirmations = `role="status"`.

**Sheets/dialogs:** `role="dialog" aria-modal="true" aria-label="…"`; focus moves into the sheet on open (first focusable, or a caller-specified selector) and back to the trigger on close (`openSheet()`/`restoreFocus()`, `main_script.js:260-271`); Escape closes via `onKeyDown={{sheetKey}}` on the dialog itself, which also `stopPropagation`s so it doesn't also trigger the global Escape handler (`main_script.js:571`); the page behind (`<main>` and, on Mac, `<nav>`) is `inert` while any sheet/drawer/popover/editor is open, rendered as the **string** `"true"` (React drops a boolean `inert` — 25-Sep fix #24). Opening the editor closes the Source sheet if it was open (same fix).

**Tabs (Results):** `role="tablist"`/`role="tab" aria-selected aria-controls`/one shared `role="tabpanel"`; roving `tabindex` (selected = `0`, others = `-1`); arrow-left/right wrap, Home/End jump to first/last, and moving selection also moves DOM focus to the newly active tab (`rtKey()`, `main_script.js:626-632`) — a 25-Sep fix (previously "no tab panels or arrow keys", finding #45).

**Hold-to-approve keyboard (D13/D24):** Space or Enter starts the hold on `keydown` (guarded by `!e.repeat` so key-repeat doesn't restart it), and either key's `keyup` ends it — same 40ms/4%-per-tick fill as pointer (`main_script.js:539-540`). **Screen-reader gap, by design:** VoiceOver and Switch Control send a single synthetic tap, not a sustained press, so they cannot trigger a hold at all. This is a known, accepted gap (E1 in `reviews/ui-review-2026-09-25.md:101`, reaffirmed by the operator over adding Face ID/Touch ID): the **typed `/approve` command stays the accessible route** for assistive-technology users (`reviews/ui-direction.md:66`, "Screen readers and the hold (D13/D24)"). The build must preserve a non-hold, non-pointer path to the same approval action.

**Fixed px sizes / Dynamic Type:** every font-size in the mock is a literal `px` value (§2); there is no fluid or `rem`-based scale, so iOS Dynamic Type has zero effect on this mock. Explicitly deferred to the build (`reviews/ui-direction.md:65`; also called out per-screen in `reviews/ui-review-2026-09-25.md:166`, "Deferred to the build").

**Reduced motion:** see §5 — covered per the 24-Sep and 25-Sep reviews' explicit sign-off ("covered everywhere").

**Touch targets:** see §3 — 44px+ on essentially every interactive control; two known sub-44px exceptions (Settings switch 30px tall, small decorative badges) both still clear WCAG's 24px CSS-pixel minimum.

---

## 7. iPhone vs Mac layout differences, screen by screen

| Screen | iPhone | Mac |
|---|---|---|
| **Global chrome** | Bottom tab bar (5 tabs, 80px), avatar/settings button top-right of each screen's own header, theme toggle lives inside the Settings sheet's header row | Left sidebar (248px): logo, nav list with active bar + Cortex `⌘K` hint, a health/follower mini-card, then a combined profile button + standalone theme toggle at the very bottom (`SIDEBAR`, `build_mac.py:98-120`). No avatar button is repeated per-screen (stripped via `no_avatar()`). |
| **Today** | Single column: header → (optional health alert) → (optional First hour card) → Next-post card with Preview button → Progress → Replies preview → Capture teaser → Plan-next flow | Two-column grid under one shared full-width header: **left 440px** = the same Today content minus the health alert (hoisted into the header) and minus the "Preview" button (redundant, cards are already visible); **right, fluid** = the live card preview / posting-steps panel, shown inline instead of navigated to. Headline is 44px/one line (D32, `ellipsis`+`nowrap` guards overflow) instead of the phone's 36px wrapping H1. |
| **Post (the cards)** | A separate screen (`isPost`), reached by tapping Preview or "Read and approve"; back link "‹ Today" | Not a separate screen at all — it's the right column of Today (`isHomeCards`). Its own H1 is replaced with a Mac-styled `<h2 data-te-cards tabindex="-1">The cards · …</h2>` (`build_mac.py:40`) used as a scroll+focus target: the Mac's "Read and approve" action scrolls this heading into view and moves focus to it (`focusCards()`, `main_script.js:343-346`) rather than navigating, fixing 25-Sep finding #15 ("does nothing"). |
| **Posting (Ready)** | Separate screen (`isReady`), back link "‹ Today" | Also folded into Today's right column (`isHomeReady`), no back link needed (`build_mac.py:44`). |
| **Posts / Capture / Replies** | Full-width single column, avatar in header | Centred single column, `max-width` 820px (Posts/Capture) or 880px (Replies) via `narrow()`, no avatar (already in sidebar). |
| **Results** | Single column, 2-col KPI grid, 22px headline | `max-width:960px`, KPI grid forced to **4 columns** (vs phone's 2), headline bumped **22px → 27px** (`build_mac.py:73-75`). |
| **Cortex** | Chat reached via a floating glow pill (`PILL`, phone-only, `showPill: DEVICE==='phone' && screen==='cortex' && !chatOpen`) which opens a bottom sheet | Chat is **permanently docked**: a sticky 400px `<aside>` beside the page content (`CORTEX`, `build_mac.py:79-86`), no pill, no sheet — matches D9/D31 ("docked beside the page" on Mac vs "a floating field that opens a sheet" on iPhone). |
| **Ask Cortex, elsewhere** | Opens the same bottom sheet as Cortex's own chat | Opens a right-side **drawer** (440px) instead — unless already on the Cortex page, where it just updates the docked chat's context chip (`askCortex()`, `main_script.js:279-284`). |
| **Source / Change something / Choose a hook** | Bottom sheets | Centred dialogs (`modal()`, 540/640/560px). |
| **Settings & health** | Bottom sheet, opened from the header avatar button | Popover anchored to the sidebar's profile button (`left:16px; bottom:80px`), and its "Match iPhone" radio label is rewritten to "Match Mac" (`build_mac.py:144`). |
| **Keyboard shortcut** | None | `⌘K` opens Ask Cortex from any page (`globalKey()`, `main_script.js:302`), hinted inline next to the Cortex nav item. |
| **Inert scope while a sheet is open** | Only `<main>` | Both `<main>` **and** `<nav>` (the sidebar) go `inert`, since the sidebar is always on-screen next to any open drawer/popover/modal (`inertOn` feeds both `mainInert` and `navInert`, `build_mac.py:100,153`). |

---

## 8. Inconsistencies found

- **`--on-fill` is a dead token.** Defined in both light (`#FFFFFF`) and dark (`#FFFFFF`) palettes (`ui/mock/project/Main.dc.html:23-25`) but never referenced by `var(--on-fill)` anywhere in `build_body.py`, `build_mac.py`, or `main_script.js`. Either drop it or find its intended use (possibly meant as "text on `--chart-on`" or a filled-icon colour that got superseded).
- **Two font sizes fall under the 12px floor the rest of the system holds to.** The working-line step counter ("Step 2 of 5") renders at **11px** (`ui/mock/project/Thinking.dc.html:73`) and is live inside the real app via `<dc-import name="Thinking">` — not a gallery-only artifact. `WorkingStates.dc.html`'s command labels at **11.5px** (`WorkingStates.dc.html:27`) are gallery-only and lower stakes, but the same pattern.
- **`--hold-fill` and `--blue` are identical in dark mode** (`#9DB3FF` both) but kept as separate tokens — intentional per the 25-Sep review's fix note ("dark hold fill: `--blue`"), yet in light mode they're also identical (`#2340A8` both). If they're meant to always track each other, `--hold-fill` could just be `var(--blue)`; if they're meant to be independently tunable (e.g. so a future "hold" colour can diverge from "live" blue), the current values don't demonstrate that yet — worth a decision before the build treats them as one variable or two.
- **`--blue-fill` and `--blue` diverge only in dark mode** (`#4E6FE6` vs `#9DB3FF`) but are the *same* hex in light (`#2340A8` both). Same ambiguity as above: two names for one value in light, two different values in dark — the intent (a separate "filled progress" blue) is real but only expressed in one theme.
- **Radio-chip groups don't all get the same keyboard treatment.** The Results tabs (`role="tab"`) have full roving-tabindex arrow-key support (`rtKey()`); the Appearance Light/Dark/Match group and the minute/capture-kind/hook `role="radio"` groups do not implement arrow-key roving between chips — they rely on each chip being an independently-tabbable `<button role="radio">`. That's a legitimate simpler pattern for a 2-4-item group, but it means "radio" semantics are promised without full native radio-group keyboard behaviour (no arrow-key movement, Home/End). Worth deciding in the build whether to standardise on one pattern.
- **The "off-topic" colour token (`--chart-off`) is a genuinely different hue from the "on-topic" token (`--chart-on`)** (green vs blue) even though D20 says "one blue for anything live" — this is correct and intentional (off-topic isn't "live," it's a category), but it's the one place a second saturated hue exists outside the amber/blue/purple palette; flagging so the build doesn't assume literally two colours (blue, amber) cover every case.
- **Mac's `H2` component-heading style ("The cards · …", "Posting") reuses `SERIF`/30px** instead of the shared `H2` constant (15-17px sans) — a deliberate one-off (`build_mac.py:40,45`) but it means "H2" isn't a single consistent typographic role across devices; the build should treat Mac's big serif sub-headers as their own named role, not an `H2` variant.
- **`--seg-sel` contrast is background-dependent and only just clears 3:1.** Against `--seg` (the track it usually sits directly on) it's 3.33:1 light / 3.05:1 dark — right at the WCAG 1.4.11 non-text threshold. Any further darkening of `--seg` or lightening of `--seg-sel` in a future palette tweak would fail; worth a wider margin in the build's token set.
- **Guardrail row order and Weights row order aren't sourced from the same list length claim.** Cortex's pipeline tile says "5" Weights (`PIPELINE`, `main_script.js:119`) and the on-screen list has 5 rows (`WEIGHTS`, `main_script.js:92-98`) — consistent — but this is mock placeholder data (`ledger`/`loop/state.json` don't yet store Weights structurally, per `reviews/ui-direction.md:121` C8); the build will need a real schema, not just matching array lengths in JS.
