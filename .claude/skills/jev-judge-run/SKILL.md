---
name: jev-judge-run
description: >
  Jev judging of repo text or decisions as build-phase research: checks
  glossary definitions, rubrics or labels against the repo's own usage, or
  whether two passages conflict. Not for design-card votes (jev-card) or
  anything in scripts/ or the product path.
---

# Jev judge run

Plain English to the operator. Research only: code lives in `research/jev-test/`, never `scripts/`. Reuse the request checks and Keychain read in `scripts/jev_design_vote.py`; never run `security` yourself and never print a key. Jev supplies one rater's probabilities; the operator decides policy. Record every run in `research/jev-test/README.md`.

Jev suits semantic reading of text: does a definition match a usage, is a term used in one sense, does a definition mention an implementation detail. Routing between documents and checking claims against code stay with you.

## Conflict questions (do two passages clash?)

Measured 30 Sep; rules and results are in `research/jev-test/README.md` (the run script stays local, uncommitted). On a sentence reversed on the page Jev caught 18 or 19 of 19 built conflicts and flagged none of 20 consistent pairs, in every question form tried (Choice, Noul, opposite-polarity Noul, plain "do they contradict?", random option names). It missed conflicts that only appear when an agent does a task, in every form and with the task named, and it did not register the 3 fixed conflicts that survived a blind check.

1. **First pass only.** Check a changed sentence against its neighbours. A "followable" is no clearance: send every pair to a blind Codex, and settle a real conflict by what fresh agents do on a concrete free-text task.
2. **Do not reword to rescue a miss.** Five forms scored alike on built pairs and alike on the real misses. Re-ask in the opposite polarity as a cheap check (the two answers summed to 0.95-1.0 on average, range 0.75-1.18) and send disagreement to the second rater.
3. **Send the disputed sentence and who acts in it,** not the whole section. Cutting one pair to the sentence lifted it from 0.15 to 0.73; cutting another to a sentence without its subject dropped it from 0.33 to 0.12.
4. **Read a Noul as a band:** below 0.3 no, above 0.7 yes, between goes to a second rater (10 of 14 real pairs landed between).
5. **Controls are built, not labelled by you:** edit one term of a real sentence for the conflict, paraphrase it for the consistent pair, and keep a pair only where a blind second rater agrees with how it was made. Run leave-one-out on the control gap; the first run passed on one planted pair and failed it. Before/after pairs from fix commits count only where a blind rater calls the before a conflict and the after followable (3 of 8 did).
6. **State no tell, no answer, no misleading name.** Show both passages under the same source label; add no note saying what the conflict is (a false note nudged consistent pairs up 0.13-0.17); name options after their meaning or with neutral strings (same answers), never a name that contradicts its description (it reversed the ranking, AUC 0.01). Pin each passage to a git revision so an old answer cannot belong to newer text.

## Before any request

Each step is done when its output exists.

1. **Snippets read.** Read every snippet you will send for the calibration terms, and a sample of the rest. Drop matches inside backticks and outside-source notes; dedupe; take at least 8 prose usages per rep. Open the file around each usage you will label (the whole line, plus its neighbours when it is short or ambiguous): a label made from a truncated grep hit is unreliable. Done when every labelled usage was read in full context.
2. **Calibration set hand-audited.** Read 16 usages of each calibration term. Label it clean (one sense), muddy (two or more) or general. Include muddy terms the glossary already admits.
3. **Senses found blind.** For the term under judgement (not the calibration terms), give Codex (read-only, pre-authorised) the usages unlabelled and shuffled, and ask it to group them by what the word refers to. Done when you hold a grouping you did not write. Give every sense it finds a cloze option: Jev cannot find a sense a card does not offer.
4. **Pass rule written.** Put the thresholds, the decision rules (what counts as overloaded, add, fold in, drop) and the controls in the README before the first request. Take thresholds from the questions' behaviour on controls, never from an earlier run's results. What only requests can measure (the noise floor in step 5) is measured in the pilot, and the margin it sets is written down before the remaining cards go out.
5. **Controls planted.**
   - **Known-bad inputs**, one per question type you will trust: a wrong definition for the faithful question, a definition full of file names for the implementation-detail question, a definition leaning on made-up words for the self-contained question.
   - **Known split**, for a one-sense verdict: 4 usages of each of two senses of one word, each line read in full, asked in the same wording as the judged question. Declare beforehand how far below the clean terms it must score. If it does not, the question cannot detect a split and its one-sense result is void.
   - **Noise floor**: ask the same snippets under two different proposed definitions, in the pilot (step 4). The shift is the definition noise, and a mixed-against-pure gap inside it is no finding.
   A question type is validated when its planted control passes. One that failed its control in an earlier run needs a second passing run before you trust it. Report every other type as unvalidated and quote none of its scores as evidence.
6. **Disclosure stated.** Tell the operator what leaves the machine: the snippets, your definitions, and everything else in each card's state (a `glossary` field carries `CONTEXT.md` text). Exclude `loop/inbox/`, `loop/followers/`, `ledger/`, `drafts/`, `shipped/`, `receipts/` and other people's data.

## Run

1. **Pilot** one clean and one muddy term. Read the answers: ranges plausible, controls pointing the right way. Send the rest only after that.
2. **Three reps**, each a different snippet sample, so variance shows. A question whose reps span more than 0.30 is unstable.
3. Keep policy in code beside the script; Jev only votes.
4. Name no sense or compound phrase in a one-sense question, and ask each control in the exact wording of the question it validates.

## Report

1. Calibration and control verdict first. If a control fails, stop and ignore that question's results; change no threshold or calibration term to pass.
2. Label every cause you did not verify as unverified. When a set you labelled scores at the extreme against its label, re-read those lines before explaining the score away.
3. Separate what Jev said from what you inferred.
4. Send contested calls to Codex or Grok read-only (pre-authorised) as a second rater, blind: no labels and no verdict.
5. Count requests and cost from the saved answer files.
6. Leave the research scripts uncommitted unless asked, and leave the target file (`CONTEXT.md`) untouched until the operator approves wording.

Which question types are validated, and why: `research/jev-build-time-evaluation-2026-09-27.md`, "Judging text with Jev".
