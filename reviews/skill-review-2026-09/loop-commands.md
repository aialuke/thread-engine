# Skill review: loop-commands

Scope: `.claude/skills/{apply,undo-rule,snapshot}/SKILL.md`. Method: `BRIEF.md`. Reviewed 29 Sep 2026. Operator approved every proposal in full.

## Baseline

Words include frontmatter. Before / after.

| File | Words | Steps | Completion criteria before |
|---|---|---|---|
| apply | 131 / 194 | 5 | 1 clear (adopted, rule `none`, else stop). 2 no case for a missing proposal. 3 no diff check. 4 no error branch. 5 "Applied" not tied to success. |
| undo-rule | 100 / 116 | 3 | 1 command run. 2 success line. 3 two errors mapped; "no lesson" and "no applied rule" not. |
| snapshot | 121 / 114 | one paragraph, steps and reference mixed | None. Claimed every failure records nothing. |

Only the description lines load into context (all three are `disable-model-invocation`). Descriptions shrank in all three. Body words rose in apply and undo-rule because stop branches were added.

## Approved and applied

- **A1** apply step 2: proceed only with a proposal naming lesson id, file and exact sentence (`results/SKILL.md:30`); otherwise say what is missing and stop.
- **A2** apply step 3: stop if the target file has uncommitted changes (`loop.py:895-899` commits the whole file's changes); check `git diff` shows only the proposed change.
- **A3** apply steps 4-5: error branch (a commit may exist, needs a Claude Code session); "Applied" only after a clean exit (`loop.py:899-904` commits before saving state).
- **A4** apply step 2: "then make it", so the operator's `/apply` is the confirmation.
- **A5** apply description: dropped the commit and undo mechanics that steps 4-5 carry.
- **U1** undo-rule: "no lesson" and "no applied rule" branches.
- **U2** undo-rule: "Uncommitted edits" ends the turn; rerun only after the operator answers.
- **U3** undo-rule description trimmed.
- **S1** snapshot: two steps, with "done when the operator has its lines or its failure".
- **S2** snapshot: two failure branches. A failed X read records nothing (`snapshot.py:195-199`). A stage failure may be partly written, so run `/next` (`snapshot.py:219-226`, `next/SKILL.md:18-19`).
- **S3** snapshot: cut the sentence on x_api.py, the Keychain keys and loop.py recording; `AGENTS.md` and the script carry it.
- **S4** snapshot description: dropped "runs daily… first thing inside /next"; the launchd job and `/next` call the script, not this skill.

## Declined

None. Kept on purpose: apply step 3's "Never touch…" list (hard guardrail, paired with the positive "Edit only that file"); undo-rule's "Conflicted… needs a Claude Code session" line; snapshot's Keychain and credits remedy, now conditioned on the error text.

## Independent read (Codex, read-only, no findings shared)

Agreed with A1, A2, A3, A5, U1, U3, S1, S2, S3, S4.

Disagreements, resolved by the operator's approval of the plan as written:

- **D1 undo-rule.** Codex: the script labels any failed revert a conflict, so the skill shouldn't assert it, and "Claude Code session" may be the host already. The label and "nothing was reverted" come from `loop.py:918-920`, which is fixed, and the skill relays them. Grok still shares skills until `reviews/factory-drop-grok-plan.md` lands. Kept.
- **D2 snapshot.** Codex: drop the blanket Keychain remedy. No evidence it is wrong. Kept, conditioned on the error text.
- **D3 apply.** Codex: the diff check should also confirm guardrails and headings are intact. Step 3 already forbids touching them. Folded in only "diff is the proposed change".
- Codex did not raise A4 or U2.

## Check

`python3 -m unittest discover -s tests`: 173 tests, OK. No posting skill in scope, so no `post_thread.py --count`. No live command run. No heading or file name another skill points to was changed (`apply`, `undo-rule` and `snapshot` names and paths unchanged).
