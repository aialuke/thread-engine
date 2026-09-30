# JEV-as-a-Judge: Accept When Confident, Escalate When Unsure

**Yubo Li Yidi Miao Ramayya Krishnan Rema Padman**

Carnegie Mellon University

```
{yubol, yidim, rk2x, rpadman}@andrew.cmu.edu
```

## Abstract

LLM-as-a-judge enables evaluation across diverse tasks, but inference cost and confidence
reliability become critical at scale. We study
whether a decision-only judge can provide
an economical first pass and identify when
stronger evaluation is needed. Comparing
**jev-as-a-judge** with sixteen generative and
reward-model judges, with blinded human adjudication, we find it within three percentage
points of a state-of-the-art LLM judge, our
strongest comparator, on ordinary preference
and evidence-grounded factuality at 0.36% of
the comparator’s fee. Larger gaps arise when
judgments require checking a derivation or resisting an elaborately written wrong answer.
On several benchmarks, JEV’s gap to this comparator is concentrated in low-confidence decisions. A frozen cascade that accepts confident
verdicts and escalates uncertain ones retains
99% of the comparator’s accuracy at lower cost.

## 1 Introduction

Evaluation has moved from scoring answers on
fixed tasks to judging behavior across open-ended
ones. Before general-purpose LLM judges, NLP
evaluation combined human assessment with taskspecific automatic metrics, such as reference overlap for machine translation (Papineni et al., 2002).
Human judges can interpret context and apply nuanced criteria, but their time limits the scale of
evaluation. As LLMs extend across dialogue, reasoning, coding, and free-form generation, evaluation must cover a wider range of tasks, plausible
answers, and notions of quality. Many of these
judgments are difficult to reduce to a fixed reference or scoring rule (Zheng et al., 2023; Li et al.,
2025).

LLM-as-a-judge offers a way to scale this contextual assessment. A capable language model can
follow a natural-language rubric, compare candidate responses, and assess qualities such as correctness, helpfulness, and instruction following. The

Human as a judge
Expertise · manual effort
Decision

LLM as a judge
Scalable · text generation
Rationale + decision

JEV as a judge
Typed outputs · decision-only
Decision
Confidence

Figure 1: **From human assessment to decision-only
judging.** Human evaluation uses manual expertise,
while generative LLM judges can produce a rationale
alongside a decision. JEV directly exposes typed decisions and label probabilities, summarized as confidence.
The diagram illustrates evaluation interfaces; generative
baselines in our experiments also receive a decision-andprobability output contract.

same interface can be adapted to different tasks
by changing the rubric and inputs, making LLM
judges widely useful for benchmarking, response
selection, and training-data assessment (Zheng
et al., 2023; Li et al., 2025). Figure 1 places this
transition from human assessment to generative
judging alongside the decision-only approach studied here.

Reasoning models introduce a new tension into
this progression. Longer chains of thought can improve difficult judgments by allocating more com- putation to evaluation (Kim et al., 2026). That
capability also carries a cost: generating additional
reasoning tokens consumes computation and, under token-based billing, increases fees; sequential
generation adds latency. Even a short final verdict
may require substantial reasoning, and simple problems can receive extended computation with little
additional benefit (Chen et al., 2025). When evaluation is repeated across many responses and model
revisions, the cost of the judge becomes part of the
cost of developing and operating the system.

An equally important constraint is knowing
when a judgment can be trusted. LLMs asked to
report their own confidence can be overconfident,
assigning high probabilities to incorrect answers
(Xiong et al., 2024). Better prompting and stronger
reasoning can improve these estimates (Tian et al.,
2023; Yoon et al., 2025), but calibration remains
an empirical property of a model, task, and elicitation procedure. An automated evaluator needs
an uncertainty signal that can help distinguish routine decisions from cases requiring further scrutiny.
This makes the quality of confidence consequential
for both reliability and resource allocation.

These pressures motivate **jev-as-a-Judge:** evaluation through a decision-only interface that exposes a verdict and label probabilities directly. We
study TypeSafe JEV, a hosted service that accepts
natural-language instructions and structured inputs
and returns judgments over a specified output type
(TypeSafe AI, 2026b). Its interface provides the
two signals needed for selective evaluation: a candidate decision and a confidence measure derived
from its probability distribution. Our central question is whether this judge can provide an inexpensive first pass and identify the inputs that warrant
a stronger LLM. This requires testing its accuracy,
probability quality, and operating cost together; a
typed probability output alone does not establish
that it is calibrated.

We compare JEV with generative LLM judges
and reward models across preference, factuality,
and answer-adjudication tasks, supplemented by
style and answer-format checks. Generative baselines also receive a decision-and-probability contract without a rationale. We measure fees and
latency on a matched panel and use blinded human
adjudication to examine disagreements with the
strongest judge. The comparison concerns complete judge configurations, since JEV’s implementation is proprietary.

The results support a selective role for decision-

only judging. JEV is competitive on ordinary preference and evidence-grounded factuality at substantially lower measured cost, while difficult correctness and misleading answer style expose clear
limits. Within suitable workloads, its confidence
supports a cascade that accepts confident decisions
and escalates uncertain ones to stronger LLMs.
Reference-free prose and failures of threshold transfer show why that policy needs local validation.
Our contribution is an empirical account of where
inexpensive judging is sufficient, where additional
reasoning earns its cost, and when confidence can
connect the two.

## 2 Related work

**LLM-as-a-judge and presentation bias.** MT-

Bench and Chatbot Arena made strong LLMs practical evaluators and documented their position, verbosity, and self-preference biases (Zheng et al.,
2023). Balanced-order evaluation addresses presentation effects (Wang et al., 2024); rubric wording
adds variation of its own (Bagaria et al., 2026);
broader taxonomies separate scoring, ranking, and
selection (Li et al., 2025). We fix one output contract, the verdict a pipeline consumes, and measure
reversal, paraphrase, and style sensitivity within it.

**Reward models and judging benchmarks.**
PairRM learns pairwise comparison for ensembling
(Jiang et al., 2023); Skywork-Reward-V2 is a modern scalar reward model (Liu et al., 2026). RewardBench measures preference across chat, safety,
and reasoning (Lambert et al., 2025); JudgeBench
stresses objective correctness (Tan et al., 2025);
HaluEval supplies evidence-grounded hallucination labels (Li et al., 2023). RewardBench 2 adds
harder multi-response selection (Malik et al., 2026),
and RM-Bench varies answer style and subtle content (Liu et al., 2025). We use all of them, and
add a modern reward model so that an older ranker
does not define the frontier of efficient judging.

**Confidence and economical escalation.** Verbalized confidence can be informative in feedbacktuned models (Tian et al., 2023), with judgespecific evidence on its reliability (Hsiao, 2026).
Temperature scaling calibrates probabilities (Guo
et al., 2017); selective classification trades coverage for risk (Geifman and El-Yaniv, 2017). Frugal-
GPT cascades models to cut generation cost (Chen
et al., 2024), and RouteLLM learns routing from
preference data (Ong et al., 2025). Closest to us,

---

Jung et al. (2025) cascade LLM judges with humanagreement guarantees, and Xu et al. (2025) route
uncertain reward-model comparisons to a strong
LLM judge. We contribute an empirical operating
profile of a hosted decision-only judge, with frozen
thresholds and measured fees, not a new routing
algorithm.

## 3 Tasks and experimental protocol

A judge’s output type is not its task. A judge
that returns only a label can still assess free text,
so we separate the *evaluated answer format* from
the *judge output.* The tasks cover pairwise ranking of generated prose, single-answer assessment
against supplied evidence, and adjudication of final
multiple-choice or numeric answers. They demand
different semantic work, and a typed output alone
earns nothing on closed-answer tasks.

**Public benchmarks.** RewardBench contributes
400 pairs, 100 from each broad category (chat, difficult chat, safety, reasoning), after exact duplicate
triples are removed (Lambert et al., 2025). This
balanced sample does not reproduce the official
subset weighting, and its labels have mixed origins. JudgeBench contributes its complete 350-
pair GPT-4o split across knowledge, reasoning,
mathematics, and coding (Tan et al., 2025); the
Claude split is not used. HaluEval contributes 240
evidence-grounded judgments: 120 QA questions,
each with its reference answer and its hallucinated
answer, judged against the supplied evidence (Li
et al., 2023). Benchmark labels are kept as supplied.

**Existing data and controls.** An existing set
of 150 saved replies from multi-turn answerconsistency experiments (six generator models;
neutral, supportive, challenging, and referenceinformed follow-ups) tests final-answer adjudication: given the multiple-choice question, a trusted
reference, and one reply, extract the reply’s final commitment and label it correct, incorrect, or
no-answer (99/25/26). Annotator identity is unavailable, so these are existing-label agreement
scores. Two controls check elementary handling:
108 final replies from twelve nine-round GSM8K
conversations in which Qwen3-32B is repeatedly
challenged, all of them reference-correct, and 64
synthetic evidence judgments (support, contradiction, missing information, distractor) from sixteen
families. Rubrics and input fields appear in Ap-

pendix A.

**What was frozen and when.** The 642-item pilot
was frozen before any inference; its public tasks
were split 40/60 by source question into a *selection
set,* used only to fit temperatures and routing thresholds, and a *pilot test set* (Appendix A, Table 4). The
670-item extension was frozen before pilot accuracy was inspected and never touched a fit. The
initial window evaluated JEV, three GPT baselines,
and PairRM; the expansion reran JEV and added
model families on all 1,312 items after those results were known, so the extension is held out but
the multi-family comparison is exploratory. Later
windows added Skywork, the RewardBench 2 and
RM-Bench samples, and GPT-6 on those frozen
samples.

Each judge also receives 894 diagnostics: all
750 preference pairs in reversed order, plus two
repeated requests and one paraphrased-rubric request on 48 fixed examples. PairRM covers both
orders of the 750 pairs; the three earlier GPT baselines have matching retained data; 48 JEV primitive
comparisons from the initial window are reported
separately.

## 4 Judges and measurement

**JEV and the shared contract.** TypeSafe JEV is
a hosted service that takes structured state, naturallanguage instructions, and an allowed output type
(TypeSafe AI, 2026b). Choice returns probabilities over specified labels; Noul returns a yesprobability; Score returns probabilities over ordered rubric levels. Our primary experiments send
one Choice question per request. At collection time
JEV 1.13.0 charged $0.042 per million input tokens and nothing for output (TypeSafe AI, 2026d),
which is its price entry in Table 5.

JEV also returns a native confidence, a statistic of its distribution (TypeSafe AI, 2026c). Its
Spearman correlation with the maximum label
probability is 0.971, 0.999, and 0.948 on Reward-
Bench, JudgeBench, and HaluEval, so we use
q = max<sub>k</sub> p<sub>k</sub> throughout for confidence plots, error
detection, and deferral, and keep native confidence
for interface diagnostics. Appendix A shows an
exact request and response.

**Models and output contracts.** Table 1 compares
seventeen configurations: thirteen hosted judges
(JEV; GPT-4.1 mini, 4.1, 5.2, 5.4, 5.6 Sol, and 6
Astra; GPT-OSS 120B and Qwen3.6/3.8 27B on

---

Groq; Claude Sonnet 5; Gemini 3 Flash and 3.1
Pro) and four local baselines. The three earlier
GPT quality runs are marked as such; all thirteen
hosted models were timed afresh. Table 5 lists
exact identifiers, prices, and settings.

Generative judges receive the same instructions
and state as JEV and are asked for the decision and
label probabilities without a rationale. Their probabilities are verbalized estimates, whose calibration
is an empirical question (Tian et al., 2023; Hsiao,
2026). Reasoning models run at low effort, except
Qwen3.6 at its default with JSON object mode; the
other hosted judges use JSON schema constraints,
and the GPT-4.1 models temperature zero. These
settings entail different amounts of computation,
which the fee and latency measurements absorb.

Qwen3 and Qwen3.5 were unavailable on the
accessible Groq endpoints, so we serve official
Qwen3-32B and Qwen3.5-27B checkpoints on
one H100 (vLLM, BF16, temperature zero, nonthinking mode, constrained JSON); they are labeled
local and carry no API-equivalent price. PairRMhf runs in FP32 with its upstream 2,048-token pair
tokenizer; truncation affects seven RewardBench
and 59 JudgeBench pairs (67.7% and 53.3% on the
untruncated ones). It is an independent ranker with
a shorter context and no rubric, not an architectural
match.

The modern reward-model baseline is Skywork-
Reward-V2-Qwen3-8B (Liu et al., 2026), run on
a V100 in emulated BF16 with its official chat
template and a 16,384-token limit. It scores each
response separately; we compare the scalars and
give half-credit to exact ties. Its raw scores are kept
out of the probability-calibration metrics.

**Validity and metrics.** Every output is validated
for schema fields, label membership, finite probabilities, normalization (sum tolerance 0.025, to
accommodate rounded native probabilities), and
verdict–argmax consistency. Invalid outcomes
count as errors in accuracy; probability metrics
condition on valid outputs, with the denominators
kept. Nothing is repaired or rerun for a better answer; transient transport failures get at most three
attempts, all retained.

We report accuracy, macro-F1 on the existing
labels, multiclass Brier score, clipped NLL (floor
10<sup>−6</sup>), and ten-bin ECE. Error-detection AUROC
treats an error as the positive class with 1 *− q* as its
score. Paired differences use 2,000 source-question
cluster bootstrap resamples, which keep the two

HaluEval answers to a question, and all presentation variants of a pair, together.

**Latency and fees.** Timings from the bulk quality
runs are retained but not used for latency claims,
because their synchronous ledger caused client contention. Latency comes instead from a frozen 120-
decision panel (40 per public task, including both
answers to 20 HaluEval questions), run one model
group at a time with a persistent client, eight workers, a 0.12-second minimum start interval, and accounting kept off the timing loop; a 50-ms heartbeat records residual event-loop lag. Outcome latency excludes initial pacing and includes network,
provider, and retry time; it is neither intrinsic inference time nor throughput. The Groq Qwen endpoints impose a 32,000-output-token-per-minute
limit, so quota failures and retry delays can dominate their tails.

Fees use reported usage at collection-time prices,
including cached-input discounts and billed reasoning tokens; where usage is missing, a conservative
reservation is charged instead of zero. The headline fee uses the same panel; full 990-item publicworkload fees are also available. All dollar values
are estimates, not invoices.

## 5 Quality and operational trade-offs

**Ordinary preference and evidence-grounded
factuality.** On RewardBench JEV scores 92.2%
against GPT-6’s 93.5%, a paired difference of
−1.25 points (95% cluster interval [−3.8,1.5]);
on HaluEval, 87.5% against 86.7%, +0.83 points
([−1.25,2.92]). Benchmark labels are not the last
word, so a member of the team adjudicated, blind to
labels and judge outputs, every base item on which
the two judges’ correctness differs (Appendix I).
The adjudication favors GPT-6 more than the labels
do: it sides with GPT-6 on 17 of the 29 Reward-
Bench disagreements and with JEV on 5 (7 indecisive), a human-adjudicated difference of *−3.0*
points ([−5.3, −0.8]), and with GPT-6 on 8 of the
10 HaluEval disagreements (−2.5, [*−5.0,* −0.4]).
It also finds that 24 of the 26 HaluEval items both
judges “miss” carry labels the evidence does not
support; with those labels corrected, JEV scores
95.8% and GPT-6 98.3%. The tie on HaluEval is
therefore partly label noise near the ceiling, and the
summary that survives both label sets is that JEV
stays within three points of GPT-6.

---

| Judge | RewardBench (400) | JudgeBench (350) | HaluEval (240) | Existing labels (150) | Valid base responses |
| --- | --- | --- | --- | --- | --- |
| JEV 1.13 | 92.2 | 78.6 | 87.5 | 94.0 | 1312/1312 |
| GPT-4.1 mini† | 89.0 | 64.0 | 86.2 | 84.0 | 1312/1312 |
| GPT-4.1† | 90.8 | 71.7 | 87.1 | 92.0 | 1312/1312 |
| GPT-5.2† | 92.0 | 88.9 | 89.6 | 95.3 | 1312/1312 |
| GPT-5.4 | 93.0 | 90.9 | 88.3 | 92.7 | 1310/1312 |
| GPT-5.6 Sol | 93.2 | 93.1 | 89.2 | 95.3 | 1312/1312 |
| GPT-6 Astra | 93.5 | 93.1 | 86.7 | 96.7 | 1312/1312 |
| GPT-OSS 120B | 87.5 | 71.1 | 87.5 | 95.3 | 1289/1312 |
| Qwen3 32B local | 88.2 | 66.9 | 81.7 | 94.0 | 1311/1312 |
| Qwen3.5 27B local | 90.5 | 77.4 | 85.0 | 92.7 | 1312/1312 |
| Qwen3.6 27B | 87.0 | 72.3 | 83.8 | 93.3 | 1206/1312 |
| Qwen3.8 27B | 93.8 | 74.3 | 87.9 | 95.3 | 1303/1312 |
| Claude Sonnet 5 | 91.2 | 88.9 | 85.8 | 94.7 | 1308/1312 |
| Gemini 3 Flash | 92.8 | 76.0 | 83.3 | 95.3 | 1312/1312 |
| Gemini 3.1 Pro | 94.5 | 87.4 | 87.1 | 94.7 | 1312/1312 |
| PairRM (local)† | 68.0 | 54.3 | - | - | 750/750 |

Table 1: Base-order accuracy (%). Invalid outcomes count as errors. Validity covers all applicable base tasks;
PairRM and Skywork support preference pairs here. *†:* initial-window quality; *‡:* follow-up addition. Local Qwen
uses non-thinking inference; hosted reasoning models use low effort except Qwen3.6 (default). Skywork scalar-score
ties receive half-credit.

**Difficult correctness.** JudgeBench separates the
judges. JEV scores 78.6% against 93.1% for GPT-
5.6 and GPT-6, a paired difference of -14.6 points
([-18.9,-10.3]). The gap is widest in reasoning (68.4% versus 95.9%, *n* = 98) and coding
(76.2% versus 97.6%, *n* = 42) and narrowest
in knowledge (84.4% versus 90.9%, *n* = 154);
Figure 7 shows every domain. It is not label
noise: the adjudication sides with GPT-6 on 57
of the 69 disputed items and with JEV on one
(11 indecisive), a human-adjudicated difference
of −16.0 points ([−20.0, −12.3]), with reasoning,
coding, and math at 27–0, 9–0, and 7–0. Skywork scores 94.0% on RewardBench and 71.1% on
JudgeBench, a far stronger reward-model reference
than PairRM’s 68.0% and 54.3%.

**Existing labels and saturated controls.** On the
150 existing replies JEV reaches 94.0% with macro-
F1 0.923; GPT-6 reaches 96.7% and 0.947 (Table 7 lists every judge). The controls saturate: fourteen of the fifteen applicable configurations score
108/108 on the GSM8K trajectories and 64/64 on
the evidence controls, and Qwen3.6’s 105/108 and
61/64 are entirely invalid outputs, its valid judgments being all correct. These results confirm
elementary handling and discriminate little (Figure 16).

**Harder selection and answer style.** JEV, GPT-6,
and Skywork judge the same frozen follow-up samples: 100 RewardBench 2 four-way prompts and 80

RM-Bench prompts with nine style pairings in both
orders (Appendix E). On four-way selection JEV
scores 73.0% against GPT-6’s 75.0% (-2.0 points,
[-12.0, 8.0]). On RM-Bench, JEV scores 84.0%
when the two answers share a style but 74.8% when
the rejected answer is the more elaborately written
one, a within-source drop of -9.2 points ([-14.0,
-4.8]); GPT-6 moves from 93.3% to 94.6%, +1.3
([−1.9,4.2]). On the hard pairs the gap is -19.8
points ([-27.7, -12.7]). Choosing the right answer
and resisting a misleading style are different abilities.

**Answer format and gold-blind extraction.** A

multiple-choice reply can be graded two ways: adjudicate it directly against the reference, or extract
its final option without showing the reference and
compare in code. A follow-up on all 150 existing
replies compares the two under a four-way contract
that adds an *ambiguous* outcome, so its scores are
not comparable with the three-way 94.0% above.
JEV’s agreement moves from 91.3% under direct
adjudication to 86.0% under extraction (∆ = *−5.3*
points, [-14.0, 2.0]); GPT-4.1 mini’s from 87.3% to
87.3%. Extraction yields more ambiguous outputs
and an inspectable answer, but no agreement gain;
independent option-extraction labels do not exist,
so these are downstream agreement scores.

To hold content fixed while varying format, forty
frozen HaluEval questions supply six reply conditions, including revisions and abstentions, in both
multiple-choice and free-response form. JEV’s di- rect agreement is 100.0% on multiple choice and
92.5% on free response, a paired change of -7.5
points ([-11.7, -3.3]). Part of that gap is rubric
alignment, since transferred hallucination labels
can conflict with semantic equivalence. Appendix J
gives conditions, prompts, and examples.

**Natural prose with and without evidence.** Only

sixteen answers in the HaluEval QA sample exceed
twenty words, so we freeze two prose samples:
eighty summaries of forty HaluEval documents,
and eighty general responses balanced over existing
human hallucination labels (Li et al., 2023). JEV,
GPT-4.1 mini, and GPT-5.4 score 71.2%, 62.5%,
and 72.5% on the document-grounded summaries,
and 52.5%, 53.8%, and 55.0% on the reference-free
responses (JEV minus GPT-5.4: -1.2 points, [-10.0,
7.5], and -2.5, [-11.2, 6.2]). Without a reference, all
three are near chance and remain confident: mean
maximum probabilities of 0.90, 0.95, and 0.96, a
JEV Brier score of 0.815 with error-detection AU-
ROC 0.518, and a GPT-5.4 Brier score of 0.813
(Table 19, Figure 18). The two samples differ in
content and label provenance, so they show workload dependence rather than a pure format effect.

**A usable verdict is its own endpoint.** JEV satisfies the contract on every base item. Several constrained generative configurations do too; validity
is not unique to a native typed interface. Others fail
at the provider (structured-generation errors), at the
contract (semantic violations), or at transport (exhausted retries); Qwen3.6 in particular must be read
alongside its valid-only accuracy and rate-limit failures. Appendix C separates these mechanisms. A
failed call is not a reasoning error, but it is no judgment either.

**Measured latency and fees.** JEV’s median latency is 0.152 seconds and its fee $0.044 per 1,000
judgments, against 0.548 seconds and $0.390 for
GPT-4.1 mini and 1.885 seconds and $12.182 for
GPT-6: about 9 and 277 times cheaper on this
workload. Figure 2 shows all thirteen hosted configurations with their tails and uncertain charges;
Figure 8 plots quality against both.

**Operating envelope.** Table 2 collects the comparisons by workload. Where the content comes
with a reference or an evidence passage, or the decision is an ordinary preference, JEV sits within
three points of the strongest judge tested at one to
two orders of magnitude lower fee; among hosted
judges under $1 per 1,000 judgments it is the most

accurate on JudgeBench, tied for the most accurate on HaluEval, and within 0.6 points of the best
on RewardBench. Where the decision requires
checking a multi-step derivation or resisting a more
elaborate wrong answer, the gap to GPT-6 is 9–20
points and escalation is warranted. Reference-free
judgment of natural prose is a boundary for every
judge, not for JEV alone. Answer format explains
little of this: on the same forty questions JEV loses
7.5 points from multiple choice to free response,
far less than the differences between workloads.

## 6 Stability and probability quality

**Repeated requests and candidate order.** Three
diagnostics probe stability: repeated identical requests (stochastic variation), paraphrased rubrics
(formulation sensitivity), and reversed candidate
order, compared after mapping labels back to response identity (Zheng et al., 2023; Bagaria et al.,
2026). JEV changes no decision across 96 repeated comparisons on 48 examples and four across
48 paraphrases. Reversal changes 3.25% of RewardBench decisions and 11.14% of JudgeBench
decisions; both-orders-correct accuracy is 91.0%
and 74.0%. JEV picks the first position 48.9%
and 48.4% of the time, so the inconsistency is
not a positional preference: of the 39 inconsistent JudgeBench pairs, 14 are always-first and 25
always-second decisions. Between collection windows, seven JudgeBench decisions changed and
net accuracy moved by one item. Tables 14 and 15
and Figure 14 give the full diagnostics.

**Accuracy and uncertainty rank judges differently.** JEV’s Brier scores are 0.111, 0.297, and
0.176 on RewardBench, JudgeBench, and HaluEval; GPT-6’s are 0.104, 0.095, and 0.245. GPT-6
is both more accurate and better calibrated on the
hard comparisons, yet its JudgeBench strength does
not carry over to evidence-grounded uncertainty,
where JEV’s probabilities are the better ones.

Figure 3 shows the distributions of *q* and the reliability curves. At *q ≥* 0.9 JEV makes 10 errors
in 199 HaluEval judgments and GPT-6 28 in 233;
the coverages differ, so Figure 12 compares the
full risk–coverage curves. JEV’s error-detection
AUROC is 0.869, 0.745, and 0.863 on the three
tasks, GPT-6’s 0.891, 0.907, and 0.899 (Table 7).
Error ranking and calibration are separate properties: GPT-6 ranks HaluEval errors better despite
the worse Brier score. On JudgeBench, nine of
JEV’s 138 high-probability judgments are wrong.

$$
\mathrm{It}q\geq0.9\mathrm{JEV}
$$

---

**(a) Median ● and p95 ◇**

| Category | Median (Outcome latency, seconds; log) | p95 (Outcome latency, seconds; log) |
| --- | --- | --- |
| JEV 1.13 (120/120) | 0.15 | 0.15 |
| GPT-4.1 mini (120/120) | 0.55 | 0.55 |
| GPT-4.1 (120/120) | 0.58 | 0.58 |
| GPT-5.2 (120/120) | 1.68 | 10.0 |
| GPT-5.4 (120/120) | 1.44 | 6.0 |
| GPT-5.6 Sol (120/120) | 1.74 | 8.0 |
| GPT-6 Astra (120/120) | 1.89 | 3.5 |
| GPT-OSS 120B (116/120) | 0.55 | 1.5 |
| Qwen3.6 27B (108/120) | 1.96 | 17.0 |
| Qwen3.8 27B (120/120) | 1.52 | 4.5 |
| Claude Sonnet 5 (119/120) | 2.28 | 13.0 |
| Gemini 3 Flash (120/120) | 0.87 | 1.0 |
| Gemini 3.1 Pro (120/120) | 3.14 | 9.0 |

**(b) Reported usage + uncertain reservations**

| Category | Reported usage (USD / 1,000 judgments) | Uncertain reservations low (USD / 1,000 judgments) | Uncertain reservations high (USD / 1,000 judgments) |
| --- | --- | --- | --- |
| unlabelled 1 | 0.04 |  |  |
| unlabelled 2 | 0.39 |  |  |
| unlabelled 3 | 1.95 |  |  |
| unlabelled 4 | 4.19 |  |  |
| unlabelled 5 | 4.81 |  |  |
| unlabelled 6 | 6.09 |  |  |
| unlabelled 7 | 12.18 |  |  |
| unlabelled 8 |  | 0.22 | 0.43 |
| unlabelled 9 | 3.16 | 3.16 | 8.47 |
| unlabelled 10 | 3.02 | 3.02 | 5.02 |
| unlabelled 11 | 5.89 |  |  |
| unlabelled 12 | 5.04 |  |  |

Figure 2: Matched isolated panel: 120 judgments per hosted configuration, with 40 per public task. Left: median
(filled circle) and p95 (open diamond) outcome latency; the connecting interval is not a confidence interval. Right:
reported-usage fee per 1,000 judgments, extended by conservative reservations where usage is missing. One model
group runs at a time with eight workers and 0.12-second minimum starts. Row labels give valid judgments /
attempted items. Local models are excluded from this API comparison.

| Workload | Sample | JEV | Comparator | Δ (pp) [95% CI] | Guidance |
| --- | --- | --- | --- | --- | --- |
| Ordinary preference | RewardBench (400) | 92.2 | GPT-6, 93.5 | -1.3 [-3.8, 1.5] | Use JEV |
| Evidence-grounded factuality | HaluEval (240) | 87.5 | GPT-6, 86.7 | +0.8 [-1.3, 2.9] | Use JEV |
| Final-answer adjudication | Existing labels (150) | 94.0 | GPT-6, 96.7 | -2.7 [-6.5, 0.7] | Use JEV |
| Difficult correctness | JudgeBench (350) | 78.6 | GPT-6, 93.1 | -14.6 [-18.9, -10.3] | Escalate |
| Style-adversarial pairs | RM-Bench hard (480) | 74.8 | GPT-6, 94.6 | -19.8 [-27.7, -12.7] | Escalate |
| Matched-style pairs | RM-Bench normal (480) | 84.0 | GPT-6, 93.3 | -9.4 [-16.7, -2.9] | Escalate |
| Four-way selection | RewardBench 2 (100) | 73.0 | Skywork, 79.0 | -6.0 [-13.0, 1.0] | Validate first |
| Grounded summaries | HaluEval summ. (80) | 71.2 | GPT-5.4, 72.5 | -1.2 [-10.0, 7.5] | Validate first |
| Reference-free prose | HaluEval general (80) | 52.5 | GPT-5.4, 55.0 | -2.5 [-11.2, 6.2] | Not supported |

Table 2: Operating envelope for JEV. Accuracy (%) and paired JEV-minus-comparator differences with 95% sourcecluster intervals; comparators are the strongest tested per workload. Style-adversarial pairs reject the more elaborate
answer. “Not supported” means all tested judges are near chance. Guidance is descriptive. Human-adjudicated
differences appear in the text and Appendix I.

Temperature scaling fitted on the pilot selection set (Guo et al., 2017) transfers unevenly. On
the extension, JEV’s NLL improves from 0.333 to
0.284 on HaluEval but worsens from 0.449 to 0.475
on JudgeBench and from 0.205 to 0.232 on RewardBench (Table 12), and the fitted temperatures
point in different directions: 0.65 sharpens Reward-
Bench, while 2.15 and 4.45 soften JudgeBench and
HaluEval. No single temperature fits; each workload needs its own validation. Figure 11 compares
raw probability scores across judges.

**Equivalent interfaces can disagree.** In the 48-
example initial-window audit, aligned Choice,
Noul, and binary Score probabilities differ: the
mean Choice–Noul gap is 0.055, the Noul complement residual averages 0.045, and hard labels
disagree in 1 case. Co-question context, stochastic
variation, and rounding all contribute, consistent
with the documented interface limitations (Type-
Safe AI, 2026a); Figure 15 and Appendix G report
the rest.

---

**RewardBench**

| JEV maximum label probability | Correct (369) (Number of judgments) | Incorrect (31) (Number of judgments) |
| --- | --- | --- |
| 0.6 | 0 | 5 |
| 0.7 | 8 | 0 |
| 0.8 | 10 | 0 |
| 0.9 | 35 | 0 |
| 1.0 | 265 | 5 |

**JudgeBench**

| JEV maximum label probability | Correct (275) (Number of judgments) | Incorrect (75) (Number of judgments) |
| --- | --- | --- |
| 0.6 | 14 | 4 |
| 0.7 | 24 | 7 |
| 0.8 | 22 | 3 |
| 0.9 | 32 | 5 |
| 1.0 | 86 | 4 |

**HaluEval**

| JEV maximum label probability | Correct (210) (Number of judgments) | Incorrect (30) (Number of judgments) |
| --- | --- | --- |
| 0.6 | 1 | 3 |
| 0.7 | 1 | 7 |
| 0.8 | 4 | 1 |
| 0.9 | 7 | 0 |
| 1.0 | 175 | 5 |

| Mean maximum probability | JEV 1.13 (Accuracy within bin) | GPT-6 Astra (Accuracy within bin) | Claude Sonnet 5 (Accuracy within bin) | Gemini 3.1 Pro (Accuracy within bin) |
| --- | --- | --- | --- | --- |
| 0.56 | 0.36 |  |  |  |
| 0.66 | 0.67 | 0.60 | 0.64 |  |
| 0.74 | 0.85 | 0.70 | 0.80 | 0.50 |
| 0.82 | 0.90 | 0.76 | 0.97 | 0.56 |
| 0.96 | 0.95 | 0.96 | 0.97 | 0.97 |
| 1.0 |  | 0.98 |  |  |

| Mean maximum probability | JEV 1.13 (Accuracy within bin) | GPT-6 Astra (Accuracy within bin) | Claude Sonnet 5 (Accuracy within bin) | Gemini 3.1 Pro (Accuracy within bin) |
| --- | --- | --- | --- | --- |
| 0.54 | 0.37 | 0.34 | 0.60 | 0.74 |
| 0.66 | 0.70 | 0.60 | 0.64 | 0.82 |
| 0.74 | 0.75 | 0.55 | 0.82 |  |
| 0.82 | 0.77 | 0.82 | 0.93 | 0.85 |
| 0.94 | 0.92 | 0.96 | 0.97 | 0.89 |
| 1.0 |  | 0.98 |  |  |

| Mean maximum probability | JEV 1.13 (Accuracy within bin) | GPT-6 Astra (Accuracy within bin) | Claude Sonnet 5 (Accuracy within bin) | Gemini 3.1 Pro (Accuracy within bin) |
| --- | --- | --- | --- | --- |
| 0.56 | 0.38 |  |  |  |
| 0.66 | 0.34 |  |  |  |
| 0.76 | 0.58 |  |  |  |
| 0.82 |  |  |  | 0.41 |
| 0.86 | 0.72 | 0.61 | 0.31 |  |
| 0.96 | 0.91 | 0.87 | 0.92 | 0.88 |
| 1.0 | 0.95 | 0.88 |  |  |

Figure 3: Top: JEV maximum-probability distributions for correct and incorrect base judgments. Bottom: reliability
curves using the same statistic for selected current judges (bins with at least five valid examples; full counts retained).
Sparse bins and differing coverage limit visual ranking.

## 7 Error complementarity and deferral

A stronger judge earns its fee by fixing the first
stage’s errors, and the two judges err differently.
On JudgeBench GPT-6 corrects 60 of JEV’s 75 errors while JEV corrects nine of GPT-6’s 24; their oracle union reaches 95.7% (Figure 13). That bound
uses the labels. A deployable gate has to find the
errors from a signal available at decision time. Figure 4 separates JEV’s two outputs: the decision is
a candidate verdict, while confidence determines
whether to accept it or call a stronger judge.

**Confidence orders the errors.** Figure 5 bins the
990 base-order judgments by JEV’s maximum label probability *q.* Accuracy rises monotonically
with *q.* Pooled over the three tasks, JEV is right on
47.7% of the 65 items with *q* < 0.6, 76.5% of the
85 in [0.7,0.8), 93.9% of the 147 in [0.95,0.99),
and 99.1% of the 322 at *q* = 1. GPT-6 on the same
items moves only from 78.5% to 99.1%, so its advantage sits where JEV is unsure. On the items
JEV would accept at *q ≥* 0.9 the two are nearly interchangeable (95.8% versus 96.5%; 97.2% versus
98.5% under the human-corrected labels of Appendix I); on the items it would escalate, GPT-6
leads by 15 points (67.9% versus 82.6%). The pat-

$$
q.
$$

$$
q\geq0.9
$$

tern holds within each task (AUROC of *q* against
correctness 0.869, 0.745, and 0.863). That is the
case for a confidence cascade: accept JEV’s verdict
when it is confident and pay for a stronger judge
only on the rest.

**Single-order cascades.** The lower row of Figure 5 and Table 13 simulate this rule on the base
order, taking the fallback’s decision on escalated
items. At *τ* = 0.9 the pooled cascade escalates
34% of items and scores 91.3% against GPT-6’s
91.7% (99.6% retained; paired difference −0.40
points, [−1.21,0.31]) at 47% of GPT-6’s fee (44%
under the conservative usage bound), about $6.3
per 1,000 judgments. The signal carries real information: escalating the same 34% at random would
reach 88.1% and the label-aware oracle 94.4%, so
*q* captures half of the attainable gain. Per task, the
picture follows the envelope. On RewardBench the
cascade beats GPT-6 alone (94.0% versus 93.5%)
at 22% of its fee, because the two judges err on
different items. On JudgeBench, where JEV’s
mean *q* is only 0.81, the same threshold escalates
61% of items and retains 98.2% at 62% of the fee;
*τ* = 0.95 retains 99.1% at 74%. On HaluEval no
threshold moves label-based accuracy, because the

---

| Fallback judge | τ | Accept (%) | Cascade acc. (%) | Fallback acc. (%) | Δ (pp) 95% interval | Fee ratio |
| --- | --- | --- | --- | --- | --- | --- |
| GPT-5.4 | 0.90 | 53.7 | 91.4 | 91.6 | -0.2 [-1.2, 0.8] | 0.639 / 1.096 |
| GPT-5.6 Sol | 0.70 | 81.0 | 91.0 | 93.3 | -2.4 [-4.5, -0.2] | 0.288 / 0.380 |
| GPT-6 Astra | 0.90 | 53.7 | 92.5 | 93.1 | -0.6 [-1.8, 0.6] | 0.568 / 0.622 |

Table 3: Selected frozen two-order JEV policies on 510 extension preference pairs; all nine fallbacks appear in
Appendix Table 11. ∆: cascade-minus-fallback accuracy with a 95% paired cluster interval. Fee ratios include both
JEV orders: reported usage / conservative upper ratio. Results are offline simulations.

Rubric A B
Rubric + responses
JEV
Decision-only judge
Decision Confidence
Confident Confidence gate Unsure
Accept decision Escalate
Stronger LLMs
Final verdict

Figure 4: **Accept when confident, escalate when unsure.** JEV produces a decision and a confidence signal
derived from its label probabilities. Confidence controls
the routing gate: confident decisions are accepted, while
uncertain inputs are escalated to stronger LLMs, whose
decision supplies the final verdict. For pairwise judgments, probabilities are aligned and averaged across
both candidate orders before gating; the threshold is
validated per workload.

low-confidence items are largely the mislabeled
ones; under the human-corrected labels, *τ* = 0.8
escalates 11% of items and matches GPT-6’s 98.3%
at 13% of its fee. Nor must the fallback be the most
expensive judge: with GPT-5.6 the *τ* = 0.9 cascade reaches 91.9% pooled at about $3.4 per 1,000
judgments. These thresholds are read off the items
they are scored on; the frozen policies below are
the pre-specified test.

$$
\tau=0.8
$$

**Frozen two-order policies.** Let *p<sub>1</sub>(x,y*) be
JEV’s probability for the first-position response
when the candidates are shown as (*x,y).* The gate

$$
p_{1}(x,y)
$$

judges each pair in both orders and averages the
aligned probability of semantic response *A:*

$$
\bar{p}(A)=\frac{1}{2}\left[p_{1}(A,B)+1-p_{1}(B,A)\right].
$$

(1)

Exact ties get half-credit. For each fallback, the
threshold was chosen on the 96 pilot selection
pairs (64 RewardBench, 32 JudgeBench) to maximize coverage while keeping selection-set accuracy within two points of the fallback (Geifman and
El-Yaniv, 2017); invalid first-stage outputs always
defer. Grid and rule were fixed before the model
expansion, and the pilot test set and extension serve
only for evaluation.

At threshold 0.9 the GPT-6 cascade accepts
53.7% of the 510 extension pairs, scores 92.5%
against 93.1%, and uses 56.8% of the fallback’s fee
(62.2% under the conservative bound); the paired
change is −0.59 points ([−1.78,0.59]). Table 3
shows three representative policies; Appendix Table 11 lists every fallback. The rule does not always transfer: the GPT-5.6 policy accepts 81.0% of
pairs at threshold 0.7 but loses 2.35 points, beyond
its two-point tolerance, and three *τ* = 0.5 policies collapse to order averaging with no fallback
at all. GPT-5.4’s conservative fee ratio of 1.096
exceeds one because missing usage is charged as a
reservation. Live sequential latency and externally
validated thresholds remain open measurements.

**Where the signal weakens.** The cascade works
because JEV is unsure where it is wrong, and that
holds only inside the envelope. On the RM-Bench
follow-up (Appendix E), the AUROC of *q* against
correctness is 0.918 on easy pairs and 0.902 on
normal pairs but 0.770 on hard pairs, where the
rejected answer is the more elaborately written one:
there JEV is wrong on a third of the pairs it scores
in [0.9,0.95) and on 15% of those in [0.95,0.99).
A *τ* = 0.9 cascade to GPT-6 retains only 96.5% of
its accuracy on those pairs (90.8% versus 94.2%),
and reaching 98.7% takes *τ* = 0.95 and 58% escalation, whereas on the normal pairs *τ* = 0.9

---

**RewardBench (400)**

| Lower edge of the q bin (items in bin) | GPT-6 Astra on the same items (Accuracy, %) | JEV 1.13 (Accuracy, %) |
| --- | --- | --- |
| 14 | 79 | 35 |
| 19 | 79 | 59 |
| 23 | 82 | 86 |
| 31 | 84 | 91 |
| 39 | 92 | 95 |
| 72 | 93 | 96 |
| 97 | 96 | 94 |
| 155 | 99 | 100 |

**JudgeBench (350)**

| Lower edge of the q bin (items in bin) | GPT-6 Astra on the same items (Accuracy, %) | JEV 1.13 (Accuracy, %) |
| --- | --- | --- |
| 43 | 84 | 54 |
| 56 | 91 | 67 |
| 74 | 91 | 77 |
| 59 | 93 | 77 |
| 42 | 95 | 88 |
| 52 | 97 | 94 |
| 22 | 100 | 95 |
| 1 | 100 | 100 |

**HaluEval (240)**

| Lower edge of the q bin (items in bin) | GPT-6 Astra on the same items (Accuracy, %) | JEV 1.13 (Accuracy, %) |
| --- | --- | --- |
| 8 | 51 | 37 |
| 11 | 37 | 37 |
| 14 | 37 | 51 |
| 17 | 57 | 72 |
| 20 | 82 | 82 |
| 23 | 86 | 86 |
| 26 | 89 | 89 |
| 29 | 98 | 98 |

**Pooled (990)**

| Lower edge of the q bin (items in bin) | GPT-6 Astra on the same items (Accuracy, %) | JEV 1.13 (Accuracy, %) |
| --- | --- | --- |
| 65 | 79 | 48 |
| 86 | 82 | 61 |
| 85 | 84 | 77 |
| 104 | 85 | 81 |
| 92 | 92 | 89 |
| 147 | 94 | 94 |
| 89 | 96 | 94 |
| 322 | 98 | 99 |

| Fee relative to GPT-6 alone | GPT-6 Astra on the same items (Cascade accuracy, %) | JEV 1.13 (Cascade accuracy, %) |
| --- | --- | --- |
| 0.00 | 93.5 | 92.2 |
| 0.06 | 93.5 | 94.6 |
| 0.12 | 93.5 | 94.5 |
| 0.18 | 93.5 | 94.4 |
| 0.25 | 93.5 | 94.0 |
| 0.31 | 93.5 | 93.8 |
| 0.37 | 93.5 | 93.5 |
| 0.44 | 93.5 | 93.2 |
| 0.50 | 93.5 | 93.0 |
| 0.56 | 93.5 | 93.3 |
| 0.63 | 93.5 | 93.5 |
| 0.70 | 93.5 | 93.5 |
| 0.77 | 93.5 | 93.5 |
| 0.83 | 93.5 | 93.5 |
| 0.90 | 93.5 | 93.5 |
| 0.97 | 93.5 | 93.5 |
| 1.00 | 93.5 | 93.5 |

| Fee relative to GPT-6 alone | GPT-6 Astra on the same items (Cascade accuracy, %) | JEV 1.13 (Cascade accuracy, %) |
| --- | --- | --- |
| 0.00 | 93.0 | 79.0 |
| 0.06 | 93.0 | 79.5 |
| 0.12 | 93.0 | 79.0 |
| 0.18 | 93.0 | 77.0 |
| 0.25 | 93.0 | 77.0 |
| 0.31 | 93.0 | 77.0 |
| 0.37 | 93.0 | 77.0 |
| 0.44 | 93.0 | 77.0 |
| 0.50 | 93.0 | 76.5 |
| 0.56 | 93.0 | 76.0 |
| 0.63 | 93.0 | 75.5 |
| 0.70 | 93.0 | 75.0 |
| 0.77 | 93.0 | 74.5 |
| 0.83 | 93.0 | 74.0 |
| 0.90 | 93.0 | 73.5 |
| 0.97 | 93.0 | 73.0 |
| 1.00 | 93.0 | 73.0 |

| Fee relative to GPT-6 alone | GPT-6 Astra on the same items (Cascade accuracy, %) | JEV 1.13 (Cascade accuracy, %) |
| --- | --- | --- |
| 0.00 | 91.6 | 86.6 |
| 0.06 | 91.6 | 87.8 |
| 0.12 | 91.6 | 88.6 |
| 0.18 | 91.6 | 90.0 |
| 0.25 | 91.6 | 90.6 |
| 0.31 | 91.6 | 90.8 |
| 0.37 | 91.6 | 90.8 |
| 0.44 | 91.6 | 91.0 |
| 0.50 | 91.6 | 91.4 |
| 0.56 | 91.6 | 91.4 |
| 0.63 | 91.6 | 91.4 |
| 0.70 | 91.6 | 91.4 |
| 0.77 | 91.6 | 91.4 |
| 0.83 | 91.6 | 91.6 |
| 0.90 | 91.6 | 91.6 |
| 0.97 | 91.6 | 91.6 |
| 1.00 | 91.6 | 91.6 |

Figure 5: Confidence orders JEV’s errors. Top: base-order accuracy of JEV and of GPT-6 on the same items, by
bin of JEV’s maximum label probability *q* (item counts under the bins; AUROC of *q* against JEV’s correctness).
Bottom: single-order cascades that accept JEV’s decision when *q ≥ τ* and otherwise call GPT-6, for *τ ∈*
{0.5,0.6,0.7,0.8,0.85,0.9,0.95,0.99,1}, plotted against fee relative to GPT-6 alone (reported usage), with random
escalation at the same budget and the label-aware oracle that escalates JEV’s errors first. Table 13 lists the numbers;
the thresholds here are post hoc, unlike the frozen policies of Table 3.

$$
q\geq\tau
$$

$$
\tau\in
$$

already retains 99.6%. On reference-free prose the
AUROC is 0.518 and no threshold helps. Confidence routes well where the first stage is competent
but uncertain, and badly where it is confidently misled; validate the cascade on the kind of pairs it will
meet.

## 8 Conclusion

JEV is enough for a large class of judging work. On
ordinary preference, evidence-grounded factuality,
and final-answer adjudication it stays within three
points of the strongest judge tested, returns a valid
verdict on every item, and costs about $0.04 per
1,000 judgments at 0.15 seconds. Escalate when a
verdict requires checking a derivation or resisting
an elaborately written wrong answer, and trust no
tested judge to grade natural prose without a reference. Because JEV’s confidence marks where
its errors lie, the escalation can be automatic: accept when confident, escalate when unsure, and
keep 99% of GPT-6’s accuracy at 57% of its fee.
The measurements leave a short checklist. (1)
Judge preference pairs in both orders and average
the aligned probability. (2) Choose the escalation
threshold on a local selection set and re-check it on
held-out items; it did not transfer for every fallback.
(3) Count invalid outputs as errors when comparing
judges. (4) Treat confidence as an escalation signal,
not a certificate; check it on style-adversarial pairs

and validate any temperature per workload. (5)
Run a small local validation before extending the
envelope to a new workload. A usable verdict, a
correct decision, and reliable uncertainty are three
different things, and each has to be checked.

## Limitations

We evaluate one proprietary JEV version against
a chosen set of configurations. Training overlap
and benchmark contamination are unknown. Reasoning effort, model size, context limits, age, and
serving systems all differ, so this is not a computematched architectural comparison. Exact snapshots
are used where available, but some service aliases
and preview models can change; the earlier GPT
quality runs and the expansion are labeled as separate windows, and one repeated JEV anchor cannot
expose every model’s drift over time.

Decision-only prompts leave out generated explanations, explanation faithfulness, extended deliberation, and many grading rubrics. Verbalized
probabilities and native distributions arise from different mechanisms. Invalid judgments count as
errors in accuracy while probability scores condition on validity; the two denominators must not be
conflated. The local non-thinking Qwen settings
do not stand in for the unavailable Groq endpoints,
and PairRM has a shorter context and no rubric.

The expansion followed inspection of the orig-