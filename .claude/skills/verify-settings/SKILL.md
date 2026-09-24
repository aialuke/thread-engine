---
name: verify-settings
description: >
  Fact-check a draft against current official pages. Fail closed. Paths
  mode writes PATHS.md; claims mode writes CLAIMS.md. Unconfirmed rows are
  VERIFY.
when-to-use: >
  Use before a draft is marked ready, when a Settings path might have
  changed, or /verify-settings.
argument-hint: "<draft-slug> [paths|claims]"
user-invocable: true
---

# Verify settings

Fail closed. A path missing from an official page this session is `VERIFY`.

Copy is `/draft-thread`. Format rules are in the draft's format skill (`.claude/skills/format-<FORMAT>/SKILL.md`).

## Argument

`<draft-slug>` is the folder under `drafts/` (`YYYY-MM-DD-slug` or a kebab slug). Omitted → the open draft. None open → ask for the slug.

Mode: `paths` (default) checks menu paths into `PATHS.md`. `claims` checks every other factual claim (prices, free tiers, specs, platforms) into `CLAIMS.md`. A draft can need both.

## Paths mode

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


## Claims mode

1. **List claims.** Every figure, price, free-tier statement, platform, spec, and "no watermark"-style promise in the cards. Each is one row.
2. **Official source.** The vendor's own pricing, feature, spec or support page, opened this session. Reviews, forums, and memory are not sources.
3. **Write `drafts/<slug>/CLAIMS.md`:**

   ```markdown
   # CLAIMS
   Checked: YYYY-MM-DD

   | Claim | Card | Task or model it applies to | Source URL | Date checked | Vendor-stated or tested | Confidence | Notes |
   |-------|------|-----------------------------|------------|--------------|-------------------------|------------|-------|
   ```

   Confidence: `high` (the page states it), `medium` (the page states it for a narrower case; Notes says which), `VERIFY` (not found).
   "Tested" only when the operator says they did it.
   **The operator's own run** (build-log and tool-verdict claims such as "the pipeline made this script in 4 minutes" or "Grok caught 3 bugs Codex missed"): Source URL is `operator, <date>` plus the artifact that shows it, a screenshot in the draft's `images/` or a log file path. Vendor-stated or tested: `tested`. No artifact means the row is `VERIFY`.
4. **VERIFY.** Unconfirmed claims stay as `VERIFY` rows and come out of the cards. Never soften a claim to keep it.
5. **Stop.** Tick the verify boxes in `CHECKLIST.md`.
