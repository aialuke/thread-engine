# Experiment list

Reached from `/next` step 3 once the experiment pause is lifted.

Every experiment scores **the root only** (the only post that counts toward X's rewards program), on one **rate** per organic impression, named in the proposal, at the 36–60 hour read: `engagement_rate` (organic likes plus reposts per 1,000 organic impressions, the default) or `visit_rate` (organic profile visits per 1,000 organic impressions). Raw likes, reposts, quotes and bookmarks are not proposed any more. A post needs 50 or more organic impressions: a cohort post below that is not admitted, and a treatment post below it counts as a miss in its Round (noted `below_floor`, never dropped). `visit_rate` is proposed only when the cohort has a median above 0, at least 5 posts with a visit and no post holding over half of the visits; at this account's volume that is rare, so default to `engagement_rate`. `open-experiment` refuses views, root replies, a cohort whose median is 0, a cohort that is not a list of unique post ids, and non-organic posts. Controls (`arm: control`) are recorded for context and never scored.

Run `python3 scripts/loop.py next-slot`.

- **explore, no open experiment:** propose the next experiment from this list, first one not yet run and not marked review-only:
  1. Standalone post (single-tip or tool-swap, root only) against the account's threads in the same lane. Cohort: main-lane threads with a valid or late snapshot. A PAID → FREE post in this arm skips its shout-out, so it stays root-only.
  2. Short thread (3 cards) against the long threads already shipped (6 to 9 posts).
  3. Posting hour: the US-overlap slots in `SKILL.md` step 4.4, against the account's usual daytime Brisbane posting.
  4. Root length: under 280 characters against 500–600.
  5. Replies: five substantive replies in the lane on a posting day against none, measured by followers gained that week. **Review-only** (operator, 28 Sep 2026): watched in the weekly review, never opened with `open-experiment`, which scores single roots only.
  6. PAID → FREE category: one category against another (for example developer against creator), with the header, shape, slot and shout-out held fixed. Cohort: earlier organic PAID → FREE posts.

  State: the question, the treatment, what it is compared with, the cohort, meaning earlier posts from `ledger/SUMMARY.md` in the same lane that match the comparison format, at least 3, and the primary: `engagement_rate` unless the cohort passes the `visit_rate` screen, named in the proposal for the operator's yes. When the operator says yes, write `loop/inbox/experiment.json` (`question`, `treatment`, `control`, `cohort` ids, `primary` the rate the operator said yes to, `effect` 1.5, `reference_facts` like ["A1","A5"]) and run `python3 scripts/loop.py open-experiment --json loop/inbox/experiment.json`.
- **explore, experiment open:** the next post is the experiment's treatment.
- **exploit:** the next post uses the best-known approach: follow any `adopted` lessons in `learnings.md`. If an experiment is open, mark the row `arm: control`.
