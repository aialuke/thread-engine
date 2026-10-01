# Code smells: scripts/ (2026-10-01)

Second run of `/code-smell-detector` today, scope `scripts/` (16 files, 278 functions), plus check 5 over the skills (section 5). It replaces the first run's report. Read-only; nothing was changed. Thresholds and their sources are in `.claude/skills/code-smell-detector/SKILL.md`.

Measured with `ast`. Complexity is an approximation of McCabe (ifs, loops, except, ternaries, comprehensions, extra and/or operands). This run also ran Ruff (`C901,PLR0915,PLR0913`) to compare, and the approximation runs high: Ruff gives `dispatch` 17 (mine 30), `merge_policy` 16 (23), `card_refusals` 15 (21), `main` 13 (14), and Ruff does not flag `account_lines`, `process` or `render` at all. Ruff's numbers are the primary measure and my `ast` counts are leads: my statement count also runs high (`dispatch` 64 against Ruff's 56), and Ruff's `PLR0915` does not flag `post_thread.py:main` at all, where I counted 55. Physical line counts are used only for file length.

Counts: file length 2 over the 1000-line error (none in the 500-1000 advisory band); function length 32 over the 24-line flag by physical lines, 23 by statements, and 1 over the 50-statement error by Ruff (`dispatch`; `main` by my count only); complexity: Ruff flags 2 over 15 (`dispatch` 17, `merge_policy` 16) and 8 are over 15 by my higher count; parameters 2 over 5; duplication 1 finding and 2 notes; comment 1. Findings counted: 21, one per file, function, parameter list, duplicate group, comment block or skill-text issue at error level: 2 files, 9 functions (2 confirmed by Ruff, 7 leads), 2 parameter lists, 1 duplicate group, 1 comment block, 6 skill-text findings (1 confirmed, 5 leads; section 5). Check 5 (contradicting text) was run in a later pass over the skills, not over `scripts/`. The numbers match the first run, so nothing in `scripts/` moved a threshold today, including the `x_read.py` edits.

Ranked by how often the file changes (commits): `loop.py` 29, `payloads.py` 11, `snapshot.py` 8, `post_thread.py` 7, `x_api.py` 6, `x_read.py` 5, `jev_referee.py` 1. `jev_referee.py` has one commit, so its history is too short to rank by; it is ranked by size, and its findings matter least because the code rarely changes.

## 1. Oversized files

- `scripts/loop.py`, 1079 lines, 29 commits (error: over 1000). Four jobs, from its section markers: a `Repo` class and file helpers, about 38 `cmd_*` commands, the readable views (`render`, `account_lines`), and the CLI parser. It is also the most-changed file, so this is the finding that costs most.
- `scripts/jev_referee.py`, 1321 lines, 1 commit (error: over 1000). Six jobs: policy loading, shell command parsing, classification, state redaction and building, the Jev call, and receipts and hook output.

## 2. Long or complex functions

Over the 50-statement error: `jev_referee.py:1138 dispatch` (92 lines, Ruff PLR0915 56, C901 17, confirmed) and `post_thread.py:332 main` (104 lines, 55 statements by my count, Ruff C901 13, not flagged by PLR0915; a lead).

Over the complexity-15 error by my count, highest first: `loop.py:870 account_lines` 35, `snapshot.py:99 process` 34, `jev_referee.py:1138 dispatch` 30, `jev_referee.py:165 merge_policy` 23, `post_thread.py:180 card_refusals` 21, `loop.py:915 render` 19, `jev_referee.py:555 _force_push` 16, `jev_referee.py:688 classify` 16. Ruff's C901 flags only four functions at all in this group (`merge_policy` 16, `dispatch` 17, `card_refusals` 15, `main` 13), because it does not count comprehensions or and/or operands. `account_lines`, `process`, `render`, `_force_push` and `classify` score high only on my count: they hold many conditional expressions and comprehensions, so treat their complexity as a lead.

What I read (this run read more than the first):
- `dispatch` runs the whole referee hook: it saves prompts, finds the hard rule, loads policy, chooses a fork, applies the skip rules, builds state, calls Jev and applies policy. It builds and appends a receipt seven times with the same `append_receipt(receipts, _receipt(fork, event, policy, state, ..., True, True, reason), None)` shape, differing only in state and reason. That repeated shape is the main reason it is long. This is measured, from the code.
- `process` records interactions, followers, new posts, snapshots, non-organic marks, activity, missed posts and experiment events in one body. Those are separate jobs that all talk to `loop.py`.
- `account_lines` builds the follower summary, the table by kind and the topic ranking in one function. It is 43 lines, so its high score is about branching, not length.
- `main` in `post_thread.py` handles argument checks, count mode, the approval gate, format checks, the copy output and the JSON output.

I did not read `merge_policy`, `card_refusals`, `render`, `_force_push` or `classify`, so for those the size is the only evidence.

Top 10% (repo-relative; cut is 26 lines and complexity 11, to rank, not to pass or fail). Longest after the above: `jev_referee.py:1232 dry_run` (58 lines), `loop.py:529 cmd_open_experiment` (47), `snapshot.py:180 run` (47), `loop.py:1018 build_parser` (44, 42 statements, Ruff 15), `experiments.py:68 evaluate_rounds` (42). `build_parser` is a flat list of subcommand declarations, so it is acceptable as it is.

## 3. Long parameter lists (over 5)

- `jev_referee.py:1100 _receipt`, 9 parameters, 1 statement (Ruff PLR0913). Probably builds a record from named fields, which makes it acceptable, but `dispatch` calls it seven times with two `True, True` flags and a reason in fixed positions, so the call sites are hard to read.
- `x_api.py:113 oauth_header`, 6 parameters, 10 lines (Ruff PLR0913). Not read.

Four or five parameters (a prompt to group, not a finding): 16 functions (checked by `ast`, excluding `self` and `cls`). The 8 with five: `snapshot.py:99 process`, `x_api.py:162 request` and `278 search`, `jev_referee.py:969 build_state` and `1001 post_jev`, `loop_core/payloads.py:146 snapshot_from_payload`, `jev_design_vote.py:88 post`, `loop.py:374 _note_person`. The 8 with four are not listed individually (`jev_design_vote.py:143 main`, `jev_referee.py` `_scan_shell` `_git` `commit_is_skippable` `_commit_state`, `experiments.py` `evaluate_rounds` `next_slot`, `x_api.py:217 timeline`). An earlier version of this report listed 7 of the 8 and left out `_note_person`.

## 4. Duplicated logic

- Finding: `jev_referee.py:366-412`, `_drop_sudo`, `_drop_command` and `_drop_env` are three copies of the same loop (skip leading flags, `--` ends the options, some flags take a value). They differ only in the set of value-taking flags, and `_drop_env` also skips `NAME=value`. Three copies is a finding by the Rule of Three. This is the referee's command parsing, where separate explicit functions may be deliberate, and I can't tell from the code. A smaller change would be one helper taking the set of value-taking flags and a skip-assignments switch, checked against the referee tests first.
- Note (second copy), checked by reading both sites: `x_api.py:272` and `:302` hold the same four lines, the `users` dictionary from `body["includes"]`, the `client.items` and `client.cost` updates, and the return of posts with their author. The two functions differ only in the request path and parameters. That is a note, not a finding.
- Note, corrected: `jev_referee.py:264 _rm_invocation` and `:456 _cd_target` share a `while index < len(argv):` scan with the `--` stop, which collects the remaining arguments. The three `_drop_*` functions use the same loop but return the rest of the arguments instead. So the loop skeleton appears five times in two variants (three returning, two collecting), not three times. The finding above still stands; the group is larger than it said.
- Inferred, not found by script: the seven receipt calls in `dispatch` (section 2).

The script matches exact text only, so it misses copies with renamed variables; this run found no other identical 4+ line block repeated three times in `scripts/`, but that does not prove none exist.

## 5. Contradicting text

Read in full: every `SKILL.md` in `.claude/skills/` (except this skill), `voice/exit-zero.md` and `AGENTS.md`. Not read: the `checklist.md` files, `format-tool-swap/background.md`, `next/weekly.md`, `next/experiment-list.md`, `hidden-settings/examples.md` and `reference/audience.md`, so conflicts that live only in those are unchecked. Most pairs I compared were consistent; the six below are the ones that were not, or could drift. `research/jev-test/conflict_items.json` pins 20 sentences by line number, and any fix that adds or removes lines above a pinned one moves it; those are flagged.

1. **Plan mode (confirmed contradiction).** `next` (line 75): "End with `Next: /draft-thread <slug>` for the slug the operator accepted (it starts in Plan mode, so the operator sees the plan first)." `draft-thread` (line 16): "`AGENTS.md` asks for Plan mode first on non-trivial work; if the session is not in Plan mode, say so once and continue." I searched `.claude/settings.json`, `.claude/hooks`, `.claude/agents` and `scripts/` for anything that makes `/draft-thread` start in Plan mode and found nothing, so `next` promises a behaviour nothing enforces. Smaller fix: change `next` to "ask the operator to start it in Plan mode". Not on a pinned line.
2. **Closing question vs the short formats (lead, inferred).** `voice/exit-zero.md` ("Asking for engagement"): "End a thread's closer, and a standalone post whose format has no fixed ending, with one real question that only a reader of that post could answer." It names three fixed endings (the tool-swap root, the shout-out, the comparison root). `format-single-tip`, `format-build-log` and `format-tool-verdict` define their shape (a skip line, a proof, a limit) and say "Under 280 characters when possible", with no question in it. Followed to the letter, a single-tip, build-log or tool-verdict draft could omit the question the voice rule requires. The gate does not enforce a question: I found only the length limits and `SOLICIT_RE` in `post_thread.py`. I haven't tried a draft to see what an agent does. A fix would add lines to `voice/exit-zero.md` above lines 44-70, which moves pinned items B01-B08.
3. **Trial-phase state held in two skills (restated state).** `next` (line 38) and `results` (the Lane bullet) both say, while the operator trials formats, the lane share is "reported, not enforced". `AGENTS.md` says current state belongs in its Current state block, "skills point here instead of restating it", but that block has no line for the format trial, so the state has no exit condition and two copies. Smaller fix: add one Current state line and have both skills point to it.
4. **The 600 and 280 limits repeated in six places (drift risk, no conflict today).** The values agree with the gate constants `ROOT_LIMIT = 600` and `SHORT_LIMIT = 280` (`post_thread.py:33-34`). They are restated in `format-build-log` (line 31, pinned as B11), `format-single-tip`, `format-tool-verdict`, `format-tool-swap`, `hidden-settings` and `draft-thread` step 3. Changing a limit means six edits plus the gate.
5. **"The gold predates the rule" stated in three files (drift risk).** `draft-thread` step 3, `hidden-settings` (twice) and the header of `voice/exit-zero.md` each explain that the gold threads' opening and closing lines predate the current rules. They agree today, but each is a place for the explanation to go stale.
6. **Other people's data via `x_api.py` (wording gap, lead).** `AGENTS.md`: "Other people's posts and research come from `scripts/x_read.py` ... It is the one route to X evidence." `results` runs `python3 scripts/x_api.py mentions` and reads other people's replies; `format-tool-swap` and `voice/exit-zero.md` ("Makers") run `x_api.py user <handle>` on another account. The mentions step also says to leave their text out of the review, so nothing is cited; the handle check reads a profile, not a post. Either `AGENTS.md` should say account lookups and mentions are the exception, or the skills should say why they are allowed. Not on a pinned line.

## 6. Comments standing in for clarity

`post_thread.py` lines 389-399: a 10-line comment sketching the X API write calls ("v1 does not call any of this"). The repo's rule is that it never posts or calls an X write API, so this is a plan for code the project does not intend to build. It is probably a lead for deletion; your call.

## What is acceptable

`build_parser`, `_receipt` and the large literal tables are long or wide but flat. `jev_referee.py` is oversized but has one commit, so splitting it buys little until it changes.

## Fixed (later the same day)

The sections above describe the code before these fixes. Operator choices: split `loop.py` only, fix the Ruff-confirmed functions and accept the five lead-only ones, add a closing question to the three short formats, end the format trial on 2026-10-08.

| Finding | Before | After |
|---|---|---|
| `loop.py` size | 1079 lines | 874 lines; the views moved to `scripts/loop_core/views.py` (223 lines, pure text builders), `render` is a short reader and writer |
| `dispatch` | Ruff C901 17, PLR0915 56 | no Ruff finding; skips, config loading and the Jev call are separate functions |
| `_receipt` | 9 parameters | 5; the verdict fields travel in an `Outcome` |
| `merge_policy` | C901 16 | no Ruff finding; two helpers, same error messages |
| `_drop_sudo`, `_drop_command`, `_drop_env` | three copies of one loop | one helper, `_after_options`, with thin wrappers |
| `post_thread.main` | C901 13 | no Ruff finding; `build_parser()` and `request_refusal()` extracted; the 10-line comment about X API write calls deleted |
| Plan mode claim in `next` | said `/draft-thread` starts in Plan mode | asks the operator to start it in Plan mode |
| Closing question | missing from single-tip, build-log, tool-verdict | a Question beat in each format and a box in each checklist |
| Format-trial state | restated in `next` and `results` | one line in `AGENTS.md` Current state (ends 2026-10-08); both skills point to it; `next` step 3 rewrites it when the pause is lifted |
| 600 and 280 limits in six files | no check | `tests/test_skills.py` fails if a skill states a limit that differs from `ROOT_LIMIT` / `SHORT_LIMIT` |
| "Gold predates the rule" | in three files | `draft-thread` step 3 now points to `hidden-settings` |
| `x_api.py` for other people's data | conflicted with "x_read.py is the one route" | `AGENTS.md` names the two exceptions (`mentions`, `user <handle>`) |

Ruff (`C901,PLR0915,PLR0913`) findings in `scripts/`: 9 before, 4 after.

**Accepted, not fixed:**
- `jev_referee.py` split (operator's choice; one commit, a hook). It is now 1335 lines.
- `account_lines`, `snapshot.process`, `card_refusals`, `_force_push`, `classify`: lead-only complexity, re-measured with Ruff (only `card_refusals`, 15, is flagged, at the flag level).
- `build_parser` (15) and `parse_commit` (12): flat declarations and a branchy parser, flag level only.
- `x_api.oauth_header` (6 parameters): they mirror the OAuth 1.0a inputs and a test calls it directly.
- `_rm_invocation` and `_cd_target`: they collect arguments instead of returning the rest, so they keep their own loops.
- `x_api.py:272/302`: two copies, a note.

**Checks run:**
- 434 tests pass (432 before, plus the limit test and a `--dry-run` test).
- Fifteen `dispatch` scenarios (every exit path, including active-mode deny and a failed Jev call), 19 `merge_policy` inputs, 16 wrapper-stripping inputs and `post_thread.py --help` gave identical output before and after.
- 60,000 random argument lists gave the same result from the old and new wrapper-stripping functions.
- `render` regenerated `ledger/SUMMARY.md`, `experiments.md` and `learnings.md` with no change.
- `dispatch` and `merge_policy` run on the real hook entrypoint without error.
- A missed caller turned up late: `dry_run` still called `_receipt` with the old arguments, and no test covered it. It is fixed and `tests/test_jev_referee.py` now has a `--dry-run` test.
- Pinned sentences: `research/jev-test` pins `format-build-log` line 31, which moved to 32 (re-pinned in `conflict_items.json` and `conflict_judge.py`). `research/layer-1-switches-profiles.md` cites `AGENTS.md` lines 43, 46 and 51, which shifted by one or were already past the end; it is a dated research note and is left as it was.
