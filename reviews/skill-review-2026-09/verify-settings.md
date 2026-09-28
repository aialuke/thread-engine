# Verify-settings skill review

Scope: `.claude/skills/verify-settings/SKILL.md`. Implemented 29 Sep 2026 from the operator-approved five-change plan, using `writing-for-agents` and `skill-creator`. No reference files added. Original line citations below refer to the skill at baseline commit `1824671`.

## Baseline

609 words, three sections (`Argument`, `Paths mode`, `Claims mode`), six paths steps and five claims steps. The description has **21 words**, not 28. Description load belongs to discovery; the body is loaded on demand. Cross-runtime loading in Grok and Claude Code was not measured; word counts are not token measurements.

| Original step | Original completion criterion |
|---|---|
| Paths 1, lines 28–30 | Every candidate has a version line or unknown; unknown fails closed. |
| Paths 2, lines 32–34 | Each kept row has a live official URL; forums and memory excluded. The preceding instruction asks for control name, full path and models or OS versions. |
| Paths 3, lines 36–50 | Every candidate is a row in `PATHS.md`, using the fixed schema and confidence definitions. |
| Paths 4, lines 52–54 | Every gated row is labelled in Notes; the preceding instruction also requires prose naming every gated row. |
| Paths 5, lines 56–58 | No guessed menu in `PATHS.md` or any card; unresolved rows stay and cards stay off the ready list. |
| Paths 6, lines 60–61 | Tick Verify boxes when the checklist exists; deliver `PATHS.md`; any `VERIFY` confidence means the draft is not ready. |
| Claims 1, line 66 | One row for every factual claim in the cards; research candidates and format-required rows are not explicit. |
| Claims 2, line 67 | Vendor pricing, feature, spec or support page opened this session; reviews, forums and memory excluded. |
| Claims 3, lines 68–80 | Write the fixed `CLAIMS.md` table with confidence definitions; tested requires operator confirmation, and operator-run evidence requires a dated source plus an artifact. No explicit exhaustive completion check. |
| Claims 4, line 81 | Retain unconfirmed claims as `VERIFY` rows, remove them from cards and never soften them to keep them. |
| Claims 5, line 82 | Tick checklist verify boxes, without an existence or satisfaction condition. |

## Approved changes

| Change | Principle and original evidence | Intended behavior and destination |
|---|---|---|
| 1. Pre-card inputs | Exhaustive completion criteria; line 66 inventories only cards. | Claims step 1 now inventories research candidates and selected-format verification rows before cards exist; rechecks include every factual claim in existing cards. Unassigned `Card` cells stay blank. Inventory stays in step 1, with format requirements reached through the existing format-skill pointer at line 18. |
| 2. Evidence routing | Co-location; vendor selection at line 67 is separated from the operator exception at lines 79–80. | Move the unchanged operator-confirmation and operator-run artifact rules into claims step 2 beside vendor-page selection. Evidence selectors encounter both routes together. Optional tool-swap testing remains optional. |
| 3. Completion criteria | Clarity and demand; lines 34, 54, 61 and 82 allow URL-only checks or indiscriminate ticks. | Paths step 2 checks control names, full paths and applicability; step 4 checks both gated Notes and prose. Claims step 5 accounts for every inventoried claim with evidence/applicability or retained `VERIFY`, and excludes unsupported claims from cards. Both stop steps tick only satisfied boxes when a checklist exists. Existing unresolved-row safeguards remain in place. |
| 4. Format ownership | Single source of truth; line 53 duplicates the warning-emoji rule. | Remove only the emoji sentence. Applicability Notes and prose remain in paths step 4. Settings writers reach the emoji budget through the existing line-18 format pointer → `format-settings/SKILL.md:12` → `hidden-settings/SKILL.md:69`; no new reference or relocated copy is needed. |
| 5. Discovery | Context-pointer coverage; description at lines 3–6 mentions only a draft. | Description now covers candidate/existing draft verification and changed Settings paths. This remains discovery metadata; `when-to-use`, `argument-hint` and `user-invocable` stay unchanged for invocation and compatibility. |

## Independent review and preserved ambiguities

The approved handoff records independent review `task-mulbiyoi-2ei6dl`: substantive agreement on all five changes, with its description count corrected from 28 to 21. No proposals declined. This implementation records that prior review; it does not claim a new independent review was run.

Two ambiguities remain intentionally unresolved:

- Readiness: paths mode says any `VERIFY` confidence makes the draft not ready, while unresolved candidates must remain recorded and unsupported material stays out of cards. Whether a discarded candidate should block the whole draft is not settled here. The existing readiness sentence remains unchanged.
- Operator-run confidence: the `high` and `medium` definitions refer to what a page states, while operator-run evidence can use an artifact. No new confidence mapping for that exception is introduced; the confidence definitions remain unchanged.

## Decisions consulted and validation

Read the latest 15 commits and the skill's recent history, including `ceb5d35` (operator testing optional), `5bebe57` (tool-swap format) and `9c51264` (build-log/tool-verdict).

Consulted the 23–24 Sep series decision record in `reviews/paid-free-session-2026-09.md`, including its rule that active format and voice instructions take precedence. The 24 Sep 2026 decision in `format-tool-swap/SKILL.md:63–70` makes research sufficient and tests optional; an unsupported claim still needs evidence or is cut. Its required verification rows at lines 74–83 explain the pre-card inventory requirement. Also consulted `reviews/skill-review-2026-09/BRIEF.md` for fixed safeguards and scope.

- Supplied pre-edit baseline: 173 tests pass; read-only character count passes on `drafts/2026-09-24-paid-free-developer`.
- Post-edit `python3 -m unittest discover -s tests`: **173 tests pass**.
- Post-edit `python3 scripts/post_thread.py drafts/2026-09-24-paid-free-developer --count`: passes; `01-hook.md` 329, `02-shoutout.md` 95. The existing over-280 notice is informational; cards were not edited.
- `git diff --check`: passes. Inspected the diff against all five approved changes: headings, filenames, schemas, mode defaults, confidence definitions and invocation/compatibility metadata preserved. Operator confirmation, artifact requirements, fail-closed behavior and fixed project safeguards preserved.
- Generic `skill-creator/scripts/quick_validate.py` rejects existing frontmatter keys `when-to-use`, `argument-hint` and `user-invocable`. This validator's allowed-key set does not cover the preserved compatibility metadata. No metadata or validator changes made.
- No live operator commands, approval-marker changes, X writes or unrelated working-tree edits. Only this record and the skill are included in the commit.
