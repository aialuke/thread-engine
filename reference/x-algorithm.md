# X algorithm reference

Source: https://github.com/xai-org/x-algorithm
Commit: `1b3fec20bc3fd9879bc3e9f3d9c42753cdc3fede` (main, 2026-09-23)
Checked: 2026-09-24
Status: current

Every value is a default. `home-mixer/params/param.rs` says its values mirror feature-switch defaults, so live experiments can override them per user. Read this file as "what the code allows", not "what X does to every post".

## Verified facts and what we do with them

| # | Fact | Source | What we do |
|---|---|---|---|
| A1 | For You keeps one post per conversation: the best-scoring one. | `home-mixer/filters/dedup_conversation_filter.rs` | Each root must stand alone and carry the payoff. |
| A2 | Replies and reposts from accounts the viewer does not follow are filtered out before scoring. | `home-mixer/filters/oon_retweet_reply_filter.rs` | A stranger can only be shown the root. |
| A3 | For followers, a reply to a reply is only served when it replies to the root and is addressed to someone they follow. | `thunder/posts/post_store.rs` | Cards past the second are reference material for people who open the thread. Thread length is tested. |
| A4 | Recommendation candidates older than 48 hours are dropped. | `home-mixer/params/config.rs:36` | The snapshot at about 48 hours measures early performance. It is not lifetime reach. |
| A5 | Originals from authors with 1,000 or fewer followers can be lifted to about the 16th slot, once per feed request. Replies and reposts are excluded. The post also has to be young, under 1,000 home views, and already ranked. | `home-mixer/scorers/author_cold_start.rs`, `home-mixer/params/param.rs` | Originals carry reach. Replies are tested for follows and profile visits, not reach. |
| A6 | The out-of-network index skips replies. The `1fav` indexes are filled when a post is liked. | `phoenix-rankall-strato/columns/phoenix_rank_all/phoenixRankAllCandidateProcessor.strato:85,281,448` | Record time to first like if the X tools expose it. Posting hour is an experiment. |
| A7 | Small authors (1,000 followers or fewer) have their own retrieval index with a 24-hour window. | `phoenix-rankall/src/config/mod.rs` | Supports A5. No action beyond posting originals. |
| A8 | Topic share is computed over the author's last 15 originals, with thresholds of 0.90, 0.75 and 0.50. Which one is live is unknown. | `phoenix-rankall-strato/lib/eventProcessing.strato:461-465` | Editorial rule, not a proven penalty: keep most originals in the main lane. The weekly review reports the share. |
| A9 | Default weights: copy-link share 20, reply 5, quote 5, DM share 5, follow 4, share 2, repost 1, like 0.5. Report −234, mute −58.8, not interested −43.2, block −31.2. Weights multiply predicted probabilities, not counts. | `home-mixer/params/param.rs`, `home-mixer/scorers/ranking_scorer.rs` | Write posts worth saving and sending. Avoid bait. Copy-link and DM shares are not public, so the loop cannot see them. |
| A10 | Replies from a mutual follow on an original post get +15 on the reply weight. | `home-mixer/scorers/ranking_scorer.rs`, `docs/BIDIRECTIONAL_BOOST_CHANGE.md` | Real mutual follows in the lane are worth building. Greeting replies do not earn it. |
| A11 | Same-author candidates in one request are scaled 1.0, 0.625, 0.44 and down to 0.25. There is no time rule. | `home-mixer/scorers/ranking_scorer.rs`, `home-mixer/params/param.rs` | Spacing between originals is recorded and tested. There is no fixed gap. |
| A12 | The reply spam scorer sees the replier's reply count for the last 24 hours and whether the reply was pasted. | `grox/core/lm/thread.py:50,63` | No bulk replies. Grok may suggest what to say. The operator writes the reply. |
| A13 | Duplicate reply text is clustered and can be labelled `COPYPASTA_SPAM`. Blue gives no exemption. | `botmaker-rules/scarecrow/bot/BBQDuplicateTextRepliesProd.bot` | Never post the same reply twice. |
| A14 | Pinning a post with a link rated low-quality or bad labels the account `SPAM_HIGH_RECALL` for one week. | `botmaker-rules/scarecrow/bot/PinnedLowQualityOrBadUrl.bot:21,38-40` | Pin a post with no link, or a link to a well-known site. |
| A15 | Media marked DMCA is dropped from recommendations. No rule penalising AI-made images was found. | `visibility-filtering/rules/tweet_rules.rs` | Never attach copied vendor images. AI images are illustration only, never shown as a screenshot or proof. |

## Not verified, do not plan around

- Video indexing windows and any video preference.
- Whether bookmarks stand in for private shares.
- Which topic-share threshold (A8) is live.

## Refresh rule

`/next` checks weekly for commits to any file in the Source column since the commit above. If one changed, set Status to `stale`, name the file, and pause lessons that cite that fact until someone re-reads it and updates this file.

## Cited paths

- home-mixer/filters/dedup_conversation_filter.rs
- home-mixer/filters/oon_retweet_reply_filter.rs
- thunder/posts/post_store.rs
- home-mixer/params/config.rs
- home-mixer/scorers/author_cold_start.rs
- home-mixer/params/param.rs
- home-mixer/scorers/ranking_scorer.rs
- phoenix-rankall-strato/columns/phoenix_rank_all/phoenixRankAllCandidateProcessor.strato
- phoenix-rankall/src/config/mod.rs
- phoenix-rankall-strato/lib/eventProcessing.strato
- docs/BIDIRECTIONAL_BOOST_CHANGE.md
- grox/core/lm/thread.py
- botmaker-rules/scarecrow/bot/BBQDuplicateTextRepliesProd.bot
- botmaker-rules/scarecrow/bot/PinnedLowQualityOrBadUrl.bot
- visibility-filtering/rules/tweet_rules.rs
