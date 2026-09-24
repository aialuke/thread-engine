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

1. Run `python3 scripts/snapshot.py`. Run it every time: a repeat on the same day costs nothing and records nothing twice.
2. Run `python3 scripts/loop.py status`.
3. Read the last lines of `ledger/runs.log`. If the last run says `snapshot failed`, or the last `snapshot ok` is more than 30 hours old, say that first, in one sentence, with the likely cause: the Mac was off or locked, or the X API credits ran out.
4. Tell the operator in two or three lines what changed: new reads, follower change, anything marked non-organic, any experiment status change. Add one line from the "Original Content Rewards" block in `ledger/SUMMARY.md`: verified followers against 500, and the last reading of X's eligibility screen.

## 2. Weekly work, when `review.review_due` is true

1. Follow `.claude/skills/results/SKILL.md` (it writes the weekly review and ends with `mark-reviewed`).
2. Algorithm check: follow the refresh rule in `reference/x-algorithm.md` (compare each cited file's blob SHA with `main`). If any changed or is gone: `python3 scripts/loop.py set-reference --status stale --files <paths>` and tell the operator which facts need a re-read before lessons that cite them are trusted. If none: `set-reference --status current`.

## 3. Pick the slot

**Experiments are paused** until the loop has two weeks of organic X API data (`reference/x-api.md`). `open-experiment` refuses views, root replies, a cohort whose median is 0, and non-organic posts, so the list below cannot run yet. Until the pause is lifted, skip this section: propose the post with no experiment arm, and tell the operator in one line that experiments restart once the organic numbers are in. When they restart, every experiment scores **the root only** (the only post that counts toward X's rewards program), on its organic reach and engagement at the 36–60 hour read. `primary` is never views.

Run `python3 scripts/loop.py next-slot`.

- **explore, no open experiment:** propose the next experiment from this list, first one not yet run:
  1. Standalone post (single-tip or tool-swap, root only) against the account's threads in the same lane. Cohort: main-lane threads with a valid or late snapshot. A PAID → FREE post in this arm skips its shout-out, so it stays root-only.
  2. Short thread (3 cards) against the long threads already shipped (6 to 9 posts).
  3. Posting hour: US-overlap slots, 22:00–23:00 or 05:00–07:00 Australia/Brisbane from Tuesday night to Friday morning, against the account's usual daytime Brisbane posting. The US-overlap slots are a hypothesis from `reviews/reports/Driving verified home timeline impressions.md`, not a finding. US daylight saving ends on 1 Nov, which moves US mornings an hour later in Brisbane.
  4. Root length: under 280 characters against 500–600.
  5. Replies: five substantive replies in the lane on a posting day against none, measured by followers gained that week.
  6. PAID → FREE category: one category against another (for example developer against creator), with the header, shape, slot and shout-out held fixed. Cohort: earlier organic PAID → FREE posts.
  State: the question, the treatment, what it is compared with, and the cohort, meaning earlier posts from `ledger/SUMMARY.md` in the same lane that match the comparison format, at least 3. When the operator says yes, write `loop/inbox/experiment.json` (`question`, `treatment`, `control`, `cohort` ids, `primary` "views", `effect` 1.5, `reference_facts` like ["A1","A5"]) and run `python3 scripts/loop.py open-experiment --json loop/inbox/experiment.json`.
- **explore, experiment open:** the next post is the experiment's treatment.
- **exploit:** the next post uses the best-known approach: follow any `adopted` lessons in `learnings.md`. If an experiment is open, mark the row `arm: control`.

## 4. Pick the topic

1. Lane: read `reference/audience.md`. Say the `lane.share` in one line. While the operator trials formats, a share below 0.8 (12 of 15) is reported, not a reason to refuse an `other` post.
2. Demand: run one or two searches for recent questions in the lane (for example `"how do I" free video editor lang:en -filter:replies`) with `python3 scripts/x_read.py search "<query>"`. It checks every post Grok returns against X and drops invented or misquoted ones; never cite a post it dropped, and don't use `x_keyword_search` directly, because it skips that check. Record each hit as a lead: post id, the query, and that the search returns at most 10. Leads are not proof of demand.
3. Queue: consider `status: queued` rows in `queue/topics.yaml`. PAID → FREE rows (`format: tool-swap`) go in the queue's order, one parent every other day: say when the last one went out.
4. Timing: propose a posting time in Australia/Brisbane. At most two originals a day, hours apart (operator, 24 Sep 2026): say how many originals went out today and how many hours since the last one. The operator should be there to reply in the first hour. A stranger only sees a post after its first like, and the like-based pool stops re-indexing at 48 hours (`reference/x-algorithm.md` A6), so prefer a time when builder mutuals and US Premium users are awake: the US-overlap slots in experiment 3 until that experiment says otherwise. The operator confirmed both slots work for them, first hour included.

## 5. Propose, then write the row

Propose one post in four lines: topic, format, experiment arm (or none), posting time. Say why in one sentence. When the operator accepts or edits it, write or update the queue row:

```yaml
  - slug: <kebab-slug>
    status: planned
    format: <settings|comparison|tool-swap|single-tip|build-log|tool-verdict>
    lane: <main|other>
    experiment: <E-00N or omit>
    arm: <treatment|control or omit>
    treatment: <the arm's exact rule, or omit>
    hypothesis: <one sentence, written now, before posting>
    post_at: <YYYY-MM-DD HH:MM Australia/Brisbane>
    leads: [<post ids>]
```

## 6. Replies worth making today

Replies bring most of the account's reach but count for nothing toward X's rewards program. Their job is gaining verified followers and real mutual follows, whose early likes open a new original to strangers (A6) and who rank the account's originals higher (A10). Find 2 or 3 conversations from the last few hours worth a reply, with `python3 scripts/x_read.py search "<query>"` (checked against X; never suggest a post it dropped):
- a builder's progress post in the lane (AI tools, agents, video pipelines, shipping), preferring verified accounts and existing mutuals;
- an early spot in a big AI or tool conversation;
- tech news, including politics when the story connects to tech.

For each: the link, and in one line the point a reply could make. Never paste-ready text: the operator writes every reply (algorithm fact A12). Remind them once: never the same reply twice, and keep volume to what they'd write by hand (`voice/exit-zero.md`).

End with: `Next: /draft-thread <slug>` (start with /plan if you want to review the plan first).
