# thread-engine

## What this repo is

Local factory for @exitzerocode X posts, with a learning loop. The goal is compelling content → engagement → account growth. Drafts are the product; the loop measures what works and feeds it back into the drafting rules. Posting stays manual.

## Operating rules

- The operator does not code or run scripts. Every step is a slash command, typed in Grok or Claude Code. Scripts exist, but the agent runs them.
- Start non-trivial work in Plan mode.
- One topic per draft folder.
- Never invent a UI path or a claim. Unverified paths and claims are VERIFY and stay out of cards.
- Never post, schedule, or call an X write API. The account's own numbers come from `scripts/x_api.py` (read-only X API keys in the Keychain; the keys never enter a session). Other people's posts and research go through Grok's X tools or `scripts/x_read.py`, which make one read-only Grok call.
- Never create, edit or delete `APPROVED`. Only the operator's typed `/approve <slug>` creates it (a hook does it; another hook blocks every agent attempt).
- Voice is `voice/exit-zero.md`. Format rules are the format skills. No "game changer", "unlock", "most people don't know", "wait for it", 🚨🔥👇.
- Loop state lives in `loop/state.json` and `ledger/*.json` and changes only through `scripts/loop.py`. Never hand-edit them or the generated `experiments.md`, `learnings.md`, `ledger/SUMMARY.md`.

## What the loop may never change

The `/approve` gate, the truth budget, fail-closed fact-checks, the shared gate refusals, and the no-X-writes rule. Lessons may change format, length, lane mix, hook style, timing and topic choice, through `/apply` only.

## Operator commands

| Command | Does |
|---|---|
| `/next` | Catch up snapshots and the weekly review, then propose the next post |
| `/draft-thread <slug>` | Write the draft in its format |
| `/approve <slug>` | Operator only. Approves the cards as they are now |
| `/ready <slug>` | Run the gate and copy cards to the clipboard one at a time |
| `/posted <link>` | Record what went live |
| `/results` | Numbers now, or the weekly review when due |
| `/apply <lesson>` / `/undo-rule <lesson>` | Accept or revert a proposed rule change |

## Layout

- `AGENTS.md` — this contract
- `README.md` — the operator's guide
- `reference/x-algorithm.md` — verified X ranking facts with sources; `reference/x-api.md` — what the X API can and cannot read, prices, and the privacy rules; `reference/audience.md` — audience promise and lane definition
- `voice/exit-zero.md` — shared voice, truth budget, image and reply rules
- `.claude/skills/format-{settings,comparison,tool-swap,single-tip,build-log,tool-verdict}/` — one format each, with its checklist. Settings detail stays in `.claude/skills/hidden-settings/`
- `.claude/skills/{next,draft-thread,verify-settings,ready,posted,snapshot,results,apply,undo-rule}/` — the commands. Grok and Claude Code both load `.claude/skills/`. `approve/` only registers `/approve` so Claude Code accepts it; the approve hook does the work
- `.claude/hooks/` — the approve hook and the guard (approval marker and loop state); `.claude/settings.json` registers both hooks and the script allowlist for both tools
- `queue/topics.yaml` — backlog and planned posts; `queue/research-backlog.md` — research and strategy to do later, operator-chosen; `queue/paid-free-roster.md` — the PAID → FREE roster (claims to check, never copy)
- `drafts/<date>-<slug>/` — numbered cards (`01-hook.md` …) are the posts; `FORMAT`; `PATHS.md` / `CLAIMS.md`; `CHECKLIST.md`; `images.md`; `REPLIES.md` (tool-swap: talking points, never paste-ready); `POST.txt` run sheet; operator-created `APPROVED`
- `ledger/` — one JSON per posted root, raw tool text in `ledger/raw/`, generated `SUMMARY.md`; `ledger/activity/` holds every post, reply and quote with its organic reads (`YYYY-MM.json`) and daily follower counts and follow credit (`account.json`), written only by `loop.py`
- `loop/state.json` — experiments, lessons, applied rules. `loop/inbox/` is scratch; `loop/followers/` and `ledger/raw/api/` hold other people's data. None of the three is committed
- `experiments.md`, `learnings.md` — generated views of the loop
- `reviews/` — weekly reviews and one-off reports; `reviews/paid-free-session-2026-09.md` records how the PAID → FREE series was designed and what changed
- `examples/`, `shipped/` — shipped gold and post-ship notes (`shipped/<slug>/NOTES.md`, and for PAID → FREE post 1 its retro `CLAIMS.md` and `REPLIES.md`)
- `ops/launchd/` — the daily snapshot job
- `scripts/post_thread.py` — the gate. Needs `APPROVED` (exit 2 `human gate` without it). Counts characters as X does (`→`, `▷` and emoji count 2, a link 23). Refuses when: cards changed after approval; `FORMAT` is unknown; a settings hook opens on `Most `; the hook is over 600 characters in a settings, single-tip, build-log, tool-verdict or tool-swap draft; a tool-swap hook doesn't open with the PAID → FREE header, or contains an @handle, a hashtag or a `1/5` counter; a card contains `VERIFY`, `💬`, "your thoughts", a banned phrase from `voice/exit-zero.md` other than "unlock" (brochure words included), or an instruction to engage ("drop a hi", "drop it below", "reply with", "save this post", "like and repost", "follow for more"); a card number repeats; media comes from `images/sources/`. Otherwise writes `POST.txt` (a tool-swap's says to wait 10–20 minutes before the shout-out); `--copy N` copies card N; `--count` prints X's counts with no approval and writes nothing
- `scripts/loop.py` — loop state: posts, snapshots, experiments, lessons, rule commits. No network
- `scripts/grok_read.py` — the one read-only structured Grok call every X read goes through
- `scripts/x_read.py` — `search "<query>"` or `thread <id>`, JSON out, for sessions without X tools. Every post Grok returns is checked by id against the X API; invented or misquoted posts are dropped and listed, and nothing is returned if the check can't run. Never cite a post that didn't pass this check
- `scripts/x_api.py` — read-only X API client for the account's own posts (whole text, from `note_tweet`), mentions, followers and profile; `user <handle>` checks an account before a post tags it; GET only; `keys` checks the Keychain without reading values
- `scripts/snapshot.py` — the daily X API read (via `x_api.py`): every post, reply and quote at 36–60 hours and again at 26–29 days, follower ids and mentions, all recorded through `loop.py`; a failed read records nothing; cost per run in `ledger/runs.log`; `--ingest` records a backfill
- `scripts/draft.py` — prints the grok draft command
- `tests/` — `python3 -m unittest discover -s tests` (scripts, loop, snapshot, hooks)

## Git

- Conventional commits. `loop.py` commits data (`chore(data)`) and applied rules (`feat(rules)`).
- `APPROVED` files are ignored by git and never committed.
- Never commit secrets or X tokens.
