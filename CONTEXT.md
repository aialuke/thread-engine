# thread-engine

Local factory for @exitzerocode X posts, with a learning loop that measures what works. This glossary covers the vocabulary of measuring the account's own posts.

## Language

**Daily run**:
The once-a-day pass that performs every Read that has come due and records the results.
_Avoid_: snapshot run, snapshot job

**Read**:
One fetch pass of the account's own posts for a single stage and time window.
_Avoid_: pull, scrape, poll

**Snapshot**:
The ledger's record of one post's metrics as observed at one Read. A Read does not always produce one: replies are recorded as activity only, and a repeat valid or final observation is skipped.
_Avoid_: read (for the record), reading, metrics row

**Payload**:
The JSON file a `record-*` or `open-experiment` command reads: one Read's observations, one post, or one experiment's terms. Its shape and call order are part of the loop's interface.
_Avoid_: input file, request, body

**48h read**:
The Read of a post between 36 and 60 hours after it was posted. Named "48h" for the middle of that window, so it is not an exact age. A post that misses the window is marked missed.
_Avoid_: 2-day read, early read

**Final read**:
The Read of a post at 26 to 29 days old, taken before X stops returning organic numbers at 30 days.
_Avoid_: 30-day read, last read

**Backfill read**:
A one-off Read of everything in a saved file, used to catch the ledger up. It counts as a Read but is not tied to a post's age.
_Avoid_: import, restore

**Experiment**:
A treatment hypothesis judged in Rounds against a threshold fixed when it opens (the cohort's median times the effect), scored on one organic rate: likes plus reposts, or profile visits, per 1,000 organic impressions. A post under 50 organic impressions is not a cohort member, and as a treatment post it counts as a miss. One is open at a time; it ends adopted, not replicated or no effect.
_Avoid_: test, trial, A/B

**Round**:
The next batch of unconsumed treatment posts, as many as the Experiment's size, each with a valid Snapshot. How many clear the threshold decides the Experiment's next state.
_Avoid_: cycle, batch

**Lesson**:
An evidence-backed statement recorded when an Experiment closes, or when an operator preference is accepted. It need not be adopted. An adopted Lesson is provisional: `learnings.md` gives its Basis (rounds, treatment posts, cohort size and the false-adoption caveat, or the operator edits behind it), and `/apply` shows that before the operator's yes.
_Avoid_: finding, insight

**Arm**:
A post's assignment inside an Experiment: treatment, control, or none for a post outside one. Only treatment posts enter Rounds.
_Avoid_: group, variant

**Slot**:
The next post's explore-or-exploit recommendation, from the time since the loop started and the posts made since. Explore posts the treatment (or asks for an Experiment); exploit posts the current best approach.
_Avoid_: turn, next post
