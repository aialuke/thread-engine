# Independent research map

All named works below were opened. Transfers from human-subject research to the typed-judgement model are explicitly labelled as inference.

## 1. How much does the writer’s framing move the vote?

**Search strategy:** broad search: `framing effects decision making evidence recommendation stated preference risk information anchoring published papers`; then citation-chain from framing, anchoring, and survey-design reviews into AI judgement/annotation studies.

**Relevant bodies and works**

- Equivalency/emphasis framing and prospect theory: [Kühberger, “The Influence of Framing on Risky Decisions: A Meta-analysis” (1998)](https://pubmed.ncbi.nlm.nih.gov/9719656/?dopt=Abstract) synthesizes 136 studies and finds reliable but design-dependent framing effects.

- Description invariance in decision-making: [Kühberger, “A systematic review of risky-choice framing effects” (2023)](https://pubmed.ncbi.nlm.nih.gov/37927347/) treats preference changes under equivalent descriptions as the central concern.

- Anchoring: [Schley & Weingarten, “Fifty Years of Anchoring Effects: A Theoretical Reintegration and Meta-Analysis” (2026)](https://pubsonline.informs.org/doi/abs/10.1287/mnsc.2023.03238?journalCode=mnsc) reports a large pooled high-versus-low-anchor effect, with important moderation by whether an anchor is meaningful rather than incidental.

**Experiment**

Create a source-backed canonical corpus of decision cards and independently manipulate:

- evidence: balanced / absent / evidence made salient for one option;
- stated lean: absent / lean toward each substantive option;
- risk note: absent / risk emphasized for each option.

Hold options, evidence propositions, citations, card length, and output schema constant. Counterbalance the favoured option, randomize option order, pin model/configuration, and repeat every cell. Use a separate “information genuinely added or removed” condition to distinguish legitimate evidential effects from framing effects.

Primary measures: identity-mapped probability shift, Jensen–Shannon divergence from the canonical distribution, top-choice switches, entropy, reported confidence, and agreement between confidence and distribution concentration. Estimate effects with a hierarchical multinomial model, including card-level random effects and baseline uncertainty.

**Likely surprise**

The human literature does not say that wording universally “hacks” decisions. Effects are heterogeneous: a stated lean is plausibly a meaningful directional anchor, whereas an arbitrary flourish may do little. That mapping to card fields is an inference, and is why lean, evidence, and risk should be experimentally separated.

## 2. Do option order and option names bias the choice?

**Search strategy:** broad search: `response option order effects survey questions primacy recency randomized experiment meta analysis published papers option labels`; then trace survey primacy/recency work and LLM multiple-choice robustness work.

**Relevant bodies and works**

- Direct LLM multiple-choice robustness: [Pezeshkpour & Hruschka, “Large Language Models Sensitivity to The Order of Options in Multiple-Choice Questions” (2023, preprint)](https://arxiv.org/abs/2308.11483) reports substantial benchmark changes when answer options are reordered, particularly around close alternatives.

- Survey primacy/recency: [Holbrook, Krosnick, Moore & Tourangeau, “Response Order Effects in Dichotomous Categorical Questions Presented Orally” (2007)](https://academic.oup.com/poq/article/71/3/325/1856101?login=true) analyzes 548 survey experiments and finds recency effects concentrated in difficult questions and complex options.

- Wording and response-category design: [Kalton, Collins & Brook, “Experiments in Wording Opinion Questions” (1978)](https://academic.oup.com/jrsssc/article/27/2/149/6953736) covers option wording, order, and context effects on response distributions.

- Web-survey layout moderation: [Terentev & Maloshonok, “The impact of response options ordering on respondents’ answers to rating questions” (2019)](https://publications.hse.ru/en/articles/222737669) finds primacy in item-by-item ratings but not grid presentation.

**Experiment**

For each card, run all option permutations for three- and four-option cards; use a balanced Williams/Latin-square design for larger sets. Separately vary names while preserving descriptions exactly:

- descriptive names;
- neutral identifiers;
- token/length-matched arbitrary names.

Counterbalance which substantive option receives each name. Include clear cards and close cards, with the pre-registered prediction that bias will be greatest when the baseline distribution is diffuse.

Analyse probabilities mapped back to substantive-option identity, rather than displayed position: positional coefficients, name coefficients, top-choice changes, entropy, confidence, and a practical invariance threshold.

**Likely surprise**

There is no universal “first-option bias.” In human studies, modality, option complexity, mutual exclusivity, layout, and difficulty determine whether primacy, recency, or no material bias emerges. Recent LLM results likewise suggest that concentration of the probability distribution is a key moderator.

## 3. What should happen to “ask the human”?

**Search strategy:** broad search: `survey methodology 'don't know' response option separate no opinion none of the above experimental study`; citation-chain through abstention, item nonresponse, forced-choice, and uncertainty-measurement research.

**Relevant bodies and works**

- Survey no-opinion/DK design: [“Estimating public opinion from surveys: the impact of including a ‘don't know’ response option in policy preference questions” (2024)](https://www.cambridge.org/core/journals/political-science-research-and-methods/article/estimating-public-opinion-from-surveys-the-impact-of-including-a-dont-know-response-option-in-policy-preference-questions/77F4AFF4FCF5D2E547C85B17FE3E2A58) is a preregistered experiment with 4,810 respondents; displaying DK greatly increased non-substantive responses and effects varied by question difficulty.

- Ambiguity of a single DK response: [“Capturing richer information: On establishing the validity of an interval-valued survey response mode” (2021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9170647/) argues that a single DK choice conflates limited knowledge, uncertainty, and opting out.

- Relaxed versus forced choice: [Jenadeleh et al., “Relaxed forced choice improves performance of visual quality assessment methods” (2023)](https://arxiv.org/abs/2305.00220) compares binary forced choice with a “not sure” option; in its within-subject study, the extra option reduced reported mental demand and improved fit to known ground truth.

**Experiment**

Build a benchmark with three deliberately different situations:

1. one substantive answer is defensible;
2. the provided set lacks a defensible answer;
3. evidence leaves two options genuinely indistinguishable.

Compare:

- current generic “ask the human”;
- split options: “none fits” and “too close/insufficient evidence”;
- no escape option;
- a two-stage protocol: substantive choice, then a yes/no escalation check.

Keep escalation costs explicit. Measure false autonomous commitments, unnecessary escalations, correct diagnosis of the two escalation reasons, probability calibration, and whether the chosen answer remains evidence/policy-consistent. Include a blinded human adjudication panel for the benchmark labels.

**Likely surprise**

“Ask the human” is not one construct. A missing-option problem and epistemic uncertainty require different remedies; a generic escape hatch may make either one unmeasurable. The application to a model is an inference from survey and psychophysics evidence.

## 4. Does the same card get the same answer on repeat calls?

**Search strategy:** broad search: `research reproducibility stochastic language model outputs repeated inference calls temperature sampling reliability`; citation-chain through repeatability, inference nondeterminism, and repeated-sampling studies.

**Relevant bodies and works**

- Repeatability/reproducibility measurement: [“A statistical framework for evaluating the repeatability and reproducibility of large language models” (2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12637745/) distinguishes repeated runs under identical settings from reproducibility across changed settings.

- Sources of variation in hosted and local models: [Coqueret et al., “Randomness in large language models: What researchers need to know (and report)” (2026, preprint)](https://arxiv.org/abs/2607.24372) documents sampling, silent updates, rounding, batching, and expert routing; it argues that zero temperature reduces but does not necessarily eliminate variance in hosted inference.

- Repeated draws as a model property: [Brown et al., “Large Language Monkeys: Scaling Inference Compute with Repeated Sampling” (2024, preprint)](https://arxiv.org/abs/2407.21787) shows that repeated samples can reveal meaningful coverage not visible in a single generation.

**Experiment**

For each canonical card, make 100–500 repeat calls in two strata:

- tightly clustered calls under fixed model/version, prompt, configuration, and where available seed;
- scheduled repeats across days or releases.

Store the complete probability vector, confidence, raw response, timestamp, model identifier, settings, and request metadata. Report:

- exact top-choice agreement;
- rank-flip rate;
- vector variance and mean pairwise Jensen–Shannon divergence;
- intraclass correlation for each option probability;
- confidence/concentration stability;
- within-window versus across-time drift.

Use a controlled local/open-weight reference run when possible to separate model sampling from hosted-serving variation.

**Likely surprise**

Zero temperature is not synonymous with reproducibility for a hosted system. The most useful unit of analysis may be a distribution of votes, not one “deterministic” vote.

## 5. Do structured option descriptions sharpen choice versus plain strings?

**Search strategy:** first broad search: `research structured response options option descriptions cognitive decision making choice quality survey experimental`; because it did not yield three directly applicable studies, a second targeted search: `choice architecture structured information option descriptions decision quality cognitive load experimental study`; then citation-chain through information presentation and choice-architecture research.

**Relevant bodies and works**

- Presentation mode and objective choice quality: [Schneider et al., “Optimizing Choice Architectures” (2019)](https://pubsonline.informs.org/doi/10.1287/deca.2018.0379) experimentally compares presentation and response modes using objectively rankable choice sets; joint presentation outperformed separate presentation.

- Simultaneous versus sequential information: [“Choosing one at a time? Presenting options simultaneously helps people make more optimal decisions than presenting options sequentially” (2017)](https://www.sciencedirect.com/science/article/pii/S0749597816302060) reports seven experiments on how presentation architecture changes decision quality.

- Attribute-by-attribute comparison: [“Deliberation or distraction: How the presentation format of choice information impacts complex decision making” (2020)](https://www.sciencedirect.com/science/article/pii/S0148296319304035) compares sequential presentation with comparative, attribute-by-attribute presentation across three experiments.

**Experiment**

Use semantically identical options in a factorial comparison:

- plain strings;
- structured objects: `what`, `not_for`, `examples`, and perhaps `tradeoffs`;
- prose with the same fields and same information, but no object structure.

The third arm is essential: it separates the value of additional/organized content from the value of JSON-like syntax. Match token count as closely as practical, rotate field order and option order, control labels, and test simple versus multi-attribute cards separately.

Evaluate policy/ground-truth accuracy, probability mass on the adjudicated answer, appropriate escalation, calibration, entropy, confidence–concentration alignment, parse failures, and sensitivity to irrelevant formatting changes.

**Likely surprise**

There is no established reason that object syntax itself should be cognitively or statistically privileged. The strongest relevant evidence concerns comparative information architecture, not JSON. Any improvement from structured fields is therefore an inference to test, and may come from making trade-offs salient rather than from structure alone.

## Cross-cutting ideas

- Treat this as an **invariance and calibration** programme, not only an accuracy programme. A sound voter should preserve its substantive distribution under irrelevant changes and change it for genuinely new evidence.

- Use a common benchmark with two ground-truth types: formally checkable policy/constraint cards and expert-adjudicated, genuinely ambiguous cards. Do not call a designer’s preference “ground truth.”

- The output’s full probability vector is the primary data. Record top choice, entropy, confidence, and the agreement between confidence and concentration; top-choice agreement alone hides important instability.

- Pre-register practical thresholds before measuring. For example, define what probability movement, switch rate, false autonomy rate, or escalation rate is unacceptable.

- Preserve every tested card variant and raw output. This is necessary to distinguish prompt/card effects from silent model or serving changes.

- A fractional factorial can test all five questions efficiently: frame condition × order/name condition × escalation design × representation, with repeated calls nested within each cell. Start with pilot estimates of effect size and variance, then power the full study from those estimates.

No repository files were read or written.

