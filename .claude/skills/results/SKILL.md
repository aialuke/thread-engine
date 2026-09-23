---
name: results
description: >
  Show how posts did and write the weekly review: results in plain
  English, experiment status, lane share, the operator's edit patterns,
  reader questions worth answering, and at most two proposed rule changes.
disable-model-invocation: true
---

# Results

Plain English. No JSON, no code in what the operator reads. Say "not enough data yet" whenever it is true.

1. Run `python3 scripts/loop.py status` and `python3 scripts/loop.py evaluate`. Read `ledger/SUMMARY.md`, `experiments.md`, `learnings.md`, and the last review in `reviews/`.
2. If the operator only wanted numbers (typed `/results` and no review is due), print the last 7 days from `ledger/SUMMARY.md` as a short table and stop.
3. Otherwise write `reviews/week-YYYY-Www.md` (ISO week, Australia/Brisbane) with these sections, each a few lines:
   - **Posts this week.** Table: posted, slug, format, views, bookmarks, outside replies, snapshot kind. Late or missed snapshots are named, not hidden.
   - **Experiment.** The open one: its question, rounds so far, posts still needed. Closed ones: result and lesson id.
   - **Lane.** `lane-share`: main posts out of the last 15. Below 12 means the next posts go to `main`.
   - **Spacing.** Hours between originals this week, as observations only.
   - **Your edits.** Group this week's `preference` edits by kind across all ledger posts. A kind seen on 3 or more posts is a candidate: propose it as one sentence. On the operator's yes, run `python3 scripts/loop.py add-preference --statement "<sentence>" --evidence <ids>`. List `violation` edits separately and say the gate may need a new refusal; that change is made in a Claude Code session, not here.
   - **Reader questions.** From outside repliers in the week's snapshots, up to 3 questions worth answering, each with the point a reply should make. Never a paste-ready reply: the operator writes it.
   - **Rule changes proposed.** At most two, each tied to an `adopted` lesson with rule state `none`: the lesson id, the file under `.claude/skills/` or `voice/`, and the exact sentence to add or change. Say: "Type /apply <lesson id> to make this change, or ignore it."
   - **Reverts proposed.** An applied rule whose next 3 posts all fell below their experiment bar or cohort median: say so and "Type /undo-rule <lesson id> to revert."
   - **Profile.** First review only: a one-sentence bio that matches `reference/audience.md`, and a pin suggestion with no link or a well-known link (algorithm fact A14).
4. Run `python3 scripts/loop.py mark-reviewed`, then `python3 scripts/loop.py commit-data --message "weekly review YYYY-Www"`.
5. Tell the operator the three things that matter most, in three sentences, and where the full review is.
