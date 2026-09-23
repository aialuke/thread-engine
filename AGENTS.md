# thread-engine

## What this repo is

Local factory for Hidden Settings X threads. Drafts are the product. Posting is a later, gated script.

## Operating rules

- Start non-trivial work in Plan mode.
- One topic per draft folder.
- Never invent a UI path. If a path is not verified this session, mark the card VERIFY.
- Never post, schedule, or call an X API from a draft skill.
- Never write APPROVED yourself. Only the human creates that file.
- Emoji marks follow `.grok/skills/hidden-settings/SKILL.md`.
- Voice is dry, specific, competent. No "game changer", "unlock", "most people don't know", "wait for it", 🚨🔥👇.

## Layout

- `AGENTS.md` — this contract, loaded every session
- `README.md` — human commands
- `.grok/skills/hidden-settings/` — format and research skill
- `.grok/skills/verify-settings/` — path fact-check skill
- `.grok/skills/draft-thread/` — write-the-thread skill
- `queue/topics.yaml` — backlog
- `voice/exit-zero.md` — voice source
- `examples/` — shipped gold threads, left as posted. Beat order is `.grok/skills/hidden-settings/SKILL.md`
- `drafts/_template/` — `thread.md`, `sources.md`, `checklist.md`
- `drafts/<slug>/` — one topic; numbered cards (`01-hook.md` …) are the posts; `POST.txt` is the run sheet; `thread.md` is not the payload; `sources.md`, `checklist.md`, `images.md`; human-created `APPROVED`
- `shipped/<slug>/` — packaged copy after the gate
- `scripts/draft.py` — print `grok -p "/draft-thread {slug}"`. Does not run grok. Does not hide Plan mode.
- `scripts/post_thread.py` — path to a draft folder; exit 2 and print `human gate` without `APPROVED`; with `APPROVED`, refuse and write nothing when a numbered card opens on `Most `, contains `VERIFY`, `💬`, or "your thoughts", repeats a card number, or attaches `images/sources/`; otherwise write `POST.txt`; `--copy N` copies card N to the clipboard; `--json` prints the payload; no X API in v1
- `tests/test_scripts.py` — gate and no-HTTP import checks

## Skills to use

- Drafting a thread → /draft-thread
- Checking setting paths → /verify-settings
- Format questions → /hidden-settings

## Verification before marking a draft ready

- Every setting has a current path
- Compatibility notes exist
- Hook and closer follow `.grok/skills/hidden-settings/SKILL.md` for that thread (settings, or comparison)
- images.md lists hook image + optional real screenshots to take

## Git

- Conventional commits
- Never commit secrets, X tokens, or APPROVED files that were created by the agent
