# Creator and analyst evidence: what drives verified Home Timeline impressions and verified followers on X (2026)

Researched 2026-09-24. Sources: web search and fetch, plus 8 read-only X searches through `scripts/x_read.py` (about $0.64 in total).

Ratings used on every claim:
- **[Official]**: X Help Center, an @XCreators post, or a named X staff member, as reported. This is a statement, not measured data.
- **[Code]**: X's open-source ranking code, as recorded in `reference/x-algorithm.md` (xai-org/x-algorithm, commit 1b3fec2, checked 2026-09-24).
- **[Data]**: a dataset of many accounts or posts with a stated sample.
- **[Anecdote]**: one creator reporting their own account.
- **[Opinion]**: an assertion with no data behind it.
- **[Grok]**: an @grok reply found on X. Grok is not X policy. Treat these as unverified.
- **[Interest]**: the source sells a growth, scheduling or analytics tool.
- **PRIOR**: from before 2026, or about the retired Creator Revenue Sharing program.

X search provenance and a reliability warning:
- Query "verified followers 500 how" failed. Grok's own error text says it "emitted a schema-shaped reply without tool output". Nothing from it is used here.
- Query "original content rewards payout" returned three posts that look fabricated. Their ids have sequential digit patterns (2102145678901234567, 2102098765432109876, 2101987654321098765). Their handles are @creatorpayouts, @threadlab and @exitmetrics. One claims "$42 for a thread". These are excluded. A single-call Grok search can therefore invent posts that pass the JSON schema. Treat any post id from `x_read.py` as unconfirmed until its thread has been fetched.
- The query "for you reach premium" returned mostly unrelated posts. One relevant post (@sidchhaya) is used.

## Q1. What creators report since Original Content Rewards launched: verified Home Timeline impressions against total impressions, what moved them, how long 500K / 500 took, and whether the progress bar lags

### Takeaway
The rules are clear and official. The practitioner numbers are thin. The only figures for the verified share of total impressions are 3–10% from an early summary and 4–20% from tool vendors, with no clean dataset behind either. The 500K threshold is a rolling 90-day window, so an account needs about 5,556 verified Home Timeline impressions a day, sustained. The creator progress reports found on X range from 7.5K to 364K out of 500K. No creator gave a dated start-to-500K timeline. Reports of a stuck or lagging progress bar exist. The only explanation found is Grok's ("batches"), and X has not confirmed it.

### Cited Findings
**Program rules [Official]**
- X announced the Original Content Rewards Program on 7 Aug 2026 to replace Creator Revenue Sharing. New revenue-share enrolments stopped on 7 Aug, existing members earned through 7 Sep, applications opened 8 Sep, and the first payment is 25 Sep 2026. — [TechCrunch, 8 Aug 2026](https://techcrunch.com/2026/08/08/x-replaces-misaligned-revenue-sharing-program-with-original-content-rewards/); [X Help: Original Content Rewards](https://help.x.com/en/using-x/original-content-rewards) (returned 403 to fetch, so the details come from the secondary reports cited here); [@XCreators announcement](https://x.com/XCreators/status/2085835082166653393)
- Eligibility:
  - an active Premium, Premium+ or Premium Business subscription
  - age 18 or over
  - an eligible country
  - at least 500 verified followers
  - at least 500,000 Home Timeline impressions from verified users in the last 90 days, with reply impressions excluded

  Sources: [Influencer Marketing Hub, Chloe West, 11 Aug 2026](https://influencermarketinghub.com/x-is-turning-creator-monetization-into-an-originality-test/); [TechCrunch](https://techcrunch.com/2026/08/08/x-replaces-misaligned-revenue-sharing-program-with-original-content-rewards/)
- A qualified impression is a "unique Home Timeline impression from Premium users, with at least half of the post visible". Paid, fraudulent and artificially generated impressions are excluded. — [Influencer Marketing Hub](https://influencermarketinghub.com/x-is-turning-creator-monetization-into-an-originality-test/)
- X executive Allegra Jacchia said the old program's "incentives were misaligned" and that "creators should be focused on bringing net new content to the platform instead of maximizing payouts." — [TechCrunch](https://techcrunch.com/2026/08/08/x-replaces-misaligned-revenue-sharing-program-with-original-content-rewards/)
- Payouts are every two weeks with a $30 minimum. There is "no official fixed RPM". Australia is listed as an eligible country. A rejected application gets one appeal, and reapplying is possible after 42 days. — [Tech2Geek, 23 Sep 2026](https://www.tech2geek.net/x-original-content-rewards-program-eligibility-payouts-and-rules/) (secondary guide)
- Views on replies and views from profile visits do not count. Only views of your posts in the For You and Following feeds from verified users count. — [@SawyerMerritt restating the X rules, Aug 2026](https://x.com/SawyerMerritt/status/2085917567722684921) (secondary, consistent with the official wording)
- The count is a rolling 90-day window. Several creators asked why their totals dropped: old days fall out of the window. — [@lalitgrateful, Aug 2026](https://x.com/lalitgrateful/status/2086726284327993553) [Opinion/explainer]
- Applicants submit 10 original posts for review. — [X trending summary "X Shifts Creators to Original Content Rewards Program"](https://x.com/i/trending/2096915916353319381). This is an AI-generated trend summary, **unverified**.
- Review takes 3 business days. — [@grok, 5 Sep 2026, id 2096231992169754837](https://x.com/grok/status/2096231992169754837) [Grok, unverified]

**Verified share of total impressions**
- X added a "Verified" filter to account analytics around 8 June 2026. It shows impressions and engagements from verified accounts over periods such as 7 days, along with a verified follower count. Early checks put verified figures at "just 3–10% of totals for some". — [X trending summary "X Adds Verified Filter to Account Analytics"](https://x.com/i/trending/2064093715371631083) (AI-written trend summary; the page returned 402 to fetch, so this was seen only as a search snippet) [Opinion/aggregated anecdote, weak]
- Tool and calculator sites put the verified share at 4–12% or 5–20% of total impressions. One example: 400K paying impressions out of 3M on a viral post, about 13%. — search snippets from [OpenTweet](https://opentweet.io/tools/x-earnings-calculator), [ClimbX](https://climbx.so/tools/how-much-does-x-pay), [Grey Journal](https://greyjournal.net/hustle/how-much-does-x-pay-creators-2026/) [Opinion, Interest: all three sell or promote X tools; no methods given]
- A contradicting source says the ratio cannot be computed from public analytics. It says "Anyone quoting you a conversion percentage either measured it on one account ... or made it up", and advises using your own payout history per post. — [Versely, 20 Aug 2026, updated 17 Sep](https://www.versely.studio/blog/x-qualified-impressions-what-actually-pays) [Opinion, Interest: sells AI video and caption tools]. The claim is partly superseded: the June Verified analytics filter shows verified impressions. It may not apply the Home-only, unique-viewer and 50%-visible filters, and no source confirms whether it does.

**Progress reports from creators (X search, September 2026)**
- @Ajithkumar4ak (24 Sep): "Today, it increased by only 1.6K. Verified Home Timeline impressions." — [id 2102943487612379158](https://x.com/Ajithkumar4ak/status/2102943487612379158) [Anecdote]
- Grok told one user they were at 7.5K out of 500K and should keep posting original content. — [@grok, 24 Sep, id 2102943949442650475](https://x.com/grok/status/2102943949442650475) [Grok]
- @DeFi_G_ (24 Sep), a solo founder building in public: "I'm at 12.5K / 500K impressions needed … a like, repost, or follow helps more than you know." — [id 2102949204331000127](https://x.com/DeFi_G_/status/2102949204331000127) [Anecdote. This is also an example of the repeated-CTA pattern the program rules warn about; see Q3.]
- @TooLateClub (31 Aug): "364K / 500K … a progress bar that refuses to move." — [id 2094381274278318312](https://x.com/TooLateClub/status/2094381274278318312) [Anecdote]
- @UrwatuSuleiman (12 Sep): "Don't trust the views under a post. Open Creator Studio → Original Content Rewards. That progress bar is the number that actually matters." — [id 2098760699358937158](https://x.com/UrwatuSuleiman/status/2098760699358937158) [Opinion]
- @AbuZ8Studios (23 Sep): "Anyone who 'monetized X in 16 days' was on the old program … Replies do not count. Copy originals with media, not reply-spam." — [id 2102878882466582682](https://x.com/AbuZ8Studios/status/2102878882466582682) [Opinion. The account posts about AI tooling.]
- A creator was rejected despite writing Articles and running live streams about stocks, and has appealed (23.5K views, 86 replies). — [@ThePPseedsShow, 9 Sep, id 2097759945563259386](https://x.com/ThePPseedsShow/status/2097759945563259386) [Anecdote: approval is a human or model judgement, not automatic on reaching the thresholds]
- One post claims the bar is "5K verified ✅ 5M verified Home Timeline impressions". That contradicts every official source, which say 500 and 500K. It reads as a joke or confusion with the old 5M bar. — [@zerobarkthirty, 14 Sep, id 2099532900492324991](https://x.com/zerobarkthirty/status/2099532900492324991) [Unreliable, do not use]

**Progress bar lag**
- Grok: the progress bar "often lags behind post stats as data processes in batches". It counts only verified Home Timeline impressions on original posts, not total views. — [@grok, 14 Sep, id 2099484004915278203](https://x.com/grok/status/2099484004915278203) [Grok, unverified]
- The bar is in Creator Studio → Original Content Rewards. It shows a progress bar below 500K and a tick once the requirement is met. — [@monetization_x, 6 Sep, id 2096709627899494817](https://x.com/monetization_x/status/2096709627899494817) [Anecdote/UI report]

**Rates (PRIOR program)**
- Grok says creators on the old program reported "roughly $8–12 per million verified impressions". — [@grok, 23 Sep, id 2102865241415582169](https://x.com/grok/status/2102865241415582169) [Grok, unverified]

### Inferences
- A rolling 90-day window means an account at a steady daily rate tops out at that rate × 90. Reaching 500K needs a sustained average of about 5,556 verified Home Timeline impressions a day, or one or more posts that break out. At 1.6K a day (@Ajithkumar4ak) the window tops out near 144K and never reaches 500K. This is arithmetic from the official rule, not a creator report.
- If the verified share really is 3–13% of total impressions (weak evidence), 500K verified needs roughly 4M–17M total impressions on originals in 90 days. That is the same order as the old 5M bar. The new threshold has moved rather than dropped.
- The progress reports visible on X (7.5K, 12.5K, 364K) suggest most small accounts chasing the program are far from the bar. This is a skewed sample: people post about being stuck, not about passing.
- Treat the Creator Studio progress bar as the source of truth. Post-level "views" include replies, profile views and non-Premium viewers.

### Gaps
- No creator gave a dated account of how long it took to reach 500K verified impressions or 500 verified followers under the new program. The program is 7 weeks old, and approvals only began on 8 Sep.
- No official X statement on how often the progress bar updates or whether it lags.
- No multi-account dataset of verified to total impression ratios. The 3–10% figure comes from an AI trend summary. The vendor ranges have no stated method.
- First payouts land 25 Sep 2026, the day after this research, so there are no creator reports of new-program payout per qualified impression yet. The three "payout" posts returned by X search were fabricated and excluded.
- The X Help page returned 403, so the official wording was only read through secondary reports.
- The X search for "verified followers 500" failed and was not re-run because of the 8-query budget.

## Q2. Which post types, posting frequencies and posting times earn Home-timeline reach from Premium users, and how a Brisbane account should time posts for a US-heavy Premium audience

### Takeaway
Only the root of a thread can count: replies, including your own thread replies, are excluded, and For You shows one post per conversation. X staff are pushing original talking-head video and long-form writing (Articles). Multi-account engagement data still favours text and images over video and links, but it measures engagement rate, not Premium Home-timeline reach. X says links are no longer deboosted and that their low reach is low engagement. No 2026 evidence was found on polls. Posting-time studies measure engagement in the poster's local time. For a US Premium audience, a Brisbane account's usable window is about 10 pm to 8 am Brisbane, Tuesday night to Friday morning.

### Cited Findings
**Threads and replies**
- Replies are excluded from the 500K threshold. Views of your replies under a post do not count. — [Influencer Marketing Hub](https://influencermarketinghub.com/x-is-turning-creator-monetization-into-an-originality-test/); [@SawyerMerritt](https://x.com/SawyerMerritt/status/2085917567722684921) [Official, restated]
- For You keeps one post per conversation, the best-scoring one. Replies from accounts the viewer does not follow are filtered out. — `reference/x-algorithm.md` A1 and A2 [Code]
- "Bumping your own post, replying to keep it alive, and re-quoting yourself" generate repeat views from accounts that already saw the post, and repeat views fail the unique-viewer filter. — [Versely](https://www.versely.studio/blog/x-qualified-impressions-what-actually-pays) [Opinion, Interest]
- Official and Grok summaries list "threads" among eligible original content. — [@grok, 13 Sep, id 2099191861424373783](https://x.com/grok/status/2099191861424373783) [Grok]. This does not contradict the root-only reading: the thread qualifies as original content, but only its root is a non-reply post.
- Graham Mann says short threads of 3–6 posts work and threads of 15 or more are "dead". — [grahammann.net, Feb 2026](https://grahammann.net/blog/how-to-grow-on-x-twitter-2026) [Anecdote/Opinion, Interest: sells SEOTakeoff and recommends the paid tools SuperX and Typefully]
- An Indie Hackers post says threads of 4–8 posts are best. It cites a better hook taking the same content from 33K to 624K views, an example attributed to Prof. Lennart Nacke. — [Indie Hackers, Farid Shukurov, 8 Jun 2026](https://www.indiehackers.com/post/the-2026-x-growth-system-how-top-creators-engineer-virality-with-threads-replies-quote-posts-66200ecdc5) [Anecdote, Interest: promotes SupaBird, an AI X-growth tool]

**Articles and long posts**
- X offered $1M to the most popular Article of a payout period, "judged primarily on Verified Home Timeline impressions". Entries had to be original, at least 1,000 words, from US Premium users only. X said: "We're doubling down on what creators on 𝕏 do best: writing." — [Social Media Today, 17 Jan 2026](https://www.socialmediatoday.com/news/x-formerly-twitter-offers-million-dollar-prize-best-article-long-form-post/809930/) [Official]
- "Articles made up 5 of the 11 best-performing posts – 45% of top performers." Long-form single posts get "40–60% more impressions than comparable thread content." — [Indie Hackers/SupaBird](https://www.indiehackers.com/post/the-2026-x-growth-system-how-top-creators-engineer-virality-with-threads-replies-quote-posts-66200ecdc5) [Anecdote, sample undisclosed, Interest]
- Contrary view: "it's not great content that earns rewards on X, it's little quips … Spend a period posting original articles and you'll probably see it go down." — [@thjonml, 12 Sep, id 2098784058121797656](https://x.com/thjonml/status/2098784058121797656) [Opinion]

**Native video**
- Nikita Bier, 12 Apr 2026: "People should make more talking videos like this on X. Easy way to get millions of impressions with basically no followers." — [PiunikaWeb, 13 Apr 2026](https://piunikaweb.com/2026/04/13/x-twitter-original-talking-videos-nikita-bier/) [Official staff opinion, no data]
- Bier also said reposted or third-party network content faces up to a 90% deduction on impressions, and that "Copy-and-paste jobs that add zero unique commentary just steal impressions from the real creators." — [PiunikaWeb](https://piunikaweb.com/2026/04/13/x-twitter-original-talking-videos-nikita-bier/) [Official, as reported]
- Video gets "roughly 10x the engagement of text-only posts." — [grahammann.net](https://grahammann.net/blog/how-to-grow-on-x-twitter-2026) [Opinion, no source, Interest]. This is contradicted by the Buffer data below.

**Text, images, video and links (engagement rate, not reach)**
- Median engagement rate on X by format: text 3.56%, images 3.40%, video 2.96%, links 2.25%. — [Buffer, "Best Content Format on Social Platforms in 2026: 45M+ posts"](https://buffer.com/resources/data-best-content-format-social-media/) [Data, Interest: Buffer sells scheduling. The sample and date range for X are not stated. Engagement rate is a different measure from verified Home-timeline reach.]
- Multi-image posts are outperforming text-only posts. — [grahammann.net](https://grahammann.net/blog/how-to-grow-on-x-twitter-2026) [Anecdote, Interest]
- No rule penalising AI-made images was found in the ranking code. Media marked DMCA is dropped. — `reference/x-algorithm.md` A15 [Code]

**Links**
- Bier told the Vatican account on 31 May 2026 that links do not reduce reach. On 29 Jul 2026 he told Mark Zuckerberg the link penalty was removed "over a year ago". — [Yahoo Tech](https://tech.yahoo.com/social-media/articles/x-debunks-popular-engagement-myth-192804752.html); [Free Press Journal](https://www.freepressjournal.in/tech/x-product-head-nikita-bier-confirms-link-penalty-removed-over-a-year-ago-tells-mark-zuckerberg-he-can-post-them-directly) [Official]
- Bier attributes lower link reach to "lower engagement", because the in-app browser covers the post. X tested a new link experience on iOS in Oct 2025 (PRIOR). — [@nikitabier, Oct 2025](https://x.com/nikitabier/status/1979994223224209709); [Nieman Lab, Oct 2025](https://www.niemanlab.org/2025/10/x-makes-overtures-to-journalists-with-new-feature-designed-to-improve-reach-for-links/)
- Many 2026 growth blogs still say links are "heavily deboosted" (for example, search snippets from [SocialRails](https://socialrails.com/blog/how-to-grow-on-twitter-x-complete-guide)) [Opinion]. This is contradicted by X staff.

**Quote posts and polls**
- X recommends the "Share Video or Quote feature to ensure your posts are properly attributed" when adding commentary to someone else's content. X now reallocates impressions from aggregator reuploads to the original creator. — [Social Media Today, 25 May 2026](https://www.socialmediatoday.com/news/x-looks-to-improve-its-incentives-for-original-creators/821051/) [Official]
- The quote weight (5) equals the reply weight (5) and is 10× the like weight (0.5). — `reference/x-algorithm.md` A9 [Code]
- Recommended mix: about 10% of daily activity as quote posts. — [Indie Hackers/SupaBird](https://www.indiehackers.com/post/the-2026-x-growth-system-how-top-creators-engineer-virality-with-threads-replies-quote-posts-66200ecdc5) [Opinion, Interest]
- Polls: no 2026 source found.

**Posting frequency**
- Bier, Jan 2026: average users view only 20–30 posts a day, so accounts that spend that attention on "gm" posts and low-value replies bury their own announcements. — [X trending summary](https://x.com/i/trending/2009783301498708004?lang=en); [Yahoo Finance](https://finance.yahoo.com/news/x-turning-away-crypto-nikita-145836959.html) [Official, as reported]
- Same-author posts in one feed request are scaled 1.0, 0.625, 0.44 and down to 0.25. There is no time rule. — `reference/x-algorithm.md` A11 [Code]
- Recommended volume:

  | Source | Posts a day | Replies a day |
  |---|---|---|
  | [Graham Mann](https://grahammann.net/blog/how-to-grow-on-x-twitter-2026), 0–1K followers | 3–5 | 20–30 |
  | [Graham Mann](https://grahammann.net/blog/how-to-grow-on-x-twitter-2026), 1K–10K followers | 5–10 | 30–50 |
  | [Indie Hackers/SupaBird](https://www.indiehackers.com/post/the-2026-x-growth-system-how-top-creators-engineer-virality-with-threads-replies-quote-posts-66200ecdc5) | 3–5, "new mix" 8 | not stated |

  Graham Mann's own numbers: 40–60 posts plus replies a day gave 7–8 new followers a day in Jan–Feb 2026 [Anecdote, Interest]. The Indie Hackers figures are [Opinion, Interest].

**Posting time**
- Best days: Wednesday, then Tuesday and Thursday. Best hours: 9–11 am on weekdays. Evenings (6–11 pm) have the lowest engagement. Saturday is worst. All times are the poster's local time. — [Buffer, "8.7 million tweets"](https://buffer.com/resources/best-time-to-post-on-twitter-x/) [Data, Interest. The page title says "1 Million Posts Analyzed" and the body says 8.7M tweets, and that inconsistency is unresolved. It measures engagement rate, not verified reach.]
- Best window: 12–6 pm Tuesday to Thursday, based on about 2 billion engagements between 27 Nov 2025 and 27 Feb 2026. — [Sprout Social](https://sproutsocial.com/insights/best-times-to-post-on-twitter/) (search snippet; page not fetched) [Data, Interest]
- Recommendation candidates older than 48 hours are dropped. Originals from small authors (1,000 followers or fewer) have their own retrieval index with a 24-hour window and a cold-start lift while they are young and under 1,000 home views. — `reference/x-algorithm.md` A4, A5, A7 [Code]

### Inferences
- **Threads:** only the root earns counted impressions (replies are excluded, and For You serves one post per conversation). A thread's reach for this program is its root's reach. Later cards add reading value and can earn follows, but no qualifying impressions.
- **Timing studies:** Buffer's "9–11 am local" is the poster's local time, normalised across posters. It says nothing about when a US Premium audience is online for a Brisbane poster. Map US windows to Brisbane (AEST, UTC+10, no daylight saving). US daylight saving ends Sunday 1 Nov 2026, which shifts every US-mapped time one hour later in Brisbane.

  | US window | Brisbane now (to 31 Oct 2026) | Brisbane from 1 Nov 2026 |
  |---|---|---|
  | 9 am ET | 11 pm same day | midnight |
  | 12 pm ET / 9 am PT | 2 am next day | 3 am next day |
  | 3 pm ET / 12 pm PT | 5 am next day | 6 am next day |
  | 6 pm ET | 8 am next day | 9 am next day |

  To hit US Tuesday to Thursday, post between Tuesday night and Friday morning Brisbane time. For a no-code operator, the practical slots are about 10–11 pm Brisbane (US East morning) or about 5–7 am Brisbane (US afternoon, UK late evening). The early-morning slot keeps a small post inside its 24-hour small-author window through the rest of the US day and the Australian day. Treat this as a hypothesis to test in the loop, not a finding.
- **Frequency:** the author-diversity scaling (A11) and Bier's attention-budget remarks both point the same way for a small account: a few strong originals a day rather than many. The 3–5 a day volumes from tool vendors are opinion.
- **Video:** Bier's talking-video claim is the strongest official hint that a format has reach for accounts with few followers. No data backs it, and it conflicts with Buffer's engagement-rate ranking. It is worth an experiment, not a rule.

### Gaps
- No dataset compares verified Home-timeline impressions by format (text, image, video, Article, poll). All format data is engagement rate on total reach.
- No data on the geography of Premium subscribers, so the premise of a "US-heavy Premium audience" is unmeasured.
- No 2026 evidence on polls.
- No creator reported whether Articles count toward the 500K as a single post with full weight. The official lists include Articles, but whether an Article impression means a card view or a read is not stated.
- Whether quote posts count as "original" for the program depends on "meaningful transformation". No creator reported how quote-post impressions show in the progress bar.

## Q3. How small accounts grow verified followers, and what counts as engagement farming and gets penalised

### Takeaway
The best evidence for gaining verified followers is still thoughtful replies to Premium users and larger accounts in your niche. Reply impressions don't count toward the 500K, but replies earn follows, and X's July 2026 change boosts mutuals in reply sections. Farming is explicitly defined for the program: repeated calls to like, repost, reply, bookmark or follow; automated engagement; posts teaching people how to game payouts; Community-Noted posts; and copied or reuploaded content. X staff describe "gm" and template replies as ranked like spam. No 2026 data was found on Communities, mutual-follow networks or collaborations.

### Cited Findings
**Replies**
- @sidchhaya (23 Sep 2026): "Don't stop replying just because replies no longer count toward Premium timeline impressions. If a Premium user's post … interests you, reply with a reasoned two or three or more lines … I gained 13 new Premium followers in the last 24 hours with t[his]." — [id 2102736605039776235](https://x.com/sidchhaya/status/2102736605039776235) [Anecdote]
- Graham Mann says "12K impressions from one reply. 7 profile visits" against about 400 impressions on one of his own original posts. He recommends 30 minutes a day replying to larger niche accounts within 30 minutes of their post, and says "one good reply on a viral tweet can drive more profile visits than five of your own posts." — [grahammann.net, Feb 2026](https://grahammann.net/blog/how-to-grow-on-x-twitter-2026) [Anecdote, Interest]
- Indie Hackers/SupaBird recommends that 60% of replies go to larger accounts (10K–500K followers), within 15–30 minutes. — [Indie Hackers/SupaBird](https://www.indiehackers.com/post/the-2026-x-growth-system-how-top-creators-engineer-virality-with-threads-replies-quote-posts-66200ecdc5) [Opinion, Interest]
- Grok: reply prioritisation for Premium "still helps small accounts … can drive follows and later engagement on your original posts … Pure reply farming won't qualify you." — [@grok, 23 Sep, id 2102755511271653573](https://x.com/grok/status/2102755511271653573) [Grok]
- The reply spam scorer sees the replier's reply count for the last 24 hours and whether the reply was pasted. Duplicate reply text can be labelled `COPYPASTA_SPAM`, and Premium gives no exemption. — `reference/x-algorithm.md` A12, A13 [Code]

**Mutuals**
- 13 Jul 2026: X changed the algorithm to show more posts from mutuals. Bier said: "We noticed this data was missing from the algo and it made your friends appear less in your replies." The aim is to help interest clusters form. — [TechCrunch, 13 Jul 2026](https://techcrunch.com/2026/07/13/x-just-tweaked-its-algorithm-to-make-it-more-friendly-less-battleground/) [Official]
- A reply from a mutual follow on an original post gets +15 on the reply weight. — `reference/x-algorithm.md` A10 [Code]

**What counts as engagement farming (Original Content Rewards rules)**
- Content that encourages users to like, repost, reply, bookmark or follow "solely to increase engagement" may lose payout eligibility. Posts teaching others how to maximise program payouts are excluded. — [Complex](https://www.complex.com/pop-culture/a/markelibert/x-original-content-rewards-program-creator-payouts) [Official, as reported]
- Automated engagement tools and repeated calls to action for likes or shares are prohibited. Posts that receive Community Notes are ineligible. — [Influencer Marketing Hub](https://influencermarketinghub.com/x-is-turning-creator-monetization-into-an-originality-test/) [Official, as reported]
- "Occasional calls to action aren't necessarily the same thing as systematic engagement manipulation." Violations can mean temporary suspension or permanent removal from the program. — [Tech2Geek](https://www.tech2geek.net/x-original-content-rewards-program-eligibility-payouts-and-rules/) [secondary]

**What X staff say gets penalised**
- Bier, Jan 2026: "If it's just replying gm or cashtagging a coin with no relevance to the parent post, it will eventually be ranked no better than spam." Discussion that people actually read is "net good". — [@nikitabier, id 2010034260292579807](https://x.com/nikitabier/status/2010034260292579807) [Official]
- Bier, Apr 2026: X will "assign a permanent deduction to habitual bait posters who use 'BREAKING' on every post". Aggregator payouts were cut to 60%, with a further 20% cut planned. — [Social Media Today, 12 Apr 2026](https://www.socialmediatoday.com/news/x-boosts-incentives-for-original-content-creators/817271/) [Official]
- Pinning a post whose link is rated low-quality labels the account `SPAM_HIGH_RECALL` for a week. — `reference/x-algorithm.md` A14 [Code]
- The weights for negative signals are large: report −234, mute −58.8, not interested −43.2, block −31.2. — `reference/x-algorithm.md` A9 [Code]

**Farming patterns seen in the wild (September 2026)**
- @DeFi_G_ asked for "a like, repost, or follow" to reach 500K. — [id 2102949204331000127](https://x.com/DeFi_G_/status/2102949204331000127)
- @HeyDhruvv promoted a person who "helped lot people to cover up their verified impressions and made them eligible for original content rewards". This suggests follow-train or pod activity, but it is ambiguous. — [id 2102830038269952309](https://x.com/HeyDhruvv/status/2102830038269952309) [Anecdote/Opinion]

**Build in public**
- Expected result from consistent building in public: 500–5,000 followers in the first 12 months. "The build-in-public crowd on X … is overwhelmingly other builders, not buyers." — search snippets from [FounderDistro](https://www.founderdistro.com/blog/build-in-public-x-twitter-guide) and [BoilerplateHub](https://boilerplatehub.com/blog/build-in-public-2026) [Opinion, Interest: both are tool or launch-service sites. Not fetched.]

### Inferences
- Verified followers come mainly from Premium users who see you. Your replies in their conversations reach them even though reply impressions don't count toward the 500K. The strongest pattern across the anecdotes is multi-line, specific replies to Premium users in the niche. The 13-in-24h and 12K-impression reports are single-account and should not be used as expected rates.
- Asking for likes, reposts or follows to reach 500K is the pattern the program names. A small account that does it risks both ranking and later approval. The exitzerocode voice rules already ban "your thoughts" and 💬 prompts, which fits these rules.
- The mutuals change (Jul 2026) plus the +15 mutual reply weight in code make real in-niche mutual follows worth more than raw follower count. That supports reciprocal relationships with a handful of AI and builder accounts over follow-for-follow trains.

### Gaps
- No 2026 data on X Communities as a growth channel, on follow-train or "verified mutuals" networks, or on collaborations such as co-written threads.
- No data on the conversion rate from reply impressions to verified follows.
- The build-in-public numbers are unsourced vendor claims. The DEV Community post "Building in Public in 2026: has the strategy been gamed" was not read.

## Q4. Lessons from the 2023–2025 revenue-sharing era that still transfer (all PRIOR)

### Takeaway
The old program moved from paying on ads served in replies (2023) to paying on engagement from Premium users (late 2024). By January 2026 replies no longer counted, and the April–May 2026 changes penalised aggregators before the Original Content Rewards reset. Three lessons carry over: optimise for Premium viewers, originals outrank replies and reposts for counted reach, and engagement bait was already being clawed back. Two widely repeated heuristics come from 2023 code and should not be relied on: the Premium 4×/2× boost and "an author reply is worth 150× a like".

### Cited Findings
- PRIOR: the old eligibility was 5M organic impressions in 3 months plus 500 verified followers. — [xpayoutcalculator eligibility page](https://www.xpayoutcalculator.com/eligibility/) (search snippet) [secondary, Interest: calculator site]; [X Help: Creator Revenue Sharing](https://help.x.com/en/using-x/creator-revenue-sharing)
- PRIOR (Oct–Nov 2024): X changed payouts to be based on engagement from Premium users (replies, likes, bookmarks, time spent) instead of ad impressions in replies. Creators reported checks two to three times larger. — [@premium announcement, Nov 2024](https://x.com/premium/status/1855026854681624761); [Influencer Marketing Hub, revenue-sharing guide](https://influencermarketinghub.com/x-twitter-ads-revenue-sharing/) (search snippet) [Official for the change; Anecdote for the 2–3× claim]
- PRIOR: under the ad-based model, creators reported about $10–20 per million impressions. — [LifeMathMoney, with screenshots](https://lifemathmoney.com/how-much-does-x-pay-creators-x-creator-ads-revenue-sharing-income/) (search snippet) [Anecdote]
- Jan 2026 (transition): replies stopped counting toward earnings, and only Home-timeline impressions from verified users counted. — [@chapps_h, Jan 2026](https://x.com/chapps_h/status/2013755362487230735); [@MrMakiri, Jan 2026](https://x.com/MrMakiri/status/2013017427513369052?lang=en) [Anecdote/explainer]
- Mar–May 2026 (transition): Musk reversed some payout changes in March after creator backlash. — [TechCrunch](https://techcrunch.com/2026/08/08/x-replaces-misaligned-revenue-sharing-program-with-original-content-rewards/) In April, aggregator payouts were cut and Bier said X was "rewarding the effort it takes to produce something, not just the poster who helped it travel furthest". — [Social Media Today, 12 Apr 2026](https://www.socialmediatoday.com/news/x-boosts-incentives-for-original-content-creators/817271/) In May, impressions on programmatic reuploads were reallocated "entirely to the creator". — [Social Media Today, 25 May 2026](https://www.socialmediatoday.com/news/x-looks-to-improve-its-incentives-for-original-creators/821051/) [Official]
- PRIOR heuristics still quoted in 2026 guides: "Premium subscribers get a 4x visibility lift in-network and 2x out-of-network", and "a reply that gets a response from the author is worth up to 150× a like". — [Indie Hackers/SupaBird, Jun 2026](https://www.indiehackers.com/post/the-2026-x-growth-system-how-top-creators-engineer-virality-with-threads-replies-quote-posts-66200ecdc5) [Opinion, Interest]. The 2026 open-source defaults recorded in `reference/x-algorithm.md` A9 show reply 5 against like 0.5, which is 10×. That file lists no author-reply weight and no Premium multiplier. These heuristics trace to the 2023 twitter/the-algorithm release and are not confirmed in the 2026 code.
- Sep 2025 (PRIOR): Bier, reviewing accounts that complained about declining reach, called them "the worst Linkedin/AI/threadboy spam I've seen in my life" and said "algorithm is working as expected 👍". — [@nikitabier, id 1965800163269919203](https://x.com/nikitabier/status/1965800163269919203) [Official staff opinion]

### Inferences
- Lessons that transfer: the paying audience is Premium users, so content that verified users stop on and engage with is the target. Replies build the audience but never counted after Jan 2026. Originality enforcement tightened step by step through 2026, so any tactic built on reposts or aggregation is on borrowed time.
- Heuristics that do not transfer: the 5M bar, reply-count payouts, "150× author reply" and "Premium 4×/2× boost". Growth blogs still repeat them in 2026. When a blog cites them, discount the blog.

### Gaps
- No clean dataset of the old program's payout per verified impression. The figures are single-creator screenshots and a Grok estimate.
- Not confirmed whether the 2026 ranking code carries any Premium-author boost. `reference/x-algorithm.md` does not record one, and this research did not re-read the code.

## Q5. Evidence specific to AI, developer and indie-hacker accounts

### Takeaway
Almost no 2026 evidence targets the AI or builder niche specifically. The most relevant signal is negative. X's head of product has singled out "Linkedin/AI/threadboy" style posts as spam that users reject, and growth writers say AI-generated posts are "dying". Build-in-public still works as a way to reach other builders, but its audience is mostly peers and the growth numbers are vendor claims. Proof-heavy, specific posts (screenshots of real work) are the format practitioners point to.

### Cited Findings
- Bier (Sep 2025, PRIOR): reach complaints came from accounts posting "the worst Linkedin/AI/threadboy spam". — [@nikitabier, id 1965800163269919203](https://x.com/nikitabier/status/1965800163269919203) [Official staff opinion]
- "AI-generated posts: Dying." "Proof is the most shareable content format." Process screenshots are recommended. — [grahammann.net, Feb 2026](https://grahammann.net/blog/how-to-grow-on-x-twitter-2026) [Opinion, Interest]
- Bier: "Copy-and-paste jobs that add zero unique commentary just steal impressions from the real creators." — [PiunikaWeb, Apr 2026](https://piunikaweb.com/2026/04/13/x-twitter-original-talking-videos-nikita-bier/). This applies directly to accounts that summarise AI news. [Official]
- An AI-tooling account advising on the program: "Copy originals with media, not reply-spam." — [@AbuZ8Studios, 23 Sep, id 2102878882466582682](https://x.com/AbuZ8Studios/status/2102878882466582682) [Opinion]
- A solo founder building in public is at 12.5K/500K and asking for engagement. — [@DeFi_G_, id 2102949204331000127](https://x.com/DeFi_G_/status/2102949204331000127) [Anecdote]
- The build-in-public audience is "overwhelmingly other builders, not buyers". That is a strength if you sell to developers or founders. — [BoilerplateHub](https://boilerplatehub.com/blog/build-in-public-2026) (search snippet) [Opinion, Interest]
- Named indie-hacker exemplars: @levelsio, @marc_louvion, @tdinh_me, @dannypostmaa, @yongfook and Arvid Kahl. — [Teract](https://www.teract.ai/resources/twitter-strategy-indie-hackers-2026) (search snippet) [Opinion, Interest: AI growth tool]. These accounts grew under the older system, before Original Content Rewards.
- X wants long-form writing partly as training data for its AI. Social Media Today reads the $1M Article prize as a way to grow xAI's "knowledge bank". — [Social Media Today, Jan 2026](https://www.socialmediatoday.com/news/x-formerly-twitter-offers-million-dollar-prize-best-article-long-form-post/809930/) [Analyst opinion]

### Inferences
- For a small Australian AI-builder account, the niche-specific risk is sounding like generic "AI tips" threads or news aggregation. X staff name both as low-value. The niche-specific opportunity is first-hand proof: builds, settings actually tested, before-and-after screenshots. Those match X's originality test and the "proof" format practitioners cite.
- Much of the AI, dev and indie audience is itself Premium (builders pay for Grok, long posts and reply priority). That would make the niche's verified share higher than the general 3–13% estimates. No source measured this.

### Gaps
- No dataset or creator report specific to AI or developer accounts under Original Content Rewards.
- No measure of what share of the AI and dev audience on X holds Premium.
- The Australian angle is unmeasured: no source reported how an Australia-based account's verified share or timing differs.
