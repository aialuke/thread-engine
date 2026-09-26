# X API discovery: search, timelines, pricing, fields, policy

Docs-only research, fetched today (2026-09-26) via WebFetch against docs.x.com / developer.x.com.
Read: `reference/x-api.md`, `research/layer-2-x-data-tiers.md` §2.1/2.4/2.5 (background, already sourced separately — not re-verified here except where noted).
No X API or xAI call was made. No Keychain read. No script run. `loop/followers/`, `ledger/raw/api/`, `loop/inbox/` were not opened.

Every quote below came back through WebFetch, which reads the page with a small summarizing model rather than handing back raw HTML. Where I could re-query the same page and get an exact substring match (yes/no) I trust the quote more; those are marked "confirmed by substring check". Anything the model may have paraphrased instead of quoting is flagged.

---

## 1. Recent search and full-archive search (pay-per-use)

**Source:** https://docs.x.com/x-api/posts/search/introduction, https://docs.x.com/x-api/posts/search-recent-posts, https://docs.x.com/x-api/fundamentals/rate-limits

| | Recent search | Full-archive search |
|---|---|---|
| Endpoint | `GET /2/tweets/search/recent` | `GET /2/tweets/search/all` |
| Window | "Search Posts from the **last 7 days**. Available to all developers." | "Search the **complete Post archive** dating back to March 2006." "Available to pay-per-use and Enterprise customers" |
| Max results/request | "Up to 100 Posts per request" | "Up to 500 Posts per request" |
| Query length | Introduction page: "512-character query length (4,096 for Enterprise)". **Conflicts** with the recent-search endpoint page's own parameter spec: "minLength: 1, maxLength: 4096" (no tier split shown there). Both quotes are from docs.x.com but disagree — **UNVERIFIED which is current**, worth a live check (send a >512-char query on pay-per-use and see if it 400s). | Introduction page: "1,024-character query length (4,096 for Enterprise)". Same caveat as above. |
| Pagination | `next_token` / `pagination_token`, base32hex-encoded. "At most one of `start_time`, `since_id`… At most one of `end_time`, `until_id`… At most one of `pagination_token`, `next_token`." | Same pagination mechanism (not separately re-confirmed for `/all`). |
| Rate limits | "GET /2/tweets/search/recent: 450/15min (Per App), 300/15min (Per User)" (RATE page) | "GET /2/tweets/search/all: 1/sec, 300/15min (Per App), 1/sec (Per User)" (RATE page) |
| `max_results` param | On the recent-search endpoint spec: "minimum: 10, maximum: 100, format: int32, default: 10" | Not re-fetched separately; introduction page's "up to 500" is the only figure for `/all`. |

**Open discrepancy to flag:** the query-length limit is inconsistent between the search-introduction page's prose (512 vs 1,024, split self-serve/Enterprise) and the recent-search endpoint's own OpenAPI-style parameter block (flat 4,096, no split). Don't build a client-side length guard on either number without a live test.

---

## 2. Query operators and sort order

**Source:** https://docs.x.com/x-api/posts/search/integrate/build-a-query, https://docs.x.com/x-api/posts/search/integrate/operators (confirmed by targeted substring checks)

Operators that **do exist** in the X API v2 query language (as documented on docs.x.com, not the website-only advanced search):

- `from:` — "Matches Posts from a specific user"
- `to:` — "Matches Posts in reply to a specific user"
- `conversation_id:` — "Matches Posts in a conversation thread"
- `is:reply` — "Matches replies"
- `is:retweet` — "Matches Retweets"
- `is:quote` — "Matches Quote Tweets"
- `is:verified` — "Matches Posts from verified authors"
- `-is:nullcast` — excludes promotional/dark posts (must be negated form)
- `has:links` — "Matches Posts with links"
- `has:media` — "Matches Posts with media (photo, GIF, video)"
- `has:mentions` — "Matches Posts with mentions"
- `has:hashtags` — "Matches Posts with hashtags"
- `url:` — tokenized match on URL
- `lang:` — "Matches Posts classified as a specific language" (60+ BCP-47 codes), conjunction-required
- `#hashtag`, `place_country:`, `context:` also appear as examples on the build-a-query page.
- **Engagement/minimum operators exist, but under different names than the website:** `min_likes:`, `min_reposts:`, `min_replies:` are valid API v2 standalone operators — "Each operator takes a non-negative integer value and is available with both recent search and full-archive search." The docs explicitly warn: "The equivalent operators on X web search are named `min_faves:` and `min_retweets:`. Those names are **not** valid in the X API and will be rejected with a 400 error." So there **is** a min-engagement filter in the API, it's just spelled `min_likes` / `min_reposts` / `min_replies`, not `min_faves` / `min_retweets` as on the website.
- `sample:` — appeared in one earlier fetch as a "not found in this doc" note; not independently confirmed either way. Treat as **UNVERIFIED**.

**Confirmed absent by direct substring check** on the operators page: `-filter:replies` and `filter:replies` do **not** appear anywhere on that page. So the website-only `-filter:replies` shortcut has no documented API equivalent; `-is:reply` is presumably the API way to do the same thing (not itself substring-checked, but listed as the positive form `is:reply` above, and `-` negation is documented as a general mechanism on the build-a-query page).

No question-mark (`?`) operator was found documented on either page fetched. **UNVERIFIED / likely doesn't exist as a distinct operator** in the v2 query language — the website's "?" filter for questions isn't shown as an API operator. This is a plain-English no, not a confirmed no from an exhaustive read; worth one more direct check of the full operators page if it matters.

**Sort order:** `sort_order` is a real, documented parameter on `GET /2/tweets/search/recent` (and presumably `/all`, not separately re-checked): an enum with exactly two values, `recency` and `relevancy`. No further definition of what "relevancy" ranks by was returned by the fetch — worth a follow-up read of the endpoint page's full description if the ranking logic matters.

**Not found documented anywhere fetched:** a consolidated single table of all operators with both a Standalone/Conjunction-required column and a tier-availability (self-serve vs Enterprise) column. Availability differences are described in prose, not a machine-readable table.

---

## 3. Pricing: how search is billed, and whether fields/expansions cost extra

**Source:** https://docs.x.com/x-api/getting-started/pricing

- Billing is **per resource fetched** for reads, not per request: "All prices are per resource fetched (reads) or per request (writes/actions)." A read charge attaches to each Post/User/etc. object returned, not to the HTTP call.
- "Posts: Read | $0.005 per resource" is the standard post-read price. The pricing page's table does **not name `tweets/search/recent` or `tweets/search/all` specifically** — search isn't broken out as its own line item, so its billing is inferred to fall under the generic "Posts: Read $0.005" category rather than stated explicitly. **This matches `research/layer-2-x-data-tiers.md`'s own note that this is "assumed, UNVERIFIED."** Treat search-post pricing as *probably* $0.005/post, not confirmed by a line naming search.
- "Owned Reads are requests made by your own developer app for your own data (posts, bookmarks, followers, likes, lists, and more)... priced at $0.001 per resource." The qualifying endpoint list given (12 endpoints) was: `GET /2/users/{id}/tweets`, `/mentions`, `/liked_tweets`, `/bookmarks`, `/followers`, `/following`, `/blocking`, `/muting`, `/owned_lists`, `/followed_lists`, `/list_memberships`, `/pinned_lists`. **Search endpoints are not on this list**, so search results are never owned reads even when searching for your own posts — they'd price as standard $0.005 reads.
- Fields/expansions: **not addressed anywhere found.** The closest statement was "Charged per resource returned in the response," which implies you pay once per object regardless of how many fields you asked for on that object, but no page explicitly says "`tweet.fields`, `user.fields` and `expansions` are free." This is an inference from silence, not a quote — mark **UNVERIFIED**, matches `reference/x-api.md`'s own "Whether `expansions` are billed as extra user or post reads. The client doesn't use them" (not verified there either).
- Rate categories quoted: "$0.005 per resource" covers Posts: Read and List: Read. "$0.010 per resource" covers User: Read and DM Event: Read (and, per `reference/x-api.md` P3/P4 and the layer-2 doc, Following/Followers: Read when not an owned read). "$0.001 per resource" covers Owned Reads and, per one fetch, Likes.
- Cap: "Pay-per-usage plans are capped at 3 million Post reads per monthly billing cycle."
- Dedup: "All resources are deduplicated within a 24-hour UTC day window. If you request and are charged for a resource (such as a Post), requesting the same resource again within that window will not incur an additional charge." (This is X's own "soft guarantee" language per the layer-2 doc; the word "soft guarantee" itself wasn't re-confirmed verbatim in this session's pricing fetch, only "deduplicated within a 24-hour UTC day window" was.)

---

## 4. Indexing delay (how fast a new post becomes searchable)

**Not found on any current docs.x.com page fetched.** No page among search/introduction, build-a-query, or operators mentions latency or indexing delay.

The only source found is X's own engineering blog (not docs.x.com/developer.x.com, so flagged as a **(copy)/secondary source**, and it's from 2020, pre-dating the current v2 pay-per-use API):
- https://blog.x.com/engineering/en_us/topics/infrastructure/2020/reducing-search-indexing-latency-to-one-second — "Tweets are now available for searching within one second of creation." Originally the delay was ~15 seconds; the 2020 post describes cutting it to ~1 second.

**This is UNVERIFIED as a current guarantee.** It is six years old, describes internal search infrastructure (not necessarily the API surface unchanged since), and no current API doc restates or commits to any indexing-delay SLA. Don't build product timing assumptions ("early replies matter, so check within N seconds") on this number without a live test against the current API.

---

## 5. Home timeline (reverse-chronological) and List endpoints

**Source:** https://docs.x.com/x-api/posts/timelines/quickstart/reverse-chron-quickstart, https://docs.x.com/x-api/getting-started/pricing, https://docs.x.com/x-api/fundamentals/rate-limits

- Endpoint: `GET /2/users/:id/timelines/reverse_chronological`.
- What it returns per the quickstart: "the most recent Tweets and Retweets posted by you and users you follow" — i.e., the signed-in user's home timeline, not search results. A community search result (not docs.x.com, so secondary/UNVERIFIED) adds it can return "every Tweet created on a timeline over the last 7 days as well as the most recent 800 regardless of creation date" — **not confirmed on an official page in this session**, flag as UNVERIFIED.
- Auth: "requires user authentication" — user access tokens (OAuth 2.0 user context per the cURL example shown: `Authorization: Bearer $USER_ACCESS_TOKEN`). No specific OAuth scopes were listed on the quickstart page fetched.
- Rate limit: "GET /2/users/:id/timelines/reverse_chronological: 180/15min (Per User)" (RATE page).
- **Pricing tier — this is the important finding: home timeline is NOT an Owned Read.** The Owned Reads qualifying-endpoint list quoted in §3 above is exhaustive as fetched (12 endpoints) and does **not include** `/2/users/{id}/timelines/reverse_chronological`. Since it returns Posts and isn't on the owned-reads list, it should price as a standard "Posts: Read, $0.005 per resource" — i.e., a standard post read, not the $0.001 owned-read rate — even though it's the signed-in user's own timeline. **This is an inference from the endpoint's absence from the quoted owned-reads list, not a line item that names the timeline endpoint and its price directly** — worth a direct live check (call it once, watch the usage dashboard) before relying on it, since being "your own data" in a colloquial sense (your timeline) clearly isn't the same test X uses ("your own data" = posts/likes/follows *you created or performed*, not content you're merely viewing).
- **List endpoints:** `GET /2/lists/:id/tweets` (a list's posts) was not in the owned-reads list either. The pricing page's category table has a line "List: Read | $0.005 per resource" (§3) — but that's ambiguous between "reading a List's own metadata" (there's a separate owned-reads line for lists you own/follow/belong to, at $0.001) and "reading a List's posts" (`/2/lists/:id/tweets`, presumably the $0.005 category since it returns Posts, not List objects). Rate limit for list posts: "GET /2/lists/:id/tweets: 900/15min (Per App), 900/15min (Per User))." **Net: a list's posts are very likely priced at $0.005/post (standard Posts: Read), not $0.001, regardless of whether you own the list — not stated explicitly as such, inferred from category structure.**

---

## 6. Fields useful for filtering spam / ranking conversations, and their cost

**Source:** https://docs.x.com/x-api/fundamentals/data-dictionary, https://docs.x.com/x-api/fundamentals/metrics

- **Post `public_metrics`:** "retweet_count, reply_count, like_count, quote_count, impression_count, bookmark_count." Available with basic Bearer Token (app-only) auth — no user context needed, no extra documented cost beyond the per-post read charge.
- **Post `reply_settings`:** "Shows who can reply to a given Tweet. Options are 'everyone', 'mentioned_users', and 'followers'." Useful to know if a conversation is even open to your reply.
- **Post `context_annotations`:** "Contains context annotations for the Tweet" (X's own entity/topic labels) — per `reference/x-api.md` P12, this is a topic-mix proxy, not the algorithm's real classifier.
- **Post `conversation_id`:** "The Tweet ID of the original Tweet of the conversation (which includes direct replies, replies of replies)" — usable to pull a whole thread or count real replies in it.
- **User `verified` / `verified_type`:** "Indicates if this user is a verified Twitter User" / "A string representing the type of verification a user has. Example: 'blue', 'business', 'government'."
- **User `public_metrics`:** `followers_count`, `following_count`, `tweet_count`, `listed_count` — useful as an author-quality/spam-ish signal (e.g., brand-new account with 0 followers replying).
- **User `protected`:** "Indicates if this user has chosen to protect their Tweets."
- **Cost:** no page found states a separate price for requesting these fields via `tweet.fields`/`user.fields`/`expansions`. As in §3, the working assumption (unconfirmed) is that you pay only for the resource (each Post or User object) once, regardless of how many fields you ask for on it — but no page says this in so many words. Author `public_metrics` via an `author_id` expansion would, if it counts as pulling a User object, cost the $0.010 user-read rate per unique author (this is `reference/x-api.md`'s own open question at line 45, not settled here either).
- **Non-public/organic metrics** (`non_public_metrics`, `organic_metrics`) need user-context auth and only exist for your own posts in the last 30 days — not usable for other people's posts, so not a spam/ranking signal for Discovery.

---

## 7. Developer Policy / automation rules relevant to a human-in-the-loop reply-target tool

**Source:** https://docs.x.com/developer-terms/policy, https://docs.x.com/developer-terms/restricted-use-cases

Relevant clauses found:
- "Services that perform write actions, including posting Posts, following accounts, or sending Direct Messages, must follow the Automation Rules."
- "Always get explicit consent before sending people automated replies or Direct Messages" and "Immediately respect requests to opt-out of being contacted by you" — these govern *sending* automated replies, i.e., writes. A tool that only *surfaces* candidate posts for a human to read and manually reply to is not itself performing a write action, so these clauses don't directly restrict it — but nothing found affirmatively blesses "reply-suggestion" tools either.
- "The use of the X API and developer products to create spam, or engage in any form of platform manipulation, is prohibited." "Never perform bulk, aggressive, or spammy actions, including bulk following."
- "You must clearly identify your service so that people can understand its source and purpose."
- "You are not permitted to register multiple applications for a single use case, or substantially similar or overlapping use cases" (Restricted Use Cases / Policy — relevant to the product's own app registration, not to this feature specifically).
- **Nothing found, on either page fetched, that names "suggesting replies," "surfacing engagement targets," "reply-finding tools," or an equivalent phrase.** The Policy and Restricted Uses pages address *automated* engagement (bulk actions, unsolicited automated DMs/replies) and platform manipulation broadly, not the narrower case here: a desktop tool that reads public posts via the API and shows a human a list of "conversations you might want to reply to," where the human decides and types the reply by hand (which is exactly this project's existing `AGENTS.md` model — "the operator writes it in their own words"). **This is a gap, not a green light** — the absence of a named prohibition isn't the same as a confirmed permission. **Mark UNVERIFIED / open question**, and note it's consistent with how `thread-engine`'s own `x_read.py`/Grok pattern already operates (surface candidates, human decides, human types).
- No clause found (on the two pages fetched) that treats "showing a human a ranked list of posts to consider replying to" as itself platform manipulation, as long as no automated write follows. This mirrors `research/layer-2-x-data-tiers.md`'s general finding that X's rules are largely silent on model-assisted *reading/surfacing*, and much more explicit about writes.

---

## Open questions a live test (or a closer doc read) should settle

1. **Query length limit contradiction:** is the real cap 512/1,024 (self-serve/Enterprise split, per the search-introduction prose) or a flat 4,096 (per the recent-search endpoint's own parameter spec)? Send an ~800-character query on pay-per-use recent search and see if it 400s.
2. **Does search billing actually fall under "Posts: Read $0.005"?** No pricing-page line names `tweets/search/recent` or `/all` directly. Run one search call, check the usage/cost dashboard for which line item it appears under.
3. **Is home timeline (`reverse_chronological`) really billed at $0.005 (standard) and not $0.001 (owned)?** It's absent from the quoted 12-endpoint owned-reads list, but that's an inference, not a direct statement pricing the endpoint. Confirm on the billing dashboard after one call.
4. **List posts (`GET /2/lists/:id/tweets`) pricing**: same as above — confirm whether it bills as "List: Read $0.005" or is treated as a plain Posts: Read.
5. **Do `tweet.fields`/`user.fields`/`expansions` (e.g., `author_id` → author `public_metrics`) add any charge beyond the base resource price?** No page states this either way. Test: call a search with and without `expansions=author_id&user.fields=public_metrics` for the same 10 posts, compare dashboard cost.
6. **Current indexing delay**: the only number (~1 second) is a 2020 engineering blog post, not a current API doc commitment. Post something and immediately search for it via recent search to see the real observed delay today.
7. **`sort_order=relevancy` semantics**: the docs give the enum but not (in what was fetched) a description of what "relevancy" actually ranks by. Worth reading the endpoint's full parameter description or testing both values on the same query.
8. **Does a `?` (question-mark) operator or a `sample:` operator exist in the v2 query language?** Not found in what was fetched; not conclusively ruled out either — a direct search or a fuller read of the operators page would settle it.
9. **Whether `min_likes:`/`min_reposts:`/`min_replies:` are available on both access tiers or gated to pay-per-use/Enterprise** — the docs say they work on "both recent search and full-archive search" but don't state a tier restriction; test on the actual pay-per-use key.
10. **The reply-suggestion/reply-target-surfacing gap in the Developer Policy**: no clause found either prohibiting or explicitly permitting a human-in-the-loop "conversations worth replying to" feature. Worth a direct question to X's developer support/forum before shipping this as a named product feature, since "your use case description is binding on you" (per the layer-2 doc, DP) — i.e., whatever the product's registered use-case description says about this feature is what actually governs it, more than any generic policy clause.

---

**Note on tool reliability in this session:** every quote above came through WebFetch's summarizing pass, not raw HTML. Two direct substring re-checks (min_likes/min_faves, -filter:replies) confirmed the summaries weren't inventing content, but not every claim above got that same double-check — treat quotes without an explicit "(confirmed by substring check)" note as first-pass summaries, correct in substance but not hand-verified word-for-word against the raw page.
