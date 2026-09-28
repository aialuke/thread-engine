# Experiment list

Reached from `/next` step 3 once the experiment pause is lifted.

Every experiment scores **the root only** (the only post that counts toward X's rewards program), on the one engagement metric named in the proposal (likes, reposts, quotes or bookmarks) at the 36–60 hour read; reach is reported but never scored. `primary` is never views. `open-experiment` refuses views, root replies, a cohort whose median is 0, and non-organic posts.

Run `python3 scripts/loop.py next-slot`.

- **explore, no open experiment:** propose the next experiment from this list, first one not yet run and not marked review-only:
  1. Standalone post (single-tip or tool-swap, root only) against the account's threads in the same lane. Cohort: main-lane threads with a valid or late snapshot. A PAID → FREE post in this arm skips its shout-out, so it stays root-only.
  2. Short thread (3 cards) against the long threads already shipped (6 to 9 posts).
  3. Posting hour: the US-overlap slots in `SKILL.md` step 4.4, against the account's usual daytime Brisbane posting.
  4. Root length: under 280 characters against 500–600.
  5. Replies: five substantive replies in the lane on a posting day against none, measured by followers gained that week. **Review-only** (operator, 28 Sep 2026): watched in the weekly review, never opened with `open-experiment`, which scores single roots only.
  6. PAID → FREE category: one category against another (for example developer against creator), with the header, shape, slot and shout-out held fixed. Cohort: earlier organic PAID → FREE posts.

  State: the question, the treatment, what it is compared with, the cohort, meaning earlier posts from `ledger/SUMMARY.md` in the same lane that match the comparison format, at least 3, and the primary metric: one of likes, reposts, quotes or bookmarks, chosen for this experiment and named in the proposal for the operator's yes. When the operator says yes, write `loop/inbox/experiment.json` (`question`, `treatment`, `control`, `cohort` ids, `primary` the metric the operator said yes to, `effect` 1.5, `reference_facts` like ["A1","A5"]) and run `python3 scripts/loop.py open-experiment --json loop/inbox/experiment.json`.
- **explore, experiment open:** the next post is the experiment's treatment.
- **exploit:** the next post uses the best-known approach: follow any `adopted` lessons in `learnings.md`. If an experiment is open, mark the row `arm: control`.
