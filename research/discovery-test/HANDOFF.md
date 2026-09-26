# Discovery test: handoff (26 Sep 2026)

Everything a new session needs to run the Discovery test exactly as planned. Read this, then `plan.md` in full.

## Status

- **Pilot run on 26 Sep, 19:01–19:10 Brisbane, in block B1.** X-only steps P0–P5 and P9 are done. Grok steps P7 (all five prompt styles) and P8-a are done.
- **Probes P8-b, P8-c, P8-d, P8-e and P8-f ran at 20:31–20:34, after the operator topped up Grok.**
  - Semantic `to_date` is **exclusive**, and the days are UTC. The index is fresh: the newest hit was 1.1 h old.
  - The harness now sets `to_date` to the day after the window ends. Details are in `private/facts.md`.
  - P7-hinted and P7-self ran before this fix, so their semantic half saw only 25 Sep.
- **All five styles were rerun at 21:09–21:19 with fixes** (list everything with Grok's `kept` flag, a clear cap, the `to_date` fix, one eligibility rule), plus P1c and P1d (F7, F8). Best-arm rule → **G-self** (9 good posts, 48 per $). Codex scored blind: 30 of 30, echo check clean; my 20% re-score found Codex a point lenient on relevance, and the stage brief is tightened. Results in `private/facts.md`.
- **Codex's blind adversarial review** of the proposal and the spam plan: `codex-proposal-review.md`. Acted on:
  - `research/discovery-x-api-search-proposal.md` now proposes only the narrow code rules as settled. Source choice, MJ2's shape, Weights and learning are hypotheses decided per job after each stage.
  - The harness reports each K sort as its own source; runs Tool research's spam query as a separate `Kspam` source; adds a `type` label; sends every positive and unclear post to a second scorer (`second-scores`, `finalise-scores`); and records `recheck` (gone after 24 h) as a signal only. 37 tests pass.
  - Spam research plan: `spam-research-plan.md`.
- **Stage 2 (Demand) ran at 22:38–22:58 on 26 Sep, in block B2.**
  - Three blind scorers, majority wins.
  - Useful posts: X API 39 (either sort), Grok 30, 54 in all. 15 were Grok-only, about 11 likely through semantic search.
  - X API wins per dollar in both Demand cells.
  - Details in `private/stage-2.md`.
  - Harness fixes: a JSONL reader that doesn't break on U+2028 in post text, and `config --new-block`.
  - Stages 1 and 3 not run.
- Console after the pilot: $18.86, a $0.34 drop against a $0.455 estimate. The snapshot's share is unknown.
- **Spend:** X API estimated $0.455 (pilot ceiling $2.50). Console read $19.20 before the pilot; the after reading is still needed. Grok reported $0.63.
- **Facts settled:** in `private/facts.md` (F1–F11, G1–G6, plus observations). Author checks stay off, because per-step billing wasn't measured (operator choice).
- **Best-arm rule result:** G-self (4 good posts per $0.158), just ahead of steered and free. Too few posts to separate the styles; see the pilot report in the conversation of 26 Sep.
- **Stages 1–3 have not run.** They need the operator's yes on the updated plan first.
- **Harness fixes made during the run:**
  - Windows end 30 s early (X wants `end_time` at least 10 s before the request).
  - Grok's folder moved outside the repo (`~/Library/Caches/thread-engine-discovery/grok-cwd/`), because a folder inside the repo loaded the project's skills.
  - The CLI's observed search arguments are now logged.
  - Post ids named only in Grok's answer text are checked too (`reprocess`).
  - The 402 wording is now recognised as the usage limit.

- **Operator decision (26 Sep): Grok is dropped entirely, for the product and the factory.** Recorded as D88 in `reviews/ui-direction.md`. Updated to match: D43 and D45, layer-2 L2-C6 and L2-C7, layer-1's model-job rows, the handoff README, and the proposal. The factory plan is `reviews/factory-drop-grok-plan.md`, for a later session. What remains for this test: Stages 1 and 3 test X API query design only (no Grok), plus the spam research.

## Files

| File | What it is |
|---|---|
| `plan.md` | The test plan, v3: questions F1–F11 and G1–G5, sources, frozen idea cards, pilot matrix, stages, scoring, observability, money. **The source of truth.** |
| `docs-xapi.md` | Docs-only findings on X API search, counts, timelines, pricing, fields, policy (26 Sep). |
| `docs-grok.md` | Docs-only findings on Grok's X search: one `x_search` tool, no structured results, pricing, ZDR terms (26 Sep). |
| `codex-plan-review.md` | Codex's blind review of plan v1. Its fixes are folded into v2/v3; the operator overrode three of them (below). |
| `docs-grok-prompting.md` | xAI guidance on prompting Grok's X search, and the Grok CLI's options. |
| `repo-grok-setup-audit.md` | Whether this repo's skills, hooks, AGENTS.md or script flags limit or distort Grok's searching, and how the test controls for it. |
| `community-grok-prompting.md` | Non-official sources on prompting Grok's X search, with reliability labels (26 Sep). If missing, redo it. |
| `grok-interview.md` | Grok's own answers about its X search tools, from the operator's interview in a clean folder (if saved). Claims are hypotheses for the pilot to check, not facts. |
| `grok-learnings.md` | One-page summary: what we learned about Grok, and how this project constrains it. Read first. |
| `private/grok-insights/` | Grok's own report (C01–C240) and its 26 Sep live semantic run (raw files are Grok's transcriptions; S2 was reconstructed from S1). Other people's posts: private. |
| `review-grok-report-*.md` | Reviews of Grok's report: observed claims (mine), repo claims, docs claims, and Codex's blind read. Their accepted changes are in `plan.md`'s last section. |
| `private/` | Gitignored. All raw data and logs go here. Delete by 24 Oct 2026. |

## Operator decisions (26 Sep, binding for this test)

1. **Scope is fact-finding**, not only "which source wins". Log everything (plan: Observability).
2. **`AGENTS.md`'s rule that other people's posts go only through Grok/`x_read.py` is set aside for this test.** Direct read-only X API search, counts and timeline calls are allowed.
3. **Money:** X API checkpoint at **$6** of estimated spend: stop, report what's learned and what more would add, wait for the operator's yes. No reserve floor: the operator manages credit. Grok checkpoint $3. Pilot ceiling $2.50 (includes the Grok prompt arms, P7, and checking the ~60 ids from Grok's 26 Sep run).
4. **Codex judges raw post text as returned**, no stripping (operator's choice, made knowing it sends other people's posts to an outside model).
5. **Grok runs through the Grok Build CLI on the operator's subscription**, as `scripts/grok_read.py` does. Keep the whole CLI envelope.
6. **Non-tech niche: satire / comedy.** Idea cards are frozen in `plan.md`.
7. **Verdict:** the report gives full data per job and niche whatever the verdict. Tie-breaker: simplicity favours dropping Grok (the product would then be CSV and CSV + X API only). Include "What dropping Grok would cost".
8. **Worth-joining posts are re-read ~6 hours later** to see if the conversation grew.
9. **Grok prompting is tested, not assumed** (plan: "Grok prompting"): steered vs free vs hinted prompts, and effort, in the pilot; the stages use the best arm.
10. **Timing:** run on the day the operator says go, from that time. Never during 19:30–20:30 Brisbane (the daily snapshot at 20:00).

## Operator housekeeping (not for the agent)

- Grok's cross-session memory is out of date (it still describes the old Hidden Settings audience). The operator may update or clear it in Grok.
- Whether `disable_codebase_upload` should be set in the Grok config is the operator's call; the agent doesn't change it.

## Rules that still apply

- Read-only on X. GET only, through `scripts/x_api.py`'s `Client` (it signs with the Keychain keys and refuses anything but GET). Never modify `scripts/`, the loop, `loop/state.json`, `ledger/`, `queue/`.
- Never open `loop/followers/`, `ledger/raw/api/` or `loop/inbox/`.
- Don't commit anything in `private/`. Don't commit at all without the operator's yes.
- Don't touch anything that affects the ~8 Oct experiment rules or the 16 Oct final read.

## Steps for the new session

1. Read `plan.md`, `docs-grok-prompting.md`, `repo-grok-setup-audit.md`, `community-grok-prompting.md` and `grok-interview.md` if present; add Grok's own suggested prompts (interview Q7) as a fourth prompt arm, "G-self"; (apply their recommendations to the Grok arms), `docs-xapi.md`, `docs-grok.md`, `scripts/x_api.py` (the `Client` class: `request`, `_fetch`, `usage`), `scripts/grok_read.py`, `scripts/x_read.py`.
2. Build `research/discovery-test/harness.py`:
   - subcommands per plan stage (`pilot`, `stage1` …), each call logged to `private/requests.jsonl` with every field in plan §Observability, raw bodies to `private/raw/`, a running cost estimate to `private/budget.log`, refusing to continue past the checkpoint;
   - Grok calls through the CLI with the full envelope saved to `private/grok.jsonl`, and every claimed post checked by id (as `x_read.py` does) with the result recorded;
   - `private/posts.csv` as the canonical post table; `private/facts.md` for F1–F11 and G1–G5.
   Test it offline first with a fake client (no network), as `tests/` does for `x_api.py`.
3. Show the operator the harness plan and the pilot's worst-case cost. **Wait for "go".**
4. Run the pilot. Stop. Report the facts it settled and the updated plan.
5. On the operator's yes, run the stages in order, with a short review note after each (`private/stage-N.md`), stopping at the $6 checkpoint.
6. Have Codex score blind (codex-delegation skill, read-only), per plan §Scoring. Re-score 20% yourself.
7. Write `research/discovery-search.md` (plan §Output). Tell the operator in three lines; they take it back to the build-strategy session.

## Where this fits

Layer 2 (X data tiers) research is in `research/layer-2-x-data-tiers.md`; decisions D1–D87 are in `reviews/ui-direction.md`. This test informs layer 2 choices L2-C6 (where other people's posts come from) and L2-C7 (Discovery without Full), and whether Grok is dropped from the product. The build-strategy session grills the operator from the report.
