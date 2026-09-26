# Spam desk: docs and sources for filtering X recent-search results

Research only, 26 Sep 2026. No X API or xAI calls were made. Sources were read on docs.x.com (raw `.md` pages and `llms-full.txt`), the web and `reference/x-algorithm.md`. Labels: **official** (X/platform docs, standards bodies, X's published code), **developer with evidence** (peer-reviewed or preprint with data), **anecdote**. **UNVERIFIED** means not confirmed on the pay-per-use tier or not confirmed by a primary source.

## Summary (10 lines)

1. Most filtering has to happen after the call. Query operators remove only the crude cases, and every post returned is billed ($0.005, official).
2. `-is:nullcast` removes only "Promoted-only" ad posts. It does not remove organic promotion, which is most of the pilot's spam. The legacy docs listed it as "Advanced" (Academic only), so it is UNVERIFIED on pay-per-use.
3. The cheap, strong query exclusions are negated `url:` on messaging and shortener domains, negated emoji (`-👇`), `-has:cashtags` and short negated phrases. All of them are standalone or negatable, and all count toward the 512 characters.
4. `-has:links` is the strongest single cut against link drops and listicles, but it may also drop posts with screenshots (media arrive as URL entities). UNVERIFIED.
5. `is:verified` is not a spam filter. X's own spam rules don't exempt blue accounts (A13, A16).
6. Post fields that carry signal without an author read: `entities` (urls/expanded_url, mentions, hashtags, cashtags), `paid_partnership`, `context_annotations`, `reply_settings`, `referenced_tweets`, `public_metrics.impression_count`, `possibly_sensitive`. The `source` field was removed in Dec 2022.
7. Author fields need `expansions=author_id`, and User: Read is officially $0.010 per resource. Whether expanded users are billed that way is UNVERIFIED, so run a user lookup only on the top-N survivors.
8. X's policy calls this "content spam" and "engagement spam" and lists account selling. Enforcement includes restricting reach, deleting posts and suspension, which explains posts vanishing. In 2011, 77% of spam accounts were suspended within a day.
9. Research says content-only classifiers are weak against modern (LLM) spam, and batch-level duplication and coordination are stronger. Simple rules work but are dataset-specific, so calibrate on the pilot's own labels.
10. Rank rather than filter: score each post as relevance minus spam penalties, take the top N, measure precision@N against hand labels, and try `sort_order=relevancy`.

## 1. Search operators against spam

Sources: operators page https://docs.x.com/x-api/posts/search/integrate/operators and build-a-query page https://docs.x.com/x-api/posts/search/integrate/build-a-query (both **official**, read 26 Sep 2026).

| Operator | Type (docs) | Use against spam | Pay-per-use status |
|---|---|---|---|
| `-is:nullcast` | Conjunction required; "Excludes promotional Posts (must be negated)" | Ad-only posts. Ads docs: nullcasted = "Promoted-only" Tweets that "do not appear in the user's public timeline" (Ads API docs, in docs.x.com/llms-full.txt). **Not organic promo** | UNVERIFIED: legacy counts table lists it "Advanced" = "only available to users that have been approved for Academic Research access" (https://docs.x.com/x-api/posts/counts/migrate/overview). The current operators page has no tier column |
| `has:links` / `-has:links` | Conjunction required; "Matches Posts with links" | Link drops, listicles, affiliate links | Legacy table "Core". Whether media counts as a link: UNVERIFIED (the data dictionary sample shows a photo as an `entities.urls` item with `media_key`) |
| `url:` | **Standalone**; "Tokenized match on URL (matches `url` or `expanded_url` fields)" | `-url:"wa.me" -url:"t.me"` etc. Negation is allowed (only `-is:nullcast` has special rules) | Legacy "Core" |
| `has:cashtags` / `$` | Conjunction required / standalone | Crypto shills | Legacy "Advanced": UNVERIFIED |
| `has:mentions` | Conjunction required | Mention-stuffing | Core |
| `has:hashtags` | Conjunction required | Hashtag-stuffing | Core |
| `has:media`, `has:images`, `has:video_link` | Conjunction required | Weak; promo cards often carry images | Core |
| `is:quote` | Conjunction required | Search matches the quote's own text, "**not** on the content from the original Post" | Core |
| `is:verified` | Conjunction required; "Posts from verified authors" | Not a spam filter (see A16 below) | Core |
| `is:retweet`, `is:reply` | Conjunction required | `-is:retweet` removes amplification; `-is:reply` removes link-drop replies | Confirmed in pilot (`-is:reply`) |
| `lang:` | Conjunction required | Off-language spam | Confirmed in pilot |
| `min_likes:`, `min_replies:`, `min_reposts:` | **Standalone**; "available with both recent search and full-archive search". Web names `min_faves:`/`min_retweets:` "will be rejected with a 400" | Engagement floor | Confirmed in pilot (`min_likes`, `min_replies`) |
| emoji | **Standalone**; "Matches an emoji within the Post body" | `-👇 -🔥 -🚀` | Core |
| `context:` / `entity:` | Standalone (`entity:` recent search only) | `-context:<domain>.<entity>` against off-topic lookalikes (e.g. a video-game entity) | Core; entity IDs must first be read from `context_annotations` |
| `sample:`, `source:`, `url_contains:`, `min_followers:`, `followers_count:`, `tweets_count:`, `bio:` | Filtered stream only | Would be ideal (author metrics in the query) | **Not in search**: "The Search Posts endpoint does not include the `sample:`, `bio:`, `bio_name:`, or `bio_location:` operators" (https://docs.x.com/x-api/fundamentals/recovery-and-redundancy). The user-metric operators appear only on the stream operators page: UNVERIFIED in search |

Rules (build-a-query, **official**):
- "Conjunction-required operators cannot be used by themselves in a query". `has:links OR is:retweet` is invalid.
- "The operator `-is:nullcast` must always be negated"; "Negated operators cannot be used alone"; "Do not negate grouped operators. Instead of `skiing -(snow OR day OR noschool)`, use `skiing -snow -day -noschool`". Every exclusion therefore costs its own `-term`.
- Length: self-serve recent search 512 characters, enterprise 4,096. "The entire query string counts toward the limit". Quotes, spaces, parentheses and `OR` all count. Whether the limit is measured before or after URL-encoding, and whether an emoji counts as 1 or 2, is UNVERIFIED. Test with a query near 512.
- AND binds before OR: `apple OR iphone ipad` = `apple OR (iphone ipad)`.
- `sort_order` takes `recency` or `relevancy` (OpenAPI spec, https://docs.x.com/x-api/posts/search-recent-posts). What "relevancy" ranks on is undocumented.

## 2. Post fields that signal spam

Source: data dictionary https://docs.x.com/x-api/fundamentals/data-dictionary (**official**). Default fields: `id`, `text`, `edit_history_tweet_ids`.

| Field | Doc line | Spam use | Author read? |
|---|---|---|---|
| `entities` | "hashtags, URLs, mentions, etc."; url items carry `expanded_url`, and in samples `unwound_url`, `title`, `status` | Domain denylist, counts of links, mentions and hashtags; `unwound_url` resolves shorteners (UNVERIFIED on self-serve) | No |
| `paid_partnership` | "disclosed by the author as containing paid promotion" | Direct promo flag (rarely set by spammers) | No |
| `context_annotations` | "Entity recognition/extraction, topical analysis" | Off-topic lookalikes (game vs software) | No. Full-archive caps `max_results` at 100 with this field (changelog); recent search UNVERIFIED |
| `public_metrics` | retweet, reply, like, quote, **impression_count**, bookmark | Low impressions for the post's age can mean restricted reach (UNVERIFIED as a signal) | No |
| `referenced_tweets` | replies, quotes, retweets | Reply + link + short text = link-drop | No |
| `reply_settings` | "everyone", "mentioned_users", "followers" | Drop from "live conversation" (b) when you can't reply | No |
| `possibly_sensitive` | "may be recognized as sensitive" | Downrank | No |
| `edit_history_tweet_ids` / `edit_controls` | versions of the post | Policy lists deceptive edit-to-promo (weak) | No |
| `note_tweet` | full text of >280-char posts | Listicles are long; you need it for the full text | No |
| `withheld` | withholding details | Rare | No |
| `source` | "Today, we are removing the source field from the post payload" (changelog, 20 Dec 2022) | **Gone** | n/a |
| `author_id` | ID only | Per-batch author repeat counts (free) | No |
| User `created_at`, `public_metrics` (followers, following, tweet_count, listed), `verified`, `verified_type`, `description`, `url`, `protected`, `most_recent_tweet_id`, `is_identity_verified`, `parody`, `location` | User object | Account age, follower/following ratio, WhatsApp/Telegram in bio, link-hub URL | **Yes**: `expansions=author_id&user.fields=...` |

Pricing (https://docs.x.com/x-api/getting-started/pricing, **official**): "Posts: Read $0.005 per resource", "User: Read $0.010 per resource", "Charged per resource returned in the response", deduplicated "within a 24-hour UTC day window". That expanded authors in `includes.users` are billed as User: Read is UNVERIFIED: the page doesn't mention expansions. Check the Developer Console on one small call. If they are billed, author data costs 3× the post read. Look up only the survivors (`GET /2/users?ids=`, same unit price).

## 3. X's policy on spam, and removal

Source: Authenticity policy (formerly "platform manipulation and spam"; help.x.com returned 403, read via Wayback snapshot 23 Sep 2026, https://web.archive.org/web/20260923091044/https://help.x.com/en/rules-and-policies/authenticity). **Official**.

- Content spam: "You may not share or post content in a bulk, duplicative, irrelevant or unsolicited manner". Examples include "posting with excessive, unrelated hashtags", "repeatedly posting ... links shared without commentary", "promoting content by replying with content that is irrelevant to the topic of the original post", and "Copypasta".
- Engagement spam and account selling: "Trading, buying, selling ... or soliciting access of X accounts, including the temporary or permanent transfer or sales of accounts, username or X ... products", and "using or promoting third-party services to perform any of the transactions described in this policy".
- Scams: "social engineering", "money-flipping schemes", "fraudulent discounts".
- Enforcement: "Restricting Reach: This may include excluding posts from search results ... removing posts from the For You and Following timelines"; "requiring deletion of one or more posts"; "accounts will be permanently suspended at first detection" for severe violations. Whether reach restrictions also apply to API recent search is UNVERIFIED.
- Why posts disappear after a day: deleted posts and posts from suspended accounts stop resolving. Historical rate (**developer with evidence**, Thomas, Grier, Paxson, Song, IMC 2011, 1.1M suspended accounts, 1.8B tweets, 2010–11 era): "77% of accounts employed by spammers are suspended within a day of their first post, and 92% of accounts within three days" (https://conferences.sigcomm.org/imc/2011/docs/p243.pdf). No current figure was found. Batch Compliance endpoints exist "to identify deleted Posts, suspended accounts" (docs.x.com, **official**).
- X's own code (**official**, xai-org/x-algorithm, via `reference/x-algorithm.md`): A12, a reply spam scorer that sees "the replier's reply count for the last 24 hours and whether the reply was pasted"; A13, "Duplicate reply text is clustered and can be labelled `COPYPASTA_SPAM` ... blue is not" exempt; A16, verified status appears "only in a spam-credibility score". Sellers with blue checks are therefore not trustworthy by badge.

## 4. Published signals for spam and promotion

| Source | Era / sample | Key line | Label | Use for us |
|---|---|---|---|---|
| Thomas et al., IMC 2011 (above) | 2010–11, 80M spam tweets | "wide-spread abuse of legitimate web services such as URL shorteners"; marketplace of "Twitter account sellers, ad-based URL shorteners" | developer with evidence (old era) | Shortener and link-hub domains = signal; resolve `expanded_url` |
| Yang & Menczer, "Anatomy of an AI-powered malicious social botnet", 2023 (https://arxiv.org/abs/2307.16336) | 2023, 1,140 accounts | Found by searching "as an ai language model"; "consistently link to three suspicious websites"; "current state-of-the-art LLM content classifiers fail to discriminate between them and human accounts in the wild"; detectable "through their coordination patterns" | developer with evidence | Self-revealing phrases, shared domains, near-duplicate text across authors in a batch |
| Hays et al., "Simplistic Collection and Labeling Practices Limit the Utility of Benchmark Datasets for Twitter Bot Detection", 2023 (https://arxiv.org/abs/2301.07015) | Multiple benchmarks | "shallow decision trees trained on a small number of features ... achieve near-state-of-the-art performance"; predictions depend on "each dataset's collection and labeling procedures" | developer with evidence | Simple rules work, but only on your own distribution. Label pilot data; don't import thresholds |
| Feng et al., "What Does the Bot Say?", ACL 2024 (https://arxiv.org/abs/2402.00371) | TwiBot-20/22 | LLM detectors from 1,000 labels improve "up to 9.1%"; LLM-guided evasion degrades detection "by up to 29.6%" | developer with evidence | An LLM judge on survivors is viable; expect drift |
| Acharya et al., "Conning the Crypto Conman", 2024 (https://arxiv.org/abs/2401.09824) | 9,000+ scammers, 25k decoy tweets | Scammers "use Twitter as a starting point ... after which they pivot to other communication channels (eg email, Instagram, or Telegram)" | developer with evidence | Off-platform contact (WhatsApp/Telegram/"DM") = strong signal |
| Meta, "Fighting Engagement Bait", 2017 (https://about.fb.com/news/2017/12/news-feed-fyi-fighting-engagement-bait-on-facebook/) | Facebook | Posts that "goad [users] into interacting"; "reviewed and categorized hundreds of thousands of posts to inform a machine learning model"; bait is "shown less prominently" (demotion) | official (other platform) | Engagement-bait taxonomy; demote, don't delete |
| Unicode UTS #39 (https://www.unicode.org/reports/tr39/) | Standard | "X and Y are defined to be confusable if and only if skeleton(X) = skeleton(Y)" | official | Fold disguised spellings (Cyrillic look-alikes) before keyword rules |
| Ferrara, Twitter spam survey, 2022 (https://arxiv.org/abs/2211.05913) | Survey | Taxonomy of "techniques used to create and detect" spam | developer with evidence | Background; feature ranking not in the abstract |
| ">56% of accounts sharing Telegram/Discord invite links were bots or suspended" | Seen only in a search summary, likely Nizzoli et al. 2020 | UNVERIFIED | UNVERIFIED | Don't cite until read |

Features you can compute without author data, ranked by the evidence above (the ranking is a judgement; no 2022+ paper gives feature importances for post-only features on current X, UNVERIFIED):
1. Link to a messaging app or link hub (`wa.me`, `api.whatsapp.com`, `chat.whatsapp.com`, `t.me`, `linktr.ee`, shorteners), or text asking to move off-platform ("DM", "WhatsApp", "Telegram", "inbox"). Strongest (Acharya; Thomas; policy).
2. Near-duplicate text across the batch, or the same `author_id` many times (policy "Copypasta"; A13; Yang & Menczer).
3. Link present plus short text plus a reply (policy "links shared without commentary"; "replying with content that is irrelevant").
4. Hashtag and cashtag count (policy "excessive, unrelated hashtags"; fox8 crypto hashtags).
5. Mention count ≥3 in an original post (policy "bulk ... mentions").
6. Arrow and pointing emoji before a link (👇 ➡️ 🔗), emoji density, all-caps ratio. Classic features; weaker, no recent primary source.
7. Offer vocabulary after confusable folding: "lifetime", "cheap", "premium account", "giveaway", "limited", "100% free", price strings.

## 5. Ranking candidates (top-N) rather than filtering

- Demote, don't delete. Meta demotes bait rather than removing it, and X's enforcement is mostly "Restricting Reach" (official). Keep a score so borderline genuine posts can still surface.
- Two-stage: query exclusions, then free post-field scoring, then an author lookup (and an optional LLM judge) only on the top N. That caps the $0.010 user reads. Hays et al. support simple scored rules if they are fitted to your labels.
- Score = topical relevance (query-term match, `context_annotations` domain) + intent cues (question mark, "anyone know", "recommend", "looking for") + conversation value (`reply_count`, reply-to-like ratio: X's ranker weights a reply at 5 vs a like at 0.5, A9, official code) − spam penalties (section 4 list).
- Evaluate with precision@N (share of the top N that a human marks useful) on the pilot's labelled posts, not with overall accuracy. Report genuine posts lost for each rule.
- Try `sort_order=relevancy` against `recency` on the same query. X doesn't document what relevancy uses (UNVERIFIED benefit).

## What to test

Each row is a candidate. Measure it on the pilot's labelled posts first (free), then in one live query.

| # | Rule | Where | Catches | Expected genuine loss |
|---|---|---|---|---|
| 1 | `-url:"wa.me" -url:"t.me" -url:whatsapp -url:telegram` | Query (~50 chars) | Premium sellers, scam pivots | Near zero |
| 2 | `-url:"bit.ly" -url:"linktr.ee" -url:"tinyurl"` | Query | Link drops, affiliate hubs | Low; some real posts use shorteners |
| 3 | `-has:links` on (a) demand and (c) opinion queries | Query | Listicles, link drops, product marketing | Medium: people sharing a screenshot or an article with their opinion (media-as-link UNVERIFIED) |
| 4 | `-has:cashtags` (fallback `-$`) | Query | Crypto shill | Near zero off-finance. Test availability first; a 400 means Advanced-only |
| 5 | `-is:nullcast` | Query | Ad-only posts | Near zero, but likely near-zero yield too. Test availability |
| 6 | `-👇 -🔥 -🚀 -✅` | Query (~12 chars) | Link-drop and bait styling | Low to medium; 🔥 is common in genuine enthusiasm |
| 7 | `-giveaway -"dm me" -"link in bio" -"who is stopping you" -"stop paying"` | Query | Bait, giveaways, paid-vs-free listicles | Medium for (c): "stop paying for X" can be a real opinion |
| 8 | `-is:reply` for (a) demand only | Query | Link-drop replies | Medium: demand stated in replies is lost |
| 9 | `min_replies:1` for (b) live conversations only | Query | Dead bait and ad posts | High for fresh posts; use only for (b) |
| 10 | `-context:<game domain>.<entity>` after reading IDs from `context_annotations` | Query | Video-game "free version" lookalikes | Low if the entity is precise |
| 11 | Drop if any `expanded_url`/`unwound_url` domain is in the messaging, link-hub or shortener denylist | Post field | Same as 1–2, including forms the query missed | Near zero |
| 12 | NFKC + UTS #39 skeleton + leet folding (0→o, 3→e, spaced letters) before keyword rules | Post text | Disguised spellings ("N e t f l i x Pr3mium") | Near zero; false matches only on real brand talk, so pair with offer words |
| 13 | Cluster near-duplicate normalised text (e.g. MinHash or shingles) per batch; drop clusters of 3+ distinct authors | Post text | Copypasta campaigns | Low; retweet-style quote waves |
| 14 | Penalty: hashtags ≥3, mentions ≥3 in an original, cashtag present, emoji density high, caps ratio high | Post field | Stuffing | Low to medium; tune on labels |
| 15 | Penalty: reply + link + text under ~60 characters after removing the URL | Post field | "Give it a try, completely free 👇 link" | Low |
| 16 | `paid_partnership=true` → treat as promotion for (a) and (b) | Post field | Disclosed ads | Low; keep for (c) product opinion |
| 17 | `reply_settings != everyone` → drop for (b) | Post field | Posts you can't reply to | None for (b) |
| 18 | Author lookup on the top N only: account age < 30 days, following ≫ followers, bio with WhatsApp/Telegram/"DM for" or a link-hub URL | Users lookup ($0.010 each) | Seller accounts | Low to medium: new real users |
| 19 | Don't add `is:verified` as a quality filter | — | — | It would drop most genuine small accounts and keep blue sellers |
| 20 | Query at ~500 characters with emoji and quotes to confirm how X counts toward 512 | Query | — | One call's cost |
