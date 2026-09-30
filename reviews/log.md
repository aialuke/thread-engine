# Knowledge log

Append-only. One line per ingest, decision or lint. Newest at the bottom. Format: `## [YYYY-MM-DD] kind | path or Dnn | one line`. Kinds: `ingest`, `decision`, `lint`, `fix`. Loop events live in the ledger and git history; this file covers the documents. `research/index.md` says what exists.

## [2026-09-29] ingest | research/index.md | First index of research/, reference/, reviews/, queue/, receipts/. Seven orphans catalogued.
## [2026-09-29] ingest | reviews/log.md | This log created.
## [2026-09-29] fix | reference/x-api.md, reference/audience.md | Added Status/Checked lines. Grok wording flagged against D88, audience.md left for the operator.
## [2026-09-29] fix | research/layer-1/2/3-*.md, reviews/ui-direction.md | Added "as of D106" markers. ui-direction "Nothing here is built yet" kept: only the mock exists.
## [2026-09-30] fix | voice/exit-zero.md | Incident figures moved out of the rules, kept here with sources. 22 Sep: one reply line went out 12 times in 3 minutes and a bare "👋" 6 times (A13). Peak reply count in 24 hours was 68 (A12). Politics earned 1 follow from 5,901 impressions (18–24 Sep export). The "Drop a hi" connect post brought 13 of the 19 follows on 18–24 Sep. The one boost (the tool-swap) bought about 2,000 impressions, about 4 profile visits and no follows.
## [2026-09-30] fix | AGENTS.md, scripts/loop_core/README.md | Agent-convention audit: Grok status, Current state block, commit and analysis-location rules, loop_core notes moved to a README, truth budget "this session" defined.
## [2026-09-30] fix | AGENTS.md, CONTEXT.md, README.md, voice/, reference/audience.md, .claude/skills/ | Agent-conventions audit, 13 fixes in commits 4d57e8a, 936868c, f776a91; report in reviews/agent-conventions-audit-2026-09-30.md. `when-to-use` kept for Grok.
## [2026-09-30] ingest | research/jev-test/README.md | Jev conflict-pair run on 8 Codex review findings: 34 requests, control valid but carried by a synthetic pair; only F6 flagged with real signal; blind Codex disagrees on F10 and F11.
## [2026-09-30] ingest | research/jev-test/README.md | Jev conflict tests E0-E4 (174 Jev requests, 1 blind Codex label check, 12 haiku runs): built-pair control passes (sensitivity 0.95, false alarm 0.00), leave-one-out on the first run fails, behavioural runs unanimous but forced-choice by design.
## [2026-09-30] fix | .claude/skills/jev-judge-run/SKILL.md, research/jev-build-time-evaluation-2026-09-27.md, research/jev-test/README.md | Conflict-question rules added to the Jev skill and validated-types table after E0-E4 and T1-T3 (194 requests): reliable on reversed sentences, unreliable on task-dependent conflicts; controls built by construction; second rater required.
