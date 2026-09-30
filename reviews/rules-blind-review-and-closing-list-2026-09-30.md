# Global rules: blind review and closing list (2026-09-30)

Two edits to `~/.claude/RULES.md` (outside git), each tested before and after with headless `claude -p` sessions from a scratch directory (no repo instructions loaded), 2 runs per prompt, scored from the stream-json tool calls or the final reply. The harness lived in the session scratchpad and is gone; nothing here is re-runnable from the repo.

## 1. Blind review before an options decision

Baseline finding: a soft line ("a conclusion deserves blind challenge before you state it") never fired. 0 of 6 headless runs on recommendation, plan and pre-commit prompts used any tool.

Edit: that trigger was removed from the Codex line. A new Delegation line says to blind-review before stating any recommendation, plan or decision that picks between options, and before a commit resting on a decision, sending Codex the question and evidence without the conclusion. If Codex is unavailable a blind Claude subagent on an appropriate model stands in, named as the one exception to the "never re-check your own answer" subagent rule.

| Case | Before | After |
|---|---|---|
| Recommendation, plan, pre-commit decision (6 runs) | 0 fired | 6 fired |
| Fact, one-line task, explanation, count-vs-total naming (8 runs) | not run | 0 fired |

- All 6 after-briefs withheld the model's own conclusion. One run hit the 5-turn test cap while retrying the Codex call.
- Fallback (Codex broken by pointing `CODEX_HOME` at a missing path): 1 valid trial. Codex failed, a blind `opus` general-purpose subagent got only the question. In that run the final message said Codex was "still running", and a failed `codex-rescue` agent was also launched first. The second run is invalid: Codex succeeded despite the setting, cause not investigated.

Source of the ask: 7 short messages in this project's transcripts mention both "blind" and "codex" (an earlier handoff said ~18; that count was unverified and is not supported).

## 2. Closing list

Edit: new section "Closing a decision". A reply that recommends, plans or reports a finished change ends with **Assumed** (facts relied on without verifying) and **Overlooked** (checks not run); `none` only after looking; plain answers, explanations and one-line tasks end without them.

| Case | Before | After |
|---|---|---|
| Decision replies (6 runs), both lists in the reply tail | 0 | 6 |
| Trivial replies (8 runs) | 0 | 0 |

- Two after-replies were read in full and the lists were specific (for example, macOS ships rsync 2.6.9; SQLite docs cited by Codex but not opened). The other 4 were scored by pattern only.
- Not tested: the "reports a finished change" trigger, and long working sessions with several topics in one reply.
- "Next step" was left out: none of the 12 short matches for "anything else / assumptions / overlooked" in this project's transcripts asks for one (an earlier handoff said ~25; unverified).

## Open

- Fallback in item 1 is n=1.
- No test of over-firing on real multi-topic sessions.
