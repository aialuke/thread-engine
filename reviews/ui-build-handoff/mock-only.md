# Mock-only behaviour: must not ship as is

Everything below is faked in the mock (version 22) so it can be clicked through. Each row says what the real app must do instead. Source: `ui/mock/src/main_script.js`, `ui/mock/src/build_body.py`, `ui/mock/project/Thinking.dc.html`.

## Time

| ID | Fake | Real |
|---|---|---|
| MO-1 | `TARGET` = 2026-09-25 06:00 Brisbane is the only slot; "Move it to" moves it in memory | the slot is the queue row's `post_at` (`queue/topics.yaml`); moving it writes the row |
| MO-2 | the Wait timer counts from when the app found the post (`foundMs`) | from the post's `created_at` read from X |
| MO-3 | "Skip the wait (mock only)" | remove |
| MO-4 | every working line advances each 1.5 s and always succeeds unless a tweak says otherwise | steps and outcome come from the real command's progress and exit status |
| MO-5 | "Last daily check: Wed 20:00", "Daily check ran 20:00 last night. 6 posts are still too new to measure." are fixed strings | from `ledger/runs.log` and the snapshot status (`loop.py status`) |
| MO-6 | Today's date label uses the device clock; other dates (week of 18–24 Sep, "Thu 1 Oct" export, "last read 24 Sep") are fixed | computed from the data and the calendar |

## Canvas tweaks (props on `Main`/`Mac`)

| Prop | Values | Stands in for |
|---|---|---|
| `health` | ok, failed | the daily check's real status |
| `find` | found, notfound, differs, twice | the real result of reading the account's latest posts and comparing with the approved cards |
| `gate` | ok, refused | `scripts/post_thread.py` refusing on the digest ("Card 1 changed after you approved it.") |
| `draft` | ok, factcheck, error | `/draft-thread` outcomes: a claim the fact-check couldn't confirm, or a failed run |
| `theme` | system, light, dark | the operator's setting (real) |

## Actions that do nothing real

| ID | Control | Real wiring |
|---|---|---|
| MO-7 | Hold to approve sets `stage = 3` | creates `APPROVED` with the cards digest, and only from the operator's own press (D13, D24). The typed `/approve <slug>` stays as backup and as the accessible route |
| MO-8 | Start posting runs a fake `ready` line; the mock mirrors the gate's refusals in JavaScript (`gateRefusals`) | runs `scripts/post_thread.py` and shows its refusals; the JS copy exists only so the mock can demonstrate them |
| MO-9 | Copy uses `navigator.clipboard` on the device | the phone's own clipboard; `post_thread.py --copy N` uses `pbcopy`, which only reaches the Mac |
| MO-10 | "I've posted it" / Check again / It's up | a read of the account's timeline, matched to the approved cards |
| MO-11 | Copy the shout-out → "Watching for your shout-out" → recorded | detect the reply on X, then `/posted` records the post, the shout-out and time to first like |
| MO-12 | Plan the next post → a fixed proposal (example tag) | `/next` |
| MO-13 | Draft on a queue item | `/draft-thread <slug>` |
| MO-14 | Write this week's review → needs-you question → "Review written" | `/results` (it asks for the eligibility numbers) |
| MO-15 | Queue for about 8 Oct | `loop.py` experiment queueing; experiments are paused until about 2026-10-08 |
| MO-16 | Apply / Undo on the example lesson (disabled) | `/apply <lesson>`, `/undo-rule <lesson>` |
| MO-17 | Cortex answers are canned (`SUGGESTIONS*`, `FALLBACK` for anything typed) | a model answering from the repo's data under the D14 rules; no backend exists |
| MO-18 | Capture saves to memory; "Turn into a post" only marks it queued | storage for screenshots, recordings and voice notes, transcription, and a route into a build-log or tool-verdict draft; no backend exists |
| MO-19 | Hook picker saves the pick in memory | the draft's hook card, and a preference signal for the loop |
| MO-20 | Editor edits change the card in memory and say "recorded as a preference" | write the card file, invalidate `APPROVED`, record the edit as a signal (not stored anywhere today) |
| MO-21 | Remind me / Settings switches toggle in memory | a notification service and stored settings (D35) |
| MO-22 | Run it now / Run the daily check now | run the snapshot on the Mac (cost: see `system-today.md`) |
| MO-23 | Answered / Not answering / Undo | stored per reply, so "Waiting for you" stays correct |
| MO-24 | "Open your post on X ↗" opens the profile | the post's own link |
| MO-25 | "Answer on X ↗" and "Open on X ↗" open x.com | the specific post |

## Example data (tagged "example" on screen, or placeholder)

- **Placeholder handles:** `@builder.one`, `@lab.notes`, `@aus.indie`, `@sec.minded`, `@pixel.tools`, `@ship.daily` and `@builder.two` contain a dot, so they can never be real X handles. `@use_bruno` is real: it's the maker in the real draft, checked 24 Sep.
- **Example content:**
  - the waiting replies and the builders (with "2 mutuals on topic")
  - "Plus 37 greetings…"
  - the first-hour card ("first like came 3 minutes later", `@builder.two`)
  - the proposal (build log, Tue 29 Sep 22:00)
  - the example lesson (24 against 11)
  - the two example captures and the reader question
  - the example tool-verdict draft and its three hooks
- **Real figures from the repo:** the post's cards and swaps, the Results figures, progress figures, the posts list, reply topics, the 68-reply peak and the 12 repeated lines. They're frozen at 24–25 Sep. Every one is traced in `data.md`.
