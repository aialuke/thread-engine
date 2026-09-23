---
name: snapshot
description: >
  Take the 36-60 hour snapshots that are due, from X read tools, into the
  ledger. Runs daily from the scheduled job, and first thing inside /next.
disable-model-invocation: true
---

# Snapshot

Read-only on X. Writes only `ledger/`, `loop/`, and the generated summary files. Never edits skills, drafts or the queue.

1. Run `python3 scripts/loop.py due`. For each post in `due`:
   1. `x_thread_fetch` the root id. From the `Engagement:` lines take `Views`, `Likes`, `Reposts`, `Quotes`, `Replies`, `Bookmarks` for the root, and `Views` for each card id listed in `card_ids`.
   2. `x_keyword_search` with `conversation_id:<root id>`, mode Top, limit 10. If 10 come back, page older with `max_id:` until fewer than 10 return or 5 pages. Collect every author handle except the root post's own.
   3. Once per run, `x_user_search` `exitzerocode` and take `Followers`.
   4. Save the raw tool text for this post to `ledger/raw/<root id>-<UTC yyyymmddThhmm>.txt`.
   5. Write `loop/inbox/snap-<root id>.json`:
      ```json
      {"root_id": "…", "observed_at": "<now, ISO UTC with Z>",
       "root": {"views": 0, "likes": 0, "reposts": 0, "quotes": 0, "replies": 0, "bookmarks": 0},
       "cards": [{"id": "…", "views": 0}],
       "repliers": ["handle", "…"], "followers": 0,
       "raw_file": "ledger/raw/…"}
      ```
      A number the tools did not return is `null`, never 0 and never a guess. If `x_thread_fetch` failed, record nothing for that post; it stays due.
   6. Run `python3 scripts/loop.py record-snapshot --json loop/inbox/snap-<root id>.json`.
2. Run `python3 scripts/loop.py mark-missed`, then `python3 scripts/loop.py evaluate`.
3. Run `python3 scripts/loop.py commit-data --message "snapshots <date>"`.
4. Print one line per post: slug, views, bookmarks, outside replies, and `kind`. Print any experiment status change from `evaluate` in plain words.
