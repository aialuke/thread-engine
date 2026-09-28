# Instruction-file review: shared brief

Each review session gets its scope from the operator's prompt and follows this brief. Start in Plan mode.

## Method

1. Load the `mattpocock-skills:writing-for-agents` skill.
2. Read `git log -15` and any recent commit touching files in your scope or files they point to. Other sessions may have changed neighbouring files; treat committed changes as settled.
3. **Baseline.** For each file in scope, record words, sections, the ordered steps, and each step's completion criterion. For always-loaded files, record the total loaded each turn.
4. **Review** each file against the skill's principles. For every proposed change give the principle, the evidence (`file:line`), and the behaviour it should change. When material moves, name who needs it and where they will reach it afterwards. "No change" is a valid result for any file.
5. **Independent read.** Run Codex read-only through the `codex-delegation` skill on the same files and the skill's principles, without your findings. Compare, and list agreements and disagreements.
6. **Operator approval.** Present each proposed change with its evidence, and the disagreements. Apply only the changes the operator approves.
7. **Check.** Run `python3 -m unittest discover -s tests`. When your scope includes a posting skill, also run `python3 scripts/post_thread.py --count` on one existing `drafts/` folder to confirm the gate still runs.
8. **Record** the baseline, the approved changes, the declined ones and the disagreements in `reviews/skill-review-2026-09/<scope>.md`.
9. **Commit** only the paths in your scope plus your record: `git add <paths>`, then a conventional commit.

## Shared working tree

Other review sessions may run at the same time in this folder.

- Stage only your own paths.
- Keep every file name, heading and anchor that another skill points to. When a change would rename or remove one, list it for the operator instead of applying it.
- When a test fails on a file outside your scope, report it and leave that file alone.

## Fixed

These keep their meaning; changes are to wording, placement and load:

- the `/approve` gate and its hooks, `scripts/post_thread.py` and its refusals, the truth budget, fail-closed fact-checks, the no-X-writes rule, the banned phrases, and the rules on engagement requests;
- the operator's settled decisions, cited with a date;
- generated files (`experiments.md`, `learnings.md`, `ledger/SUMMARY.md`), which only `scripts/loop.py` writes;
- scripts, which are unchanged.

Skills are still shared with Grok until `reviews/factory-drop-grok-plan.md` lands. Run no live command (`/next`, `/ready`, `/posted`, snapshot). Do not post or write to X.
