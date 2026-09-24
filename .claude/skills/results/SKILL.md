---
name: results
description: >
  Show how posts did and write the weekly review: results in plain
  English, followers and replies, experiment status, lane share, the
  operator's edit patterns, reader questions worth answering, and at most
  two proposed rule changes.
disable-model-invocation: true
---

# Results

Plain English. No JSON, no code in what the operator reads. Say "not enough data yet" whenever it is true.

1. Run `python3 scripts/loop.py status` and `python3 scripts/loop.py evaluate`. Read `ledger/SUMMARY.md`, `experiments.md`, `learnings.md`, and the last review in `reviews/`.
2. If the operator only wanted numbers (typed `/results` and no review is due), print the last 7 days from `ledger/SUMMARY.md` as a short table and stop.
3. Otherwise write `reviews/week-YYYY-Www.md` (ISO week, Australia/Brisbane) with these sections, each a few lines:
   - **Posts this week.** Table from `ledger/SUMMARY.md`: posted, slug, format, lane, organic impressions, non-organic %, profile visits, bookmarks, outside replies, credited follows, snapshot kind. Name late or missed reads and any post marked non-organic (boosted or otherwise); non-organic posts never count as wins.
   - **Followers.** From the Account block in `ledger/SUMMARY.md`: followers now, new and lost this week, how many new followers were credited to something they engaged with (a lower bound), and follows per profile visit. If the operator dropped an X analytics export in `loop/inbox/`, compare its per-post "New follows" with the credited follows and say how far apart they are.
   - **Replies.** From this week's `reply` rows in `ledger/activity/`: how many, their organic reach, and their profile visits, grouped by topic (read the account's own reply text and X's labels). Name the reply that earned the most visits. Flag any reply text used twice and the busiest 24 hours of replies (`voice/exit-zero.md`).
   - **Experiment.** The open one: its question, rounds so far, posts still needed. Closed ones: result and lesson id.
   - **Lane.** `lane-share`: main posts out of the last 15, against the target of 12. While the operator trials formats this is reported, not enforced; say how `main` and `other` posts compare on organic reach and profile visits.
   - **Spacing.** Hours between originals this week, as observations only.
   - **Your edits.** Group this week's `preference` edits by kind across all ledger posts. A kind seen on 3 or more posts is a candidate: propose it as one sentence. On the operator's yes, run `python3 scripts/loop.py add-preference --statement "<sentence>" --evidence <ids>`. List `violation` edits separately and say the gate may need a new refusal; that change is made in a Claude Code session, not here.
   - **Reader questions.** Run `python3 scripts/x_api.py mentions` and read this week's replies to the account. Up to 3 questions worth answering, each with the point a reply should make. Never name the person, never copy their text into the review, never a paste-ready reply: the operator writes it.
   - **Lanes to review.** Posts the daily run recorded on its own (slug `x-<id>`, lane `other`) and any post whose lane looks wrong: test each against the three tests in `reference/audience.md` and propose `main` or `other` in one line. On the operator's yes, run `python3 scripts/loop.py set-lane --root-id <id> --lane <lane> --reason "<which test>"`.
   - **Rule changes proposed.** At most two, each tied to an `adopted` lesson with rule state `none`: the lesson id, the file under `.claude/skills/` or `voice/`, and the exact sentence to add or change. Say: "Type /apply <lesson id> to make this change, or ignore it."
   - **Reverts proposed.** An applied rule whose next 3 posts all fell below their experiment bar or cohort median: say so and "Type /undo-rule <lesson id> to revert."
   - **Profile.** Run `python3 scripts/x_api.py me`. Say whether the bio and the pinned post match `reference/audience.md`. If not, suggest a one-sentence bio and a pin with no link or a well-known link (algorithm fact A14).
4. Run `python3 scripts/loop.py mark-reviewed`, then `python3 scripts/loop.py commit-data --message "weekly review YYYY-Www"`.
5. Tell the operator the three things that matter most, in three sentences, and where the full review is.
