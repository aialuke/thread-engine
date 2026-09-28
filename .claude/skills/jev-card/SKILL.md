---
name: jev-card
description: >
  Jev vote on a design card. Use when the user is grilling a design card and
  says the card is ready for Jev, or says "continue" after a Jev vote.
---

# Design grilling (Jev cards)

Run this only when the user is grilling a design card and says the card is ready for Jev. Ordinary coding work, spawn, commit, and delete stay off this loop. Leave `scripts/jev_referee.py` and `jev/thresholds.yaml` unchanged.

1. Write `{model, state, questions}` to `/tmp/jev-card.json`. That file is the request body, not a script. zsh parse-errors on a raw `{`.
2. Run `python3 scripts/jev_design_vote.py /tmp/jev-card.json`. That script is the only call. Do not run `security` yourself. If the script is missing, print one bash snippet Luke can paste into an already-open terminal: `curl` to `https://api.typesafe.ai/v1/systemone` with `--max-time 5`, the Keychain read in the snippet, and the body as `--data-binary @/tmp/jev-card.json` or a single-quoted heredoc (`<<'EOF'`). The snippet must not call `exit`. Then stop. No vote.
3. Quote answers only. Never quote a key. State the card's question in words before the choice.
4. Apply that card’s policy.
5. Print one design receipt line in chat. Do not append `receipts/decisions.jsonl`.
6. Stop.

If the script fails or the guard blocks it, say so. Do not invent a vote.

After a vote is applied and the user says "continue":

- If the user locked the last card, draft the next OPEN question from `reviews/ui-build-handoff/build-questions.md` dependency order (section 4).
- Skip ids already frozen or already Jev-audited (one-log, stop-hook, leave-shadow, and Q16 once locked).
- One card only. Then ask "Card ready for Jev?"
- Do not draft and vote in the same turn.
