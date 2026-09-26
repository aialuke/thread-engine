# Factory: moving off Grok (plan, 26 Sep 2026)

**Decision:** D88 (`reviews/ui-direction.md`). The operator dropped Grok entirely, for the product and for this factory. This file plans the factory's change. **Nothing here is done yet.** Until it is, the factory keeps working as it does today (Grok relay, commands typed in Grok or Claude Code), and `AGENTS.md` stays as it is. Changing the rules before the code would break `/next`.

**Evidence and search rules:** `research/discovery-x-api-search-proposal.md` and `research/discovery-test/private/facts.md`. Relevant X API facts, confirmed on this account's pay-per-use keys:
- recent search works with the Keychain's OAuth 1.0a keys;
- the query limit is 512 characters;
- `min_likes:`, `min_replies:` and `-is:reply` are accepted;
- relevancy sort favours older, high-engagement posts;
- results are X's own data, so no id check is needed;
- about $0.005 a post.

## What changes

| Where | Today | After |
|---|---|---|
| `scripts/x_read.py` | `search` and `thread` run one Grok call, then check every post by id on the X API | `search`: X API recent search through `x_api.Client` (GET only), with the same JSON shape out. `thread`: the X API conversation read. No Grok, and no id check (X's own data). Keeps the query rules: API syntax only, 512-character check, exact window |
| `scripts/x_api.py` | No search function; docstring says other people's posts go through Grok | Add `search()` (recent search, cost per post returned, `sort_order`, `start_time`/`end_time`). Docstring updated |
| `scripts/grok_read.py` | The one Grok call | Deleted once nothing imports it (`snapshot.py` never did, layer-1 H4) |
| `scripts/draft.py` | Prints a `grok -p "/draft-thread …"` command | Deleted, or prints the Claude Code equivalent |
| `scripts/loop.py:429` | Default `source` is `"grok"` | `"agent"`. Data only; existing ledger rows untouched |
| `.claude/skills/next/SKILL.md` | "in Grok or Claude Code" (line 12); the demand example uses website syntax with `-filter:replies` (line 46); reply leads via `x_read.py` | Claude Code only. The demand example in API syntax, **replies kept**, no engagement floor, 2–3 phrasings (pilot lessons). Reply leads use `-is:reply` and `min_replies:` |
| `.claude/skills/format-tool-swap/SKILL.md:48` | "never a raw Grok search" | "check with `x_read.py search`" (now X API) |
| `.claude/skills/approve/SKILL.md` | Explains registration for Claude Code and Grok | Claude Code only |
| `.claude/hooks/guard_approved.py` | Handles both Grok's and Claude Code's tool names; blocks `grok -p "/approve …"` | Keep blocking any CLI that nests `/approve`, `grok` included, as a safety net. Grok-only tool names can stay until tests cover the change |
| `.claude/settings.json` | Allowlist for both tools | Claude Code only |
| `AGENTS.md` | Lines 9, 13, 41, 53–57: Grok as a command tool and as the X reader | Claude Code only. "Other people's posts go through `scripts/x_read.py` (X API recent search)". The script list updated |
| `README.md` | Operator guide: type in Grok or Claude Code; Grok balance; Grok hook trust | Claude Code only; the Grok balance and hook-trust notes removed |
| `reference/x-api.md` | No search facts | Add: search price, 512 limit, operators confirmed, sort behaviour |
| `tests/test_x_read.py`, `tests/test_scripts.py` | Test the Grok relay | Test X API search with the fake opener, as `tests/test_x_api.py` does |

| `voice/exit-zero.md:55` | "Grok may suggest what a reply should say" | "A model may suggest…" (the rule is about pasting, not Grok) |
| `reference/x-algorithm.md:25` (A12, "our rule" column) | "Grok may suggest what to say" | "A model may suggest what to say". The rest of the file cites X's own `xai-org` repo, which is unaffected |
| `examples/iphone-18-pro-aperture.md:5`, `examples/macbook-battery.md:5` | Point to `.grok/skills/…`, already a stale path | `.claude/skills/…` |
| `scripts/loop.py:2` docstring | "Grok calls this" | "The agent calls this" |

**The operator's call, not infrastructure:**
- `reference/audience.md:5` says the pipeline uses "AI agents (Claude, Codex, Grok)". That's a public-facing promise about the operator's own pipeline; update it only if the operator also stops using Grok in their own builds.
- `queue/topics.yaml:102` notes "the account's own pipeline runs on paid Claude, Codex and Grok". Same.

Not infrastructure, so not changed: Grok as **example content** in `format-tool-verdict` and `verify-settings` (a verdict comparing Claude, Codex and Grok is still a valid post).

## Order

1. Add `x_api.search()` and rewrite `x_read.py` on it, keeping the JSON shape, so skills keep working. Tests first.
2. Switch `/next` and `format-tool-swap` to the new rules (API syntax, replies kept for demand).
3. Update `AGENTS.md`, `README.md` and `reference/x-api.md` in the same change, so the rules and the code agree.
4. Remove `grok_read.py`, `draft.py` and the Grok-only settings; tidy the guard and the approve skill.
5. The operator stops using Grok as the command tool; Claude Code only.

## Constraints

- Don't touch loop state, the ledger, or anything that affects the ~8 Oct experiment rules or the 16 Oct final read. The daily snapshot doesn't use Grok, so it's unaffected.
- The `/approve` gate, fail-closed fact-checks and the no-X-writes rule stay as they are (`AGENTS.md`, what the loop may never change).
- Search is billed per post returned: `/next` demand at 2–3 queries × 10 is about $0.15 a run. Record it in `ledger/runs.log` like other X API reads.
- Start in Plan mode (`AGENTS.md`).
