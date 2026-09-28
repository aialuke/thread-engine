# Instruction-file review: next

Scope: `.claude/skills/next/` and the files it points to that no other skill uses. Method: `BRIEF.md` (this folder). Date: 28 Sep 2026. Fixed for this scope: the output lengths the operator reads (operator, 28 Sep).

## Baseline

| File | Words before | Words after | Sections | Steps and completion criteria |
|---|---|---|---|---|
| `next/SKILL.md` | 1,271 | 947 | intro; 1 Catch up; 2 Weekly work; 3 Pick the slot; 4 Pick the topic; 5 Propose, then write the row; 6 Replies worth making today | 1: snapshot, status, runs.log check, 2–3 line summary plus Rewards line. 2 (when `review_due`): /results, then algorithm SHA check ending in `set-reference`. 3: ambiguous while paused ("skip this section", then "Run `next-slot`"). 4: lane share; 1–2 checked searches recorded as leads; queue; posting time. 5: 4-line proposal plus why; queue row written on accept. 6: 2–3 conversations, link plus one-line point each; ends on the `Next:` line |
| `next/experiment-list.md` | new | 367 | one section | `next-slot` branches; experiment opened by `open-experiment` on the operator's yes |

Files pointed to that no other skill uses: `ledger/runs.log` (data), `reference/x-api.md` (also cited in `AGENTS.md`), `reviews/reports/Driving verified home timeline impressions.md` (research record), `loop/inbox/experiment.json` (scratch, not present), and the `results/SKILL.md` path (reviewed with /results). Only `reference/x-api.md` is an instruction-bearing reference.

## Approved and applied

1. **Pause pointer fixed** (`SKILL.md` step 3). The old line cited `reference/x-api.md`, which never mentions the pause. It now cites the decision: 24 Sep 2026, `reviews/audit-2026-09.md:112` (also `README.md:33`). It also says the change that lifts the pause rewrites this section. Principle: context pointer, single source of truth. Behaviour: the agent no longer decides by itself that the organic numbers are in. Codex agreed.
2. **Paused branch made one step, and the experiment material disclosed.** The old step 3 said "skip this section" and then "Run `next-slot`", and `next-slot` returns "open an experiment first" (`scripts/loop.py:803`). Now, while paused: propose with no arm, skip `next-slot`, and say so in one line. The root-only scoring rule, `next-slot` and its branches, the six-item list and the `open-experiment` procedure moved word for word, apart from changes 3 and 7, into `.claude/skills/next/experiment-list.md`. `SKILL.md` points there "when the pause is lifted". Principle: branching, progressive disclosure, sprawl. Who needs it: `/next` after API plan step 5 (about 8 Oct), which now edits that file alone. The name `experiments.md` is taken by the generated view and blocked by the guard hook (`.claude/hooks/guard_approved.py:34`), hence `experiment-list.md`. Codex agreed on the ambiguity.
3. **US-overlap slots moved into step 4.4.** Step 4.4 used them every run through "the slots in experiment 3". It now holds the slot times, the "hypothesis, not a finding" note with its report, and the 1 Nov daylight-saving note. Experiment 3 points back to step 4.4. Principle: co-location, single source of truth.
4. **Snapshot-health check split into three cases** (step 1.3): a stage failure, an error failure, and no run in 30 hours. Each case still says it first, in one sentence. The error case now gives the logged error instead of guessing "credits ran out". The stale case names an unloaded job as a cause, since the job has been unloaded 27 Sep–11 Oct. Principle: a clear criterion for each branch. Codex agreed.
5. **Step 1.1 cost claim corrected.** "costs nothing" became "X charges each item once per UTC day (a soft guarantee, `reference/x-api.md` P5)". Principle: a cache must match its source. Codex agreed.
6. **Trims.** The intro's "The operator's main command, in Grok or Claude Code" repeated the description. Section 6's "Replies bring most of the account's reach but count for nothing toward X's rewards program" changed no choice. Both are cut. The fail-closed `x_read.py` rule and "never paste-ready" are unchanged. Principle: no-ops and duplication.
7. **Experiment 5 marked review-only** (operator, 28 Sep 2026). It is measured by followers gained that week, and `open-experiment` scores single roots only (`scripts/loop.py:675-692`). It stays on the list and is watched in the weekly review, but it is never opened as a loop experiment. Raised by Codex.

## Declined and disagreements

- **"A stranger only sees a post after its first like" overstates A6** (Codex). Declined. `reference/x-algorithm.md:19` itself says "The first like is the gate to strangers", and A7 (`:20`) says not to plan around the tail index.
- **Make the output counts exact: "two or three lines" plus a Rewards line (step 1.4), and "four lines" plus a why sentence (step 5)** (Codex). Declined because output lengths are fixed (operator, 28 Sep). It stays an open ambiguity for the operator: is the Rewards line inside the 2–3 lines, and is the why sentence inside the four?
- **Move the remaining rationale in steps 4.2 and 4.4 out to the references** (Codex). Only partly done (change 6). The A6 sentence in step 4.4 is the reason the slots are preferred, and it stays.

## No change

- `reference/x-api.md`: a reference of verified API facts. The problem was the `/next` pointer to it (change 1).
- Frontmatter: `disable-model-invocation: true` fits an operator-typed command (Codex agreed).
- The fail-closed `x_read.py` rule, stated in both steps 4.2 and 6, is a guardrail kept at each use.

## Check

`python3 -m unittest discover -s tests`: 173 tests, OK. `/next` is not a posting skill, so there is no gate run. No file outside `next/` points into `next/` or to "experiment 3".
