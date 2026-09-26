# What we learned about Grok, and how this project constrains it (26 Sep 2026)

Summary from the build-strategy session, after `docs-*.md`, `community-grok-prompting.md`, `repo-grok-setup-audit.md`, Grok's own report and live run (`private/grok-insights/`) and the four reviews (`review-grok-report-*.md`). Directional: one live run.

## Grok
- Two search engines. **Keyword** (live; X website syntax; `Latest` on "CapCut" returned 10/10 spam). **Semantic** (matches meaning; on "people unhappy with CapCut charging to export" it found genuine complaints). Semantic search is the one thing the X API can't do.
- Semantic limits: not recent-first (2018–2025 posts without dates); calendar-day dates only, no hours; a rewording returns a different set; some empty result slots; no score or language shown.
- In-session controls, per Grok's own tool definitions and not in xAI's docs: `limit` (default 3, max 10), `min_score_threshold` (0.18), `usernames`/`exclude_usernames`, dates; keyword `mode` Top/Latest. Unconfirmed until the pilot.
- In session Grok sees id, time, author, engagement and text; an API caller gets only Grok's text and links. Grok's saved copies aren't guaranteed faithful (its S2 file was reconstructed from S1).
- No official or community guidance on prompting it for X search. The one supported tip: cap posts fetched.
- Invented-post rate unknown; earlier cases came through the keyword relay's retyping. The pilot checks ~60 real semantic ids.
- Cost $5 per 1,000 posts fetched plus tokens, no repeat discount; CLI bills the subscription.

## How this project constrains Grok
1. `scripts/x_read.py` forces one `x_keyword_search`, `Latest`, limit 10: semantic search has never been used by the factory.
2. `scripts/grok_read.py` forces `--effort low` (default is high) and sets no model.
3. `/next` allows one or two keyword searches for demand.
4. Run in the repo, Grok loads `AGENTS.md`, `CLAUDE.md`, 17 skills and its memory; `format-tool-swap` ("never a raw Grok search") can fire unasked on "free alternatives".
5. Grok's memory is out of date (old Hidden Settings audience).
6. `/next`'s example query mixes website syntax (fine for Grok, wrong for the X API) with `lang:en`, which Grok's tool doesn't list.
7. `x_read.py`'s text match (60% or first 40 characters) can count a real paraphrased post as invented.
8. Hooks and settings don't touch search.

Bottom line: the factory has used Grok in roughly its weakest configuration. The Discovery test measures it at its best before the product decides whether to drop it.
