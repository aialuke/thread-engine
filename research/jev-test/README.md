# Jev build-phase test

> **2026-10-01: Discovery scoring code retired.** `research/discovery-test/` (its corpora, labels and harness) was deleted after the Grok removal, so the pipeline that scored Discovery posts with Jev could no longer run. Removed: `jev.py`, `raters.py`, `arms.py`, `labelling.py`, `extract_subagent.py`, their tests, `questions.json`, `questions-reworded.json`, `thresholds.json` and `synthetic.jsonl` (all in git history before the commit that adds this note). Still here and working: `conflict_judge.py`, `glossary_check.py`, `glossary_judge.py`, `placement_judge.py`, `proof_judge.py`, `pstack_routing.py`, `conflict_items.json` and `test_conflict.py`. The runbook (setup, commands, rubric, pre-registration and the pull-day checklist) was removed the same day. The sections below are what the experiments found. Paths under `discovery-test/` are history. The product referee's own questions are `jev/questions.json`, not these.

Tests: `python3 -m unittest discover -s research/jev-test`.

Does Jev, TypeSafe's typed-judgement model, earn a place as a cheap, repeatable judge while we tune Discovery search and filtering? This is build-phase research only. Nothing in the factory (`scripts/`, skills, hooks, `ledger/`, `loop/`) uses it. The case for testing, and its limits, are in [`../jev-build-time-evaluation-2026-09-27.md`](../jev-build-time-evaluation-2026-09-27.md).


## Sources

- **TypeSafe docs and official posts:** docs.typesafe.ai and typesafe.ai/blog.
- **Partner write-ups** (LangChain, Browserbase): used for patterns, not as independent evidence.
- **thejevai.com** says it is "independently operated and not affiliated with TypeSafe". Its design advice is used; its API details (`thejevai.com/v1/systemone`, `JEV_API_KEY`) are not.
- **evals.typesafe.ai** renders in the browser. Only its overview could be read (28 Sep): break a policy into small Noul, Choice and Score questions and combine them in code.
- The five articles are in `../jev-articles/`.

## Results

### Experiment 1, 27 Sep 2026: the setup works (the quality reading doesn't hold)

- **Run:** 30 made-up posts, served by pinned `jev-1.13.0`. 31 calls including the smoke test, $0.0012 in all, about 0.3 s a post.
- **Bar:** `act` matched on 25 of 30 (the bar was 24), with AUC 0.97.
- **Other dimensions:** real 93% exact, relevant 80%, type 80%, useful 60% (87% within one).
- **Every `act` miss said yes when it should have said no.** None were missed genuine posts:
  - Both video-game "free version" lookalikes (y04 at 0.87, y05 at 0.59). Jev called them squarely relevant (2) and `genuine` with 0.99 confidence on y04. This is the same trap the real pilot hit (`../discovery-x-api-search-proposal.md`), and the clearest weakness: a real ask outside the idea's domain reads as on-topic.
  - Replies and advice for someone else's need (y06 at 0.78, y18 at 0.74). Relevance was right (1), but `act` still said yes.
  - A "10 free alternatives" listicle (y10 at 0.52), borderline.
- **Useful runs high:** it often scores 1–2 where the label is 0, including spam and promotion. Treat it as the weakest dimension.
- **Type misses were mostly between neighbouring kinds of spam** (promotion, engagement-bait, product-marketing), which doesn't change `act`.

**Correction, 28 Sep:** the made-up labels were stricter than the real ones. In settled Stage 2 labels, 52 of 54 replies are marked "act", and the operator counts a reply opportunity as useful. So the `act` "misses" on replies (y06, y18) may be right. The relevance rule below is **withdrawn**: it would drop 71 of 126 settled Stage 2 "act" posts.

**Withdrawn hypothesis (27 Sep):** requiring Jev's `relevant` = 2 as well as `act` ≥ 0.5, combined in code, gives 28 of 30 here. The video-game pair still passes it. Test it on the real replay as a secondary rule, never as the pass measure.

The rubric wording is unchanged. The one allowed revision is held back: the real fix for the video-game trap is probably the idea's own wording ("creator or developer **software**"), which is a Discovery change, not a Jev one.

### Experiment 3, 28 Sep 2026: the B3 pull (directional)

- **Pre-registered result:** at the frozen cut-off (0.8 on `max(p_good, 1 − p_good)`), Jev decides 108 of 186 final posts (58.1%) and agrees with the Codex/Claude/Grok majority on 92.6% (random, same share, about 80.6%). Validation gave 96.1%, so the 95% level the cut-off was chosen for didn't carry over.
- **By job:** closest to the LLM raters on Tool research and Demand. Weakest on Worth joining, where the level rule overcalls and 5 of 10 reworded verdicts flipped.
- **Stability:** 0 of 30 repeated calls changed a verdict. Confidence AUROC was 0.75–0.83. Every rater answered every post.
- **Not included:** the operator's labels, by the operator's choice; they can be added to validation later. The Worth-joining re-read hadn't run yet.
- **Full write-up and the AUD/USD correction:** [`../jev-build-time-evaluation-2026-09-27.md`](../jev-build-time-evaluation-2026-09-27.md#results-experiment-3-the-b3-pull-28-september-2026).


### Experiment 2, 28 Sep 2026: the development set's `act` labels

The `act` pass rule written on 27 Sep is withdrawn. The harness copied every final `act` label from Codex's first score and never compared or settled it (`discovery-test/harness.py`, now deleted). Measuring Jev against it would have measured agreement with Codex. `act` is a historical field only.

### Experiment 4: B4 was not run

The B4 query-design pull was pre-registered on 28 Sep, before any read, and was not run. Its command list went with the scoring code. Checking `arms.py` against B3 before that pull recorded two corrections:

- "Good" is the product rule by each question's most probable level (relevant 2, real 2, useful ≥ 1), with the panel as the LLM raters' strict majority. Read that way, B3 was 89 of 364 good, 16% with a link against 29% without, and all 10 good Worth-joining posts under an hour old. Jev was still read by its frozen rule, `p_good ≥ 0.5`, alongside.
- Two predictions were not supported by B3. Under the three-question rule, B3's LLM pairwise κ was 0.48, 0.61 and 0.63, against 0.51, 0.70 and 0.63 under the current rule. Jev agreed with the panel 64.6% of the time, against 78.0%. On Worth joining: κ 0.46–0.50 against 0.54–0.75, and Jev 61.1% against 62.5%. The rules disagreed on 31 posts, 29 of them genuine. A ≤2 h cut dropped 4.2% of B3's current-card Worth-joining posts and kept every good one. A ≤1 h cut dropped 22.2%, also keeping every good one. B3 pooled at the 0.8 cut-off gave 57.7% decided at 94.3% agreement.


## Glossary judge (2026-09-30)

`glossary_judge.py` asks Jev whether proposed `CONTEXT.md` definitions match how the repo uses each term
(`build`, `run [term]`, `report`). Snippets are prose from committed `.md` files only. Answers are in
`private/glossary/` (v1, superseded, in `private/glossary-v1/`).

**Calibration set, hand-audited before the v2 run** (8 usages read each): clean = Cohort, Roster, Truth budget;
muddy = Control, Round (3+ senses seen), Hook, Topic (glossary admits a second sense); general = JSON, retry,
regex, endpoint; exploratory, outside the rule = Lane, Slot, Arm.

**Pass rule, declared before any v2 request. Fail means stop, with no rescue edits:**
- specific >= 0.70 on Cohort, Roster, Truth budget, Hook, Topic
- specific <= 0.30 on every general term
- one-sense: mean(clean) minus mean(muddy) >= 0.25
- cloze accuracy: mean over clean terms >= 0.70
- faithful: mean of each clean term's minimum >= 0.60

v1 failed the one-sense check (gap 0.15 vs 0.20) because Lane and Slot were wrongly labelled clean.

## Glossary check of the new entries (2026-09-30)

`glossary_check.py` asks Jev whether the seven new `CONTEXT.md` definitions (Post, Ledger, Queue, Organic,
Retrospective post, Shout-out, Voice) match the repo's usage. Slot is not checked: its entry deliberately
excludes the clock-time and feed senses. Three reps per term, each a different 8-snippet sample (seeds 1-3, prose
`.md` only, no matches inside backticks, no outside-source notes), so 24 snippets per term.

**Controls, planted before the run** (they must behave as the questions claim, else the new results are ignored):
- wrong definition: Shout-out as "a line in a Card" -> mean faithful <= 0.50
- implementation-laden: Ledger as file names and scripts -> impl_detail >= 0.60
- undefined words: Queue leaning on "Wibbler" and "Foozle" -> self_contained <= 0.40

**Pass rule for each new definition** (mean over the 3 reps; controls must pass first):
- mean faithful >= 0.75, self_contained >= 0.60, impl_detail <= 0.40
- any question whose 3 reps span > 0.30 is flagged unstable, not passed

A definition that fails is marked "revise" with the failing questions. Nothing is edited automatically.

**Result (2026-09-30): controls failed, so the new-definition scores are ignored.** The wrong Shout-out control scored
0.52 on faithful (needed <= 0.50) and was indistinguishable from the real Shout-out entry (0.53). The
implementation-detail control passed (0.98 vs 0.16-0.33 on the seven new entries) and the undefined-word control passed
(0.24), but real entries also scored 0.24-0.56 on self_contained, so that question does not separate them. In that
run only impl_detail was validated (later runs validated more: see the evaluation doc). Likely cause (unverified): most
snippets mention the term without saying enough to confirm or refute a definition, so a yes/no "is this true of the
usage" sits near 0.5. Next time: a Choice of consistent / contradicts / silent per snippet, and snippets where the term
is the subject of the sentence.

## Placement judge (2026-09-30)

`placement_judge.py` asks Jev, per learning from the Jev runs, where it should live: skill, research doc, memory,
RULES.md, AGENTS.md, or none (already covered / leave out). Two requests, destination order reversed in the second.
Sent: my own learning statements and destination descriptions only.

**Recommendations (mine, fixed before the run):** L1 skill, L2 research doc, L3 memory, L4 RULES.md, L5 none,
L6 none, L7 none, L8 AGENTS.md.

**Controls with known answers (fixed before the run):** C1 skill, C2 memory, C3 AGENTS.md, C4 research doc,
C5 RULES.md.

**Pass rule:** trust the learnings' verdicts only if >= 4 of 5 controls are picked correctly in both orders.
Otherwise stop and report. A learning counts as agreeing only if both orders pick my recommendation; a split
between orders is reported as order-sensitive, not as a verdict. Disagreement goes to the operator, not to Jev.

**Result (2026-09-30): controls failed (2/5 in both orders), so the placement verdicts are ignored.** Jev sent the
release-steps skill control to memory (0.79-0.83), the project-invariant control to rules_md (0.89-0.90), and split the
experiment-result control between rules_md and agents_md (0.42-0.43). Its confident wrong answers on obvious cases mean
its agreements on the real learnings carry no weight either. Likely cause (unverified): the six destinations overlap in
purpose and the state carried too little of what each file is for. Placement between documentation homes is a
convention judgment, not a semantic reading of text, and is not a fit for Jev without much richer destination context.

## Proof judge (2026-09-30)

`proof_judge.py` is the record of this run, not a template; the procedure is the `jev-judge-run` skill. It asks whether
**Proof** is used in one sense.

**Current reading (start here).** Jev does not separate Proof's evidence sense (A) from its proof-line sense (B) under
the wording first used: mixed 0.64 against pure 0.76 and 0.81, far above a known split (Hook, 0.21 and 0.18). Under a
neutral wording the answer is inconclusive by the declared rule (A 0.56, B 0.71, mixed 0.44; a pure card is under the
0.60 floor). A blind Codex found four senses and said one entry is not enough. Jev's result is not evidence that Proof
has one sense. **Decision (operator, 30 Sep): two glossary entries, Proof and Proof line**, written to `CONTEXT.md` on
my recommendation, which rested on the repo's own usage read in full context and on Codex agreeing with the A/B split,
not on Jev. Codex's other two senses were not given entries: claim substantiation is ordinary English plus sense A, and
the approval-test "proof test" is UI-project vocabulary. My hand labels had errors, listed under "Second rater". 55 requests in all (40 main run, 3 hook control, 12 wording
follow-up), about $0.02 at the documented price ($0.042 per million input tokens, 466,957 input tokens; arithmetic, not
a bill).

**Hand labels (mine, made before any request, and flawed).** I labelled 45 prose usages of "proof" in committed `.md`
files (outside `jev-*` research, `discovery-test/` and `layer-3`) from grep output cut to 300 characters. I did not open
the surrounding text, and that is where the errors below came from. 38 lines were kept and 7 dropped (outside sources,
or a match I could not read). Sense **A**, evidence attached or shown (real proof: screenshot, recording, output,
figure, named source): 24 lines (corrected from 25 after the run). Sense **B**, the `▷` proof line in a PAID → FREE post:
9 lines. **C**, which I called ordinary English ("not proof of demand", "proof test"): 5 lines, used only in one
cloze-only card; two of the five were wrongly labelled (see the second rater below). My prior: two senses (A, B), so
overloaded.

**Calibration terms.** I read 16 usages of each (seed `audit-<term>`), separate from the 8 usages each card samples
(seeds `…-proof-cal-<rep>`), so the labels apply to the term, not to a card's snippets. Clean Cohort, Roster, Truth
budget (one sense; Cohort has three field-name lines, Roster one odd line); muddy Control, Round, Hook, Topic (UI
controls, round buttons, Claude Code hooks, off-topic and X topic labels beside the project sense). Same split as the
2026-09-30 glossary runs.

**Cards, each repeated for 3 reps with a different sample seed.** Proof A-only (8 snippets), B-only (8 of 9, so reps
overlap), and mixed (4 A + 4 B). Every card asks `one_sense`, `specific`, `impl_detail` and a per-snippet cloze
(the word masked; options Proof, Proof line, "a general English word"). For B the phrase "proof line(s)" is masked as
one blank, so "line" does not leak the answer; A masks "proof". Calibration cards come from `glossary_judge.build_card`.
Planted controls on the Proof text: an implementation-laden definition (file names), an undefined-word definition, and
a wrong definition (the proof-line sentence, B, asked about the A snippets). One more card, `proof-c`, asks only the
cloze for the 5 C lines.

**Pass rule (calibration first; if any line fails, stop and ignore the Proof results).**
1. `one_sense`: mean(clean) − mean(muddy) >= 0.25 over the 7 terms.
2. Cloze accuracy: mean over the clean terms >= 0.70.
3. `impl_detail`: planted laden definition >= 0.60 and both real Proof definitions <= 0.40.
4. No calibration term's `one_sense` spans more than 0.30 across reps (else that question is unstable).
The 0.25, 0.70 and 0.30 numbers were declared before the 2026-09-30 glossary run and are reused here, not tuned to its
results. `self_contained` and `faithful` were unvalidated in that run; they stay unvalidated here unless the planted
undefined-word control gives `self_contained` <= 0.40 and the wrong-definition control gives mean `faithful` <= 0.50
on A snippets, in which case they are reported as a second signal, still not a verdict.

**Decision rules for Proof (only after calibration passes).**
- *Overloaded, split:* `one_sense` on A-only >= 0.60 and on B-only >= 0.60, and mixed <= min(A-only, B-only) − 0.25.
  Action: propose two entries, Proof and Proof line.
- *One sense, fold:* mixed within 0.25 of the pure cards. Action: one Proof entry with the proof line as an example;
  my labels go to a second rater (Codex or Grok, read-only) before I accept that.
- *Cloze:* accuracy >= 0.70 on A and on B means the senses are separable by context. Below that, report the cloze as
  inconclusive; it is not evidence for one sense.
- *Inconclusive:* any pure card below 0.60, or any rep span > 0.30. Report and change nothing.
Nothing here edits `CONTEXT.md`; wording goes to the operator first.

**Disclosure (corrected after review).** Sent to TypeSafe: snippets of repo prose (about 320 characters each) from
committed `.md` files outside the excluded folders (skills, `voice/`, `reference/`, `reviews/`, `research/*.md`,
`queue/`, and the root `AGENTS.md` and `README.md`), plus my definitions, and, in every Proof and calibration card,
the 36 glossary definitions parsed from `CONTEXT.md`. Not sent: `drafts/`, `shipped/`, `receipts/`, `ledger/`,
`loop/`, other people's data. The first version of this paragraph said `CONTEXT.md` was not sent; a blind Grok review
found the glossary in the card state.

**Result, main run (2026-09-30): calibration passed on all five lines.** 40 requests (21 calibration cards, 19 Proof
and control cards), 3 reps, no failures. Pilot first: Cohort one-sense 0.82 and Control 0.10, inside the earlier run's
ranges, then the rest.
- Calibration: `one_sense` clean 0.75-0.81 against muddy 0.09-0.19 (gap 0.63); largest rep span 0.19; cloze on clean
  terms 1.00; laden control `impl_detail` 0.98 against 0.14 (A) and 0.29 (B) on the real definitions.
- Proof `one_sense`: A-only 0.76, B-only 0.81, mixed 0.64 (max rep span 0.13). The mixed gap to the lower pure card is
  0.12, under the declared 0.25, so **by the pre-declared rule Jev does not see an overload (fold)**. It is well above
  the muddy range (0.09-0.19), so Jev does not treat Proof like Control or Round.
- Noise in that gap (my reading): the three control cards use the same A snippets as `proof-a` and scored 0.64-0.66
  against 0.76, so a different proposed definition alone moves `one_sense` by about 0.1. The mixed gap is inside that.
- Cloze: A 1.00, B 0.96 (one miss, `reviews/paid-free-session-2026-09.md:503`). Separable by context, but the B snippets
  carry `▷` and "swap" cues, so this is not evidence of two senses. The 5 lines I labelled ordinary English scored 0.00
  on cloze: Jev always picked Proof or Proof line, never "a general word". That was a warning about my label, not about
  Jev: two of the five were the approval-test sense (see the second rater below).
- Unvalidated signals: `faithful` separated this time (wrong definition 0.14 against 0.79 on A); `self_contained`
  gave 0.19 on the undefined-word control against 0.41-0.42 on the real definitions, a gap but not a clean split.
  Real B definition faithful only 0.60: the session notes talk about the line's shape and wording, not the reason.
- Not verified at the time: whether Jev was reading "proof" and "proof line" as one word because my question said
  "alone or in 'proof line'". The wording follow-up below tests it.

**Follow-up control, rule declared before its requests (2026-09-30).** The run had no known-positive for a 4-and-4 split
of one word, so a mixed score of 0.64 could not be read either way. Card `hook-mixed`: 4 usages of Hook as the opening
Card or hook style (`.claude/skills/format-settings/checklist.md:12`, `reviews/paid-free-session-2026-09.md:108`,
`README.md:49`, `reviews/ui-build-handoff/mock-only.md:43`) and 4 as a Claude Code or Grok hook that blocks or writes on
a typed prompt (`.claude/skills/approve/SKILL.md:14`, `.claude/skills/draft-thread/SKILL.md:51`, `AGENTS.md:13`,
`reviews/x-tools-pilot.md:37`). Every line was printed in full and read before labelling. The question was the Proof
cards' wording with the word "hook" (this omitted the "alone or in ..." parenthetical; see the wording follow-up),
3 reps, different order each. **Rule:** `one_sense` can detect a 4-and-4 split only if `hook-mixed` <= mean(clean
terms) - 0.25. If it can, the Proof mixed score of 0.64 counts as Jev not seeing a split. If it cannot, the Proof
"fold" verdict above is void and Jev says nothing about the A/B split.

**Control result: `hook-mixed` one_sense 0.21 (span 0.09), against a threshold of 0.52, so the question can detect a
4-and-4 split.** 3 requests, no failures. What it does not settle (inference, untested): Hook's two senses sit in
different domains (post copy against tool plumbing), while A and B sit in one (evidence for a post). A question that
catches a domain split may miss a smaller difference in referent, such as an attached file against a sentence of copy.

**Wording follow-up, rule declared before its requests (2026-09-30).** A blind Grok review pointed out that the hook
control asked its question without the parenthetical the Proof cards used ("alone or in 'proof line'"). So 0.21 shows
that the neutral wording detects a split, not that the Proof wording does. 12 requests, one question each, on the same
snippets as the existing cards for each rep: (a) `neutral-a`, `neutral-b`, `neutral-mixed`, the Proof snippet sets asked
as "Do all of `snippets` use the word 'proof' in one and the same sense?"; (b) `hook-mixed-p`, the hook snippets asked
as "... the word 'hook' (alone or in 'hook style') ...", the parenthetical mirrored. **Rule:**
1. If `hook-mixed-p` <= mean(clean terms) - 0.25, the parenthetical does not blunt split detection and the Proof
   result above stands as a reading of its own wording. If not, that Proof one-sense result is void.
2. Neutral Proof wording: either pure card < 0.60 or any rep span > 0.30 is inconclusive; else mixed <= min(pure) - 0.25
   means Jev sees two senses (this overturns the fold); else the fold is confirmed. The neutral hook control (0.21)
   already covers this wording.
If the two wordings disagree, the disagreement is the finding.

**Wording follow-up result: `hook-mixed-p` 0.18 (threshold 0.52), so the parenthetical does not blunt split detection
and the parenthetical Proof result stands as a reading of its own wording. The neutral Proof wording is inconclusive
under rule 2:** A-only 0.56, B-only 0.71, mixed 0.44 (max rep span 0.27), and the A card is under the 0.60 floor.
Read with care (inference): the neutral wording lowered all three Proof cards (A by 0.20, B by 0.10, mixed by 0.20)
but left the Hook control where it was (0.21 to 0.18), which fits the parenthetical having lifted the Proof scores.
The mixed card stays 0.12 below the lower pure card under both wordings, inside the definition noise noted above. So
Jev gives no usable signal either way on A against B; it is neither a split nor a confirmation of one sense.

**Second rater: Codex, read-only, blind (2026-09-30).** Sent the 38 usages unlabelled and shuffled, with no verdict and
no pointer at this file. Codex read the files and found **four senses and says more than one entry is needed**, against
Jev's parenthetical-wording "fold". It agrees with my A and B split. It differs on the rest (its groupings, my checks in
brackets):
1. Artifact evidence, 23 lines: my A, less `reference/audience.md:20`.
2. Proof line, 9 lines plus `.claude/skills/format-tool-swap/SKILL.md:67`: my B. Line 67 holds both senses
   ("first-hand proof" and "the judgement in the proof lines"), so my A label for it was incomplete [checked by reading
   the line]. The window sent to Jev in the A cards ends before the second sense, so Jev saw only the first.
3. Claim substantiation, 4 lines (`reference/audience.md:20`, `research/layer-2-x-data-tiers.md:251` and `:255`,
   `research/layer-1-switches-profiles.md:206`): evidence that warrants a claim, not an attached thing. I had
   `audience.md:20` under A and the other three under C.
4. Safety demonstration, 2 lines (`research/layer-1-switches-profiles.md:27` and `:219`, "D37's proof test"): a test
   that an agent cannot reach approval. I had these as ordinary English (C). D37 does specify "a test proving an agent
   can't trigger it" [checked, `reviews/ui-direction.md:47`], so C was wrong for these two: it is a project meaning.
Codex's suggested entries: Run evidence, Proof line, Claim evidence, Approval safety test. That naming and the
"claim evidence" group are its inference, not settled.

**What the run does and does not show.** Jev: under the wording first used, no overload at the A/B level, far from a
known split; under a neutral wording, inconclusive. Codex: overloaded, four senses. Me: A and B are distinct referents;
whether that needs two entries is a wording call. The disagreement is unresolved and is the operator's to settle. Jev
was not asked about the D37 sense or the claim-substantiation sense, so it says nothing about them.

## Experiment: do two instructions conflict? (30 Sep 2026)

**Question type under test:** a Choice per pair of passages, "can an agent follow both in one draft?", with options `both_followable`, `cannot_both_be_followed`, `silent`. Untested until its controls pass. Code: `conflict_judge.py`; answers cache in `private/conflict/`.

**Items:** 8 findings from a blind Codex review of the edited docs (#3, #4, #5, #6, #7, #8, #10, #11), each a pair of exact lines read from the current files. **Controls, fixed before any request:**
- Known conflicts (3): AGENTS.md "ledger/raw written only by loop.py" against `/posted` step 2 saving there (AGENTS.md at `ffea23c`); AGENTS.md "lessons through /apply only" against the exploit slot "follow adopted lessons" (both at `ffea23c`); voice "never edit a live post to add a caveat" against a planted sentence that says to edit it (synthetic).
- Known consistent (3): the 600-character root cap in `hidden-settings` and `format-build-log`; Plan mode in AGENTS.md and README; lane judged by audience fit in CONTEXT.md and `/results`.

**Wordings:** A, and B (options in reverse order, rephrased). The mean A-versus-B shift across all pairs is the wording noise.

**Pass rule (written before the pilot):**
- The type is valid only if the mean `cannot_both_be_followed` probability on the 3 known conflicts is at least 0.30 above the mean on the 3 known consistent pairs, in both wordings.
- "Jev flags it" means a finding's probability is above the highest consistent-control score plus the wording noise, in both wordings.
- A pilot pair asked three uncached times spanning more than 0.30 makes the question unstable.
- If the control fails, no finding score is quoted, and no threshold or control changes to pass.
- Second rater: Codex, read-only and blind (no labels, no verdict), on any pair Jev calls silent or contested.

**What leaves the machine:** the quoted lines, their file names and the question wording. No `glossary` field and no `CONTEXT.md` beyond the quoted lines. Request cap: 80.

### Result (30 Sep 2026): 34 requests, about 9,600 input tokens, about $0.0004 (arithmetic at $0.042 per million, not a bill)

- **Control verdict, by the pre-set rule: valid.** Gap 0.44 (wording A) and 0.40 (B) against the 0.30 needed; wording noise 0.03. Pilot repeats: the known conflict CX1 scored 0.36, 0.26, 0.38, 0.30 (span 0.12), the consistent CK1 0.03-0.04, so not unstable.
- **The verdict rests on the planted sentence.** CX3 (synthetic, an explicit opposite) scored 0.99 and 1.00. The two real known conflicts scored 0.33/0.20 (CX1) and 0.05/0.04 (CX2), and Jev chose `both_followable` for both. On the two real ones alone the gap is 0.17 and 0.11, under 0.30 (inference; the rule was not written for this split and is not changed).
- **Jev's choice was `cannot_both_be_followed` only for CX3 and F6** (0.51 and 0.57, close to even). By the ceiling rule (0.07 and 0.06) Jev also "flags" F4, F8 and F10, at 0.07-0.18 with `both_followable` still the choice at 0.7-0.9. Treat those three as noise, not flags (inference).
- **Blind Codex (14 pairs shuffled, no labels)** said `cannot_both_be_followed` for CX1, CX3, F6, F10 and F11, and `both_followable` for CX2 and the rest. Agreement with Jev on the findings: F3, F4, F5, F7, F8 (both followable) and F6 (conflict). Disagreement: F10 and F11, where Codex says conflict and Jev says both followable. CX2 is now doubtful as a "known conflict": both raters called it followable (unverified which reading is right).
- **Status of the type: partly validated.** It caught a blatant reversal and a consistent pair, missed one of the two real known conflicts, and did not settle the CX2 label. Quote no per-finding score as evidence beyond F6.

## Experiments E0-E4: replacing my labels and my explanations (30 Sep 2026)

Rules fixed before any of these calculations or requests. Ground truth comes from how a pair was made or from observed behaviour, not from my reading of it.

- **E0, leave-one-out** (existing 34 answers, no requests): drop each of the 6 controls in turn. The type passes only if every drop leaves a control gap of at least 0.30 in both wordings.
- **E1, controls built by construction:** 20 base rules (exact sentences from `voice/` and the skills, each with one flippable term). Per base: A = the sentence, B-same = my faithful paraphrase (consistent), B-flip = the paraphrase with one term flipped (conflict). A blind Codex labels all 40 shuffled and unlabelled; a pair stays only if Codex's label equals the construction label, and dropped pairs are listed. Jev, Choice question, wordings A and B. **Pass:** `cannot_both_be_followed` chosen for at least 85% of kept conflicts and at most 10% of kept consistent pairs, in both wordings. Report the AUC and every miss.
- **E2, question shape:** a Noul "Is there a task where obeying A breaks B?" against the Choice, on the kept E1 pairs, then on the 6 old controls and 8 findings, wording A. A shape is better only if it meets the E1 rule and the other does not.
- **E3, ablation:** for F10, F11, CX1 and CX2 add one `note` sentence stating the practical consequence, wording A. "Moved" means the conflict probability changes by more than 0.15 (wording noise 0.03 plus repeat span 0.12). Moved: the miss was in the state. Not moved: the model misses it even when told.
- **E4, behavioural:** 12 haiku subagents (4 pairs x 3 runs), one concrete task each, single-word answer; count which rule each obeys. A pair is a behavioural conflict if runs split or all runs break one rule.
- **Not sent:** no `glossary` field; nothing from `loop/`, `ledger/`, `drafts/`, `shipped/`, `receipts/`. Request cap raised to 200.

### Results E0-E3 (30 Sep 2026)

- **E0, leave-one-out: fails.** Dropping the planted pair CX3 leaves a gap of 0.17 (A) and 0.11 (B), under 0.30. Every other single drop passes (0.40-0.64). The first run's "valid" verdict rested on that one synthetic pair, now a measured fact.
- **E1, controls built by construction: passes.** 20 bases gave 40 pairs. Blind Codex agreed with the construction label on 39; B04f (a flip to "at least 1 in 15") was dropped as not a conflict by its reading. On the 19 kept conflicts and 20 kept consistent pairs: sensitivity 0.95, false alarm 0.00, AUC 1.00, in both wordings. The single miss is B20f ("rule state is already applied" as the flip of "rule state is none"), in both wordings. These flips negate the sentence on the page; the pass says nothing about conflicts that need a task to appear.
- **A tell in the first run.** CX3's second passage was shown under the source "planted sentence"; the built pairs show both passages under the same file name. Whether the label inflated CX3's 0.99 and 1.00 is unverified.
- **E2, Noul shape: also passes E1 (sensitivity 1.00, false alarm 0.00, AUC 1.00), so by the pre-set rule neither shape is better.** On the real pairs Noul compresses toward 0.5: consistent controls scored 0.23-0.43, the known conflicts CX1 and CX2 0.48, F6 0.84, F10 0.56, F3 0.55, F8 0.53.
- **E3, ablation:** a note stating the practical consequence moved CX1 from 0.33 to 0.97 and CX2 from 0.05 to 0.25 (both over the 0.15 bar), and did not move F10 (0.15 to 0.24) or F11 (0.02 to 0.13). Told the consequence, Jev still called F10 and F11 followable. A note that states the conflict may just hand Jev the answer (unverified).
- **Slip:** F6 and F10 first read the working tree, which changed when the `voice/` reconciliation was committed (`1b60b91`); a few requests used the new text before I pinned both to `260bd45`. The first-run report reproduces exactly after the pin.
- **Requests:** 174 so far, about $0.004 (arithmetic).

### Result E4, behavioural (12 haiku runs, 30 Sep 2026)

Each agent read both passages (F6 and F10 at the pre-reconcile text `260bd45`) and one task. Answers were unanimous in every pair: F10 (free text) 3 of 3 ended at the thank-you with no question, obeying the tool-swap format over voice; F6 3 of 3 DRAFT, obeying tool-swap over voice's "own test"; F5 3 of 3 POINTS, obeying voice's "never paste-ready text" over the shout-out card; CX1 3 of 3 SKIP, obeying AGENTS.md's "only loop.py writes ledger/raw" over `/posted` step 2.

- **What it shows:** in each pair a small model broke one rule, the same one every time. Direction of resolution: the format skill over the general voice rule (F6, F10), the general voice rule over the format skill (F5), the contract over the step skill (CX1).
- **Design flaw, mine:** F5, F6 and CX1 were forced two-option tasks whose options I wrote as one-obeys-each, so any pair would look like a conflict. Only F10 (free text) could have shown both rules obeyed, and it did not. E4 therefore measures which rule wins, not whether a conflict exists; by the pre-set rule (all runs break one rule) all four count, but for three of them that is by construction. One model, three runs each.
- **Against Jev's Choice answers (first run):** Jev chose conflict only for F6 (0.51 and 0.57); blind Codex for CX1, F6 and F10, not F5.

## Experiments T1-T3: which of my explanations hold (30 Sep 2026)

Rules fixed before any request. Tasks, notes and trims below are written before any answer is seen.

- **T1, a question that names the task.** Choice, options `yes_obeys_both`, `no_must_break_one`, `task_not_covered`, with one task line in the state. Tasks: CX1 "Record a posted thread: read it with x_api.py and store the output." CX2 "Choose how to draft the next exploit-slot post when learnings.md has an adopted lesson whose rule is none." CX3 "A reader raises a caveat about a live post and the agent must respond." CK1 "Write the root post of a build-log." CK2 "Start a non-trivial drafting session." CK3 "Judge the lane of a PAID → FREE post." F3 "Judge the lane of a post that asks a question containing a factual assertion." F4 "Complete the tool-swap checklist when a revised draft still needs approval." F5 "Write the shout-out reply under a PAID → FREE post." F6 "Draft a PAID → FREE post when the operator has tested none of the tools." F7 "Finish a verify run in which one candidate stays VERIFY." F8 "Draft a control-arm post." F10 "Write the maker shout-out card." F11 "Begin a draft in a session that is not in Plan mode." **Detects** if P(`no_must_break_one`) is at least 0.5 on CX3, CX1, F5, F6 and F10 (the planted pair and the four where the E4 agents broke one rule) and at most 0.2 on CK1-CK3. The other six are reported, not scored.
- **T2, does a false note steer?** Add "Passage A tells the agent to do something that passage B forbids, so the agent cannot follow both." to CK1-CK3, Choice wording A. Steering is shown if any control passes 0.5 or the mean rises more than 0.15.
- **T3, distractor trim.** CX1 with passage B cut to its save sentence; F10 with B cut to "Ends at the thank-you"; F5 with B cut to the shout-out heading and the thank-you line. Choice wording A. "Moved" means a change over 0.15 against the untrimmed answers (0.33, 0.15, 0.01).
- Request cap stays 200; this adds about 20.

### Results T1-T3 (30 Sep 2026): 20 requests, 194 in total, about $0.005 (arithmetic)

- **T1, task named: fails its rule.** P(`no_must_break_one`) at least 0.5 was needed on five pairs; it held on the planted CX3 (0.99) and F6 (0.81) and missed CX1 (0.20), F5 (0.09) and F10 (0.26), where E4 agents broke one rule every time. The consistent controls passed (CK1 0.04, CK2 0.01, CK3 0.11). Reported, not scored: CX2 0.20, F3 0.48, F4 0.36, F7 0.31, F8 0.17, F11 0.13. Naming the task did not raise detection, so "the question was too broad" is not supported by this run.
- **T2, false note: no steering by the rule.** No control passed 0.5 and the mean rise was +0.147 (limit 0.15), but all three moved the same way: CK1 0.03 to 0.17, CK2 0.00 to 0.13, CK3 0.02 to 0.19. A note nudges by about 0.15 and did not flip any answer. The E3 true-note jump on CX1 (+0.65) is much larger than that nudge; the other three E3 pairs moved 0.09 to 0.20.
- **T3, trim: mixed.** F10 with passage B cut to "Ends at the thank-you" rose from 0.15 to 0.73 and is the only pair here that moved toward conflict. CX1 fell from 0.33 to 0.12 when its subject (the agent saving the file) was cut off, and F5 stayed near 0.01. Whether the F10 rise is less clutter or a sharper contrast with passage A is untested.
- **Reading (inference):** Jev is reliable on literal reversals and unreliable on conflicts that need an agent's task to appear, whether or not the task is named. What settled the real pairs in this work was blind Codex and the E4 behaviour runs.

## Experiments T4-T7: what online Jev users found, tested here (30 Sep 2026)

Rules fixed before any request. Pairs P53 = the 14 real pairs plus the 39 kept built pairs. Request cap raised to 500. Sent: the same quoted repo sentences (some at older git revisions), paraphrases, and question wording; no `glossary` field; nothing from `loop/`, `ledger/`, `drafts/`, `shipped/`, `receipts/`.

- **T4, option names** (Choice, wording A, P53): (a) random-string names (`k7`, `q2`, `m9`) with the same descriptions; (b) swapped names, where the name `both_followable` sits on the description that says they conflict and the reverse. The names matter if, under (a), the E1 rate rule (at least 85% of built conflicts and at most 10% of built consistent pairs, judged by the option whose description says "break") fails, or the mean absolute change on the 14 real pairs is over 0.15. Under (b), Jev follows the description if that rate rule holds and the name if sensitivity by description falls below 15%; in between, mixed.
- **T5, opposite polarity** (Noul "Can an agent always obey both passages together?", conflict probability = 1 minus the answer, P53): consistent with the E2 Noul if the mean absolute gap on the built pairs is at most 0.15 and the E1 rate rule holds for the new polarity. The sum of each pair's two answers is reported.
- **T6, the benchmark's probe** (Noul "Do passage A and passage B contradict each other?", P53): passes the E1 rate rule on the built pairs and scores at least 0.5 on at least 4 of CX3, CX1, F5, F6, F10 with CK1-CK3 at most 0.2. T1 got 2 of 5.
- **T7, natural experiment:** 8 before/after pairs from the fix commits (same two passages before and after the fixing text): ledger/raw, lessons, lane, plan mode, card count, own test, closing question, user/operator. A blind Codex labels all 16 shuffled and unlabelled; a pair is kept only when Codex calls the before state a conflict and the after state compatible. A question sees the fix if the conflict probability drops by at least 0.15 from before to after on at least 6 kept pairs (75% of the kept pairs if fewer than 8 are kept), for Choice wording A, the E2 Noul, the T5 Noul and the T6 Noul.
- A shape counts as better only by meeting its rule where the others do not. No pair or threshold changes after any answer is seen.

### Results T4-T7 (30 Sep 2026): 222 requests, 416 in total, about $0.01 (arithmetic)

- **T4a, random option names: pass.** Sensitivity 0.95, false alarm 0.00, AUC 1.00, the same as the semantic names; the mean change on the built pairs was 0.013 and on the 14 real pairs 0.025 (max 0.18). Names that match their descriptions did not steer.
- **T4b, swapped names: mixed by the pre-set rule, and the ranking reversed.** The rate rule failed (false alarm 1.00) and sensitivity by description was not under 15% (1.00), so the rule says "mixed". But P(name `both_followable`, described as "break") was 0.88 on consistent pairs and 0.70 on conflicts, AUC 0.01: Jev ranked by the name, against the description. The mean shift from the baseline was 0.55 (built) and 0.69 (real).
- **T5, opposite polarity: pass.** Mean gap between the two Noul polarities 0.059 (built) and 0.091 (real); the "always obey both" Noul met the rate rule (sensitivity 1.00, false alarm 0.00). The two answers summed to 0.997 on average on the built pairs (0.80-1.18) and 0.954 on the real pairs (0.75-1.13).
- **T6, plain contradict probe: rate rule passes, real-pair rule fails.** Built pairs: sensitivity 0.95, false alarm 0.00, AUC 1.00. On CX3, CX1, F5, F6, F10 it scored at least 0.5 on 2 (CX3, F6), the same as T1; CK1-CK3 stayed under 0.2. The gap to the E2 Noul on the 14 real pairs was 0.213.
- **T7, natural experiment: no question sees the fix.** Blind Codex labelled the before and after texts of 8 fix commits; only 3 stayed as before-conflict, after-followable (ledger/raw, own test, closing question). The other 5 (lessons, lane, plan mode, card count, user/operator) were read as followable before the fix, so five of the Pass 1 "contradictions" are not conflicts by a blind reading. On the 3 kept pairs, the conflict probability fell by 0.15 or more on 1 (Choice: +0.18, +0.14, -0.07), 0 (E2 Noul), 0 (always) and 0 (probe); the rule needed all 3. Three pairs is a small test.
- **Reading (inference):** for a sentence reversed on the page, Jev's answer did not depend on the question form (Choice, Noul, opposite-polarity Noul, plain probe, random option names), and for the conflicts that need an agent's task no form fixed the miss. A misleading option name does steer it. So more rewording is unlikely to help; the limit is what Jev reads, not how we ask.

## 1 Oct: routing run (pstack review scope), unvalidated use

`pstack_routing.py`: 20 requests, 6 task descriptions, Choice over models and agent types, options asked in both orders. Routing is outside the validated question types, so no score is evidence. Sent: task descriptions only. Answers in `private/pstack-routing/`.

- Controls: mechanical rename picked haiku-4.5 (0.44, 0.46); novel architecture picked opus-5.5 (0.72, 0.69). Direction right, margins small.
- Read tasks T1-T3: model opus-5.5 in 5 of 6 (probabilities 0.39-0.52, sonnet 0.27-0.39 close behind); agent type literature-reader in 4 of 6 but flipped with option order on T1 (general-purpose 0.41 fwd, literature-reader 0.55 rev) and on T3 fwd (0.40 vs 0.34).
- Synthesis T4: sonnet-5.5 (0.67, 0.73), general-purpose (0.84, 0.79), stable under reordering.
