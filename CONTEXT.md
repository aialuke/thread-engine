# thread-engine

Local factory for @exitzerocode X posts, with a learning loop that measures what works. This glossary covers the vocabulary of drafting posts and of measuring the account's own posts.

## Language

### Drafting

**Draft**:
One topic's worth of posts, prepared for the operator to post by hand. It is a thread or a single standalone post, and holds one or more Cards.
_Avoid_: thread (for the unit), post (for the unit)

**Card**:
The text of one post within a Draft. A Draft's Cards are numbered in the order they are posted.
_Avoid_: slide, tweet, part

**Topic**:
The subject one Draft covers; a Draft has exactly one. The queue lists Topics, and a queue row is that Topic's record, with its status. A PAID → FREE row is a Topic like any other. It is not X's own topic labels on a post, which the ledger also calls topics.

**Roster**:
The operator's gathered list of paid tools and free alternatives that PAID → FREE posts draw their categories from. It is a source of claims to check, never of wording. It is not a queue; a Topic is taken from it, not listed in it.
_Avoid_: tool list

**Hook**:
The first Card of a Draft, the one a stranger is shown (the root, once posted). In a single standalone post it is the whole post. Not a Claude Code hook. **Hook style** is how a Hook is written, not a separate thing; it is one of the levers a Lesson may change.
_Avoid_: opener, intro

**Format**:
The shape a Draft takes, such as single tip, tool swap, comparison, build log or settings thread. It is chosen for the Draft. A tool swap series is also called PAID → FREE. Independent of Lane.
_Avoid_: template, type

**Lane**:
Whether a post serves the account's audience: `main` (tech and building, for builders and AI-using creators) or `other` (networking, banter, opinion with no tech angle). Set per post, and judged by audience fit, never by Format. The share of `main` posts is reported, not enforced, while formats are trialled.
_Avoid_: channel

**Truth budget**:
The rule that every figure or claim in a Card is sourced this session: an official page, the operator, or the operator's own run with its artifact. A claim that can't be sourced comes out of the Card; it is never softened to keep it.
_Avoid_: fact-check (for the rule), accuracy policy

**VERIFY**:
The status a path or claim carries in the Draft's `PATHS.md` or `CLAIMS.md` until a source confirms it. A VERIFY row stays in those files and out of the Cards; the word appearing in a Card makes the Gate refuse.
_Avoid_: TODO, unconfirmed, pending

### Approval and posting

**Operator**:
The human who runs the account: the only party who gives Approval and posts to X, by hand. The factory is driven by the operator typing slash commands. A role, not a name; it is defined by what a person typing at the prompt can do that no agent can. Does not code or run scripts.
_Avoid_: user, owner, admin

**Approval**:
The operator's typed `/approve <slug>`, saying a Draft's Cards are ready to post, recorded as the Draft's `APPROVED` file. Agreeing in conversation is not Approval. It covers the exact Cards the operator re-read: editing any Card afterwards voids it, and the operator approves again. No agent creates, edits or deletes it.
_Avoid_: sign-off, permission, go-ahead

**Gate**:
The checks a Draft must pass before it can be posted: it has an Approval that still covers its Cards, and each Card passes the format and voice checks. A Draft that fails is refused with the reasons. Approval is one input to the Gate, not the Gate itself.
_Avoid_: validator, linter, approval (for the checks)

**Posted**:
A Draft is posted when its first Card is live on X; that Card is the post's **root**, and its time is when the post was posted. The operator's `/posted` records it in the ledger with the Draft's Format, Lane and Arm, and its Edits. The daily run may record a live post on its own first, without a Draft; `/posted` then takes over that record and keeps its Snapshots. Only a recorded post can have a Snapshot. The queue's `shipped` status is legacy: posts from before `/posted` existed. Posted replaces it.
_Avoid_: published, launched

**Edit**:
One difference between a posted Card's live text and the Draft's Card, in either direction, so an added or removed Card counts. Recorded by `/posted` in exactly one of four classes. A **preference** is wording, length, order or emphasis with nothing factual changed; three posts showing the same kind make it a candidate Lesson. A **correction** is a fact the operator fixed. A **deviation** is a change that leaves the post no longer following its Experiment's Arm, so the post drops out of that Experiment. A **violation** breaks the voice rules, a Gate refusal or the Truth budget; it is never learned as a preference, and it is reported so the Gate can gain a refusal. A change that is both a violation and a deviation is a violation, and the deviation's effect on the Experiment still applies.
_Avoid_: change, diff

### Measuring

**Daily run**:
The pass, run at least once a day, that performs every Read that has come due and records the results. Not called a snapshot run: a Snapshot is a record, not a pass.
_Avoid_: snapshot run, snapshot job

**Read**:
One data-gathering pass for a single stage and time window, taken by fetching the account's own posts from X (or, for a Backfill read, from a saved file).
_Avoid_: pull, scrape, poll

**48h read**:
The Read of a post between 36 and 60 hours after it was posted. Named "48h" for the middle of that window, so it is not an exact age. A post that misses the window is marked missed, unless it was recorded after the fact (a retrospective post).
_Avoid_: 2-day read, early read

**Final read**:
The Read of a post at 26 to 29 days old, taken before X stops returning organic numbers at 30 days.
_Avoid_: 30-day read, last read

**Backfill read**:
A one-off Read of everything in a saved file, used to catch the ledger up. It counts as a Read but is not tied to a post's age.
_Avoid_: import, restore

**Snapshot**:
The ledger's record of one post's metrics as observed at one Read. It is **valid** when taken 36 to 60 hours after the post, **early** before that and **late** after; only a valid Snapshot counts toward a Round. A Read does not always produce one: replies are recorded as activity only, and a repeat valid or final observation is skipped.
_Avoid_: read (for the record), reading, metrics row

**Payload**:
The JSON file a loop command reads through `--json`: one Read's observations, one post, one experiment's terms, or another such record. A few `record-*` commands take a CSV or flags instead. Its shape and call order are part of the loop's interface.
_Avoid_: input file, request, body

### Experiments

**Experiment**:
A treatment hypothesis judged in Rounds against a threshold fixed when it opens (the cohort's median times the effect), scored, for new proposals, on one organic rate: likes plus reposts, or profile visits, per 1,000 organic impressions. A post under 50 organic impressions is not a cohort member, and as a treatment post with measured numbers it counts as a miss; a post with no rate at all (no impressions or a missing count) is left out. One is open at a time; it ends adopted, not replicated or no effect.
_Avoid_: test, trial, A/B

**Cohort**:
The earlier posts an Experiment is measured against, accepted by the operator with the Experiment and ideally from the same Lane and matching the format the treatment is compared with. A post joins only if it is organic and has a Snapshot that can be scored on the Experiment's measure. Its median times the effect sets the threshold. It is the reference the threshold comes from; unlike Control posts, its posts all predate the Experiment.
_Avoid_: sample, baseline

**Treatment**:
The one change an Experiment tests, stated as the exact rule a post follows. A treatment post is one that follows it.
_Avoid_: variant, intervention

**Control**:
A post normally made on an exploit Slot while an Experiment is open, following the current best approach. It is recorded for context and never scored: the Treatment is judged against the Cohort's threshold, not against Control posts. The Experiment's own "compared with" wording is a description and may not match what Control posts do.
_Avoid_: control group

**Round**:
The next batch of unconsumed treatment posts, as many as the Experiment's size, each with a valid Snapshot. How many clear the threshold decides the Experiment's next state.
_Avoid_: cycle, batch

**Arm**:
A post's assignment inside an Experiment: Treatment, Control, or none for a post outside one. Only treatment posts enter Rounds, and a retrospective post cannot join an Experiment, so its Arm is none. Skills and queue rows also say "the arm" for the Treatment's rule.
_Avoid_: group

**Lesson**:
An evidence-backed statement recorded when an Experiment closes, or when an operator preference is accepted. It need not be adopted. An adopted Lesson is provisional: `learnings.md` gives its Basis (rounds, treatment posts, cohort size and the false-adoption caveat, or the operator edits behind it), and `/apply` shows that before the operator's yes.
_Avoid_: finding, insight

**Slot**:
The next post's explore-or-exploit recommendation, from the time since the loop started and the posts made since. Explore posts the treatment, or asks for an Experiment if none is open; exploit posts the current best approach, as a Control post when one is open.
_Avoid_: turn, next post
