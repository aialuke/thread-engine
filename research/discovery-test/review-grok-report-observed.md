# Review of Grok's report: observed claims (C227–C240)

Checked 26 Sep 2026 by the build-strategy session against `private/grok-insights/runs/semantic-live-2026-09-26/calls/*` with a script (ids, timestamps, authors, "No results" lines, overlaps).

| ID | Mark | Evidence |
|---|---|---|
| C227 | KEEP (the "default threshold" part is the reported schema, not observed) | S1: 10 slots, 9 numeric ids, 1 blank slot; posts dated 2024–2026 |
| C228 | KEEP | No score or language line in any raw file |
| C229 | UNRESOLVED | S2 ids match S1, **but the run's own README says `S2.raw.txt` was saved from `S1.raw.txt` with one view count edited**, not captured from S2's call (found by Codex, confirmed by diff). So S2 proves nothing about threshold 0. |
| C230 | KEEP | S3: "No results" |
| C231 | KEEP | S4: 10 ids, all 2026 (24–25 Sep); 3 overlap S1 |
| C232 | KEEP | S5: 6 posts, one author (the S1 author) |
| C233 | KEEP | S6: that author absent; 10 slots incl. 1 blank |
| C234 | KEEP | S7: "No results" |
| C235 | KEEP | S8 ∩ S1 = 0; S8 includes a 2018 post |
| C236 | KEEP | S9 includes 2024 and 2025 posts despite `within_time:6h` in the query |
| C237 | KEEP | K1: 10 posts, all 26 Sep 2026, none shared with S1; spot-checked text is account-selling spam |
| C238 | KEEP | K2: 1 post, none shared with S8 |
| C239 | KEEP as inference (the raw doesn't define a reply field) | Rendering has ID and Conversation ID only; no reply-to field |
| C240 | KEEP | `field-inventory.md` and `overlap.md` exist |

**Limits of these runs** (not errors in the report):
- **The raw files are the parent Grok session's saved copies of its runners' messages, not captured tool output.** At least one (S2) was reconstructed from another file. Treat every raw file as a transcription until the pilot captures output with provenance (original stdout, hash, cwd, time).
- The raw files were written by the Grok session; the post ids were not checked against the X API, so "verbatim tool output" is likely (bios, avatars, engagement lines) but unproven. The pilot should verify these ~60 ids by X API lookup (about $0.30 plus authors), which also measures Grok's invented rate on real semantic output.
- One meaning query, one paraphrase, one product. Directional only.
- Grok ran with the repo as its working folder (it loaded `AGENTS.md`, skills and its memory, per C150–C158).
- S2–K2 all started at 07:43:23Z: run in parallel in one turn.
