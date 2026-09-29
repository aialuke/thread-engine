# Knowledge index

Read this first, then open only the pages it names. Kinds: **raw** (source material, never edit), **synthesis** (agent-maintained, cite sources), **snapshot** (true on its date, not updated), **decision-log**. Add a line here whenever a file is added under `research/`, `reviews/` or `reference/`; add a dated line to `reviews/log.md` too. Status is `current`, `snapshot`, `superseded`, or `orphan` (nothing else points to it; read before relying on it).

Decisions are cited as `Dnn` (`reviews/ui-direction.md`), algorithm facts as `An` (`reference/x-algorithm.md`), API facts as `Pn` (`reference/x-api.md`). Numbers are never reused.

## reference/ — verified facts
| Path | Kind | Status |
|---|---|---|
| `reference/x-algorithm.md` | synthesis, A1–A22, blob SHAs, refreshed by `/next` | current (checked 2026-09-24) |
| `reference/x-api.md` | synthesis, what the X API can read, prices, privacy | current; Grok wording pre-dates D88 |
| `reference/audience.md` | synthesis, audience promise and lanes (operator's choice) | current; names Grok, see D88 |

## research/ — product and platform research
| Path | Kind | Date | Status |
|---|---|---|---|
| `research/x-rules.md` | synthesis, X's own rules for a drafting tool | 2026-09 | current |
| `research/layer-1-switches-profiles.md` | synthesis, layer 1 | 2026-09-26 | current, Grok rows pre-date D88 (note at top) |
| `research/layer-2-x-data-tiers.md` | synthesis, layer 2 | 2026-09-26 | current, cites D1–D87 |
| `research/layer-3-engines.md` | synthesis, layer 3, no Grok | 2026-09-27 | current, cites D37–D104 |
| `research/discovery-x-api-search-proposal.md` | proposal and decision (D88 path) | 2026-09-26 | orphan |
| `research/jev-build-time-evaluation-2026-09-27.md` | proposal, "not evidence" | 2026-09-27 | orphan |
| `research/Jev cookbooks.md` | raw, vendor docs | 2026-09 | raw |
| `research/jev-articles/` | raw, 6 vendor articles on Jev | 2026-09 | raw |
| `research/jev-design-cards-reading/` | synthesis (`README.md`, `where-jev-succeeds.md`), snapshot (`votes-2026-09-28.md`), `readers/` = 5 literature-reader reports | 2026-09-28 | current |
| `research/jev-test/` | code, questions and synthetic data for the Jev tests (`README.md`) | 2026-09-28 | current |
| `research/discovery-test/` | Grok-vs-X-API discovery test. Start at `HANDOFF.md`, `plan.md`, `grok-learnings.md`. Raw: `docs-*.md`, `community-grok-prompting.md`, `spam-desk-research.md`. Reviews: `codex-*-review.md`, `review-grok-report-*.md` (orphan). `private/` holds scores, not committed reading | 2026-09-26 | snapshot |

## reviews/ — decisions, audits, weekly reviews
| Path | Kind | Status |
|---|---|---|
| `reviews/ui-direction.md` | decision-log, D1–D106 (as of 2026-09-28); the UI itself is only the mock in `ui/mock/` | current |
| `reviews/ui-build-handoff/` | synthesis, build handoff pinned to mock v22 | snapshot (2026-09-25) |
| `reviews/factory-drop-grok-plan.md` | plan for D88, nothing done yet | current |
| `reviews/week-2026-W39.md` | weekly review (`/results`) | snapshot |
| `reviews/audit-2026-09.md` | audit that chose the audience promise | snapshot |
| `reviews/paid-free-session-2026-09.md` | how PAID → FREE was designed | snapshot |
| `reviews/2026-09-22.md` | early review of the repo and account | snapshot, orphan |
| `reviews/ui-review-2026-09-24.md`, `ui-review-2026-09-25.md` | adversarial and code/browser reviews of the mock | snapshot, orphan |
| `reviews/x-tools-pilot.md` | pilot of X tools | snapshot |
| `reviews/prompt-audit-2026-09-24/`, `prompt-audit-2026-09-28/` | prompt audits, `REPORT.md` plus patches | snapshot |
| `reviews/skill-review-2026-09/` | instruction-file review (`BRIEF.md` + one file per skill group) | snapshot |
| `reviews/research_notes/Driving verified home timeline impressions/` | raw notes behind the report below | raw |
| `reviews/reports/Driving verified home timeline impressions.md` | synthesis of those notes | snapshot |
| `reviews/log.md` | append-only log of ingests, decisions and lints | current |
| `reviews/lint-YYYY-MM-DD.md` | `/lint` reports | snapshot |

## queue/, receipts/
| Path | Kind | Status |
|---|---|---|
| `queue/topics.yaml` | backlog and planned posts | current |
| `queue/research-backlog.md` | research to do later, operator-chosen | current |
| `queue/paid-free-roster.md` | claims to check, never copy | current, no last-checked dates |
| `receipts/decisions.jsonl` | decision-log, append-only, one JSON line per Jev vote | raw |
| `receipts/prompts/` | raw prompt receipts, one folder per call | raw |

## Loop data (not indexed here)
`ledger/`, `loop/state.json`, `experiments.md`, `learnings.md` and `ledger/SUMMARY.md` are owned by `scripts/loop.py`. Read them through `/results`.

## Reference facts and where they are cited
Filled by `/lint` when it finds an `An` or `Pn` cited that this table lacks. Grep for `A12`, `P14` etc. to find citers.
