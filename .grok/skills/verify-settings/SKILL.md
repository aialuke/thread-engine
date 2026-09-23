---
name: verify-settings
description: >
  Fact-check Hidden Settings paths against current official docs. Fail
  closed. Write PATHS.md. Unconfirmed paths are VERIFY.
when-to-use: >
  Use before a draft is marked ready, when a Settings path might have
  changed, or /verify-settings.
argument-hint: "<draft-slug>"
user-invocable: true
---

# Verify settings

Fail closed. A path missing from an official page this session is `VERIFY`.

Copy is `/draft-thread`. Format is `/hidden-settings`.

## Argument

`<draft-slug>` is the folder under `drafts/` (`YYYY-MM-DD-slug` or a kebab slug). Omitted → the open draft. None open → ask for the slug.

## Steps

1. **Version assumptions.**
   Read the draft folder (`PATHS.md`, else `sources.md`, else the setting files). Each candidate gets OS / app / hardware (iOS version, Camera generation, gateway model, firmware family).
   Done: every candidate has a version line, or unknown — and unknown fails closed.

2. **Official docs.**
   Open the vendor page (Apple Support, manufacturer admin guide, ISP gateway help). Confirm control name, full path, models or OS versions. Date: `YYYY-MM-DD`.
   Done: each kept row has a live official URL. Forums and memory are not sources.

3. **Write `drafts/<slug>/PATHS.md`.**

   ```markdown
   # PATHS
   Checked: YYYY-MM-DD
   OS / app assumptions: …

   | Setting | Path | Source URL | Date checked | Confidence | Notes |
   |---------|------|------------|--------------|------------|-------|
   | Grid and Level | Settings → Camera → Grid, Level | https://support.apple.com/… | YYYY-MM-DD | high | |
   | Main Camera default | VERIFY | — | YYYY-MM-DD | VERIFY | no official path this session |
   ```

   Confidence: `high` (page names the control), `medium` (page names the feature; label taken from that page), `VERIFY` (no official path).
   Done: every candidate is a row.

4. **Gated controls.**
   Pro-only, model-only, plan-only, firmware-only → say so in Notes. Thread body uses ⚠️ once (`/hidden-settings` emoji budget). `PATHS.md` names every gated row in prose.
   Done: every gated row is labelled in Notes.

5. **VERIFY.**
   Unconfirmed → Path `VERIFY`, Confidence `VERIFY`. Row stays. Card stays off the ready list.
   Done: no guessed menu in `PATHS.md` or in any card file.

6. **Stop.**
   Tick Verify boxes in `CHECKLIST.md` when that file exists. `PATHS.md` is the deliverable. Confidence `VERIFY` means the draft is not ready.
