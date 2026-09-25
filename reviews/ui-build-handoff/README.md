# Thread Engine UI: build handoff

**For:** the agent planning the build with the operator.
**Pinned to:** mock version 22 (https://claude.ai/artifact/8zaBcxWAknJaXWkReQQPqg), source `ui/mock/`, decisions D1–D36 in `reviews/ui-direction.md`, reviews `reviews/ui-review-2026-09-24.md` and `reviews/ui-review-2026-09-25.md`. Written 25 Sep 2026.
**Your job:** help the operator decide how to build this, by grilling them on the open questions in `build-questions.md`. This handoff doesn't recommend a build path; that's the operator's call.

## 1. What this is, in one paragraph

Thread Engine is a local "factory" for the @exitzerocode X account. It researches, drafts, fact-checks, gates and measures posts, and it learns which formats grow the account. Today it runs as slash commands in Claude Code or Grok Build on the operator's Mac (`AGENTS.md`). The operator doesn't code and doesn't want to type commands. The UI turns every command into a button (D2), phone first (D31), with the Mac app later. Posting itself always stays manual: the operator pastes into X.

## 2. Who it's for and what success means

- **The operator:** an Australian builder making an idea → script → finished-video pipeline with AI agents. They post around 06:00 Brisbane, usually from the phone. They have no coding knowledge and use no scripts ([`reference/audience.md`](../../reference/audience.md), operator notes).
- **The goal:** compelling content, then engagement, then growth. The concrete target is X's Original Content Rewards: 500 verified followers and 500K Verified Home Timeline impressions within 90 days. On 24 Sep the account stood at 27 of 500 and 337 of 500K.
- **Shared later (D3):** built to a standard fit to share, but for one operator first.

## 3. Rules the build can never break

Each is a MUST with its source. `decisions.md` §Invariants has the full list.

1. **MUST NOT post, schedule, or call any X write API.** The operator presses Post on X (AGENTS.md).
2. **Only the operator approves.** Approval is the operator's own hold on the button (D13, D24) or the typed `/approve <slug>`. No model, script, scheduled job or agent may approve, press the button, or call what it calls (AGENTS.md; `ui-direction.md` build notes). The hooks enforce this today for the approval file; the build must extend it to the button.
3. **The gate stays.** `scripts/post_thread.py` refuses changed-after-approval cards and every rule listed in AGENTS.md. The UI shows the refusals; it never bypasses them.
4. **Truth budget, fail closed.** Every figure is sourced this session; an unconfirmed claim stays out of the cards (`voice/exit-zero.md`).
5. **Loop state changes only through `scripts/loop.py`**, never by hand, and lessons change rules only through `/apply` (AGENTS.md).
6. **X keys never enter a session.** They stay in the Mac's Keychain, read only by `scripts/x_api.py`.
7. **Other people's data stays private and local** (`loop/followers/`, `ledger/raw/api/`); the shared mock uses dotted placeholder handles.
8. **The operator stays no-code,** in setup and maintenance too. Anything they'd have to do by hand must be a button or an agent's job.
9. **Settled decisions:** hold to approve with no Touch ID or Face ID (D13, D24), and the Cortex chat stays (D31). Don't reopen them.

## 4. How the pieces fit (macro to micro)

| Level | Read | What you get |
|---|---|---|
| The system today | `system-today.md` | What runs where, every command and script, hooks, data stores, costs, tests |
| Decisions | `decisions.md` | D1–D36 with what each means for the build, the rules the build can never break, what's deferred |
| Open questions | `build-questions.md` | Constraints C1…, threat model, questions Q1… with options and trade-offs, a suggested order for the grilling |
| Behaviour | `state-machine.md` | The post's life, posting steps, time states, working line, sheets and focus |
| Wiring | `wiring.md` | Each UI action → command/script → inputs, outputs, side effects, cost, failure, progress |
| Screens | `screens.md` | Every screen, section and control: purpose, conditions, handler, real wiring, states, accessibility |
| Controls | `inventory.yaml` | The same controls, one entry each, for checking coverage (`ui/mock/test/controls.py --check`) |
| Data | `data.md` | Every figure on screen traced to its source, the data model the UI needs, what isn't stored yet |
| Look | `design-system.md` | Tokens (light and dark), type, components, motion, accessibility rules |
| Fakes | `mock-only.md` | Everything the mock fakes and what the real app does instead |
| The mock itself | `ui/mock/README.md` | Source layout, how to build, serve and test it |

## 5. The UI in brief

Five tabs on iPhone and a sidebar on Mac (D8): **Today** (the next post, progress, replies, capture, plan next: D5, D27), **Posts** (up next, drafts, capture, queue, posted: D25), **Replies** (waiting for you, builders, worth joining: D12, D28), **Results** (Growth, Posts, Replies: D18, D22, D27, D30), **Cortex** (lessons, weights, guardrails, experiments, open questions, and the chat: D6, D7, D9, D10, D11, D14, D31). A round profile button opens Settings and health (D8, D23, D35). Each command shows a live working line while it runs (D4). Every flow has its unhappy paths designed: refused, not found, found with differences, found twice, failed copy, a fact-check that couldn't confirm a claim, a command that fails, and one that needs an answer.

## 6. Where things stand (25 Sep)

- The mock is final after two full reviews. Every finding is fixed and re-tested (`ui-review-2026-09-25.md` §11).
- **Live posting continues while the build happens:**
  - The PAID → FREE series runs one post every other day to about late October.
  - The developer-tools post is drafted and waiting for approval.
  - Experiment rules are due about 8 Oct; experiments stay paused until then.
  - The daily snapshot's 26–29 day final read must work by 16 Oct.
  The build must not disrupt any of this.
- **Known outside issue:** `scripts/loop.py` `render()` puts two reads taken hours apart into one `ledger/SUMMARY.md` row (`ui-review-2026-09-25.md` §6). It's a job for a loop session.

## 7. Conventions in this folder

- **IDs:** `SCR-*` screens, `SHT-*` sheets, `NAV-*`, `MAC-*`, `CMP-*` components, `CTL-*` controls, `CMD-*` existing commands, `FN-*` UI-only functions, `DATA-*` data items, `MO-*` mock-only items, `C*` constraints, `Q*` open questions, `D*` decisions.
- **Mock vs real:** "mock" is what version 22 does, and "real" is what the built app must do.
- **Sources:** every claim cites a file (`path:line`) or "operator note". When this folder and the repo disagree, the repo wins; flag the difference.
