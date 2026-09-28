---
name: next
description: >
  Start the next post: catch up snapshots and the weekly review, then
  propose one post (topic, format, what it tests, when to post) for the
  operator to accept. The operator's main command.
disable-model-invocation: true
---

# Next

Speak plainly. The operator does not read code or JSON: turn every helper output into a sentence.

## 1. Catch up

1. Run `python3 scripts/snapshot.py`. Run it every time: a same-day repeat records nothing twice, and X charges each item once per UTC day (a soft guarantee, `reference/x-api.md` P5).
2. Run `python3 scripts/loop.py status`.
3. Read the last few lines of `ledger/runs.log`, not only the last: step 1's fresh run can hide an earlier failure. For each case below, say it first, in one sentence:
   - a line since the previous `snapshot ok` says `snapshot failed stage=`: recording failed at that stage, which is not the Mac or the X API credits. If a later run says `snapshot ok`, that run filled in what was missed (`loop.py` skips snapshots it already has).
   - the last run says `snapshot failed error=`: the X read failed; give the logged error in plain words.
   - the last `snapshot ok` is more than 30 hours old and no error line explains it: the daily job didn't run (the Mac was off or locked, or the job is unloaded).
4. Tell the operator in two or three lines what changed: new reads, follower change, anything marked non-organic, any experiment status change. Add one line from the "Original Content Rewards" block in `ledger/SUMMARY.md`: verified followers against 500, and the last reading of X's eligibility screen.

## 2. Weekly work, when `review.review_due` is true

1. Follow `.claude/skills/results/SKILL.md` (it writes the weekly review and ends with `mark-reviewed`).
2. Algorithm check: follow the refresh rule in `reference/x-algorithm.md` (compare each cited file's blob SHA with `main`). If any changed or is gone: `python3 scripts/loop.py set-reference --status stale --files <paths>` and tell the operator which facts need a re-read before lessons that cite them are trusted. If none: `set-reference --status current`.

## 3. Pick the slot

**Experiments are paused** (24 Sep 2026, `reviews/audit-2026-09.md`) until two weeks of organic X API data exist. The change that lifts the pause rewrites this section; while this paragraph stands, they are paused. Propose the post with no experiment arm, skip `next-slot`, and tell the operator in one line that experiments restart once the organic numbers are in.

When the pause is lifted, follow `experiment-list.md` in this folder.

## 4. Pick the topic

1. Lane: read `reference/audience.md`. Say the `lane.share` in one line. While the operator trials formats, a share below 0.8 (12 of 15) is reported, not a reason to refuse an `other` post.
2. Demand: run one or two searches for recent questions in the lane (for example `"how do I" free video editor lang:en -filter:replies`) with `python3 scripts/x_read.py search "<query>"`. It checks every post Grok returns against X and drops invented or misquoted ones; never cite a post it dropped, and don't use `x_keyword_search` directly, because it skips that check. Record each hit as a lead: post id, the query, and that the search returns at most 10. Leads are not proof of demand.
3. Queue: consider `status: queued` rows in `queue/topics.yaml`. PAID → FREE rows (`format: tool-swap`) go in the queue's order, one parent every other day: say when the last one went out.
4. Timing: propose a posting time in Australia/Brisbane. At most two originals a day, hours apart (operator, 24 Sep 2026): say how many originals went out today and how many hours since the last one. The operator should be there to reply in the first hour. A stranger only sees a post after its first like, and the like-based pool stops re-indexing at 48 hours (`reference/x-algorithm.md` A6), so prefer a time when builder mutuals and US Premium users are awake: the US-overlap slots, 22:00–23:00 or 05:00–07:00 Australia/Brisbane from Tuesday night to Friday morning, until experiment 3 in `experiment-list.md` says otherwise. The slots are a hypothesis from `reviews/reports/Driving verified home timeline impressions.md`, not a finding. US daylight saving ends on 1 Nov, which moves US mornings an hour later in Brisbane. The operator confirmed both slots work for them, first hour included.

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

A reply's job is gaining verified followers and real mutual follows, whose early likes open a new original to strangers (A6) and who rank the account's originals higher (A10). Find 2 or 3 conversations from the last few hours worth a reply, with `python3 scripts/x_read.py search "<query>"` (checked against X; never suggest a post it dropped):
- a builder's progress post in the lane (AI tools, agents, video pipelines, shipping), preferring verified accounts and existing mutuals;
- an early spot in a big AI or tool conversation;
- tech news, including politics when the story connects to tech.

For each: the link, and in one line the point a reply could make. Never paste-ready text: the operator writes every reply (algorithm fact A12). Remind them once: never the same reply twice, and keep volume to what they'd write by hand (`voice/exit-zero.md`).

End with: `Next: /draft-thread <slug>` (start with /plan if you want to review the plan first).
