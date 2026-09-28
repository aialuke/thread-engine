# Instruction-file review: results

Scope: `.claude/skills/results/` and the files it points to that no other skill uses. Method: `BRIEF.md` (this folder), using `writing-for-agents` and its `SKILL-MECHANICS.md`. Reviewed 28 Sep 2026; implemented 29 Sep 2026. Fixed: all operator-facing output lengths (operator, 28 Sep). The operator approved all five changes below before implementation.

## Baseline

Baseline source: commit `8fe59ba`; line references below refer to the unchanged baseline. Read `git log -15`, scope history, and recent changes to referenced files. In particular, `ceb5d35` settled sourcing and the post-1 lane exception; `300d2a9` preserved output lengths and corrected the audience reference; `ca71976` and `8fe59ba` settled neighbouring instruction reviews.

| File | Words before | Words after | Sections |
|---|---:|---:|---|
| `.claude/skills/results/SKILL.md` | 931 | 978 | One heading, `Results`; seven ordered steps; 14 weekly-review sections |

Counts use whitespace-separated words, including frontmatter. The skill is not always loaded: `disable-model-invocation: true`; its 35-word description is human-facing under the review skill's mechanics. No always-loaded instruction file changes.

| Baseline step | Action and completion criterion |
|---|---|
| 1 | Import the newest analytics export through `record-export`; ask once if none is from the last seven days. Import completion is implicit in command success; the scope of “once” is unspecified. |
| 2 | Ask weekly for eligibility figures and record them, or continue with daily-read numbers if skipped. Weekly prompting has no explicit tracking criterion. |
| 3 | Run `status` and `evaluate`; read the summary, experiments, lessons, and “last review”. Completion means both commands and all reads finish, but the previous-review selector is ambiguous. |
| 4 | For a direct numbers-only request with no review due, show the last seven days as a short table and stop. The due field is unnamed. |
| 5 | Save the Brisbane ISO-week review with all 14 named sections, each a few lines, retaining each section's limits and operator-approval conditions. Exhaustive coverage is implicit rather than a stated check. |
| 6 | Run `mark-reviewed`, then `commit-data`. Command success is the implicit completion criterion; no explicit saved-report check precedes it. |
| 7 | Give the three most important things in three sentences and the full review's location. |

The weekly sections are Rewards progress, Posts this week, Followers, Replies, Experiment, Lane, Spacing, Your edits, Reader questions, Lanes to review, Rule changes proposed, Reverts proposed, Profile, and PAID → FREE runway. Their names and order remain unchanged.

There are no exclusively used instruction references to edit. The voice, audience, algorithm reference, queue, scripts, summary, lessons, and weekly reviews have other skill consumers. `experiments.md` (30 words, one heading, no ordered steps) is an exclusively referenced generated view; `ledger/activity/` is data. Both are fixed and unchanged, as are scratch/import files. `/next` still follows this skill's existing path; `/apply` still reads the weekly reports.

## Approved and applied

1. **Precise previous-review pointer** (`SKILL.md:17`). Replaced “the last review in `reviews/`” with the most recent weekly review matching `reviews/week-YYYY-Www.md`, treating no match as the first review. Principle: context pointers and completion clarity. Behaviour: unrelated audits and design reviews are not selected as weekly performance context. `/apply` already uses weekly files (`.claude/skills/apply/SKILL.md:13`).
2. **Explicit branch condition** (`SKILL.md:18`). Named `review.review_due` from `status`, retaining an explicit review request as a reason to take the weekly branch. Principle: checkable criteria. Behaviour: the existing short-table exit uses the field supplied by `scripts/loop.py:944`, also used by `/next`.
3. **Weekly-only reads moved after the exit** (`SKILL.md:17–19`). `status`, `evaluate`, and the summary remain before the branch; experiments, lessons, and the previous weekly review are read in step 5. Principle: progressive disclosure by branch. Who needs the moved material: the weekly reviewer, who reaches it at the start of step 5. Numbers-only runs avoid these reads. The 14 section instructions remain in this file.
4. **Stronger use-site reference pointers** (`SKILL.md:23,32`). The reply check explicitly reads the voice's “Replies” section; pin suggestions explicitly read A14 in `reference/x-algorithm.md`. Principle: sharpen context pointers before copying their targets. Behaviour: the reviewer consults the governing references instead of relying on recalled rules. Shared references and existing rules are unchanged.
5. **Saved-review completion check** (`SKILL.md:19,34`). Before `mark-reviewed`, require every section in the saved report, identify unavailable evidence, and use “not enough data yet” where applicable. Principle: completion clarity and exhaustiveness. Behaviour: the review is checked for coverage before its completion is recorded. All output limits remain unchanged.

## Independent read, disagreements, and deferred items

The `codex-delegation` skill launched an independent read without the originating findings. Job `task-mulb9m0d-7fjtg3`, session `01a0e84d-97ff-78e1-b997-61e38aa002c5`, completed in 1m 28s; verdict: used. The first job, `task-mulb8ylg-1dcvrq`, failed during sandbox initialization after two seconds and returned no findings. The successful run was read-only; citations were checked locally.

- **Agreements:** both reviews independently identified changes 1–3. Codex additionally proposed 4–5; the originating reviewer checked and accepted them. The operator approved all five; none of those five was declined.
- **Resolved disagreement:** the originating reviewer initially favoured extracting weekly instructions into a separate file. Codex considered the 14 sections a legitimate peer set and extraction unnecessary. The approved plan keeps them together and moves only prerequisite reads.
- **Deferred:** “ask once” and “once a week” do not specify tracking semantics. Choosing per-invocation, calendar-week, or last-record behaviour could change operator interaction, so neither was changed.
- **Deferred:** user-only invocation versus `/next` reading the file may depend on runtime mechanics. Neither runtime was tested; the flag and caller path remain unchanged, with no claim that the caller is broken.
- **No change:** command examples, safety prohibitions, consent conditions, Grok/Claude distinctions, output lengths, and the dated lane and pin decisions remain operative. Generated files and scripts were not edited.

## Check

`python3 -m unittest discover -s tests`: 173 tests, OK. Diff inspection confirmed preserved frontmatter, seven steps, 14 section names and order, output lengths, commands, approval conditions, and dated decisions. `git diff --check` passed. This is a reporting skill, so no posting-gate run was required. No live workflow command or X call was run. Only the skill and this record are included in the review commit.
