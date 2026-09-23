# thread-engine

Makes @exitzerocode posts and learns which ones grow the account. You type slash commands in Grok or Claude Code, whichever you have open, and paste posts into X. The agent runs everything else. X is always read through Grok, so Claude Code needs Grok installed too.

## The cycle

1. **`/next`** — Grok catches up on results, then proposes one post: topic, format, what it tests, and when to post. Say yes or change it.
2. **`/draft-thread <slug>`** — Grok researches, checks every path and claim, and writes the cards. Start with `/plan` if you want to see the plan first.
3. **Read the cards.** Change anything you like.
4. **`/approve <slug>`** — only you can do this. It approves the cards exactly as they are. If a card changes later, approve again.
5. **`/ready <slug>`** — Grok checks the draft and puts card 1 on your clipboard. Paste it into X as a new post. Say `next` for each following card and post it as a reply to the one before.
6. **`/posted <link to the first post>`** — Grok records what actually went live and asks how long it took.

Numbers are collected automatically 36 to 60 hours after each post by the daily snapshot job.

## Learning

- **`/results`** shows recent numbers any time. Once a week, `/next` writes a review in `reviews/` for you.
- Each review can propose up to two rule changes, each backed by a test. **`/apply <lesson>`** accepts one. **`/undo-rule <lesson>`** takes it back.
- One experiment runs at a time. A result needs 3 posts to look promising and 3 more to be adopted. With one or two posts a day, expect about one answer every week or two.
- `experiments.md`, `learnings.md` and `ledger/SUMMARY.md` are always up to date to read. Never edit them; Grok rewrites them.

## What never changes

Only you approve a post. Nothing is posted for you. Every figure needs a source checked in the same session. The learning loop can change formats, length, timing, topics and hook style, never those rules.

## One-time setup

- **Commands and hooks:** both tools read `.claude/skills/` and `.claude/settings.json`. Grok needs this folder trusted (`/hooks-trust`); it already is on this Mac. Claude Code asks once to trust the project hooks.
- **Daily snapshot job:** `ops/launchd/com.exitzerocode.thread-engine.snapshot.plist` runs `/snapshot` at 20:00 each day. Ask Claude Code to install it; it copies the file to `~/Library/LaunchAgents/` and loads it. Log: `~/Library/Logs/thread-engine-snapshot.log`.

## Monthly outside check (optional)

Grok drafts, measures and grades its own work. Once a month, ask a different model to check it blind. In a Claude Code session in this folder, say:

> Read only `ledger/*.json` and `ledger/raw/`. Without opening `learnings.md`, `experiments.md` or `reviews/`, write down which formats, lengths and posting times did best and how sure you are. Then open `learnings.md` and list where it disagrees with you.

## For maintainers

Tests: `python3 -m unittest discover -s tests`. The contract for agents is `AGENTS.md`.
