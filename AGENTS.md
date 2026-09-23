# thread-engine

## What this repo is

Local factory for @exitzerocode X posts, with a learning loop. The goal is compelling content → engagement → account growth. Drafts are the product; the loop measures what works and feeds it back into the drafting rules. Posting stays manual.

## Operating rules

- The operator does not code or run scripts. Every step is a slash command. Scripts exist, but Grok runs them.
- Start non-trivial work in Plan mode.
- One topic per draft folder.
- Never invent a UI path or a claim. Unverified paths and claims are VERIFY and stay out of cards.
- Never post, schedule, or call an X write API. X read tools are fine.
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
- `reference/x-algorithm.md` — verified X ranking facts with sources; `reference/audience.md` — audience promise and lane definition
- `voice/exit-zero.md` — shared voice, truth budget, image and reply rules
- `.grok/skills/format-{settings,comparison,tool-swap,single-tip}/` — one format each, with its checklist. Settings detail stays in `.grok/skills/hidden-settings/`
- `.grok/skills/{next,draft-thread,verify-settings,ready,posted,snapshot,results,apply,undo-rule}/` — the commands
- `.grok/hooks/` — `/approve` hook and the APPROVED guard
- `queue/topics.yaml` — backlog and planned posts
- `drafts/<date>-<slug>/` — numbered cards (`01-hook.md` …) are the posts; `FORMAT`; `PATHS.md` / `CLAIMS.md`; `CHECKLIST.md`; `images.md`; `POST.txt` run sheet; operator-created `APPROVED`
- `ledger/` — one JSON per posted root, raw tool text in `ledger/raw/`, generated `SUMMARY.md`
- `loop/state.json` — experiments, lessons, applied rules. `loop/inbox/` is scratch, not committed
- `experiments.md`, `learnings.md` — generated views of the loop
- `reviews/` — weekly reviews and one-off reports
- `examples/`, `shipped/` — shipped gold and post-ship notes
- `ops/launchd/` — the daily snapshot job
- `scripts/post_thread.py` — the gate. Needs `APPROVED` (exit 2 `human gate` without it). Refuses when: cards changed after approval; `FORMAT` is unknown; a settings hook opens on `Most `; a card contains `VERIFY`, `💬` or "your thoughts"; a card number repeats; media comes from `images/sources/`. Otherwise writes `POST.txt`; `--copy N` copies card N
- `scripts/loop.py` — loop state: posts, snapshots, experiments, lessons, rule commits. No network
- `scripts/draft.py` — prints the grok draft command
- `tests/` — `python3 -m unittest discover -s tests`

## Git

- Conventional commits. `loop.py` commits data (`chore(data)`) and applied rules (`feat(rules)`).
- `APPROVED` files are ignored by git and never committed.
- Never commit secrets or X tokens.
