# State machine

Every state the UI can be in, what moves it, and the guards on each move. Source: `ui/mock/src/main_script.js` (the `DEFAULTS` object, `renderVals()` and the `Component` methods). Where the real app must differ from the mock, the row says **Real:**.

## 1. The post's life (`stage`)

One post at a time moves through five steps (D15: Plan → Draft → Approve → Post → Measure). The mock starts at stage 2 with the developer-tools post drafted.

| `stage` | Name (`STAGE_NAMES`) | Stepper shows | Entered by | Left by |
|---|---|---|---|---|
| 1 | Drafting | Draft current | **Real:** `/draft-thread <slug>` running (mock never shows 1 for the main post; queue items draft separately, §4) | draft written → 2 |
| 2 | Needs your approval | Approve current | draft done; `saveEdit` after approval (changed text); `reapprove`; `withdraw` | hold completes → 3 |
| 3 | Approved | Approve current (✓ after) | `approveNow` (hold reached 100%); `notNow` from 4; gate refusal keeps 3 | `doneReady` with no refusals → 4; card edit → 2 |
| 4 | Posting | Post current | `doneReady` when stage is still 3, cards equal `approvedText`, and `gateRefusals()` is empty | `doneRecord` → 5; `notNow` → 3; `withdraw` → 2 |
| 5 | Posted, measuring | Measure current | `doneRecord` (after the shout-out is recorded or skipped) | **Real:** the next post becomes the current one |

### Guards (MUST keep in the real app)

- **G-APPROVE:** approval stores the exact card text (`approvedText`). **Real:** the `approve.py` hook writes `APPROVED` with `cards-sha256:` = `post_thread.cards_digest()`, a SHA-256 over every numbered card's filename and bytes in order (`scripts/post_thread.py:158-163`). Only the operator's typed `/approve` may create it (`AGENTS.md:14`); a button path needs a contract change (README rule 2).
- **G-EDIT:** any saved change to the cards at stage 3 drops to stage 2 and clears the approval (`saveEdit`). Editing is disabled while the final checks run (`editDisabled` when `thinking === 'ready'`).
- **G-READY:** `doneReady` moves to 4 only if the stage is still 3 **and** the text equals `approvedText` **and** there are no gate refusals. Otherwise it stays at 3 and shows the reasons (`refused`). **Real:** this is `scripts/post_thread.py`: exit 2 prints `human gate` (no approval); exit 1 prints the `REFUSED:` lines on **stderr**, a stale digest first (`post_thread.py:404-410`); exit 0 writes `POST.txt`. Card edits never delete `APPROVED`; they make its digest stale.
- **G-BUSY:** only one command runs at a time (`busy = thinking || drafting`). Plan, Draft, Write review, Start posting, Start early and Pick another are disabled while busy. **Real:** the Mac-side runner must serialise commands or reject a second one.
- **G-BACK:** "Not now" and "Withdraw approval" exist only at stage 4 before the post is found (`canBack`). **Real:** "Not now" is UI-only. "Withdraw approval" would delete `APPROVED`, which `AGENTS.md:14` forbids; it needs a contract change and an operator-only path, or it goes (editing a card already makes the approval stale).

## 2. Posting (stage 4) sub-steps (D17)

| Step | State keys | Shown | Moves when |
|---|---|---|---|
| 1 Post | `copyState` none → ok / failed; `finding`; `notFound`; `posted1` | Copy the post → Copied / Couldn't copy (Copy again, Open X) → "I've posted it" (only after a successful copy) → finding (working line `find`) → Found / Not on X yet (Check again, It's up, carry on) | `doneFind` sets `posted1`, `foundMs`, `foundAt`; tweak `find` = `differs` or `twice` adds an amber warning |
| 2 Wait | `waitLeft` = max(0, `foundMs` + 10 min − now), or 0 if `waitSkipped` | countdown, window "between HH:MM and HH:MM" | reaches 0 → step 3. **Real:** `foundMs` must be the post's `created_at` from X, not the time the app found it |
| 3 Thank the maker | `copied2`, `copy2Failed`, `nudgeSent`, `windowClosed` | Copy the shout-out; failure card; "Nudge sent" if the Settings switch is on; "window closed" after +20 min | copy ok → `thinking = 'posted'` (watching for the shout-out) |
| 4 Done | `thinking` `posted` or `record` | working line; Done button as fallback | `doneRecord` → stage 5, screen Today. **Real:** `/posted` records the root, the thread's cards and `production_minutes` only; shout-out status and time to first like need new `loop.py`-owned data and commands |

"Skip the shout-out" sets `skipShout` and runs the shorter `record` steps. "Skip the wait (mock only)" is mock-only.

## 3. Time states (the next post's slot)

The slot is `slotMs` (default `TARGET` = 2026-09-25 06:00 Brisbane). Brisbane is UTC+10 all year; the script does its own arithmetic (`hhmm`, `brisShort`, `brisMidnight`).

| Condition | Countdown | Stage 2 headline / primary | Stage 3 headline / primary |
|---|---|---|---|
| more than 30 min before | "in H h M m" (blue) | "Today's / Tomorrow's / Your next post needs your read." / Read and approve | "Approved, and ready for 06:00 today/tomorrow/on <day>." / Remind me at 05:50 (toggles `remind`), plus "Start posting early anyway" |
| within 30 min before | "in M min" | same | "Almost time to post." / Start posting |
| 0–60 min after (inside 05:00–07:00) | "N min late, still inside the 05:00–07:00 slot" (amber) | same | "Time to post." / Start posting |
| more than 60 min after | "missed the slot" (amber) | "The 06:00 slot has passed." / Read and approve, hint "Then move it to tomorrow, 06:00" | "The 06:00 slot has passed." / "Move it to <next slot>" → `slotMs = nextSlot(now)` |

`nextSlot(now)` = the next 06:00 at least 30 minutes away. At stage 5 the hint reads "The first full read comes with the daily check on <day> at 20:00", where `firstRead(posted)` = the first 20:00 Brisbane at or after posting + 36 h (the snapshot's 36–60 h window and the 20:00 launchd job). **Real:** the slot comes from the queue row's `post_at` (`queue/topics.yaml`), and moving it must write the new time back.

The first-hour card (D29) shows at stage 5 until `foundMs` + 60 min, or until closed.

## 4. Queue drafting (Posts screen)

Per queue item: `showDraft` → Draft (disabled while busy) → `drafting = id` (working line `draft`) → `drafted[id]` → chip "Drafted · next in line". Tweak `draft`: `factcheck` adds the amber "couldn't confirm one claim" note; `error` stops the working line at step 2 with Try again / Cancel (`draftRetried` clears the failure). **Real:** `/draft-thread <slug>`; the fact-check (`/verify-settings` claims mode) fails closed.

## 5. Working line (`Thinking.dc.html`)

| State | Trigger | Shows | Leaves by |
|---|---|---|---|
| running | mount | done steps ✓, current step with its icon and shimmer, "Step i of n" | last step → done (calls `onDone` after 500 ms) |
| error | `fail` prop set and step ≥ `failAt` | amber "Stopped at: <step>. <message>", Try again, Cancel | Try again → `onRetry` then restart; Cancel → `onCancel` |
| needs you | `ask` prop set, last step reached | amber "Needs you. <question>", two answers | an answer → `onA`/`onB`, then `onDone` |
| static | `show` = `error` or `needs` (gallery) | that state immediately | – |

Hosts: `next` (Today, Plan the next post), `draft` (Posts queue), `ready` (Today next-post card / Mac right column), `find`, `posted`, `record` (Posting), `ask` (chat), `results` (Results, with the needs-you question for the eligibility numbers). The mock advances every 1.5 s. **Real:** steps must come from the command's actual progress; progress must live with the command runner, not the screen. In the mock, leaving the screen unmounts the line; `thinking` stays set (so every other command stays disabled), and coming back restarts the line from step 1 (screens.md G66).

## 6. Sheets, focus and keys

Layers, top first, as `closeTop()` closes them: hook sheet → editor → source → chat (not the Mac's docked chat) → settings. Escape closes the top layer (`sheetKey` on each dialog stops the event; `rootKey` on `.te-root` handles Escape outside dialogs and ⌘K on the Mac).

| Event | Effect |
|---|---|
| open a sheet (`openSheet(patch, label, first?)`) | remembers the focused element; after render focuses `first`, else the first textarea/input, else the first button |
| close | `restoreFocus()` returns focus to the opener if it still exists |
| any sheet open | `mainInert` and `navInert` = `'true'` (main content and nav/sidebar inert) |
| editor opens | Source closes (`source: null`) |
| editor closed by Escape or scrim | edits kept (`draftPending`), note "Your unsaved changes are still here." on reopen; Cancel discards |
| chat closed while answering | the answer is added at once (`finishAsk`), so the chat is never left stuck |
| ⌘K (Mac) | opens the chat drawer; on the Cortex page focuses the docked input instead |
| navigating (`go(screen)`) | closes the chat and the source sheet |

## 7. Other local state

| Key | Values | Set by |
|---|---|---|
| `screen` / `prevScreen` | today, post, ready, posts, capture, replies, results, cortex | tabs, Preview, Back |
| `theme` | null (follow device), light, dark | toggle, Settings radios (D23) |
| `rtab`, `showTable` | growth / posts / replies; bool | Results tabs (arrow keys), Show as table |
| `remind`, `nudge` | bool | Settings switches, Remind me (D35) |
| `dismissed[id]` | answered, skipped | Replies buttons, Undo |
| `captures[]`, `turned[id]`, `capKind` | list with `id`, `format` | Capture |
| `hookPick`, `hookTake`, `hookSaved` | index, text, bool | hook sheet (D26) |
| `cardBase`, `cardTake`, `draftText`, `takeText`, `draftPending` | text | editor |
| `proposal` | null, shown, accepted | Plan the next post |
| `review`, `queuedExp`, `minutes`, `firstHourClosed`, `healthFixed`, `readerTurned` | bool / value | their buttons |
| `context` | null, post, results, reply, proposal | Ask Cortex buttons (D14) |

**Real:** every key above that records a choice (remind, nudge, dismissed, captures, hook picks, edits, minutes, queued experiment, theme) must persist somewhere; today none are stored (see `data.md`).
