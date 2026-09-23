---
name: ready
description: >
  Check an approved draft through the gate and copy its cards to the
  clipboard one at a time for pasting into X.
disable-model-invocation: true
argument-hint: "<slug>"
---

# Ready

1. Find the draft folder for the slug (`drafts/*-<slug>` or the queue row's `draft:`).
2. Run `python3 scripts/post_thread.py <folder>`.
   - **Exit 2, `human gate`:** say "Not approved yet. Read the cards, then type /approve <slug>." Stop.
   - **Exit 1:** turn each `REFUSED:` line into a plain sentence: what is wrong, which card, and the fix. "Cards changed after approval" means read them again and retype `/approve <slug>`. Offer to fix card problems; never touch `APPROVED`. Stop.
   - **Exit 0:** continue.
3. Show the run sheet: how many posts, each card's length, what to attach.
4. Run `python3 scripts/post_thread.py <folder> --copy 1`. Say: "Card 1 is on your clipboard. Post it as a new post on X." If it names an attachment, say which file (Finder has it selected).
5. Each time the operator says `next`, run `--copy N` for the next card and say: "Card N is on your clipboard. Post it as a reply to card N-1."
6. After the last card: "When it's all live, type /posted <link to the first post>."

Never paste or post anything yourself. This skill has no X write access and must not look for one.
