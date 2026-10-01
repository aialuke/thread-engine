---
name: hidden-settings
description: >
  Settings-thread beat order, card structure, closer, and emoji budget.
  Research, fact-check, and images are format-settings. Writing is
  /draft-thread. Use for hook beats, card structure, closer rules, or
  /hidden-settings. Comparison threads use /format-comparison.
disable-model-invocation: true
when-to-use: >
  Use for settings-thread format, hook beats, emoji budget, card
  structure, closer rules, or /hidden-settings. Comparison threads use
  /format-comparison.
user-invocable: true
---

# Settings format (Hidden Settings)

This is the `settings` format. Shared voice, truth budget and image rules: `voice/exit-zero.md`. Beat-check: `examples.md` (this folder). Full transcripts: `examples/`.

Open a new hook on the result, then neglect; take the later beats and card texture from the gold. The posted gold opens on neglect and predates that opening.

Comparison threads use `.claude/skills/format-comparison/SKILL.md`.

Rules here change only through an adopted lesson and `/apply` (see `learnings.md`).

Write with `/draft-thread`. Paths with `/verify-settings`.

## Hook beat order

Settings threads. Required, this order:

1. **Result** — the first sentence names the product and the result, so the hook opens on them.
2. **Universal neglect** — the default has sat untouched since setup day.
3. **Scene** — one named person, one room, one failed result, and a purchase they almost made (a number only when sourced).
4. **Expert** — a competent outsider who already knew where to tap.
5. **– no-list** — each skip on its own line, starting with `–`.
6. **Snap** — they changed N settings. Same sitting: same object, same seat, different result. Later result: a second sentence on the same object that names when it shows (next charge, next morning, next evening).
7. **Thesis quote** — one quotation from the expert. The object was not the failure. Name the party who sells the replacement and will not show the free path.
8. **🧵 promise** — `🧵 Here are the N settings that fixed it:`

## Root post

For You shows one post per conversation, and a stranger can only be shown the root (`reference/x-algorithm.md` A1, A2). The root carries the result on its own. Keep the hook under 600 characters, the settings root cap in `scripts/formats.py`: scene and expert may share a sentence, and the no-list may be two or three lines.

N is the number of setting cards, 3 to 7, and it is the number in the snap, the promise and the setting-card count. The thread has N + 2 posts: root, N setting cards, closer. When the queue row names an experiment arm, the arm's post count wins.

## Card micro-structure

One setting per post. `Setting N: Name`.

1. **Title**
2. **Why the default is wrong** — in that same scene
3. **Exact path** — from `PATHS.md` (`Settings → Camera → Preserve Settings`)
4. **One action** — one primary toggle, in verbs
5. **Payoff** — same room / same photo / same call

Skip line when the menu can be missing: `No Main Camera menu? Skip it.`

## Closer rules

- `✓` recap of the setting names, one line
- Same-object line: same phone / same gateway / same wedding. Different result
- Time and money already used in the hook; repeat only those figures
- The closing question asks about the fork that changes which settings matter (model, chip, age, or ISP) and promises which 3 of the N to do first: "Which <model> is yours? The menus differ, and 3 of these <N> matter most on each". Engagement rules: `voice/exit-zero.md` "Asking for engagement". The transcripts in `examples/` use that question. Posted "Reply with…" and "Save this before…" lines predate the rule and sit in HTML comments in those files. `examples.md` shows the same question.

## Emoji budget

| Mark | Where | Count |
|------|--------|-------|
| 🧵 | hook | 1 |
| – | each no-list line | 1 per skip |
| ✓ | closer, on its one recap line | 1 |
| ⚠️ | first Pro-only / model-only caveat | 1 |

## Settings voice

Beats, scene, expert, no-list and same-object rules: `Hook beat order`. The expert is a friend, tech or repair person in the room. The fix was already in Settings.

Banned phrases, farm tells and the truth budget: `voice/exit-zero.md`.
