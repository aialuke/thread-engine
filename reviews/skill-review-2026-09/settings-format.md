# Settings-format skill review

Scope: `.claude/skills/format-settings/` (SKILL.md, checklist.md) and `.claude/skills/hidden-settings/` (SKILL.md, examples.md). Reviewed 29 Sep 2026 against `writing-for-agents` and `BRIEF.md`. `examples/` transcripts untouched.

## Baseline

| File | Words before | Words after | Shape |
|---|---|---|---|
| format-settings/SKILL.md | 153 | 129 | 7 bullets |
| format-settings/checklist.md | 201 | 220 | 5 groups, 14 boxes |
| hidden-settings/SKILL.md | 685 | 634 | intro, 8 hook beats, Root post, 5-part card, Closer rules, Emoji budget, Settings voice |
| hidden-settings/examples.md | 929 | 918 | A) Router QoS (8 cards), B) iPhone Camera (7 cards) |

Total 1,968 → 1,901. All four load on every settings run (`draft-thread` step 3). Completion criteria before: "N matches" and the checklist only.

## Approved and applied (all seven)

1. Checklist gate box: "APPROVED is absent" → "this run left APPROVED untouched; revised cards need `/approve` again" (matches `draft-thread` step 8, reused folders).
2. Checklist made exhaustive: `high`/`medium` PATHS rows only; snap N = promise N = card count; later-result snap names when; closer promises which 3 of N; beat list points at `Hook beat order`.
3. Card count owned by `Root post`; loader points to it. `Settings voice` reduced to a pointer (heading kept); almost-purchase detail moved into the Scene beat.
4. Closer rule stated as the target plus a pointer to `voice/exit-zero.md` "Asking for engagement"; the "gold predates this rule" note kept once in `SKILL.md`, and `examples.md:7` keeps its own where the transcripts are pointed to.
5. Loader "Gate extras" line deleted (gate unchanged); Hook beat 1 states the hook opens on product and result; AI-image sentence dropped from loader (owned by `voice/exit-zero.md` Images).
6. `hidden-settings/SKILL.md` intro split; beat-order precedence stated once, positively; comparison routing on its own line; loader Contract says "read … before writing".
7. `examples.md`: card-shape line points to `Card micro-structure`; A labelled historical 8-card count; comparison pointer shortened.

## Declined / not changed

- "Under 600" wording (gate refuses only >600; the stricter target is deliberate).
- `hidden-settings` frontmatter (`argument-hint [hook|card|closer|emoji]`, `when-to-use`, `/hidden-settings`): the body never says what an argument does. Left for the operator's decision.
- Examples staying loaded every run: `draft-thread` step 3 requires them, so no conditional-load claim is made.

## Independent read (Codex, read-only, blind)

Agreed on all seven. Differences: Codex kept a pointer-based handling of the `Most ` gate line, where I removed the loader line and rely on Hook beat 1; it did not flag the argument-hint mismatch, the four-way beat-order duplication (`SKILL.md`, `examples.md`, `voice/exit-zero.md:3`, `draft-thread` step 3) or the off-branch comparison paragraph. `voice/exit-zero.md:3` and `draft-thread` step 3 are outside scope and still restate the precedence.

## Checks

- `python3 -m unittest discover -s tests`: 173 pass.
- `python3 scripts/post_thread.py drafts/2026-09-24-paid-free-developer --count`: runs (329 / 95).
- `git diff --check` clean. All headings, filenames and anchors kept.
