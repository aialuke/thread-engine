---
name: format-settings
description: >
  Settings format (multi-post Hidden Settings thread): points at the
  settings contract and lists its research, fact-check, image and
  checklist rules.
user-invocable: false
---

# Format: settings

- **Contract:** read `.claude/skills/hidden-settings/SKILL.md` (hook beats, cards, closer, emoji budget) and `.claude/skills/hidden-settings/examples.md` before writing.
- **Shape:** a thread. Root plus N setting cards plus a closer. N: `Root post` in the contract.
- **Research:** each candidate setting needs a name, exact path, official URL, models / OS, and a skip line.
- **Fact-check:** `/verify-settings <folder>` in paths mode writes `PATHS.md`. Cards use `high` and `medium` rows only.
- **Images:** hook image is a real before/after photo of the same object, or no image.
- **Checklist:** copy `.claude/skills/format-settings/checklist.md` to the draft as `CHECKLIST.md`.
