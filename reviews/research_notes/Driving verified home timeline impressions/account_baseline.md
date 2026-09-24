# @exitzerocode baseline: verified Home Timeline impressions and verified followers (as of 24 Sep 2026)

Scope and sourcing. Everything here comes from local repo files; nothing was fetched from X. "Computed" means I derived the number from the cited file(s) myself. The X eligibility-screen figures (26/500 verified followers, 337/500K Verified Home Timeline impressions in the last 90 days, "Does not include replies", seen 24 Sep 2026) were supplied in the research brief. No repo file records them, so they are cited as "eligibility screen (brief)". Other accounts appear only as counts.

Source files (all under `/Users/lukemckenzie/src/thread-engine/`):
- ACT = `ledger/activity/2026-09.json` (157 items, API read 24 Sep 01:20 UTC under `reads.backfill`, X export under `reads.export`)
- CSV = `loop/inbox/account_analytics_content_2026-09-18_2026-09-24.csv` (X analytics export, 152 rows, downloaded 24 Sep 12:21 Brisbane)
- LED = `ledger/<root_id>.json` (format, lane, cards, Boost flag); SUM = `ledger/SUMMARY.md`
- RAW = `ledger/raw/api/backfill-20260924T0120.json` (API `me`, timeline, mentions, follower IDs)
- ACC = `ledger/activity/account.json`; FOL = `loop/inbox/followers.json`, `loop/followers/followers-2026-09-24.json`
- AUD = `reviews/audit-2026-09.md`; R22 = `reviews/2026-09-22.md`; XAPI = `reference/x-api.md`; XALG = `reference/x-algorithm.md`; AUDIENCE = `reference/audience.md`

## Q1. Original and quote posts: reach, follows, timing, and which ones most likely produced the 337 qualified impressions

### Takeaway
The whole 90-day window is 3.7 days of activity: the account's first post went out on 20 Sep 2026. In that time, 11 originals and quotes earned 2,329 organic impressions. One networking post ("Drop a hi", 856) and one iPhone comparison (509) make up 59% of that, and the networking post brought all 13 follows from originals and 20 of the 21 profile visits. 337 qualifying impressions is 14.5% of the organic original+quote pool. The most likely reasons for the gap are a low Premium share among out-of-network viewers, plus impressions from outside the Home Timeline on the one post that pulled an engaged builder crowd, plus a few hours of analytics lag. The repo can't see which post produced which qualifying impression.

### Cited Findings

**Account context**
- The account was created 28 Nov 2025, but its API `tweet_count` is 157, exactly the 157 timeline items read since 20 Sep 2026 00:00 UTC. The earliest is 20 Sep 09:25 UTC. So every post the account has ever made (ignoring deleted ones) falls inside the 90-day eligibility window, and nothing ages out until about 18–19 Dec 2026. — [RAW `me.created_at`, `me.public_metrics.tweet_count`, `since`, timeline dates](/Users/lukemckenzie/src/thread-engine/ledger/raw/api/backfill-20260924T0120.json)
- Profile on 24 Sep: 36 followers, following 13, 92 likes given, 21 media posts, and the pinned post is the boosted tool-swap (`2102737637346095128`). — [RAW `me`](/Users/lukemckenzie/src/thread-engine/ledger/raw/api/backfill-20260924T0120.json)
- The account has a blue check. — [R22 line 13](/Users/lukemckenzie/src/thread-engine/reviews/2026-09-22.md)
- The export's numbers are organic. The boosted tool-swap shows 98 there, against 99 organic and 2,105 public in the API. Its profile visits match the API's (58 total). — [XAPI "X's analytics export"](/Users/lukemckenzie/src/thread-engine/reference/x-api.md)
- In the API, public impressions equalled organic impressions (within 1) on 10 of 11 originals and quotes. The exception was the boosted tool-swap. — [XAPI P9](/Users/lukemckenzie/src/thread-engine/reference/x-api.md)

**Per-post table (originals and quotes).** Times were computed from `created_at` with Python zoneinfo: Brisbane is UTC+10 and US Eastern is EDT, UTC−4. Impressions are organic, shown as "API / export". Likes, profile visits, bookmarks, new follows and detail expands come from the export (CSV). "Card follows/visits" are the export's numbers summed over that post's own thread cards. Age is the post's age at the API read (24 Sep 01:20 UTC). — computed from [ACT](/Users/lukemckenzie/src/thread-engine/ledger/activity/2026-09.json), [CSV](/Users/lukemckenzie/src/thread-engine/loop/inbox/account_analytics_content_2026-09-18_2026-09-24.csv), [LED files](/Users/lukemckenzie/src/thread-engine/ledger/), [SUM](/Users/lukemckenzie/src/thread-engine/ledger/SUMMARY.md)

| # | Post (own content) | Kind · format · lane (current) | Brisbane | US Eastern | Organic impr. API / export | Public impr. | Likes | Profile visits | Bookmarks | New follows (root) | Card follows / card visits | Detail expands | Boosted | Age h |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---:|---|---:|
| 1 | Home Wi-Fi settings thread (6 cards, no media) | original · settings · other | Sun 20 Sep 19:25 | Sun 20 Sep 05:25 | 285 / 285 | 285 | 1 | 0 | 2 | 0 | 1 / 0 (cards: 229 impr.) | 18 | no | 87.9 |
| 2 | iPhone Camera settings thread (8 cards, photo) | original · settings · other | Mon 21 Sep 16:48 | Mon 21 Sep 02:48 | 137 / 137 | 137 | 1 | 0 | 2 | 0 | 0 / 1 (220) | 11 | no | 66.5 |
| 3 | MacBook battery settings thread (8 cards, photo) | original · settings · other | Tue 22 Sep 09:05 | Mon 21 Sep 19:05 | 151 / 151 | 151 | 1 | 0 | 1 | 0 | 1 / 0 (224) | 8 | no | 50.2 |
| 4 | "Drop a hi" networking post for AI builders (tags one account; was the pin on 22 Sep) | original · other (networking) · other | Tue 22 Sep 10:35 | Mon 21 Sep 20:35 | 856 / 855 | 856 | 24 | 20 | 0 | **13** | none | 29 | no | 48.8 |
| 5 | iPhone 18 Pro vs 17 Pro comparison (5 cards, photo) | original · comparison · other | Tue 22 Sep 15:45 | Tue 22 Sep 01:45 | 509 / 500 | 509 | 1 | 0 | 0 | 0 | 0 / 1 (170) | 6 | no | 43.6 |
| 6 | Quote post: AI-industry commentary | quote · other · other | Wed 23 Sep 13:17 | Tue 22 Sep 23:17 | 217 / 214 | 217 | 1 | 0 | 0 | 0 | 0 / 0 (19) | 9 | no | 22.0 |
| 7 | "Prompt vs finish" builder question | original · other · **main** | Wed 23 Sep 14:16 | Wed 23 Sep 00:16 | 54 / 54 | 54 | 1 | 0 | 0 | 0 | 0 / 0 (44) | 3 | no | 21.1 |
| 8 | Paid → free creator-tool swap (pinned since 23 Sep) | original · tool-swap · other | Wed 23 Sep 22:31 | Wed 23 Sep 08:31 | 99 / 98 | **2,105** | 2 | 1 | 1 | 0 | 0 / 0 (12) | 9 | **yes: 95% non-organic (~2,006 paid)** | 12.8 |
| 9 | Quote post: Australian politics | quote · other · other | Thu 24 Sep 08:37 | Wed 23 Sep 18:37 | 15 / 15 | 15 | 0 | 0 | 0 | 0 | none | 0 | no | 2.7 |
| 10 | Builder connect post ("What is your current project?") | original · other · other | Thu 24 Sep 10:30 | Wed 23 Sep 20:30 | 2 / not in export | 2 | 0 | 0 | – | – | none | – | no | 0.8 |
| 11 | Australian government / AI joke | original · other · other | Thu 24 Sep 11:08 | Wed 23 Sep 21:08 | 4 / not in export | 4 | 0 | 0 | – | – | none | – | no | 0.2 |
| | **Total** | 9 originals + 2 quotes | | | **2,329 / 2,315*** | **4,335** | 32 | 21 | 6 | **13** | 2 / 2 (918) | 93 | | |

\* Export column total: the 9 rows present in the export (2,309) plus the API values for the two 24 Sep originals missing from it (6).

- The ledger marks the tool-swap `nonorganic`: "95% of 2,105 impressions non-organic (Premium Boost; API 2026-09-24: 99 organic)". It is the only boosted post. — [LED 2102737637346095128](/Users/lukemckenzie/src/thread-engine/ledger/2102737637346095128.json)
- The audit put the Boost at "about 2,006 impressions", producing about 4 profile visits and 0 extra likes. — [AUD §4](/Users/lukemckenzie/src/thread-engine/reviews/audit-2026-09.md)
- The networking post's conversation holds 40 posts from 33 distinct other accounts that reply to or mention the account (API mentions). The account also replied 7 times in that conversation. — computed from [RAW mentions](/Users/lukemckenzie/src/thread-engine/ledger/raw/api/backfill-20260924T0120.json) and [ACT](/Users/lukemckenzie/src/thread-engine/ledger/activity/2026-09.json)
- On 22 Sep the networking post was the pinned post ("The pin's 634 views and 25 replies"). — [R22 line 80](/Users/lukemckenzie/src/thread-engine/reviews/2026-09-22.md)
- X's topic labels are a proxy. The comparison and camera threads carry Apple / Apple‑iPhone. The networking post carries Politics / Political issues / X (a labelling quirk). Across the account, the top labels by organic impressions are Technology Business 2,500, Technology 2,472, Politics 1,853, Apple 1,522, Apple‑iPhone 1,053. — [ACT `topics`](/Users/lukemckenzie/src/thread-engine/ledger/activity/2026-09.json); [SUM](/Users/lukemckenzie/src/thread-engine/ledger/SUMMARY.md)
- Lanes were relabelled on 24 Sep against the builder audience. Only "prompt-vs-finish" is `main`. The device threads and the comparison are `other` ("device settings tip with no link to the build"). — [LED amendments](/Users/lukemckenzie/src/thread-engine/ledger/); [AUDIENCE](/Users/lukemckenzie/src/thread-engine/reference/audience.md)

**Pool sizes and qualifying share (computed: 337 ÷ pool)**

| Pool that might sit behind "Verified Home Timeline impressions" | Impressions | 337 as % |
|---|---:|---:|
| Originals + quotes, organic (API) | 2,329 | **14.5%** |
| Originals + quotes, organic (export) | 2,315 | 14.6% |
| Only posts made before 23 Sep 00:00 UTC (if the screen lags ~1 day) | 1,938 | 17.4% |
| Originals + quotes + own thread cards (if self-replies counted, which the screen says it doesn't) | 3,262 | 10.3% |
| Originals + quotes, public, including ~2,006 Boost impressions (if paid counted) | 4,335 | 7.8% |

**Evidence bearing on the gap**
- **Analytics lag.** The export was downloaded about an hour after the API read (API 01:20 UTC; CSV file time 02:21 UTC). Even so, items under 3 h old at the API read showed 11.5% fewer impressions in the export (5,916 vs 6,683 over 26 items). Items 3–6 h old showed 6.8% fewer, 6–12 h 2.3%, 12–24 h 1.4%, and ≥24 h 0.5% (4,112 vs 4,131 over 80 items). — computed from [ACT `reads.backfill` vs `reads.export`](/Users/lukemckenzie/src/thread-engine/ledger/activity/2026-09.json)
- **Surfaces other than Home.** Profile visits from all items total 58 in the export, and every visitor lands on the pinned post. The networking post had 29 detail expands (the most of any post) and a 40-reply conversation. Replies notify their authors, and those authors see the root in conversation view. — [CSV](/Users/lukemckenzie/src/thread-engine/loop/inbox/account_analytics_content_2026-09-18_2026-09-24.csv); [RAW mentions](/Users/lukemckenzie/src/thread-engine/ledger/raw/api/backfill-20260924T0120.json)
- **Out-of-network distribution rules.** Originals from authors with ≤1,000 followers can be lifted to about slot 16 of For You when young and under 1,000 home views (A5). Small authors have their own 24-hour retrieval index (A7). Replies and reposts from accounts a viewer doesn't follow are filtered out of For You (A2). — [XALG A2, A5, A7](/Users/lukemckenzie/src/thread-engine/reference/x-algorithm.md)
- **Verified audience inside the network.** 26 verified followers (eligibility screen, brief) out of 36 total. — [ACC](/Users/lukemckenzie/src/thread-engine/ledger/activity/account.json)

### Inferences
- **Which posts most likely carried the 337.** The repo has no per-post verified-viewer or per-surface split, so this is a ranking of likelihood, not a measurement.
  - A naive proportional split at 14.5% gives: networking post ≈124, iPhone comparison ≈74, Wi-Fi thread ≈41, AI-commentary quote ≈31, MacBook ≈22, Camera ≈20, tool-swap (organic) ≈14, prompt-vs-finish ≈8, the rest ≈3.
  - Adjusting for audience: the **networking post is probably the single biggest contributor**. It is the only post whose viewers acted like the follower base: 33 distinct repliers, 24 likes, 20 visits, 13 follows. That base is 72% verified, and build-in-public networking circles are the likely source of those verified followers. Offsetting this, part of its 856 came from profile (pin) and conversation views, which aren't Home Timeline.
  - The **iPhone comparison (509)** looks like passive For You distribution to a general Apple audience: 1 like, 0 visits, 6 detail expands, posted 01:45 US Eastern. Its impressions were probably mostly Home Timeline, but its verified share is likely below average.
  - The three **settings threads (573 root impressions)** behave like the comparison: 3 likes, 0 root visits, 5 bookmarks.
  - Posts from 23–24 Sep (≈391 organic) may be partly missing if the screen lags like the export does.
- **Size of the in-network ceiling.** 26 verified followers × 11 posts ≈ 286 impressions, if every verified follower saw every post once on Home. The follower count was lower earlier in the week (33 on 22 Sep), so the real ceiling was lower still. The 337 is therefore about what verified followers alone could produce, plus a thin verified slice from out-of-network viewers. The data can't separate the two, but either way the number rests on a few dozen Premium viewers, not a broad Premium reach.
- **The likeliest explanation for the gap, in order of weight:**
  1. Most original impressions were out-of-network For You views, where the Premium share of viewers is low.
  2. On the networking post, some impressions came from surfaces other than Home (pin, conversation, notifications).
  3. A few hours of reporting lag on 23–24 Sep posts, worth roughly 1–3 points of the share.
  4. The paid Boost impressions (~2,006) are very likely excluded. If they counted, the share would be 7.8%, and 337 would be implausibly low given 26 verified followers.
- **Timing.** The best original (networking) was posted at 20:35 US Eastern on a Monday, which is 10:35 Brisbane on a Tuesday. But the 509-impression comparison went out at 01:45 US Eastern, so five posts with reach can't separate posting time from topic and format.

### Gaps
- The repo holds no per-post "verified impressions" or per-surface (Home vs profile vs conversation vs search) breakdown. Neither the API (organic/public/non-public metrics) nor the CSV has these columns. So which posts actually produced the 337 cannot be measured, only inferred.
- The eligibility metric's exact definition isn't documented in the repo. Open points: whether paid Boost impressions, quote posts and self-thread cards count; which timestamp window applies; the refresh cadence. Nor is any "50% visibility" impression rule documented; I found no local source for how X counts an impression (pixels visible or dwell time).
- The Premium share of X users in general, and of the Apple / Australia / builder audiences, isn't in the repo.
- The export has no "Shares" signal (all 0) and no copy-link data. Bookmarks from the API are totals, not organic (XAPI P7).
- The two 24 Sep originals are missing from the export and were 0.2–0.8 h old at the API read. They are not yet measurable.

## Q2. Replies and thread cards: reach, profile visits and follows (they don't count toward the 337)

### Takeaway
Replies drove 87% of the account's measured reach (14,220 organic impressions from 115 replies), but they converted poorly: 4 follows (0.3 per 1,000 impressions) against 13 follows from originals (6.3 per 1,000), all 13 from the networking post. None of the high-reach politics/news replies produced a follow. Three of the four reply follows came from low-reach networking replies to builders on 22 Sep.

### Cited Findings
- **By kind (API organic / X export).** — [SUM "Account" table](/Users/lukemckenzie/src/thread-engine/ledger/SUMMARY.md); [AUD](/Users/lukemckenzie/src/thread-engine/reviews/audit-2026-09.md); export columns computed from [ACT](/Users/lukemckenzie/src/thread-engine/ledger/activity/2026-09.json)

| Kind | Items | Organic impr. (API) | Impr. (export, rows present) | Profile visits | Likes | Visits per 1,000 | New follows (export) | Follows per 1,000 (export impr.) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Original | 9 | 2,097 | 2,080 (7 rows) | 21 | 31 | 10.0 | 13 | 6.3 |
| Quote | 2 | 232 | 229 | 0 | 1 | 0.0 | 0 | 0 |
| Reply | 115 | 14,220 | 13,117 (112 rows) | 33 | 60 (62 export) | 2.3 | 4 | 0.3 |
| Thread card | 31 | 933 | 930 | 4 | 12 (13 export) | 4.3 | 2 | 2.2 |
| **All** | 157 | 17,482 | 16,356 (152 rows) | 58 | 107 (export) | – | **19** | – |

- **Export totals (18–24 Sep, 152 rows):** 16,356 impressions, 449 engagements, 158 detail expands, 107 likes, 91 replies, 58 profile visits, 19 new follows, 7 bookmarks, 1 repost, 0 shares, 0 URL clicks. — computed from [CSV](/Users/lukemckenzie/src/thread-engine/loop/inbox/account_analytics_content_2026-09-18_2026-09-24.csv)
- **Where follows came from (export):** the networking post 13; a Wi-Fi thread card 1; a MacBook thread card 1; replies 4. The 4 reply follows: three on Tue 22 Sep between 09:57 and 10:28 Brisbane, each a reply in another account's builder or networking conversation, each with 6–39 impressions (one was the repeated "Would love to connect…" line); one on Thu 24 Sep, a government/politics reply with 46 impressions. — computed from [ACT `reads.export.new_follows`](/Users/lukemckenzie/src/thread-engine/ledger/activity/2026-09.json)
- **Reply reach is concentrated:** median 11 impressions per reply. The top 5 replies hold 66% of reply impressions (export), and the largest single reply had 3,878 organic (API) / 3,615 (export). The eight biggest replies (364–3,615 impressions in the export) were all posted Thu 24 Sep 04:00–10:00 Brisbane (Wed 23 Sep 14:00–20:00 US Eastern), on Australian politics/news and AI-industry threads. Together they brought 12 profile visits and 0 follows. — computed from [ACT](/Users/lukemckenzie/src/thread-engine/ledger/activity/2026-09.json)
- **Replies by US Eastern time:** 90 replies posted 09:00–21:00 ET earned 13,578 organic impressions (≈151 per reply), 31 visits and all 4 reply follows. 25 replies posted 21:00–09:00 ET earned 642 (≈26 per reply), 2 visits and 0 follows. Topic is confounded with time here: the politics burst fell in US afternoon. — computed from [ACT](/Users/lukemckenzie/src/thread-engine/ledger/activity/2026-09.json)
- **Replies in other accounts' conversations vs the account's own:** 107 replies elsewhere earned 13,007 impressions, 31 visits and 4 follows. 8 replies in its own conversations (7 of them under the networking post) earned 122 impressions, 2 visits and 0 follows. — computed from [ACT](/Users/lukemckenzie/src/thread-engine/ledger/activity/2026-09.json)
- **Replies by topic (the audit's hand classification):** Australian politics & news, 28 replies, 6,680 impressions, 15 visits (2.2 per 1,000). AI/coding/building, 29 replies, 2,331 impressions, 4 visits (1.7). Networking with builders, 32 replies, 422 impressions, 10 visits (**23.7 per 1,000**). Other banter, 26 replies, 4,787 impressions, 4 visits (0.8). — [AUD "Replies by topic"](/Users/lukemckenzie/src/thread-engine/reviews/audit-2026-09.md)
- **Risk flags on replies:** the same reply text went out 12 times in 3 minutes on 22 Sep, and "👋" alone 6 times. There were 68 replies in one 24-hour stretch. Duplicate reply text can be labelled `COPYPASTA_SPAM` (A13), and the reply spam scorer sees the replier's 24-hour reply count (A12). — [AUD §2](/Users/lukemckenzie/src/thread-engine/reviews/audit-2026-09.md); [XALG A12, A13](/Users/lukemckenzie/src/thread-engine/reference/x-algorithm.md)
- **Interaction graph:** API mentions show 62 replies to the account from 48 distinct accounts. The follow-credit map records 83 accounts the account replied to and 43 that replied to it. — computed from [RAW mentions](/Users/lukemckenzie/src/thread-engine/ledger/raw/api/backfill-20260924T0120.json); [interactions.json](/Users/lukemckenzie/src/thread-engine/loop/followers/interactions.json)
- **Thread cards:** 31 cards, 933 impressions, 4 visits, 2 follows. The two follows landed on a mid-thread card of the Wi-Fi thread (10 impressions) and of the MacBook thread (32 impressions). — computed from [ACT](/Users/lukemckenzie/src/thread-engine/ledger/activity/2026-09.json)

### Inferences
- Replies are the account's reach engine, but they add nothing to the 337 and very little to the follower count. Politics/news reach, in particular, lands with an audience that doesn't follow: the audit found 1 of 36 followers has a politics/news bio. For the eligibility targets, the reply reach mainly matters indirectly, through the few profile visits it sends to a profile whose pin and originals must then convert.
- Follows are driven by builder networking, whether it's a connect post or connect-style replies. That mechanism yields a Premium-heavy follower base (see Q3). It also runs into the voice guide's "Drop a hi" farm-tell ban and the duplicate-text risk, so any strategy that leans on it has to use specific, non-repeated interactions.
- The settings/comparison format produced 0 root follows and 0 root visits from 1,082 root impressions. Its only two follows came through thread cards.

### Gaps
- The export's "New follows" is gross. Unfollows per post are not recorded, so net follows per post are unknown.
- Whether reply-driven profile visits later turned into follows through the pinned post can't be seen. The export credits a follow to the post it was made from.
- The reply topic split comes from the audit's reading of reply text. I didn't re-classify it. The ≥364-impression replies I describe as "politics/news and AI-industry" from the account's own text.

## Q3. Verified share of the follower base and the reachable Premium audience

### Takeaway
X counts 26 verified followers out of 36 total, about 72%. That is far above what 337 verified impressions out of 2,329 (14.5%) implies for the viewers of the account's originals. The follower base, recruited mainly through builder networking, is heavily Premium. The out-of-network audience the originals reach mostly is not. I could not confirm the "27 of 36 by the API" figure from any repo file.

### Cited Findings
- Followers: 36 on 24 Sep 2026 01:52 UTC, the first recorded count. — [ACC](/Users/lukemckenzie/src/thread-engine/ledger/activity/account.json); [SUM](/Users/lukemckenzie/src/thread-engine/ledger/SUMMARY.md)
- Of those 36, one is the operator's own second account, listed as a `self_id`. The stored daily follower list therefore keeps 35 external follower IDs. — [FOL inbox](/Users/lukemckenzie/src/thread-engine/loop/inbox/followers.json); [followers-2026-09-24.json](/Users/lukemckenzie/src/thread-engine/loop/followers/followers-2026-09-24.json)
- Follower trajectory: 33 at the 22 Sep review, 34 at 23 Sep 19:10 UTC, 36 at 24 Sep 01:20 UTC. — [R22 line 13](/Users/lukemckenzie/src/thread-engine/reviews/2026-09-22.md); [LED snapshots `followers`](/Users/lukemckenzie/src/thread-engine/ledger/2101603601143803913.json)
- Verified followers: 26 of 500 per X's eligibility screen. — eligibility screen (brief)
- The API follower objects stored in the repo contain only `id` and `username`, with no `verified` or `verified_type` field. A search of the repo's data files for "verified" finds nothing. — [RAW `followers`](/Users/lukemckenzie/src/thread-engine/ledger/raw/api/backfill-20260924T0120.json)
- The only "27 of 36" in the repo is a bio-keyword count: "27 describe themselves as AI builders, developers, founders or indie hackers". Other bio counts: 2 Australian, 2 crypto, 1 creator, 1 politics/news, and 12 following more than twice as many accounts as follow them (a follow-back pattern). — [AUD "Who follows the account"](/Users/lukemckenzie/src/thread-engine/reviews/audit-2026-09.md); [AUDIENCE](/Users/lukemckenzie/src/thread-engine/reference/audience.md)
- Mutual-follow replies on an original get a +15 reply-weight boost. — [XALG A10](/Users/lukemckenzie/src/thread-engine/reference/x-algorithm.md)

### Inferences
- Verified share: 26/36 = **72%** (26/35 = 74% if the operator's second account isn't verified). If the "27 by the API" figure comes from a live read outside the repo, it gives 75%, which is consistent. The report should cite X's 26 as authoritative and treat 27 as unverified here. The one-follower difference could be timing, or the operator's own account.
- The Premium audience the account can reach reliably is small but dense: about 26 verified followers who see its originals in-network. Out-of-network reach so far has been mostly non-Premium, since 14.5% qualifying against 72% among followers.
- The builder-networking audience that produced 13 of 19 follows is where verified followers come from. Growing in that community should keep the verified share of new followers high. Broad device/Apple content widens reach but probably dilutes the verified share, and it brought no follows at the root.
- Since 12 followers show a follow-back pattern, some verified followers may be low-engagement follow-for-follow accounts. They count toward 500, but they may add little to Home Timeline engagement.

### Gaps
- There is no per-follower verified flag in the repo, so the "27 of 36 by the API" claim and the verified share of *new* followers per post can't be checked locally.
- The verified share of *viewers* per post isn't available anywhere in the repo.
- Whether the operator's second account (a follower) is verified is unknown.

## Q4. Pace needed vs current pace (500K qualified impressions and 500 verified followers in 90 days)

### Takeaway
Qualified impressions need about 61× the current pace: 5,556 a day, against about 91 a day. Verified followers need 36.9 a week. That is about 1.4× the pace of the one week that contained a viral networking post, and about 4.6× the pace without it. The impression target is the binding constraint by more than an order of magnitude.

### Cited Findings (all computed from the cited files and the brief's figures)
- **Measurement window:** first post 20 Sep 09:25 UTC; export downloaded 24 Sep ≈02:21 UTC; about 3.71 days of activity in total. — [RAW](/Users/lukemckenzie/src/thread-engine/ledger/raw/api/backfill-20260924T0120.json); [CSV file time]
- **Qualified impressions, current:** 337 in about 3.7 days, or **≈91 a day (≈640 a week)**. — eligibility screen (brief)
- **Qualified impressions, required:** 500,000 over 90 days is **5,556 a day (≈38,900 a week)**, 61× the current pace. Measured from the first post (target date ≈19 Dec 2026), the remaining 499,663 over about 86.3 days is ≈5,790 a day.
- **What that means for originals and quotes at today's 14.5% qualifying rate:** about 38,400 organic original+quote impressions a day (≈1.15M a month), against about 629 a day now (2,329 ÷ 3.7). At 2 originals a day, that is about 19,200 impressions per post, against today's median of 184 and best of 856 (eight posts with ≥12 h of data). — [ACT](/Users/lukemckenzie/src/thread-engine/ledger/activity/2026-09.json)
- **If the qualifying share rose to the follower base's 72%,** originals would still need about 7,700 organic impressions a day, about 12× today.
- **For scale, the account's total impressions including replies** were about 4,400 a day in the export (16,356 ÷ 3.7). Replies don't count toward the target.
- **Verified followers, required:** 500 − 26 = 474 in 90 days, which is **5.3 a day, or 36.9 a week**. At a 72% verified share of new followers, that is about 51 total new followers a week.
- **Verified followers, current:** the export credits 19 gross new follows in 3.7 days, about 36 a week. 13 of those came from one networking post within about a day. Excluding it, the pace is about 11 a week (6 follows). At 72% verified, that is about 26 verified a week gross, or about 8 a week without the networking post. The raw follower count rose 33 → 36 from 22 Sep to 24 Sep 01:20 UTC, about 12 a week. — [ACT](/Users/lukemckenzie/src/thread-engine/ledger/activity/2026-09.json); [R22](/Users/lukemckenzie/src/thread-engine/reviews/2026-09-22.md); [LED snapshots](/Users/lukemckenzie/src/thread-engine/ledger/)
- **Cold-start ceiling:** the small-author lift applies only below 1,000 followers and 1,000 home views per post (A5). A post that must reach about 19,000 impressions would pass through and beyond that window. — [XALG A5](/Users/lukemckenzie/src/thread-engine/reference/x-algorithm.md)
- **Data expiry:** X deletes per-post organic metrics 30 days after posting, so the 20 Sep posts lose theirs around 20 Oct. — [AUD Appendix](/Users/lukemckenzie/src/thread-engine/reviews/audit-2026-09.md); [XAPI P6](/Users/lukemckenzie/src/thread-engine/reference/x-api.md)

### Inferences
- The verified-follower target is within reach of a sustained networking-led growth rate: roughly one networking-post-sized win per week plus steady specific replies to builders. The Home Timeline impression target is not within reach through incremental gains on today's formats. It needs originals that repeatedly break out of the cold-start band to tens of thousands of impressions, delivered to a Premium-dense audience, or a much larger verified follower base generating in-network Home impressions (each verified follower seeing ~2 originals a day adds about 60 qualifying impressions a month).
- Even 500 verified followers each seeing every original (2 a day) would give only about 1,000 qualifying impressions a day. So the target also needs out-of-network reach to Premium viewers, not just followers.
- The weekly averages above rest on 3.7 days and one outlier post. A second week of data could move the follower pace by ±50%.

### Gaps
- There is no time series of the eligibility screen's figures in the repo. Qualified-impression pace can only be computed from one reading, whose timestamp is unknown.
- There is no history of verified-follower counts, so the verified share of new follows can't be tracked.
- Net follower change per day starts only with the next daily read ([ACC `baseline: true`](/Users/lukemckenzie/src/thread-engine/ledger/activity/account.json)). Unfollows are unknown.
- The follower count before 20 Sep (before the first post) isn't recorded, so how many of the 36 predate posting can't be separated from the export's 19 attributed follows. At most 17 are unattributed or predate posting.
