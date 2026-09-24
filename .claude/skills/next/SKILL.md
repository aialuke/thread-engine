---
name: next
description: >
  Start the next post: catch up snapshots and the weekly review, then
  propose one post (topic, format, what it tests, when to post) for the
  operator to accept. The operator's main command.
disable-model-invocation: true
---

# Next

The operator's main command, in Grok or Claude Code. Speak plainly. The operator does not read code or JSON: turn every helper output into a sentence.

## 1. Catch up

1. Run `python3 scripts/loop.py status`.
2. If `due.due` is not empty, run `python3 scripts/snapshot.py`.
3. Tell the operator in two or three lines what changed: new snapshots, any missed ones, any experiment status change.

## 2. Weekly work, when `review.review_due` is true

1. Follow `.claude/skills/results/SKILL.md` (it writes the weekly review and ends with `mark-reviewed`).
2. Algorithm check: for each path under "Cited paths" in `reference/x-algorithm.md`, open `https://github.com/xai-org/x-algorithm/commits/main/<path>` and look for commits after the commit date in that file. If any: `python3 scripts/loop.py set-reference --status stale --files <paths>` and tell the operator which facts need a re-read before lessons that cite them are trusted. If none: `set-reference --status current`.

## 3. Pick the slot

**Experiments are paused** until the loop has two weeks of organic X API data (`reference/x-api.md`). `open-experiment` refuses views, root replies, a cohort whose median is 0, and non-organic posts, so the list below cannot run yet. Until the pause is lifted, skip this section: propose the post with no experiment arm, and tell the operator in one line that experiments restart once the organic numbers are in.

Run `python3 scripts/loop.py next-slot`.

- **explore, no open experiment:** propose the next experiment from this list, first one not yet run:
  1. Standalone post (single-tip or tool-swap, root only) against the account's threads in the same lane. Cohort: main-lane threads with a valid or late snapshot.
  2. Short thread (3 cards) against the long threads already shipped (6 to 9 posts).
  3. Posting hour: 07:00–09:00 against 19:00–21:00 Australia/Brisbane.
  4. Root length: under 280 characters against 500–600.
  5. Replies: five substantive replies in the lane on a posting day against none, measured by followers gained that week.
  State: the question, the treatment, what it is compared with, and the cohort, meaning earlier posts from `ledger/SUMMARY.md` in the same lane that match the comparison format, at least 3. When the operator says yes, write `loop/inbox/experiment.json` (`question`, `treatment`, `control`, `cohort` ids, `primary` "views", `effect` 1.5, `reference_facts` like ["A1","A5"]) and run `python3 scripts/loop.py open-experiment --json loop/inbox/experiment.json`.
- **explore, experiment open:** the next post is the experiment's treatment.
- **exploit:** the next post uses the best-known approach: follow any `adopted` lessons in `learnings.md`. If an experiment is open, mark the row `arm: control`.

## 4. Pick the topic

1. Lane: read `reference/audience.md`. If `lane.share` is below 0.8 (12 of 15), the next post must be `main`.
2. Demand: run one or two searches for recent questions in the lane (for example `"how do I" free video editor lang:en -filter:replies`). Use `x_keyword_search` when this session has it; otherwise run `python3 scripts/x_read.py search "<query>"`. Record each hit as a lead: post id, the query, and that the search returns at most 10. Leads are not proof of demand.
3. Queue: consider `status: queued` rows in `queue/topics.yaml`.
4. Timing: propose a posting time in Australia/Brisbane. Say how many hours since the last original; there is no fixed minimum.

## 5. Propose, then write the row

Propose one post in four lines: topic, format, experiment arm (or none), posting time. Say why in one sentence. When the operator accepts or edits it, write or update the queue row:

```yaml
  - slug: <kebab-slug>
    status: planned
    format: <settings|comparison|tool-swap|single-tip>
    lane: <main|other>
    experiment: <E-00N or omit>
    arm: <treatment|control or omit>
    treatment: <the arm's exact rule, or omit>
    hypothesis: <one sentence, written now, before posting>
    post_at: <YYYY-MM-DD HH:MM Australia/Brisbane>
    leads: [<post ids>]
```

End with: `Next: /draft-thread <slug>` (start with /plan if you want to review the plan first).
