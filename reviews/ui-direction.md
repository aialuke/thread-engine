# UI direction: decision log

A running record of decisions about a Thread Engine interface: what was decided, why, and what was rejected. Each round of the mock builds on this. Nothing here is built yet.

Mock: https://claude.ai/artifact/8zaBcxWAknJaXWkReQQPqg (private until the operator shares it).

## Decided (operator, 24 Sep 2026)

| # | Decision | Why | Rejected |
|---|---|---|---|
| D1 | Works on both MacBook (at home) and iPhone (everywhere else). | That's where the operator is. The 06:00 posts will often be on the phone. | Desktop-only; phone-only. |
| D2 | Every command becomes a button, `/approve` included. | The operator doesn't type commands by choice; buttons remove recall. | Keeping typed commands alongside as the main path. |
| D3 | Built to a standard fit to share. | "If it's good enough for me, it should be good enough for others." The operator plans to share it later. | A private tool with rough edges. |
| D4 | A working command shows a live line: an icon that moves with the kind of step, and shimmering text naming the real step. | The operator's reference is Claude's own "thinking" line. It shows the tool is working and what it's doing. | Spinners; progress bars with no words; fake percentages. |
| D5 | Today is the home screen: the next post, replies worth making, the account. | Operator, after clicking through the first mock: "feels like the perfect home screen". | A dashboard of charts; landing on Posts or Results. |

## Open, from the approve button (D2)

Today only a message the operator types can approve, and the rules protect that gate (`AGENTS.md`: the loop may never change it). A button is still the operator approving, but it needs a design that lets only a person press it: never the model, a script or a scheduled job. To settle before anything is built.

## First mock: choices to grill

These are the mock's guesses, not decisions:

- A post's life as six steps: Research, Draft, Approve, Ready, Post, Measure.
- Cards shown as they'll look on X, with where "Show more" cuts in, and each swap's source one tap away.
- Approve by press-and-hold, not a tap.
- Posting as four guided steps with a 10–20 minute shout-out timer.
- Results as sentences first, then the rewards bars at their real scale, then the table.
- Look: warm paper, ink black, one blue for "live", amber only for "needs you". Instrument Serif headlines, IBM Plex Sans body, IBM Plex Mono for numbers and sources.
