---
name: jev-card
description: >
  Jev vote on a design card. Use when the operator is grilling a design card and
  says the card is ready for Jev, or says "continue" after a Jev vote.
---

# Design grilling (Jev cards)

Run this only when the operator is grilling a design card and says the card is ready for Jev. Ordinary coding work, spawn, commit, and delete stay off this loop. Leave `scripts/jev_referee.py` and `jev/thresholds.yaml` unchanged.

1. Write `{model, state, questions}` to `jev-card.json` in the session scratchpad (`<scratchpad>/jev-card.json`). That file is the request body, not a script. zsh parse-errors on a raw `{`.
2. Run `python3 scripts/jev_design_vote.py <scratchpad>/jev-card.json`. That script is the only call, and the Keychain stays untouched by you. If the script is missing, print one bash snippet the operator can paste into an already-open terminal: `curl` to `https://api.typesafe.ai/v1/systemone` with `--max-time 5`, the Keychain read in the snippet, and the body as `--data-binary @<scratchpad>/jev-card.json` or a single-quoted heredoc (`<<'EOF'`). The snippet ends without `exit`. Then stop. No vote.
3. Quote answers only, and keep any key out of the quote. State the card's question in words before the choice.
4. Apply the card's own policy: the rule the card being grilled states for each answer. If the card states none, ask the operator.
5. Print one receipt line in chat: the card, its question in words and the answer Jev gave. Leave `receipts/decisions.jsonl` alone; it belongs to the referee hook.
6. Stop.

If the script fails or the guard blocks it, say so and cast no vote.

After a vote is applied and the operator says "continue":

- If the operator locked the last card, draft the next OPEN question from `reviews/ui-build-handoff/build-questions.md` dependency order (section 4).
- Skip ids already frozen or already Jev-audited (one-log, stop-hook, leave-shadow, and Q16 once locked).
- One card only. Then ask "Card ready for Jev?"
- Do not draft and vote in the same turn.
