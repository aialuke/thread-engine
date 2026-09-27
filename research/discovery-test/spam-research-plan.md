# Spam and off-topic research plan (26 Sep 2026)

This plan feeds §5 of `research/discovery-x-api-search-proposal.md`. It was revised after Codex's blind adversarial review (`codex-proposal-review.md`) and the session's own review.

## Why

- About half of what the pilot retrieved was spam or promotion: X API 8 of 14, Grok 9 of 30 (`private/facts.md`).
- Genuine posts are few: about 5 a day for the pilot's Demand idea. So dropping one genuine post costs about 20% of a day's leads.
- X bills per post returned. Spam removed in the query is never paid for; spam removed afterwards is.
- The product needs the **cost per genuine lead**, and a design that removes spam without losing genuine posts.

## What the product needs to know

1. Which spam and off-topic types appear, **per job** (Demand, Worth joining, Tool research) and per niche (tech, comedy).
2. Which filters remove them, at what cost in genuine posts lost, and in what order: query exclusions, post-field rules, author-field rules, then an optional model classifier (D81's pattern: a code rule by default, AI as the user's option).
3. For Worth joining, which shows 2–3 leads: whether the leads a person would pick **rank in the top 3**, not only whether spam is removed.
4. The cost per genuine lead, with and without the filters.

## Rules fixed before any data

- **Spam and off-topic are separate.**
  - Spam: selling, promotion, engagement bait, product marketing, bots.
  - Off-topic: a real person on a different subject, such as a video game's "free version".

  Off-topic is fixed by anchoring the query, not by spam filters.
- **The taxonomy is per job.** A builder's own launch post is spam for Demand, but it's the conversation itself for Worth joining, and it's data for Tool research.
- **Pass bar**, per job, fixed before testing. A filter is kept only if both hold:
  - on held-out data, it drops at most 1 genuine post in 20 (upper 90% bound at most 10%);
  - it removes at least a third of the spam.

  The bar is measured only once the held-out set has **at least 30 genuine posts** for that job. Below that, results are reported as directional and nothing ships.
- **A person is the last filter.** An uncertain post passes through; it's never silently dropped.
- **The product keeps rules, not posts.** The output is operators, field thresholds and phrase lists. Private data is deleted by 26 Mar 2027 (180 days; operator, 27 Sep, replacing 24 Oct 2026), and X's rules on deleted posts apply.

## Steps

| # | Step | Cost | Output |
|---|---|---|---|
| 1 | **Desk research.** X API operators (`-is:nullcast`, `-has:links`, `-has:cashtags`, `-is:quote`, `lang:`); post fields already fetched (`entities`, `source`, `possibly_sensitive`, `context_annotations`, `reply_settings`); author fields (account age, followers and posts, verified); X's spam and platform-manipulation policy; published spam signals. Each finding gets a reliability label, as in `community-grok-prompting.md` | free | `spam-desk-research.md` |
| 2 | **Decide the deployable fields.** Which fields each tier actually fetches (post-only on every tier; author fields only if affordable, since F2 is unresolved). Filters are designed and tested as two separate sets, post-only and author-enhanced, with the author set's extra cost shown | free | a field list in this file |
| 3 | **Taxonomy and labels.** The `type` label (genuine, account-selling, promotion, engagement-bait, product-marketing, off-topic, other) is now in the scoring brief (`harness.py` `scoring_brief`). The ~80 posts collected so far are relabelled blind. **Every positive and every unclear post gets a second, independent score** (`ingest-scores`, `second-scores`); disagreements are settled with a reason (`finalise-scores`); agreement is reported per axis. Text-only labellers can't judge author signals, so author-set tests need a fixed field packet shown with the text | free (Codex) | a labelled pilot set |
| 4 | **Stages supply the held-out data.** Stage 2, then 1 and 3, score every post with `type` and the second scorer. The pilot set is for **developing** rules only; Stage data, later in time and covering every job and niche, is for **testing** them | inside the stage budgets | held-out labels per job |
| 5 | **"Gone after 24 h" as its own signal.** `harness.py recheck --hours 24` records whether each post still exists, reason unknown. It's a candidate feature and a secondary metric, **never** the spam label | $0.005 a post, repeats in the same UTC day likely free | `private/recheck.jsonl` |
| 6 | **Offline rule tests.** Post-field rules and author-field rules, developed on the pilot set and measured on held-out Stage data, per job, against the pass bar. Report what each rule removes, what genuine posts it drops, and the uncertainty | free | rule candidates |
| 7 | **Live query-exclusion test.** First, confirm each operator is accepted (a rejected query returns no posts, so it should be free). Then run each Demand and Worth-joining query with and without each exclusion in a **frozen past window**, the same UTC day, so repeats should be free and results comparable. Tool research gets this through Stage 3's separate `Kspam` source. Score the union; report what each exclusion removed and what it lost | about $0.30–0.60 of X | query exclusions that pass |
| 8 | **Design in layers.** Query exclusions, then post-field rules, then author-field rules (if affordable), then the optional model classifier. For Worth joining, measure top-3 precision after ranking. Price each layer as cost per genuine lead | free | §5 of the proposal |

## Deployable fields (step 2, decided 26 Sep)

Filters are designed in two sets and tested separately. The operator decided the author-field cost stays an estimate; F2 is unresolved.

**Set A: post-only.** Available on every tier that searches, at no extra charge beyond the post (X bills per resource returned). These are the fields the harness requests (`harness.py` `TWEET_FIELDS`):

| Field | Candidate signal |
|---|---|
| `text` / `note_tweet` | Phrases ("DM", "link in bio", "save this", "giveaway"), messaging-app links, disguised spellings, emoji and hashtag density, all-caps share, list formatting ("1. … Paid vs Free") |
| `entities` | Counts of URLs, mentions, hashtags and cashtags; URL domains (shorteners, wa.me, whatsapp.com, t.me) |
| `referenced_tweets` / `in_reply_to_user_id` / `conversation_id` | Reply or original; replies to a stranger's post containing only a link |
| `public_metrics` | Zero-engagement with links; reply count (Worth joining) |
| `lang` | Already an eligibility rule |
| `possibly_sensitive`, `withheld` | X's own flags |
| `source` | Removed from the API in Dec 2022 (`spam-desk-research.md`); not usable |
| `context_annotations` | X's topic labels, as an off-topic signal (a video game against software) |
| `reply_settings`, `attachments`, `edit_history_tweet_ids`, `geo` | Minor; kept for completeness |

**Set B: author-enhanced.** Needs `expansions=author_id` plus `user.fields` (`harness.py` `USER_FIELDS`): account age (`created_at`), `public_metrics` (followers, following, posts), `verified` / `verified_type`, `description` (bio), `protected`, `url`. Estimated cost: $0.010 per unique author, unverified. So a set-B rule must beat set A by enough to pay for about $0.10 more per 10 posts. It's reported as an incremental gain, with that cost attached.

Labellers get the post text only. When a set-B rule is tested, the adjudication packet adds the author fields for that test alone.

## Progress (26 Sep)

- **Step 1 done:** `spam-desk-research.md`. Key points:
  - `-is:nullcast` removes only ad-only posts, so it barely touches organic spam.
  - The strongest query cuts are negated `url:` on messaging and shortener domains, negated emoji, `-has:cashtags` and `-has:links`. The last may drop genuine screenshot posts.
  - `source` is gone.
  - X names account selling, bulk links and irrelevant promo replies as spam, and restricts or deletes them.
  - Research finds near-duplicate text and coordination beat content classifiers.
- **Step 2 done:** the field sets above.
- **Step 3 done:** 118 pilot posts labelled by Codex (luna). A blind second score by Claude went on every positive and unclear post plus 20% of the rest (87 posts); the 59 disagreements went to a blind third scorer (Codex sol), majority wins. Details in `private/facts.md`.
  - Most disagreement was relevance 1 against 0 and spam type, not spam or not.
  - Against the final labels, Codex alone agreed on good-or-not for 117 of 118 posts, and on spam-or-not for 114 of 118.
- **Directional look at the development set** (not the test): four precise post-only rules together catch 23 of 42 spam posts and drop 0 of 18 good ones. They are:
  - a link-only reply;
  - duplicate text;
  - a list format;
  - "save this" or "swipe" phrases.

  "Has any link" catches 24 of 42 spam but drops 5 of 18 good. These are candidates for held-out testing, not results.

## Order

1. Steps 1–3 now, all free.
2. Stage 2 with `type` labels and the second scorer.
3. Steps 5–6 on Stage 2's data, and step 7 in a frozen window.
4. Stages 1 and 3 extend the held-out set, with step 6 rerun per job.
5. Step 8 writes the proposal's §5.

## Limits

- Tech and comedy spam differ. Results from one niche aren't general.
- `lang:en` already removes some spam (the disguised account-selling posts). A profile language setting changes that.
- Spam changes over time: disguised spellings and new promotions appear. The product needs a vendor-maintained list, versioned, like the algorithm reference: ongoing work, not a one-off.
- A spam model learned across users falls under D76 and the open terms question L2-C10.

## Needs the operator

- **Codex labelling spam types.** It sends other people's post text to Codex, which extends operator decision 4 (scoring). Assumed covered unless the operator says otherwise.
- **Author-field cost (F2).** Settling it needs console readings just before and just after one isolated author call. Otherwise the author set stays priced by estimate.
