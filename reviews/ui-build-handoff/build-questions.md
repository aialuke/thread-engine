# Handoff: build constraints, threat model, open questions

For the agent strategising the build of the Thread Engine UI (button interface over the existing
CLI/skills system, iPhone first, Mac later). Read alongside `decisions.md`. Every option below is
presented neutrally — the operator wants to be grilled and decide the build path themselves, so
this file does not rank or recommend a stack, an architecture, or a security model.

## 1. Hard constraints (C1…)

Any build path must satisfy all of these. They are not up for the grilling session — they define
its boundaries.

| # | Constraint | Source |
|---|---|---|
| C1 | No X writes, ever — not from the UI, not from any agent the UI drives. The only proven guarantee today is that the Keychain keys are Read-scoped and X refuses writes from them. | `AGENTS.md`:13; `reference/x-api.md` P1 |
| C2 | Only the operator approves. Today the one path is the typed `/approve <slug>`, caught by a hook that matches a literal person-typed prompt and writes `APPROVED` with the cards digest. D2 and D13 want the hold button to approve too, which `AGENTS.md:14` currently forbids: the operator must change that rule first, and the button then needs an operator-only path at least as strong as the typed one. The typed `/approve` stays as backup and as the accessible route (C12). | `AGENTS.md`:14; `.claude/hooks/approve.py`; D2, D13, D24; `ui-direction.md` build notes |
| C3 | No model, script, or scheduled job may approve — and the build must stop agents from reaching the Approve button or calling whatever it calls, not just from writing the file. This is an explicit open problem, not yet solved by any existing mechanism. | `ui-direction.md`:69; `decisions.md` §2 (D13/D24, do not reopen) |
| C4 | Truth budget: every figure the UI shows or Cortex states must be sourced in-session (an official page, `PATHS.md`/`CLAIMS.md`, or the operator). No invented dB/%/$ figures. | `voice/exit-zero.md`:41–43 |
| C5 | Fact-checks fail closed: an unconfirmed claim is refused/flagged, never silently passed. | `AGENTS.md`:18–20; `.claude/skills/verify-settings` |
| C6 | The gate's refusals (`scripts/post_thread.py`) must be the real logic, not a UI reimplementation that can drift from it. | `AGENTS.md`:51; `ui-review-2026-09-25.md` #3 (the mock's own reimplementation let refusable content through) |
| C7 | Loop state (`loop/state.json`, `ledger/*.json`, generated `.md` views) changes only through `scripts/loop.py`, from any execution surface the build adds. | `AGENTS.md`:16; `.claude/hooks/guard_approved.py` |
| C8 | X API keys never enter a session; only `scripts/x_api.py`, in its own process, reads the Keychain. No new backend, log, or agent may read Keychain values directly. | `reference/x-api.md`:5; `AGENTS.md`:13 |
| C9 | The operator does not code or run scripts. Every step is a slash command or button; the agent runs everything else. Whatever the build looks like, setup and ongoing use must stay button/command-driven for the operator. | `AGENTS.md`:9; operator note |
| C10 | Other people's data — follower ids, raw API responses, reply text, DMs-equivalent — stays local and out of anything meant to be shared (an artifact, a shared build). | `AGENTS.md`:46; `reference/x-api.md`:48–50; `ui-review-2026-09-24.md` C.10 |
| C11 | Don't disrupt the posting cadence or the calendar: experiment rules are due ~2026-10-08 (experiments paused until then), final 26–29-day reads must be working by 2026-10-16, and the PAID → FREE series runs one post every other day into late October with a post already drafted and approved-pending. | Operator note |
| C12 | Screen readers (VoiceOver, Switch Control) send a tap, not a hold, so they cannot trigger a hold-to-approve control. The operator's call (25 Sep) is that the typed `/approve` is the accessible route, and it must keep working. **Open:** typed `/approve` exists only in a Mac CLI, so there's no accessible route on the iPhone yet; any route must also satisfy C2. | Operator note, 25 Sep; `ui-direction.md`:66 |
| C13 | Vendor prices shown anywhere in the UI (including a Cortex summary) keep the vendor's own currency label; never convert to AUD. | `decisions.md` D36 |
| C15 | One writer at a time across processes: the UI's runner, the 20:00 launchd snapshot and interactive CLI sessions all run read-modify-write `loop.py` commands, so they need one shared lock or queue. | `scripts/loop.py:99-112`; `scripts/snapshot.py` |
| C16 | Account-specific values (handle, city, time zone, vocabulary) are configuration, not constants, even for one operator (D3). | `reviews/ui-direction.md` D3 |
| C14 | D13/D24 (press-and-hold Approve, no biometric step) and D31 (Cortex chat ships) are closed. A build plan that reopens either is answering a question the operator already decided. | Operator note; `decisions.md` §2 |

## 2. Threat model

### Assets

| Asset | Where it lives today |
|---|---|
| X API keys | macOS Keychain, service `thread-engine-x`; read only by `scripts/x_api.py` |
| Approval capability (what turns a draft into something postable) | The `APPROVED` marker file per draft, written only by `approve.py` |
| Drafts (pre- and post-approval card text) | `drafts/<date>-<slug>/`, plain files on disk |
| Other people's data | `loop/followers/` (follower ids), `ledger/raw/api/` (raw responses), reply text not yet stored anywhere tracked |
| Loop state (experiments, lessons, applied rules, ledger) | `loop/state.json`, `ledger/*.json`, generated `.md` views — writable only via `loop.py` |
| The clipboard | Currently `pbcopy` on the Mac, used to carry a card into X |

### Actors

| Actor | Trust level | Notes |
|---|---|---|
| The operator | Trusted principal | No-code; every action is a typed command or (in the future) a button |
| Headless agents (Claude Code, Grok Build) running the project's skills, possibly with computer-use/browser tools | Untrusted for anything gated (C2, C3) | The 24 Sep review's core finding: agent sessions on this Mac already have tools that can press and hold a screen button, or call an endpoint directly |
| Other people's posts and replies (ingested via Grok's X tools, `scripts/x_read.py`, or a future Cortex read of mentions) | Untrusted input, treated as data not instruction today | `scripts/x_read.py` checks every post Grok returns against the X API by id before use; nothing analogous exists yet for a Cortex chat reading live replies |
| Anyone with network access to the Mac (once a phone-to-Mac bridge or remote service exists) | Untrusted until authenticated | No such surface exists today (`ui-review-2026-09-24.md` C.1: "nothing can run from the iPhone today") |

### Attack paths and what exists today to stop each

| # | Path | What exists today | Gap |
|---|---|---|---|
| T1 | An agent (with computer-use/browser tools, or by calling an endpoint directly) presses/holds the UI's Approve control. | `guard_approved.py` blocks an agent from writing a path named `APPROVED` (`SHELL_MARKER_WRITE`, direct `path_values` check) and from shelling out to `grok`/`claude`/`codex` with a prompt starting `/approve` (`SHELL_NESTED_APPROVE`). | Neither check covers a UI button's own call path — "whatever it calls" isn't specified because that call doesn't exist yet. This is C3/D24's open problem, not yet solved by anything in the repo. |
| T2 | Injected instructions in a reply, mention, or other people's post reach Cortex chat or a drafting step and get treated as instructions rather than data. | `scripts/x_read.py` checks every Grok-returned post against the X API by id before it's used, and drops unchecked/invented ones (`reference/x-api.md` P14). D14 states, as a decision, that Cortex "discusses the point but never writes it" on a reply. | D14 is a UI/voice decision, not an enforced control — there's no code today that sanitises or isolates untrusted reply text before it reaches a live Cortex chat (flagged as a live risk in `ui-review-2026-09-24.md` A.6: "a reply it reads could inject one [an action]"). |
| T3 | Remote access to the Mac (a phone reaching a Mac-side service, or anyone else on the network reaching it). | Nothing — no remote surface exists yet. | Entirely open; see Q7. |
| T4 | Wrong or stale content copied to the clipboard and pasted live. | The gate refuses bad cards before `POST.txt`/copy is generated (`scripts/post_thread.py`); the 25 Sep review's fix for #19 makes the app compare the found live post against the approved text rather than assume a match. | Still a manual paste step; no clipboard-permission model designed for a phone yet (Q5). |
| T5 | An agent or shell command reads the Keychain directly. | `guard_approved.py`'s `SHELL_KEYCHAIN` regex denies `security find-generic-password`/`dump-keychain` in any shell command it sees. | Only covers the two CLI sessions the hook is wired into today; a new execution surface (a Mac-side service, a different process) needs the equivalent enforced independently. |
| T6 | An agent writes directly to loop state or the generated `.md` views, bypassing `loop.py`. | `guard_approved.py`'s `LOOP_STATE` regex denies writes to `loop/state.json`, `ledger/*.json`, `ledger/SUMMARY.md`, `experiments.md`, `learnings.md`, `ledger/activity/*`, `loop/followers/*`. | Same as T5 — scoped to today's two CLI sessions. |
| T7 | An agent spawns another agent session and feeds it a prompt that types `/approve` on its behalf. | `SHELL_NESTED_APPROVE` regex denies invoking `grok`/`claude`/`codex` with a prompt starting `/appro` + `ve` (deliberately split in source to resist casual grep, `guard_approved.py`:23–24). | Same coverage question as T1 for any new execution surface. |

## 3. Open build questions (Q1…)

Each is genuinely open. Options are listed without ranking; "strains" names which constraint(s)
above (C-numbers) or which threat (T-numbers) an option puts pressure on.

### Q1. Stack for iPhone now, Mac later

**Why it matters:** determines what's possible for push (Q6), clipboard (Q5), offline/background behaviour, and how much of the Mac mock's design system is directly reusable.

| Option | Trade-offs | Strains |
|---|---|---|
| Native (Swift/SwiftUI on iOS, later a native Mac app) | Full access to push, clipboard, background tasks, biometrics if ever revisited; two codebases to maintain long-term; slower iteration; App Store review if ever distributed beyond the operator. | C9 (more setup complexity to keep no-code for the operator); D31 (Mac reuses the same design — a second native codebase risks drift from "built from the same pieces" per `ui-direction.md`:53) |
| PWA / home-screen web app | One codebase for phone and Mac (a browser-based Mac app is trivial once the web app exists); web push works but only after "Add to Home Screen" + permission grant; no biometric API relevant here since D13/D24 excludes biometrics anyway. | C3/T1 (a web app is easier for a computer-use agent to reach and click than a native app sandboxed per-app) |
| Hybrid (e.g. a thin native shell wrapping a web view) | Gets native push/clipboard entitlements with mostly-shared web code; adds a build/signing pipeline; still one visual codebase. | C9 (more moving parts in setup) |
| Something else (e.g. a chat-only interface, no bespoke UI at all) | Not what was speced (the mock exists and D1–D36 assume a button UI), but worth naming as the boundary case. | Would abandon D2 (every command becomes a button) |

**What would decide it:** whether push notifications (D35, Q6) are considered essential for v1; how much native-only OS integration (share sheet, clipboard, background tasks) the operator wants; whether the operator wants the Mac app to literally be "the same pieces" as the iPhone build (D31) or a separate native artifact.

### Q2. How the phone reaches the Mac (and the Mac-asleep-at-06:00 problem)

**Why it matters:** the keys, the clipboard, and the only scheduled job all live on the Mac today (`ui-review-2026-09-24.md` C.1). Posting happens around 06:00 Brisbane, usually on the phone, and the Mac is often asleep at night — the mock's health "failed" state already models "daily check didn't run, probably because the Mac was asleep" (operator note).

| Option | Trade-offs | Strains |
|---|---|---|
| Everything stays server-side on a Mac that must be awake/reachable; the phone is a thin client | Simplest trust model (keys never leave the Mac); directly breaks if the Mac sleeps at 06:00 — the exact failure mode the operator already described. | C11 (must not disrupt the 06:00 posting habit); needs a "Mac unreachable" health state per `ui-review-2026-09-24.md` C.1 |
| Keep the Mac awake / auto-wake on a schedule (e.g. `pmset` scheduled wake, or a `caffeinate`-style always-on posture) | Solves reachability without moving keys off the Mac; a MacBook staying awake overnight has power/thermal/battery-cycle cost, and "always on" is a new operational habit for the operator. | C9 (a scheduled-wake setup is exactly the kind of one-time technical setup the no-code rule wants minimized) |
| Move the always-available piece to something else (a cloud relay, a small always-on server, iCloud/relay sync) that the Mac syncs with when awake | Phone works even when the Mac sleeps; introduces a third place data/keys could live, which the current threat model (C8, T3, T5) says nothing about. | C8 (keys never enter a session — does a relay count as "a session"? undefined); T3 (a new remote surface) |
| Accept that Mac-asleep is a real failure mode and design the UI around graceful degradation (queue the action, show "will run when the Mac wakes", let the operator post manually via the existing CLI as fallback) | No new infrastructure; keeps the trust boundary exactly where it is today; doesn't solve "the phone can act at 06:00 when the Mac is asleep" — it accepts the gap. | C11 if the gap is wide enough to actually delay a post |

**What would decide it:** how often the Mac is actually asleep at 06:00 in practice (an empirical question the operator can answer); whether the operator is willing to change Mac power habits (e.g. never let it sleep) versus wanting the UI to work regardless; risk tolerance for keys or approval-adjacent logic existing anywhere off the Mac.

### Q3. A Mac-side service running headless agents with the project's hooks

**Why it matters:** the commands are currently skills inside interactive Claude Code / Grok Build CLI sessions. A UI implies *something* runs those skills headlessly, on a trigger, with the same hooks (`.claude/settings.json`, `guard_approved.py`, `approve.py`) enforced.

| Option | Trade-offs | Strains |
|---|---|---|
| Claude Code only, run headlessly (e.g. via the SDK / a scripted invocation) | One CLI's hook model to reason about; Claude session usage limits are real — the operator hit them twice this week already, and any headless run from a UI button draws on the same subscription allowance (operator note). | C9 (usage-limit failures need a clear, no-code-friendly UI state); C3 (whatever executes commands is exactly what T1 targets) |
| Grok Build only | Already shares `.claude/skills/` and `.claude/settings.json` with Claude Code per the repo's design; same usage-limit-pressure question for its own balance (README:45 mentions topping up Grok balance already). | Same as above |
| Both, chosen per command or as a fallback when one is rate-limited | Spreads usage-limit risk across two subscriptions; doubles the hook-enforcement surface that must independently satisfy C2/C3/C7/C8 (today's hooks are literally shared between the two — `AGENTS.md`:41 — a new execution path must preserve that). | C7, C8 (twice the surface to keep correct) |
| Neither — no headless execution; the UI is a display/trigger layer that still requires the operator to be in front of an interactive CLI session to actually run a command | Sidesteps usage-limit and hook-duplication risk entirely; largely defeats the point of a phone-first UI (D1, D2) since nothing can run from the iPhone today anyway. | D1/D2 (the decisions this whole build exists to satisfy) |

**What would decide it:** how tight the Claude/Codex/Grok subscription usage limits actually are against expected command frequency (one post every other day plus `/next`, `/results`, replies research); whether the operator wants a single point of failure (one CLI) or redundancy (two, at double the integration cost).

### Q4. How progress streams to the working line (D4)

**Why it matters:** D4 specifies a live line with real step names, not a spinner or fake progress bar — and the 24 Sep review already found the mock's version used canned text and unrealistic durations (`ui-review-2026-09-24.md` C.9).

| Option | Trade-offs | Strains |
|---|---|---|
| The headless agent (Q3) emits structured step events (e.g. to a log file or local socket) that the UI polls or streams | Requires instrumenting the skills/scripts to emit named steps, not just final output; works for both native and web clients once there's a channel (SSE, WebSocket, polling) to the phone. | Depends on Q2 (the phone must reach whatever emits these events) |
| Parse the CLI's own stdout/transcript in real time | No new instrumentation in the skills; fragile — a reworded skill or a Claude Code UI change breaks the parser. | — |
| No live step names — a generic "working" state with a static description of the command | Simplest; violates D4 directly ("shimmering text naming the real step"). | Would not satisfy D4 |

**What would decide it:** whether it's acceptable to touch the skills/scripts to add step-emission, or whether the build must treat them as a black box.

### Q5. Phone clipboard vs `pbcopy`

**Why it matters:** posting (D17) relies on copying a card and pasting it into X; today that's `pbcopy` on the Mac. A phone has its own clipboard and its own permission model for programmatic clipboard writes.

| Option | Trade-offs | Strains |
|---|---|---|
| Native clipboard APIs on the phone (write directly from the app) | Works offline from the Mac's own clipboard state; requires the card text to already be on the phone, i.e. depends on Q2's data path. | Depends on Q1 (native has broader clipboard API access than a web app) |
| Web Clipboard API from a PWA | Works, but requires a user gesture and, on iOS Safari, has tighter restrictions than native; still needs the card text delivered to the phone first. | Depends on Q1, Q2 |
| Keep `pbcopy` as the only copy path and have the phone just display the card for manual copy-paste (no programmatic clipboard write) | No new clipboard code; slower for the operator at 06:00 (exactly the friction D17 was designed to remove). | Undercuts D17's stated goal |

**What would decide it:** the Q1 stack choice (native vs web materially changes what's available) and how much manual-copy friction is acceptable at 06:00 given D17 already exists specifically to remove friction from this step.

### Q6. Push notifications (D35)

**Why it matters:** D35 specifies two off-by-default notifications (a 10-minute pre-post reminder, a shout-out-window nudge). Web push has a specific iOS requirement.

| Option | Trade-offs | Strains |
|---|---|---|
| Native push (APNs) | Full reliability, works regardless of whether the web app is open; requires native app (Q1) and a push-sending backend somewhere. | Depends on Q1, Q3 (something must trigger the push at the right time — likely the Mac-side service or a cloud relay) |
| Web push from a home-screen PWA | Works on iOS only after "Add to Home Screen" + explicit permission grant — an extra setup step for the operator to complete once. | C9 (a permission-grant flow is a one-time setup cost, consistent with C9's "setup" carve-out but still a step) |
| No push for v1; rely on the operator opening the app | Removes D35 entirely for v1; the "Remind me" toggle on Today (D35) would have nothing to do. | Doesn't satisfy D35 as specified |

**What would decide it:** whether D35 is a v1 requirement or can slip; the Q1 stack decision (native vs PWA) directly gates which push mechanism is even available.

### Q7. Authentication / remote access security

**Why it matters:** T3 in the threat model is currently wide open — nothing today authenticates a phone (or anyone else) to a Mac-side service, because no such service exists yet.

| Option | Trade-offs | Strains |
|---|---|---|
| A private tunnel/VPN between the operator's own devices only (e.g. a personal mesh network, SSH tunnel, or an OS-level "Handoff"-style private channel) | No public attack surface; setup is a one-time technical step (tension with C9); still needs a design for *what* is authenticated — the person, or just the device. | C9 (setup complexity); doesn't by itself solve T1 (an authenticated device can still run an agent with computer-use tools) |
| A hosted service with account-based auth (the operator logs in from the phone) | Standard, well-understood pattern; means keys/logic exist on infrastructure beyond "this Mac", which nothing in the current threat model (C8) has been evaluated against. | C8's scope is currently "the Mac" only — extending trust to a hosted service is a scope change the operator would need to explicitly accept |
| No remote access at all — the phone only ever talks to the Mac when both are on the same local network | Simplest trust boundary; directly fails the "iPhone everywhere else" requirement (D1) whenever the operator isn't home. | D1 (works on both, "iPhone everywhere else") |

**What would decide it:** how literally D1's "everywhere else" needs to hold (does "everywhere" include cellular data away from home?); whether the operator is willing to extend the trust boundary beyond "this Mac" (C8's current scope) to a hosted relay.

### Q8. Protecting Approve from agents (D24's open build problem)

**Why it matters:** this is the single most safety-critical open question. T1 in the threat model is unsolved by anything in the repo today.

| Option | Trade-offs | Strains |
|---|---|---|
| The UI's Approve control, when tapped/held, doesn't directly mutate anything — it sends the literal typed `/approve <slug>` string into a real interactive CLI session as if the operator typed it, so the existing hook (`approve.py`) is the actual enforcement point unchanged | Reuses a mechanism already proven to fail closed (`approve.py`:70–77); still requires solving *how* the UI proves the tap was a human's, not an agent driving the same UI surface — the hook trusts "this came through UserPromptSubmit", which an agent with computer-use tools could also trigger by clicking the same button. | Doesn't fully close T1 by itself — a computer-use agent clicking a UI button that types `/approve` is indistinguishable from the operator clicking it, unless something else identifies the actor |
| A narrow credential that only the operator's own device holds (a device-bound secret the headless agent processes can never read), checked between the hold and the write. No biometric prompt: biometric approval is out of scope (D13/D24) | Could close T1 more completely; adds key management on the phone. | Needs the operator's sign-off that it isn't a biometric step |
| Process isolation: the execution environment that can trigger Approve is architecturally separated from the environment(s) running headless drafting/research agents, so no agent process ever has the capability to reach the Approve control at all | Removes the risk at the architecture level rather than the UI level; constrains Q3's design (can't freely run "both CLIs, whichever's available" in the same context that also serves the Approve UI). | Depends heavily on Q3's answer |
| Accept that this problem isn't solvable at the UI layer today and keep the UI's Approve button cosmetic/disabled, routing all real approval through the typed CLI command as the only actual gate, for v1 | No new risk introduced; directly contradicts D2 ("every command becomes a button, `/approve` included") for this one command. | D2 |

**Before any option:** `AGENTS.md:14` allows only the typed `/approve` to create `APPROVED`. Every option except the last needs the operator to change that rule, recorded as a decision, before the build wires a button.

**What would decide it:** whether the operator considers a UI Approve button that's indistinguishable-from-a-human-tap an acceptable residual risk (given the hold is already framed as a failsafe against *accidents*, not adversarial agents, per D13's stated rationale); how Q3's execution architecture is designed, since several options depend on it.

### Q9. Storing data the UI needs that isn't stored today

**Why it matters:** several decisions assume data that the current ledger/loop schema doesn't capture.

| Data | Needed for | Current state |
|---|---|---|
| Waiting replies with `referenced_tweets` (which post a reply answers) | D12 (Waiting for you / Worth joining split) | Not stored; a 24 Sep check showed all 59 replies as unanswered, which is known wrong (`ui-direction.md`:70) |
| "Worth joining" results | D12 | Ephemeral `/next` chat output today, up to ~$0.15 of X API per search (`ui-review-2026-09-24.md` C.5) |
| Weights as structured data | D6, D11 (Cortex → Weights) | Prose only, inside the format skills (`ui-review-2026-09-24.md` C.8) |
| Preference signals from card edits | D26 | Not recorded anywhere; the weekly review found zero edit signal to date (`ui-review-2026-09-24.md` D.2) |
| Captures and their media | D25 | No capture pipeline exists (Q12) |
| Time to first like | D29 | Not recorded per post today |

| Option (for where new structured state lives) | Trade-offs | Strains |
|---|---|---|
| Extend `loop.py`'s schema and add new subcommands, so everything still funnels through the one script the invariant (C7) already requires | Keeps the existing guard/enforcement model intact with no new surface; is more upfront schema/script work before any UI can show real data. | C7 (satisfies it cleanly, at the cost of doing this work first) |
| A separate, UI-only data store (e.g. a local database the service maintains alongside the ledger) | Faster to build against; creates two sources of truth (ledger via `loop.py`, and this store) that must stay reconciled, and needs its own answer to "does this count as loop state" under C7. | C7 (ambiguous — the invariant names specific paths, not "loop-like data" generically; the build would need to decide whether new data types are in scope or not) |

**What would decide it:** whether the strategy treats "extend the loop schema" as in-scope groundwork before UI work, or tries to layer a UI on the existing ledger as-is and defer this (in which case D12, D25, D26, D29 ship in reduced form or not at all in v1).

### Q10. Live reads and their cost

**Why it matters:** several UI features imply reads outside the once-daily 20:00 snapshot, and live reads cost money per the pricing already measured.

| Live read | Cost | Source |
|---|---|---|
| Mentions, first read of a UTC day | ~$0.06–0.10 | `ui-review-2026-09-24.md` C.3; operator note |
| Timeline read (e.g. "find the post" in D17) | ~$0.001–0.01 | `ui-review-2026-09-24.md` C.4; operator note |
| Re-running the snapshot near the UTC-day boundary (10:00 Brisbane) | Double-charges, since items are billed once per UTC day (`reference/x-api.md` P5) | `ui-review-2026-09-24.md` C.7 |

| Option | Trade-offs | Strains |
|---|---|---|
| Cache aggressively: only re-read live when the UI is actually opened, and never re-trigger a read for data already fetched that UTC day | Minimizes spend; "Waiting for you" and similar views could be stale between opens. | — |
| Poll on a fixed interval regardless of whether the UI is open (needed for push notifications, Q6) | Enables real-time features; costs scale with polling frequency and could approach or exceed the ~$0.25/day baseline spend noted in `reference/x-api.md`:54. | C11 indirectly (spend isn't itself a hard constraint, but the $10/cycle limit and auto-recharge-off setting mean an overspend fails closed rather than silently overcharging — still worth surfacing) |
| A budget/rate-limiter in the service itself that refuses a live read once a daily cap is hit, surfaced to the UI as a state | Prevents runaway cost from a bug (e.g. a retry loop); adds a new failure mode ("read refused, budget hit") the UI must render. | — |

**What would decide it:** what daily live-read budget the operator is comfortable with, given the $10/cycle spending limit and no-auto-recharge setup (`README.md`:55) already caps worst case; how "live" D12/D17/D29 actually need to feel in practice.

### Q11. Cortex chat backend

**Why it matters:** D9/D14 specify a chat that discusses drafts, results, weights, and waiting replies — its model, its data access, and its exposure to untrusted third-party text (T2) are all undecided.

| Option | Trade-offs | Strains |
|---|---|---|
| Whichever CLI the operator already has open drives Cortex too (Claude Code or Grok Build, per D9: "whichever the operator has set up") | Reuses existing subscriptions and hook enforcement; ties Cortex's availability to the same usage limits already a live problem (operator note: hit limits twice this week). | C9 (usage-limit UX); T2 (same injection surface as any other agent read of third-party text) |
| A dedicated, more constrained model/agent just for Cortex, with a narrower tool surface (read-only access to ledger/results, no ability to touch drafts, loop state, or Approve) | Shrinks the blast radius if a reply successfully injects instructions (T2); is more implementation work and a second execution path to keep in sync with the guard hooks (C7, C8). | C3/T1 if Cortex's process ever shares privilege with whatever can reach Approve — argues for the "process isolation" option under Q8 |
| No live third-party data in Cortex at all — it only discusses the operator's own ledger, weights, and lessons, never reads a live reply's text | Removes T2 entirely for Cortex; conflicts with D14's stated design ("on a reply, Cortex discusses the point but never writes it" — implying it does read the reply). | D14 as specced |

**Third-party data:** live replies, handles and ids are other people's data, kept local by design (`AGENTS.md:46`; `reference/x-api.md`). Sending them to an external model is a privacy decision in its own right, separate from injection: keep them out of prompts, use a local model, or record an explicit contract change for redacted processing.

**What would decide it:** how literally D14's "Cortex discusses the point" needs live reply text (versus the operator pasting/summarising it in); whether the operator accepts injection risk (T2) as a residual given the "Cortex suggests, never writes" guardrail is a norm today, not an enforced control (24 Sep review A.6 flagged exactly this gap).

### Q12. Capture pipeline (D25)

**Why it matters:** screenshots, screen recordings, and voice notes need to reach the system, get stored, and (for voice) get transcribed — none of which exists today.

| Option | Trade-offs | Strains |
|---|---|---|
| Native OS share-sheet / share-extension integration (phone) | Lowest-friction capture (share directly from Photos, Screen Recording, Voice Memos); requires native app (Q1) or at least app-level OS integration a plain web app can't get. | Depends on Q1 |
| In-app capture only (record/upload from inside the web or native app) | Works regardless of Q1's answer; adds a step (open the app first) the OS share-sheet route avoids. | — |
| Third-party transcription API for voice notes vs. on-device transcription | On-device (e.g. Apple's Speech framework) keeps audio local, consistent with C10's "other people's data stays local" spirit even though captures are the operator's own; a third-party API sends audio off-device, which needs its own privacy review even though the *content* is the operator's, not a third party's. | C10 is scoped to *other people's* data, so this is a related-but-distinct privacy question the strategy should still name |

**What would decide it:** the Q1 stack choice (share-sheet integration depends on it); whether on-device transcription is good enough quality for the operator's use, or a cloud transcription API is acceptable.

### Q13. Sharing with others later (D3)

**Why it matters:** D3 says the app is "built to a standard fit to share," but everything hard-wires this account. The 25 Sep review explicitly deferred this to the build (E6).

| Option | Trade-offs | Strains |
|---|---|---|
| Design multi-tenancy in from the start (accounts, handles, cities as configuration, not constants) | Avoids a later rewrite; adds real scope to v1 for a feature the operator isn't using yet. | C9 (more setup surface, even if it's a one-time config step per new account) |
| Deploy for one operator account in v1, with account-specific values (handle, city, time zone, vocabulary) as configuration from the first build, and no multi-account features | Honours D3's "don't hard-code what blocks reuse" without building accounts now; sharing later is setup plus the deferred items, not a rewrite. | – |
| Hard-code @exitzerocode now and fork later | Least v1 work; conflicts with D3, which rules out hard-coding that would force a rewrite. | D3 |

**What would decide it:** whether "share it" currently means "show people the app" (content) or "let someone else run their own account through it" (a product) — the 25 Sep review recorded "share it as content first" (E6).

### Q14. How the build keeps the operator no-code, including setup

**Why it matters:** C9 applies not just to daily use but to whatever one-time setup the build requires (installing an app, granting push permission, configuring a tunnel, etc.) — several of the above options (Q6's permission grant, Q7's tunnel, Q1's app installation) introduce setup steps that are new relative to today's "type a command" model.

| Option | Trade-offs | Strains |
|---|---|---|
| Minimize setup to what a normal consumer app install already involves (download, grant a permission or two, done) | Familiar pattern; still real friction the operator wasn't asked to absorb before (they currently don't install or configure anything — the Mac already has hooks trusted per `README.md`:53). | C9 |
| Have the agent (Claude Code, in a session like this one) perform every setup step it technically can, and hand the operator only the steps that require their own device (biometric grant, app store install, notification permission) | Matches how the daily job install already works today ("Ask Claude Code to install it; it copies the file..." — `README.md`:54); keeps the pattern consistent. | Depends on which setup steps genuinely require the operator's own hands (this can't be fully known until Q1/Q6/Q7 are answered) |
| Accept that the very first setup is a one-time exception to "no-code," clearly scoped and explained, after which everything reverts to buttons | Honest about the trade-off rather than pretending zero setup is possible; still asks something new of the operator once. | C9, but as an acknowledged one-time exception rather than a violation |

**What would decide it:** the concrete setup steps implied by whatever Q1/Q6/Q7 choices are made — this question can really only be answered in detail once those are.

### Q15. Testing strategy

**Why it matters:** the mock has already been reviewed seven ways (24 Sep) and code+browser tested (25 Sep) as a *design* artifact; the real build introduces real integration surfaces (headless agents, live reads, push, remote access) that need their own testing approach, and the repo already has a test convention (`tests/`, `python3 -m unittest discover -s tests`) to either extend or diverge from.

| Option | Trade-offs | Strains |
|---|---|---|
| Extend the existing `unittest`-based `tests/` suite to cover new scripts/service code, keeping one test runner for the whole repo | Consistent with `AGENTS.md`:58 and how `scripts/loop.py`, `snapshot.py`, hooks are tested today; unittest is a reasonable fit for backend/service logic, less natural for UI/interaction testing. | — |
| A separate test suite/tooling for the UI layer (whatever framework fits the Q1 stack choice — e.g. XCTest for native, Playwright for web) alongside the existing Python `unittest` suite | Matches each layer to its natural tooling; means "run the tests" is no longer one command, a small but real change to the maintainer workflow in `AGENTS.md`. | — |
| Adversarial review as a standing practice (the pattern already used for the mock: multiple reviewer angles, a code pass, a browser pass) extended to the real build before each milestone ships | Has already found a Blocker-class bug (25 Sep review #1: an edited card could post without re-approval) that unit tests alone might have missed since it was a cross-state interaction bug; is labor-intensive per round. | — |

**What would decide it:** whether the operator wants ongoing adversarial reviews (as used for the mock) to continue into the real build, and at what cadence, versus relying primarily on automated tests; this is largely independent of the other questions and could be decided at any point.

### Q16. Calendar fit

**Why it matters:** the operator has a live posting cadence and two hard dates. A build that consumes the operator's attention or breaks the pipeline around either date has a real cost beyond the UI itself.

| Fixed point | Detail |
|---|---|
| ~2026-10-08 | Experiment rules (API plan step 5) are due; experiments are paused until then |
| ~2026-10-16 | The daily run's 26–29-day final read must be working by this date |
| Ongoing into late October | PAID → FREE series posts one every other day; the developer-tools post is drafted and approved-pending |

| Option | Trade-offs | Strains |
|---|---|---|
| Build entirely outside the existing CLI/skills path (a new, additive layer) so the current `/next → /draft-thread → /approve → /ready → /posted` cycle keeps running unmodified throughout the build | Zero risk to the posting cadence or the two dates; likely means the UI can't actually call real commands until it's finished, so there's a long period where it exists but doesn't do anything real. | — |
| Build incrementally against the live system, with each piece (e.g. Today's view, then Post, then Posting) wired to real data/commands as it's finished | Faster to get something real in the operator's hands; each increment is a chance to break the live posting flow around 8/16 Oct if not carefully isolated (e.g. via C6, reusing the real gate rather than a reimplementation). | C6 (a half-built UI reimplementing gate logic instead of calling the real script is exactly the risk 25 Sep review #3 found) |
| Pause/slow the build itself around 8 and 16 Oct specifically, to avoid any risk during those windows | Directly protects the two dates; adds calendar complexity to the build's own schedule. | — |

**What would decide it:** how much slack the operator has around 8 and 16 Oct specifically (are these hard deadlines with no room for a bad day, or soft targets); whether the build strategy from Q3 onward treats "call the real script" as non-negotiable for anything shipped before those dates.

## 4. Suggested order of questions for the grilling session

Ordered by dependency — later questions assume answers to earlier ones — not by preference. Q16 is placed first as a gate on the whole session's ambition, since it bounds how much can safely be built before the two fixed dates; the strategist may prefer to revisit it last as a sanity check instead.

1. **Q16** — calendar fit: how much build risk is acceptable before 8/16 Oct, and does that argue for additive-first or incremental-against-live.
2. **Q1** — stack for iPhone/Mac: gates what's technically available for nearly every question after this.
3. **Q3** — the Mac-side headless service and which CLI(s) run it: defines what actually executes commands.
4. **Q2** — how the phone reaches the Mac, including the asleep-at-06:00 case: depends on Q3 existing, and its answer shapes Q7.
5. **Q7** — authentication/remote access security: depends on Q2's chosen bridge mechanism.
6. **Q8** — protecting Approve from agents: the highest-stakes question, best answered once Q3 (execution architecture) and Q7 (auth) are settled, since several of its options depend on both.
7. **Q4** — how progress streams to the working line: depends on Q3 (what emits events) and Q1 (what channel the client can receive on).
8. **Q5** — phone clipboard vs `pbcopy`: depends on Q1.
9. **Q6** — push notifications: depends on Q1 and Q2.
10. **Q9** — storing data the UI needs: largely independent, but best scoped once the execution architecture (Q3) is known, since it decides whether new state lives in `loop.py`'s schema or elsewhere.
11. **Q10** — live reads and their cost: depends on Q9 (what's being read live) and interacts with Q16's budget concerns.
12. **Q11** — Cortex chat backend: depends on Q3 (which CLI/agent) and directly extends the Q8 threat-model discussion (T2).
13. **Q12** — capture pipeline: depends on Q1 (native share-sheet vs in-app).
14. **Q14** — keeping the operator no-code through setup: can only be answered concretely once Q1, Q6, Q7 are settled.
15. **Q13** — sharing with others later: lowest urgency per the operator's own review notes (E6: "leave for the build... share it as content first"); best discussed last since its answer doesn't gate anything else.
16. **Q15** — testing strategy: can be decided at any point once Q1/Q3 are known; placed last because it's about how the rest gets validated, not what gets built.
