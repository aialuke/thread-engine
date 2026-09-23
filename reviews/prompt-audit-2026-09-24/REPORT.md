# Prompt audit, 2026-09-24

## Assumptions

- **Scope.** The request named no files, so the scope is the whole repo's prompt surface (inventory below).
- **Target model.** Grok 4.7 through Grok Build CLI 1.0.40, which runs every skill here. This is a non-Anthropic provider, and this audit does not propose switching it. `AGENTS.md` is also read by Claude Code and Codex.
- **Confidence scale.** The audit guide's model-behaviour rules are documented for Claude, not Grok. So no finding here rests on a Claude-only behaviour claim. High means a contradiction, a stale reference, or a gap shown in this repo's own data. Medium means a general contract or architecture pattern.
- **Provenance.** Git history covers one day. The old core (`hidden-settings`, `verify-settings`, `examples.md`) came in with the initial import. Everything else was written on 2026-09-24 for the current model. So the "left over from an older model" patterns barely apply, and the scan confirms it.

## Inventory

- `AGENTS.md`
- `voice/exit-zero.md`, `reference/audience.md`, `reference/x-algorithm.md`
- 17 skills in `.grok/skills/*/SKILL.md`, 4 format checklists, `.grok/skills/hidden-settings/examples.md`
- `drafts/_template/*.md`; gold threads in `examples/`, read as few-shot material by `/draft-thread`
- Hook reason strings the model sees: `.grok/hooks/guard_approved.py`, `.grok/hooks/approve.py`
- No request-building code. Nothing calls a model API directly; `scripts/draft.py` only prints a command.

## Summary

| Group | Findings |
|---|---|
| 1 Dated prompt text | 4 (1c ×1, 1d ×2, 1e ×1) + 3 low flags |
| 2 Brittle skill files | 2 |
| 3 Tool and skill descriptions | 1 |
| 4 Architecture | 2 |

The signal scan came back clean: no capitalised emphasis, no "think step by step", no reply-length caps aimed at model verbosity. The numeric limits (280 and 600 characters) are X posting constraints and a tested variable, so they stay (keep-list 1 and 7).

The three highest-impact findings:
- **The daily snapshot runs an LLM through a fixed script (M1).** Grok parses numbers, writes files and commits, although only the X fetch needs a model. One structured call plus code removes the chances to misread or invent a number.
- **Outside-reply counts are overstated as exact (H3).** The pinned post returned 9 reply authors against 32 replies.
- **Two files disagree on whether the gold threads can override the root rules (H1).** The shipped roots open on "Most …" and run to about 787 characters, which the gate now refuses.

## Findings

| # | Location | Evidence | Pattern | Why it matters for the target | Confidence | Action |
|---|---|---|---|---|---|---|
| H1 | `voice/exit-zero.md:3` vs `.grok/skills/hidden-settings/SKILL.md:16` | "The settings gold transcripts in `examples/` win on disagreement for settings threads only." vs "Settings transcripts win on settings beat order after the opening." | Keep-list 8 exception: duplicates that disagree | The broad version lets the shipped roots override the result-first and 600-character rules, and the gate then refuses the draft | High | rewrite: gold wins only on beat order after the opening |
| H2 | `.grok/skills/hidden-settings/SKILL.md:10` | `argument-hint: "[hook|card|closer|emoji|voice|farm-tells]"` | Group 3: the contract no longer matches what the skill contains | The voice and farm-tell sections moved to `voice/exit-zero.md` today, so `/hidden-settings voice` points at nothing | High | rewrite: `[hook|card|closer|emoji]` |
| H3 | `.grok/skills/snapshot/SKILL.md:14`; `scripts/loop.py` `record-snapshot` | Outside replies are computed from the reply authors search returns | Group 3: stated behaviour does not match actual behaviour | The backfill shows the pinned post with 32 replies and 9 authors returned, yet the summary prints 8 as if exact | High | add: a `repliers_complete` flag, and a leading ≥ in the summary when it is false |
| M1 | `.grok/skills/snapshot/SKILL.md` (whole); `ops/launchd/…plist` | Numbered steps: fetch, parse Engagement lines, write JSON, call `loop.py`, commit | Group 4: an LLM executing a fixed plan | Only the X fetch needs Grok, since no X API key exists. Parsing, file writes, recording and the commit are determined by their inputs and belong in code. Today one model loop runs with `--always-approve` and workspace write access | Medium | replace: `scripts/snapshot.py` with one read-only structured Grok call; the skill and job call the script |
| M2 | `voice/exit-zero.md:19-21`; `AGENTS.md` | Banned phrases and emoji are enforced only as prose | 1d: an instruction that code could enforce | The gate already refuses the similar "your thoughts" and 💬. The rest of the list is just as greppable | Medium | add: gate refusal for the multi-word phrases and three emoji. "unlock" stays guidance, since it is a real settings word |
| M3 | `AGENTS.md:16` | "Never hand-edit them or the generated `experiments.md`, `learnings.md`, `ledger/SUMMARY.md`." | 1d: an instruction that code could enforce | A hand edit to `state.json` can break the experiment rules with no warning. The guard hook already exists | Medium | add: the guard denies edit tools on loop state; shell calls to `loop.py` are unaffected |
| M4 | `voice/exit-zero.md:19-25` | Banned phrases and farm tells listed with no reason | 1e: a prohibition cluster judged by provenance | These are a brand policy, so they stay. The rule is to state the reason beside them | Medium | rewrite: add a one-line reason and say which parts the gate enforces |
| M5 | `.grok/skills/format-tool-swap/SKILL.md:12` | "the account's best root so far" | Group 2: volatile specifics and history narrative | "Best so far" rots with the next post, and the ledger is the source for results | Medium | rewrite: "for shape only", keeping the lesson about the unsourced line |
| M6 | `.grok/skills/draft-thread/SKILL.md:30` | "A settings row also reads … the gold threads in `examples/`." | 1c: example over-indexing | Concrete examples are the strongest signal in a prompt. The gold roots break the current opening and length rules, so the model copies them and the gate refuses the draft | Medium | rewrite: take card texture and beat order from the gold, and the root's opening and length from the format |
| M7 | whole loop | No record of Grok spend per run | Group 4: no token accounting | Every automated run costs money, and nothing here totals it | Medium | add: `ledger/runs.log` records `total_cost_usd` per snapshot run (inside the M1 patch) |
| L1 | `.grok/skills/draft-thread/SKILL.md:18-60` | Nine numbered steps with "Done:" lines | 1c: step choreography | Research before prose and verify before cards are real ordering constraints, so most of the order is load-bearing | Low | flag |
| L2 | `.grok/skills/hidden-settings/SKILL.md:16` | "Posted settings gold opens on neglect. A new settings hook's first sentence is the result…" | 1d: migration-relative phrasing | It explains why the examples differ from the rule, so it is working context | Low | flag |
| L3 | `.grok/skills/format-comparison/SKILL.md:11` | The gold is paired with NOTES "(it lists what not to copy)" | 1c: a gold example that needs negative reading | It works today; a cleaner gold would remove the caveat | Low | flag |
| L4 | `AGENTS.md:10` | "Start non-trivial work in Plan mode." | 1d: an unenforced instruction | `/draft-thread` softens it to "say so once and continue". Nothing checks it | Low | flag |

## Kept on purpose

- **Character limits:** 280 fits a free X account, and 600 is the root rule and an experiment variable. They are format constraints on the artifact, not caps on the model's replies.
- **Tool contract detail:** result caps and paging, the `max_id` method, null rather than zero, raw-file paths. Group 3 says contract detail stays and often grows.
- **The `APPROVED` rules:** they have a stated reason and a hook enforces them.
- **Duplicated beat order:** it appears in `hidden-settings`, `format-settings` and the checklist, and all three agree (keep-list 8).

## Proposed diff

The patches in this folder apply cleanly to `main` at `d4421fe`, one group per file:

| Patch | Findings |
|---|---|
| `0001-…prose….patch` | H1, H2, M4, M5, M6: one hunk each |
| `0002-…banned-phrases.patch` | M2: gate, test, AGENTS line |
| `0003-…loop-state.patch` | M3: guard hook |
| `0004-…lower-bound….patch` | H3: loop.py, snapshot skill, test |
| `0005-…snapshot-script….patch` | M1 and M7: `scripts/snapshot.py`, tests, skill, `/next`, plist, AGENTS line |

To apply one, run `git am reviews/prompt-audit-2026-09-24/<patch>` in a Claude Code session. Patch 0005 changes the job file in the repo only. The installed copy in `~/Library/LaunchAgents/` must be reloaded after applying it. Patch 0004 does not fix the pinned post's existing ledger entry; that needs its snapshot re-recorded with `repliers_complete: false`.

## Verification

- **Code probes, run.** With every patch applied in a throwaway clone, all 66 tests pass: 61 existing plus 5 new. The guard change was probed directly: an edit to `loop/state.json` is denied, and a draft edit or a shell call reading `ledger/SUMMARY.md` is allowed.
- **Behaviour probes, not run.** Each would cost a Grok run:
  - For H1 and M6: run `/draft-thread` on a settings topic before and after, and check the root's opening and length.
  - For M1: run the script against a live due post and compare its numbers with a manual `x_thread_fetch`.
