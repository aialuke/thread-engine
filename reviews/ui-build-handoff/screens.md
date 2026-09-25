# Screens: every screen, section and control

Part 1 covers Today, Post, Posting, Posts and Capture. Part 2 covers Replies, Results, Cortex, every sheet, navigation, the Mac-only pieces, the working line and the canvas. Gaps are numbered G1–G45 in part 1 and G46–G72 in part 2. Line numbers: `Main.dc.html`/`Mac.dc.html` file lines; see each part's §0 for offsets.

## Part 1: Screens, part 1: Today, Post, Posting, Posts, Capture

Scope: the iPhone screens TODAY, POST, READY (posting), POSTS and CAPTURE, plus their Mac equivalents. On the Mac these are the Today page (left column: today; right column: cards or posting), the Posts page and the Capture page. The other handoff part covers Replies, Results, Cortex, the internals of every sheet (Source, Change something, Choose a hook, Settings and health, chat), navigation (tab bar, Mac sidebar, theme toggle, ⌘K) and the working-line component (`Thinking.dc.html`). This part only points to them.

### 0. Conventions

- **Line numbers.** `Main.dc.html:N` and `Mac.dc.html:N` are real file lines. `controls.json` counts from the `<x-dc>` tag at line 9, so **file line = controls.json line + 8** in both files. Script lines are cited as `main_script.js:N`. The same script is inlined at **Main.dc.html:N+756** and **Mac.dc.html:N+801** (checked: `const DEVICE` is at main_script.js:1, Main:757 and Mac:802; `renderVals()` is at 305, 1061 and 1106).
- **`s.*`** means mock state (`DEFAULTS`, main_script.js:166-179). **Handler** means a key returned by `renderVals()` (main_script.js:305-678).
- **Every sheet makes `main` inert** (`mainInert`, main_script.js:468 and 477; `<main inert>` at Main:36 and Mac:62). While a sheet is open, none of the controls below can be reached.
- **Canvas props** (the mock's failure tweaks, Main:756 `data-props`): `health: ok|failed`, `find: found|notfound|differs|twice`, `gate: ok|refused`, `draft: ok|factcheck|error`, `theme`. All of them are mock-only.
- **The clock.** `componentDidMount` calls `forceUpdate` every 1 s (main_script.js:248), so the countdown, the wait timer and the first-hour close all recompute from `Date.now()`.
- **`busy`** = `!!(s.thinking || s.drafting)` (main_script.js:309). `s.thinking` is one of `null | 'ready' | 'next' | 'posted' | 'results'`. `s.drafting` is a queue id or `null`.
- **Mock-only constant:** `TARGET = 2026-09-25T06:00+10:00` (main_script.js:162). It seeds `s.slotMs` (166-167), so after 07:00 on 25 Sep the default view is the "missed" state.

### 0.1 The post's stage (drives TODAY, POST, POSTING)

`s.stage` (default 2, main_script.js:166). `STAGE_NAMES` (161) and the five-step indicator (160, 334-340; step index `at = stage<=3 ? stage : stage-1`):

| s.stage | STAGE_NAMES | Step shown as current | Real source (proposed) |
|---|---|---|---|
| 0 | – | Plan | queue row `status: queued`, nothing planned. **Not reachable in the mock** |
| 1 | Drafting | Draft | row `status: planned`, or `/draft-thread` running. **Not reachable in the mock** |
| 2 | Needs your approval | Approve | row `status: drafted`, and either no `APPROVED` file or its `cards-sha256` doesn't match the cards (`post_thread.approval_refusal`) |
| 3 | Approved | Post | `APPROVED` present and digest matches |
| 4 | Posting | Post | UI session state: the gate passed (exit 0) and posting has started. No file records it today |
| 5 | Posted, measuring | Measure | row `status: posted` with `root_id`, and `ledger/<root_id>.json` exists |

### 0.2 Command IDs (what the real button must run)

Every command runs on the Mac. The iPhone can't run any of them today (review 24 Sep, C1: Keychain, launchd, `pbcopy` and the skills are all Mac-only). The build needs a Mac-side service that runs headless agents with the project's hooks.

| ID | Really does (source) | Writes | Asks the operator (needs-you) |
|---|---|---|---|
| CMD-NEXT | `/next` (`.claude/skills/next/SKILL.md`). Runs `scripts/snapshot.py` (1.1), `loop.py status` (1.2), checks `ledger/runs.log` (1.3), summarises (1.4). If `review.review_due`: weekly review via the results skill, plus the algorithm check `loop.py set-reference` (2). `loop.py next-slot` (3; experiments paused, so there is no arm). Lane share (4.1), `scripts/x_read.py search` for demand (4.2, a Grok call), the queue (4.3), timing: at most 2 originals a day, hours apart (4.4). Proposes in four lines (5). Replies worth making, 2 or 3 with links (6) | on accept: a `queue/topics.yaml` row with `status: planned` and slug/format/lane/experiment/arm/treatment/hypothesis/post_at/leads (5). Snapshot data through `loop.py`. Review files | accept or edit the proposal (5); the experiment "yes" (3); the weekly review's eligibility numbers |
| CMD-DRAFT | `/draft-thread <slug>` (`.claude/skills/draft-thread/SKILL.md`). Reads the contract, the row and the format skill; researches; runs `/verify-settings` in paths and/or claims mode (fails closed); writes files; previews with `post_thread.py --count` | `drafts/YYYY-MM-DD-slug/`: `FORMAT`, `01-hook.md` …, `CLAIMS.md`/`PATHS.md`, `REPLIES.md` (tool-swap), `images.md`, `CHECKLIST.md`; row `status: drafted`, `draft:` (steps 6-7). Never `APPROVED` (8) | build-log and tool-verdict "Material" questions, and a stop without proof (4); the tool-swap's optional operator test, offered once (4) |
| CMD-APPROVE | `.claude/hooks/approve.py`: a UserPromptSubmit hook on typed `/approve <slug>`. Finds the folder (exact name or `*-slug`; ambiguous → block), hashes every numbered card (`post_thread.cards_digest`), writes `APPROVED` | `APPROVED`: `cards-sha256`, `approved-at` (UTC Z), `approved-by: operator, typed /approve` (approve.py:59-62) | – |
| CMD-READY | `/ready` → `python3 scripts/post_thread.py <folder>` (`.claude/skills/ready/SKILL.md`). Exit 2 prints `human gate` (no `APPROVED`). Exit 1 prints `REFUSED:` lines on stderr: a stale digest first, then card refusals for every card. Exit 0 writes the run sheet. `--copy N` copies card N with `pbcopy` and prints `copied post N of M`, `open:`, `wait: …` (tool-swap card 1) and `next:`. Media is revealed in Finder | `POST.txt` in the draft folder | – |
| CMD-POSTED | `/posted <link>` (`.claude/skills/posted/SKILL.md`). Root id from the link; `x_api.py thread <root id>`; saves raw output; matches the queue row; classifies each edit as preference, correction, deviation or violation; asks the minutes; `loop.py record-post` | `ledger/raw/<id>-posted.txt`, `loop/inbox/post-<id>.json`, `ledger/<id>.json` (via loop.py), row `status: posted` and `root_id` | "Roughly how many minutes did this one take?" (5); which slug, if unsure (3) |
| CMD-SNAPSHOT | `python3 scripts/snapshot.py`. Reads the X API (36-60 h and 26-29 day reads, followers, mentions); records through `loop.py` | `ledger/runs.log` line `snapshot ok … cost_usd=` or `snapshot failed error=…` (snapshot.py:196, 210). A failed run records nothing | – |
| X-READ | **No command yet.** Read-only `scripts/x_api.py timeline --start <ISO>`, `thread <id>` or `mentions --since-id` (x_api.py:355-362). Needed for "find my post", live replies and "watch for the shout-out" | nothing, or private data under `loop/followers/` | – |
| CAPTURE-STORE | No backend exists | – | – |
| LOCAL | UI-only state | – | – |
| NO-CMD | The real behaviour needs a new command or file write (named in each block) | – | – |

---

### 1. SCR-TODAY

**Purpose.** The home screen: the next post and its one next action, progress toward X's rewards bars, replies worth making, capture, and planning the next post (D5, D15, D27).

**Sections in order** (iPhone Main:37-166; Mac Main-equivalent Mac:63-195 in the left column, headline full width):
1. Header: date, profile button (iPhone only), h1 headline, health line (D5, D8, D32 on Mac). Main:39-43 · Mac:65-69
2. Health alert when the daily check failed (D8, D20 amber). Main:44-46 · Mac:70-72
3. First hour card, after posting (D29, D34). Main:48-64 · Mac:78-94
4. Next post card: eyebrow, title, Preview (iPhone), when and countdown, five-step indicator, then either the working line (`ready`) or the primary button, hint and "early anyway" (D15, D4, D35, D2). Main:66-90 · Mac:96-119
5. Progress: verified followers, qualified impressions, followers, analytics export (D27). Main:92-114 · Mac:121-143
6. Replies: waiting count and preview, then Worth joining (D12, D28). Main:116-133 · Mac:145-162
7. Capture entry (D25). Main:135-139 · Mac:164-168
8. Plan the next post: button, `next` working line, proposal card, accepted note (D2, D4, D14). Main:141-164 · Mac:170-193

On the Mac, Today's right column shows SCR-POST's content (`isHomeCards`, Mac:197-267) or SCR-POSTING's (`isHomeReady`, Mac:268-317). The Mac `isHome` flag is true for screen `today`, `post` and `ready` (main_script.js:471), so the left column stays visible during review and posting.

**Elements that show data or take input, in order:**

| # | Element | Binding / content | Where (Main · Mac) | Real source |
|---|---|---|---|---|
| 1 | Date line | `todayLabel` | 40 · 66 | device clock, Australia/Brisbane |
| 2 | Profile button | CTL-TODAY-AVATAR | 40 · (sidebar, other part) | – |
| 3 | Headline h1 | `headline` | 41 · 67 | derived from stage and slot (table in CTL-TODAY-PRIMARY) |
| 4 | Health dot and line | `healthDot`, `healthLine` | 42 · 68 | `ledger/runs.log` + `loop.py status` (count of posts still too new) |
| 5 | Health alert and "Run it now" | static text; CTL-TODAY-RUN-HEALTH | 45 · 71 | runs.log |
| 6 | First hour: close time | `fhClose` | 50 · 80 | posting time + 1 h |
| 7 | First hour: posted time and first like | `foundAt`; "3 minutes later" is static, tagged `example` | 51 · 81 | X created_at; first-like time (not stored anywhere, G5) |
| 8 | First hour: "Answer now" item and link | static "@builder.two asked…"; CTL-TODAY-FH-ANSWER-LINK | 54 · 84 | fresh mentions read (X-READ) |
| 9 | Minutes radiogroup | CTL-TODAY-FH-MINUTES | 58-60 · 88-90 | – |
| 10 | Close the first-hour card | CTL-TODAY-FH-CLOSE | 62 · 92 | – |
| 11 | Eyebrow and title | `cardEyebrow`; title static "PAID → FREE: developer tools" | 68 · 98 | queue row (category or slug title) |
| 12 | Preview button | CTL-TODAY-PREVIEW (iPhone only) | 69 · – | – |
| 13 | When and countdown | `whenLabel`, `countdown`, `countdownColor` | 71 · 100 | row `post_at`; posting time once posted |
| 14 | Step indicator `<ol>` | `steps[].{mark,label,state,current,bar,color,weight}` | 72-79 · 101-108 | stage (0.1) |
| 15 | Working line `ready` | `<dc-import Thinking cmd="ready" on-done=doneReady>` when `thinkingReady` | 80-82 · 109-111 | CMD-READY progress |
| 16 | Primary button and hint | CTL-TODAY-PRIMARY; `primaryHint` | 85-86 · 114-115 | – |
| 17 | Start posting early anyway | CTL-TODAY-START-EARLY | 87 · 116 | – |
| 18 | Verified followers "27 of 500", bar, "About 37 a week … in 90 days" | static | 96-98 · 125-127 | `loop.py record-eligibility` / `ledger/SUMMARY.md` "Original Content Rewards"; the rate is derived: (500−27)/(90/7) ≈ 37 |
| 19 | Qualified impressions "337 of 500,000" and definition | static | 101-103 · 130-132 | `record-eligibility` (X's eligibility screen, weekly) |
| 20 | Followers "36", "First daily count 24 Sep" | static | 106-107 · 135-136 | `ledger/activity/account.json` daily count |
| 21 | Analytics export "Thu 1 Oct" and instructions | static | 110-111 · 139-140 | last `loop.py record-export` + 7 days |
| 22 | All replies | CTL-TODAY-ALL-REPLIES | 117 · 146 | – |
| 23 | Waiting summary button | CTL-TODAY-WAITING (`waitingText`, `waitingPreview[].handle/where`) | 120-123 · 149-152 | fresh mentions read (build note D12) |
| 24 | "Worth joining" rows | CTL-TODAY-WORTH-JOINING (`replies[].handle/found/short`) | 126-131 · 155-160 | stored `/next` section 6 output (C5) |
| 25 | Capture blurb and button | CTL-TODAY-CAPTURE | 137-138 · 166-167 | – |
| 26 | Plan the next post | CTL-TODAY-PLAN-NEXT | 143 · 172 | – |
| 27 | Working line `next` | `<dc-import Thinking cmd="next" on-done=doneNext>` when `thinkingNext` | 145-147 · 174-176 | CMD-NEXT progress |
| 28 | Proposal: title, "Tue 29 Sep · 22:00 · no experiment", why | static, tagged `example` | 150-153 · 179-182 | CMD-NEXT proposal (four lines) |
| 29 | Proposal actions | CTL-TODAY-PROPOSAL-ASK, -ACCEPT, -ANOTHER | 154-157 · 183-186 | – |
| 30 | Accepted note "Planned: the build log … It's in Posts, ready to draft." | static, when `proposalAccepted` | 161-163 · 190-192 | the written queue row |

### Controls

```yaml
id: CTL-TODAY-AVATAR
label: "EZ" (plus an amber dot, aria-hidden, when healthBad). aria-label = avatarLabel: "EZ, settings and health" | "EZ, settings and health, something needs you"
where: Main.dc.html:40 (controls.json 32). Mac: none on the page; the Mac equivalent is the sidebar button (toggleSettings, Mac.dc.html:52), covered by the other part
binding: onClick=openSettings (main_script.js:666) → openSheet({settingsOpen:true}, 'Settings and health') (261-270): stores returnFocus, sets s.settingsOpen=true, then focuses the first field or button in the dialog
shown when: always on Today (iPhone)
enabled when: always
purpose: D8. Settings and health open from a round profile button at the top right of each tab's title, with an amber dot when something breaks
real wiring: LOCAL (opens the Settings sheet). The dot needs the real health state; see CTL-TODAY-RUN-HEALTH
states: normal / something-needs-you (dot + label). The mock has no "Mac unreachable" state; the real app needs one (C1)
mock-only: healthBad comes from the canvas prop `health` (main_script.js:440)
a11y: the name carries the health state; the dot is aria-hidden; focus goes into the sheet and returns here on close (restoreFocus, 271)
```

```yaml
id: CTL-TODAY-RUN-HEALTH
label: "Run it now" (inside role=alert: "Last night's daily check didn't run, probably because the Mac was asleep. Numbers are from the night before.")
where: Main.dc.html:45 (cj 37), Mac.dc.html:71 (cj 63). Same handler inside Settings (Main:730, Mac:795; other part)
binding: onClick=fixHealth (main_script.js:490) → setState({healthFixed:true, settingsOpen:false}). healthBad becomes false, so the alert, the dot and the amber health line all revert
shown when: healthBad = props.health==='failed' && !s.healthFixed (440)
enabled when: always
purpose: D8, D20 (amber = needs you). Recovers from a missed 20:00 launchd run
real wiring: CMD-SNAPSHOT (`python3 scripts/snapshot.py` on the Mac). Read the result from its runs.log line. Health is "bad" when the last run is `snapshot failed` or the last `snapshot ok` is more than 30 h old (next SKILL 1.3). Cost is per run (review C7 warns about double-charging across the UTC day boundary, 10:00 Brisbane)
states: mock shows success only (instant). Real needs: running (working line, suggested cmd `sync`), success (health line refreshed from runs.log), failure with its cause: Keychain locked, X credits exhausted, network, or "Mac unreachable" (snapshot SKILL; C1)
mock-only: instant success; the cause text is fixed ("probably because the Mac was asleep")
a11y: the alert is role=alert, so it's announced on appear. After success the button disappears and focus is dropped (no focus management; G32)
```

```yaml
id: CTL-TODAY-FH-ANSWER-LINK
label: "Answer on X ↗" (after "@builder.two asked whether Bruno handles GraphQL.")
where: Main.dc.html:54 (cj 46), Mac.dc.html:84 (cj 76)
binding: <a href="https://x.com" target="_blank" rel="noopener">, no handler
shown when: showFirstHour = s.stage>=5 && !s.firstHourClosed && now < fhCloseMs, where fhCloseMs = (s.foundMs||now)+1h (main_script.js:511, 412-413)
enabled when: always
purpose: D29. Replies to answer now, in the first hour
real wiring: X-READ (`x_api.py mentions --since-id` right after posting; about a cent a read, build note D12) → one row per substantive reply, linking to https://x.com/<handle>/status/<reply id>. Third-party text stays private (C10; keep it in loop/followers/). The operator writes the answer (voice: Replies)
states: mock has one fixed item. Real needs: none yet ("No replies yet"), several, and a failed read
mock-only: the reply text and the link target are placeholders
a11y: the link text names the action; the ↗ glyph is read as part of the name (consider aria-label "Answer on X, opens X")
```

```yaml
id: CTL-TODAY-FH-MINUTES
label: radios "15 min" | "30 min" | "1 hour" | "Longer" in radiogroup "Time taken", under "Roughly how long did this post take you?"
where: Main.dc.html:59 (cj 51; sc-for minuteChips as mc), Mac.dc.html:89 (cj 81)
binding: onClick=mc.pick (main_script.js:512-513) → setState({minutes: <label>}). on/bg/border/weight follow s.minutes
shown when: showFirstHour (as above)
enabled when: always
purpose: D34. The /posted minutes question, asked where the operator already is
real wiring: CMD-POSTED's `production_minutes` (posted SKILL 5-6; loop.py record-post payload). Conflict: /posted asks before `record-post`, but the mock asks after recording (stage 5). record-post won't re-record ("already recorded", loop.py:358) and has no amend command. Choose one: hold record-post until answered or the card closes, or add a loop.py amend command (NO-CMD). production_minutes must be an int or null (loop.py:207-209): map 15/30/60 and "Longer" → ? (G4)
states: none picked / one picked. Real: saved confirmation, save failure
mock-only: the value is never persisted or sent
a11y: role=radio buttons with aria-checked, but each is its own tab stop and there are no arrow keys (G31)
```

```yaml
id: CTL-TODAY-FH-CLOSE
label: "Close the first-hour card"
where: Main.dc.html:62 (cj 54), Mac.dc.html:92 (cj 84)
binding: onClick=closeFirstHour (main_script.js:511) → setState({firstHourClosed:true})
shown when: showFirstHour
enabled when: always
purpose: D29 (the card also closes by itself an hour after posting; review #13)
real wiring: LOCAL, persisted per root id so it stays closed after a reload. If the minutes question is still open, closing it means "no answer" → production_minutes null
states: open / closed. Auto-close at fhClose
mock-only: none beyond the example content
a11y: plain button. Focus is lost when the card unmounts (G32); move it to the Next post card
```

```yaml
id: CTL-TODAY-PREVIEW
label: "Preview"
where: Main.dc.html:69 (cj 61). Mac: none (the cards are always visible in the right column)
binding: onClick=goPost = readCards (main_script.js:484, 347). iPhone: go('post') (308) → screen 'post', prevScreen=current, source null, chatOpen false
shown when: always on Today (any stage, including posted)
enabled when: always
purpose: D16. Read the cards as strangers will see them
real wiring: LOCAL navigation to SCR-POST for the current post's draft folder
states: –
mock-only: –
a11y: the name "Preview" lacks an object; consider "Preview the post"
```

```yaml
id: CTL-TODAY-PRIMARY
label: primaryLabel, by state (main_script.js:350-374; missed = now > slot+1h; late = now > slot; isEarly = more than 30 min before the slot):
  - stage 2, missed: "Read and approve". Headline "The HH:MM slot has passed.". Hint "Approving posts nothing. Then move it to {nextLabel}."
  - stage 2: "Read and approve". Headline "Today's post needs your read." | "Tomorrow's post needs your read." | "Your next post needs your read.". Hint "Change anything first. Edits teach the loop what you prefer."
  - stage 3, missed: "Move it to {nextLabel}" (for example "Move it to tomorrow, 06:00"). Hint "Your approval stays. Nothing is posted for you."
  - stage 3, isEarly: "Remind me at {slot−10 min}" | "Reminder set for {slot−10 min}". Headline "Approved, and ready for HH:MM today|tomorrow|on {Ddd D Mon}.". Hint "A nudge 10 minutes before. Nothing is posted for you." | "Tap to turn it off. Nothing is posted for you."
  - stage 3, otherwise: "Start posting". Headline "Time to post." (late) | "Almost time to post.". Hint "Final checks first. You press Post on X."
  - stage 4: "Back to posting". Headline "You're in the middle of posting.". Hint "The shout-out is still to come."
  - stage 5: "See results". Headline "Posted. Stay close for the first hour.". Hint "The first full read comes with the daily check on {Ddd D Mon} at 20:00." (firstRead, 234: first 20:00 at least 36 h after posting)
where: Main.dc.html:85 (cj 77), Mac.dc.html:114 (cj 106)
binding: onClick=primaryAction, one of:
  - readCards (347): iPhone go('post'); Mac focusCards (343-346): screen 'today', scrolls `[data-te-cards]` (Mac:200 h2, tabindex -1) into view and focuses it
  - moveSlot (332): setState({slotMs: nextSlot(now)}), the next 06:00 at least 30 min away (232)
  - remind toggle (364): setState({remind: !s.remind}). This is the same key as Settings → Notifications → "Before a post" (main_script.js:148, 669-671)
  - startReady (348): returns if thinking or drafting; else setState({screen:'today', thinking:'ready', refused:null}). The ready line (Main:81 / Mac:110) runs, then doneReady (501-508)
  - go('ready') (370): screen 'ready'
  - go('results') (373)
shown when: showPrimary = s.thinking !== 'ready' (499); the working line replaces it while checks run
enabled when: disabled={{primaryDisabled}}, true only for "Start posting" while busy (368); opacity 0.45 (497)
purpose: D2 and D15: one button per step of the post's life. D35: "Remind me" on Today switches the first notification. Review #11 (missed slot), #15 (Mac focus)
real wiring:
  - Read and approve → LOCAL nav to SCR-POST
  - Move it to … → NO-CMD: rewrite this row's `post_at` in queue/topics.yaml (an agent-written file, not loop state). The next slot should come from the posting-slot rule (22:00–23:00 or 05:00–07:00, Tue night to Fri morning; Weights, main_script.js:96), not a fixed 06:00 (G7)
  - Remind me → LOCAL setting `remind` + a scheduled push at post_at−10 min (D35; needs a poller and push, C4; web push on iPhone only works for a home-screen app)
  - Start posting → CMD-READY (`post_thread.py <folder>`). Exit 2 → back to approve; exit 1 → SCR-POSTING refused with each REFUSED line in plain words (ready SKILL 2); exit 0 → SCR-POSTING steps, stage 4
  - Back to posting / See results → LOCAL nav
states: running (the ready working line); success → SCR-POSTING; refused → SCR-POSTING alert; approval stale → the mock silently returns (504, G16). Real also needs: "human gate" (exit 2) and "Mac unreachable"
mock-only: the slot comes from TARGET (162); nextSlot only knows 06:00; the reminder never fires
a11y: the label changes with state. The Remind toggle has no aria-pressed (G8). After Start posting the button unmounts and focus is dropped (G32). Mac focusCards moves focus to the cards heading
```

```yaml
id: CTL-TODAY-START-EARLY
label: "Start posting early anyway"
where: Main.dc.html:87 (cj 79), Mac.dc.html:116 (cj 108)
binding: onClick=startEarly = startReady (main_script.js:498, 348). Same as CTL-TODAY-PRIMARY's Start posting
shown when: showPrimary && showEarlyAnyway (stage 3 && isEarly && !missed; 360-365)
enabled when: disabled={{busy}}; opacity busyOpacity (509)
purpose: D15 and review #16 (disabled while another command runs)
real wiring: CMD-READY, as for Start posting
states: as CTL-TODAY-PRIMARY
mock-only: –
a11y: plain button; focus is dropped when it unmounts (G32)
```

```yaml
id: CTL-TODAY-ALL-REPLIES
label: "All replies"
where: Main.dc.html:117 (cj 109), Mac.dc.html:146 (cj 138)
binding: onClick=goReplies = go('replies') (main_script.js:484, 308)
shown when: always
enabled when: always
purpose: D12
real wiring: LOCAL nav (Replies is covered by the other part)
states: –
mock-only: –
a11y: plain button
```

```yaml
id: CTL-TODAY-WAITING
label: "{waitingText}" + up to two "{handle} · {where}" lines. waitingText = "1 person is waiting for your answer" | "N people are waiting for your answer". Example rows: "@sec.minded · on your breach reply", "@pixel.tools · on PAID → FREE: creator tools"
where: Main.dc.html:120 (cj 112), Mac.dc.html:149 (cj 141)
binding: onClick=goReplies (484). Data: waitingPreview = WAITING not in s.dismissed, first 2 (418, 520); waitingText (521)
shown when: hasWaiting = nWait > 0 (520)
enabled when: always
purpose: D12. Today shows the count; people who replied are the warmest audience
real wiring: LOCAL nav. Data: X-READ fresh mentions read on open, plus `referenced_tweets` stored by the snapshot so answered and unanswered can be told apart (build note D12, C3). Third-party text stays private (C10)
states: waiting ≥1 / none (the button is hidden; the "Worth joining" label follows directly). Real: the read failed, and stale data shown with its read time
mock-only: WAITING constant (main_script.js:30-37), placeholder handles
a11y: the whole summary is one button, so its accessible name is long (the count plus two rows). It opens Replies at the top, not at the person (G45)
```

```yaml
id: CTL-TODAY-WORTH-JOINING
label: per row "{handle} · found {found}" + "{short}". Example rows: "@builder.one · found 05:40", "@lab.notes · found 05:40", "@aus.indie · found 05:40"
where: Main.dc.html:127 (cj 119; sc-for replies as r), Mac.dc.html:156 (cj 148)
binding: onClick=goReplies (484)
shown when: always (list from REPLIES, main_script.js:19-29, 515)
enabled when: always
purpose: D12 (Worth joining), D28 (leans toward verified builders who aren't mutuals yet)
real wiring: LOCAL nav. Data: CMD-NEXT section 6 output (2 or 3 conversations, each a link and a point), which is chat output today and must be stored with its found time (C5). Only posts checked against X by x_read.py may appear
states: rows / none. Real: "Plan the next post to find some" when empty
mock-only: REPLIES constant, placeholder handles
a11y: each row is a button whose name is handle, time and summary. It lands on Replies at the top, not on that row (G45)
```

```yaml
id: CTL-TODAY-CAPTURE
label: "Capture something"
where: Main.dc.html:138 (cj 130), Mac.dc.html:167 (cj 159)
binding: onClick=goCapture = go('capture') (main_script.js:485, 308); prevScreen becomes 'today'
shown when: always
enabled when: always
purpose: D25
real wiring: LOCAL nav to SCR-CAPTURE
states: –
mock-only: –
a11y: plain button
```

```yaml
id: CTL-TODAY-PLAN-NEXT
label: "Plan the next post"
where: Main.dc.html:143 (cj 135), Mac.dc.html:172 (cj 164)
binding: onClick=planNext (main_script.js:525) → if !busy: setState({thinking:'next', proposal:null}). The `next` working line (Main:146 / Mac:175) runs its 5 steps (Thinking STEPS.next), then doneNext (526) → setState({thinking:null, proposal:'shown'})
shown when: showPlanButton = s.thinking!=='next' && !s.proposal (524)
enabled when: disabled={{busy}}
purpose: D2 (every command a button), D4 (working line)
real wiring: CMD-NEXT, all of it (0.2). It stops for needs-you on the proposal, an experiment yes/no and weekly-review eligibility numbers. It ends in a proposal (topic, format, arm, time, why) and the replies list
states: idle, running (working line), proposal shown. Error and needs-you exist in the working line (other part) but aren't wired here (no fail/ask props at Main:146). Real: every one of them
mock-only: fixed 1.5 s steps (Thinking) and a fixed proposal
a11y: the button unmounts while running; the working line has aria-live (Thinking.dc.html). No focus is set when the proposal appears (G32)
```

```yaml
id: CTL-TODAY-PROPOSAL-ASK
label: "Ask Cortex about this" (with the orb icon, aria-hidden)
where: Main.dc.html:154 (cj 146), Mac.dc.html:183 (cj 175)
binding: onClick=askAboutProposal (main_script.js:530) → askCortex('proposal') (279-285): sets chatOpen + context 'proposal' (Mac on the Cortex page only sets context), then focuses the "Ask Cortex" input. Chip "About: the proposed build log" (431)
shown when: proposalShown (527)
enabled when: always
purpose: D14 (a small "Ask Cortex" button on the thing you're looking at)
real wiring: opens the chat with the proposal as context (chat is covered by the other part)
states: –
mock-only: canned answers (SUGGESTIONS)
a11y: the name comes from the text; focus goes to the chat input and returns on close
```

```yaml
id: CTL-TODAY-PROPOSAL-ACCEPT
label: "Accept"
where: Main.dc.html:156 (cj 148), Mac.dc.html:185 (cj 177)
binding: onClick=acceptProposal (528) → setState({proposal:'accepted'}); the "Planned: the build log …" note replaces the card
shown when: proposalShown
enabled when: always (not busy-gated)
purpose: CMD-NEXT step 5 (accept, then write the row)
real wiring: CMD-NEXT continuation: write or update the `queue/topics.yaml` row (status planned, format, lane, hypothesis, post_at, leads, experiment/arm if any). If an experiment was proposed and accepted: `loop.py open-experiment --json loop/inbox/experiment.json`. The row must then appear in SCR-POSTS (G10)
states: accepted. Real: write failed; and "edit before accepting" (the skill allows edits, the mock doesn't)
mock-only: nothing is written; Posts doesn't show the planned row
a11y: focus is dropped when the card unmounts (G32)
```

```yaml
id: CTL-TODAY-PROPOSAL-ANOTHER
label: "Pick another"
where: Main.dc.html:157 (cj 149), Mac.dc.html:186 (cj 178)
binding: onClick=changeProposal (529) → if not thinking or drafting: setState({proposal:null, thinking:'next'}), which reruns the whole `next` line
shown when: proposalShown
enabled when: disabled={{busy}}
purpose: review #16
real wiring: CMD-NEXT, asking for a different proposal in the same session. It should not rerun snapshot.py (C7 double-charge) or the x_read searches unless the topic changes (G11)
states: as CTL-TODAY-PLAN-NEXT
mock-only: reruns the same fixed proposal
a11y: as above
```

---

### 2. SCR-POST

**Purpose.** Read the next post's cards as they'll look on X, check each swap's source, then approve by press-and-hold or edit; once approved, start posting or move a missed slot (D13, D16, D24, D26).

iPhone: its own screen (`isPost`, Main:168-238). Mac: Today's right column (`isHomeCards` = screen `today` or `post`, main_script.js:471; Mac:197-267), with the h2 "The cards · {postTitle}" (Mac:200, `data-te-cards`, tabindex -1) as the focus target.

**Sections in order:**
1. Back (iPhone only) and header: title, status pill, edited-after-approval notice, saved note (D26). Main:170-178 · Mac:199-206
2. Card 1 preview `<article aria-label="Card 1, as it will look on X">`: author row, lines with the fold line and swap buttons, count line (D16, D36 in Source). Main:180-198 · Mac:208-226
3. Ask Cortex about this post (D14). Main:199 · Mac:227
4. Shout-out card: "Then, 10 to 20 minutes later, as a reply. Only people who open your post see this." (D16, D17). Main:201-207 · Mac:229-235
5. Stage 2: "Approve both cards", Change something, hold to approve, help text (D13, D24, D26). Main:209-220 · Mac:237-248
6. Stage 3: early note and early start, or Start posting, or the missed note and Move; Edit a card (D15, review #11). Main:221-236 · Mac:249-264

**Elements:**

| # | Element | Binding | Where (Main · Mac) | Real source |
|---|---|---|---|---|
| 1 | ‹ Today | CTL-POST-BACK | 170 · – | – |
| 2 | Title | `postTitle` (whenShort or "Posted") | 172 · 200 | row `post_at` |
| 3 | Pill "Needs your approval" | `stageApprove` | 173 · 201 | stage 2 |
| 4 | Pill "Approved at {approvedAt}, as shown" | `stageApprovedOnly`, `approvedAt` | 174 · 202 | `APPROVED` `approved-at` in Brisbane time |
| 5 | Pill "Posted {foundAt}" | `stagePosted`, `foundAt` | 175 · 203 | X created_at |
| 6 | "You changed a card after approving it, so approve again." | `editedAfter` | 176 · 204 | digest mismatch (`approval_refusal`) |
| 7 | role=status "Saved. Your edit is recorded as a preference…" | `savedNote` | 177 · 205 | edit store (G12, G13) |
| 8 | Author row "Exit Zero Code", "@exitzerocode · {whenCard}" | `whenCard` | 183 · 211 | account profile; post_at or posting time |
| 9 | Card lines | `cardLines[]`: text, isBlank, isText, isSwap, fade, bg | 186-195 · 214-223 | `01-hook.md` (tweet_text) |
| 10 | Fold line "Strangers stop here unless they tap Show more" | `cl.foldBefore` | 188-190 · 216-218 | X's real truncation rule (build note; G35) |
| 11 | Swap line buttons | CTL-POST-SWAP-SOURCE | 193 · 221 | CLAIMS.md rows |
| 12 | Count "{cardCount} characters as X counts · your limit 600", "Tap an underlined line for its source" | `cardCount`, `countColor` (amber over 600) | 197 · 225 | `post_thread.py --count` / `x_length` |
| 13 | Ask Cortex about this post | CTL-POST-ASK | 199 · 227 | – |
| 14 | Shout-out text "@use_bruno thanks for keeping API collections…" and "95 characters as X counts · account checked 24 Sep" | static | 204-205 · 232-233 | `02-shoutout.md`; handle check `x_api.py user` date (topics.yaml `drafted_note`, CLAIMS.md) |
| 15 | Approve heading and copy | static | 211-212 · 239-240 | – |
| 16 | Change something | CTL-POST-CHANGE | 213 · 241 | – |
| 17 | Hold to approve, with fill width | CTL-POST-HOLD-APPROVE (`holdWidth`, `holdLabel`) | 214-217 · 242-245 | – |
| 18 | Hold help `#te-hold-help` | static | 218 · 246 | – |
| 19 | Early note | `earlyNote` | 224 · 252 | post_at, remind setting |
| 20 | Early / Start / Move / Edit | CTL-POST-START-EARLY, -START, -MOVE-SLOT, -EDIT | 225-234 · 253-262 | – |
| 21 | "The slot has passed. Your approval stays." | `showMoveHere` | 231 · 259 | – |

### Controls

```yaml
id: CTL-POST-BACK
label: "‹ Today"
where: Main.dc.html:170 (cj 162). Mac: none (use the sidebar's Today)
binding: onClick=goToday = go('today') (main_script.js:484, 308)
shown when: always on the iPhone Post screen
enabled when: always
purpose: navigation
real wiring: LOCAL
states: –
mock-only: –
a11y: the "‹" is read aloud; consider aria-label "Back to Today"
```

```yaml
id: CTL-POST-SWAP-SOURCE
label: "{line text}" + visually hidden ", show the source". Example lines: "Postman Team → Bruno", "Navicat Premium → Beekeeper Studio", "ngrok Pay-as-you-go → Cloudflare Tunnel"
where: Main.dc.html:193 (cj 185; sc-for cardLines as cl), Mac.dc.html:221 (cj 213)
binding: onClick=cl.open (main_script.js:401) → openSheet({source: swapIdx}, 'Source'): sets s.source (the line's bg turns --blue-soft, 400) and focuses into the Source dialog (Main:626; other part)
shown when: cl.isSwap, a line that starts with a SWAPS[i].paid + " →" (397-399)
enabled when: always
purpose: D16 (each swap's source one tap away), D36 (US$ labels in the sheet)
real wiring: LOCAL sheet fed from the draft's `CLAIMS.md` rows for that swap (paid fact + source, free quote + source, limit); REPLIES.md holds the talking points. Match by the swap row, not by a hard-coded SWAPS list
states: normal / source open (highlighted). Opacity 0.6 below the fold
mock-only: SWAPS constant (main_script.js:2-15)
a11y: an underlined button whose accessible name adds ", show the source" (te-sr). Focus returns here when the sheet closes
```

```yaml
id: CTL-POST-ASK
label: "Ask Cortex about this post"
where: Main.dc.html:199 (cj 191), Mac.dc.html:227 (cj 219)
binding: onClick=askAboutPost (main_script.js:543) → askCortex('post'). Chip "About: the next post"; suggestions SUGGESTIONS_POST
shown when: always
enabled when: always
purpose: D14
real wiring: chat with the draft folder as context (other part)
states: –
mock-only: canned answers
a11y: as CTL-TODAY-PROPOSAL-ASK
```

```yaml
id: CTL-POST-CHANGE
label: "Change something"
where: Main.dc.html:213 (cj 205), Mac.dc.html:241 (cj 233)
binding: onClick=openEditor (main_script.js:546-550): returns if thinking==='ready'. Otherwise opens the 'Change something' sheet with editorOpen:true and source:null. If no draft is pending, it seeds draftText=cardBase and takeText=cardTake. Save/cancel are in the sheet (saveEdit 558-567; other part)
shown when: stageApprove (s.stage===2)
enabled when: disabled={{editDisabled}} = s.thinking==='ready' (545); opacity editOpacity
purpose: D26 (edit freely before approval; 2-3 hooks; a "my take" line; every edit a preference signal)
real wiring: writes `drafts/<folder>/01-hook.md` (card 1 + take; the gate's 600 cap applies) on save. Card 2 editing is missing (G14). Record the edit as a preference signal: there is no store today (loop.py only learns preferences from /posted edits and `add-preference` needs 3 posts, loop.py:850-859; G13)
states: see the sheet (other part). After save: savedNote
mock-only: edits live in memory
a11y: a disabled attribute during checks (not aria-disabled), so it leaves the tab order and gives no reason
```

```yaml
id: CTL-POST-HOLD-APPROVE
label: holdLabel = "Hold to approve" | "Keep holding…" (while s.hold>0). aria-describedby="te-hold-help": "Press and hold for a second. With a keyboard, hold Space. Approving locks in the cards as shown; nothing is posted."
where: Main.dc.html:214 (cj 206), Mac.dc.html:242 (cj 234)
binding:
  - onPointerDown=holdStart (main_script.js:382-389): a setInterval every 40 ms adds 4 to s.hold; at 100 (about 1.0 s) it calls approveNow
  - onPointerUp / onPointerLeave / onPointerCancel / onLostPointerCapture / onBlur = holdEnd → cancelHold (258): clears the timer and sets hold 0. visibilitychange (hidden) also cancels (249)
  - onKeyDown=holdKeyDown (539): Space/Enter without repeat → preventDefault, holdStart. onKeyUp=holdKeyUp (540) → holdEnd
  - approveNow (377-381): setState({hold:0, stage:3, approvedAt:hhmm(now), approvedText: cardBase(+take), editedAfter:false, savedNote:false}); focusButton(['Start posting','Move it to','Edit a card'])
shown when: stageApprove
enabled when: always (no disabled binding). Nothing edits during a hold
purpose: D13 and D24 (press-and-hold, no Face ID or Touch ID); review #2 (every interruption cancels)
real wiring: CMD-APPROVE's equivalent. It must write `drafts/<folder>/APPROVED` with `cards-sha256` over **all** numbered cards (post_thread.cards_digest), `approved-at` in UTC and `approved-by`. The endpoint must be reachable only by the operator. guard_approved.py blocks agent writes of the marker today, and it must also block agents calling what this button calls (D24 build note; C2). The typed `/approve <slug>` stays as the backup and the accessible route (build note)
states: idle, holding (fill), approved (stage 3, pill "Approved at HH:MM, as shown"), cancelled (fill resets). Real needs: write failed ("Nothing was approved: …", like approve.py:74-77), no draft folder, ambiguous slug
mock-only: approvedText is a copy of card 1 text only (G14); approval lives in memory
a11y: keyboard hold with Space/Enter. There's no click handler, so VoiceOver and Switch Control (a tap) can't approve (build note; G40). The fill isn't announced; the label change is. Focus moves to the next action after approval
```

```yaml
id: CTL-POST-START-EARLY
label: "Start posting early anyway" (after earlyNote: "Approved. It's planned for {whenShort}. Come back about 10 minutes before." [+ " A reminder is set for HH:MM."])
where: Main.dc.html:225 (cj 217), Mac.dc.html:253 (cj 245)
binding: onClick=startEarly = startReady (main_script.js:498, 348). On the iPhone this switches to Today (screen 'today') to show the ready line, then doneReady → screen 'ready'
shown when: stageApprovedOnly && isEarly (isEarly && !missed, 535)
enabled when: disabled={{busy}}
purpose: D15, review #16
real wiring: CMD-READY
states: as CTL-TODAY-PRIMARY Start posting
mock-only: TARGET slot
a11y: focus is dropped when the screen changes (G32)
```

```yaml
id: CTL-POST-START
label: "Start posting"
where: Main.dc.html:228 (cj 220), Mac.dc.html:256 (cj 248)
binding: onClick=startReady (main_script.js:537, 348)
shown when: stageApprovedOnly && showStartHere (!isEarly && !missed, 535)
enabled when: disabled={{busy}}
purpose: D15
real wiring: CMD-READY
states: as above
mock-only: –
a11y: gets focus after approval when shown (approveNow focusButton)
```

```yaml
id: CTL-POST-MOVE-SLOT
label: moveLabel = "Move it to {nextLabel}", for example "Move it to tomorrow, 06:00" (after "The slot has passed. Your approval stays.")
where: Main.dc.html:232 (cj 224), Mac.dc.html:260 (cj 252)
binding: onClick=moveSlot (main_script.js:332, 535) → setState({slotMs: nextSlot(now)})
shown when: stageApprovedOnly && showMoveHere (missed = now > slot+1h)
enabled when: always
purpose: review #11 ("Move it to tomorrow, 06:00" moves this post)
real wiring: NO-CMD: rewrite the row's `post_at` in queue/topics.yaml. Approval is unaffected (the digest covers cards, not time). Take the next slot from the posting-slot rule (G7)
states: moved (the header, countdown and headline follow). Real: write failed
mock-only: 06:00-only slot rule
a11y: gets focus after approval when shown
```

```yaml
id: CTL-POST-EDIT
label: "Edit a card"
where: Main.dc.html:234 (cj 226), Mac.dc.html:262 (cj 254)
binding: onClick=openEditor (as CTL-POST-CHANGE). The sheet then shows the "editing clears approval" warning (editClearsApproval = stage 3, 545). saveEdit with a change: stage→2, editedAfter=true, approvedAt/approvedText cleared (563-565)
shown when: stageApprovedOnly
enabled when: disabled={{editDisabled}} (thinking==='ready'): editing is locked while the checks run (review #1)
purpose: D26, review #1
real wiring: writes the card file. APPROVED stays on disk but goes stale (digest mismatch), so the UI must derive stage 2 from the mismatch
states: as CTL-POST-CHANGE, plus "approve again"
mock-only: –
a11y: as CTL-POST-CHANGE
```

---

### 3. SCR-POSTING (screen `ready`)

**Purpose.** After the final checks pass: copy card 1, post it on X yourself, let the app find it (read-only), wait 10 minutes, thank the maker, record. Refusals stop here with reasons (D15, D17, D29 after).

iPhone: `isReady`, Main:240-289 (h1 "Posting", "‹ Today"). Mac: Today's right column when screen `ready` (`isHomeReady`, Mac:268-317, h2 "Posting", no back button). `backTo(stage)` returns to screen 'post' on the iPhone and 'today' on the Mac (main_script.js:414-415).

**Sections in order:**
1. Back (iPhone), heading. Main:242-243 · Mac:270
2. Refused alert with reasons and "Read and approve again" (review #3). Main:244-246 · Mac:271-273
3. Passed line "The final checks passed. You press Post on X; nothing is posted for you." Main:248 · Mac:275
4. Not now / Withdraw approval (review #12). Main:249 · Mac:276
5. Step 1 "Post the list": copy, copy status, copy again and Open X, I've posted it, `find` working line, not found, found, differs, twice (D17 Post, review #19). Main:250-262 · Mac:277-289
6. Step 2 "Wait, and answer early replies": timer, bar, window text, skip buttons (D17 Wait). Main:263-271 · Mac:290-298
7. Step 3 "Thank the maker": nudge, window closed, copy shout-out, failed, copied with Open your post (D17 Thank, D35, review #10). Main:272-281 · Mac:299-308
8. Step 4 "Done": `posted`/`record` working line and Done (D17 Done). Main:282-286 · Mac:309-313

Step sections carry `aria-disabled="{{sNOff}}"` and badge/head colours from `stepVals` (main_script.js:410, 674). Active: s1 = stage≥4; s2 = posted1; s3 = posted1 && waitLeft===0; s4 = copied2 || skipShout (409).

**Elements:**

| # | Element | Binding | Where (Main · Mac) | Real source |
|---|---|---|---|---|
| 1 | Refusal reasons | `refusedReasons[].t` | 245 · 272 | post_thread.py stderr `REFUSED:` lines, in plain words |
| 2 | Copy status: failed alert, copied status | `copyFailed`, `copiedOk` | 253-254 · 280-281 | clipboard result |
| 3 | `find` working line | `finding` → Thinking cmd="find" on-done=doneFind | 257 · 284 | X-READ |
| 4 | Not-found alert | `notFound` | 258 · 285 | X-READ |
| 5 | Found status | `foundText`: "Found it: posted HH:MM." [+ " Matches your approved card."] | 259 · 286 | X created_at + text match |
| 6 | Differs alert | `foundDiff` | 260 · 287 | text compare with the approved card |
| 7 | Twice alert | `foundTwice` | 261 · 288 | two matching posts |
| 8 | Timer "{waitText}" "until the shout-out window opens" and bar | `waitText` (m:ss), `waitPct` | 266-267 · 293-294 | created_at + 10 min |
| 9 | Window text "Post the shout-out between {winStart} and {winEnd}. No replies yet; new ones show here." | `winStart`, `winEnd` | 268 · 295 | created_at +10 / +20 min; live mentions (C4) |
| 10 | Nudge status "Nudge sent at {winStart}: the window is open." | `nudgeSent` | 275 · 302 | push delivery (D35) |
| 11 | Window closed alert | `windowClosed` | 276 · 303 | clock |
| 12 | Shout-out copy failed alert | `copy2Failed` | 278 · 305 | clipboard |
| 13 | "Copied. Reply to your post with it." + "In the real app this opens the post itself." | `copied2` | 279 · 306 | – |
| 14 | `posted`/`record` working line | `thinkingPosted`, `recordCmd` | 284 · 311 | CMD-POSTED progress |

### Controls

```yaml
id: CTL-POSTING-BACK
label: "‹ Today"
where: Main.dc.html:242 (cj 234). Mac: none
binding: onClick=goToday (main_script.js:484). Stage is unchanged; Today then shows "Back to posting" (stage 4)
shown when: always on the iPhone Posting screen
enabled when: always
purpose: navigation; posting resumes from Today
real wiring: LOCAL. The posting session state (copy done, found root id, found time) must persist across navigation and app restarts
states: –
mock-only: –
a11y: as CTL-POST-BACK
```

```yaml
id: CTL-POSTING-REAPPROVE
label: "Read and approve again" (in role=alert: "The final check stopped this post." + reasons + "Change the card if it needs it, then read and approve again.")
where: Main.dc.html:245 (cj 237), Mac.dc.html:272 (cj 264)
binding: onClick=reapprove (main_script.js:574) → setState({stage:2, refused:null, approvedAt:'', approvedText:''}); readCards() (iPhone → Post; Mac → focusCards)
shown when: readyRefused = !!s.refused (573). s.refused is set by doneReady (505-507) from gateRefusals(card text) (198-219), with "Card 1 changed after you approved it." first when props.gate==='refused'
enabled when: always
purpose: review #3 (the mock runs the gate's refusals), review #15 (Mac focus)
real wiring: LOCAL nav to the cards at stage 2. It shouldn't delete APPROVED (agents may not). A stale APPROVED is simply overwritten by the next approval. For a content refusal (for example "asks for engagement"), steer to edit first: re-approving unchanged cards will be refused again (G17). The reasons come from post_thread.py exit 1 stderr, one plain sentence each with its card (ready SKILL 2)
states: refused. Real also: exit 2 "human gate" ("Not approved yet")
mock-only: gateRefusals covers card 1 with tool-swap rules only (G15); the gate canvas prop
a11y: the alert is announced; the button is inside it. On the Mac, focus moves to the cards heading
```

```yaml
id: CTL-POSTING-NOT-NOW
label: "Not now"
where: Main.dc.html:249 (cj 241), Mac.dc.html:276 (cj 268)
binding: onClick=notNow = backTo(3) (main_script.js:575, 414-415) → stage 3, screen post (iPhone) or today (Mac), copyState 'none', finding false, notFound false; the approval is kept
shown when: readyOk && canBack (stage===4 && !posted1 && !finding, 575)
enabled when: always
purpose: review #12 (a way back once posting starts)
real wiring: LOCAL. Nothing on disk changes (APPROVED and POST.txt stay)
states: –
mock-only: –
a11y: focus is dropped on the screen change (G32)
```

```yaml
id: CTL-POSTING-WITHDRAW
label: "Withdraw approval"
where: Main.dc.html:249 (cj 241), Mac.dc.html:276 (cj 268)
binding: onClick=withdraw = backTo(2) (575, 414-415) → stage 2, approvedAt and approvedText cleared, copy state reset
shown when: readyOk && canBack
enabled when: always
purpose: review #12
real wiring: NO-CMD. The real effect is removing `APPROVED`, which only the operator may do (AGENTS.md; guard_approved.py blocks agents; approve.py only creates). It needs an operator-only path with the same trust as approve (G6)
states: withdrawn. Real: failed
mock-only: memory only
a11y: destructive, but there's no confirmation (approving is cheap to redo, so acceptable)
```

```yaml
id: CTL-POSTING-COPY-POST
label: "Copy the post"
where: Main.dc.html:252 (cj 244), Mac.dc.html:279 (cj 271)
binding: onClick=copy1 (main_script.js:577) → copyText(cardText) (236-244; navigator.clipboard.writeText) → copyState 'ok' | 'failed'; then focusButton(["I've posted it"]) on ok, or (["Copy again"]) on failure
shown when: readyOk && showCopy1 (copyState==='none')
enabled when: always (the step section is aria-disabled only visually before stage 4)
purpose: D17 Post (copy, paste into X)
real wiring: CMD-READY `--copy 1` semantics. Copy the exact text of `01-hook.md` (tweet_text: one trailing newline stripped) after exit 0. `post_thread.py --copy` uses pbcopy, the Mac's clipboard. On the iPhone the app must write the phone's own clipboard with the same text (C1; G18). If images.md names an attachment, say which (the Mac reveals it in Finder)
states: ok → role=status "Copied. Check it starts “PAID → FREE / Finding free developer tools…” when you paste." (the text should come from the card's first line, `open:`); failed → role=alert "Couldn't copy it. Tap Copy again. Nothing old was left for you to paste by mistake."
mock-only: the status text is hard-coded to this draft
a11y: status and alert roles announce the result; focus moves to the next action
```

```yaml
id: CTL-POSTING-COPY-AGAIN
label: "Copy again"
where: Main.dc.html:255 (cj 247), Mac.dc.html:282 (cj 274)
binding: onClick=copy1 (as above)
shown when: readyOk && showCopyAgain (copyState!=='none' && !posted1, 579)
enabled when: always
purpose: recovery from a failed copy, or a re-copy
real wiring: as CTL-POSTING-COPY-POST
states: as above. If the copy keeps failing there's no way forward: "I've posted it" needs copyState 'ok' (580; G19)
mock-only: –
a11y: gets focus after a failed copy
```

```yaml
id: CTL-POSTING-OPEN-X
label: "Open X ↗"
where: Main.dc.html:255 (cj 247), Mac.dc.html:282 (cj 274)
binding: <a href="https://x.com" target="_blank" rel="noopener">
shown when: readyOk && showCopyAgain
enabled when: always
purpose: D17 (paste into X)
real wiring: open the X app or compose (for example https://x.com/compose/post, or the iOS X app). It never posts (AGENTS.md: no X writes)
states: –
mock-only: generic x.com
a11y: opens a new tab/app; say so in the name
```

```yaml
id: CTL-POSTING-POSTED-IT
label: "I’ve posted it"
where: Main.dc.html:256 (cj 248), Mac.dc.html:283 (cj 275)
binding: onClick=postedIt (main_script.js:581) → setState({finding:true, notFound:false}). The `find` line (Main:257) runs its 2 steps, then doneFind (583-588): if props.find==='notfound' and not found once → notFound; else posted1=true, foundMs=Date.now(), foundAt=hhmm, foundDiff (props.find==='differs'), foundTwice (props.find==='twice')
shown when: readyOk && showPosted1 (copyState==='ok' && !posted1 && !finding && !notFound, 580)
enabled when: always
purpose: D17 (the app finds the post itself, read-only; no link pasting), review #19
real wiring: X-READ: `x_api.py timeline --start <copy/approval time>` (own posts; about US$0.001-0.01, C4) → match against the approved `01-hook.md` text → root id and created_at. Found: store root id; the wait timer and first-hour card run from **created_at**, not the time found (review #14; G3). Differs: record as an edit for /posted (preference, correction or violation). Twice: tell the operator to delete the later one and count the first
states: finding, found (role=status), not found (role=alert with Check again and carry on), differs (alert), twice (alert). Real: read failed (Keychain, credits, Mac unreachable)
mock-only: the result comes from the canvas prop `find`; the time is Date.now()
a11y: the button unmounts, and focus isn't moved to the working line or its result (G32)
```

```yaml
id: CTL-POSTING-CHECK-AGAIN
label: "Check again" (in role=alert "Not on X yet. A new post can take a minute to show up.")
where: Main.dc.html:258 (cj 250), Mac.dc.html:285 (cj 277)
binding: onClick=postedIt (581); the second find always succeeds (foundOnce, 585)
shown when: readyOk && notFound
enabled when: always
purpose: D17 recovery
real wiring: X-READ again (rate-limit it; each read costs)
states: as CTL-POSTING-POSTED-IT
mock-only: succeeds on the second try
a11y: as above
```

```yaml
id: CTL-POSTING-CARRY-ON
label: "It’s up, carry on"
where: Main.dc.html:258 (cj 250), Mac.dc.html:285 (cj 277)
binding: onClick=carryOn (main_script.js:589) → setState({notFound:false, posted1:true, foundMs:now, foundAt:hhmm(now)})
shown when: readyOk && notFound
enabled when: always
purpose: the operator's override when X is slow
real wiring: no root id is known, but CMD-POSTED needs one. The real app must keep retrying the find in the background, or ask for the link as a last resort, or leave it to the daily snapshot's auto-record (`record-post` with slug `x-<id>`, replaced later by /posted, loop.py:354-362) (G20). The timer uses "now"
states: –
mock-only: –
a11y: –
```

```yaml
id: CTL-POSTING-SKIP-WAIT
label: "Skip the wait (mock only)"
where: Main.dc.html:269 (cj 261), Mac.dc.html:296 (cj 288)
binding: onClick=skipWait (main_script.js:597) → setState({waitSkipped:true}) → waitLeft 0 (408) → step 3 active
shown when: readyOk && posted1
enabled when: always
purpose: demo only
real wiring: none. Remove it. The format rule is that the shout-out goes 10-20 minutes after the root (format-tool-swap SKILL 90; post_thread SHOUTOUT_WAIT)
states: –
mock-only: yes, entirely
a11y: –
```

```yaml
id: CTL-POSTING-SKIP-SHOUT
label: "Skip the shout-out" (step 2)
where: Main.dc.html:269 (cj 261), Mac.dc.html:296 (cj 288)
binding: onClick=skipShout (main_script.js:598) → setState({skipShout:true, thinking:'posted'}). recordCmd becomes 'record' (602); the step 4 line runs "Recording the post", "Opening the first-hour card", then doneRecord
shown when: readyOk && posted1
enabled when: always
purpose: D17; also experiment arm 1, where a PAID → FREE post skips its shout-out (next SKILL 3)
real wiring: CMD-POSTED straight away with the root only (payload `cards: []`). /ready says /posted waits for the shout-out in a tool-swap (ready SKILL 20), so skipping must be explicit in the record (G23)
states: recording (working line) → Done
mock-only: –
a11y: –
```

```yaml
id: CTL-POSTING-COPY-SHOUT
label: "Copy the shout-out"
where: Main.dc.html:277 (cj 269), Mac.dc.html:304 (cj 296)
binding: onClick=copy2 (main_script.js:600) → copyText(CARD2) → ok: setState({copied2:true, copy2Failed:false, thinking:'posted'}), which starts the `posted` line (watch for the shout-out, record, open first hour); fail: {copy2Failed:true}
shown when: readyOk && waitDone (s3Active && !skipShout) && showCopy2 (!copied2)
enabled when: always
purpose: D17 Thank the maker; review #10 (a failed copy records nothing)
real wiring: `--copy 2` semantics (the `02-shoutout.md` text) to the device clipboard. Then X-READ polls `x_api.py thread <root id>` for the account's reply under the root. When found → CMD-POSTED (thread read, edits, record-post, row posted)
states: ok → the "Copied…" block + Open your post; failed → role=alert "Couldn't copy the shout-out. Tap Copy the shout-out again. Nothing is recorded until it's on X." + Skip. Also shown here: nudgeSent status and windowClosed alert
mock-only: CARD2 constant (main_script.js:17); nudgeSent is shown just because the setting is on (596)
a11y: no focus move after copy2 (unlike copy1)
```

```yaml
id: CTL-POSTING-SKIP-SHOUT-FAILED
label: "Skip the shout-out" (after a failed shout-out copy)
where: Main.dc.html:278 (cj 270), Mac.dc.html:305 (cj 297)
binding: onClick=skipShout (as CTL-POSTING-SKIP-SHOUT)
shown when: readyOk && waitDone && copy2Failed (copy2Failed && !copied2)
enabled when: always
purpose: review #10
real wiring: as CTL-POSTING-SKIP-SHOUT
states: –
mock-only: –
a11y: –
```

```yaml
id: CTL-POSTING-OPEN-POST
label: "Open your post on X ↗" + "In the real app this opens the post itself."
where: Main.dc.html:279 (cj 271), Mac.dc.html:306 (cj 298)
binding: <a href="https://x.com/exitzerocode" target="_blank" rel="noopener">
shown when: readyOk && waitDone && copied2
enabled when: always
purpose: D17 (no hunting for your own post)
real wiring: https://x.com/exitzerocode/status/<root id> from the find step (or the X app deep link). Remove the "In the real app…" line
states: –
mock-only: the profile URL and the explanatory line
a11y: as CTL-POSTING-OPEN-X
```

```yaml
id: CTL-POSTING-DONE
label: "Done" + "It records everything once it sees your shout-out. Tap Done if it doesn't."
where: Main.dc.html:285 (cj 277), Mac.dc.html:312 (cj 304)
binding: onClick=doneRecord (main_script.js:603) → setState({thinking:null, stage:5, screen:'today'}). This is the same callback the working line calls when it finishes (Main:284)
shown when: readyOk && thinkingPosted (s.thinking==='posted')
enabled when: always
purpose: D17 Done (recorded when the shout-out is found, with Done as the fallback)
real wiring: the fallback means "record now with what's on X": run CMD-POSTED without waiting for the shout-out. It must not skip recording. In the mock, Done cancels the line and records nothing (G24). After recording: stage 5, the first-hour card, "See results"
states: recording; done → Today "Posted. Stay close for the first hour." Real: record failed, "already recorded", slug ambiguous (a needs-you from /posted step 3), minutes question (see G4)
mock-only: the working line's steps are timed
a11y: focus lands wherever it can after the screen change (G32)
```

---

### 4. SCR-POSTS

**Purpose.** Every post in one list: up next, other drafts (with the D26 hook picker), the capture inbox entry, the queue with Draft buttons, and the posted history (D15, D25, D26).

iPhone `isPosts` Main:291-344 (header with the profile button). Mac `isPosts` Mac:322-377 (no profile button; that's in the sidebar).

**Sections in order:**
1. Header: profile button (iPhone), h1 "Posts". Main:293-296 · Mac:324-328
2. Up next. Main:297-303 · Mac:329-335
3. Also drafted (example tool verdict + hook) (D26). Main:304-311 · Mac:336-343
4. Capture: count and Open (D25). Main:312-315 · Mac:344-347
5. Queued: rows with Draft, drafting working line, drafted tag, fact-check note (D2, D4). Main:316-331 · Mac:348-363
6. Posted: list with follows, visits and views. Main:332-342 · Mac:364-374

**Elements:**

| # | Element | Binding | Where (Main · Mac) | Real source |
|---|---|---|---|---|
| 1 | Profile button | CTL-POSTS-AVATAR | 294 · – | – |
| 2 | Up next button | CTL-POSTS-UP-NEXT (`whenLabel`, `stageName`) | 299-302 · 331-334 | current post row |
| 3 | "Tool verdict: one fix, three reviewers", "From your voice note. This format opens on a hook you choose." | static, tagged `example` | 307 · 339 | a drafted non-fixed-header row |
| 4 | Hook chosen quote "“{hookChosen}”", "Hook chosen. Your pick is recorded as a preference." | `hookSaved`, `hookChosen` | 309 · 341 | hook store (G12) |
| 5 | "{captureCount} captures waiting to become posts" | `captureCount` | 313 · 345 | CAPTURE-STORE |
| 6 | Queue rows: title, meta | `queue[].title/meta` | 322 · 354 | topics.yaml `status: queued` rows (title from category; meta from roster/notes) |
| 7 | "Drafted · next in line" | `q.isDrafted` | 324 · 356 | row `status: drafted` |
| 8 | Drafting working line | `q.isDrafting` → Thinking cmd="draft" fail={{q.fail}} fail-at="1" on-retry/on-cancel/on-done | 326 · 358 | CMD-DRAFT progress |
| 9 | Fact-check note (role=status) "The fact-check couldn't confirm one claim, so it's left out of the cards. Its row in CLAIMS.md says why." | `q.factNote` | 327 · 359 | VERIFY rows in CLAIMS.md/PATHS.md |
| 10 | Posted rows: title, date, "N follows · N visits · N views [· not counted]" | `postedList[]` | 335-340 · 367-372 | ledger/*.json + record-export (follows, visits) + snapshots (views); boosted = non-organic |

### Controls

```yaml
id: CTL-POSTS-AVATAR
label: "EZ" (aria-label avatarLabel), as on Today
where: Main.dc.html:294 (cj 286). Mac: none (sidebar)
binding: onClick=openSettings (main_script.js:666)
shown when: always on the iPhone Posts screen
enabled when: always
purpose: D8 (the profile button at the top right of each tab's title)
real wiring: as CTL-TODAY-AVATAR
states: as CTL-TODAY-AVATAR
mock-only: as CTL-TODAY-AVATAR
a11y: as CTL-TODAY-AVATAR
```

```yaml
id: CTL-POSTS-UP-NEXT
label: "PAID → FREE: developer tools" + "{whenLabel} · {stageName}", for example "Today, 06:00 · Needs your approval", "Tomorrow, 06:00 · Approved", "Posted 06:04 · Posted, measuring"
where: Main.dc.html:299 (cj 291), Mac.dc.html:331 (cj 323)
binding: onClick=goPost = readCards (main_script.js:484, 347): iPhone go('post'); Mac focusCards (Today, scrolls to and focuses the cards)
shown when: always
enabled when: always
purpose: D15 (the post and its stage)
real wiring: LOCAL nav to the current post (the earliest planned, drafted or approved row by post_at). After posting it should move to Posted and Up next should show the next row (G26)
states: one per stage. Real: nothing planned (point to Plan the next post)
mock-only: fixed title
a11y: one button, and its name is title + time + stage
```

```yaml
id: CTL-POSTS-CHOOSE-HOOK
label: "Choose a hook"
where: Main.dc.html:308 (cj 300), Mac.dc.html:340 (cj 332)
binding: onClick=openHook (main_script.js:609) → openSheet({hookOpen:true}, 'Choose a hook', '[role=radio][aria-checked="true"]'). The sheet (Main:738, other part) picks s.hookPick among HOOKS (155-159) plus an optional take, and saveHook (615) sets hookSaved
shown when: hookNotSaved (!s.hookSaved)
enabled when: always
purpose: D26 (2-3 hooks to choose from; review E4: shown on an example tool verdict because PAID → FREE has a fixed header)
real wiring: NO-CMD. No format skill produces hook options today (format-*/SKILL.md; draft-thread writes one `01-hook.md`), and nothing stores a pick. The build needs /draft-thread to write the options (for example `HOOKS.md` in the draft folder), a save that writes the chosen hook into `01-hook.md`, and a preference-signal store (G12)
states: not chosen / chosen
mock-only: example draft and HOOKS constant
a11y: focus goes to the checked radio in the sheet and returns here
```

```yaml
id: CTL-POSTS-CHANGE-HOOK
label: "Change the hook"
where: Main.dc.html:309 (cj 301), Mac.dc.html:341 (cj 333)
binding: onClick=openHook (as above)
shown when: hookSaved
enabled when: always
purpose: D26
real wiring: as CTL-POSTS-CHOOSE-HOOK. Changing a hook after approval invalidates APPROVED (the digest)
states: –
mock-only: –
a11y: as above
```

```yaml
id: CTL-POSTS-OPEN-CAPTURE
label: "Open" (beside "Capture · {captureCount} captures waiting to become posts")
where: Main.dc.html:314 (cj 306), Mac.dc.html:346 (cj 338)
binding: onClick=goCapture = go('capture') (485); prevScreen becomes 'posts'
shown when: always
enabled when: always
purpose: D25
real wiring: LOCAL nav
states: –
mock-only: the count comes from example captures
a11y: "Open" alone is ambiguous out of context; consider aria-label "Open Capture"
```

```yaml
id: CTL-POSTS-QUEUE-DRAFT
label: "Draft" (per queued row). Example rows: "PAID → FREE: local AI · Ollama, Cline", "… productivity · Obsidian, OnlyOffice", "… privacy · Bitwarden, AdGuard Home", "… storage · Syncthing, Nextcloud"
where: Main.dc.html:323 (cj 315; sc-for queue as q), Mac.dc.html:355 (cj 347)
binding: onClick=q.draft (main_script.js:460) → if not thinking or drafting: setState({drafting: q.id}). The row's `draft` line runs (Main:326). Callbacks:
  - q.onDone (461): drafted[q.id]=true, drafting=null → "Drafted · next in line"; q.factNote if props.draft==='factcheck'
  - fail = draftFail (453): with props.draft==='error' and !s.draftRetried, the line stops at step 2 (fail-at="1") with "Couldn't reach postman.com/pricing. Nothing was written; try again in a minute."
  - q.retry (458): draftRetried=true (the Thinking Try again, Thinking.dc.html:79; other part)
  - q.cancel (459): drafting=null (the Thinking Cancel)
shown when: q.showDraft (!isDrafting && !isDrafted)
enabled when: disabled={{busy}}: only one command runs at a time
purpose: D2, D4, review #18 and #20 (error and fact-check states)
real wiring: CMD-DRAFT `/draft-thread <slug>`. It takes minutes, not 7 seconds (C9). Needs-you: build-log and tool-verdict Material questions (and a stop without proof); the tool-swap's optional test offer. Fails closed: unconfirmed claims stay VERIFY in CLAIMS.md/PATHS.md and out of the cards → factNote. On success the row becomes `drafted` with its `draft:` folder. Order: PAID → FREE rows go in queue order, one every other day (next SKILL 4.3)
states: idle, drafting (working line), error (Try again / Cancel), fact-check note, drafted. Real also: needs-you (Material questions), and "stopped: no proof, pick another format"
mock-only: the fixed error text names postman.com for every row; draftRetried is global; several rows can say "next in line" (G28); QUEUE shows 4 of the 10 queued tool-swap rows (topics.yaml)
a11y: the Draft button unmounts while drafting; the working line is live
```

---

### 5. SCR-CAPTURE

**Purpose.** An inbox for first-hand material (screenshots, recordings, voice notes, one-line notes) and reader questions, each turnable into a post idea (D25).

iPhone `isCapture` Main:346-378 (the tab bar highlights Posts: main_script.js:447). Mac `isCapture` Mac:378-412.

**Sections in order:**
1. Back, h1 "Capture", intro. Main:348-349 · Mac:381-382
2. New capture: kind radiogroup, label "What happened, in one line", textarea, Save. Main:350-357 · Mac:383-390
3. Captured list: kind (+ " · example"), when, text, Turn into a post or "Queued as a {format}". Main:358-368 · Mac:391-401
4. From your readers: one reader question, Turn into a tool verdict or "Queued as a tool verdict". Main:369-376 · Mac:402-409

**Elements:**

| # | Element | Binding | Where (Main · Mac) | Real source |
|---|---|---|---|---|
| 1 | Kind radios | CTL-CAPTURE-KIND | 352 · 385 | – |
| 2 | Textarea | CTL-CAPTURE-TEXT | 355 · 388 | – |
| 3 | Captured rows: kind, when, text | `captures[].kind/when/text` | 362-363 · 395-396 | CAPTURE-STORE |
| 4 | "Queued as a {format}" | `cp.turned`, `cp.format` | 365 · 398 | queue row written |
| 5 | Reader question text | static | 372 · 405 | mentions/replies (X-READ), private |
| 6 | "Queued as a tool verdict" | `readerTurned` | 374 · 407 | queue row written |

### Controls

```yaml
id: CTL-CAPTURE-BACK
label: "‹ Back"
where: Main.dc.html:348 (cj 340), Mac.dc.html:381 (cj 373)
binding: onClick=goBackFromCapture (main_script.js:485) = go(s.prevScreen==='capture' ? 'today' : s.prevScreen): back to 'today' or 'posts', whichever opened it
shown when: always
enabled when: always
purpose: navigation
real wiring: LOCAL (history back)
states: –
mock-only: –
a11y: consider aria-label "Back to Today" or "Back to Posts"
```

```yaml
id: CTL-CAPTURE-KIND
label: radios "Screenshot" | "Screen recording" | "Voice note" | "Just a note" (radiogroup "Kind of capture"); default "Just a note" (DEFAULTS 174; review #25)
where: Main.dc.html:352 (cj 344; sc-for capKinds as ck), Mac.dc.html:385 (cj 377)
binding: onClick=ck.pick (main_script.js:617) → setState({capKind: k})
shown when: always
enabled when: always
purpose: D25
real wiring: CAPTURE-STORE. Each kind other than a note needs its input: a photo or file picker (screenshot), a screen-recording file, the mic (voice note, with a transcript). The mock only takes text (G30)
states: one selected
mock-only: no media
a11y: role=radio buttons, each its own tab stop, with no arrow keys (G31)
```

```yaml
id: CTL-CAPTURE-TEXT
label: <label for="te-cap">"What happened, in one line"; placeholder "Codex and Claude disagreed on the fix; Grok broke the tie"
where: Main.dc.html:355 (cj 347), Mac.dc.html:388 (cj 380)
binding: onChange=setCapText (main_script.js:618) → setState({capText: value}); value={{capText}}
shown when: always
enabled when: always
purpose: D25 (one line on what happened)
real wiring: LOCAL draft text until saved (keep an unsent draft per device)
states: empty / typed
mock-only: –
a11y: a proper label; id te-cap
```

```yaml
id: CTL-CAPTURE-SAVE
label: "Save capture"
where: Main.dc.html:356 (cj 348), Mac.dc.html:389 (cj 381)
binding: onClick=saveCapture (main_script.js:619): if capText.trim() is empty, returns (a silent no-op); else prepends {id:'c<n>-<ts>', kind: capKind, when:'just now', text, format:'build log'} to s.captures and clears capText
shown when: always
enabled when: always (not disabled when the text is empty)
purpose: D25
real wiring: CAPTURE-STORE (none exists). Decide where captures live. They're first-hand material and may include third-party screenshots, so keep them local and out of the shared artifact (C10). The format guess should come from the content (a tool comparison → tool verdict; a pipeline event → build log), not always 'build log'
states: saved (the list grows). Real: saved confirmation (role=status), upload/transcription progress, failure. The empty case should disable the button or say why
mock-only: memory only; format fixed to 'build log'
a11y: no announcement after save; focus stays on the button (G32)
```

```yaml
id: CTL-CAPTURE-TURN
label: "Turn into a post" (per capture). Examples: "Voice note · 0:42 · example — Codex and Claude disagreed on the fix; Grok broke the tie." (format tool verdict), "Screenshot · example — The Bruno collection sitting in the repo as plain files." (format build log)
where: Main.dc.html:364 (cj 356; sc-for captures as cp), Mac.dc.html:397 (cj 389)
binding: onClick=cp.turn (main_script.js:622) → turned[c.id]=true → "Queued as a {format}"; captureCount drops by one (605)
shown when: cp.canTurn (!turned)
enabled when: always
purpose: D25 (captures seed build-log and tool-verdict drafts)
real wiring: NO-CMD. Write a queue/topics.yaml row (status queued, format build-log or tool-verdict, lane main, a note that links the capture). /draft-thread's Material step then uses the capture as proof. /next should see captures when it picks topics (the example proposal cites "your voice note"). The new row must show in SCR-POSTS Queued (G10)
states: turned. Real: write failed
mock-only: nothing appears in the queue
a11y: focus is dropped when the button unmounts (G32)
```

```yaml
id: CTL-CAPTURE-TURN-READER
label: "Turn into a tool verdict" (for "A reader asked how Grok compares with Codex and Claude Code on big projects and tricky debugging.")
where: Main.dc.html:373 (cj 365), Mac.dc.html:406 (cj 398)
binding: onClick=turnReader (main_script.js:623) → setState({readerTurned:true}) → "Queued as a tool verdict"
shown when: readerCanTurn (!readerTurned)
enabled when: always
purpose: D25 (reader questions and waiting replies can become post ideas)
real wiring: NO-CMD, as CTL-CAPTURE-TURN, with format tool-verdict. The source question comes from mentions or replies (X-READ). Keep the asker's text private and cite the question, not the person
states: turned
mock-only: one static reader question
a11y: as above
```

---

### 6. Display values (renderVals keys used in these screens that aren't controls)

All in main_script.js. "Real" is the build's data source.

| Key | Shows | Computed at | Real |
|---|---|---|---|
| isToday, isPost, isReady, isPosts, isCapture | iPhone screen flags (s.screen) | 482-483 | router |
| isHome, isHomeCards, isHomeReady | Mac: left column (today/post/ready), cards (today/post), posting (ready) | 471 | router |
| todayLabel | "Friday 25 Sep · Brisbane" (toLocaleDateString en-AU, Australia/Brisbane) | 491, 225-228 | clock |
| headline | h1; see CTL-TODAY-PRIMARY | 350-374, 493 | stage + post_at + clock |
| healthBad | alert, dot, amber | 440, 488 | runs.log (G33) |
| healthDot | --amber-fill or --ok | 488 | – |
| healthLine | "Daily check ran 20:00 last night. 6 posts are still too new to measure." / "Last daily check: Wed 20:00" | 489 | runs.log last ok; `loop.py status`/`due` for "too new" |
| avatarLabel | profile button name | 487 | health |
| showFirstHour | first-hour card visibility | 511 | stage 5 && posting time + 1 h |
| fhClose | "closes HH:MM" | 511, 413 | created_at + 1 h |
| foundAt | posting time HH:MM (fallback: now) | 590 | X created_at |
| minuteChips[].label/on/bg/border/weight | radio chips | 512-513 | – |
| cardEyebrow | "Next post" / "Just posted" | 493 | stage |
| whenLabel | "Today, 06:00" / "Tomorrow, 06:00" / "Sat 26 Sep, 06:00" / "Posted HH:MM" | 494, 315-316 | post_at / created_at |
| whenShort | same, without the posted case (used in earlyNote) | 494 | post_at |
| whenCard | author-row time | 494 | same |
| countdown | "in H h M m", "in M min", "N min late, still inside the 05:00–07:00 slot", "missed the slot"; "" at stage 5 | 319-329, 495 | clock vs post_at |
| countdownColor | --blue or --amber (late/missed) | 319-329 | – |
| steps[].label/mark/state/current/bar/color/weight | five-step indicator (✓ done, current, to do; aria-current="step") | 334-340, 495 | stage (0.1) |
| stageName | STAGE_NAMES[stage] | 496, 161 | stage |
| primaryLabel, primaryHint, primaryDisabled, primaryOpacity | primary button | 350-374, 496-497 | – |
| showEarlyAnyway | the early button on Today | 365, 498 | – |
| thinkingReady, showPrimary | ready line vs primary button | 499 | command run state |
| busy, busyOpacity | disables Plan, Draft, the Start buttons, Pick another | 309, 509 | "a command is running" (one at a time) |
| hasWaiting, waitingText, waitingPreview[].handle/where | Today replies summary | 418-421, 520-521 | mentions + referenced_tweets |
| replies[].handle/found/short | Worth joining rows | 515 | stored /next section 6 |
| showPlanButton, thinkingNext, proposalShown, proposalAccepted | Plan section state | 524, 527 | CMD-NEXT run + proposal state |
| postTitle | Post heading ("Today, 06:00" or "Posted") | 532 | post_at |
| stageApprove, stageApprovedOnly, stagePosted | Post pills and sections | 533 | stage |
| approvedAt | "Approved at HH:MM" | 534, 379 | APPROVED approved-at |
| editedAfter | "approve again" notice | 534, 564 | digest mismatch |
| savedNote | "Saved. Your edit is recorded as a preference…" | 534, 564 | edit store |
| cardLines[].text/isBlank/isText/isSwap/foldBefore/fade/bg | card preview lines | 393-402, 542 | 01-hook.md; fold rule |
| cardCount, countColor | X-weighted length; amber over 600 | 403, 542, 183-191 | x_length |
| editDisabled, editOpacity | edit lock during checks | 545 | – |
| holdWidth, holdLabel, holdTextColor | hold fill and label | 541 | – |
| isEarly | early branch on Post (isEarly && !missed) | 330, 535 | – |
| showStartHere, showMoveHere, moveLabel | Post stage-3 branches | 535 | – |
| earlyNote | "Approved. It's planned for … Come back about 10 minutes before." (+ reminder) | 536 | post_at, remind |
| readyRefused, readyOk, refusedReasons[].t | Posting refusal | 573, 505-507 | post_thread stderr |
| canBack | Not now / Withdraw visibility | 575 | – |
| showCopy1, copyFailed, copiedOk, showCopyAgain, showPosted1 | step 1 copy states | 576-580 | clipboard result |
| finding, notFound, posted1, foundText, foundDiff, foundTwice | step 1 find states | 582, 591-592 | X-READ result |
| s1Off…s4Off, s1Badge…s4Badge, s1Head…s4Head | step section aria-disabled and colours | 409-410, 674 | – |
| waitText, waitPct | "m:ss" countdown to the window; bar width | 408, 411, 593 | created_at + 10 min |
| winStart, winEnd | shout-out window HH:MM–HH:MM | 413, 594 | created_at + 10 / + 20 min |
| waitDone | step 3 content visible | 599 | – |
| nudgeSent | "Nudge sent at …" | 596 | push delivery receipt |
| windowClosed | "The window closed at …" | 595 | clock |
| showCopy2, copy2Failed, copied2 | step 3 copy states | 601 | clipboard |
| thinkingPosted, recordCmd | step 4 working line; 'posted' or 'record' | 602 | CMD-POSTED run |
| hookNotSaved, hookSaved, hookChosen | Also drafted hook state | 611 | hook store |
| captureCount | un-turned captures | 605 | CAPTURE-STORE |
| queue[].title/meta/showDraft/isDrafted/isDrafting/factNote/fail | queue rows | 454-462 | topics.yaml + CMD-DRAFT state |
| postedList[].title/whenShort/meta | posted history | 606-607 | ledger + export + snapshots |
| capKinds[].label/on/bg/border/weight | kind radios | 617 | – |
| capText | textarea value | 618 | – |
| captures[].kind/when/text/canTurn/turned/format | captured list | 620-622 | CAPTURE-STORE |
| readerCanTurn, readerTurned | reader question state | 623 | – |

**Working-line callbacks** (not controls; they fire when a Thinking line ends; the component is covered by the other part): `doneReady` (501-508; Main:81, Mac:110), `doneNext` (526; Main:146, Mac:175), `doneFind` (583-588; Main:257, Mac:284), `doneRecord` (603; Main:284, Mac:311), `q.onDone`/`q.retry`/`q.cancel` (458-461; Main:326, Mac:358).

**Static text that must become data** (no binding today): the next post's title "PAID → FREE: developer tools" (Main:68, 300; Mac:98, 332); the Progress figures (Main:96-111); the first-hour reply and first-like time (Main:51, 54); the proposal (Main:151-153); the accepted note (Main:162); the shout-out card and its count and check date (Main:204-205); the copied-status opening line (Main:254); the "Also drafted" example (Main:307); the reader question (Main:372).

---

### 7. Gaps

G1. `ui/` shows as untracked (`?? ui/` in git status at session start), though the brief calls the mock "committed". Confirm before the build relies on it.

G2. controls.json line numbers are relative to `<x-dc>`; this file uses file lines (+8).

G3. **Timer base.** `foundMs` is when the app *found* the post (doneFind, main_script.js:586) or the carry-on time (589), not X's created_at. D17 and review #14 say the timer runs from the real posting time. It drives waitLeft, the window, the first-hour close and the first-read date.

G4. **Minutes question vs /posted.** /posted asks for minutes before `record-post` (posted SKILL 5-7). The mock asks after recording, in the first-hour card (D34). `record-post` refuses a second record and has no amend (loop.py:354-358). The chips are ranges and "Longer" has no integer; `production_minutes` is int|null (loop.py:207-209).

G5. **Time to first like** (D29: "Time to first like is recorded per post") has no field, command or read. The mock's "3 minutes later" is example text.

G6. **Withdraw approval** has no real path: removing APPROVED is operator-only and no command does it. Needs a path with the same trust as the approve button (D24).

G7. **Moving the slot.** No command rewrites `post_at`. `nextSlot` knows only 06:00 (main_script.js:232). The posting-slot rule is "22:00–23:00 or 05:00–07:00, Tue night to Fri morning" (Weights, 96; next SKILL 3.3). At stage 2 with the slot missed, the hint says "Then move it to …", but you can't move it until you approve. Review #11 asked for the missed state before approval; the mock only changes the wording.

G8. The "Remind me" primary is a toggle with no `aria-pressed`, and there's no push machinery (C4; D35).

G9. "Nudge sent at …" shows whenever the Settings nudge is on (main_script.js:596), with nothing sent.

G10. **Accepted, turned and queued items never reach Posts.** "It's in Posts, ready to draft." (Main:162), turned captures and the turned reader question all leave the Queued list (the QUEUE constant, 44-49) unchanged.

G11. "Pick another" reruns the whole `next` line, including the snapshot: the C7 double-charge risk.

G12. **The hook picker (D26) has no backend.** No format skill writes hook options, and nothing stores the pick or its "preference" signal.

G13. **Pre-approval edits as preference signals** (D26, savedNote) have no store. loop.py only learns preferences from /posted edits (`add-preference` needs 3 posts, loop.py:850-859).

G14. **Approval scope.** The UI says "Approve both cards", but the mock's approvedText is card 1 (+ take) only (379). The shout-out is static markup (Main:204) that the editor can't edit. The real digest covers every numbered card.

G15. **Gate coverage.** The mock's gateRefusals (198-219) checks card 1 with tool-swap root rules. post_thread.py checks every card: format rules, the root cap for ROOT_LIMIT_FORMATS, the setup-day "Most " opening, VERIFY, 💬, thoughts, solicitation, banned phrases, duplicate numbers and sources media, with the stale digest first.

G16. doneReady returns silently when the approval no longer matches (504). The real app must show "cards changed after approval".

G17. "Read and approve again" re-approves without making you edit, even for content refusals; unchanged cards would be refused again.

G18. **Clipboard on iPhone.** `--copy` uses `pbcopy` on the Mac. The phone must copy locally the exact card text the gate passed.

G19. If the clipboard copy keeps failing, there's no path to "I've posted it" (580). The app needs a manual-select fallback.

G20. "It's up, carry on" leaves no root id for /posted. It needs a background retry, a link fallback, or the snapshot auto-record.

G21. The external links are placeholders: Open X (x.com), Open your post (profile URL), Answer on X (x.com).

G22. Posting step 2 promises "new [replies] show here". There is no live-read machinery (C4, build note D12).

G23. Skipping the shout-out conflicts with /ready's "/posted waits until the shout-out is live" (ready SKILL 20). The record must say the shout-out was skipped (and the experiment arm 1 case).

G24. **Done vs the working line.** Done shows while the record line runs, and both call doneRecord. In the mock, Done ends the flow with nothing recorded. For real, Done must mean "record now".

G25. On the Mac at stage 4, the left column's primary is "Back to posting" while posting is already in the right column: `go('ready')` does nothing there.

G26. After posting, Up next still shows the posted post ("Posted HH:MM · Posted, measuring").

G27. The Posted list is sorted by day of month (`dayOf`, 235, 606), which breaks across months; sort by posted_at. "{n} captures waiting" has no singular ("1 captures", Main:313).

G28. **Queue mock artefacts.** The error text names postman.com for every row (453). draftRetried is global. Several rows can say "Drafted · next in line". The queue shows 4 of the 10 queued rows.

G29. **Draft needs-you isn't modelled.** Material questions and the optional test offer (draft-thread SKILL 4) are missing, as is a realistic duration (C9).

G30. **Capture is text only.** There's no media input for Screenshot, Screen recording or Voice note. New captures always get format 'build log' (619). Save does nothing on empty text, with no feedback. There's no storage or privacy decision.

G31. **Radiogroups** (minute chips, capture kinds) have no roving tabindex or arrow keys. Only the Results tabs have arrow keys (rtKey, 626-632; other part).

G32. **Focus is lost** when a pressed button unmounts after: Start posting → doneReady, I've posted it → doneFind, Done/doneRecord, Run it now, Plan → proposal, Accept, Save capture, Turn into a post, Close the first-hour card, Not now and Withdraw. Only approveNow and copy1 manage focus (380, 577; review #46).

G33. **Health** comes from a canvas prop, and the cause text is fixed. Real health: runs.log `snapshot failed` or more than 30 h since `snapshot ok` (next SKILL 1.3), plus "Mac unreachable" (C1). "Run it now" has no running or failure state.

G34. The Progress figures are static markup. Sources: record-eligibility (27, 337), ledger/activity/account.json (36), record-export (export due date).

G35. The fold line is "the first line where the cumulative X length passes 280" (394-395). The build note says compute where X really shows "Show more".

G36. "your limit 600" is shown for any post. The cap applies only to card 1 of settings, single-tip, build-log, tool-verdict and tool-swap, not to comparison (Guardrails text, main_script.js:104).

G37. The slot is fixed by TARGET (162). Viewed on 25 Sep after 07:00 or any later day, the mock opens in the missed state.

G38. The real draft `drafts/2026-09-24-paid-free-developer/` already has `APPROVED`, but the mock starts at stage 2 (example state). Real stage must come from the files (0.1).

G39. **Stages 0 and 1 aren't shown** on Today's Next post card. The build must design "planned, not drafted" and "drafting" there (Draft from Today, or point to Posts).

G40. **Hold and assistive tech.** The hold has no click path, so VoiceOver and Switch Control can't approve. The typed `/approve` backup only exists in a CLI on the Mac, so the iPhone has no accessible route.

G41. Worth joining rows and the waiting summary all open Replies at the top, not at that item.

G42. On the iPhone, Start posting (from Post) jumps to Today to show the ready line, then to Posting (startReady sets screen 'today', 348; doneReady sets 'ready', 507). This is two screen changes for one tap. Consider running the check in place.

---

### 8. Coverage check against controls.json

In-scope entries: Main isToday 16, isPost 9, isReady 16, isPosts 6, isCapture 6 (53); Mac isHome 14, isHomeCards 8, isHomeReady 15, isPosts 5, isCapture 6 (48). Total 101. Out of scope and not documented here: screen `null` (nav, Mac sidebar, theme), every sheet flag (settingsOpen, editorOpen, chatOpen, hookOpen, hasSource, showDrawer, showPill), isReplies, isResults, isCortex, and Thinking.dc.html.

| controls.json (file:cj line) | File line | Control id |
|---|---|---|
| Main:32 | Main:40 | CTL-TODAY-AVATAR |
| Main:37 / Mac:63 | Main:45 / Mac:71 | CTL-TODAY-RUN-HEALTH |
| Main:46 / Mac:76 | Main:54 / Mac:84 | CTL-TODAY-FH-ANSWER-LINK |
| Main:51 / Mac:81 | Main:59 / Mac:89 | CTL-TODAY-FH-MINUTES |
| Main:54 / Mac:84 | Main:62 / Mac:92 | CTL-TODAY-FH-CLOSE |
| Main:61 | Main:69 | CTL-TODAY-PREVIEW |
| Main:77 / Mac:106 | Main:85 / Mac:114 | CTL-TODAY-PRIMARY |
| Main:79 / Mac:108 | Main:87 / Mac:116 | CTL-TODAY-START-EARLY |
| Main:109 / Mac:138 | Main:117 / Mac:146 | CTL-TODAY-ALL-REPLIES |
| Main:112 / Mac:141 | Main:120 / Mac:149 | CTL-TODAY-WAITING |
| Main:119 / Mac:148 | Main:127 / Mac:156 | CTL-TODAY-WORTH-JOINING |
| Main:130 / Mac:159 | Main:138 / Mac:167 | CTL-TODAY-CAPTURE |
| Main:135 / Mac:164 | Main:143 / Mac:172 | CTL-TODAY-PLAN-NEXT |
| Main:146 / Mac:175 | Main:154 / Mac:183 | CTL-TODAY-PROPOSAL-ASK |
| Main:148 / Mac:177 | Main:156 / Mac:185 | CTL-TODAY-PROPOSAL-ACCEPT |
| Main:149 / Mac:178 | Main:157 / Mac:186 | CTL-TODAY-PROPOSAL-ANOTHER |
| Main:162 | Main:170 | CTL-POST-BACK |
| Main:185 / Mac:213 | Main:193 / Mac:221 | CTL-POST-SWAP-SOURCE |
| Main:191 / Mac:219 | Main:199 / Mac:227 | CTL-POST-ASK |
| Main:205 / Mac:233 | Main:213 / Mac:241 | CTL-POST-CHANGE |
| Main:206 / Mac:234 | Main:214 / Mac:242 | CTL-POST-HOLD-APPROVE |
| Main:217 / Mac:245 | Main:225 / Mac:253 | CTL-POST-START-EARLY |
| Main:220 / Mac:248 | Main:228 / Mac:256 | CTL-POST-START |
| Main:224 / Mac:252 | Main:232 / Mac:260 | CTL-POST-MOVE-SLOT |
| Main:226 / Mac:254 | Main:234 / Mac:262 | CTL-POST-EDIT |
| Main:234 | Main:242 | CTL-POSTING-BACK |
| Main:237 / Mac:264 | Main:245 / Mac:272 | CTL-POSTING-REAPPROVE |
| Main:241 notNow / Mac:268 | Main:249 / Mac:276 | CTL-POSTING-NOT-NOW |
| Main:241 withdraw / Mac:268 | Main:249 / Mac:276 | CTL-POSTING-WITHDRAW |
| Main:244 / Mac:271 | Main:252 / Mac:279 | CTL-POSTING-COPY-POST |
| Main:247 button / Mac:274 | Main:255 / Mac:282 | CTL-POSTING-COPY-AGAIN |
| Main:247 a / Mac:274 | Main:255 / Mac:282 | CTL-POSTING-OPEN-X |
| Main:248 / Mac:275 | Main:256 / Mac:283 | CTL-POSTING-POSTED-IT |
| Main:250 postedIt / Mac:277 | Main:258 / Mac:285 | CTL-POSTING-CHECK-AGAIN |
| Main:250 carryOn / Mac:277 | Main:258 / Mac:285 | CTL-POSTING-CARRY-ON |
| Main:261 skipWait / Mac:288 | Main:269 / Mac:296 | CTL-POSTING-SKIP-WAIT |
| Main:261 skipShout / Mac:288 | Main:269 / Mac:296 | CTL-POSTING-SKIP-SHOUT |
| Main:269 / Mac:296 | Main:277 / Mac:304 | CTL-POSTING-COPY-SHOUT |
| Main:270 / Mac:297 | Main:278 / Mac:305 | CTL-POSTING-SKIP-SHOUT-FAILED |
| Main:271 / Mac:298 | Main:279 / Mac:306 | CTL-POSTING-OPEN-POST |
| Main:277 / Mac:304 | Main:285 / Mac:312 | CTL-POSTING-DONE |
| Main:286 | Main:294 | CTL-POSTS-AVATAR |
| Main:291 / Mac:323 | Main:299 / Mac:331 | CTL-POSTS-UP-NEXT |
| Main:300 / Mac:332 | Main:308 / Mac:340 | CTL-POSTS-CHOOSE-HOOK |
| Main:301 / Mac:333 | Main:309 / Mac:341 | CTL-POSTS-CHANGE-HOOK |
| Main:306 / Mac:338 | Main:314 / Mac:346 | CTL-POSTS-OPEN-CAPTURE |
| Main:315 / Mac:347 | Main:323 / Mac:355 | CTL-POSTS-QUEUE-DRAFT |
| Main:340 / Mac:373 | Main:348 / Mac:381 | CTL-CAPTURE-BACK |
| Main:344 / Mac:377 | Main:352 / Mac:385 | CTL-CAPTURE-KIND |
| Main:347 / Mac:380 | Main:355 / Mac:388 | CTL-CAPTURE-TEXT |
| Main:348 / Mac:381 | Main:356 / Mac:389 | CTL-CAPTURE-SAVE |
| Main:356 / Mac:389 | Main:364 / Mac:397 | CTL-CAPTURE-TURN |
| Main:365 / Mac:398 | Main:373 / Mac:406 | CTL-CAPTURE-TURN-READER |

53 Main rows and 48 Mac rows map to 53 control ids. No in-scope control is undocumented. The only iPhone-only controls are CTL-TODAY-AVATAR, CTL-TODAY-PREVIEW, CTL-POST-BACK, CTL-POSTING-BACK and CTL-POSTS-AVATAR; the Mac has no control of its own in scope.

## Part 2: Screens, part 2: Replies, Results, Cortex, sheets, navigation, working line

Scope: SCR-REPLIES, SCR-RESULTS, SCR-CORTEX; the internals of every sheet (SHT-SOURCE, SHT-EDITOR, SHT-CHAT, SHT-SETTINGS, SHT-HOOK); NAV-PHONE (tab bar, badge, Cortex pill), NAV-MAC (sidebar, status card, profile button, theme toggle, ⌘K hint); the Mac containers MAC-DRAWER, MAC-DOCK, MAC-POPOVER; the working-line component CMP-THINKING; the gallery BRD-GALLERY; canvas tweaks and the dark boards. Part 1 (`screens-part1.md`) covers Today, Post, Posting, Posts and Capture, including the controls that *open* these sheets (CTL-POST-SWAP-SOURCE, CTL-POST-CHANGE, CTL-POSTS-CHOOSE-HOOK, CTL-TODAY-AVATAR …). This part covers what happens inside them.

### 0. Conventions

Same as part 1 §0, restated where it matters here:

- **Line numbers.** `Main.dc.html:N` and `Mac.dc.html:N` are real file lines. controls.json counts from the `<x-dc>` tag at line 9, so **file line = controls.json line + 8** in Main, Mac and Thinking. `main_script.js:N` is inlined at **Main.dc.html:N+756** and **Mac.dc.html:N+801** (`data-props` script tag at Main:756, Mac:801). `Thinking.dc.html:N` is its own file (script at 90-219). `build_body.py` = `ui/mock/src/build_body.py`, `build_mac.py` = `ui/mock/src/build_mac.py`.
- **`s.*`** is mock state (`DEFAULTS`, main_script.js:166-179). **Handler** = a key returned by `renderVals()` (main_script.js:305-678).
- **`busy`** = `!!(s.thinking || s.drafting)` (main_script.js:309). `s.thinking ∈ null|'ready'|'next'|'posted'|'results'`.
- **`go(screen)`** (main_script.js:308) sets `{screen, prevScreen: s.screen, source: null, chatOpen: false}`.
- **Review C-numbers** ("review C1") are `reviews/ui-review-2026-09-24.md` part C. **BQ-Qn / BQ-Cn / BQ-Tn** are `handoff/build-questions.md` questions, hard constraints and threats. **DATA-xxx** ids are `handoff/data.md`. **G1–G45** are part 1's gaps; this part's gaps start at **G46**.
- **Command IDs.** Part 1 §0.2 defines CMD-NEXT, CMD-DRAFT, CMD-APPROVE, CMD-READY, CMD-POSTED, CMD-SNAPSHOT, X-READ, CAPTURE-STORE, LOCAL, NO-CMD. Command internals: `handoff/system-today.md` §2 (cited, not re-derived). This part adds:

| ID | Really does | Writes | Needs-you |
|---|---|---|---|
| CMD-RESULTS | `/results` (system-today.md:329-376). Imports the analytics CSV from `~/Downloads` (step 1), asks X's eligibility numbers (step 2), `loop.py status`/`evaluate` (3), writes `reviews/week-YYYY-Www.md` with its sections (5), `mark-reviewed` + `commit-data` (6), three-sentence summary (7). Network: `x_api.py mentions` (owned, US$0.001/item) and `x_api.py me` (US$0.010) | review file, `loop/state.json.last_review_at`, regenerated views, a `chore(data)` commit | export the CSV if none in 7 days (1); eligibility numbers or decline (2); `add-preference`/`set-lane` yeses (5) |
| CMD-APPLY | `/apply <lesson id>` (system-today.md:378-400). Lesson must be `adopted`, `rule: none`; agent edits one file under `.claude/skills/` or `voice/`; `loop.py commit-rule --lesson <id> --files <path>` | the rule file; a `feat(rules)` commit; `loop/state.json.rules[]` | confirms the shown change (2) |
| CMD-UNDO | `/undo-rule <lesson id>` → `loop.py undo --lesson <id>` (system-today.md:402-421): `git revert`; refuses on uncommitted edits or conflict | revert commit; `rule.undone`, `lesson.rule_state="reverted"` | "keep your uncommitted edits?" on that error |
| CMD-VERIFY | `/verify-settings <slug> [paths|claims]` (system-today.md:484). Fails closed | `PATHS.md`/`CLAIMS.md` | – |
| CORTEX-CHAT | **No backend exists.** A model answering questions about the operator's own posts, weights, lessons and X ranking notes (D9, D14; BQ-Q11). Rules in §4.3 | nothing (answers only) | – |
| REPLIES-READ | **No command exists.** Fresh `x_api.py mentions --since-id <last>` when Replies (or Today's waiting summary) opens (build note D12, ui-direction.md:70). Owned read, US$0.001 per item, each item charged once per UTC day (`reference/x-api.md` P2, P5); review C3 puts the first read of a UTC day at about US$0.06–0.10. Must also know which mentions the operator already answered: `referenced_tweets` on the operator's replies, which the snapshot doesn't store yet (D12 build note). Text of other people's replies stays local in `loop/followers/` (review C10; data.md §5) | private cache under `loop/followers/`, nothing committed | – |
| SETTINGS-STORE | **No store exists.** Per-operator UI settings: notification toggles (D35), theme choice (D23: "kept even if the device changes later"), Cortex model. Not loop state; must not live in `loop/state.json` (loop.py only) | a new settings file or app storage | – |

---

### 1. SCR-REPLIES

**Purpose.** Replies to the operator's own posts that deserve an answer, then builders worth replying to. The operator writes every reply; nothing is pasteable (D12, D14, D28; voice/exit-zero.md "Replies").

**Sections in order** (iPhone `isReplies` Main:380-433, from `build_body.py` REPLIES:400-436 + WAITCARD:383-398; Mac Mac:412-468, same block via `narrow(no_avatar(bb.REPLIES), 880)`, build_mac.py:71):
1. Header: avatar (iPhone only, Main:383), h1 "Replies" (Main:384 · Mac:418), lead "You write every reply. Nothing here is meant to be pasted. Names in this mock are placeholders." (Main:386 · Mac:420).
2. **Waiting for you** "replies to your posts" (D12): one card per waiting reply (`waiting as wt`), or its collapsed outcome row with Undo; empty state; "Plus 37 greetings…" line tagged `example` (Main:387-407 · Mac:421-441).
3. **Builders** "people you've had a real exchange with" (D28): "2 mutuals on topic …(A10)" tagged `example`, then the `builders` list (Main:408-419 · Mac:442-453). Display only.
4. **Worth joining** "verified builders first" (D12, D28): one card per `replies` row with "Open on X ↗" (Main:420-430 · Mac:454-464).
5. Footer note on reply volume (A12, A13): "Your busiest 24 hours (Wed to Thu) had 68 replies…" (Main:431 · Mac:465).

Mac differences: no avatar (`no_avatar`), 880px measure. Otherwise identical.

### Controls

```yaml
id: CTL-REPLIES-AVATAR
label: "EZ" (+ amber dot aria-hidden when healthBad). aria-label = avatarLabel
where: Main.dc.html:383 (cj 375). Mac: none (sidebar CTL-NAVMAC-PROFILE)
binding: onClick=openSettings (main_script.js:666) → openSheet({settingsOpen:true}, 'Settings and health')
shown when: isReplies (iPhone)
enabled when: always
purpose: D8 (profile button top right of each tab's title)
real wiring: LOCAL. Identical to CTL-TODAY-AVATAR (part 1); the dot needs real health (G33)
states: normal / needs-you
mock-only: –
a11y: name carries health state; focus returns here on close (restoreFocus, 271)
```

```yaml
id: CTL-REPLIES-ANSWER-LINK
label: "Answer on X ↗" (one per open waiting card)
where: Main.dc.html:397 (cj 389), Mac.dc.html:431 (cj 423); inside <sc-for waiting as wt>, <sc-if wt.open>
binding: <a href="https://x.com" target="_blank" rel="noopener">, no handler, no state change
shown when: wt.open = !s.dismissed[wt.id] (main_script.js:516)
enabled when: always
purpose: D12 (answer the warmest audience first), D14 (the operator writes the reply on X)
real wiring: REPLIES-READ supplies the mention id → href https://x.com/<handle>/status/<mention id> (deep link to reply composer is not needed; X's own reply box). Never pre-fills text (voice: "The operator writes it in their own words"; A12 sees pasted replies)
states: mock only has the link. Real: link per mention; when the mention was deleted, the card should say so after the next read
mock-only: href placeholder (part 1 G21)
a11y: the ↗ glyph is part of the name; add "opens X" in the accessible name. Same text on every card → screen-reader link list reads "Answer on X" ×3; add the handle to aria-label ("Answer @sec.minded on X")
```

```yaml
id: CTL-REPLIES-ANSWERED
label: "Answered"
where: Main.dc.html:398 (cj 390), Mac.dc.html:432 (cj 424)
binding: onClick=wt.answered = mark(wt.id,'answered') (main_script.js:419, 518) → s.dismissed = {...dismissed, [id]:'answered'}. Card collapses to "<handle> · Answered" + Undo; waitingCount, badge, tab label and Today's waiting summary all drop by one (420, 449, 520-521)
shown when: wt.open
enabled when: always
purpose: D12 (Waiting shrinks as you answer)
real wiring: NO-CMD. Needs a reply-outcome store (data.md "Reply outcome"). Better: confirm from X — the operator's reply with referenced_tweets → this mention id (D12 build note) — and auto-collapse; the button then records the operator's claim until the read confirms it. Private (other people's ids) → loop/followers/-style local storage, not committed
states: mock: instant. Real: saved / save failed; "confirmed on X" vs "you said answered"
mock-only: dismissal lives in memory only; reload restores all three
a11y: the button unmounts on click (the card becomes the collapsed row), so focus is lost (extends part 1 G32). Move focus to the new Undo button
```

```yaml
id: CTL-REPLIES-NOT-ANSWERING
label: "Not answering"
where: Main.dc.html:399 (cj 391), Mac.dc.html:433 (cj 425)
binding: onClick=wt.skip = mark(wt.id,'skipped') (main_script.js:518) → dismissed[id]='skipped'; collapsed row status "Not answering" (517)
shown when: wt.open
enabled when: always
purpose: D12. Lets a substantive reply leave the waiting list without an answer
real wiring: NO-CMD, same store as CTL-REPLIES-ANSWERED. Outcome "skipped" must survive re-reads so the mention doesn't return
states: as Answered
mock-only: memory only
a11y: as Answered (focus lost on unmount)
```

```yaml
id: CTL-REPLIES-UNDO
label: "Undo" (in the collapsed row "<handle> · Answered|Not answering")
where: Main.dc.html:390 (cj 382), Mac.dc.html:424 (cj 416)
binding: onClick=wt.undo = mark(wt.id,null) (main_script.js:419, 518) → deletes dismissed[id]; the card reopens
shown when: wt.closed = !!s.dismissed[wt.id] (516)
enabled when: always
purpose: D12; review 25 Sep #29–47 ("reply outcomes with Undo")
real wiring: NO-CMD, same store (delete the outcome). If the outcome was confirmed from X, Undo should not be offered (or should only hide the confirmation)
states: instant
mock-only: –
a11y: unmounts on click → focus lost; move focus to the reopened card's "Answered". The collapsed row has no live region, so the change isn't announced
```

```yaml
id: CTL-REPLIES-ASK
label: "Ask Cortex about this reply" (orb icon aria-hidden)
where: Main.dc.html:401 (cj 393), Mac.dc.html:435 (cj 427)
binding: onClick=wt.ask → askCortex('reply') (main_script.js:519, 279-285): returnFocus = this button; setState({chatOpen:true, context:'reply'}) (Mac off Cortex → MAC-DRAWER; iPhone → SHT-CHAT); focuses the last shown "Ask Cortex" input. Chip "About: a reply waiting for you" (431); suggestions = SUGGESTIONS_REPLY (133-136)
shown when: wt.open
enabled when: always
purpose: D14 (small Ask button on the thing you're looking at; "On a reply, Cortex discusses the point but never writes it (A12)")
real wiring: CORTEX-CHAT with context = this mention (id, author handle, text, the post it replies to, the suggested point). The mock's context is only the string 'reply' — it doesn't say WHICH reply (G46). The reply text is untrusted third-party input (prompt injection; §4.3)
states: see SHT-CHAT
mock-only: every waiting card opens the same generic context
a11y: text name is unique per card only by position; add the handle to the name
```

```yaml
id: CTL-REPLIES-WORTH-OPEN
label: "Open on X ↗" (one per Worth joining card)
where: Main.dc.html:427 (cj 419), Mac.dc.html:461 (cj 453); <sc-for replies as r>
binding: <a href="https://x.com" target="_blank" rel="noopener">, no handler
shown when: always on Replies (3 rows)
enabled when: always
purpose: D12, D28 (Worth joining leans to verified builders who aren't mutuals yet)
real wiring: stored CMD-NEXT section 6 output (review C5: store it with "found HH:MM"); href = the post's URL. Every suggested post must have passed the x_read.py id check (AGENTS.md: "Never cite a post that didn't pass this check"; review C10 "checked against X"). No "Ask Cortex" on these cards (asymmetry with Waiting; G47)
states: real: none found / stale (found yesterday) / list. Freshness and cost: G67
mock-only: href placeholder; handles are dotted placeholders (main_script.js:18)
a11y: identical link text ×3; add the handle to the name
```

**Not controls, but data on this screen:** `wt.handle/where/age/said/point` (DATA-RP01), `b.handle/last/tags` (DATA-RP03), `r.handle/found/kind/what/point` (DATA-RP02), "2 mutuals" (DATA-RP04), "37 greetings" (DATA-RP05), footer (DATA-RP06). "A point you could make" is a talking point, never paste-ready text (D14; format-tool-swap REPLIES.md rule in AGENTS.md).

---
### 2. SCR-RESULTS

**Purpose.** This week's numbers, led by two lines (D18), in three tabs Growth → Posts → Replies opening on Growth (D22, D27, D33), with a table view for every chart, "Ask Cortex about these results" and the weekly review button (D2, D4).

**Sections in order** (iPhone `isResults` Main:435-541, from `build_body.py` RESULTS:458-543; Mac Mac:469-577 via `narrow(no_avatar(bb.RESULTS), 960)` with KPI grid 4 columns and h1 27px, build_mac.py:72-75):
1. Eyebrow "Results · week of 18–24 Sep" (static) + avatar (iPhone) (Main:438 · Mac:473).
2. h1, two spans (D18): serif line "Every profile visit from an unboosted post came from one networking post." and sans line "115 replies brought 14,220 views and 4 follows." (Main:439 · Mac:474; DATA-RES01).
3. Controls row: tablist Growth/Posts/Replies (Main:442-446 · Mac:477-481); date-range radiogroup 7/30/90 days + "Show as table" (Main:448-453 · Mac:483-488); note "Data starts 20 Sep, so 30 and 90 days open up later." (Main:455 · Mac:490; DATA-RES18).
4. Tab panel `#te-rt-panel` (Main:457-535 · Mac:492-570): four KPI tiles `kpis` (DATA-RES02–10), then per tab:
   - Growth: "Where this week's 19 follows came from" bars/table (DATA-RES11); "Followers over time" single column "36 · Thu 24 Sep" / table (DATA-RES12).
   - Posts: "On topic, last 15 posts / target 12" 15-slot strip or table, legend, D19 definition (DATA-RES13, 14); "Posts, by what they brought" list/table sorted follows→visits→views, "Charts come once there's a month of data. The boosted post never counts as a win." (DATA-RES15).
   - Replies: "Replies that led somewhere" bars/table (DATA-RES16); footnote on reply views (DATA-RES17, D27).
5. "Ask Cortex about these results" (Main:536 · Mac:571).
6. "Write this week's review" → working line `results` with needs-you → "Review written" status (Main:537-539 · Mac:572-574).

### Controls

```yaml
id: CTL-RESULTS-AVATAR
label: "EZ"; aria-label = avatarLabel
where: Main.dc.html:438 (cj 430). Mac: none
binding: onClick=openSettings (main_script.js:666)
shown when: isResults (iPhone)
enabled when: always
purpose: D8
real wiring: LOCAL (as CTL-TODAY-AVATAR)
states: normal / needs-you dot
mock-only: –
a11y: as CTL-TODAY-AVATAR
```

```yaml
id: CTL-RESULTS-TAB
label: "Growth" | "Posts" | "Replies" (role=tab)
where: Main.dc.html:443/444/445 (cj 435/436/437), Mac.dc.html:478/479/480 (cj 470/471/472). Container role=tablist aria-label="Results" onKeyDown=rtKey (Main:442, Mac:477)
binding: onClick=rtGoGrowth|rtGoPosts|rtGoReplies (main_script.js:625) → s.rtab. aria-selected=rtGrowth/rtPosts/rtReplies, tabindex=rt*Ti ('0' selected, '-1' others), styles rt*Bg/Border/Weight (seg(), 438-439, 675). rtKey (626-632): ArrowRight/ArrowLeft wrap, Home→Growth, End→Replies; preventDefault, sets rtab, then focuses the j-th shown [role=tab] 60 ms later. aria-controls="te-rt-panel"; the one panel's aria-label=rtPanelLabel (633)
shown when: isResults
enabled when: always
purpose: D22, D27, D33 (order Growth, Posts, Replies; opens on Growth: DEFAULTS rtab 'growth', 172)
real wiring: LOCAL (view state). Remembering the last tab per device is optional LOCAL storage
states: n/a
mock-only: –
a11y: correct APG tabs pattern with automatic activation. rtKey focuses `this.shown('.te-root [role=tab]')[j]`, which assumes the Results tabs are the only visible role=tab in .te-root (true today)
```

```yaml
id: CTL-RESULTS-RANGE
label: "7 days" (checked) | "30 days" | "90 days" (disabled, title "Data starts 20 Sep")
where: Main.dc.html:449/450/451 (cj 441/442/443), Mac.dc.html:484/485/486 (cj 476/477/478); role=radiogroup aria-label="Date range" (Main:448, Mac:483)
binding: none. "7 days" has no handler and aria-checked="true" hard-coded; the other two disabled="{{ true }}"
shown when: isResults
enabled when: 7 days always (does nothing); 30/90 never in the mock
purpose: D22 (one row of date range and table toggle); DATA-RES18
real wiring: LOCAL filter over the ledger reads (ledger/activity/*.json, ledger/<id>.json). Enable 30 when the earliest organic read is ≥30 days old (first post 20 Sep → about 20 Oct); 90 about 19 Dec. Every KPI sub-label and the header lines are weekly today ("this week", "week of 18–24 Sep"), so the range must drive the header too, or the header stays weekly (G48)
states: real: each range needs its own empty/insufficient-data state
mock-only: whole control is inert
a11y: no roving tabindex or arrow keys (same issue as part 1 G31); a disabled radio with only a `title` gives touch and screen-reader users no reason (the visible note at Main:455 does)
```

```yaml
id: CTL-RESULTS-TABLE-TOGGLE
label: tableLabel = "Show as table" | "Show charts"
where: Main.dc.html:453 (cj 445), Mac.dc.html:488 (cj 480)
binding: onClick=toggleTable (main_script.js:635) → s.showTable = !s.showTable; showChart = !showTable (634). Applies to every chart in every tab; persists across tab switches
shown when: isResults
enabled when: always
purpose: D22 ("a table view for every chart"); review 25 Sep #21
real wiring: LOCAL (view preference; may persist per device)
states: n/a
mock-only: –
a11y: label swap conveys state; aria-pressed would be more robust. Tables have scope=col headers and no <caption> (the section h2 precedes them, but isn't associated)
```

```yaml
id: CTL-RESULTS-ASK
label: "Ask Cortex about these results" (orb aria-hidden)
where: Main.dc.html:536 (cj 528), Mac.dc.html:571 (cj 563)
binding: onClick=askAboutResults → askCortex('results') (main_script.js:645, 279-285). Chip "About: this week's results"; suggestions SUGGESTIONS_RESULTS (129-132)
shown when: isResults
enabled when: always
purpose: D14
real wiring: CORTEX-CHAT with context = the current tab, range and the numbers on screen (own data only; DATA-RES*). The context should carry which tab was open; the mock's doesn't (G46)
states: see SHT-CHAT
mock-only: canned answers
a11y: fine
```

```yaml
id: CTL-RESULTS-WRITE-REVIEW
label: "Write this week's review"
where: Main.dc.html:537 (cj 529), Mac.dc.html:572 (cj 564)
binding: onClick=writeReview (main_script.js:647): if !busy → s.thinking='results'. disabled={{busy}}, opacity busyOpacity (509). The button hides (showReviewButton = thinking!=='results' && !s.review, 646) and the working line mounts (thinkingResults, Main:538 · Mac:573): <dc-import Thinking cmd="results" ask=reviewAsk ans-a="Use 24 Sep's: 27 and 337" ans-b="Leave them out this week" on-done=doneReview>. After 4 steps (6 s) it stops in needs-you; either answer → finish() → onDone → doneReview (647): thinking=null, review=true → role=status "Review written · The next one is due Thu 1 Oct, after your analytics export." (Main:539 · Mac:574)
shown when: showReviewButton
enabled when: !busy (no other command running: ready, next, posted, results, or a draft)
purpose: D2, D4; review 25 Sep #18 (the review asks for the eligibility numbers)
real wiring: CMD-RESULTS. Needs-you states in the real order: step 1 CSV export missing (instructions "X on a computer → Premium → Analytics → Content → Export, last 7 days"; on iPhone there is no ~/Downloads, so a file import is needed, system-today.md:356-361), step 2 eligibility numbers (two numbers to type, or decline), step 5 add-preference/set-lane yeses. "Use 24 Sep's: 27 and 337" means reuse the last record-eligibility reading. Should only be offered when review.review_due (loop.py status), otherwise `/results` prints numbers only (step 4). Result: link to reviews/week-YYYY-Www.md and the 3-sentence summary (step 7). Network: mentions + me (about US$0.01 + items)
states: mock: idle → running → needs → done. Missing: error (Thinking supports fail/onRetry/onCancel, not wired here), "not due yet" (G49), the review content itself (nothing opens it), the second and third questions
mock-only: both answers do the same thing (no onA/onB); needs-you appears after the last step, not at step 2 (G50); due date "Thu 1 Oct" static (DATA-RES20)
a11y: the button unmounts when pressed → focus lost (part 1 G32); needs-you is role=alert (Thinking.dc.html:83) so it's announced; "Review written" is role=status
```

**Working-line callback** (not a control): `doneReview` (main_script.js:647).

---

### 3. SCR-CORTEX

**Purpose.** What the engine knows and how it may change: pipeline counts, Lessons (with receipts), Weights (tunable), Guardrails (never tunable), Experiments, Open questions, and the glowing chat (D6, D7, D9, D10, D11, D14, D31).

**Sections in order** (iPhone `isCortex` Main:543-608, from `build_body.py` CORTEX:545-611; Mac Mac:578-671, build_mac.py:77-86: a 2-column grid, content left and MAC-DOCK chat right, 400px, sticky, 820px tall):
1. Eyebrow "What your engine knows" + avatar (iPhone), h1 "Cortex", lead "Set by you for now. Once experiments finish, it proposes changes and you decide." (Main:546-548 · Mac:582-584).
2. Pipeline tiles `pipeline`: 2 Open questions · 0 Experiments · 0 Lessons · 5 Weights, and "Questions become experiments. Experiments become lessons. You apply a lesson to change a weight." (Main:550-555 · Mac:586-591; DATA-CX01).
3. **Lessons**: "No lessons yet. The first experiment can start around 8 Oct…" then the example lesson card "EXAMPLE OF A LESSON · NOT REAL DATA" with 24 vs 11 bars, "6 posts each · 20 Sep – 12 Oct / Bar set before the test: 1.5×. Result: 2.2×. / Proven 14 Oct", and disabled "Apply to Post length" + "Undo" (Main:556-569 · Mac:592-605; D7, D10; DATA-CX02, CX03).
4. **Weights** "the ones that matter most": `weights` (name, src, value; italic when `guess`) (Main:570-580 · Mac:606-616; D11; DATA-CX04).
5. **Guardrails** "never changed by Cortex or the loop": `guardrails` with lock icons (Main:581-586 · Mac:617-622; DATA-CX05; AGENTS.md "What the loop may never change").
6. **Experiments**: "None running · Paused until about 8 Oct", reason line, "Up next, in order" `nextExperiments` with "Queue for about 8 Oct" on the first (Main:587-602 · Mac:623-638; DATA-CX06, CX07).
7. **Open questions**: `questions` (Main:603-606 · Mac:639-642; DATA-CX08).
8. iPhone: the floating glowing pill "Ask Cortex…" above the tab bar (NAV-PHONE, CTL-NAVPHONE-PILL). Mac: MAC-DOCK (§5.2), always visible on this page.

### Controls

```yaml
id: CTL-CORTEX-AVATAR
label: "EZ"; aria-label = avatarLabel
where: Main.dc.html:546 (cj 538). Mac: none
binding: onClick=openSettings (main_script.js:666)
shown when: isCortex (iPhone)
enabled when: always
purpose: D8
real wiring: LOCAL
states: normal / needs-you
mock-only: –
a11y: the pill (outside <main>) is not made inert while Settings is open (G53)
```

```yaml
id: CTL-CORTEX-APPLY
label: "Apply to Post length" (example lesson card)
where: Main.dc.html:567 (cj 559, first of two), Mac.dc.html:603 (cj 595)
binding: none; disabled="{{ true }}" always
shown when: isCortex (static, inside the example card)
enabled when: never in the mock
purpose: D7 (lesson with its receipt), D11 (a lesson changes a Weight), AGENTS.md ("Lessons may change … through /apply only"); GUARDRAILS[5] "Lessons change things only when you apply them."
real wiring: CMD-APPLY with the lesson id. Enabled only when the lesson is `adopted` with `rule: none` and the latest weekly review proposes a change (apply SKILL 1-2). Before running, show the proposed file diff (step 2 shows the change and the file) — the button is the operator's consent, like Approve, so it must be operator-only: /apply is `disable-model-invocation`, and the D24 build note ("block agents from calling whatever the button calls"; BQ-C3 for Approve) applies equally (G51). Target label must name a real Weight: "Post length" isn't among the five WEIGHTS (Opening, Daily limit, Series pace, Posting slots, On topic means) (G52)
states: real: running (seconds, working line), success ("Applied <id>. Drafts follow it from now on." + Undo appears), refused (not adopted; no proposal; file outside .claude/skills or voice; nothing to commit — loop.py:889-896)
mock-only: example card, never enabled
a11y: a disabled button with no explanation; the card's "EXAMPLE … NOT REAL DATA" label explains it visually
```

```yaml
id: CTL-CORTEX-UNDO
label: "Undo" (example lesson card)
where: Main.dc.html:567 (cj 559, second), Mac.dc.html:603 (cj 595)
binding: none; disabled always
shown when: isCortex (static)
enabled when: never in the mock
purpose: D7, D11; CMD-UNDO
real wiring: CMD-UNDO with the lesson id. Enabled when the lesson has a non-undone rules[] entry. Errors: "uncommitted edits" (needs-you: keep them?) and "conflicted" (nothing changed; needs a hand fix in Claude Code) (undo-rule SKILL 3)
states: real: running (seconds), success ("Reverted <id>. Drafts are back to the rule before it."), the two errors
mock-only: never enabled
a11y: as Apply; both labels are generic — add the lesson to the name
```

```yaml
id: CTL-CORTEX-QUEUE-EXP
label: queueLabel = "Queue for about 8 Oct" | "Queued for about 8 Oct"
where: Main.dc.html:597 (cj 589), Mac.dc.html:633 (cj 625); inside <sc-for nextExperiments as x>, <sc-if x.first>
binding: onClick=queueFirst (main_script.js:653) → s.queuedExp=true; disabled={{queuedExp}} (so it can't be undone)
shown when: isCortex, on the first "Up next" row only ("A single post against a thread")
enabled when: !queuedExp
purpose: D6 (experiments coming up); review 25 Sep #29–47 ("Queue for about 8 Oct")
real wiring: NO-CMD. There is no "queued experiment" record: experiments are opened by `loop.py open-experiment --json loop/inbox/experiment.json` inside CMD-NEXT step 3 with the operator's yes, and are paused until two weeks of organic reads (next SKILL:28). Loop state changes only through loop.py (AGENTS.md), so this needs a new loop.py subcommand or a UI-side intent that CMD-NEXT reads. "about 8 Oct" is computed from the first daily read (24 Sep) + 14 days (DATA-CX02) and must be derived, not static
states: real: queued / cannot queue (an experiment is open) / un-queue
mock-only: one-way; only the first row can be queued; label date static
a11y: after click the button becomes disabled while focused, so keyboard focus sits on a disabled control (may be dropped by the browser); no announcement of "Queued"
```

**Not controls:** `pipeline`, `weights`, `guardrails`, `nextExperiments`, `questions`, the example lesson (see §7). Weights aren't stored anywhere (review C8): a structured weights file is needed before this list can be real.

---
### 4. Sheets

**Containers.** iPhone: every sheet is `sheet()` (build_body.py:627-635): an absolute full-screen layer with a `--scrim` backdrop (`div onClick=<close> aria-hidden="true"`) and a bottom sheet `role=dialog aria-modal=true aria-label=<label> onKeyDown=sheetKey class=te-sheet-in`, radius 26px top, `max-height: 90%` (chat `height: 88%`), grab handle HANDLE (aria-hidden, build_body.py:637). Mac (build_mac.py): Source/Editor/Hook are centred `modal()` dialogs (122-130; widths 540/640/560, max-height 820, handle removed); chat off Cortex is MAC-DRAWER (132-139); Settings is MAC-POPOVER (141-146); chat on Cortex is MAC-DOCK (82-84). DOM order after `<main>`: iPhone NAV, PILL, SOURCE, EDITOR, CHAT, SETTINGS, HOOK (build_body.py:756-778); Mac SIDEBAR precedes main, then Source, Editor, Hook, DRAWER, POPOVER (build_mac.py:150-166). Later in DOM = painted on top.

```yaml
id: CTL-SHEET-SCRIM
label: none (aria-hidden div; pointer only). Not in controls.json
where: Main.dc.html:625 (Source), 644 (Editor), 665 (Chat), 695 (Settings), 737 (Hook); Mac.dc.html:675 (Source), 694 (Editor), 715 (Hook), 734 (Drawer), 763 (Popover, transparent, no --scrim)
binding: onClick = closeSource | closeEditor (= closeEditorKeep: keeps unsaved edits, draftPending) | closeChat | closeSettings | closeHook
shown when: with its sheet
enabled when: always
purpose: tap outside to dismiss (HIG sheets); review 25 Sep #24, #26
real wiring: LOCAL
states: –
mock-only: –
a11y: correctly hidden from AT; Escape and the visible Done/Cancel are the keyboard paths. The Mac popover scrim covers the whole window, so a pointer click on the sidebar profile button while Settings is open hits the scrim (closeSettings), not toggleSettings
```

### 4.1 SHT-SOURCE ("Source")

**Purpose.** The receipt behind one PAID → FREE swap, one tap from the card (D16 "Each swap's source is one tap away", D36 vendor currency, truth budget). Opened by CTL-POST-SWAP-SOURCE (part 1): `openSheet({source: swapIdx}, 'Source')` (main_script.js:401).

**Content in order** (Main:626-638 · Mac:676-688; build_body.py SOURCE_INNER:639-650): "SOURCE · SWAP {src.n} OF 3" + "CHECKED 24 SEP" (static); h2 "{src.paid} → {src.free}"; PAID SIDE `src.paidFact` + `src.paidSrc`; FREE SIDE · THE VENDOR'S OWN WORDS `src.quote` + `src.freeSrc`; IF SOMEONE PUSHES BACK `src.limit`; Done. `src` = SWAPS[s.source] (main_script.js:2-15, 464, 569). Real source: the draft's `CLAIMS.md` rows and their check date (DATA-P05, DATA-P06). Source domains are plain text, not links (G54).

```yaml
id: CTL-SOURCE-DONE
label: "Done"
where: Main.dc.html:637 (cj 629), Mac.dc.html:687 (cj 679)
binding: onClick=closeSource (main_script.js:570) → s.source=null; restoreFocus() (the swap line that opened it)
shown when: hasSource = s.source !== null && s.source >= 0 (569)
enabled when: always
purpose: D16
real wiring: LOCAL
states: –
mock-only: –
a11y: it's the only button, so openSheet focuses it on open (267); Escape closes (closeTop step 3)
```

### 4.2 SHT-EDITOR ("Change something")

**Purpose.** Free edits to the card before approval plus a one-line take, with the X character count; editing an approved post clears the approval (D26, D15; review 25 Sep #1, #24, #26). Opened by CTL-POST-CHANGE / CTL-POST-EDIT (part 1): `openEditor` (main_script.js:546-550) → `openSheet({editorOpen:true, source:null, [draftText:cardBase, takeText:cardTake unless draftPending]}, 'Change something')`; focus lands on the textarea.

**Content in order** (Main:645-660 · Mac:695-710; build_body.py EDITOR_INNER:653-666): h2 + Cancel; "Your unsaved changes are still here." + Discard them (when draftPending); amber "Saving clears the approval. You'll read and approve again." (when editClearsApproval = stage 3, 545); label "Card 1" + textarea; "{draftCount} characters as X counts · your limit 600" (draftCountColor amber > 600, 557; part 1 G36); note "This format has a fixed header, so there's no hook to choose. Other formats offer two or three hooks here."; label + take input; "Every claim still goes through the fact-check, and the final check still applies."; Save changes.

```yaml
id: CTL-EDITOR-CANCEL
label: "Cancel"
where: Main.dc.html:648 (cj 640), Mac.dc.html:698 (cj 690)
binding: onClick=cancelEdit (main_script.js:552) → editorOpen=false, draftPending=false; restoreFocus(). Unsaved text is discarded on next open (openEditor re-seeds because draftPending is false)
shown when: editorOpen
enabled when: always
purpose: review 25 Sep #26 ("Cancel discards"; Escape and the scrim keep)
real wiring: LOCAL
states: –
mock-only: –
a11y: Escape does NOT do what Cancel does (Escape = keep, closeEditorKeep 286-290). Intended (#26), but the difference is invisible; the "still here" note on reopen explains it
```

```yaml
id: CTL-EDITOR-DISCARD
label: "Discard them" (after "Your unsaved changes are still here.")
where: Main.dc.html:649 (cj 641), Mac.dc.html:699 (cj 691)
binding: onClick=discardDraft (main_script.js:554) → draftText=cardBase, takeText=cardTake, draftPending=false. Sheet stays open
shown when: draftPending && editorOpen (553)
enabled when: always
purpose: review 25 Sep #26
real wiring: LOCAL (unsaved draft text is device-local; if the real app keeps it, keep it per draft folder and per device)
states: –
mock-only: –
a11y: the button unmounts on click → focus lost; move focus to the textarea
```

```yaml
id: CTL-EDITOR-CARD
label: <label for="te-card">"Card 1"</label>; textarea#te-card rows=12
where: Main.dc.html:652 (cj 644), Mac.dc.html:702 (cj 694)
binding: value=draftText; onChange=setDraftText (main_script.js:555) → s.draftText. draftCount = xLength(draftText + (take ? '\n\n'+take : '')) (405)
shown when: editorOpen
enabled when: always
purpose: D26 (edit freely before approval), D16 (count as X counts)
real wiring: on Save, NO-CMD: write the edited text to the card file `drafts/<folder>/01-hook.md` (the card files are the posts; AGENTS.md layout). Only card 1 is editable here; the shout-out card 02 is not (part 1 G14). If APPROVED exists, the file change alone makes the digest stale (post_thread.approval_refusal), so the stage falls back to "Needs your approval" without touching APPROVED (agents may never edit it). New or changed claims need CMD-VERIFY (claims mode) before approval; the mock only promises it in the note (G55). The edit is a preference signal (D26) with no store (part 1 G13)
states: real: save failed (file write), fact-check pending/failed for new claims, refusals preview: run the real gate logic (`post_thread.py` card_refusals), never a UI port like the mock's gateRefusals (198-219), which can drift (BQ-C6)
mock-only: edits live in memory
a11y: labelled; the count line isn't tied to the field (aria-describedby would announce it) and isn't live
```

```yaml
id: CTL-EDITOR-TAKE
label: "Your take, in one line (optional, added under the list)"; placeholder "I moved my own collections to Bruno last month"
where: Main.dc.html:656 (cj 648), Mac.dc.html:706 (cj 698)
binding: value=takeText; onChange=setTakeText (main_script.js:556). On save it is trimmed and kept separate as s.cardTake, rendered under card 1 after a blank line (310, 563)
shown when: editorOpen
enabled when: always
purpose: D26 ("a 'my take' line that goes into the card"); voice "What every post delivers" (the operator's own verdict)
real wiring: as CTL-EDITOR-CARD (becomes part of 01-hook.md). The take is a first-hand claim by the operator: truth budget says the operator is a valid source, so no fact-check, but it counts toward the 600 cap
states: as the card
mock-only: –
a11y: labelled
```

```yaml
id: CTL-EDITOR-SAVE
label: "Save changes"
where: Main.dc.html:658 (cj 650), Mac.dc.html:708 (cj 700)
binding: onClick=saveEdit (main_script.js:558-567): cardBase=draftText, cardTake=trim(take), editorOpen=false, draftPending=false; if the text changed and stage was 3 → stage=2, editedAfter=true, approvedAt='', approvedText=''; savedNote=changed. restoreFocus()
shown when: editorOpen
enabled when: always (even with no change, or over 600)
purpose: D26, D15; review 25 Sep #1
real wiring: NO-CMD (write card file; see CTL-EDITOR-CARD) + preference record. Should refuse or warn on a gate refusal before saving? The mock saves anything; the gate refuses at Start posting (CMD-READY)
states: real: saving / saved / failed
mock-only: –
a11y: focus returns to the opener
```

### 4.3 SHT-CHAT ("Ask Cortex") — iPhone sheet, MAC-DRAWER, MAC-DOCK

**Purpose.** Talk to the AI about why the engine is set as it is, what to test, a post, the results or a waiting reply. It answers and suggests; it never writes a reply and never changes anything (D9, D14, D31; footer "Cortex answers and suggests. Every change is a button you press yourself.").

**Three hosts, one inner block** (`CHAT_INNER`, build_body.py:669-691):
- iPhone sheet `chatOpen` (Main:663-692), `height: 88%`, purple gradient background (`--sheet-top` → `--sheet-mid` → `--paper`), header orb + h2 "Cortex" + "Claude" + Done.
- MAC-DRAWER `showDrawer` = Mac && chatOpen && screen≠cortex (main_script.js:472; Mac:732-761; build_mac.py:132-139): right-hand drawer 440px, full height, scrim, same header with Done.
- MAC-DOCK on the Cortex page (Mac:645-669; build_mac.py:82-84): `<aside aria-label="Ask Cortex">`, 400px, sticky, 820px; no Done and no handle; not a dialog, not modal, never closes.

**Content in order:** header; `role=log aria-live=polite aria-label="Conversation"` with `chat` messages (user right, bot with orb) and, while `asking`, `<dc-import Thinking cmd="ask" on-done=doneAsk>` (Main:679 · Mac:658 dock · Mac:748 drawer); context chip "About: {contextLabel}" with × (when hasContext); suggestion chips `suggestions`; the glowing input (`te-glow` + `te-glass`) with Send; footer line.

**State.** `s.chat` (seed CHAT_SEED, 138; DATA-CX09), `s.asking` (the suggestion object being answered), `s.context ∈ null|'post'|'results'|'reply'|'proposal'`, `s.typed`. Suggestions: `ctxSet[context] || SUGGESTIONS` (430, 661) — 'proposal' maps to the general SUGGESTIONS set, not a proposal set (G56). contextLabel: post "the next post", results "this week's results", reply "a reply waiting for you", proposal "the proposed build log" (431). Answers: `finishAsk` (278) appends `asking.a` or FALLBACK (137). The chat history persists across opens and screens (one conversation for all contexts).

**Openers** (all call `askCortex(context)`, 279-285; none use openSheet): CTL-NAVPHONE-PILL (null), CTL-REPLIES-ASK ('reply'), CTL-RESULTS-ASK ('results'), CTL-POST-ASK ('post', part 1), CTL-TODAY-PROPOSAL-ASK ('proposal', part 1), ⌘K on Mac (null, §6.4).

```yaml
id: CTL-CHAT-DONE
label: "Done"
where: Main.dc.html:669 (cj 661) iPhone sheet; Mac.dc.html:738 (cj 730) drawer. Dock: none
binding: onClick=closeChat (main_script.js:657) → chatOpen=false, plus finishAsk if an answer is in flight (so the answer is appended, review 25 Sep #17); restoreFocus()
shown when: chatOpen (iPhone) / showDrawer (Mac)
enabled when: always
purpose: D9, D14
real wiring: LOCAL. Real: closing must not cancel a server-side answer; the answer arrives into history. The mock fakes that by writing the canned answer instantly
states: –
mock-only: finishAsk on close
a11y: restoreFocus fails when the opener was the iPhone pill: the pill unmounts while chat is open (showPill needs !chatOpen, 655), so returnFocus is disconnected and focus is lost (G57)
```

```yaml
id: CTL-CHAT-CLEAR-CONTEXT
label: aria-label "Stop asking about this" (× icon), after "About: {contextLabel}"
where: Main.dc.html:683 (cj 675); Mac.dc.html:662 (cj 654) dock; Mac.dc.html:752 (cj 744) drawer
binding: onClick=clearContext (main_script.js:662) → context=null; the chip disappears and suggestions revert to SUGGESTIONS
shown when: hasContext = !!s.context
enabled when: always
purpose: D14 ("opens the same chat with an 'About: …' chip")
real wiring: LOCAL (drops the context object from the next request)
states: –
mock-only: –
a11y: the button unmounts on click → focus lost; move focus to the input
```

```yaml
id: CTL-CHAT-SUGGESTION
label: sg.q, e.g. "Why cap the first post at 600?" (3 in general; 2 per context)
where: Main.dc.html:685 (cj 677); Mac.dc.html:664 (cj 656) dock; Mac.dc.html:754 (cj 746) drawer; <sc-for suggestions as sg>
binding: onClick=sg.ask → askQ(sg) (main_script.js:423-427, 661): ignored if asking; appends {role:'user', text:q}; asking=sg; typed=''. The ask working line runs 3 steps (5 s) then doneAsk (660) appends the canned answer. disabled={{asking}}
shown when: always in the chat
enabled when: !asking
purpose: D9, D14 (recall-free questions)
real wiring: CORTEX-CHAT. Suggestions should be generated from the context by code or curated, never as buttons that act: "buttons never model-written" — a suggestion only sends a question; the model's answer may never render as a control (D14 footer; GUARDRAILS)
states: real: answering (working line with real steps), answer, error ("Couldn't reach the model. Nothing was changed." + Try again), model unavailable / usage limit (operator note in BQ-Q11: limits hit twice this week)
mock-only: canned Q&A (SUGGESTIONS*, 120-136)
a11y: disabled while answering, so focus on a pressed chip is kept but inert; the answer is announced via role=log
```

```yaml
id: CTL-CHAT-INPUT
label: aria-label "Ask Cortex"; placeholder "Ask Cortex…"; enterkeyhint=send
where: Main.dc.html:687 (cj 679); Mac.dc.html:666 (cj 658) dock; Mac.dc.html:756 (cj 748) drawer
binding: value=typed; onChange=setTyped (663); onKeyDown=typedKey (664): Enter without Shift and not composing → preventDefault, sendText(e.target.value). sendText (429): trims; empty → nothing; exact case-insensitive match against ALL_Q (all four suggestion sets) → canned answer, else FALLBACK "In the real app I'd answer from your posts, weights and the X ranking notes. This mock only knows the suggested questions."
shown when: always in the chat
enabled when: always (not disabled while asking; a send while asking is silently ignored and the text stays, askQ 425)
purpose: D9 (the glowing field, "like Apple's Siri field"), D14 (glow only here)
real wiring: CORTEX-CHAT (§4.3.1)
states: as CTL-CHAT-SUGGESTION; plus "still answering, wait" feedback when sending mid-answer
mock-only: canned matching
a11y: labelled; askCortex focuses the last shown input with this label (284) — on the Mac Cortex page with the drawer closed that's the dock input
```

```yaml
id: CTL-CHAT-SEND
label: aria-label "Send" (arrow icon)
where: Main.dc.html:687 (cj 679, second control); Mac.dc.html:666 (cj 658) dock; Mac.dc.html:756 (cj 748) drawer
binding: onClick=sendTyped (663) → sendText(s.typed)
shown when: always in the chat
enabled when: always
purpose: D9
real wiring: CORTEX-CHAT
states: as input
mock-only: –
a11y: labelled; 44px circle
```

#### 4.3.1 CORTEX-CHAT: what the real backend must be

- **Model.** Settings shows "Model · Claude" (SETTINGS, main_script.js:151-153) and the chat header "Claude" (Main:669, Mac:648, Mac:738). D9: "whichever the operator has set up". Options in BQ-Q11. No control changes it in the mock (G58).
- **May read (own data):** `ledger/SUMMARY.md`, `ledger/<id>.json`, `ledger/activity/*`, `reviews/week-*.md`, `learnings.md`, `experiments.md`, `loop.py status` output, the Weights source (a structured file once it exists, review C8), `reference/x-algorithm.md` (answers cite fact ids like A9), `reference/audience.md`, `voice/exit-zero.md`, the current draft folder (cards, `CLAIMS.md`, `REPLIES.md`) for context 'post', the stored `/next` proposal for 'proposal'.
- **May read (third-party, untrusted):** for context 'reply', the one mention's text. Treat it as data: quote it inside a delimited block, never follow instructions in it, keep it out of logs and anything committed (review C10; data.md §5; BQ-T2).
- **Never:** write or draft a reply for pasting ("On a reply, Cortex discusses the point but never writes it (A12)", D14; SUGGESTIONS_REPLY answer text at 134 states it); call any command; create, edit or delete `APPROVED`; change loop state, skills, voice or queue; post to X. Its tool surface should be read-only (BQ-Q11 option 2). Any output that looks like a ready-to-paste reply should be refused by instruction and, ideally, checked.
- **Buttons are never model-written.** Every action the chat talks about (Apply, Queue, Approve) is an existing app button the operator presses; the chat may point to it, not render it. Suggestion chips are code-defined.
- **Truth budget.** Figures in answers must come from the files above (voice "Truth budget"); an answer with no source says so.
- **Cost/limits.** Model usage limits are a live problem (BQ-Q11 operator note); show "Cortex is at its usage limit until HH:MM" rather than a generic failure.

### 4.4 SHT-SETTINGS ("Settings and health") — iPhone sheet, MAC-POPOVER

**Purpose.** Health of the daily check and X API, spend, notifications, the Cortex model and appearance (D8, D21, D23, D35).

**Content in order** (iPhone Main:693-734, build_body.py SETTINGS_INNER:702-733; Mac popover Mac:762-798, build_mac.py:141-146 — theme toggle removed (it's in the sidebar), "Match iPhone" → "Match Mac"): header (EZ avatar aria-hidden, h2 "Exit Zero Code", "@exitzerocode · 36 followers" DATA-SET08, iPhone theme toggle, Done); `settingsGroups` sections Health (5 value rows with status dots: Daily check, Still too new to measure, X API, X API spend, Ranking notes; DATA-SET01–05), Notifications (2 switches; DATA-SET06), Cortex (Model "Claude"; DATA-SET07); Appearance radiogroup; "Run the daily check now" when healthBad.

```yaml
id: CTL-SETTINGS-THEME-FLIP
label: icon only; aria-label/title = flipLabel "Switch to dark mode" | "Switch to light mode"; moon when resolved light, sun when dark (showMoon/showSun, 478; te-swap rotate-in)
where: Main.dc.html:702 (cj 694) in the iPhone sheet header. Mac: the same THEME_TOGGLE sits in the sidebar instead (CTL-NAVMAC-THEME)
binding: onClick=flipTheme (main_script.js:480) → s.theme = resolved==='dark' ? 'light' : 'dark'. resolved = theme, or the OS preference when 'system' (434-437). themeAttr → data-theme on .te-root (477)
shown when: settingsOpen (iPhone)
enabled when: always
purpose: D23 (two-state toggle showing what you'd switch to; iPhone: top row of the profile sheet), D21
real wiring: SETTINGS-STORE (D23: "Your choice is kept even if the device changes later" = an explicit choice persists and stops following the OS). LOCAL until then
states: –
mock-only: s.theme in memory; the canvas prop `theme` seeds it (434)
a11y: it's the first button in the dialog, so openSheet focuses it on open (267) rather than Done (G59)
```

```yaml
id: CTL-SETTINGS-DONE
label: "Done"
where: Main.dc.html:706 (cj 698), Mac.dc.html:771 (cj 763)
binding: onClick=closeSettings (main_script.js:667) → settingsOpen=false; restoreFocus()
shown when: settingsOpen
enabled when: always
purpose: D8
real wiring: LOCAL
states: –
mock-only: –
a11y: on Mac it's the first button, so it takes focus on open
```

```yaml
id: CTL-SETTINGS-NOTIFY-SWITCH
label: role=switch, aria-label=row.name: "Before a post" ("A reminder 10 minutes before the planned time") | "Shout-out window" ("A nudge when it opens, if you left the app")
where: Main.dc.html:716 (cj 708), Mac.dc.html:781 (cj 773); <sc-for settingsGroups as sgp><sc-for sgp.rows as row><sc-if row.isToggle>
binding: onClick=row.flip (main_script.js:671) → s[remind|nudge] = !value. aria-checked=row.on ('true'|'false'); knob/track styles (672). Value "On"/"Off" (670) isn't rendered for toggles (only notToggle rows show row.value)
shown when: settingsOpen
enabled when: always
purpose: D35 (both off until switched on; "Remind me" on Today switches the first: the same s.remind, part 1 CTL-TODAY-PRIMARY)
real wiring: SETTINGS-STORE + push. Needs a poller and push (review C4; BQ-Q6). "Before a post" fires at post_at − 10 min; "Shout-out window" fires at posting time + 10 min only if the app is in the background. On iPhone web push needs a home-screen app and permission: turning a switch on must request permission and show "Notifications are off for this app in iOS Settings" when denied
states: real: on / off / permission denied / push unavailable (Mac unreachable)
mock-only: in-memory; part 1 G9 (nudge "sent" shows with nothing sent)
a11y: role=switch with name; the sub-line isn't associated (aria-describedby)
```

```yaml
id: CTL-SETTINGS-APPEARANCE
label: role=radio "Light" | "Dark" | "Match iPhone" (Mac: "Match Mac"); group aria-label "Appearance"
where: Main.dc.html:725/726/727 (cj 717/718/719), Mac.dc.html:790/791/792 (cj 782/783/784)
binding: onClick=thIsLightGo|thIsDarkGo|thIsSystemGo (main_script.js:676-677) → s.theme='light'|'dark'|'system'. aria-checked=thIsLight/thIsDark/thIsSystem; styles thIs*Bg/Border/Weight
shown when: settingsOpen
enabled when: always
purpose: D21 ("Settings has Light, Dark and 'Match iPhone / Mac'"), D23 (full choice stays in Settings)
real wiring: SETTINGS-STORE
states: –
mock-only: in memory
a11y: no roving tabindex or arrow keys: seg() computes thIs*Ti (439) but the template doesn't use it (part 1 G31 class of issue)
```

```yaml
id: CTL-SETTINGS-RUN-HEALTH
label: "Run the daily check now"
where: Main.dc.html:730 (cj 722), Mac.dc.html:795 (cj 787)
binding: onClick=fixHealth (main_script.js:490) → healthFixed=true, settingsOpen=false (no restoreFocus)
shown when: healthBad = props.health==='failed' && !s.healthFixed (440)
enabled when: always
purpose: D8, D20
real wiring: CMD-SNAPSHOT (same as CTL-TODAY-RUN-HEALTH, part 1). Beware the UTC-day double charge (review C7) and a run while the Mac is asleep/unreachable (review C1)
states: mock: instant success. Real: running (working line cmd `sync`-kind steps), ok (health rows refresh from runs.log), failed with cause (Keychain locked, credits exhausted, network, Mac unreachable)
mock-only: instant; the Health rows don't change with healthBad (they always say "Ran 20:00 last night", "Last read worked") (G60)
a11y: closes the sheet without restoreFocus → focus lost (part 1 G32)
```

### 4.5 SHT-HOOK ("Choose a hook")

**Purpose.** Pick one of 2–3 openings and add a take; the pick is a preference signal (D26; review 25 Sep E4: shown on an example tool-verdict draft in Posts). Opened by CTL-POSTS-CHOOSE-HOOK / CTL-POSTS-CHANGE-HOOK (part 1): `openSheet({hookOpen:true}, 'Choose a hook', '[role=radio][aria-checked="true"]')` (609) — focus lands on the selected hook.

**Content in order** (Main:738-751 · Mac:716-729; build_body.py HOOK_INNER:736-747): h2 + Cancel; "Strangers see the opening first. Pick the one that sounds like you; the rest of the card stays as drafted." + `example` chip; radiogroup "Hooks" (`hooks`: text, "{count} characters as X counts"); take input; "Your pick is recorded as a preference, so the loop can learn which openings you choose."; Use this hook.

```yaml
id: CTL-HOOK-CANCEL
label: "Cancel"
where: Main.dc.html:741 (cj 733), Mac.dc.html:719 (cj 711)
binding: onClick=closeHook (main_script.js:610) → hookOpen=false; restoreFocus(). Does NOT revert hookPick or hookTake
shown when: hookOpen
enabled when: always
purpose: D26
real wiring: LOCAL
states: –
mock-only: a pick changed then cancelled stays selected in state (hookChosen shows it only after hookSaved) (G61)
a11y: fine
```

```yaml
id: CTL-HOOK-OPTION
label: role=radio, name = "{hk.text} {hk.count} characters as X counts", e.g. "Codex and Claude disagreed on a fix. Grok broke the tie. 56 characters as X counts"
where: Main.dc.html:744 (cj 736), Mac.dc.html:722 (cj 714); <sc-for hooks as hk>; group role=radiogroup aria-label="Hooks" (Main:743, Mac:721)
binding: onClick=hk.pick (main_script.js:613) → s.hookPick=i. aria-checked=hk.on; border/bg blue when chosen (612-613). count = xLength(text)
shown when: hookOpen
enabled when: always
purpose: D26 (choice of 2–3 hooks), D16 (count as X counts)
real wiring: NO-CMD. Hook options must come from the draft (no format skill writes them yet; part 1 G12). The choice becomes the first line of 01-hook.md (a card edit → re-approval rules as CTL-EDITOR-SAVE) and a preference record
states: real: no options (format has a fixed header, e.g. tool-swap; the editor note says so)
mock-only: HOOKS constant (155-159), tagged example
a11y: no roving tabindex/arrow keys (part 1 G31 class)
```

```yaml
id: CTL-HOOK-TAKE
label: "Your take, in one line (optional)"; placeholder "Two reviewers beat one, when they disagree for a reason"
where: Main.dc.html:747 (cj 739), Mac.dc.html:725 (cj 717)
binding: value=hookTake; onChange=setHookTake (main_script.js:614)
shown when: hookOpen
enabled when: always
purpose: D26
real wiring: NO-CMD, into the card as CTL-EDITOR-TAKE. The mock never shows the saved take anywhere (G61)
states: –
mock-only: –
a11y: labelled
```

```yaml
id: CTL-HOOK-SAVE
label: "Use this hook"
where: Main.dc.html:749 (cj 741), Mac.dc.html:727 (cj 719)
binding: onClick=saveHook (main_script.js:615) → hookOpen=false, hookSaved=true; restoreFocus(). Posts then shows hookChosen (part 1)
shown when: hookOpen
enabled when: always
purpose: D26
real wiring: NO-CMD (card write + preference store)
states: real: saved / failed
mock-only: –
a11y: on the first save, restoreFocus fails: the opener "Choose a hook" (Main:308, under hookNotSaved) unmounts and "Change the hook" (Main:309, under hookSaved) is a new element, so the stored returnFocus is disconnected and focus is lost (G57). Later saves (opened from Change) restore correctly
```

---
### 5. Navigation and Mac containers

### 5.1 NAV-PHONE (tab bar, badge, Cortex pill)

**Purpose.** Five tabs Today · Posts · Replies · Results · Cortex (D5, D6, D11; D8 keeps Settings out of the tab bar), a count badge on Replies only when someone is waiting (D12), and on Cortex only the glowing "Ask Cortex…" pill (D9, D14).

**Structure** (Main:611-622; build_body.py NAV:620-625, tab():613-615, BADGE:618, PILL:750-754): `<nav aria-label="Sections" inert={{navInert}}>` after `<main>`, 80px, 5-column grid; each tab = icon (aria-hidden) + 12px label, colour `tab<K>` (ink when current, faint otherwise), weight `tab<K>Weight`, `aria-current=tab<K>Current` ('page'|'false'), `aria-label=tab<K>Label` (main_script.js:444-451). Current: Today for today/post/ready; Posts for posts/capture (445-447). The pill is absolutely positioned `left/right 20px, bottom 94px`, outside `<main>` and `<nav>`, with `.te-glow` (animated gradient border, 2 iterations of 6 s; none under reduced motion) and `.te-glass` (backdrop blur).

```yaml
id: CTL-NAVPHONE-TAB
label: "Today" | "Posts" | "Replies" | "Results" | "Cortex". aria-label = tabTodayLabel … ; Replies = "Replies, N waiting" when N>0 (449). Replies badge: {{waitingCount}} aria-hidden, amber (--amber-fill / --on-amber), top-right of the icon, only when hasWaiting
where: Main.dc.html:612/613/614/615/616 (cj 604/605/606/607/608)
binding: onClick=goToday|goPosts|goReplies|goResults = go(screen) (484, 308): screen, prevScreen, source=null, chatOpen=false. goCortex (484) = setState({screen:'cortex', context:null}) only (no prevScreen, no chatOpen/source reset)
shown when: always (iPhone)
enabled when: always; unreachable while any sheet is open (nav inert)
purpose: D5 (Today home), D6/D11 (Cortex as fifth tab), D8, D12 (badge only when waiting)
real wiring: LOCAL router. Badge count = REPLIES-READ unanswered substantive mentions (greetings excluded, D12); it must not cost a read on every render — use the cached result, refresh on open of Replies/Today (BQ-Q10)
states: badge hidden at 0 (review 25 Sep §8: "counting 3 → 1 → hidden")
mock-only: waitingCount counts the WAITING constant minus dismissed
a11y: aria-current=page marks the tab; badge count is in the accessible name. Tab change doesn't reset <main>'s scroll or move focus/announce the new page (G62). The five buttons are a nav landmark, not role=tablist (correct for page navigation)
```

```yaml
id: CTL-NAVPHONE-PILL
label: "Ask Cortex…" (orb aria-hidden); no aria-label
where: Main.dc.html:620 (cj 612)
binding: onClick=openChat → askCortex(null) (656, 279-285): returnFocus=pill; chatOpen=true, context=null; focuses the chat input
shown when: showPill = DEVICE==='phone' && screen==='cortex' && !chatOpen (655)
enabled when: always
purpose: D9 (floating glowing field that opens a sheet), D14 (glow only on the Cortex tab)
real wiring: LOCAL (opens SHT-CHAT)
states: –
mock-only: –
a11y: looks like a text field but is a button (name "Ask Cortex…" is fine; role button is honest). It sits outside main/nav so it is NOT inert while Settings is open on Cortex (G53). It unmounts while the chat is open, so focus can't return to it on close (G57). It overlaps the bottom of <main> content: Cortex main has `padding-bottom: 84px` to clear it (build_body.py:546; removed on Mac, build_mac.py:77)
```

### 5.2 NAV-MAC (sidebar, status card, profile button, theme toggle, ⌘K hint)

**Structure** (Mac:36-61; build_mac.py SIDEBAR:98-120, nav():88-91, BADGE:94, KBD:96): `<aside>` 248px (no landmark label): title "Thread Engine" + "@exitzerocode"; `<nav aria-label="Sections" inert={{navInert}}>` with five rows (icon + label; current row: `nav<K>Bg` = --line2 fill and `nav<K>Bar` = 3px ink bar, weight 600); Replies row ends with an amber count badge (aria-hidden); Cortex row ends with "⌘K" (aria-hidden, title "Ask Cortex from any page"). Status card (not controls): health dot + `sideHealth` ("Daily check ran 20:00" | "Daily check missed last night", 475), Followers 36, Verified followers "27 of 500" + a 5.4% bar, "Export due Thu 1 Oct" — all static except the health line (DATA-T03, T10, T16, T18 in data.md; D8 "below the status card"). Bottom row: profile button + theme toggle (D8, D23), **outside the `<nav>`, so never inert**.

```yaml
id: CTL-NAVMAC-TAB
label: "Today" | "Posts" | "Replies" (+ badge) | "Results" | "Cortex" (+ "⌘K" hint). aria-label = tab<K>Label (the ⌘K text is not part of the name)
where: Mac.dc.html:39/40/41/42/43 (cj 31/32/33/34/35)
binding: as CTL-NAVPHONE-TAB (goToday … goCortex). Mac goToday etc. land on the two-column Today (isHome, 471)
shown when: always (Mac)
enabled when: always; unreachable while a modal, the drawer or the popover is open (navInert)
purpose: D1, D5, D6, D12; D14 (⌘K hint)
real wiring: LOCAL router; badge as the iPhone
states: as iPhone
mock-only: –
a11y: add aria-keyshortcuts="Meta+K" to the Cortex row (or document ⌘K elsewhere) since the hint is aria-hidden and outside the name. Same scroll/announce issue as iPhone (G62)
```

```yaml
id: CTL-NAVMAC-PROFILE
label: "EZ" avatar (amber dot aria-hidden when healthBad) + "Exit Zero Code" / "Settings and health"; aria-label = avatarLabel; aria-expanded = settingsOpen
where: Mac.dc.html:52 (cj 44)
binding: onClick=toggleSettings (main_script.js:473): if open → settingsOpen=false + restoreFocus(); else openSheet({settingsOpen:true}, 'Settings and health'). Background profileBg = --line2 while open (474)
shown when: always (Mac)
enabled when: always (not inert: outside <nav>)
purpose: D8 (Mac: bottom of the sidebar, below the status card; amber dot on failure)
real wiring: LOCAL (opens MAC-POPOVER)
states: normal / needs-you
mock-only: –
a11y: disclosure pattern (aria-expanded) on a control that opens an aria-modal dialog; pick one model: a non-modal popover (then drop aria-modal and inert) or a modal dialog (then drop aria-expanded) (G63). The 36px avatar is inside a 165×52 hit area (review 25 Sep §7)
```

```yaml
id: CTL-NAVMAC-THEME
label: icon only; aria-label/title = flipLabel ("Switch to dark mode" | "Switch to light mode")
where: Mac.dc.html:56 (cj 48)
binding: onClick=flipTheme (main_script.js:480); as CTL-SETTINGS-THEME-FLIP
shown when: always (Mac)
enabled when: always (outside <nav>, never inert — reachable by Tab while any Mac dialog is open)
purpose: D23 (Mac: beside the profile button at the bottom of the sidebar)
real wiring: SETTINGS-STORE
states: –
mock-only: –
a11y: 44px circle with name; not inert while a modal is open (G53)
```

### 5.3 MAC-DRAWER, MAC-DOCK, MAC-POPOVER

| Container | Shown when | Markup | Modal? | Closes by |
|---|---|---|---|---|
| MAC-DRAWER | `showDrawer` = Mac && chatOpen && screen≠'cortex' (main_script.js:472) | Mac:732-761; right-hand 440px full-height dialog "Ask Cortex" with scrim and purple gradient (build_mac.py:132-139) | yes: aria-modal, main+nav inert (468) | Done, scrim, Escape (closeTop step 4) |
| MAC-DOCK | `isCortex` on Mac | Mac:645-669; `<aside aria-label="Ask Cortex">` in the Cortex grid (build_mac.py:79-86) | no; never inert (it's inside <main>, and inertOn excludes chat on Cortex, 468) | never; Escape does nothing (closeTop skips chat on Mac Cortex, 296) |
| MAC-POPOVER | `settingsOpen` on Mac | Mac:762-798; 400px dialog pinned `left:16, bottom:80` above the profile button; transparent full-window scrim (build_mac.py:141-146) | aria-modal, main+nav inert; profile button and theme toggle stay live | Done, scrim, Escape (closeTop step 5), CTL-NAVMAC-PROFILE toggle |

On Mac, Source/Editor/Hook are centred `modal()` dialogs (build_mac.py:122-130, 161-163) with the same controls as the iPhone sheets (§4). The ⌘K route into the drawer/dock is §6.4.

---

### 6. Focus and modality

### 6.1 Layers

A layer is open when its state flag is set. `inertOn` (main_script.js:468) = Mac ? (chatOpen && screen≠cortex) : chatOpen, OR settingsOpen OR editorOpen OR source≠null OR hookOpen. Then `mainInert = navInert = 'true'` (477), else `null` (attribute omitted): `<main inert>` (Main:36, Mac:62) and `<nav inert>` (Main:611, Mac:38).

| Layer | Flag | iPhone container | Mac container | Opened by | Initial focus |
|---|---|---|---|---|---|
| Source | `s.source` (≥0) | sheet Main:623-641 | modal Mac:673-691 | openSheet (401) | first `textarea, input` else first enabled `button, a[href]` → **Done** |
| Editor | `editorOpen` | sheet Main:642-662 | modal Mac:692-712 | openSheet (549) | **textarea#te-card** |
| Chat | `chatOpen` | sheet Main:663-692 | drawer Mac:732-761 (dock when on Cortex) | askCortex (279-285), not openSheet | last shown `input[aria-label="Ask Cortex"]` (284) |
| Settings | `settingsOpen` | sheet Main:693-734 | popover Mac:762-798 | openSheet (666; Mac toggleSettings 473) | iPhone: **theme flip** (first button); Mac: **Done** |
| Hook | `hookOpen` | sheet Main:735-753 | modal Mac:713-731 | openSheet (609) with `first='[role=radio][aria-checked="true"]'` | **selected hook radio** |

`openSheet(patch, label, first)` (261-270): stores `this.returnFocus = document.activeElement`, sets state, then after 60 ms (`later`, 257) finds the *visible* dialog `.te-root [role=dialog][aria-label="<label>"]` (`shown()`, 259: offsetParent or position fixed) and focuses as above.

### 6.2 closeTop() order and Escape per layer

`closeTop()` (291-299) closes exactly one layer, first match wins:
1. **Hook** → hookOpen=false; restoreFocus.
2. **Editor** → `closeEditorKeep()` (286-290): editorOpen=false, draftPending = (draftText≠cardBase || takeText≠cardTake); restoreFocus. (Keeps unsaved edits; reopen shows "Your unsaved changes are still here.")
3. **Source** → source=null; restoreFocus.
4. **Chat**, unless Mac on Cortex → chatOpen=false, plus finishAsk if answering; restoreFocus.
5. **Settings** → settingsOpen=false; restoreFocus.
Returns false if nothing closed.

Escape paths:
- **Inside a dialog**: `sheetKey` (571) on every `role=dialog` (Main:626, 645, 666, 696, 738; Mac:676, 695, 716, 735, 764): on Escape → `stopPropagation()`, `preventDefault()`, `closeTop()`. Note: it closes the top of closeTop's order, not necessarily the dialog that had focus (matters only when layers stack; §6.4).
- **Anywhere else in the mock**: `rootKey` (476) on `.te-root` (Main:34, Mac:34) → `globalKey` (300-303): Escape → `closeTop()`; preventDefault only if something closed.
- **Mac dock**: Escape in the dock input bubbles to rootKey; closeTop skips chat on Cortex, so it only closes another open layer, else nothing.

Per layer: Hook Escape = Cancel (keeps pick, G61). Editor Escape = keep, ≠ Cancel (discard). Source Escape = Done. Chat Escape = Done (answer finished instantly). Settings Escape = Done.

### 6.3 Focus on close

- `restoreFocus()` (271): takes and clears `returnFocus`, then after 60 ms focuses it **only if still connected** (`isConnected`). Called by closeTop, closeSource (570), cancelEdit (552), saveEdit (566), closeEditorKeep (289), closeChat (657), closeSettings (667), toggleSettings close (473), closeHook (610), saveHook (615).
- **Not called** by `fixHealth` (490; closes Settings, focus lost).
- **Lost when the opener unmounted** (G57): the iPhone pill (hidden while chat is open); "Choose a hook" on first save; any opener whose screen changed.
- `focusButton(texts)` (272-277): after 60 ms, focuses the first visible `button`/`a` in `.te-root main` whose text starts with one of `texts`. Used by approveNow (380) and copy1 (577) (part 1). Not used in this part's screens.
- `returnFocus` is one slot: opening a second layer on top (only possible via ⌘K on Mac) overwrites it, so closing the lower layer later returns focus to an element inside the upper one or nothing (G64).

### 6.4 Keyboard entry, ⌘K and the canvas constraint

- **No global listeners.** The canvas forbids a global keydown handler, so keys are handled by `onKeyDown` on `.te-root` (rootKey), on each dialog (sheetKey), on the Results tablist (rtKey), on the chat input (typedKey) and on the hold button (part 1). Consequence: Escape and ⌘K do nothing until focus is inside the mock (after the first click or Tab into it). The real app should register ⌘K as an app/menu shortcut and Escape per dialog (G65).
- **⌘K / Ctrl+K on Mac** (302): `(metaKey || ctrlKey) && key ∈ {k,K}` → preventDefault → `askCortex(null)`:
  - Not on Cortex: returnFocus = active element; chatOpen=true, **context=null** (clears any "About:" chip) → MAC-DRAWER opens; focus to its input.
  - On Cortex: only context=null; focus to the dock input (the last shown "Ask Cortex" input).
  - With another layer open (sheetKey handles Escape only, so ⌘K bubbles): the drawer opens **on top of** a Source/Editor/Hook modal (DOM order), but **under** the Settings popover (POPOVER is last). closeTop then closes Hook/Editor/Source before Chat, i.e. the layer under the drawer first; with Settings open, it closes the drawer (under) before Settings (over) (G64).
  - iPhone: ⌘K is ignored (DEVICE check).
- **Tab order.** DOM order; main/nav inert while a layer is open. There is no focus trap: Tab from the last control of a dialog reaches any non-inert element outside it — iPhone: the Cortex pill (when Settings is open on Cortex); Mac: the sidebar profile button and theme toggle for every layer (G53).
- **aria-modal** is set on every dialog; the drawer/popover/modals rely on inert, not on a trap.

### 6.5 What the real app must keep

Focus into the dialog on open (the rules in 6.1), back to the opener on close (with a fallback target when the opener is gone: the screen's h1 or the replacement control), Escape closes the topmost visible layer, Cancel vs Escape semantics in the editor (#26), a single modal layer at a time or a real stack (closeTop order = paint order, per-layer returnFocus), everything behind a modal inert including the pill and the Mac sidebar controls (or make the Mac popover non-modal on purpose), reduced motion (`te-sheet-in`, `te-glow`, `te-swap` all disabled, Main:22, 31).

---
### 7. CMP-THINKING (the working line) and BRD-GALLERY

**Purpose.** While a command runs, its button becomes a live line: an icon that moves with the kind of step and shimmering text naming the real step; if it fails or needs an answer the line stops and says so in amber (D4, D20; review 25 Sep #18). File: `ui/mock/project/Thinking.dc.html` (template 35-88, script 90-219).

### 7.1 Interface

Props (data-props, Thinking.dc.html:90): `cmd` enum next|draft|ready|find|posted|record|ask|results (default draft; unknown → draft, 139); `loop` boolean (default `loop ?? !onDone`, 143: loops forever when no onDone); `show` live|error|needs (gallery only); `fail` string (non-empty = this run fails); `failAt` step index as string (default last step; clamped, 151-154); `ask` string (non-empty = ends in needs-you); `ansA`/`ansB` (default "Yes"/"Not now"); callbacks `onDone`, `onRetry`, `onCancel`, `onA`, `onB` (onA/onB are read in chooseA/B, 203-204, but not declared in data-props).

Rendering (renderVals 190-217): `done[]` = steps before the current one, each a ✓ row (36-41); `running` row (42-75) = `role=status aria-live=polite` with the step icon and `.te-shimmer` text `current`, plus "Step i of n" `counter`; `isError` block (76-81) `role=alert`: warning icon, "Stopped at: {current}." + `fail` (default "The command stopped before it finished. Nothing was changed."), buttons Try again / Cancel; `isNeeds` block (82-87) `role=alert`: "?" icon, "Needs you." + `ask` (default "This command needs an answer before it goes on."), buttons ansA / ansB. Reduced motion stops every icon animation and the shimmer (32).

State machine (script 146-188): mount → if `show` is error|needs, jump to that end state (i = failAt or last) (147); else `start()`: every **1500 ms** advance i; at `i >= failAt` with `fail` → `ended='error'`; at the last step: loop → i=0; else stop, then `fail` → error, `ask` → needs, else `onDone()` after **500 ms** (174). Mock duration = n × 1.5 s + 0.5 s. `finish(handler)` (178-183): calls onA/onB if given, sets ended='done' (the running row shows the last step again), then onDone immediately. Unmount clears both timers (185-188), so **leaving the screen stops the line; returning remounts it from step 1** while the host's `s.thinking` stays set (G66).

Step kinds and icons: `sync` rotating arrows (te-spin), `read` open book (te-bob), `search` magnifier sweep (te-sweep), `write` pencil (te-write), `count` three bars (te-bar1-3), `clock` rotating hand (te-hand), `check` shield + tick (te-pulse), `copy` two sheets (te-bob; defined, used by no step).

### 7.2 Commands, steps, hosts

| cmd | Mock steps (kind) — Thinking.dc.html:91-135 | Mock time | Real command and real steps to stream (system-today.md §2; BQ-Q4) | Error / needs in the mock | Hosts (Main · Mac) and callback |
|---|---|---|---|---|---|
| next | Running the daily snapshot (sync) · Reading the loop status (read) · Searching X for questions on your topic (search) · Checking the queue and your last post (read) · Picking the time slot (clock) | 8 s | CMD-NEXT: 1.1 snapshot (skip if already run this UTC day, review C7), 1.2 status, 1.3 runs.log, 2 weekly review + set-reference if due, 3 next-slot / experiment, 4.1 lane share, 4.2 x_read search (Grok), 4.3 queue, 4.4 timing, 5 proposal (needs-you: accept/edit; the mock shows it as the proposal card instead), 6 replies worth joining | none wired | Today: Main:146 · Mac:175, `doneNext` (526) |
| draft | Reading the PAID → FREE rules (read) · Checking the paid tools' pricing pages (search) · Reading the free tools' own docs (search) · Writing the claims table (write) · Counting characters as X does (count) | 8 s | CMD-DRAFT (minutes, review C9): read contract/row/format skill, research, CMD-VERIFY (fails closed), write files, `post_thread.py --count`. Step names depend on the format (these are tool-swap's) | error via `fail=q.fail` at failAt 1 (canvas `draft: error`, 453): "Couldn't reach postman.com/pricing. Nothing was written; try again in a minute." Try again → `q.retry` (draftRetried) then restart; Cancel → `q.cancel` (drafting=null). Needs-you (material questions, optional test offer) not modelled (part 1 G29) | Posts queue rows: Main:326 · Mac:358, `q.onDone` (461), `q.retry` (458), `q.cancel` (459) |
| ready | Checking the cards match your approval (check) · Running the final checks (check) · Writing the run sheet (write) | 5 s | CMD-READY: digest check, card refusals, POST.txt. Refusals are a *result*, not an error: the host shows them on the Posting screen (doneReady, 501-508) | none; refusals via doneReady | Today card: Main:81 · Mac:110, `doneReady` |
| find | Reading your latest posts from X (sync) · Matching it to your approved cards (check) | 3.5 s | X-READ timeline since the copy time, then text match against the approved card | not found is a host state (doneFind, canvas `find`) | Posting step 1: Main:257 · Mac:284, `doneFind` (583) |
| posted | Watching for your shout-out on X (sync) · Recording the post and the shout-out (write) · Opening the first-hour card (clock) | 5 s | poll X-READ for the shout-out reply, then CMD-POSTED (asks minutes; `loop.py record-post`) | none | Posting step 4: Main:284 · Mac:311 (cmd={{recordCmd}}), `doneRecord` (603) |
| record | Recording the post (write) · Opening the first-hour card (clock) | 3.5 s | CMD-POSTED without the shout-out (skip) | none | same host, recordCmd='record' when skipShout (602) |
| ask | Reading your weights and posts (read) · Checking the X ranking notes (search) · Writing an answer (write) | 5 s | CORTEX-CHAT: the real tool reads, then the answer (stream the answer text into the log instead of a final drop) | none; real needs error + usage-limit | Chat: Main:679 (sheet) · Mac:658 (dock), Mac:748 (drawer), `doneAsk` (660) |
| results | Reading this week's snapshots (sync) · Grouping your replies by topic (count) · Checking the rewards numbers (count) · Writing the weekly review (write) | 6 s, then needs-you | CMD-RESULTS: 1 CSV import (needs-you if missing), 2 eligibility numbers (needs-you), 3 status/evaluate, 4 numbers-only exit, 5 write the review sections (13 sections = a natural step count, system-today.md:374), 6 mark-reviewed + commit, 7 summary | needs-you after the last step: ask=`reviewAsk` "The review needs this week's numbers from X's eligibility screen." (648), "Use 24 Sep's: 27 and 337" / "Leave them out this week" → both → doneReview. Error not wired | Results: Main:538 · Mac:573, `doneReview` (647) |

**Not hosted anywhere:** a `sync` line for "Run the daily check now" / "Run it now" (CMD-SNAPSHOT is instant in the mock), and CMD-APPLY / CMD-UNDO (the buttons are disabled examples). The real app needs both.

**Real timing.** Steps and their order come from the running command's progress events, never a timer (D4 rejects fake progress; review C9: drafting takes minutes). The counter "Step i of n" is only honest when n is known up front; otherwise drop it. Keep the mock's rule that nothing is shown as done until the real step finished.

### 7.3 Controls inside the working line

```yaml
id: CTL-THINK-RETRY
label: "Try again" (after "Stopped at: {current}. {fail}")
where: Thinking.dc.html:79 (cj 71)
binding: onClick=retry (Thinking.dc.html:201): calls onRetry if given, sets {i:0, ended:null}, start()
shown when: isError (ended==='error')
enabled when: always
purpose: D4, D20; review 25 Sep #18
real wiring: re-run the same command from the start (or from the failed step if the command is resumable). Draft host: q.retry (main_script.js:458) sets draftRetried=true so the next run passes (canvas draft:error)
states: –
mock-only: in the gallery (no onRetry) it fails again at the same step
a11y: inside role=alert; the alert is announced on appear; focus isn't moved to it (the pressed button unmounted)
```

```yaml
id: CTL-THINK-CANCEL
label: "Cancel"
where: Thinking.dc.html:79 (cj 71, second)
binding: onClick=cancel (202): calls onCancel if given; nothing else (the line stays in error until the host unmounts it)
shown when: isError
enabled when: always
purpose: D4
real wiring: abandon the run; the host returns to its idle button. Draft host: q.cancel (459) → drafting=null
states: –
mock-only: gallery has no onCancel, so Cancel does nothing there
a11y: as Try again
```

```yaml
id: CTL-THINK-ANSWER
label: ansA | ansB (default "Yes" | "Not now"; results host: "Use 24 Sep's: 27 and 337" | "Leave them out this week")
where: Thinking.dc.html:85 (cj 77, two buttons)
binding: onClick=chooseA|chooseB (203-204) → finish(onA|onB): handler, ended='done', onDone()
shown when: isNeeds (ended==='needs')
enabled when: always
purpose: D4 (needs-you inside the line), D20 (amber)
real wiring: sends the answer to the waiting command (e.g. CMD-RESULTS step 2: record-eligibility with the numbers, or decline). Real answers often need input (two numbers), not two fixed buttons (G50)
states: –
mock-only: the only host (results) passes no onA/onB, so both answers are identical
a11y: in role=alert; two buttons with visible text
```

### 7.4 BRD-GALLERY (`WorkingStates.dc.html`)

Board "Working states" (canvas.json: 1200×1000 at y=2640). Heading "While a command is working" + explainer (WorkingStates.dc.html:21-22). Ten sections, each a label + command and a `<dc-import Thinking loop=true fail-at="1" …>` (25-30), from `cmds` (46-57): Plan the next post `/next`; Draft `/draft-thread`; Start posting `/ready`; I've posted it `/posted` (find); Copy the shout-out `/posted` (posted); Skip the shout-out `/posted` (record); Ask Cortex `chat`; Write this week's review `/results`; "When a command fails" (draft, show=error, the postman.com message, stops at step 2); "When it needs you" (results, show=needs, "Use 24 Sep's" / "Leave them out"). Then an "Approve" section: "Approving is not a working state. You press and hold…" with a looping CSS hold demo `.te-holddemo` (3.2 s; static 60% under reduced motion) (31-38). No handlers of its own; Try again / Cancel / answers inside have no host callbacks (mock-only). The separate board "Working state (one component)" is Thinking.dc.html itself with its prop editor (canvas.json).

---

### 8. Canvas tweaks and dark boards

- **Canvas props on Main and Mac** (Main:756, Mac:801; build.py:16; line 18 is an older `ORIGPROPS` variant): `theme` system|light|dark (seeds the theme when `s.theme` is null, main_script.js:434); `health` ok|failed (healthBad, 440); `find` found|notfound|differs|twice (doneFind, 585-587; part 1); `gate` ok|refused (doneReady, 506; part 1); `draft` ok|factcheck|error (453, 457; part 1). `$preview` 390×844 / 1440×900. All mock-only; the real app derives each from real state (G33, part 1 §0).
- **Dark boards**: `PhoneDark.dc.html` and `MacDark.dc.html` are wrappers that `<dc-import name="Main|Mac" theme="dark">` at 390×844 / 1440×900 on `#15140F` (identical except size and title). They are live, interactive copies with their own state (D21). Tokens: `.te-root[data-theme="dark"]` (Main:24) and `@media (prefers-color-scheme: dark){.te-root[data-theme="system"]…}` (Main:25), the same values; details in `handoff/design-system.md`.
- **Canvas layout** (canvas.json): iPhone (0,0) and MacBook (470,0) interactive; "Dark mode" title at y 1020, dark boards at y 1320; "Working states" title at y 2340, gallery (0,2640) and single component (1280,2640). Title note "Thread Engine UI".
- **build.py** (ui/mock/src/build.py) also writes test-only light pages `serve/T-{notfound,differs,twice,refused,factcheck,draftfail,health}.dc.html` (build.py:32-36), not committed.

---
### 9. Display values (renderVals keys in scope that aren't controls)

All in main_script.js unless noted. "Real" = the build's data source (data.md ids where they exist).

| Key | Shows | Computed at | Real |
|---|---|---|---|
| isReplies, isResults, isCortex | screen flags | 483 | router |
| showDrawer | Mac chat drawer visible (Mac && chatOpen && screen≠cortex) | 472 | router |
| showPill | iPhone Cortex pill visible | 655 | router |
| chatOpen, settingsOpen, editorOpen, hookOpen, hasSource | layer flags (sc-if and aria-expanded) | 655, 666, 545, 611, 569 | LOCAL |
| mainInert, navInert | 'true' or null → `inert` on main/nav | 468, 477 | LOCAL |
| themeAttr | data-theme on .te-root: s.theme ‖ props.theme ‖ 'system' | 434, 477 | SETTINGS-STORE |
| showMoon, showSun, flipLabel | toggle icon and name from the resolved theme | 478-479 | – |
| avatarLabel, healthBad, healthDot | profile button name, amber dot, status dot | 487-488, 440 | runs.log (part 1 G33) |
| sideHealth | Mac status card: "Daily check ran 20:00" / "Daily check missed last night" | 475 | runs.log last line (DATA-T03) |
| profileBg | Mac profile row fill while Settings is open | 474 | – |
| tab{K}, tab{K}Weight, tab{K}Current, tab{K}Label | iPhone tab colour, weight, aria-current, name ("Replies, N waiting") | 444-451 | router + REPLIES-READ |
| nav{K}Bg, nav{K}Bar | Mac sidebar row fill and 3px bar | 450 | router |
| waitingCount, hasWaiting, noWaiting | badge count and visibility; empty state | 420, 520 | REPLIES-READ minus outcomes |
| waiting[] {id, handle, where, age, said, point, open, closed, status} | Waiting for you cards | 30-37, 516-519 | REPLIES-READ (DATA-RP01); `point` is a talking point from where? (G46) |
| builders[] {handle, tags, last} | Builders list | 38-43, 522 | none yet (DATA-RP03; D28) |
| replies[] {handle, found, kind, what, point} | Worth joining (short is Today's) | 19-29, 515 | stored CMD-NEXT §6 (DATA-RP02; review C5) |
| rtGrowth/rtPosts/rtReplies (+Bg, Border, Weight, Ti) | selected tab, tab styles, roving tabindex; also the panel sc-if | 438-439, 675 | LOCAL |
| rtPanelLabel | panel aria-label | 633 | – |
| showTable, showChart, tableLabel | chart/table switch | 634 | LOCAL |
| kpis[] {label, value, sub} | four tiles for the tab (KPIS[rt]) | 72-91, 635 | DATA-RES02–10 |
| followSrc[] {t, n, pct, label} | follow sources bars; pct = n/13×70% (13 hard-coded max) | 71, 636 | weekly export (DATA-RES11) |
| followerDays[] {d, n} | followers table: one row "Thu 24 Sep, 36"; the chart is literal markup (Main:481-482) | 637 | account.json days[] (DATA-RES12) |
| shareSlots[] {bg, border}, shareRows[] {n, v}, shareLabel | 15-slot on-topic strip, its table and its img label "On topic: 5 of your last 11 posts, 4 still to post. Target 12 of 15."; legend counts (5)/(6)/(4) are literal markup (Main:498) | 64, 640-642 | lane of the last 15 originals (DATA-RES13; D19, D30) |
| rposts[] {title, when, label}, postRows[] {t, f, v, w, topic} | posts sorted follows → visits → views; "not counted" for boosted | 50-62, 466, 638-639 | ledger (DATA-RES15; D27) |
| rtopics[] {t, visits, follows, views, pct, label} | reply topics; pct = visits/15×48% (15 hard-coded) | 65-70, 643-644 | hand-grouped in the weekly review (DATA-RES16) |
| showReviewButton, thinkingResults, reviewWritten, reviewAsk | review button / working line / "Review written" / the needs-you question | 646-648 | CMD-RESULTS state; review_due |
| busy, busyOpacity | disables the review button while any command runs | 309, 509 | command runner state |
| pipeline[] {n, label} | 2 / 0 / 0 / 5 tiles (static) | 119, 650 | counts from questions, experiments.md, learnings.md, weights file (DATA-CX01) |
| weights[] {name, value, src, style} | Weights; italic when `guess` | 92-98, 650 | a weights file (review C8; DATA-CX04) |
| guardrails[] {text} | six guardrails | 99-106, 651 | fixed text (DATA-CX05) |
| questions[] {t, why} | open questions | 115-118, 651 | queue/research-backlog.md (DATA-CX08) |
| nextExperiments[] {n, text, first}, queuedExp, queueLabel | experiments up next; queue state and label | 107-114, 652-653 | next SKILL list (DATA-CX07) + NO-CMD queue |
| chat[] {text, isUser, isBot} | conversation | 138, 658 | CORTEX-CHAT history (per device or shared: undecided, G58) |
| asking | answer in flight (disables chips, mounts the `ask` line) | 659 | CORTEX-CHAT |
| suggestions[] {q, ask} | chips for the context | 661 | curated per context |
| hasContext, contextLabel | "About: …" chip | 662, 431 | context object |
| typed | input value | 663 | LOCAL |
| settingsGroups[] {title, rows[] {name, sub, value, dot, isToggle, notToggle, on, knob, track}} | Settings Health / Notifications / Cortex | 139-154, 668-673 | runs.log, loop.py status, x-algorithm.md header, SETTINGS-STORE (DATA-SET01–07) |
| thIsLight/thIsDark/thIsSystem (+Bg, Border, Weight; Ti unused) | Appearance radios | 676-677 | SETTINGS-STORE |
| src {n, paid, free, paidFact, paidSrc, quote, freeSrc, limit} | Source sheet | 464, 569 | CLAIMS.md (DATA-P05, P06) |
| draftPending, editClearsApproval, draftText, takeText, draftCount, draftCountColor | Editor state, amber note at stage 3, X count | 545, 553-557 | card file + x_length |
| hooks[] {text, n, count, on, border, bg}, hookTake | Hook sheet | 155-159, 612-614 | draft's hook options (none exist, part 1 G12) |
| Thinking: done[] {text}, running, current, counter, isSync … isCopy, isError, isNeeds, fail, ask, ansA, ansB | the working line | Thinking.dc.html:190-217 | command progress events |
| WorkingStates: cmds[] {cmd, label, what, show, fail, ask, ansA, ansB} | gallery rows | WorkingStates.dc.html:44-58 | – |

**Static markup worth flagging (not renderVals):** Results eyebrow "week of 18–24 Sep" and both h1 lines (Main:438-439; DATA-RES01); "Data starts 20 Sep" (Main:455); followers chart "36 / Thu 24 Sep" (Main:481-482); legend counts (Main:498); the example lesson (Main:559-568); "None running · Paused until about 8 Oct" (Main:590); Settings header "@exitzerocode · 36 followers" (Main:701); chat header model "Claude" (Main:669); Mac status card numbers (Mac:47-49); "Review written … due Thu 1 Oct" (Main:539).

---

### 10. Gaps (G46 onward; part 1 has G1–G45)

G46. **Ask contexts are anonymous.** `askCortex(context)` passes only a string ('reply', 'results', 'post', 'proposal'); it doesn't say which reply, which tab/range, or which draft. The real chat needs a context object (id + snapshot of what's on screen). Also: where does a waiting card's "A point you could make" come from? It reads like Cortex/Grok output (voice: "Grok may suggest what a reply should say"), but no command produces it for mentions; /next §6 only covers Worth joining.

G47. **Worth joining has no "Ask Cortex"** while Waiting does; D14 lists "a waiting reply", so this may be intended. Confirm.

G48. **Date range vs weekly copy.** 30/90 days are planned, but the header lines, KPI subs ("this week") and the review cadence are weekly. Decide what the range changes.

G49. **Results with no review due.** The review button shows whenever no review has been written in this session. `/results` only writes a review when `review_due`; otherwise it prints numbers. The real button needs a "not due until <date>" state.

G50. **Needs-you shape.** The mock asks after the last step with two fixed buttons that do the same thing. CMD-RESULTS asks at steps 1–2 and needs typed numbers (or a CSV file import on iPhone). The working line needs an input variant and callbacks per answer.

G51. **Apply/Undo trust level.** /apply and /undo-rule change the drafting rules and are operator-only commands, like /approve. The D24 build note (block agents from what the Approve button calls) should cover Apply/Undo too, or state why not.

G52. **Example lesson names a Weight that doesn't exist** ("Apply to Post length"; Weights are Opening, Daily limit, Series pace, Posting slots, On topic means). The real Apply label must name the lesson's target file/Weight.

G53. **Not everything behind a modal is inert.** iPhone: the Cortex pill (outside main/nav) stays focusable under Settings. Mac: the sidebar profile button and theme toggle (outside nav) stay focusable under every modal, the drawer and the popover. There is no focus trap.

G54. **Source domains are plain text** ("postman.com/pricing"). A receipt should be a link to the exact page (the claims table has the URL).

G55. **Edits vs fact-check.** The editor promises "Every claim still goes through the fact-check", but nothing re-runs CMD-VERIFY after an edit. A changed claim must be re-verified before approval (fail closed).

G56. **Proposal context uses the general suggestions** (ctxSet.proposal = SUGGESTIONS, 430) while its chip says "About: the proposed build log".

G57. **Focus return fails when the opener unmounts**: the iPhone pill (hidden while chat is open), "Choose a hook" on first save, Answered/Not answering/Undo, Clear context, Discard them, Run the daily check now. restoreFocus silently does nothing.

G58. **Cortex model and history.** The model is shown ("Claude") but not choosable; D9 says "whichever the operator has set up". Chat history is one in-memory list shared by all contexts; decide persistence (device vs Mac) and whether contexts get separate threads.

G59. iPhone Settings focuses the theme toggle on open (first button), not Done or the heading.

G60. **Settings Health rows are static** and don't change with `health: failed` (Daily check still "Ran 20:00 last night", X API "Last read worked"). Real rows: last runs.log line, keys check (`x_api.py keys` only checks presence, review C6), spend estimate incomplete (review C6: x_read/Grok/CLI costs not logged).

G61. **Hook Cancel keeps the new pick** in state (closeHook doesn't revert hookPick/hookTake). The saved take is never displayed.

G62. **Tab changes don't reset scroll or announce the page.** `<main>` is one scroll container for every screen and nothing sets scrollTop (no scrollTop in main_script.js), so a new tab opens at the previous tab's scroll offset; focus stays on the tab button with no heading focus or live announcement.

G63. **Mac Settings is both a disclosure and a modal** (aria-expanded on the button, aria-modal on the popover, main/nav inert, sidebar live). Pick one model.

G64. **Layers can stack only via ⌘K on Mac**, and then closeTop order ≠ paint order and the single returnFocus slot is overwritten. Either block ⌘K while a modal is open, or keep a real layer stack.

G65. **Keyboard reach.** Escape and ⌘K only work once focus is inside `.te-root` (canvas has no global handler). The real app: ⌘K as an app shortcut (and a menu item), Escape per dialog.

G66. **Working line tied to the screen.** Thinking's timers live in the component; leaving the screen unmounts it, the host flag (`s.thinking='results'`) stays set so `busy` stays true (every other command disabled), and returning restarts the line from step 1. Real progress must live with the command runner, survive navigation and app restarts, and the UI re-attach to it.

G67. **Replies data freshness and cost.** Waiting/badge need REPLIES-READ; the first mentions read of a UTC day costs about US$0.06–0.10 (review C3), repeats that day are free (x-api P5). Decide when it runs (on open of Replies/Today, on the first-hour card, never per render) and show "checked HH:MM".

G68. **Greetings line and counts.** "Plus 37 greetings…" and "2 mutuals on topic" need a greeting classifier and a mutual/on-topic computation that don't exist (DATA-RP04, RP05). Classification of other people's text happens locally and stays private.

G69. **Chart scales are hard-coded** (follow sources /13, reply topics /15, verified bar 5.4%). Scale from the data.

G70. **Queue an experiment has no record or undo** (CTL-CORTEX-QUEUE-EXP), and "about 8 Oct" is static text in three places (button, Lessons empty state, Experiments panel).

G71. **Send while answering** is silently dropped (the text stays in the field); only the chips are disabled.

G72. **`copy` step kind** is defined in Thinking but used by no command; posting's copy steps aren't working lines in the mock. Keep or drop in the real icon set.

---

### 11. Coverage check against controls.json

In-scope controls.json entries: Main isReplies 7, isResults 10, isCortex 4, screen null 5 (tab bar), showPill 1, hasSource 1, editorOpen 5, chatOpen 5, settingsOpen 7, hookOpen 4 (49); Mac screen null 7 (sidebar), isReplies 6, isResults 9, isCortex 7 (incl. dock chat 4), hasSource 1, editorOpen 5, hookOpen 4, showDrawer 5, settingsOpen 6 (50); Thinking.dc.html 4. Total 103. (WorkingStates.dc.html has no controls of its own.)

| controls.json (file:cj line) | File line | Control id |
|---|---|---|
| Main:375 | Main:383 | CTL-REPLIES-AVATAR |
| Main:382 / Mac:416 | Main:390 / Mac:424 | CTL-REPLIES-UNDO |
| Main:389 / Mac:423 | Main:397 / Mac:431 | CTL-REPLIES-ANSWER-LINK |
| Main:390 / Mac:424 | Main:398 / Mac:432 | CTL-REPLIES-ANSWERED |
| Main:391 / Mac:425 | Main:399 / Mac:433 | CTL-REPLIES-NOT-ANSWERING |
| Main:393 / Mac:427 | Main:401 / Mac:435 | CTL-REPLIES-ASK |
| Main:419 / Mac:453 | Main:427 / Mac:461 | CTL-REPLIES-WORTH-OPEN |
| Main:430 | Main:438 | CTL-RESULTS-AVATAR |
| Main:435-437 / Mac:470-472 | Main:443-445 / Mac:478-480 | CTL-RESULTS-TAB (×3) |
| Main:441-443 / Mac:476-478 | Main:449-451 / Mac:484-486 | CTL-RESULTS-RANGE (×3) |
| Main:445 / Mac:480 | Main:453 / Mac:488 | CTL-RESULTS-TABLE-TOGGLE |
| Main:528 / Mac:563 | Main:536 / Mac:571 | CTL-RESULTS-ASK |
| Main:529 / Mac:564 | Main:537 / Mac:572 | CTL-RESULTS-WRITE-REVIEW |
| Main:538 | Main:546 | CTL-CORTEX-AVATAR |
| Main:559 (1st) / Mac:595 (1st) | Main:567 / Mac:603 | CTL-CORTEX-APPLY |
| Main:559 (2nd) / Mac:595 (2nd) | Main:567 / Mac:603 | CTL-CORTEX-UNDO |
| Main:589 / Mac:625 | Main:597 / Mac:633 | CTL-CORTEX-QUEUE-EXP |
| Main:604-608 | Main:612-616 | CTL-NAVPHONE-TAB (×5) |
| Main:612 | Main:620 | CTL-NAVPHONE-PILL |
| Mac:31-35 | Mac:39-43 | CTL-NAVMAC-TAB (×5) |
| Mac:44 | Mac:52 | CTL-NAVMAC-PROFILE |
| Mac:48 | Mac:56 | CTL-NAVMAC-THEME |
| Main:629 / Mac:679 | Main:637 / Mac:687 | CTL-SOURCE-DONE |
| Main:640 / Mac:690 | Main:648 / Mac:698 | CTL-EDITOR-CANCEL |
| Main:641 / Mac:691 | Main:649 / Mac:699 | CTL-EDITOR-DISCARD |
| Main:644 / Mac:694 | Main:652 / Mac:702 | CTL-EDITOR-CARD |
| Main:648 / Mac:698 | Main:656 / Mac:706 | CTL-EDITOR-TAKE |
| Main:650 / Mac:700 | Main:658 / Mac:708 | CTL-EDITOR-SAVE |
| Main:661 / Mac:730 (drawer) | Main:669 / Mac:738 | CTL-CHAT-DONE |
| Main:675 / Mac:654 (dock) / Mac:744 (drawer) | Main:683 / Mac:662 / Mac:752 | CTL-CHAT-CLEAR-CONTEXT |
| Main:677 / Mac:656 / Mac:746 | Main:685 / Mac:664 / Mac:754 | CTL-CHAT-SUGGESTION |
| Main:679 input / Mac:658 / Mac:748 | Main:687 / Mac:666 / Mac:756 | CTL-CHAT-INPUT |
| Main:679 button / Mac:658 / Mac:748 | Main:687 / Mac:666 / Mac:756 | CTL-CHAT-SEND |
| Main:694 | Main:702 | CTL-SETTINGS-THEME-FLIP |
| Main:698 / Mac:763 | Main:706 / Mac:771 | CTL-SETTINGS-DONE |
| Main:708 / Mac:773 | Main:716 / Mac:781 | CTL-SETTINGS-NOTIFY-SWITCH |
| Main:717-719 / Mac:782-784 | Main:725-727 / Mac:790-792 | CTL-SETTINGS-APPEARANCE (×3) |
| Main:722 / Mac:787 | Main:730 / Mac:795 | CTL-SETTINGS-RUN-HEALTH |
| Main:733 / Mac:711 | Main:741 / Mac:719 | CTL-HOOK-CANCEL |
| Main:736 / Mac:714 | Main:744 / Mac:722 | CTL-HOOK-OPTION |
| Main:739 / Mac:717 | Main:747 / Mac:725 | CTL-HOOK-TAKE |
| Main:741 / Mac:719 | Main:749 / Mac:727 | CTL-HOOK-SAVE |
| Thinking:71 retry | Thinking:79 | CTL-THINK-RETRY |
| Thinking:71 cancel | Thinking:79 | CTL-THINK-CANCEL |
| Thinking:77 chooseA / chooseB | Thinking:85 | CTL-THINK-ANSWER |

Counts: Main 49 entries (7+10+4+5+1+1+5+5+7+4) and Mac 50 entries (7+6+9+7+1+5+4+5+6) and Thinking 4 map to 45 control ids. Every in-scope handler binding in controls.json (`openSettings`, `wt.undo/answered/skip/ask`, `rtGo*`, `toggleTable`, `askAboutResults`, `writeReview`, `queueFirst`, `goToday/goPosts/goReplies/goResults/goCortex`, `openChat`, `toggleSettings`, `flipTheme`, `closeSource`, `cancelEdit`, `discardDraft`, `setDraftText`, `setTakeText`, `saveEdit`, `closeChat`, `clearContext`, `sg.ask`, `setTyped`, `typedKey`, `sendTyped`, `closeSettings`, `row.flip`, `thIs*Go`, `fixHealth`, `closeHook`, `hk.pick`, `setHookTake`, `saveHook`, `retry`, `cancel`, `chooseA`, `chooseB`) is documented above. Also documented though not in controls.json: the scrims (CTL-SHEET-SCRIM), `sheetKey`, `rootKey`, `rtKey`. **No in-scope control is undocumented.** iPhone-only: CTL-REPLIES-AVATAR, CTL-RESULTS-AVATAR, CTL-CORTEX-AVATAR, CTL-NAVPHONE-TAB, CTL-NAVPHONE-PILL, CTL-SETTINGS-THEME-FLIP. Mac-only: CTL-NAVMAC-TAB, CTL-NAVMAC-PROFILE, CTL-NAVMAC-THEME, and the dock instances of the chat controls (no CTL-CHAT-DONE in the dock).
