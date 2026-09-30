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

1. Run `python3 scripts/loop.py status` and keep its `health.warnings`: step 2's fresh run would hide a daily job that didn't run.
2. Run `python3 scripts/snapshot.py`. Run it every time: a same-day repeat records nothing twice, and X charges each item once per UTC day (a soft guarantee, `reference/x-api.md` P5).
3. Run `python3 scripts/loop.py status` again.
4. Say each string in `health.warnings` from the first status output and any new one from this one first, one sentence each. It covers a last run that failed, a last `snapshot ok` more than 26 hours old (the daily job didn't run: the Mac was off or locked, or the job is unloaded), and posts inside the last 48 hours of their final read. If the list is empty, say nothing about it. Then read the last few lines of `ledger/runs.log`, not only the last: step 1's fresh run can hide an earlier failure.
   - a line since the previous `snapshot ok` says `snapshot failed stage=`: recording failed at that stage, which is not the Mac or the X API credits. If a later run says `snapshot ok`, that run filled in what was missed (`loop.py` skips snapshots it already has).
   - the last run says `snapshot failed error=`: the X read failed; give the logged error in plain words.
5. Tell the operator in two or three lines what changed: new reads, follower change, anything marked non-organic, any experiment status change. Add one line from the "Original Content Rewards" block in `ledger/SUMMARY.md`: verified followers against 500, and the last reading of X's eligibility screen.

Done: the operator has heard what changed, and any failed or missed snapshot, in plain words.

## 2. Weekly work

When `review.review_due` is true, follow `.claude/skills/next/weekly.md`. Otherwise skip to step 3.

## 3. Pick the slot

Read Current state in `AGENTS.md`. While it says experiments are paused, propose the post with no experiment arm, skip `next-slot`, and tell the operator in one line that experiments restart once the organic numbers are in.

When Current state no longer says paused, follow `experiment-list.md` in this folder.

## 4. Pick the topic

1. Lane: read `reference/audience.md`. Say the `lane.share` in one line. While the operator trials formats, a share below the target in `reference/audience.md` is reported, not a reason to refuse an `other` post.
2. Demand: run one or two searches for recent questions in the lane (for example `"how do I" free video editor lang:en -filter:replies`) with `python3 scripts/x_read.py search "<query>"`. It checks every post Grok returns against X and drops invented or misquoted ones; never cite a post it dropped, and don't use `x_keyword_search` directly, because it skips that check. Record each hit as a lead: post id, the query, and that the search returns at most 10. Leads are not proof of demand.
3. Queue: consider `status: queued` rows in `queue/topics.yaml`. PAID → FREE rows (`format: tool-swap`) go in the queue's order, one parent every other day: say when the last one went out.
4. Timing: propose a posting time in Australia/Brisbane. At most two originals a day, hours apart: say how many originals went out today and how many hours since the last one. The operator should be there to reply in the first hour. A stranger only sees a post after its first like, and the like-based pool stops re-indexing at 48 hours (`reference/x-algorithm.md` A6), so prefer a time when builder mutuals and US Premium users are awake: the US-overlap windows, 22:00–23:00 or 05:00–07:00 Australia/Brisbane from Tuesday night to Friday morning, until experiment 3 in `experiment-list.md` says otherwise. The windows are a hypothesis from `reviews/reports/Driving verified home timeline impressions.md`, not a finding. US daylight saving ends on 1 Nov, which moves US mornings an hour later in Brisbane. The operator confirmed both windows work for them, first hour included.

Done: the lane share, the leads (or that none were found), the queue state and the timing figures have each been said in a line.

## 5. Propose, then write the row

Propose one post in four lines: topic, format, experiment arm (or none), posting time. Say why in one sentence. Then stop and wait for the operator's yes or edit. Write or update the queue row only after it:

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

Run this once the operator has answered step 5.

A reply's job is gaining verified followers and real mutual follows, whose early likes open a new original to strangers (A6) and who rank the account's originals higher (A10). Find 2 or 3 conversations from the last few hours worth a reply, with `python3 scripts/x_read.py search "<query>"` (checked against X; never suggest a post it dropped):
- a builder's progress post in the lane (AI tools, agents, video pipelines, shipping), preferring verified accounts and existing mutuals;
- an early spot in a big AI or tool conversation;
- tech news, including politics when the story connects to tech.

For each: the link, and in one line the point a reply could make. Remind the operator once of the reply rules in `voice/exit-zero.md` → Replies.

Done: 2–3 links, each with the point a reply could make, every one from `x_read.py` results.

End with `Next: /draft-thread <slug>` for the slug the operator accepted (start with /plan if you want to review the plan first).
