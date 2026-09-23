# X tools pilot

Run: 2026-09-24 (AEST). Grok Build 1.0.40, read-only sandbox, Bash/Edit/Write denied. Session `01a0cf9c-cea6-7531-9baf-e2e1939b38d4`, cost about US$0.53.
Posts: thread root `2102272933087363155` (6 posts) and standalone `2102737637346095128` (plus 1 self-reply card).

## What the tools return

Responses are rendered text, not JSON. Each post has an `Engagement:` line and a `Timestamp:` line.

| Metric | Available | Where | Precision | Ledger field |
|---|---|---|---|---|
| Views | yes | `Engagement` `Views=` | exact integer, live (moved 1271 → 1273 between two calls) | `views` |
| Likes | yes | `Likes=` | exact integer | `likes` |
| Reposts | yes | `Reposts=` | exact integer | `reposts` |
| Quotes | yes | `Quotes=` | exact integer | `quotes` |
| Replies | yes | `Replies=` | exact integer. Counts direct replies only, so a thread root counts its own first card | `replies` |
| Bookmarks | yes | `Bookmarks=` | exact integer | `bookmarks` |
| Per-card views | yes | each card's `Engagement` line in `x_thread_fetch` | exact integer | `cards[].views` |
| Posted time | yes | `Timestamp: Tue, 22 Sep 2026 05:45:00 GMT` | seconds | `posted_at` |
| Media | yes | `Media` / `Item N: photo` | type only | `media` |
| Reply authors | yes | `x_keyword_search conversation_id:<root>` (Top includes the root, Latest omits it) | complete for these two threads; capped at 10 per call, page with `since_id` / `max_id` | `repliers` |
| Follower count | yes, account only | `x_user_search` `Followers:` | exact integer | snapshot `followers` |
| First-like time | **no** | not in any response | n/a | not recorded |
| Following / post counts | no | not in `x_user_search` | n/a | not recorded |

Failure shape: `x_thread_fetch` on a missing id returns `Failed to fetch thread: Post 1 is missing extended_data.conversation_id in API response`. A snapshot that gets this is recorded as missing, never as zeros.

## Consequences for the ledger

- The primary outcome is root `views` at the snapshot. It is exact but live, so the snapshot stores the time it was taken and the post's age.
- Outside replies are computed, not read: every reply author in the conversation minus the account's own handles and the operator's other handles. The `Replies=` count is kept as-is for reference.
- "Time to first like" from the plan is dropped. The tools cannot see it.
- Follower count is taken once per snapshot run from `x_user_search`, and reported for the account only.

## Operator steps checked

- **Approval line.** Grok 1.0.40 has no `!` shell prefix. Approval is instead a `UserPromptSubmit` hook on the typed text `/approve <slug>`. The hook payload carries the typed text in `prompt` (captured 2026-09-24). The hook writes `APPROVED` and blocks the prompt, so the model never sees it.
- **Headless runs.** `grok -p` fires `UserPromptSubmit` hooks too, so a model-started `grok -p "/approve …"` is blocked by a `PreToolUse` guard.
