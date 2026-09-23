---
name: draft-thread
description: >
  Write a Hidden Settings thread in Exit Zero voice into
  drafts/YYYY-MM-DD-slug/. Research and verify before cards. Print a
  copy-paste preview. A human creates APPROVED.
when-to-use: >
  Use when the user says draft a thread, next topic, write hook, generate
  hidden settings thread, or /draft-thread.
argument-hint: "[topic-slug|device-name]"
user-invocable: true
---

# Draft thread

Write the thread. Stop at a filled draft folder plus a chat preview.

Format: `/hidden-settings`. Paths: `/verify-settings`.

## Argument

Slug or device name. Bare `/draft-thread` or "next topic" → first `status: queued` row in `queue/topics.yaml`.

## Steps (this order)

1. **Contract.**
   Read `AGENTS.md`, `voice/exit-zero.md`, `queue/topics.yaml`.
   Done: all three read this session.

2. **Format.**
   Read `.grok/skills/hidden-settings/SKILL.md`, `.grok/skills/hidden-settings/examples.md`, and both folders under `examples/` before any hook prose.
   Done: beat order and both gold threads are in view.

3. **Topic.**
   Argument matching a yaml slug or device, else the first `queued` row. New device → kebab slug, add the yaml row.
   Done: slug, angle, and N-range (5–8) written down.

4. **Research, then write.**
   Finish research before hook or card prose. Spawn a research subagent when available; otherwise finish the research pass in this turn, then write.
   Each candidate: name, exact path, official URL, models / OS, skip line. 5–8 settings matching the angle. No official path → omit.
   Done: candidate list exists. `01-hook.md` does not.

5. **Verify.**
   Run `/verify-settings` for this slug. Cards are `high` / `medium` rows only. `VERIFY` rows stay in `PATHS.md` and out of numbered posts.
   Done: `PATHS.md` in the draft folder. Card count = kept rows. Hook N will match.

6. **Files.**
   `drafts/YYYY-MM-DD-slug/` (today's date, kebab slug). Reuse that folder if it already exists.

   Consecutive two-digit names:
   - `01-hook.md`
   - one `NN-<setting-slug>.md` per kept setting
   - `NN-closer.md`
   - `images.md` — hook image is before/after of the same object, shot on a real device; optional screenshots to take
   - `CHECKLIST.md` — copy `.grok/skills/draft-thread/checklist.md`
   - `PATHS.md` from step 5

   Hook, cards, closer follow `/hidden-settings`.
   Done: those files exist. Card files = kept settings. Hook names that N.

7. **Queue.**
   Set that topic's `status` to `drafted` in `queue/topics.yaml`.
   Done: the yaml row says `drafted`.

8. **Gate.**
   Leave `APPROVED` uncreated. A human creates it.
   Done: `APPROVED` is absent.

9. **Preview.**
   Print `01-hook.md` through closer in chat, separated by `---`. Then list leftover `VERIFY` rows and the `images.md` shots.
   Done: preview is in the reply. This skill stops.
