# Prompt audit, 2026-09-28

## Assumptions

- **Scope.** The request named no files, so the scope is the whole repo's prompt surface (inventory below). Skipped: `~/.claude/CLAUDE.md` and `~/.claude/RULES.md` (user-level, outside the project); `.claude/settings.json` (settings files are not read by this audit); the hook reason strings in `.claude/hooks/*.py` (covered by the 24 Sep audit, unchanged in scope).
- **Target model.** Claude Opus 5.5 in Claude Code, the model running this audit. The 24 Sep audit targeted Grok 4.7; Grok was dropped from the product on 26 Sep (D88), but the factory's move off Grok (`reviews/factory-drop-grok-plan.md`) has not happened, so Grok may still read these skills.
- **Non-Anthropic marker.** `scripts/grok_read.py` calls the Grok CLI. It is outside the Claude target, and this audit proposes no switch.
- **Earlier audit.** `reviews/prompt-audit-2026-09-24/`. Its H1, H2, M1–M6 fixes are live in the files. Its low flags L1–L4 still stand and are not repeated here.

## Inventory

- `CLAUDE.md` (imports `AGENTS.md`, `voice/exit-zero.md`, `reference/audience.md`, `learnings.md`, `experiments.md`, `queue/topics.yaml`)
- 17 skills in `.claude/skills/*/SKILL.md`, 6 format checklists, `.claude/skills/hidden-settings/examples.md`
- `drafts/_template/*.md`
- Gold transcripts in `examples/` and `shipped/*/NOTES.md`: shipped records, read as few-shot material. Not edited.
- No request-building code for a Claude model.

## Summary

Three things matter most:

- **`/posted` matches a queue status that doesn't exist (G2-1).** It looks for `status: approved`, but the queue has no such status. Approval is a file (`APPROVED`), not a queue status.
- **The compressed gold still ends on the closers the gate refuses (G1-1).** A caveat line warns against them, but Opus 5.5 copies a concrete example more strongly than it follows a caveat. The draft then fails at `/ready`.
- **CLAUDE.md tells every session to skip the snapshot (G2-3).** The "not available here" line was written for cloud sessions, but CLAUDE.md loads on the Mac too, where `/next` step 1 runs `snapshot.py` every time.

| Group | Findings |
|---|---|
| 1 Dated prompt text | 2 (1c ×1, 1f ×1) |
| 2 Brittle skill and configuration files | 4, plus 4 low flags |
| 3 Tool and skill descriptions | 0 |
| 4 Request config and architecture | not applicable (no Claude request code) |

The pressure-language scan came back clean: no capitalised emphasis, no "think step by step", no prohibition lists without a reason. The 280- and 600-character limits are posting constraints on the post itself, not caps on the model's replies (keep-list 1).

## Findings

| # | Location | Evidence | Pattern | Why | Confidence | Action |
|---|---|---|---|---|---|---|
| G2-1 | `.claude/skills/posted/SKILL.md:14` | "the row with `status: approved` or `drafted`" | Group 2: volatile specifics, contradicted by the repo | The queue's statuses are `queued \| planned \| drafted \| posted \| shipped \| killed` (`queue/topics.yaml:1`). Nothing sets `approved`; `/draft-thread` step 7 sets `drafted` | High | rewrite: "the row with `status: drafted`" |
| G2-2 | `reference/audience.md:46` | "They get relabelled … once `loop.py set-lane` exists." | Group 2: stale fact | `set-lane` exists (`scripts/loop.py:1184`), and `/results` already uses it under "Lanes to review" | High | rewrite: "The weekly review relabels them against the tests above with `loop.py set-lane`." |
| G2-3 | `CLAUDE.md:14` vs `.claude/skills/next/SKILL.md:16` | "X API keys live in macOS Keychain and are not available here. Skip snapshot/metrics that need them." vs "Run `python3 scripts/snapshot.py`. Run it every time" | Group 2: instruction files that contradict each other | Added for cloud sessions (`41f88d9`), but project CLAUDE.md loads in every session. Read literally on the Mac, it tells the model to skip the step `/next` requires. Neither line is a safety rule; the fix states the condition | Medium | rewrite: "In a cloud session the X API keys (macOS Keychain) are not available: skip …" |
| G2-4 | `drafts/_template/thread.md:3` vs `.claude/skills/hidden-settings/SKILL.md:24-35` | `hook: scene, wasted spend, N settings, "nobody was going to tell you"` | Group 2: instruction files that contradict each other | The template comes from the initial import. The newer beat order puts the result first. Nothing references the template today, but anything that opens it gets the old hook | Medium | rewrite: point the comment at the skill's beat order |
| G1-1 | `.claude/skills/hidden-settings/examples.md:7, 41, 72` | "Reply with the gateway model (xFi, XB7, XB8, sticker name) and which of the 8 the menu has." / "Reply with the model — 13, 15, 16 Pro, 17 — …" | 1c: stale few-shot block | Current models match concrete examples more strongly than they follow a caveat. This file is the beat-check `/draft-thread` reads, and the gate refuses "reply with". The shipped transcripts in `examples/` are records and stay as they are | Medium | rewrite: both closers become real questions in the `SKILL.md:60` form; line 7 now points the caveat at the transcripts |
| G1-2 | `.claude/skills/next/SKILL.md:19`; `.claude/skills/results/SKILL.md:35` | "in two or three lines" / "the three things that matter most, in three sentences" | 1f: numeric output ceilings | Numeric caps were tuned against models that padded. "Speak plainly" and "Plain English" already set the register for a no-code operator. This is the easiest hunk to decline if the fixed count is a deliberate UX choice | Medium | rewrite: "briefly" / "what matters most, in plain sentences" |
| F1 | `.claude/skills/draft-thread/SKILL.md:24` | "Read `AGENTS.md`, `voice/exit-zero.md`, `reference/audience.md`, … `queue/topics.yaml`. Done: all five read this session." | Padding (1c) | In Claude Code, CLAUDE.md already imports four of the five. Re-reading them is harmless, and Grok may still need it | Low | flag |
| F2 | `CLAUDE.md:5-7` | `@learnings.md`, `@experiments.md`, `@queue/topics.yaml` | Group 2: load tax | Volatile loop data loads into every session, including `/ready` and `/snapshot`, which never read it | Low | flag |
| F3 | `.claude/skills/next/SKILL.md:12, 46`; `approve/SKILL.md:12`; `results/SKILL.md:27`; `undo-rule/SKILL.md:14`; `AGENTS.md` | "in Grok or Claude Code"; "in a Claude Code session, not here" | Group 2: facts with a known end date | True until `reviews/factory-drop-grok-plan.md` lands. Then every one of these goes stale in one move. Fold them into that plan's edit list | Low | flag |
| F4 | `.claude/skills/next/SKILL.md:35` | "US daylight saving ends on 1 Nov" | Group 2: time-sensitive content | True now. After 1 Nov the line describes a change that has already happened | Low | flag |

## Kept on purpose

- **The banned-phrase list and the gate refusals:** the reason is stated beside them, and code enforces them (1e).
- **Operator attributions ("operator, 24 Sep 2026"):** they are the reason each rule exists and the authority behind "Settled (don't reopen)". That makes them context, not history (keep-list 1).
- **`/draft-thread`'s ordered steps with "Done:" lines:** research before prose and verify before cards are real ordering constraints (keep-list 3; also the earlier L1).
- **`hidden-settings/SKILL.md:60` "predate this rule; don't copy them":** it still guards the shipped transcripts after G1-1.
- **The handle table in the tool-swap skill:** it has a check date and a re-check instruction.
- **Duplicate rules between CLAUDE.md and AGENTS.md** (no posting, APPROVED, loop state, Plan mode): they agree (keep-list 8).

## Proposed diff

`proposed.patch` in this folder has one hunk per finding (G1-1 has three hunks in one file, and G1-2 has two). It applies cleanly to the working tree as of this audit (`git apply --check` passed). Nothing has been applied. The Group 2 hunks are proposed for the operator to confirm and are never applied on a blanket request.

To take all of it: `git apply reviews/prompt-audit-2026-09-28/proposed.patch`. To take some of it: `git apply --include=<path>`, or edit the patch.

## Verification

- **Repo checks, run.** Every path, script subcommand and flag named in the instruction files was checked against the repo. `loop.py` subcommands, `x_api.py` and `x_read.py` subcommands, `post_thread.py --copy/--count` with its `wait:` line and `open -R`, `snapshot.py --ingest`, the x-algorithm refresh rule and every cited file all exist. The only contradictions found are G2-1 and G2-2.
- **Behaviour probes, not run.** For G1-1: run `/draft-thread` on a settings topic before and after, and check whether the closer is a question or a "Reply with…" line. For G2-3: start a local session, run `/next`, and check that step 1 runs the snapshot.
