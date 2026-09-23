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
2. Read the live thread: `x_thread_fetch` the root when this session has it; otherwise run `python3 scripts/x_read.py thread <root id>`. Note the root and each of the author's own replies in order: id, time, text, media. Save the raw output to `ledger/raw/<root id>-posted.txt`.
3. Match the queue row: the row with `status: approved` or `drafted` whose draft cards match the live text best. If unsure, ask the operator which slug. Read that row's `format`, `lane`, `experiment`, `arm`, `hypothesis`.
4. Compare every live card with its draft card. Put each difference in exactly one class:
   - `preference` — wording, length, order, emphasis, a changed title. Nothing factual changed.
   - `correction` — a fact fixed by the operator.
   - `deviation` — the post no longer follows the experiment arm (for example card count or length changed).
   - `violation` — breaks `voice/exit-zero.md` or the gate: VERIFY text, "your thoughts", 💬, an unsourced or loosened figure, vendor or `images/sources/` media, a repeated card number.
   One line each: class, card, what changed.
5. Ask one question: "Roughly how many minutes did this one take, start to finish?"
6. Write `loop/inbox/post-<root id>.json`:
   ```json
   {"root_id": "…", "slug": "…", "format": "…", "lane": "main",
    "posted_at": "<root Timestamp as ISO UTC with Z>", "made_in_repo": true, "retrospective": false,
    "experiment": "E-00N or null", "arm": "treatment|control|none", "hypothesis": "…",
    "cards": [{"id": "…", "text": "…"}], "media": ["photo"], "ai_media": false,
    "production_minutes": 0, "edits": [{"class": "preference", "card": "01-hook.md", "note": "…"}],
    "draft": "drafts/…"}
   ```
   `cards` lists the author's replies after the root, not the root itself. If there is a `deviation`, set `arm` to `none` and `experiment` to null, and say the post will not count toward the experiment.
7. Run `python3 scripts/loop.py record-post --json loop/inbox/post-<root id>.json`. If it says "already recorded", say so and stop.
8. Set the queue row `status: posted`, `root_id: <id>`.
9. Tell the operator: when its snapshot is due (36 to 60 hours after posting; the daily job takes it), and list any `violation` found, since violations are never learned as preferences.
