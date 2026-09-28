# Instruction-file review: always-loaded

Scope: `CLAUDE.md` and every file it imports with `@`. Method: `BRIEF.md` (this folder). Date: 28 Sep 2026.

## Baseline

| File | Words before | Words after | Sections | Steps and completion criteria |
|---|---|---|---|---|
| `CLAUDE.md` | 83 | 33 | imports; Cloud session notes | none |
| `AGENTS.md` | 1,299 | 1,067 | What this repo is; Operating rules; What the loop may never change; Operator commands; Layout; Git; Design grilling (Jev cards) | Jev cards: 6 steps, criterion "6. Stop" after one receipt line; the rest is reference |
| `voice/exit-zero.md` | 1,040 | 1,016 | Rules; What every post delivers; Texture; Banned phrases; Farm tells; Asking for engagement; Truth budget; Images; Replies; Networking; Makers; Boosting | reference only |
| `reference/audience.md` | 623 | 623 | Main lane (3 tests); Other lane; Replies; Before 24 Sep | lane check: all three tests true |
| `learnings.md` | 63 | not loaded | generated | – |
| `experiments.md` | 30 | not loaded | generated | – |
| `queue/topics.yaml` | 1,002 | not loaded | 16 topic rows | – |
| **Loaded every turn** | **4,140** | **2,739** (−34%) | | |

The new skill `.claude/skills/jev-card/SKILL.md` loads only its description each turn (about 25 words).

## Approved and applied

1. **Removed `@queue/topics.yaml`, `@learnings.md` and `@experiments.md` from `CLAUDE.md`.** Principle: progressive disclosure (only some branches need them). Who reads them now: `/next` (`next/SKILL.md:41,47`), `/draft-thread` (`draft-thread/SKILL.md:24`), `/posted` (step 3), `/results` (`results/SKILL.md:17,33`), `/apply` (`apply/SKILL.md:12`). Every one already names the file, so no skill changed. File content untouched (generated files).
2. **Cut `CLAUDE.md` "Cloud session notes" to the cloud-only line** (X API keys unavailable). Principle: single source of truth. The other five lines repeated `AGENTS.md:5,10,13,14,16`.
3. **Moved "Design grilling (Jev cards)" out of the always-loaded file** into `.claude/skills/jev-card/SKILL.md`, word for word. Principle: branching (a rare trigger doesn't belong in every turn). `AGENTS.md` keeps the heading and a one-line pointer. `scripts/jev_referee.py`, `jev/thresholds.yaml` and the vote script are unchanged.
4. **Trimmed "What every post delivers"** (`voice/exit-zero.md:16`) to a positive target plus a one-clause reason. "Posting stays manual" lives in `AGENTS.md:13`.
5. **`AGENTS.md:15` Voice bullet:** dropped the second copy of the banned-phrase list. The only list is `voice/exit-zero.md` → Banned phrases (Fixed; unchanged).
6. **Voice repeats consolidated** (duplication):
   - "Drop a hi" now sits in the Asking for engagement list, the single home of the engagement rules (meaning unchanged).
   - Networking's "Bare 👋, repeated lines…" line is removed; Replies already carries both rules (`:53`, `:57`).
   - Networking's gate sentence now points to Asking for engagement.
   - Makers' shout-out line points to the Replies no-repeat rule.
   - Every heading was kept: `format-tool-swap/SKILL.md:125-126` links to → Makers and → Boosting, and six checklists cite "banned phrases and farm tells".

## Declined

- **Stop loading `voice/exit-zero.md` and `reference/audience.md` every turn** (Codex; about 1,660 words). Operator kept both loaded: reply and post advice comes up in chat without a command.
- **Collapse `AGENTS.md` Layout to a map pointer** (Codex; about 400 words). Declined: it holds rules the directory can't show, such as the `x_read.py` "never cite a post that didn't pass this check" rule, what isn't committed, and whose data is private.
- **Split Replies/Networking/Makers/Boosting into a separate reference** (Codex). Declined: it adds a file and retargets the tool-swap links, and the voice file stays loaded anyway.

## No change

- **`AGENTS.md:52` gate bullet.** It restates the gate's refusals, but `scripts/post_thread.py` has no docstring listing them, so this is the only written copy.
- **`reference/audience.md` "Before 24 Sep".** No relabel record exists in `ledger/` yet, so it is still live.
- Operating rules, What the loop may never change, Operator commands, Git, Banned phrases, Truth budget, Images, Boosting, the Grok mentions (still shared, per BRIEF), `learnings.md`, `experiments.md`, `queue/topics.yaml` content.

## Codex comparison

Blind read-only run (`task`, gpt-5.6-terra, job `task-mulab0ay-x0pshw`), given the files, the principles and BRIEF, without these findings.

- **Agreed:** changes 1–4 above, and no content change to audience, learnings, experiments or topics.
- **Codex only:** the three declined items.
- **Mine only:** changes 5 and 6 (duplicates inside the always-loaded set).
- **Citation spot-check:** `format-tool-swap/SKILL.md:123-126` checked out.

## Check

`python3 -m unittest discover -s tests`: 173 tests, OK. No posting skill or gate text changed, so there was no `--count` run.

## For the operator

- **Nothing was renamed or removed.** No file points at a heading in these files other than the voice → Makers/Boosting and "banned phrases and farm tells" links, and all of those headings are kept.
- **Grok loads `.claude/skills/`,** so the new `jev-card` skill is available there too. Whether Grok follows `AGENTS.md`'s pointer to it wasn't tested.
