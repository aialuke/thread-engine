---
name: jev-judge-run
description: >
  Jev judging of repo text or decisions as build-phase research: checks
  glossary definitions, rubrics or labels against the repo's own usage. Not
  for design-card votes (jev-card) or anything in scripts/ or the product path.
---

# Jev judge run

Plain English to the operator. Research only: code lives in `research/jev-test/`, never `scripts/`. Reuse the request checks and Keychain read in `scripts/jev_design_vote.py`; never run `security` yourself and never print a key. Jev supplies one rater's probabilities; the operator decides policy. Record every run in `research/jev-test/README.md`.

Jev suits semantic reading of text: does a definition match a usage, is a term used in one sense, does a definition mention an implementation detail. Routing between documents and checking claims against code stay with you.

## Before any request

Each step is done when its output exists.

1. **Snippets read.** Read every snippet you will send for the calibration terms, and a sample of the rest. Drop matches inside backticks and outside-source notes; dedupe; take at least 8 prose usages per rep.
2. **Calibration set hand-audited.** Read 16 usages of each calibration term. Label it clean (one sense), muddy (two or more) or general. Include muddy terms the glossary already admits.
3. **Pass rule written.** Put the thresholds, the decision rules (what counts as overloaded, add, fold in, drop) and the controls in the README before the first request. Take thresholds from the questions' behaviour on controls, never from an earlier run's results.
4. **Controls planted.** For each question type you will trust, include a known-bad input: a wrong definition for the faithful question, a definition full of file names for the implementation-detail question, a definition leaning on made-up words for the self-contained question. A question type without a passing control is reported as unvalidated.
5. **Disclosure stated.** Tell the operator what leaves the machine. Exclude `loop/inbox/`, `loop/followers/`, `ledger/`, `drafts/`, `shipped/`, `receipts/` and other people's data.

## Run

1. **Pilot** one clean and one muddy term. Read the answers: ranges plausible, controls pointing the right way. Send the rest only after that.
2. **Three reps**, each a different snippet sample, so variance shows. A question whose reps span more than 0.30 is unstable.
3. Keep policy in code beside the script; Jev only votes.

## Report

1. Calibration and control verdict first. If a control fails, stop and ignore that question's results; change no threshold or calibration term to pass.
2. Label every cause you did not verify as unverified.
3. Separate what Jev said from what you inferred.
4. Send contested calls to Codex or Grok read-only (pre-authorised) as a second rater.
5. Leave the research scripts uncommitted unless asked, and leave the target file (`CONTEXT.md`) untouched until the operator approves wording.

Which question types are validated, and why: `research/jev-build-time-evaluation-2026-09-27.md`, "Judging text with Jev".
