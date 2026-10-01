---
name: lint
description: >
  Read-only check of the repo's documents: files missing from the
  knowledge index, dangling decision/fact references, stale markers.
  Writes one report and one log line. Fixes nothing.
disable-model-invocation: true
---

# Lint

Plain English to the operator. This skill's only two writes are `reviews/lint-YYYY-MM-DD.md` (Australia/Brisbane date) and one line appended to `reviews/log.md`; everything else is read. Never edit loop state, `ledger/`, generated views or `APPROVED`. The operator picks which findings to fix.

Run these checks with grep and ls. Report each as file:line and one sentence.

1. **Unindexed files.** Every file and folder under `research/`, `reviews/`, `reference/`, `queue/` and `receipts/` (skip `__pycache__`, `private/`) must appear in `research/index.md`.
2. **Dangling references.** Every `Dnn` cited outside `reviews/ui-direction.md` exists there; every `An` exists in `reference/x-algorithm.md`; every `Pn` in `reference/x-api.md`. List citers of any that don't.
3. **Marker drift.** "as of Dnn" and "Dxx–Dnn" ranges in `research/` and `reviews/` against the highest `D` in `reviews/ui-direction.md`. Say which docs cite an older log.
4. **Reference headers.** Each `reference/*.md` has `Status:` and `Checked:` lines. A `current` status older than 14 days is flagged.
5. **Stale claims.** Grep for "not yet built" and other claims a later `D` overrides (check the row's text, do not guess). Draft folders in `drafts/` missing `FORMAT`, or claims in `CLAIMS.md` still marked `VERIFY`.
6. **Lessons.** Lesson ids (`L-nnn`) cited in `reviews/` or `shipped/` must exist in `loop/state.json` (read it, never write it).

Report layout: a count line per check, then findings grouped by check. End with "Nothing to fix" when every check is clean. Then append `## [date] lint | reviews/lint-<date>.md | <n> findings` to `reviews/log.md`.
