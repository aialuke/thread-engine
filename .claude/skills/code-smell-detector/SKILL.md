---
name: code-smell-detector
description: >
  Read-only scan of scripts/ and .claude/skills/ for code smells: oversized
  files, long or complex functions, long parameter lists, duplicated logic, and
  skill text that contradicts other skills or AGENTS.md. Writes one report and
  one log line. Fixes nothing.
disable-model-invocation: true
argument-hint: "[path, default scripts/]"
---

# Code smell detector

Plain English to the operator. This skill's only two writes are `reviews/code-smells-YYYY-MM-DD.md` (Australia/Brisbane date) and one line appended to `reviews/log.md`; everything else is read. Never edit code, skills, loop state, `ledger/`, generated views or `APPROVED`. The operator picks which findings to fix, because a smell is a lead to check, not a verdict.

Scope is the path given, else `scripts/` and `.claude/skills/`. Measure with grep, ls, `wc -l` and a read-only `python3 -c` using `ast`. Report each finding as file:line and one sentence of evidence.

## Thresholds

No study gives a universal number, so each one is labelled by where it comes from. Quote the label in the report, so the operator knows how much weight a finding carries.

| Check | Flag | Error | Source |
|---|---|---|---|
| Function length | over 24 lines | over 50 statements | 24: Chowdhury et al., MSR 2022, ~785K Java methods (SLOC, so a physical-line count runs high). 50: Pylint `max-statements` and Ruff PLR0915 default (tool default) |
| Complexity (branches per function, McCabe) | over 10 | over 15 | McCabe via NIST SP 500-235; Ruff C901 default 10 |
| Parameters | over 5 | none; 4–5 is a prompt to group, not a finding | Pylint and Ruff default 5 (tool default). Martin's 3 is opinion |
| File length | over 500 lines (advisory) | over 1000 | Judgment for 500. 1000: Pylint `max-module-lines` (tool default, a page-count heuristic) |
| Duplication | second copy is a note | third copy is a finding | Fowler's Rule of Three (guideline). Identical blocks of 4+ lines are review hints (Pylint `min-similarity-lines`) |

Measure statements, complexity and parameters, not lines: scripts here hold long literal tables and docstrings that inflate line counts. The thresholds above come from Ruff and Pylint, so use their numbers when `ruff` is installed: `ruff check --select C901,PLR0915,PLR0913 --output-format concise <path>`. A finding that Ruff confirms is a finding; one that only your own count raises is a lead, and the report says so. Without Ruff, use `ast`:
- Statements are the `ast.stmt` nodes inside the function, not counting the `def`. This runs higher than Ruff's count, so call it approximate.
- Complexity is 1, plus one for each `if`, `for`, `while`, `except` and ternary. Counting comprehensions and `and` / `or` operands as well runs well above McCabe and Ruff, so keep those out or label the result a lead.
- Count parameters without `self` and `cls`. Use physical lines only for file length.

## Checks

1. **Oversized files.** Name the separate jobs the file holds, from its top-level names (`jev_referee.py` and `loop.py` are the known ones).
2. **Long or complex functions.** Size is a proxy for "does more than one thing", so name the things.
3. **Long parameter lists.** Note when the same group of parameters travels together across several functions.
4. **Duplicated logic.** Two steps. First find candidates: functions with near-identical names or bodies (sibling names like `_drop_x`, repeated loop shapes), and identical runs of 4+ lines by script. The script only matches exact text, so it misses copies with renamed variables; say so in the report rather than claiming none exist. Then read each candidate, count the copies, and say why it is duplicated. Copies that are deliberate or kept apart for a reason are not findings.
5. **Contradicting text.** A skill whose instruction conflicts with another skill, `AGENTS.md` or `voice/exit-zero.md`, or restates a rule `AGENTS.md` says is held there ("skills point here instead of restating it"). Quote both sentences. `research/jev-test/` pins skill sentences by line number, so list any finding whose fix would move a pinned line.
6. **Comments standing in for clarity.** Dense comment blocks that explain what a name or function should say.

Leave out class-based smells (data clumps, primitive obsession, switch-to-polymorphism): this repo is mostly functions, and those suggestions invite over-engineering.

## Reporting

Separate what you measured from what you infer, say when a smell is acceptable (small, stable, rarely touched), and never write a fix as code. A suggestion is one sentence naming the smaller change.

Also list the top 10% of functions by length and by complexity, whatever the fixed numbers say. The studies favour thresholds tailored to the project, and this repo is small, so use the list to rank, not to pass or fail.

List error-level findings in full. For flag-level ones, list the worst 10 per check and give the total ("32 over 24 lines, worst 10 shown"). Say which findings you read and which rest on size alone.

Report layout: a count line per check, then findings grouped by check, ranked by how often the file changes (`git log --oneline -- <file> | wc -l`). When a file has only 1-2 commits the history is too short to rank by, so say so and rank by size instead. State how you counted findings: one per file, function, parameter list, duplicate group or comment block at error level, split into "confirmed by the tool" and "leads". If a report for today's date already exists, overwrite it and replace its log line instead of adding a second. End with "Nothing to fix" when every check is clean. Then append `## [date] code-smells | reviews/code-smells-<date>.md | <n> findings` to `reviews/log.md`, and tell the operator the report needs a line in `research/index.md` (`/lint` flags it otherwise).
