# Jev design cards: what the research says

28 Sep 2026. A reading fan-out on two problems seen in six Jev design votes: the card writer may be steering the vote, and `ask_luke` mixes "none of the options fit" with "too close to call". This file is the synthesis. The five full reports are in `readers/`.

## How it was done

- Four readers, one per kind of source, each covering all five questions: TypeSafe's own material and this repo's earlier experiments (Sonnet); LLM choice bias and framing (Opus); abstention and calibration (Opus); human survey and decision methods (Opus). Jev chose the models; two picks under 0.50 confidence went to the operator.
- Every reader returned findings with an exact quote and a link, plus "contradicts our plan" and "searched, found nothing" sections.
- Codex (gpt-5.6-terra) was given only the five questions, with no seeds and no findings, and asked what it would look for. Its map was compared with ours to find gaps.
- The claims the plan rests on were checked against the full source text before being used here (see "Checked by the lead" below). Everything else carries the reader's quote but was not re-opened.
- Almost all LLM findings come from generative models picking letters or writing text. Jev scores named options and returns a probability map. Each finding is a hypothesis for Jev, not a fact about it.

## The five questions

1. How much does the card writer's framing (evidence, risk note, stated lean) move the vote?
2. Do option order and option names bias the choice?
3. Should `ask_luke` be split, dropped, or replaced by a separate "does any option fit?" check?
4. Does the same card get the same answer on repeat calls?
5. Do structured option descriptions sharpen the choice compared with plain strings?

## Headline

1. **Framing moving the vote is a known, documented behaviour, and it can be large.** TypeSafe's own jev-1.13 page says a "deliberately misleading framing … can move the answer". In one code-review study, a strong "this is safe" note dropped a model's detection from 97.2% to 3.6%. The experiment should measure how much, not whether.
2. **The stated lean has to be deleted, not labelled.** Humans and models both anchor on a recommendation even when told it is arbitrary; "ignore this" instructions don't fix it; and confidence doesn't change when the anchor works. Legal experts anchored on sentencing demands they had rolled with dice, with certainty "independent of the anchoring condition".
3. **Replace `ask_luke`, don't split it.** Three independent lines agree (human surveys, LLM calibration studies, reject-option theory): "too close" can be read from Jev's own probabilities, but "none fit" needs its own question, because a normalised distribution always picks something and confidence stays high when the right answer is missing. Extra escape options attract probability for reasons unrelated to the evidence.
4. **Stable is not unbiased.** Judges that repeat above 0.95 are still position-biased. Repeat calls and order swaps are separate tests. Our own Experiment 3 already showed repeats are stable (0 of 30 changed) while rewording is not (7 of 30).
5. **Confidence can't be the steering detector or the "none fit" detector.** Jev's confidence is exactly `(k × top probability − 1) / (k − 1)` for k options, so it carries no information beyond the top probability, and it moves with the option count.

## Findings by question

### 1. Framing

| Finding | Source | What it changes |
|---|---|---|
| TypeSafe: framing in state "can move the answer" | docs.typesafe.ai/model-jaggedness/jev-1.13 | Measure size, not existence |
| Framing effect scales with strength and is asymmetric ("safe" moved far more than "risky") | arXiv 2603.18740 | Arm: risk note at none / weak / strong, in both directions |
| Judges follow the prompt-favoured option: accurate when it is right, much worse when it isn't | arXiv 2604.16790 | Test cards where the lean and the evidence point to **different** options; otherwise tracking the writer looks like accuracy |
| A lean labelled random still anchors; certainty unchanged | Englich et al. 2006 | Delete `current_lean`; don't use confidence to detect steering |
| "Ignore the anchor", chain of thought and reflection don't remove anchoring | arXiv 2412.06593, 2505.15392 | The neutral arm removes fields; it doesn't instruct |
| Acquiescence: about 10% more agree with an assertion than choose it among rivals | Krosnick & Presser 2010 | Never ask "confirm X?"; always a choice among rivals |
| "Consider the opposite" beats "be fair" | Lord, Lepper & Preston 1984 | A "fails if …" line for every option instead of one risk note |
| Loss vs gain wording of the same facts flips choices | Kahneman & Tversky 1984 | Same frame for every option's risk line; invariance pairs in the test set |
| Models lean on the first piece of evidence | arXiv 2609.03148 | Arm: reverse evidence order |
| Detailed reasoning persuades even when wrong | arXiv 2509.16533 | Control the length of each option's supporting text |
| Evidence judged against every option (ACH); drop non-diagnostic items | Heuer 1999 | Evidence as an option × item grid, not prose |
| A dominated near-copy raises the option it resembles (decoy) | Huber, Payne & Puto 1982 | Prune dead options by rule; drop only the disproved, never the merely unproven (Heuer) |

### 2. Order and names

| Finding | Source | What it changes |
|---|---|---|
| TypeSafe cookbook: sibling options are asked in order, and "line order is significant" | docs.typesafe.ai hierarchical_classification | Order is in scope for Jev specifically |
| Jev: reversing candidates changed 3.25% (RewardBench) and 11.14% (JudgeBench) of decisions; no first-position preference | `research/jev-articles/Jev as a judge.md` | Jev-specific size to compare against |
| Most letter-option bias is token bias (A/B/C); a smaller, irregular position bias remains | arXiv 2309.03882 (PriDe) | The A/B/C literature mostly doesn't apply; measure position on Jev with no assumed direction |
| Order flips concentrate where the top two are close | arXiv 2308.11483, 2305.17926 | Report order effects by top-two gap. Q8 (0.44 vs 0.25) is that case |
| Direction flips with option quality (primacy when all good, recency when all weak); name bias exists | arXiv 2506.14092 | Arm: neutral codes vs descriptive names |
| Averaging over cyclic permutations helps; scoring options in isolation removes bias without improving accuracy | arXiv 2310.07712, 2608.11947 | Vote over all rotations and average; keep all options visible |
| A content-free input estimates the model's prior per option | Zhao et al. 2021; arXiv 2309.04992 | Control: the same options with state set to "N/A" |
| A writer who can reorder options can steer | arXiv 2607.24869 | Fix order by rule, never by the writer |

### 3. `ask_luke`

| Finding | Source | What it changes |
|---|---|---|
| "Too close" (ambiguity) and "none fit" (novelty) are two named rejection types; the first is read from the model's probabilities, the second usually needs a separate check | Hendrickx et al., arXiv 2107.11277 | Two signals, detected differently |
| Select with "none of the above" beats plain select on calibration (72.59 vs 53.17 Calibration-AUC); a separate yes/no check scores 73.79; select-then-check 75.34. The NOTA answer is used as a score and excluded from the pick | Ren et al., arXiv 2312.09300 (PaLM-2 Large, TruthfulQA) | Choice over real options plus a separate Noul |
| With the correct answer removed, models "maintain near-baseline confidence" | arXiv 2606.08239 | Confidence can't flag "none fit" |
| A "don't know" option drew people with opinions: 4.7% → 17.2%; data quality "not compromised by the omission" | Krosnick et al. 2002 | Extra escape options are cues, not measurements |
| A random word draws abstention as well as "Unknown" | Ling et al., arXiv 2507.16199 | Placebo-option control; splitting may double the pull |
| An "I don't know" option reduced bias when the winner was picked with it excluded | Choi et al., arXiv 2409.18857 | Variant: keep an escape option but read its mass, never let it win |
| Close rivals raise deferral (34% → 46%) | Tversky & Shafir 1992 | "Too close" is a real category; validate it against the top-two gap |
| Midpoints improved reliability; removing one scattered answers | Krosnick & Presser 2010 (citing O'Muircheartaigh et al.) | Support for keeping "too close" as a signal |
| TypeSafe cookbooks gate on a probability band (Choice under 0.60; Noul 0.30–0.70), not a point cut | consistency_choice / consistency_noul cookbooks | Threshold the "any fit?" Noul with a band |
| TypeSafe: a Noul and its negation aren't guaranteed to be consistent | jev-1.13 page | Word the Noul to mean exactly what's wanted; expect Choice and Noul to disagree sometimes, and set a rule for it |

**Where the evidence disagrees.** Codex found a psychophysics study where a "not sure" option improved fit to ground truth (Jenadeleh et al., arXiv 2305.00220), against Krosnick's survey result. They fit together: a "not sure" between two close options is the "too close" case, which the human evidence supports; "none fit" is the case that invites satisficing. Vision-classifier work (arXiv 2110.06207) says top probability can detect "none fit"; the LLM option-scoring study above says it can't. The removed-answer test below settles it for Jev.

### 4. Repeat calls

| Finding | Source | What it changes |
|---|---|---|
| Already settled here: 0 of 30 repeats changed a verdict; rewording changed 7 of 30 | `research/jev-build-time-evaluation-2026-09-27.md` | Light repeat check only; the risk is wording |
| Jev changed no decision across 96 repeats; four across 48 paraphrases | `research/jev-articles/Jev as a judge.md` | Same |
| Capable judges repeat above 0.95 and are still position-biased | Shi et al., arXiv 2406.07791 | Repeat stability can't stand in for the order test |
| Answer-distribution entropy didn't predict perturbation sensitivity in 7 of 9 models | Tjuatja et al., arXiv 2311.04076 | Test whether Jev's confidence predicts flips before trusting it |
| Hosted "deterministic" inference can drift across days and releases | Codex: arXiv 2607.24372 | Log model id and date; recheck across time |

### 5. Structured descriptions

| Finding | Source | What it changes |
|---|---|---|
| TypeSafe recommends `what` / `not_for` / `examples` for options the model confuses, with no measured effect | primitives/choice | Our test would be the first numbers |
| Format effects are large and don't transfer between models | Sclar et al., arXiv 2310.11324 | Measure on Jev; report a range over formats |
| Style (Markdown) is the largest judge bias measured | arXiv 2604.23178 | Structure every option or none, never mixed |
| Shared attributes get extra weight; gaps get filled in favour of the leader | Kivetz & Simonson 2000 | Every option fills every field ("none known" rather than blank) |
| Structure may help only by adding content | Codex | Arm: prose carrying the same fields, to separate content from syntax |

## Gaps the blind Codex map found

- A **"real evidence added"** condition, to separate legitimate updating from framing. Without it, any shift looks like bias.
- A **prose-with-the-same-fields** arm for question 5.
- **Drift over time**, not just repeats in one sitting.
- **Two kinds of test card**: ones with a checkable answer (a policy or constraint decides it) and genuinely ambiguous ones judged by more than one rater. It warned against calling the designer's preference ground truth, as the operator-labels memory also says.
- Analyse **probabilities mapped back to option identity**, not by display position.

Things the readers had that Codex didn't: the TypeSafe material and this repo's own results, the placebo-option control, the "read the escape option's mass, never let it win" variant, the lean-vs-evidence conflict cards, and the confidence arithmetic.

## Checked by the lead

Opened in the original and confirmed: the TypeSafe jev-1.13 framing sentence; Ren et al.'s five Calibration-AUC figures and the NOTA exclusion; Wang et al.'s "near-baseline confidence"; the code-review 240/247 → 9/247 collapse; Shi et al.'s RS above 0.95 with position bias "not due to random"; Choi et al.'s "excluding IDK"; Jenadeleh et al.'s "not sure" result; Krosnick et al.'s 4.7% → 17.2%; Englich et al.'s dice study; and the repo's own Jev numbers. The confidence formula was checked against the three live votes on 28 Sep (Q8, Q10, Q12). Secondary sources are marked in the human-methods report (Kahneman–Lovallo–Sibony, the Delphi textbook).

## What changes in the plan

**Card format** (to trial, not yet adopted):

1. No `current_lean`, no "current" or default label on any option.
2. The question is a choice among rivals, never "confirm X?".
3. Fixed decision criteria before the options.
4. Every option fills the same fields ("none known" if empty), all structured or all plain.
5. Evidence as an option × item grid, with non-diagnostic items dropped.
6. A "fails if …" line for every option, in the same frame, instead of one risk note.
7. No evaluative words from the writer ("clearly", "safer").
8. Options pruned only when a stated fact disproves them.
9. Order set by rule and averaged over rotations.
10. Real options only in the Choice. A separate Noul asks "does any listed option fit?". "Too close" comes from the top-two gap.

**Experiment arms** (to pre-register):

- **Framing:** lean absent / present / flipped; risk note none / weak / strong in both directions; one-sided vs balanced evidence; evidence order reversed; a "real evidence added" control; lean-vs-evidence conflict cards.
- **Order and names:** all rotations; neutral codes vs descriptive names; a content-free prior card.
- **Escape design:** A current `ask_luke`; B split; C real options + separate Noul (the recommended design); C′ escape option read but never allowed to win; a placebo nonsense option. Test cards: one clear winner, two near-equal options, and past cards with the eventual answer removed.
- **Repeats:** a light check within a day and a recheck on another day.
- **Structure:** plain vs structured vs prose-with-the-same-fields.

**Measures:** probability shift per option (by identity), top-choice flips, top-two gap, the "none fit" hit rate and false-escape rate, and whether confidence predicts flips. Thresholds set before the run.

**Policy consequence already known:** because confidence rescales by option count, a 0.50 confidence bar is stricter on cards with fewer options. Changing the option count (for example removing `ask_luke`) changes what the bar means. The gap between the top two options doesn't have that problem.

## Not settled by anything found

- No study of a stated lean inside a structured state for a probability-returning scorer.
- No study of option names vs descriptions for an API that scores named options.
- No direct comparison of a split escape option against a single one, for models or people.
- No repeat-call study of a scoring endpoint (as opposed to text generation).
- No direct test of structured vs plain option sets in a choice question.

These are the parts the experiment would add.
