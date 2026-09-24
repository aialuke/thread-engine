# X algorithm reference

Source: https://github.com/xai-org/x-algorithm
Commit: `44d37ebf87f2185b949cd37b710d410c2a77d21f` (main, 2026-09-24 01:53 UTC)
Checked: 2026-09-24
Status: current

Every value is a default. `home-mixer/params/param.rs` says its values mirror feature-switch defaults (last synced 2026-09-23), and the VM ranker loads its parameters from a live config repo. Live experiments can override any of it per user. Read this file as "what the code allows", not "what X does to every post". Code notes with line numbers: `reviews/research_notes/Driving verified home timeline impressions/algorithm_code.md`.

## Verified facts and what we do with them

| # | Fact | Source | What we do |
|---|---|---|---|
| A1 | For You keeps one post per conversation: the best-scoring one, keyed on the root. | `home-mixer/filters/dedup_conversation_filter.rs` | Each root must stand alone and carry the payoff. |
| A2 | Replies and reposts from accounts the viewer does not follow are filtered out before scoring, as are replies whose earlier posts are missing. | `home-mixer/filters/oon_retweet_reply_filter.rs` | A stranger can only be shown the root. |
| A3 | For followers in For You, a reply to a reply is only served when it replies to the root and is addressed to someone they follow. The chronological Following tab keeps self-threads. | `thunder/posts/post_store.rs` | Cards past the second are reference material for people who open the thread. Thread length is tested. |
| A4 | Recommendation candidates older than 48 hours are dropped. | `home-mixer/params/config.rs:36` | The snapshot at about 48 hours measures early performance. It is not lifetime reach. |
| A5 | One original per feed request from an author with 1,000 or fewer followers can be lifted to about the 16th slot. Replies and reposts are excluded. The post also has to be under 48 hours old, under 1,000 home views, and already ranked inside the top 85% of that viewer's candidates. The lift is applied before the out-of-network discount (A17). | `home-mixer/scorers/author_cold_start.rs`, `home-mixer/params/param.rs` | Originals carry reach. It is a lift, not a way in: the post still has to be retrieved first. |
| A6 | The main out-of-network pool (`1fav_1day`) skips replies and is filled when a post is liked. It re-indexes at 2, 4, 8, 16, 32 … likes, only while the post is under 49 hours old. | `phoenixRankAllCandidateProcessor.strato:85,281,448`, `favoriteEventProcessor.strato` | **The first like is the gate to strangers.** Early likes from real mutuals matter more than late ones. Posting hour is an experiment. |
| A7 | A small-author "tail" index (authors under 1,000 followers, 24 hours, no like needed) exists, but nothing shows Home queries it. | `phoenix-rankall/src/config/mod.rs` | Don't plan around it. |
| A8 | Topic share is computed over the author's last 15 originals, with thresholds of 0.90, 0.75 and 0.50. Which one is live is unknown. | `phoenix-rankall-strato/lib/eventProcessing.strato:461-465` | Editorial rule, not a proven penalty. The weekly review reports the share. |
| A9 | Default weights: copy-link share 20, reply 5, quote 5, DM share 5, follow 4, share 2, repost 1, like 0.5, click 0.4, open link 0.2. Report −234, mute −58.8, not interested −43.2, block −31.2. Weights multiply predicted probabilities, not counts. | `xai-value-model/scoring.rs`, `vm-ranker/params.rs`, `home-mixer/params/param.rs` | Write posts worth sending to someone. Avoid bait. Copy-link and DM shares are not public, so the loop cannot see them. |
| A10 | When the viewer mutually follows the author of an original post, the weight on "the viewer will reply" rises from 5 to 20 (+15). It is about the viewer's reply to a mutual's original, not replies from mutuals. | `xai-value-model/inputs.rs`, `xai-value-model/weights.rs`, `docs/BIDIRECTIONAL_BOOST_CHANGE.md` | Real mutual follows in the lane make every original rank higher for them. Greeting replies do not build that. |
| A11 | Same-author posts in one viewer's pool are scaled 1.0, 0.625, 0.44 and down to 0.25. There is no time rule. | `vm-ranker/params.rs:139-156` | Spacing between originals is recorded and tested. There is no fixed gap. |
| A12 | The reply spam scorer sees the replier's reply count for the last 24 hours and whether the reply was pasted. | `grox/core/lm/thread.py:50,63` | No bulk replies. Grok may suggest what to say. The operator writes the reply. |
| A13 | Duplicate reply text is clustered and can be labelled `COPYPASTA_SPAM`. Only high-credibility accounts, a skip list and government-verified accounts are exempt; blue is not. | `botmaker-rules/scarecrow/bot/BBQDuplicateTextRepliesProd.bot` | Never post the same reply twice. |
| A14 | Pinning a post with a link rated low-quality or bad labels the account `SPAM_HIGH_RECALL` for one week, which drops **all** the account's posts from Home. | `botmaker-rules/scarecrow/bot/PinnedLowQualityOrBadUrl.bot:21,36-41`, `visibility-filtering/rules/author_rules.rs` | Pin a post with no link, or a link to a well-known site. Check x.com/i/under_the_hood for labels. |
| A15 | Media marked DMCA is dropped from recommendations. No rule penalising AI-made images was found. | `visibility-filtering/rules/tweet_rules.rs` | Never attach copied vendor images. AI images are illustration only, never shown as a screenshot or proof. |
| A16 | **No ranking or filtering step uses the author's or the viewer's Premium or verified status.** The viewer's subscription level is read only for stats and ads logging. Verified status appears only in a spam-credibility score, in spam-rule exemptions (A13), and as a line in the post's text embedding. | `xai-value-model/inputs.rs`, `home-mixer/scorers/vm_ranker_request.rs`, `user-cred-v2/UserCredV2App.scala` | There is no Premium dial. The share of impressions from Premium viewers depends only on who the posts reach, so aim originals at audiences that are mostly Premium. |
| A17 | Out-of-network posts are scored at 0.75× against the viewer's in-network originals. In-network replies and reposts also get 0.75×. | `vm-ranker/params.rs:157-192` | Strangers are harder to reach than followers. Followers and mutuals carry the early signal. |
| A18 | A diversity step (DPP) keeps a top set from the best 150 candidates and sets every other post's score to 0. | `vm-ranker/dpp.rs`, `vm-ranker/params.rs:199-211` | Near-duplicate topics compete with each other in one viewer's feed. Default settings; live values unknown. |
| A19 | Profile clicks and video watch quality have weight 0 by default. Bookmarks are not in the weight list. | `home-mixer/params/param.rs:295-407`, `vm-ranker/params.rs` | Profile visits matter for follows, not ranking. Don't expect bookmarks to move reach. |
| A20 | Only engagement on posts served in the Home timeline feeds ranking. The code's comment: coordinating via group chat "has no ranking impact". | `home-mixer/params/param.rs:266-293` | Engagement pods don't help ranking. A like from any source still triggers the `1fav` index (A6). |
| A21 | Followers get the account's recent originals without any engagement: Thunder pulls up to 50 originals per followed author. | `thunder/posts/post_store.rs` | Every verified follower is a guaranteed chance at a qualified impression. |
| A22 | There is no hard link penalty in ranking. Links act only through predicted clicks; malicious URLs are dropped for strangers. | `home-mixer/models/content_features.rs`, `visibility-filtering/rules/registry.rs` | A link is allowed when it adds value. The pin rule (A14) still applies. |

## Not verified, do not plan around

- Whether Home queries the tail or post-creation indexes (A7).
- Live values of the out-of-network factor, author diversity and DPP.
- Which topic-share threshold (A8) is live.
- Any video preference beyond extra retrieval indexes for videos over 10 seconds.
- How impressions are counted; the code has no visibility threshold.

## Refresh rule

X publishes this repo as one squashed commit each time, so commit history can't show which files changed. `/next` checks weekly: run `gh api repos/xai-org/x-algorithm/git/trees/main?recursive=1` and compare each cited file's blob SHA below with the one on `main`. If a file changed or is gone, set Status to `stale` (`python3 scripts/loop.py set-reference --status stale --files <paths>`), name the facts that cite it, and pause lessons that cite those facts until someone re-reads the file and updates this reference. If none changed, `set-reference --status current`.

## Cited paths (blob SHA at the commit above)

| Path | Blob SHA |
|---|---|
| home-mixer/filters/dedup_conversation_filter.rs | 9e73fc2f546ab76b91f9ae0841469cc5e1c95c37 |
| home-mixer/filters/oon_retweet_reply_filter.rs | 06dd0acef0ea91325e26b27d273bc9e15fbca2cd |
| thunder/posts/post_store.rs | 5a1c1966d3469c33ec62fcb66bb1654c5642dd91 |
| home-mixer/params/config.rs | 1a85cb7c86b06eda6bc1d8470d420d37e26484dc |
| home-mixer/scorers/author_cold_start.rs | ea3c59e12dda9d86e1651f92ac781e0a446eb470 |
| home-mixer/params/param.rs | 2d0e4c86d1447dc50ec98d86106c0d8e32095a7e |
| home-mixer/scorers/vm_ranker_request.rs | 4c7f575f8e7f48c45de08e66d5f5f748064cd186 |
| xai-value-model/scoring.rs | 61bbf7dadab8c0ecafb7f8a5927d96c18d5f6492 |
| xai-value-model/inputs.rs | 16e638ea73f1357dde3124fa9f7f4b40b7b339fb |
| xai-value-model/weights.rs | a4faefc9fb1fd6bd242a0279c68d54106887a35a |
| vm-ranker/params.rs | c225fe9ce4d1ca6914974fac35242ec393779d26 |
| vm-ranker/dpp.rs | 0b5952e48adbd146c83163293e7f37bf2a2b3aeb |
| phoenix-rankall-strato/columns/phoenix_rank_all/phoenixRankAllCandidateProcessor.strato | 552e4fd28c84190f5003b3d3dd0b05a46ca11cc5 |
| phoenix-rankall-strato/columns/favoriteEventProcessor.strato | 5d77e244d24269785cdee5f01662090206cba678 |
| phoenix-rankall/src/config/mod.rs | d873aba76f1874fc8336e67181f5d45570ce0dd1 |
| phoenix-rankall-strato/lib/eventProcessing.strato | 51d7db24216e27e65169f179a3984bb1fc97f8d0 |
| docs/BIDIRECTIONAL_BOOST_CHANGE.md | 9d0d75002116c1859cbd7b8b2b54e4a9e19cef28 |
| grox/core/lm/thread.py | b5b680923a8574b10826a51e311690f11d4b4025 |
| botmaker-rules/scarecrow/bot/BBQDuplicateTextRepliesProd.bot | 23795a560faa5788a8b63d8f3dc80e7be331b281 |
| botmaker-rules/scarecrow/bot/PinnedLowQualityOrBadUrl.bot | b6501a4986fa0194264d673a5075f61c8e32537f |
| visibility-filtering/rules/tweet_rules.rs | 1fdf6832da27ccb7a93d2cc4ea3b6f4b22efcfbd |
| visibility-filtering/rules/author_rules.rs | 79a6b2ebe5233bc17a57f56e181dff7bf53fd574 |
| user-cred-v2/UserCredV2App.scala | a7976c71eaed5ba3e05f0af936b29c0381a84047 |
| home-mixer/models/content_features.rs | 3cfaa98dbd317a65b0ad6216f7773ade99efc408 |
| visibility-filtering/rules/registry.rs | 8e5cc079a35f9e7701348de810fcc20077d822ac |
