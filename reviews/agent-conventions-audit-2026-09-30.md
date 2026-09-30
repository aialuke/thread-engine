# Agent-conventions audit, 2026-09-30

Where the repo's instructions could confuse, mislead or steer an agent. Every finding below was checked against the file text, a script or the session's skill listing. Fixes landed in commits `4d57e8a`, `936868c` and `f776a91`.

## Fixed

| # | Finding | Evidence | Fix |
|---|---|---|---|
| 1 | AGENTS.md said only `loop.py` writes `ledger/raw/`; `/posted` writes there, and `snapshot.py` and `x_api.py` write `ledger/raw/api/` | `posted/SKILL.md` step 2; `scripts/snapshot.py:16` | AGENTS.md Layout names the real writers |
| 2 | Exploit slot said "follow adopted lessons in `learnings.md`", against "lessons change rules through `/apply` only" | `next/experiment-list.md` exploit line; `learnings.md` header | Exploit follows the current rules; lessons arrive only via `/apply` |
| 3 | `x_read.py` is "the one route… so a Grok run is never the source", yet it is one Grok call; RULES.md routes X evidence to `grok-delegation` | AGENTS.md line 12; `scripts/x_read.py:2` | AGENTS.md says what `x_read.py` is and that the global route does not apply here |
| 4 | Plan mode was a rule in AGENTS.md and optional in README and `/next` | README step 2; `next/SKILL.md` last line | README and `/next` say `/draft-thread` starts in Plan mode |
| 5 | "Card" meant every post in the glossary but only the setting posts in `hidden-settings` (N vs N + 2) | CONTEXT.md Card; `hidden-settings` Root post | CONTEXT.md defines N and N + 2; skills say "posts" for totals |
| 6 | Lane was "never by Format" in the glossary, with a PAID → FREE exception in `/results` | CONTEXT.md Lane; `results/SKILL.md` | Exception removed; audience fit only |
| 7 | Experiment pause exit was a data condition with no owner | `next/SKILL.md` step 3 | Dated line (2026-10-08) plus an ask in `/next`; the yes edits AGENTS.md |
| 8 | "This session" was redefined only in CONTEXT.md, which drafting never reads | CONTEXT.md Truth budget; `verify-settings` | Skills say "this verify run" |
| 9 | Bare `/draft-thread` took the first queued row (`windows-laptop`, `settings`) | `draft-thread/SKILL.md` Argument; `audience.md` audit line | Stops and points to `/next` |
| 10 | Gold examples close with lines the gate refuses; only two pointers carried the warning | `examples/*.md`; `post_thread.py` | `draft-thread` step 3 says take the closer from the format |
| 11 | Examples in instructions read as facts ("Grok caught…", "Photopea isn't open source") | `format-tool-verdict`, `verify-settings`, `format-tool-swap` | Placeholders |
| 12 | Prohibitions quoted the phrase they forbid; dated handle table and daylight-saving date sat in permanent skills | `voice/exit-zero.md`; `format-tool-swap`; `next/SKILL.md` | Positive phrasing; table moved to `shipped/paid-to-free-tools/NOTES.md` |
| 13 | README was Grok-first; `jev-card` said "user" and "Luke", hard-coded `/tmp`, left "policy" and "receipt line" undefined; `next` step 1.4 used "first" twice | README; `jev-card/SKILL.md`; `next/SKILL.md` | Reworded |

## Corrected during the fix

- **Jev pointer.** The audit said `jev-judge-run` pointed at a "not evidence" document. The pointer is to its section "Judging text with Jev", which does hold the validation record. The index row was the misleading part, and it is fixed.
- **`when-to-use` frontmatter.** The audit called it dead text because Claude Code's skill listing omits it. `reviews/skill-review-2026-09/` shows it was kept on purpose, and the Grok docs read it for matching. It stays until D88 removes Grok. A change that removed it was reverted before commit.

## Left as is, by decision

- The "Settled" list in `format-tool-swap` stays: it applies to every draft, and the job-first line is now phrased positively.
- The `examples/` posted copies are unchanged; the warning sits at the pointer instead.
- `when-to-use` in eight skills (see above).

## Not verified

- Whether any live draft copied the old TV closer.
- What `/next` does on 2026-10-08, since the pause has not yet reached its date.
