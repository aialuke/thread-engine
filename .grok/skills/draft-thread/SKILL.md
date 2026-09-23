---
name: draft-thread
description: >
  Write one post or thread in Exit Zero voice into drafts/YYYY-MM-DD-slug/,
  in the format named by its queue row. Research and verify before cards.
  Print a preview. The operator approves by typing /approve.
when-to-use: >
  Use when the operator says draft a thread, draft the next post, write
  the hook, or /draft-thread.
argument-hint: "[topic-slug]"
user-invocable: true
---

# Draft thread

Write the draft. Stop at a filled draft folder plus a chat preview. `AGENTS.md` asks for Plan mode first on non-trivial work; if the session is not in Plan mode, say so once and continue.

## Argument

A queue slug. Bare `/draft-thread` → the queue row with `status: planned`, else the first `status: queued`.

## Steps (this order)

1. **Contract.** Read `AGENTS.md`, `voice/exit-zero.md`, `reference/audience.md`, `reference/x-algorithm.md`, and `queue/topics.yaml`.
   Done: all five read this session.

2. **Topic.** Find the queue row. Note `format`, `lane`, `experiment`, `arm`, `treatment`, and `hypothesis` if present. A row with no `format` is `settings`.
   Done: slug, format and, if set, the experiment arm are written down.

3. **Format.** Read `.grok/skills/format-<format>/SKILL.md` and every file it points to. A settings row also reads `.grok/skills/hidden-settings/examples.md` and the gold threads in `examples/`.
   If the row is a `treatment` or `control` arm, the arm's description wins over the format's defaults (for example card count). Never change anything else about the post, so the test stays clean.
   Done: shape, research rule, image rule and checklist are known.

4. **Research, then write.** Finish research before any card prose, following the format's research rule. No official source → the item is omitted.
   Done: a candidate list exists. `01-hook.md` does not.

5. **Verify.** Run `/verify-settings <folder>` in the mode the format names (`paths`, `claims`, or both). Cards use `high` and `medium` rows only. `VERIFY` rows stay in `PATHS.md` / `CLAIMS.md` and out of cards.
   Done: `PATHS.md` and/or `CLAIMS.md` exist in the draft folder.

6. **Files.** `drafts/YYYY-MM-DD-slug/` (today's date in Australia/Sydney). Reuse the folder if it exists.
   - `FORMAT` — one word: `settings`, `comparison`, `tool-swap`, or `single-tip`
   - `01-hook.md` and further consecutive `NN-<name>.md` cards as the format's shape says. A single-tip has only `01-hook.md`.
   - `images.md` — what to attach, following the format's image rule. Write `Attach: none` when nothing is attached.
   - `CHECKLIST.md` — copy of `.grok/skills/format-<format>/checklist.md`, boxes ticked where done
   Done: files exist. Card count matches the format, the hook, and the arm.

7. **Queue.** Set the row's `status` to `drafted` and `draft:` to the folder.
   Done: the row says `drafted`.

8. **Gate.** Never create, edit or delete `APPROVED`. A hook blocks it anyway.
   Done: `APPROVED` is absent.

9. **Preview.** Print every card in order, separated by `---`, with each card's character count. Then list leftover `VERIFY` rows and what `images.md` asks for. End with exactly:
   `Read the cards. If you change any, that's fine. When they're right, type /approve <slug>. Then /ready <slug>.`
