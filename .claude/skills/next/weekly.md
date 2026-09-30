# Weekly work

Reached from `/next` step 2 when `review.review_due` is true.

1. Follow `.claude/skills/results/SKILL.md` (it writes the weekly review and ends with `mark-reviewed`).
2. Algorithm check: follow the refresh rule in `reference/x-algorithm.md` (compare each cited file's blob SHA with `main`). If any changed or is gone: `python3 scripts/loop.py set-reference --status stale --files <paths>` and tell the operator which facts need a re-read before lessons that cite them are trusted. If none: `set-reference --status current`.
3. Offer `/lint` once (docs check). Run it only if the operator says yes.
