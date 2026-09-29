---
name: posted
description: >
  Record a live post in the ledger: the text actually posted, ids, time,
  media, differences from the draft, and production time.
disable-model-invocation: true
argument-hint: "<link to the first post>"
---

# Posted

1. Take the root id from the link (the number after `/status/`).
2. Read the live thread: run `python3 scripts/x_api.py thread <root id>`. It returns the root and the account's own thread cards in order. Note each one's id, time, text. It reaches only the 6 hours after the root and returns no media: for a card posted later, or for `media` and `ai_media`, use the draft's `images.md` and ask the operator. Save the output to `ledger/raw/<root id>-posted.txt` (it holds only the account's own posts).
3. Match the queue row: the row with `status: drafted` whose draft cards match the live text best. If unsure, ask the operator which slug. Read that row's `format`, `lane`, `experiment`, `arm`, `hypothesis`.
4. Compare the live cards with the draft cards, both ways, so an added or removed card is a difference. Put each difference in exactly one class:
   - `preference` — wording, length, order, emphasis, a changed title. Nothing factual changed.
   - `correction` — a fact fixed by the operator.
   - `deviation` — the post no longer follows the experiment arm (for example card count or length changed).
   - `violation` — breaks `voice/exit-zero.md` or one of the gate's refusals (`scripts/post_thread.py`), or carries an unsourced or loosened figure.
   One line each: class, card, what changed. A difference that is both a `violation` and a `deviation` takes `violation`, and the deviation rule in step 6 still applies.
5. Ask one question, once: "Roughly how many minutes did this one take, start to finish?"
6. Write `loop/inbox/post-<root id>.json`:
   ```json
   {"root_id": "…", "slug": "…", "format": "…", "lane": "main",
    "posted_at": "<root Timestamp as ISO UTC with Z>", "made_in_repo": true, "retrospective": false,
    "experiment": "E-00N or null", "arm": "treatment|control|none", "hypothesis": "…",
    "cards": [{"id": "…", "text": "…"}], "media": ["photo"], "ai_media": false,
    "production_minutes": null, "edits": [{"class": "preference", "card": "01-hook.md", "note": "…"}],
    "draft": "drafts/…"}
   ```
   `cards` lists the author's replies after the root, not the root itself. If the operator doesn't know the minutes, leave `production_minutes` null. If there is a `deviation`, set `arm` to `none` and `experiment` to null, and say the post will not count toward the experiment.
7. Run `python3 scripts/loop.py record-post --json loop/inbox/post-<root id>.json`. Continue only on `recorded: true`. If the daily run already recorded the post on its own (its record has `auto: true`), this record replaces it and keeps its reads. On "already recorded", set the queue row as in step 8 if it still says `drafted`, say so, and stop.
8. Set the queue row `status: posted`, `root_id: <id>`.
9. Tell the operator: when its snapshot is due (36 to 60 hours after posting; the daily job takes it), and list any `violation` found, since violations are never learned as preferences.
