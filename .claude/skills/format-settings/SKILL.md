---
name: format-settings
description: >
  Loader for the settings format (multi-post Hidden Settings thread).
  Points at the settings contract and lists its research, fact-check,
  image and checklist rules. Used by /draft-thread.
user-invocable: false
---

# Format: settings

- **Contract:** `.claude/skills/hidden-settings/SKILL.md` (hook beats, cards, closer, emoji budget) and `.claude/skills/hidden-settings/examples.md`.
- **Shape:** a thread. Root plus N setting cards plus a closer. N is 3 to 7; an experiment arm in the queue row wins.
- **Research:** each candidate setting needs a name, exact path, official URL, models / OS, and a skip line.
- **Fact-check:** `/verify-settings <folder>` in paths mode writes `PATHS.md`. Cards use `high` and `medium` rows only.
- **Images:** hook image is a real before/after photo of the same object, or no image. AI images only as labelled illustration.
- **Checklist:** copy `.claude/skills/format-settings/checklist.md` to the draft as `CHECKLIST.md`.
- **Gate extras:** the gate refuses a settings hook that opens on "Most ".
