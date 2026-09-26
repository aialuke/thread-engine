# Layer 2 research: X data tiers

**For:** the build-strategy session, which grills the operator from this document and logs the decisions. This document decides nothing.
**Scope:** how the product gets each user's X data, in tiers (D45, D46). The starting sketch is `reviews/ui-direction.md:120`. Out of scope: AI engines (layer 3), stack, and the product's own price.
**Researched 26 Sep 2026.** Repo read: `reviews/ui-direction.md` (D1–D87, build notes), `research/layer-1-switches-profiles.md`, `research/x-rules.md`, `reference/x-api.md`, `reference/x-algorithm.md`, `AGENTS.md`, `scripts/{x_api,x_read,grok_read,snapshot,loop,post_thread}.py`, `ledger/runs.log`. No private folder was opened (`loop/followers/`, `ledger/raw/api/`, `loop/inbox/`). No X or xAI API call, no Keychain read, nothing written to X.
**Sources.** Official pages fetched today. How each was reached:
- **Live:** docs.x.com (pricing, rate limits, OAuth 2.0, metrics, post analytics, search, compliance, the Activity API, the `/2/users/me` spec, Developer Agreement, Developer Policy, Restricted Uses, Display Requirements), developer.x.com, x.com/en/tos, x.com/en/privacy and docs.x.ai. The clauses this document leans on were checked line by line in this session.
- **Browser:** x.ai/legal/terms-of-service-enterprise ("Last Updated: August 14, 2026"). It blocks fetching, so it was read in the browser.
- **Copies:** help.x.com pages blocked fetching and came through a reader proxy, marked "(copy)". Other pages that blocked fetching are marked "(copy)" too.
- **Not X's own pages:** two @premium posts were read through X's public embed endpoint (not the X API). devcommunity.x.com threads are forum posts.

**Update 26 Sep (D88): Grok is dropped from the product.** The tiers are CSV only and CSV + X API. Discovery comes only from X API recent search. The Grok rows and options below are kept as the research record: L2-C6 is decided (X API search, with code-built queries from any remaining engine's phrases), L2-C7 loses option (b), and conflict K11 no longer applies. Evidence: `research/discovery-x-api-search-proposal.md`.

**Update 26 Sep (D89–D104): layer 2 is decided.** Both tiers at launch, with Discovery if its stages pass (D89); each user brings their own X keys (D90); Premium is required (D95). Each choice in §5 and each conflict in §3 says which decision settled it.

Anything not confirmed is marked **UNVERIFIED**. Codex gave a blind second read (§4); its accepted points are folded in.

**Short names for sources.**

| Name | URL |
|---|---|
| PRICING | https://docs.x.com/x-api/getting-started/pricing |
| RATE | https://docs.x.com/x-api/fundamentals/rate-limits |
| DA (Developer Agreement) | https://docs.x.com/developer-terms/agreement |
| DP (Developer Policy) | https://docs.x.com/developer-terms/policy |
| RU (Restricted Uses) | https://docs.x.com/developer-terms/restricted-use-cases |
| DR (Display Requirements) | https://docs.x.com/developer-terms/display-requirements |
| ACTIVITY (X's event stream) | https://docs.x.com/x-api/activity/introduction |
| XAI-ENT (xAI's enterprise terms) | https://x.ai/legal/terms-of-service-enterprise |
| XSEARCH (Grok's X search tool) | https://docs.x.ai/developers/tools/x-search |

---

## 1. One-page summary

- **Three tiers, as sketched.**
  - **Basic** is the analytics CSV the user downloads from X by hand.
  - **Full** is the read-only X API.
  - **Discovery** reads other people's posts, through Grok or X API search. *(D88, 26 Sep: Grok dropped; Discovery is X API recent search only.)*
  - Each tier can do less than the sketch assumed, for the reasons below.
- **Basic probably needs X Premium.** X moved analytics behind Premium in 2024 (@premium, https://x.com/premium/status/1801292231774765140). No current help page says so, and none describes the export: no menu path, no column list, no date limit. The only column list is the operator's own 24 Sep export (`reference/x-api.md:33`).
- **The app can't fetch the CSV itself.** No API or link gives it, and scripting x.com breaks X's terms (x.com/en/tos). The user downloads it by hand each time.
- **What the CSV adds, and what it lacks.**
  - It has per-post **new follows** and **shares**, which the pay-per-use API can't give (`reference/x-api.md:23, 33`). Profile visits are in both (`reference/x-api.md:19, 35`).
  - It has no mentions, no timing and no follower list, and nothing between downloads.
  - Today's importer only updates posts the API already recorded (`scripts/loop.py:501-506`). A CSV-only user needs a new importer.
- **Bring-your-own X keys (option A) looks barred.** X's Restricted Uses page, read live, says "requiring your end users to register applications for the purpose of using your tool or service could result in enforcement actions against you, your applications, your customers, and/or the end users" (RU). D54's own example of a guided step, "getting X API keys from X's developer portal", is this pattern.
- **One product app with "Sign in with X" (option B) avoids that warning, but costs 5 to 10 times more per item.**
  - The $0.001 "owned read" price applies only when the signed-in user "is the owner of the developer app" (PRICING). Product users aren't.
  - They pay full price: $0.005 a post, $0.010 a follower, $0.010 a user lookup. The vendor pays X.
  - One app is capped at 3 million post reads a month on pay-per-use.
  - X still has to accept the product's use case; one app is necessary, not sufficient.
- **Cost is driven by follower count, not posting.**
  - Today's daily run reads the whole follower list every day (`scripts/snapshot.py:191`). At full price that's **$0.30 per follower per month**, so $1,500 a month at 5,000 followers.
  - The same heavy user costs about **$28 a month** if followers are counted rather than listed (estimates, §2.1).
  - Follow events from X's Activity API ($0.010 per follow, PRICING) could replace the list, but they need a server to receive them (§2.1).
- **X can require Enterprise.**
  - Once a product's users "greatly exceed the normal levels" (DP, "X Login").
  - Beyond "a limited number of end-users" (DA III.L).
  - For any government end users (DA XIV.C).
  - X publishes no number and no Enterprise price.
- **Discovery needs an X API check somewhere.** Grok has invented posts (`scripts/x_read.py:9-11`), so `x_read.py` checks each one by id and returns nothing if the check can't run (`scripts/x_read.py:9-14`). Without the user's Full connection, the check has to run on the vendor's app, at the vendor's cost. X API recent search (7 days) needs no check. *(D88, 26 Sep: Grok dropped; Discovery is X API recent search only.)*
- **Terms: four open legal questions.**
  1. Sending post text to a cloud model (D78, D81): no X term addresses it. The closest is the ban on providing Licensed Material "to any third party" (DA III.A(d)).
  2. The vendor's aggregate learning data (D76): aggregate analysis without identifiers is allowed (RU). A clause against "calculating aggregate X Post metrics, such as … the number of account engagements" for commercial benchmarking (DP) may or may not reach it. That's a legal interpretation.
  3. Stored X content must be kept current. It must be deleted or changed promptly, and within 24 hours of a request, when deleted, protected or suspended on X (DP, DA IV.B).
  4. Other people's posts shown in the app must follow X's display rules (DR).
- **Conflicts:** 13 listed in §3, not worked around. **Choices:** L2-C1 to L2-C13 in §5.

---

## 2. Detail

### 2.1 The tiers

#### What each tier reads

| | **Basic (CSV)** | **Full (X API, read-only)** | **Discovery (other people's posts)** |
|---|---|---|---|
| **Source** | X analytics content export, downloaded by the user (`reference/x-api.md:33`) | `GET /2/users/{id}/tweets`, `/mentions`, `/followers`, `/2/users/me`, `/2/users/by/username`, `/2/tweets` (`scripts/x_api.py:205-278`). Possibly the Activity API's events (ACTIVITY) | Grok's X search (`x_keyword_search`, `x_semantic_search`, `x_user_search`, `x_thread_fetch`; https://docs.x.ai/developers/tools/tool-usage-details), or X API recent search (https://docs.x.com/x-api/posts/search/introduction) |
| **Reads** | One row per post and reply: Post id, Date, Post text, Post Link, Impressions, Likes, Engagements, Bookmarks, Shares, New follows, Replies, Reposts, Profile visits, Detail Expands, URL Clicks, Hashtag Clicks, Permalink Clicks. All organic (`reference/x-api.md:33-35`) | Own posts, replies and quotes with organic metrics (impressions, likes, replies, reposts, profile clicks, link clicks) for 30 days (`reference/x-api.md:18-19`); full text via `note_tweet` (`reference/x-api.md:27`); mentions; the follower list with verified flags (`reference/x-api.md:26`); any account by handle (`reference/x-api.md:28`); `subscription_type` and `verified_followers_count` on `/2/users/me` (spec only, https://docs.x.com/x-api/users/get-my-user) | Other people's posts. Recent search covers the last 7 days, 100 per request. Full-archive search is on pay-per-use too |
| **Can't read** | Mentions, other people's replies, followers, timing (first like), anything newer than the last download. Per-day totals: UNVERIFIED | Per-post follows, unfollows and shares: `/2/tweets/analytics` returns 403 on pay-per-use (`reference/x-api.md:23`). Organic numbers after 30 days (`reference/x-api.md:18`). The exact time of the first like (`reference/x-api.md:46`). Qualified home-timeline impressions for the rewards program (typed from X's screen, `.claude/skills/results/SKILL.md:16`) | Grok's answers can name posts that don't exist (`scripts/x_read.py:9-11`). The repo asks Grok for structured post objects and replaces their facts with X's (`scripts/x_read.py:28-35, 68-86`) |
| **Freshness** | Whenever the user downloads. The numbers seem to add up per post to the download date (`scripts/loop.py:488-489`, operator's observation; UNVERIFIED on any official page) | Live, when the app is running (§2.3, L2-C12) | Live |
| **Needs** | Probably X Premium (below) | An X connection (option A or B, §2.2) | For Grok: an xAI account or Grok subscription (layer 3). For the check, or for X API search: an X API app, the user's or the vendor's |

#### What the user does to set each tier up (D54)

- **Basic.**
  1. On a computer, open X → Premium → Analytics → Content → Export and pick the range (path verified by the operator on 24 Sep, `reference/x-api.md:33`; no official page describes it).
  2. Drop the file onto the app, or pick it with a file dialog. A file drop zone, not a paste box.
  3. Repeat weekly; the app reminds. Mobile export: UNVERIFIED.
- **Full, option B (one product app).**
  1. Press "Connect X". The browser opens X's sign-in page, asking for the scopes `tweet.read`, `users.read`, `follows.read` and `offline.access`.
  2. Press Authorise, and return to the app. No paste box.
  - The code must be exchanged within 30 seconds. Access tokens last 2 hours; `offline.access` gives a refresh token (https://docs.x.com/fundamentals/authentication/oauth-2-0/authorization-code).
  - UNVERIFIED: how long refresh tokens last, and whether a localhost or custom-scheme callback is accepted.
- **Full, option A (the user's own developer app).**
  1. Sign up at the developer console and write a use-case description, which "is binding on you" (DP).
  2. Create a project and app, and set Read permission.
  3. Buy credits with a card and set a spending cap (`reference/x-api.md:54`).
  4. Generate four keys and paste them into four boxes.
  - This is how the operator's own factory is set up (`scripts/x_api.py:43-45`). See §2.2 for why it's risky for a product.
- **Discovery.** Via Grok: an xAI API key in a paste box, or the Grok CLI signed in (layer 3). Via X API search: nothing extra on option B. *(D88, 26 Sep: Grok dropped; Discovery is X API recent search only.)*

#### Does the CSV export need Premium?

- For: "Upgrade to Premium to get daily insights into how your posts are performing" (@premium, 13 Jun 2024, https://x.com/premium/status/1801292231774765140, text via X's embed endpoint). The path runs through "Premium" (`reference/x-api.md:33`).
- Against, or silent:
  - The current X Premium help page doesn't mention analytics (https://help.x.com/en/using-x/x-premium, copy).
  - The old analytics help page is gone (404, copy).
  - business.x.com still calls analytics "a free service available to all X users" (https://business.x.com/en/help/campaign-measurement-and-analytics/tweet-activity-dashboard, live). That page describes the old dashboard and is stale.
- **Result: probably needs Premium. UNVERIFIED on a current official page.**
- Also UNVERIFIED: the export's date limit (the old dashboard's was "up to 30 days … 3,000 post cap … UTC", same business.x.com page) and a mobile export.
- The operator could settle it in the X UI: ask a non-Premium account whether it sees the export, and find the maximum range. Not done here.
- **Can the app get the file itself?** No.
  - No stable link or scheduled report was found.
  - The API equivalent, `/2/tweets/analytics`, is Enterprise-only in practice (`reference/x-api.md:23`).
  - "Crawling or scraping the Services in any form, for any purpose without our prior written consent is expressly prohibited" (x.com/en/tos, live).
  - Whether a user may hand their own file to a commercial app, and whether X's Developer Agreement covers data that didn't come through the API: no official answer. X Content includes content supplied through X's other authorised means as well as the API (DA I.12; Codex). A forum question on exactly this went unanswered (https://devcommunity.x.com/t/245687, not official).

#### Prices today (live, 26 Sep)

*D88 (26 Sep): Grok rows here are the research record only; the product doesn't use Grok.*

| Read | Price per item | Source |
|---|---|---|
| Own posts, mentions, followers, following, when the signed-in user **owns the developer app** | $0.001 | PRICING, "Owned Reads" |
| Posts (timeline, ID lookup, search, anyone's timeline when not owned) | $0.005 | PRICING |
| Users (`/users/me`, by handle) | $0.010 | PRICING |
| Following/Followers, not owned | $0.010 | PRICING |
| Likes | $0.001 | PRICING. Whether `liking_users` bills as "Like: Read" or as users: UNVERIFIED |
| Search results | No line of its own; assumed $0.005 per post returned. UNVERIFIED | PRICING |
| Activity API events | `follow.follow` $0.010, `follow.unfollow` $0.010, `post.create` $0.005 per event; like events not priced on the page | PRICING, "Webhook events" |
| Same item again the same UTC day | free: "deduplicated within a 24-hour UTC day window". X calls this "a **soft guarantee**" | PRICING |
| Cap | "3 million Post reads per monthly billing cycle" on pay-per-use | PRICING |
| Grok X search | "$5 per 1k posts fetched and $10 per 1k user profiles fetched, in addition to token costs"; the counts "are not de-duplicated; a post returned by two searches counts twice" (https://docs.x.ai/developers/tools/x-search.md, line 359) | XSEARCH |
| Grok tokens (per 1M, input / output, prompts under 200k tokens) | grok-4.7 $2.00 / $6.00; grok-4.3 $1.25 / $2.50. Long prompts cost more | https://docs.x.ai/developers/pricing |

- Basic and Pro subscriptions are closing into pay-per-use: Basic "after June 1, 2026" (https://x.com/XDevelopers/status/2057572111020134462, copy), and Pro "after September 1, 2026" (https://devcommunity.x.com/t/important-update-legacy-x-api-pro-plans-are-moving-to-pay-per-use-ppu/273255, copy).
- The Enterprise price is not published. Blogs quote $42,000+ a month (UNVERIFIED).

#### Cost per user per month at the loop's read pattern

*D88 (26 Sep): Grok rows here are the research record only; the product doesn't use Grok.*

**The pattern today.**
- Each own post, reply and thread card is read twice: once 36–60 hours after posting, once at 26–29 days (`scripts/snapshot.py:33-34, 181-194`).
- Each mention is read once, after the last one seen (`scripts/snapshot.py:187-194`).
- **The whole follower list is read every day** (`scripts/snapshot.py:191`).
- On 25 Sep that was 38 followers, 47 posts and 5 mentions: 90 items, an **estimated** $0.09 (`ledger/runs.log:8`). Earlier days were 36–47 items (`ledger/runs.log:4-7`).
- These are the client's own estimates: returned items times a fixed price (`scripts/x_api.py:178-181`). They aren't X's bill, and don't allow for same-day repeats being free (three runs on 24 Sep each logged a charge).

**Reads the app adds.**
- **Waiting for you on open (D12).** New mentions, plus the user's own replies since the last read, to tell answered from unanswered. With shared cursors, each item is charged about once more. The build note guesses "about a cent a read" (`reviews/ui-direction.md:133`).
- **Finding the post (W4).** An own-timeline read from approval to now, about 2 items per original.
- **First-hour polling (W7).** Poll the user's own timeline from the posting time, which keeps the owned price. ID lookup is never an owned read (`reference/x-api.md:15`).
  - Charges the root and its cards once, if the hour stays in one UTC day: about 3 items per original.
  - Under 900 requests per 15 minutes per user (RATE).
  - For a Brisbane user the UTC day turns at 10:00 local. A post near then pays twice.
- **Handle check** before a tag: $0.010 each.
- **Profile read** (Premium, follower and verified-follower counts): $0.010 a read.
- **Following list** for Builders (D28 needs both directions): same price as followers.
- **Voice import (D78)**, once at first run: about 200 posts, $0.20 owned or $1.00 full.

**Overlap.** W4, W7 and Waiting for you can read the same posts on the same UTC day. The totals below count them separately, so they're an upper bound on those lines. Deduplication is only "a soft guarantee" (PRICING).

**Two example users.** These profiles are assumptions for illustration. Only the prices and the read pattern are sourced.

| | Light | Heavy |
|---|---|---|
| Originals a month (P) | 20 | 90 |
| Own items a month (T: originals, cards, replies) | 100 | 1,200 |
| Mentions a month (M) | 60 | 1,500 |
| Followers (F) | 300 | 5,000 |
| Accounts followed (G) | 200 | 1,000 |
| Handle checks | 4 | 30 |

**Monthly cost, estimated.** Items: 2T (snapshot) + M + followers + T (Waiting for you) + 2P (W4) + 3P (W7), plus user reads.

| | Light, owned price (option A) | Light, full price (option B) | Heavy, owned price (A) | Heavy, full price (B) |
|---|---|---|---|---|
| Snapshot own items (2T) | $0.20 | $1.00 | $2.40 | $12.00 |
| Mentions (M) | $0.06 | $0.30 | $1.50 | $7.50 |
| **Follower list daily (30F)** | **$9.00** | **$90.00** | **$150.00** | **$1,500.00** |
| Waiting for you (T) | $0.10 | $0.50 | $1.20 | $6.00 |
| W4 + W7 (5P) | $0.10 | $0.50 | $0.45 | $2.25 |
| Profile weekly + handle checks | $0.08 | $0.08 | $0.34 | $0.34 |
| **Total, as today** | **≈ $9.54** | **≈ $92.38** | **≈ $155.89** | **≈ $1,528.09** |
| Total, count daily (`/users/me`, $0.30) + follower list weekly (4F) | ≈ $2.00 | ≈ $14.64 | ≈ $26.15 | ≈ $228.35 |
| Total, count daily only, no list | ≈ $0.80 | ≈ $2.64 | ≈ $6.15 | ≈ $28.35 |
| Add: following list weekly for Builders (4G) | + $0.80 | + $8.00 | + $4.00 | + $40.00 |

**How it scales.**
- **Followers grow the cost fastest.** Every follower costs $0.03 a month at owned price and $0.30 at full price, as long as the list is read daily.
- **Replies are next.** Every own reply is read twice, plus once for Waiting for you: $0.003 or $0.015 a reply.
- **Mentions** cost once each. A reply-heavy account pays mostly for its own replies and its mentions.
- **Posting little doesn't help** a big account: a quiet account with 5,000 followers still pays $1,500 a month at full price, as today.
- **The 3M cap** (option B, one app for everyone) counts post reads. Follower reads appear to be separate (PRICING, by its wording; UNVERIFIED). The heavy user reads about 5,550 posts a month (2T + M + T + 5P), so about 540 heavy users fill the cap.

**Follow events instead of lists** (Codex, checked live).
- X's Activity API sends follow, unfollow, post and mention events, among others, by webhook or persistent HTTP stream (ACTIVITY).
- Follow and unfollow events cost $0.010 each (PRICING). A heavy user gaining 300 followers a month would cost about $3, against $1,500 for daily lists. The 300 is an illustrative assumption.
- A self-serve app can hold at most 1,500 subscriptions (ACTIVITY, "Subscription limits"). How many subscriptions one user needs: UNVERIFIED.
- Events arrive at a URL or a held-open stream, which points to a vendor server. The product so far has no server for reads (§2.2).
- Also UNVERIFIED: replay after downtime, and whether like events exist and are billed.

**Discovery costs, per search of 10 posts.**
- **Grok:**
  - 10 posts: $0.05, plus tokens. "Fetched" can include parent and quoted posts, so the count can exceed what's shown.
  - The X API check (`x_read.py`): $0.05 for the posts and up to $0.10 for 10 authors (`scripts/x_api.py:256-267`).
  - About **$0.20 before tokens**.
- **X API recent search:** 10 posts at $0.005 is $0.05. With 10 authors expanded at $0.010 it's **$0.15**, if expansions bill as user reads (UNVERIFIED, `reference/x-api.md:45`).
- **Worth joining**, three searches a day: about $18 a month through Grok, or $13.50 through X API search, both before tokens.

### 2.2 Keys: option A (bring your own) against option B (one product app)

*D88 (26 Sep): Grok rows here are the research record only; the product doesn't use Grok.*

| | **A: each user brings their own X developer keys** | **B: the product is one X app; users sign in with OAuth 2.0 (PKCE)** |
|---|---|---|
| **Setup burden** | High. A developer account, a binding use-case description, a project and app, Read permission, credits with a card, a spending cap, four keys pasted (§2.1). D54's paste boxes can hold it, but it's several screens on X's site. | Low. One button and X's own sign-in page. Native apps are "public clients", with no secret (https://docs.x.com/fundamentals/authentication/oauth-2-0/authorization-code). |
| **Who pays X** | Each user, on their own card. | The vendor, for every user's reads. |
| **Price per item** | Owned price: $0.001 for own posts, mentions, followers and following (PRICING). | Full price: $0.005 a post, $0.010 a follower (PRICING). |
| **X's terms** | **Looks barred.** "requiring your end users to register applications for the purpose of using your tool or service could result in enforcement actions against you, your applications, your customers, and/or the end users of your tool or service" (RU, live). Also: "You may not use, and may not encourage or facilitate others to use, API keys or other access credentials owned by others" (DP, live). The keys would be the user's own, so this clause fits less directly; the RU clause names the pattern. | Avoids the multiple-apps warning. "Providing the same service or application to different end users counts as a single use case" (RU). At most 3 apps (dev, staging, production); no white-label versions without approval (DP; developer.x.com). X still has to accept the use case (DP: "Your use case description is binding on you"). |
| **Enterprise** | Each user's app is small. The risk is enforcement, not an Enterprise requirement. | Required on notice once sign-ins "greatly exceed the normal levels of other developers subscribed to a similar tier" (DP, "X Login"), or beyond "a limited number of end-users" (DA III.L, M). Required for "Government End Users" (DA XIV.C). X can require a tier change "at any time" (DA III.J). No number or price is published. |
| **Rate limits** | Per user token; each user's own app. | Per user token too: timeline 900 per 15 min, mentions 300, followers 300, by-handle 900, `/users/me` 75 (RATE). The 3M monthly post-read cap is shared by all users. |
| **At scale** | Nothing grows at the vendor, but every customer carries enforcement risk, and the RU clause names end users. | Cost grows with every user's follower count (§2.1); the cap and Enterprise follow. The vendor must also meet X's duties for all stored data (§2.5). |
| **Where the data lives** | On the user's machine. | On the user's machine too. A public client can call X directly from the desktop, so reads need no vendor server; only the client id is the vendor's. Whether X expects a vendor backend: UNVERIFIED. |
| **Spending control** | The user's own cap in X's console. | **A client-side meter isn't a hard limit** (Codex, inference). A user's token calls X directly and bills the vendor's app. A hard per-user budget needs the reads to go through a vendor service, which would send users' X data off their machines (D42, D52). X's console limit caps the whole app, not one user. |

- **Grok keys for Discovery**, if each user brings one: xAI says "Do not share keys between teammates" (https://docs.x.ai/developers/faq/security).
- xAI's enterprise terms let a customer build "integrations between the Services and Customer's own products" and make them available to "End Users" (XAI-ENT §1).
- No rule against a user using their own key in a third-party app was found (UNVERIFIED either way).

### 2.3 Every screen and switch that needs X data

*Update 26 Sep (D88): Grok is dropped. The Grok options below are the research record; the product's Discovery column is X API recent search, with no check needed.*

"Not recorded yet" is D42's wording for missing data (`reviews/ui-direction.md:52`). "Full" assumes the app is running when a read is due. What happens when it isn't is L2-C12.

| Screen or switch | Basic (CSV) | Full (X API) | Discovery | Fallback |
|---|---|---|---|---|
| **Daily snapshot**: 36–60 h and 26–29 day reads (`scripts/snapshot.py:33-34`) | No daily read. Each download gives numbers accumulated to that date, including follows and shares. **Needs a new importer**: today's skips posts it hasn't seen (`scripts/loop.py:501-506`), ignores text and dates, and keeps only the latest download (`scripts/loop.py:512`) | As today, at the price in §2.1. The follower list is the cost driver (L2-C2). A missed 36–60 h read can't be taken later, and organic numbers end at 30 days (`reference/x-api.md:18`) | – | Basic: weekly download reminder. Full: the CSV fills in follows and shares (`reference/x-api.md:36`) |
| **Find the post after posting** (W4, D17; `research/layer-1-switches-profiles.md:401`) | Can't. The user pastes the post's link (the sketch, `reviews/ui-direction.md:120`). D17 rejected pasting (`reviews/ui-direction.md:27`): conflict K9 | Own-timeline read, matched to the approved cards. About $0.002–0.010 a post | Grok could search the handle, but the result must be checked on an X API app | Paste box for the link |
| **Shout-out detection** (W6; `layer-1…:403`) | Can't | Own-timeline read: an own reply in the root's conversation **whose text matches the approved shout-out**. Any own reply under the root could be a thread card or an answer to someone | Grok `x_thread_fetch`, checked on an X API app | The Done button (D17) |
| **First-hour card and first like** (W7, D29; `layer-1…:404`) | Can't: the CSV has no timing. The minutes question (D34) and timers still work (conflict K10) | Poll the root's like count every 1–2 minutes for 60 minutes. Record the **first observed** like, with its uncertainty; "unknown" if polling started late or was interrupted, since a like and unlike between polls is missed. `liking_users` gives who, not when; its billing is UNVERIFIED | – | The card shows the minutes question and says to check X for likes |
| **Waiting for you** (W9, D12; `layer-1…:406`) | Can't: no mentions in the CSV | Mentions filtered to real replies to the user's posts. "Answered" needs the id of the reply the user answered, from `referenced_tweets`. Today's snapshot keeps only the user id for the user's own replies (`scripts/snapshot.py:106-107`) | Grok search for replies to the handle, checked on an X API app | "Not recorded yet"; the user checks X's notifications |
| **Worth joining** (W10, D12; `layer-1…:407`) | – | X API recent search (7 days) | Grok search, checked by id on an X API app (`scripts/x_read.py:68-86`) | Nothing, unless the vendor runs the check (L2-C7) |
| **Builders** (W11, D28; `layer-1…:408`) | Can't: no follower or following list | Follower and following lists plus interactions: a big read (§2.1). Weekly would do | – | "Not recorded yet" |
| **Mentions** (reader questions, weekly review Q8) | Can't | `/mentions`, once each | Grok, checked on an X API app | Section left out of the review |
| **Handle check before a tag** (`reference/x-api.md:28`) | Can't | `/2/users/by/username`, $0.010, never an owned read | Grok `x_user_search`, not proof | Guided step: open x.com/<handle> in the browser, then confirm the right account posted recently. A person's check, not a gate |
| **Premium status** (D83) | Asked at first run. A user who can download the export probably has Premium (§2.1) | `subscription_type` on `/2/users/me`: "Basic, Premium, PremiumPlus or None" (API spec; whether pay-per-use apps get it is UNVERIFIED). Codex reports X's Premium help page lists longer posts in the Basic subscription (not re-checked here) | – | Ask; unknown means no Premium (D83) |
| **Daily post count** (D82) | Can't count live. The app counts posts the user marked as posted: a lower bound | Own-timeline read of the last 24 hours, free again the same UTC day | – | Not claimed (D82: "not claimed otherwise") |
| **Duplicate-text check against past posts** (D82) | Covers only the downloaded ranges. Whether long posts come through in full: UNVERIFIED | Covers what the app has read. The timeline helper refuses windows older than 29 days (`scripts/x_api.py:210-217`), so older history needs a separate first-run import. No history source is decided (conflict K14) | – | Checks only what the app has seen, and says so |
| **Voice-capture import** (D78) | Post text from the CSV. D79 allows only originals as samples, and the CSV has no type column; a leading @ is a guess, not proof (conflict K13) | Own timeline, about 200 posts, $0.20–1.00 once | Grok `from:` search, checked on an X API app | The questionnaire (D78) |
| **Experiments** (primary today: the root's metric at the 36–60 h snapshot, `scripts/loop.py:1149, 290-293`) | Possible only with new rules: a download range covering each post at a fixed age, kept history (today's importer overwrites, `scripts/loop.py:512`), a maximum scoring age, and missed-download handling. Most For You reach comes within 48 hours (`reference/x-algorithm.md:17`), but that doesn't show follows and visits settle then. New follows per post become a usable primary | As today | – | Basic and Full cohorts kept apart (L2-C5) |
| **Weekly review** (`.claude/skills/results/SKILL.md:15-35`) | Posts, follows, shares, profile visits and own-reply rows. No reader questions and no profile check. Verified followers and qualified impressions are typed from X's screen | As today, plus the CSV for follows. X's eligibility screen stays the authority for verified followers (`reference/x-api.md:26`) | Reader questions only if checked | The review says which sections are missing, and why |
| **Growth: verified followers and qualified impressions** (D27) | Typed by the user from X's screen (`.claude/skills/results/SKILL.md:16`) | Verified followers from `verified_followers_count` (spec only) or the follower list; qualified impressions still typed | – | Typed weekly |

### 2.4 Discovery

*Update 26 Sep (D88): Grok is dropped. The Grok options below are the research record; the product's Discovery column is X API recent search, with no check needed.*

**Grok (xAI) for reading X.**
- **Costs:** "$5 per 1k posts fetched and $10 per 1k user profiles fetched, in addition to token costs". "Every post returned by a search or thread fetch, including parent and quoted posts, counts" (https://docs.x.ai/developers/pricing). Counts are "not de-duplicated" (XSEARCH).
- **Limits** are per model, in requests per second and tokens per minute. The tier rises with spend (https://docs.x.ai/developers/rate-limits). No X-search-specific limit is documented.
- **Why a check is needed:**
  - The repo has seen Grok invent three posts, ids and handles (`scripts/x_read.py:9-11`).
  - xAI's citations are a list of source links, and "not every URL in this list will necessarily be directly referenced" (https://docs.x.ai/developers/tools/citations).
- **Today's repo** runs the Grok Build CLI (`scripts/grok_read.py:36-39`), not the xAI API. Its model and billing, and which terms apply to the CLI route rather than the API, belong to layer 3 (https://docs.x.ai/build/settings).

**xAI's terms (XAI-ENT, read in the browser).**
- **End users:** API customers may build "Bundled Services" and make them available to "End Users". "Customer remains fully responsible and liable" for them (§1). End-user terms must be "no less protective of SpaceXAI" (§2).
- **Training:**
  - xAI "will not use any User Content to train", "subject to disclosures to Customer and Customer-controlled user settings" (§3.1).
  - The customer must not use Output to train models "except as may be expressly permitted in an Order Form" (§3.2).
- **Personal data:** "Customer represents and warrants that it will not intentionally submit … any Personal Data to the Services except through SpaceXAI's ZDR-Enabled API" (§11.2).
  - Other people's posts and handles are personal data in most privacy laws. So for any job that sends them, zero data retention looks like a **prerequisite**, not an option.
  - The next sentence speaks of "if Customer elects ZDR", so how the two read together is UNVERIFIED.
- **X content:** no clause was found that allows or forbids storing, caching or showing posts that come back from X search, or that passes X's Developer Agreement down. Third-party services are governed by "the terms between Customer and the applicable third-party provider" (§3.5).
- **Not found:** the "no competing product" and "no resale" wording a search copy reported was not in the part of the page read (the first 50,000 characters). UNVERIFIED.

**What `x_read.py`'s rule means without Full.**
- Every Grok post is looked up by id on the X API. Missing or mismatched posts are dropped. "If the lookup can't run, nothing is returned" (`scripts/x_read.py:9-14, 68-86`; the rule in `AGENTS.md`).
- The check needs an X API app, not necessarily the user's connection. Public posts can be looked up with the vendor's app-only token (https://docs.x.com/fundamentals/authentication/oauth-2-0/application-only; Codex).
- So a Basic-only user gets Discovery only if the vendor runs and pays for the check: $0.005 a post plus $0.010 an author (`scripts/x_api.py:256-267`). Otherwise they get nothing.
- Showing Grok's posts unchecked would break the rule "Never cite a post that didn't pass this check" (`AGENTS.md`).

**X API search as the alternative.**
- Recent search covers 7 days and returns up to 100 posts a request. Full-archive search is on pay-per-use (https://docs.x.com/x-api/posts/search/introduction).
- Results are X's own data, so no check is needed, and they can be shown under X's display rules.
- Keyword queries only. Any model could suggest the queries.
- Needs an X API app; bills at post price (assumed, UNVERIFIED).

**The box.**
- D60 lets a model job reach the web "only through a fetch the backend controls and logs" (`reviews/ui-direction.md:70`).
- Grok's X search runs on xAI's side, inside the model call. The backend can restrict it (allowed and excluded handles, dates) and see the tool calls in the stream (XSEARCH), but the fetch itself doesn't pass through the backend. Conflict K11.

### 2.5 Terms and privacy

**Storing and deleting.**
- "If you store X Content offline, you must keep it up to date with the current state of that content on X" (DP).
- Delete or change content deleted, made private or protected, suspended or withheld on X "as soon as reasonably possible, or within 24 hours after receiving a request to do so by X or the applicable X account owner" (DP).
- The Agreement says "all reasonable efforts … as soon as possible, and in any case within twenty four (24) hours after a written request" (DA IV.B).
- The 24 hours runs from a request. Without one, the duty is "as soon as reasonably possible".
- On termination, "permanently delete all Licensed Material" (DA VII.I). Keep it "secure … using industry-standard organizational and technical safeguards" (DA III.G).
- **Tools:**
  - Batch compliance is open to any approved app with a bearer token, and reports deleted, protected, deactivated, suspended and edited items (https://docs.x.com/x-api/compliance/batch-compliance/introduction).
  - Creating a job uses POST and uploading ids uses PUT (same page). The product's "no X writes" promise (D58) will need to say whether these count (Codex, inference).
  - The real-time compliance streams are Enterprise-only (https://docs.x.com/x-api/compliance/streams/introduction).
  - No clause makes a compliance endpoint mandatory; the outcome is what's required.
- **For this product:**
  - Under option B the vendor is the licensee for data kept on every user's machine. Meeting the duty across offline installs, and handling a request that arrives while a machine is off, is an unsolved design requirement.
  - The daily follower read refreshes follower ids. Stored reply text doesn't refresh itself.
  - A vendor compliance service would send stored ids off the user's machine (D42, D52).

**Showing other people's posts in the app** (Waiting for you, Worth joining, Builders).
- Allowed: "Copy a reasonable amount of and display the X Content on and through your Services to Users" (DA II.A).
- Conditions (DR, DP), not a complete checklist:
  - "The post author's profile picture, @username, and display name must always be displayed and link to the user's X profile."
  - Text "may not be altered or modified".
  - "The post timestamp must be displayed and link to the post's permalink".
  - Action icons, or "In lieu of post Actions, 'View on X' may be shown".
  - The X logo "reasonably visible".
  - Links in the text, edited posts, and replies or reposts have their own display rules on the same page (Codex).
  - Use the API for "the most current version available for display" (DP).
  - No iframes (DA III.K).
  - "You may not serve content obtained using one person's authentication token to a different person who is not authorized to view that content" (DP).
  - "Don't … Use mock ups of posts that don't exist on the platform" (DR). Whether an app-styled draft preview counts: UNVERIFIED (conflict K8).
- Today's check fetches the text, author handle and numbers (`scripts/x_api.py:262-263`), not the avatar, display name or links a compliant card needs.

**Passing X data to the vendor as aggregate learning data (D76).**
- For: "Aggregate analysis of X content that does not store any personal data (for example, user IDs, usernames, and other identifiers) is permitted, provided that the analysis also complies with applicable laws and all parts of the Developer Agreement and Policy" (RU).
- Possibly against: "You may not use the X API to measure the availability, performance, functionality, or usage of X for benchmarking, competitive, or commercial purposes". One example: "Calculate aggregate X Post metrics, such as the total number of Posts posted per day, or the number of account engagements" (DP, "X performance benchmarking").
  - **Two readings, neither established:** that the clause is about measuring X itself, which learning which formats work isn't; or that any pooled engagement numbers for a commercial product are caught.
  - Pooling only relative outcomes (which format won) isn't an established way out either.
- Derived data can't go to "any third party" (DA III.A(d)), and X Content includes "derivative works" (DA I.12). Under option A the vendor is a third party to each user's licence. Under option B the vendor is the licensee.
- Consent: "a person authenticating into your service does not by itself constitute consent" (DP). A privacy policy must be shown "before they are permitted to download, install, or sign up" (DP).
- "Off-X matching" (linking an @handle or user id to an off-X identifier, such as a licence account) needs "express opt-in consent", or falls under the narrow exceptions the Policy lists (DP).

**Post text in model prompts (D78, D81) against the training ban.**
- **Training:**
  - "(k) use the X API or X Content to fine-tune or train a foundation or frontier model" (DA III.A(k)).
  - "X prohibits any use of the X APIs and/or X Content to fine-tune or train a foundation or frontier model with the exception of Grok" (RU).
  - Neither page defines "foundation or frontier model".
  - The product doesn't plan training. D76's vendor improvements go out as product updates (`reviews/ui-direction.md:86`).
- **Prompts (inference):**
  - No X term addresses sending X content to a model API. The Agreement, Policy, Restricted Uses and Display Requirements were searched for "artificial", "machine learning", "AI", "LLM", "model" and "ingest"; only the training ban matched.
  - The nearest clause is the ban on providing Licensed Material "to any third party except as expressly permitted" (DA III.A(d)). A model provider processing a prompt for the user may or may not be that. No processor carve-out is stated. UNVERIFIED.
  - "Your use case description is binding on you" (DP), so declaring the model processing in it is at least prudent.
- **By decision:**
  - D78 sends only the user's own posts.
  - D81's optional "more accurate sorting" sends other people's reply text. That's both X content and third-party personal data. With xAI as the engine, §11.2's zero-retention clause applies.

**Other people's data stays private and local (D42).**
- X agrees in spirit: no "surveillance … investigating or tracking X users" (DA XIV.B), and no "individual profiling or psychographic segmentation" (RU).
- Builders (mutuals, last exchange) is a per-user view of people the user talks to. Whether that counts as "profiling" is UNVERIFIED. It stays on the user's machine and isn't sold.

**X's user terms change on 9 Oct 2026.** They add "autonomous actions on your behalf" to what users are responsible for, and cover prompts, outputs and information obtained (x.com/en/tos, live). Manual posting keeps the product out of automated publishing. What the change means for automated reading is a separate reading, not settled here.

---

## 3. Conflicts with D37–D87

Listed as found, not worked around.

| # | Decision | What strains it | Evidence |
|---|---|---|---|
| K1 | **D54** (guided in-app steps; its example is "getting X API keys from X's developer portal") | X warns that requiring end users to register apps "could result in enforcement actions against you, your applications, your customers, and/or the end users". D54's example is the pattern X names. | RU; `reviews/ui-direction.md:64` *Accepted risk under D90 (own keys); X not asked, D94.* |
| K2 | **D43 / D50** (a tier "that works from the analytics CSV export alone"; the CSV-only tier "matters as much" in a public v1) | If the export needs Premium, the CSV tier isn't open to non-Premium users, and no current official page settles it. (Codex reads this as an access limit rather than a conflict; kept, §4.) | §2.1; `reviews/ui-direction.md:53, 60` *Settled by decision in D95 (Premium required for everyone), not by an official page; narrows D50.* |
| K3 | **D76** (aggregate learning data, "on, with the switch to disable" as the lean) | X's benchmarking clause may reach pooled engagement numbers (a legal reading). X says sign-in isn't consent. Under option A the vendor is a third party to each user's X data. | DP; DA III.A(d); `reviews/ui-direction.md:86` *Accepted risk under D103; D91 reopens D52.* |
| K4 | **D78 / D81** (post text into model prompts) | No X term covers inference; the third-party transfer ban is the nearest. D81's cloud option sends other people's replies, and xAI's terms send personal data to its zero-retention API only. | DA III.A(d); XAI-ENT §11.2; `reviews/ui-direction.md:88, 91` *Deferred to layer 3 by D104.* |
| K5 | **D42** (other people's data in private local files) | Stored X content must be kept current, and removed promptly and within 24 hours of a request. A private file that's never refreshed breaks that. Under option B the vendor answers for every user's files, including machines that are off. | DP; DA IV.B; `reviews/ui-direction.md:52` *Addressed by D101 (ids and numbers only, text fetched fresh, deleted after 30 days); residual risk accepted: unopened ids for up to 30 days, and requests while the machine is off.* |
| K6 | **D12 / D28** (Waiting for you, Worth joining, Builders cards) | Other people's posts must follow X's display rules: avatar, name, linked handle, linked timestamp, the X logo, actions or "View on X", unaltered and current. The mock uses placeholders. Collapsing greetings to one line hides them rather than altering them; whether that's allowed: UNVERIFIED. | DR; DP; `reviews/ui-direction.md:22, 38` *Resolved by D102: X-compliant cards.* |
| K7 | **D58** (no X writes, a safety promise for everyone) | Batch compliance, the tool for keeping stored content current, uses POST and PUT to X. | Batch compliance page; `reviews/ui-direction.md:68` *Resolved by D101: no batch compliance.* |
| K8 | **D16** (cards previewed in X's layout, in the app's own look) | "Don't … Use mock ups of posts that don't exist on the platform." Whether a draft preview counts: UNVERIFIED. The app's own look may already avoid it. | DR; `reviews/ui-direction.md:26` *Addressed by D102 (a "Draft" label on previews); whether previews fall under the rule stays unverified, risk accepted.* |
| K9 | **D17** (the app finds the post; pasting the link was rejected) | On Basic the app can't find the post. The sketch's fallback is the rejected paste. | §2.3; `reviews/ui-direction.md:27, 120` *Resolved by D97: the paste returns on CSV only.* |
| K10 | **D29 / D12 badge** (first-hour likes and replies, the live waiting count) | These need Full and live polling, so they're empty on Basic. Timers, the pre-post reminder (D35) and the minutes question don't need X data. On Full, the UTC day turn (10:00 Brisbane) can double-charge. | §2.3; `reviews/ui-direction.md:22, 39, 45` *Resolved by D97.* |
| K11 | **D60** (a model job reaches the web only through the backend's own fetch) | Grok's X search runs on xAI's side inside the model call. It can be restricted and observed, but its fetch doesn't pass through the backend. X API search, run by the backend, doesn't have this problem. | §2.4; `reviews/ui-direction.md:70` *Void under D88: no Grok.* |
| K12 | **D68** (the daily check is all-or-nothing, written once) | Scheduled reads fail in new ways on a desktop: asleep, token expired, credits out. A weekly follower list (L2-C2) is a different cadence from the daily transaction. A missed 36–60 h read can't be retaken. | `reviews/ui-direction.md:78`; `scripts/snapshot.py:179-199`; `reference/x-api.md:18` *Resolved by D98: catch up on wake.* |
| K13 | **D79** (only originals are voice samples) | On Basic, the CSV has no post type, so originals can't be told reliably from replies. | §2.3; `reviews/ui-direction.md:89` *Resolved by D97: on CSV only nothing is preselected; the user ticks each original.* |
| K14 | **D82** (refuse a draft whose text repeats an earlier post) | "Earlier post" needs a history source. On Full the timeline helper stops at 29 days; on Basic it's the downloaded ranges. Without a decided first-run history, the check covers only what the app has seen. | `reviews/ui-direction.md:92`; `scripts/x_api.py:210-217` *Resolved by D99: first-run history, and the check says how far back.* |

**Notes, not conflicts** (moved here after Codex's read, §4):
- **The D52 trust note** says users give the program "their X and model API keys" (`reviews/ui-direction.md:124`). Under option B there are OAuth tokens instead; they still need the secure store. A wording update.
- **D77** says each extra profile multiplies API cost (`reviews/ui-direction.md:87`). At full price the cost per profile also varies with follower count. That's a pricing input, not a contradiction.

**Checked and not in conflict:**
- D83: Premium can be asked on Basic and read on Full if `subscription_type` is returned (conditional).
- D82's daily count is shown only where the tier can count it.
- D39 and D47: this research touched nothing in the loop.

---

## 4. Codex's second read

Codex (read-only, blind: given the document and the repo, not this session's reasoning) ran for 7 minutes 45 seconds and raised 33 points. Three were spot-checked live before acting: the token quote's ending, the off-X exceptions, and the Activity API. All three held. One check failed: Codex couldn't find xAI's "not de-duplicated" wording, but it is on the X Search page (`.md` line 359).

| # | Codex's point | What was done |
|---|---|---|
| 1 | The 24 hours runs from a request; otherwise the duty is "as soon as reasonably possible". A weekly pass isn't shown to be enough | **Accepted.** Summary, §2.5, K5 and L2-C8 reworded |
| 2 | "No X developer terms at all" for CSV-only is unsupported; X Content includes content supplied through other authorised means | **Accepted.** L2-C1 and §2.1 reworded |
| 3 | Discovery doesn't need the user's Full connection: the vendor's app-only token can run the check | **Accepted.** Summary, §2.4, L2-C7 reworded |
| 4 | The Builders following list is missing from costs; the recommended option's total leaves out the daily profile read | **Accepted.** Rows added and totals corrected ($228.35) |
| 5 | Overlapping reads are double-counted; a daily profile read includes the weekly one; deduplication is a soft guarantee | **Accepted.** Count-only totals corrected; overlap and "soft guarantee" noted |
| 6 | A client-side budget can't stop a user's token billing the vendor's app | **Accepted.** §2.2 row added; L2-C3 reworded |
| 7 | Event-based reads (Activity API) are a missing alternative | **Accepted, checked live.** §2.1 section and L2-C2 option added |
| 8 | Grok against search compares unequal outputs; with authors it's $0.20 against $0.15 | **Accepted.** Figures and L2-C6 corrected |
| 9 | Today's CSV importer can't bootstrap a CSV-only account | **Accepted, checked** (`scripts/loop.py:501-506`). §1 and §2.3 now say it's new work |
| 10 | Weekly scoring needs a download and history contract; 48-hour reach doesn't show follows settle | **Accepted.** §2.3 and L2-C5 reworded |
| 11 | "Basic users never learn anything" is false: edits and voice still teach | **Accepted.** L2-C5 reworded |
| 12 | D79 is a missing conflict | **Accepted.** K13 |
| 13 | D82's duplicate check needs a history source; the timeline helper stops at 29 days | **Accepted.** K14, L2-C13 |
| 14 | Desktop downtime and D68 are missing | **Accepted.** K12, L2-C12 |
| 15 | Daily follower matching isn't "exact" credit; stopping at the first known follower misses unfollows | **Accepted.** L2-C2 reworded |
| 16 | The benchmarking reading and the "relative outcomes" workaround are both too confident | **Accepted.** §2.5 gives two readings; L2-C10 recommends clearance first |
| 17 | The token quote dropped "who is not authorized to view that content"; the off-X rule has exceptions | **Accepted, checked.** Quote restored; exceptions named |
| 18 | xAI terms: training promise and output rule have qualifiers; Third-Party Services is §3.5; zero retention is a prerequisite, not "where offered"; CLI and API differ | **Accepted, checked.** §2.4 and L2-C9 reworded |
| 19 | "Permitted" overstates option B: the use case still needs X's acceptance; government end users need Enterprise (DA XIV.C) | **Accepted, checked.** §2.2 and L2-C1 reworded |
| 20 | Batch compliance uses POST and PUT, against the no-writes promise; a vendor service sends ids off the machine | **Accepted.** K7 added; §2.5 and L2-C8 reworded |
| 21 | The display checklist is incomplete; "View on X" is an alternative to actions; today's lookup lacks avatar and display name | **Accepted.** §2.5 and L2-C11 reworded |
| 22 | Polling gives the first *observed* like, not a guaranteed bound; use the owned-price timeline, not ID lookup | **Accepted.** §2.1 and §2.3 reworded |
| 23 | Waiting for you needs replies filtered and the answered reply's id; shout-out detection must match the approved shout-out | **Accepted.** §2.3 reworded |
| 24 | D83 must stay conditional; add qualified impressions (D27); X's screen stays the authority | **Accepted.** §2.3 rows reworded. The Premium help page point is recorded as Codex's, not re-checked |
| 25 | K2, K3 and K12 (first draft) aren't conflicts | **Partly accepted.** The trust note and D77 moved to notes. **K2 kept:** D43 describes a tier "that works from the analytics CSV export alone" for a wide public v1 (D50), and a Premium requirement narrows it |
| 26 | Not all nudges need Full: timers, D35 and the minutes question work on Basic | **Accepted.** K10 narrowed |
| 27 | "The backend can't control or log" Grok's search is overstated: handles, dates and streamed tool calls are visible | **Accepted.** K11 reworded; the conflict stands |
| 28 | C6 needn't require Grok for query ideas; C9 wrongly says a use-case description exists only under B | **Accepted.** L2-C6 and L2-C9 reworded |
| 29 | Profile visits aren't CSV-only | **Accepted.** Summary corrected |
| 30 | runs.log amounts are estimates, not bills | **Accepted.** §2.1 says so |
| 31 | "Not de-duplicated" not found; token prices are short-context only; the Basic-plan quote lacks a link | **Partly accepted.** **Not accepted:** the quote is on https://docs.x.ai/developers/tools/x-search.md line 359, now cited. Short-context note and the link added |
| 32 | Citations don't show Grok's whole output is links; rest the check on observed invented posts | **Accepted.** §1 and §2.4 reworded |
| 33 | "Reading isn't posting, so the terms change doesn't touch this layer" doesn't follow | **Accepted.** §2.5 reworded |

---

## 5. Choices for the operator

**L2-C1. How does the product connect to each user's X account?**
- **Decided 26 Sep (D90):** option (b), each user brings their own X developer keys and pays X directly. X's enforcement warning is accepted; X is not asked first (D94). D91 reopens D52 (paid, closed) in favour of weighing a free, open-source product.
- **Options:**
  - (a) Option B only: one product app, "Connect X" with OAuth.
  - (b) Option A: each user brings their own developer keys.
  - (c) No API at launch: Basic (CSV) only, with Full added later.
- **Trade-offs:**
  - (a) Easiest for users, and it avoids X's multiple-apps warning. The vendor pays full price, is capped at 3M post reads a month, needs X to accept the use case, and can be pushed to Enterprise at an unknown size.
  - (b) Cheapest reads, paid by the user. Heavy setup, and X names this pattern as enforcement-worthy, for customers too.
  - (c) No API developer app, but whether X's developer terms reach user-downloaded CSVs is unresolved (§2.1). Most live screens are empty (K9, K10), and Discovery is nothing unless the vendor runs checks.
- **Recommendation:** (a).
- **Depends on:**
  - L2-C2's cost cut.
  - X accepting the use case.
  - X's answer on the Enterprise threshold. X links an Enterprise interest form from PRICING; asking is outward-facing, so it's the operator's call.

**L2-C2. How does Full track followers?**
- **Decided 26 Sep (D92):** option (c), the count daily, the lists weekly, per-post follows from the CSV. Follow events researched at the build stage.
- **Options:**
  - (a) The whole list daily, as today.
  - (b) The list weekly.
  - (c) Counts daily from `/2/users/me` (`followers_count`, `verified_followers_count`); the list weekly for Builders; per-post follows from the CSV.
  - (d) Counts only; no list, and no Builders.
  - (e) Follow and unfollow events from the Activity API.
- **Trade-offs:**
  - (a) The most complete, but it dominates cost (§2.1). Its per-post credit is only a lower-bound match to recent interactions (`reference/x-api.md:40`), and it misses follow-then-unfollow between reads.
  - (c) Cuts a heavy user from about $1,528 to about $228 a month at full price. The daily match is lost, but the CSV's per-post follows are exact where the user downloads it (`reference/x-api.md:36`).
  - (e) The cheapest at scale (about $0.010 per follow), but needs a vendor server to receive events, and a self-serve app is capped at 1,500 subscriptions.
- **Recommendation:** (c) for v1, with (e) researched at the build stage.
- **Depends on:** `verified_followers_count` being returned to pay-per-use apps (spec only, not live-tested); the build stack (D47), for (e).

**L2-C3. Who pays for X reads under option B, and where is the budget enforced?**
- **Decided 26 Sep (D93):** moot under D90 (the user pays); X's console cap is the only spending limit, and the per-run search cap stays.
- **Options:**
  - (a) Built into the price, with a per-user monthly read budget shown in the app.
  - (b) A usage add-on the user pays.
  - (c) Price tiers by follower count.
  - For each, the budget is soft (in the app) or hard (reads pass through a vendor service).
- **Trade-offs:**
  - (a) Simplest for users. A soft budget can't stop a modified client billing the vendor's app.
  - A hard budget means users' X data passes through the vendor, which strains D42 and the D52 trust note.
  - (b) Fair, but adds a bill. (c) Matches the cost driver, but is odd to explain.
- **Recommendation:** (a) with a soft budget and X's app-wide spending limit as the backstop.
- **Depends on:** build-stage pricing (D52), and how much vendor risk the operator accepts.

**L2-C4. What is the Basic tier, given the export probably needs Premium?**
- **Decided 26 Sep (D95):** Premium is required for everyone (the operator knows the export needs it). The export's range is unknown.
- **Options:**
  - (a) Basic = CSV, stated as "needs X Premium".
  - (b) Basic plus a manual mode for non-Premium users, who type a few numbers per post.
  - (c) No Basic; everyone connects Full.
- **Trade-offs:**
  - (a) Honest and simple, but leaves non-Premium users unmeasured.
  - (b) Serves them, but typed numbers are slow and error-prone.
  - (c) Clean, but every user costs the vendor API money.
- **Recommendation:** (a), after the operator checks a non-Premium account in X's UI.
- **Depends on:** that check, the export's date limit, and a new importer that can build history from the CSV alone (§2.3).

**L2-C5. How are experiments scored on Basic?**
- **Decided 26 Sep (D96):** option (a), a fixed post age from the downloads, cohorts kept apart.
- **Options:**
  - (a) At a fixed post age from downloads, with new follows available as a primary.
  - (b) No experiments on Basic. Basic users still learn from their edits and voice picks (D26, D78); only experiment-based lessons are missing. No Full user's lessons carry over (D76).
  - (c) The same 36–60 hour rule, with the user asked to download daily.
- **Trade-offs:**
  - (a) Works with a weekly habit, and follows are the goal metric. It needs a download range covering each post at the chosen age, kept history, a maximum scoring age and missed-download rules.
  - (b) Simple, and loses only one kind of learning.
  - (c) Exact, but no one downloads daily.
- **Recommendation:** (a), with Basic and Full cohorts kept apart.
- **Depends on:** confirming that export numbers add up per post, the export's date limit, and the new importer. This is product work; this repo's ~8 Oct experiment rules are untouched.

**L2-C6. Where do other people's posts come from on Full?**
- **Decided 26 Sep (D88):** option (a) with (c)'s query ideas: X API recent search run by the backend, queries built by code from phrases any remaining engine supplies. Grok, option (b), is dropped.
- **Options:**
  - (a) X API recent search, run by the backend.
  - (b) Grok's X search, checked by id on the X API.
  - (c) X API search as the source, with query ideas from any eligible model the user has set up.
- **Trade-offs:**
  - (a) X's own data: no check, displayable, inside the box. About $0.15 per 10 posts with authors; keyword-only; 7 days.
  - (b) Adds semantic search at about $0.20 per 10 plus tokens, sits outside the box (K11), and xAI's terms are silent on X content.
  - (c) Keeps (a)'s strengths and gains better queries, at the cost of one more model job.
- **Recommendation:** (c).
- **Depends on:** confirming search bills per post returned (UNVERIFIED), and layer 3.

**L2-C7. What does a user without Full get from Discovery?**
- **Decided 26 Sep (D100):** option (a), Discovery needs the user's X connection.
- **Updated 26 Sep (D88):** option (b) is gone with Grok. What remains: (a) nothing, or (c) the vendor runs X API search itself with its app-only token, at the vendor's cost (no check needed, since X API results are X's own data). Still open.
- **Options:**
  - (a) Nothing.
  - (b) Grok results shown unchecked, with a label.
  - (c) The vendor runs the check with its app-only token, at the vendor's cost, perhaps as a paid add-on.
- **Trade-offs:**
  - (a) Keeps "never cite an unchecked post" at no cost.
  - (b) Breaks the rule and risks invented posts on screen.
  - (c) Keeps the rule and serves Basic users, but adds vendor cost and a vendor service.
- **Recommendation:** (a) for v1, with (c) as a later add-on.
- **Depends on:** L2-C1 and L2-C3.

**L2-C8. What is stored, and how is it kept current?**
- **Decided 26 Sep (D101):** option (a), with other people's ids and numbers deleted after 30 days and no batch compliance.
- **Options:**
  - (a) Store the user's own posts in full, and other people's content as ids and numbers only. Fetch their text when shown. Run a regular compliance pass over stored ids.
  - (b) Store everything; refresh daily.
  - (c) Store nothing of other people's.
- **Trade-offs:**
  - (a) Keeps the least to be kept current, but showing old replies costs a read.
  - Batch compliance uses POST and PUT (K7), and a vendor service sends ids off the machine.
  - (b) Simplest to build, but has the biggest compliance surface.
  - (c) Safest, but Builders and Waiting for you lose history.
- **Recommendation:** (a).
- **Depends on:** a design for machines that are off when a deletion request arrives, and whether compliance calls count as X writes under D58. Neither is solved here.

**L2-C9. Can post text go into a cloud model's prompt?**
- **Decided 26 Sep (D104):** deferred to layer 3, per engine.
- **Note 26 Sep (D88):** the xAI terms part no longer applies; the question stays open for whichever engines remain (layer 3).
- **Options:**
  - (a) Ask X in writing, and name the model processing in the use-case description (options A and B both have one).
  - (b) Proceed on the reading that inference for the user isn't "providing access to a third party".
  - (c) Only local models get text imported from X. Cloud drafting from the user's own typed material stays open.
- **Trade-offs:**
  - (a) Slow, but settles it.
  - (b) Fast, and the risk falls on the vendor's X access.
  - (c) Safe for imported text, but voice capture (D78) and reply sorting (D81) would need a local engine.
- **Recommendation:** (a).
- **Depends on:** layer 3's engine list. Any job that sends other people's posts or handles to xAI needs its zero-retention API (XAI-ENT §11.2).

**L2-C10. How does D76's aggregate collection meet X's terms?**
- **Decided 26 Sep (D103):** option (c), collected as D76 says; X's terms an accepted risk.
- **Options:**
  - (a) Legal clearance first; collection off until cleared.
  - (b) Collect only relative outcomes (which format won within a user's own experiment, Weight values), never engagement counts.
  - (c) Collect as D76 says.
- **Trade-offs:**
  - (a) Safest, but delays the learning.
  - (b) Lower exposure, but not an established way out of the benchmarking clause.
  - (c) Simplest, and the most exposed.
- **Recommendation:** (a), designing to (b)'s shape meanwhile.
- **Depends on:** the build-stage privacy research D76 already names.

**L2-C11. How are other people's posts shown?**
- **Decided 26 Sep (D102):** option (a), plus a "Draft" label on the user's own previews.
- **Options:**
  - (a) A card that meets X's display rules: avatar, name, linked handle, linked timestamp, X logo, actions or "View on X", links and edits handled, text unaltered, fetched fresh.
  - (b) A one-line summary with "View on X" only.
  - (c) Summaries in lists, and the full card when opened.
- **Trade-offs:**
  - (a) Compliant but heavy. It needs more fields read (avatar, display name) and the design reworked (K6).
  - (b) Light, but a model-written summary of someone's post is a derivative the display rules don't address.
  - (c) Balances the two, with (b)'s question.
- **Recommendation:** (a) in the lists, with greetings as a count, not hidden posts.
- **Depends on:** the design review of D12 and D28, and the read cost of the extra fields.

**L2-C12. What happens when a scheduled read can't run?** (the Mac asleep, sign-in expired, credits out, one read failing)
- **Decided 26 Sep (D98):** option (a), with waking the machine researched at the build stage.
- **Options:**
  - (a) Catch up on wake where possible. Mark a missed 36–60 h read as missed (it can't be retaken). Keep D68's all-or-nothing per run.
  - (b) Wake the machine for reads, where the operating system allows.
  - (c) A vendor server does the reads.
- **Trade-offs:**
  - (a) Honest and local, but some posts lose their early read.
  - (b) Fewer misses, but it depends on the platform (D49).
  - (c) Reliable, but moves X data off the machine and adds a server (D42, D52).
- **Recommendation:** (a), with (b) researched at the build stage.
- **Depends on:** the stack (D47, D49), and how weekly reads (L2-C2) fit D68's single daily write.

**L2-C13. How much history does the app import at first run?** (for D82's duplicate check and D78's voice capture)
- **Decided 26 Sep (D99):** option (a), about 800 posts as a target on a connection, every CSV range on CSV only.
- **Options:**
  - (a) Full: the user's own recent timeline, say the last 200–800 posts. Basic: every CSV range the user can download.
  - (b) Only what the app sees from now on.
  - (c) The user's X data archive, downloaded from X's settings.
- **Trade-offs:**
  - (a) Covers most repeats at a one-off cost ($0.20–1.00 at 200 posts on Full).
  - (b) Free, but D82's refusal misses older repeats.
  - (c) Complete, but another manual download, and its format and terms weren't researched here (UNVERIFIED).
- **Recommendation:** (a), with the check saying how far back it looked.
- **Depends on:** the timeline endpoint's history limit for non-organic fields (UNVERIFIED), and the export's range.

### Suggested order

1. **L2-C1** (connection) and **L2-C2** (follower tracking) together: they set the cost and the terms exposure.
2. **L2-C3** (who pays, and where the budget is enforced), which follows from both.
3. **L2-C4** and **L2-C5** (the Basic tier and its scoring), after the operator checks a non-Premium account.
4. **L2-C12** and **L2-C13** (missed reads, first-run history), which shape the stack.
5. **L2-C6** and **L2-C7** (Discovery), which feed layer 3.
6. **L2-C8** and **L2-C11** (storage and display), then **L2-C9** and **L2-C10** (the two legal questions). These can run in parallel with layer 3.
