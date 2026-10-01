# Skills audit, 2026-10-01

Read-through of all 20 skills in `.claude/skills/` against skill-creator's writing guide: explains the reason behind each rule, stays lean, points at `AGENTS.md` instead of restating it, has a trigger description that fits how the skill is actually used. No eval runs. A pilot eval on `format-tool-swap` (3 runs, 21 checks) passed 21 of 21 and told us nothing the read-through didn't, so it was dropped.

An earlier skill review the same day (`reviews/log.md`, 2026-10-01 `fix`) already dropped the Grok mentions, moved tool-swap operations to `background.md`, and ran a before/after eval on `format-tool-swap` (11/11 both). This audit covers what that review did not.

## Checks run

`tests/test_skills.py` (new) passes: every `name` matches its folder, frontmatter parses, every SKILL.md is under 500 lines (longest is 116), every `scripts/*.py` path exists, and no skill file mentions Grok. I also checked by hand that every other repo file the skills name exists (examples, shipped notes, research, reference, reviews). None is missing.

## How the skills are used

- Nine are operator-only slash commands: `apply`, `approve`, `lint`, `next`, `posted`, `ready`, `results`, `snapshot`, `undo-rule`. They run scripts that write to the ledger or git, so they were not run in any test.
- The six format skills are loaded by path from `draft-thread` step 3, using the queue row's `format`. They are not picked by description matching, so their trigger descriptions matter little.
- Only `draft-thread`, `verify-settings`, `hidden-settings`, `jev-card` and `jev-judge-run` depend on description matching.

## Findings

Ranked by value. "Do" means a small edit I would make on a yes.

1. **Do not run the description optimizer.** It targets triggering, and only five skills trigger by description. Their descriptions already name the operator's phrasing. It costs a lot of usage (`claude -p`, three runs per query) for no expected gain.
2. **`hidden-settings` has a dead argument.** Its frontmatter says `argument-hint: "[hook|card|closer|emoji]"`, but the body never uses an argument. Do: drop the hint. It also says "Comparison threads use `format-comparison`" twice; do: keep one.
3. **`format-tool-swap` has a list that renders wrong.** In "Research and fact-check", the line starting `"Settled" choices below are editorial` is indented as a sub-bullet of "A swap with no official page…". It is a separate rule. Do: unindent it.
4. **Rules restated from `AGENTS.md`.**
   - `draft-thread` step 8 repeats "Never create, edit or delete `APPROVED`". Do: keep only the consequence ("Revised cards need `/approve` again before `/ready`").
   - `apply` step 3 repeats the loop's never-change list. Do: point at "What the loop may never change" in `AGENTS.md`. Keep the `APPROVED` and gate names, since `apply` is the one skill allowed to write skill files.
5. **`jev-judge-run` is the heaviest skill** (58 lines, dense, many fixed numbers and dated results). The earlier review already moved the numbers to its README. What is left is the "Before any request" and "Run" checklists, which read as procedure and are the place to cut if the skill is trimmed later. No edit now: the Jev work is in progress (D1–D106 UI project), and trimming it blind could drop a rule that was learned the hard way.
6. **Duplicated character-limit wording.** "Under 280 characters when possible, never over 600" appears in four format skills, and the gate (`post_thread.py` `ROOT_LIMIT`) enforces it. Left as is: each skill must read on its own when `draft-thread` loads only one.
7. **`format-settings` is a pure pointer** to `hidden-settings`, one extra hop. It holds the checklist path that `tests/test_hooks.py` uses. Keep. A merge would touch the test and the hook guard for no gain.
8. **Open dependency, not an edit:** `next` (three places) and `format-tool-swap` (two) call `scripts/x_read.py`, which still calls Grok underneath. When `reviews/factory-drop-grok-plan.md` lands, these five lines change with it. `AGENTS.md` line 28 already says so.
9. **`results` step 5 is a 14-section list in one step.** It works and is operator-only. `next` already moved its weekly work to `weekly.md`; `results` could do the same. Low value, leave unless it gets longer.

## What I would not touch

`approve` (the hook design depends on its exact text and `tests/test_hooks.py` checks its frontmatter), `ready`, `snapshot`, `undo-rule`, `lint`, `posted`, `draft-thread`'s step structure, `verify-settings`, and the five format skills not named above. They are short, say why, and have clear "Done:" lines.

## Proposed edits (each needs the operator's yes)

| # | Edit | Files |
|---|------|-------|
| A | Drop unused `argument-hint`; keep one "comparison" pointer | `hidden-settings/SKILL.md` |
| B | Unindent the "Settled choices" rule | `format-tool-swap/SKILL.md` |
| C | Trim the `APPROVED` restatement to its consequence | `draft-thread/SKILL.md` |
| D | Point `apply` step 3 at the `AGENTS.md` never-change list | `apply/SKILL.md` |

All four are wording only. None changes what a skill does, so none needs an eval. `python3 -m unittest discover -s tests` should still pass afterwards.
