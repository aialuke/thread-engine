# draft-thread instruction review

Date: 2026-09-29. Scope: `.claude/skills/draft-thread/`.
Status: approved changes applied and committed.

## Method and history

Followed `BRIEF.md` with the installed `mattpocock-skills:writing-for-agents`
skill and `SKILL-MECHANICS.md`; also read the local writing-for-agents and
skill-creator guidance. This session is in Default mode; review and proposal
precede edits. The independent read uses the installed `codex-delegation` skill.

Read `git log -15` and relevant history. Settled changes include:

- `ceb5d35` (2026-09-24): operator testing is optional for tool-swap; research
  suffices. Preserve the once-only optional offer and claim-level evidence rule.
- `300d2a9` (2026-09-28): settings examples use real questions; shipped gold's
  engagement requests must not be copied.
- `ca71976` (2026-09-28): always-loaded instructions and voice consolidation.
- `e3e2d8d`: verification supports research candidates before cards and accepts
  operator-run claims with dated attribution and an artifact.
- `8fe59ba`: next ends with the operator's `/draft-thread <slug>` handoff.

Other working-tree changes are outside this review and remain untouched.

## Baseline

One file: `SKILL.md`, 55 lines, 587 whitespace-separated words including
frontmatter; 525 body words. Three Markdown headings: `Draft thread`, `Argument`,
`Steps (this order)`. No supporting files in scope.

This is an invoked skill, not an always-loaded body. Its description is 33 words;
the separate `when-to-use` value is 17 words. Those are source-field counts, not
a claim that every host loads both. Invocation metadata remains unchanged.

| Order | Step | Existing completion criterion |
| --- | --- | --- |
| 1 | Contract | All five named files read this session. |
| 2 | Topic | Slug, format and any experiment arm written down. |
| 3 | Format | Shape, research rule, image rule and checklist are known. |
| 4 | Research, then write | Candidate list exists; `01-hook.md` does not. |
| 5 | Verify | `PATHS.md` and/or `CLAIMS.md` exist. |
| 6 | Files | Files exist; card count matches format, hook and arm. |
| 7 | Queue | Row says `drafted`; instruction also requires `draft:` path. |
| 8 | Gate | `APPROVED` is absent, while the instruction forbids touching it. |
| 9 | Preview | Implicit: every card and X count, unresolved rows, image needs,
  and exact closing handoff printed. |

## Proposed changes

All evidence below refers to the unchanged baseline skill unless stated otherwise.
No file, heading, anchor, format skill or checklist target is renamed or removed.

### P1 — Make format reference loading conditional

Evidence: line 30 says to read “every file it points to”; format files mix
required contracts with conditional references and historical material.
Principle: context pointers and progressive disclosure.

Replace that clause with: “Read `.claude/skills/format-<format>/SKILL.md`, its
required contract and checklist, and references whose stated conditions apply
to this draft.” Retain the settings examples and gold pointers and their
precedence caveat. Replace “are known” with “Done: the applicable shape,
research/verification mode, image rule and checklist are identified, including
any arm override.”

Behavior: follow each format's routing without treating every mention as an
unconditional read. Nothing moves: the drafting agent reaches the same targets
from step 3 when their branch applies.

### P2 — Resolve the folder before research and support reuse

Evidence: lines 35 and 40 require both an absent hook and reuse of an existing
folder; line 37 uses `<folder>` before line 40 defines it.
Principle: co-location and clear completion criteria.

Move the dated folder selection/reuse instruction from step 6 into step 2:
“Resolve `drafts/YYYY-MM-DD-slug/` using today's Australia/Brisbane date; reuse
it if it exists.” Include the path in Topic's completion criterion. Replace
step 4's hook-absence criterion with “Done: candidates and their evidence are
recorded for verification; no card prose has been written or revised this run.”

Behavior: a fresh draft and a revision both finish research before writing;
existing cards are not deleted to satisfy a negative file-existence criterion.
The folder convention stays in this file, beside the topic that determines it.

### P3 — Route evidence requirements through the selected format

Evidence: line 34's “No official source → the item is omitted” conflicts with
operator-run evidence in `format-build-log/SKILL.md` → Research and fact-check,
`format-tool-verdict/SKILL.md` → Research and fact-check, and the optional tested
claim in `format-tool-swap/SKILL.md` → Research, and an optional test.
Principle: single source of truth and precise context pointers.

Replace the blanket sentence with: “Collect the evidence the format requires:
official sources for vendor claims, and the operator's account plus real proof
for claims about their own runs. Verification decides which claims reach cards.”
Keep the Material question pointers and the tool-swap optional test offer.

Behavior: preserve fail-closed evidence requirements without rejecting the
already-authorized operator-evidence branch. This clarifies existing rules;
it introduces no new acceptable source type. Detailed evidence rules remain
in the format and verify-settings skills.

### P4 — Make verification and queue completion exhaustive

Evidence: line 38 checks only that a file exists, even if incomplete or stale;
line 49 checks only status, despite line 48 also requiring the folder pointer.
Principle: completion criteria, clarity and demand.

Replace Verify's completion criterion with: “Done: every candidate and required
format claim is accounted for in `PATHS.md` and/or `CLAIMS.md`, with evidence
and applicability or a retained `VERIFY` row; only supported `high`/`medium`
claims are eligible for cards.” Replace Queue's criterion with “Done: the row
says `drafted` and `draft:` points to this folder.”

Behavior: an existing evidence file or a half-updated queue row is insufficient.
The verification procedure remains behind `/verify-settings <folder>`.

### P5 — Preserve existing approval markers without implying current approval

Evidence: lines 51–52 prohibit touching `APPROVED` but require its absence;
line 40 permits reusing a folder that could already contain one.
Principle: clear completion criteria and positive target beside hard guardrails.

Keep the no-create/edit/delete prohibition. Replace “A hook blocks it anyway.
Done: `APPROVED` is absent.” with “Done: this run has left `APPROVED` untouched.
Any revised cards need the operator's `/approve <slug>` again before `/ready`.”

Behavior: never delete an existing marker to satisfy the step, and never treat
an old marker as approval of revised cards. Approval hooks and gate remain fixed.

## Retained without change

Keep all headings, format and checklist paths, supported format names, card
shape reminders, truth restrictions, preview count command, exact closing
handoff, and invocation metadata. The body is short enough that another
reference file would add navigation without a useful split. Do not review or
edit the format skills in this session.

## Independent read

Codex read-only, blind to the primary findings and to this record: job
`task-mumgpfl1-dsfrb1` (runtime default model and effort, 1m26s, verdict: used).
An earlier job never returned a result. Codex confirmed every format,
checklist, hidden-settings and verify-settings pointer resolves.

| Topic | Result |
| --- | --- |
| P1 conditional format loading | Agreed. |
| P2 / research criterion | Partly agreed. Codex also wanted the Material answers and real proof in the step 4 criterion; folded in. |
| P3 evidence routed through the format | Codex left the old "No official source" line unchanged; primary kept P3 because the operator-evidence formats conflict with it. Wording keeps the omission rule ("No qualifying source"). |
| P4 verify and queue criteria | Agreed on Verify; Queue is primary only. |
| P5 existing `APPROVED` | Disagreed. Codex: stop the run when the folder holds `APPROVED`. Primary: continue, leave the marker untouched, require `/approve` again, since the gate already refuses cards changed after approval. Applied the primary. |
| Move triggers from `when-to-use` into `description` | Codex only. Declined: invocation metadata is fixed and Codex did not claim `when-to-use` is unsupported. |
| Append verify-settings path at step 5 | Codex only, optional. Declined: the pointer resolves. |

## Decisions and validation

Approved and applied 2026-09-29: P1, P2 (with Codex's Material-answers
addition), P3, P4, P5. Declined: the two Codex-only items above. No heading,
file name or anchor changed.

Post-edit validation: `python3 -m unittest discover -s tests`: 173 passed.
`python3 scripts/post_thread.py drafts/2026-09-24-paid-free-developer --count`:
exit 0; hook 329, shout-out 95 X characters. Count-only.
