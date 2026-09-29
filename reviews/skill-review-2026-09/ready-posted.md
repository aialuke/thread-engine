# Skill review: ready and posted (29 Sep 2026)

Scope: `.claude/skills/ready/SKILL.md`, `.claude/skills/posted/SKILL.md`. Method: `BRIEF.md`; independent read by Codex (read-only, findings withheld).

## Baseline
- ready: 289 words, 6 steps. Criteria: gate exit code (2, 1, 0); run sheet shown; "Card N is on your clipboard"; `next` per card; final `/posted` prompt.
- posted: 398 words, 9 steps. Criteria: root id taken; raw file saved; queue row matched; each difference classed once; minutes asked; JSON written; `record-post` run; queue row set; operator told.
- Pointers in: AGENTS.md, README.md, draft-thread, format-tool-swap, approve.py, queue/topics.yaml. No name, heading or step number changed.

## Approved and applied (all ten proposed)
ready
1. Every `--copy` reruns the gate: exit 1/2 handled as in step 2; last card is `next: none`.
2. Run sheet comes from script output; counting rule no longer restated.
3. Tool-swap `wait:` handling moved beside `--copy 1`.
4. Finder selects the attachment only when the file exists (post_thread.py:254-260).
5. Closing prohibition rewritten as a positive target; the no-X-write guardrail is kept.

posted
6. `x_api.py thread` covers 6 hours and returns no media (x_api.py:55-57, 246-252): media and `ai_media` come from `images.md` and the operator.
7. Compare cards both ways; a card added or removed is a difference. A violation that is also a deviation takes `violation`; the step 6 arm rule still applies.
8. `violation` points at `voice/exit-zero.md` and the gate instead of a partial list.
9. Minutes asked once; unknown stays `null` (loop.py:207-209 accepts it); payload example no longer `0`.
10. Replacement keys on the record's `auto` flag, not the slug (loop.py:355-362); continue only on `recorded: true`; "already recorded" still sets the queue row if it says `drafted`.

## Declined
None.

## Disagreements with Codex
- Codex suggested a pointer for experiment-arm rules in posted. Left inline: it is one sentence.
- Item 10's stale-queue case is Codex's inference, kept because it costs one clause.

## Checks
`python3 -m unittest discover -s tests`: 173 OK. `post_thread.py drafts/2026-09-24-paid-free-developer --count` runs.
