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

1. If the operator has exported X analytics (a file named `account_analytics_content_*.csv` in `~/Downloads`), move the newest one into `loop/inbox/` and run `python3 scripts/loop.py record-export --csv loop/inbox/<file>`. Its per-post "New follows" become the exact follow numbers. If there is none from the last 7 days, ask the operator once to export it: X on a computer → Premium → Analytics → Content → Export, last 7 days.
2. Once a week, ask the operator for the two numbers on X's eligibility screen (X → Creator Studio → Original Content Rewards): verified followers and Verified Home Timeline impressions. Record them with `python3 scripts/loop.py record-eligibility --verified-followers <n> --qualified-impressions <n>`. If they'd rather skip it, carry on with the daily read's numbers.
3. Run `python3 scripts/loop.py status` and `python3 scripts/loop.py evaluate`. Read `ledger/SUMMARY.md`, `experiments.md`, `learnings.md`, and the last review in `reviews/`.
4. If the operator only wanted numbers (typed `/results` and no review is due), print the last 7 days from `ledger/SUMMARY.md` as a short table and stop.
5. Otherwise write `reviews/week-YYYY-Www.md` (ISO week, Australia/Brisbane) with these sections, each a few lines:
   - **Rewards progress.** From the "Original Content Rewards" block in `ledger/SUMMARY.md`: verified followers against 500, qualified impressions against 500,000, and the share of organic impressions on originals that qualified. Say what pace each needs over the remaining days and how this week compared. Only originals count, so name the originals that did most.
   - **Posts this week.** Table from `ledger/SUMMARY.md`: posted, slug, format, lane, organic impressions, non-organic %, profile visits, bookmarks, outside replies, follows, snapshot kind. Name late or missed reads and any post marked non-organic (boosted or otherwise); non-organic posts never count as wins.
   - **Followers.** From the Account block in `ledger/SUMMARY.md`: followers now, new and lost this week, follows per profile visit, and which posts and replies brought the new followers (exact from the export; otherwise the credited lower bound). Say how far the credited count is from the export's, so the matching can be trusted or not.
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
6. Run `python3 scripts/loop.py mark-reviewed`, then `python3 scripts/loop.py commit-data --message "weekly review YYYY-Www"`.
7. Tell the operator the three things that matter most, in three sentences, and where the full review is.
