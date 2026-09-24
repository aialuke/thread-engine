# X API reference

Sources: https://docs.x.com/x-api (OpenAPI 2.168), https://docs.x.com/x-api/getting-started/pricing, https://docs.x.com/x-api/fundamentals/metrics
Read: 2026-09-24. Live tests: 2026-09-24, pay-per-use app, OAuth 1.0a user context.
Client: `scripts/x_api.py`. Keys: macOS Keychain, service `thread-engine-x`.

This is what the X API can and cannot tell the loop about the account's own posts. Other people's posts and research still go through Grok (`scripts/x_read.py`).

## Verified facts

| # | Fact | Source | What we do |
|---|---|---|---|
| P1 | The keys have Read permission. Every tested response carried `x-access-level: read`. | Live test | **This is the real no-writes guarantee: X refuses writes from these keys.** The client also sends GET only and stops if a response reports any other level. |
| P2 | Reading the account's own posts, mentions and followers is an "owned read": $0.001 per item. It covers `GET /2/users/{id}/tweets`, `/mentions` and `/followers` when `{id}` is the app owner. | Pricing page | All own-account reads go through those three endpoints. |
| P3 | Looking a post up by ID (`GET /2/tweets?ids=`) is a standard post read, $0.005 per item, even for the account's own posts. The usage counter counted only the 2 ID lookups in a test that also read 153 posts from the timeline. | Pricing page; live test | Never look up the account's own posts by ID. Use timeline windows. |
| P4 | A user read is $0.010 per item (`/2/users/me` included). | Pricing page | Read the profile weekly, not daily. |
| P5 | Items are charged once per UTC day. Reading the same item again the same UTC day is free (X calls this a soft guarantee). | Pricing page | One daily run. A repeat run the same UTC day costs nothing. |
| P6 | `organic_metrics` and `non_public_metrics` exist only for posts created in the last 30 days. | Metrics page | Every post gets its final read at days 26–29. The client refuses windows older than 29 days. |
| P7 | The user timeline returns `organic_metrics` for every post, reply and quote: `impression_count`, `like_count`, `reply_count`, `retweet_count`, `user_profile_clicks` (plus `url_link_clicks` when a post has a link). **It has no quote or bookmark counts.** | Live test (154 items); metrics page | Quotes and bookmarks come from `public_metrics` and are labelled "total", not organic. |
| P8 | A root's `reply_count` counts the account's own thread cards. MacBook thread: 8 replies, 0 from other accounts. | Ledger; live test | Engagement uses replies from other accounts (from mentions), never a root's `reply_count`. |
| P9 | Public impressions equalled organic impressions (within 1) on 10 of 11 originals and quotes. The exception was the boosted tool-swap: 2,082 public, 98 organic. Its `promoted_metrics` were all 0. | Live test | A post with more than 10% non-organic reach is marked `nonorganic` and kept out of experiments, whatever the cause. |
| P10 | The public−organic gap is not always a Boost. X's forum has cases with a large gap and zero `promoted_metrics`. | devcommunity.x.com threads 262134 and 262980 (April 2026) | The rule in P9 doesn't try to name the cause. |
| P11 | `GET /2/tweets/analytics` (per-post `follows`, `unfollows`, `shares`, `user_profile_clicks`, hourly to total) and `GET /2/media/analytics` return 403 `client-not-enrolled` on pay-per-use. X staff said on 12 Mar and 27 May 2026 that both are Enterprise-only. | Live test; devcommunity threads 259582 and 266576 | Per-post follows are credited by matching (see below), or read from the analytics CSV export if it has them. |
| P12 | `context_annotations` gives X's own entity and topic labels for each post (e.g. "Computer software", "Animation"). | Live test | Topic mix in reviews. **A proxy**: it's not the topic-share classifier in `x-algorithm.md` A8. |
| P13 | The account's user ID is `1994313953191833600`. | Live test (`/2/users/me`) | Hardcoded in `x_api.py`. |

## X's analytics export has what the API doesn't

On a computer, X → Premium → Analytics → Content → Export gives a CSV (`account_analytics_content_<from>_<to>.csv`) with one row per post and reply. Columns: Post id, Date, Post text, Post Link, Impressions, Likes, Engagements, Bookmarks, **Shares**, **New follows**, Replies, Reposts, **Profile visits**, Detail Expands, URL Clicks, Hashtag Clicks, Permalink Clicks. Checked 24 Sep 2026 on the export for 18–24 Sep.
- Its numbers are organic. The boosted tool-swap shows 98 impressions, against the API's organic 99 and public 2,105.
- Its profile visits match the API's (58 total).
- `loop.py record-export --csv <file>` adds each row to the activity file; the latest export wins, because X's numbers are cumulative per post. **The export is the exact per-post follow source.** The matching below is the fallback between exports.

## Follow credit without the analytics endpoint

The loop compares follower IDs day to day. Each new follower is credited once, to the most recent of: replying to one of our posts (from mentions), or being an account one of our replies went to (`in_reply_to_user_id`). Anyone who followed without either stays unattributed, so per-post credit is a lower bound. Quoters aren't matched: a quote that doesn't tag us never appears in mentions.

## Not verified, do not plan around

- Whether the follower list comes back newest-first. If it does, the daily read can stop at the first known follower.
- Whether `expansions` are billed as extra user or post reads. The client doesn't use them.
- The price of `GET /2/tweets/{id}/liking_users`. It isn't an owned read. The client doesn't call it.

## Privacy

Follower IDs (`loop/followers/`) and raw API responses (`ledger/raw/api/`) contain other people's data. Both are gitignored and stay on this Mac. Only counts and per-post totals are committed. Model sessions read the ledger, so nothing about a specific person goes there.

## Spend

Set in the developer console: a spending limit of $10 per billing cycle, auto-recharge off. Expected spend at September 2026 volume (about 40 items a day): under $0.25 a day. `ledger/runs.log` records the estimate for each run.
