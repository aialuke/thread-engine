# X's own rules for a post-drafting, learn-from-results tool

Research only. Fetched today (2026-09-26) from official X sources (help.x.com, legal.x.com,
docs.x.com) via a live browser session, except where marked "(search copy)". This does not decide
which rules the product enforces for everyone vs. per profile — that's the operator's call. It only
sorts what X itself requires from whom.

Classification key: **EVERYONE** (binds every X user) · **SOME USERS** (binds a subset — say which)
· **TOOL** (binds the product/app itself, developer terms) · **ADVICE** (guidance, not a rule).

---

## One-page summary

### EVERYONE (every X account, regardless of tier or program enrollment)

| Rule | One line |
|---|---|
| No unauthorized automation / scripted posting | "Automated or scripted accounts that do not comply with our Developer Policy" are an inauthentic-account violation — a general Rule, not just a rewards-program condition. |
| No content/engagement spam | No bulk, duplicative, irrelevant or unsolicited posting; no inauthentic use of engagement features. |
| No deceptive synthetic/manipulated media | Can't deceptively share manipulated media likely to cause harm; X may label it either way. |
| No civic-process manipulation | No false/misleading info about how, when, or where to vote or otherwise participate; enforced with a reach-killing "Civic Integrity" label in serious cases. |
| No impersonation / deceptive identity | Can't impersonate a person, group or org to mislead. Parody/commentary/fan accounts are fine if compliant. |
| Copyright and trademark | Can't infringe others' IP; repeat DMCA complaints can get an account suspended. |
| No malicious/deceptive links | Malware, phishing, deceptive redirects. |
| Sensitive media must be marked | Nudity/violence/graphic content needs the sensitive-media flag, per-post or account-wide; X can apply it for you and label the account after repeat misses. |
| Paid Partnership disclosure | Any post with a commercial arrangement (gifted product, commission, ambassador deal, etc.) must have the "Paid Partnership" toggle on — this binds *whoever does a paid partnership*, not just advertisers or Premium accounts. |
| Technical posting limits | 50 original posts / 200 replies per day for unverified accounts, an overall 2,400 posts/day cap broken into smaller windows, 500 DMs/day, 400 follows/day. Applies "including... API." |
| Character limit without Premium | 280 characters (X's own weighting: `→`, `▷`, emoji count 2; a link counts 23 — already implemented in `scripts/post_thread.py`). |

### SOME USERS (say which, so it becomes a profile setting)

| Rule | Who it binds |
|---|---|
| "Do not solicit engagements" (repeatedly instructing people to like/reply/bookmark/follow/repost) | **Original Content Rewards Program members only** — this is a program eligibility rule, not a general X Rule. An ordinary, non-enrolled account is not violating "the X Rules" by writing "reply with your take" — it just won't earn payouts from it if it were enrolled. |
| "Was created or posted using automated means" → content ineligible for payout | Same program: Original Content Rewards. Undefined phrase (X does not define "automated means" anywhere found). |
| No bots/tools to artificially generate likes/follows/views/comments/shares; don't tamper with the recommendation algorithm | Original Content Rewards conduct rules. |
| AI-generated armed-conflict video must be disclosed as AI-generated, or lose program earnings for 90 days | Original Content Rewards / Creator Monetization Standards conduct rules — binds monetizing creators, specifically around that one topic. |
| Prohibited/restricted content categories (drugs, weapons, gambling, adult content, hate/extremist content, graphic violence, sensitive political/social content, strong language) | Creator Monetization Standards — binds accounts trying to earn money from content, not posting generally. |
| Longer posts (up to 25,000 characters), Articles, Communities, edit window | Feature access gated by Premium tier — not a content rule, a capability. |
| Advertiser rules, Amplify Pre-Roll Guidelines | Advertisers / Amplify publishers only. Not reviewed in depth here (out of scope for a drafting tool unless it starts running ads). |
| Enterprise API tier requirement once usage exceeds "hobbyist... early-stage... limited end-users" | Binds **the product**, but *conditionally* on user-base size — see TOOL section. |

### TOOL (binds the product itself, as an X API developer)

| Rule | One line |
|---|---|
| Never use the X API or X Content to fine-tune or train a foundation or frontier model | Developer Agreement III.A.k. This is a hard line for a product whose whole premise is "learns from each post's results." Training on *your own account's numbers* (impressions, likes) to steer a prompt/heuristic is very different from training on X Content (post text) itself — see Open Questions. |
| Commercial Use requires the right API tier | Pay-Per-Use/Basic/Pro plans are for "hobbyists, commercial prototyping, initial development, early-stage... integrations... limited end-users." A paid, multi-user product that scales needs an Enterprise plan. |
| No non-API scripting of the website; no rate-limit circumvention | Automation Rules "Don't" list; Developer Agreement III.A/III.D. |
| Automated write actions need per-user opt-in consent, not just OAuth | OAuth alone "does not by itself constitute sufficient consent to take automated actions." Irrelevant while posting stays 100% manual/copy-paste, but binds the product the moment it adds any auto-post or auto-reply feature. |
| AI-powered auto-reply bots need X's prior written approval | Automation Rules II.B.3. Same trigger condition as above. |
| Pay-to-engage is banned | "You may not sell or receive monetary or virtual compensation for any X actions" (Developer Policy) — broader than the account's own "don't boost" house rule; this one bars *the product* from ever paying users or others for likes/follows/etc. |
| Content redistribution caps | Max 1,500,000 Post IDs to any entity per 30 days; full post/user objects capped at 500/person/day via non-automated means — relevant only if the product shows other users' posts (swipe files, research) to its own users at any real scale. |
| Service must self-identify; bot accounts must say so in bio | Developer Policy "Service authenticity." |

### ADVICE (guidance, not a binding rule)

- "Ask a real question, not an instruction" — X's own guidance is the instruction rule above (SOME USERS); phrasing it as a question is the account's/this repo's chosen way to comply, not itself an X rule.
- Community Notes explainer — describes a feature, not an obligation on posters.
- FAQ-style Premium comparisons, pricing, "does this mean free X is going away" — informational.

### Biggest surprises

1. **"Do not solicit engagement" and "no automated-means content" are Original Content Rewards Program rules, not general X Rules.** They only bind accounts enrolled in that specific monetization program (Premium/Premium+/Premium Business + eligibility thresholds). A non-monetizing user typing "reply with your favorite setting" breaks no X Rule. This repo already treats the no-solicit rule as universal (`voice/exit-zero.md`, `scripts/post_thread.py` `SOLICIT_RE`) — reasonable as a house style choice, but the underlying justification cited in the code (the rewards rule) only actually applies once/if the account enrolls.
2. **Creator Revenue Sharing was retired 2026-09-07 and replaced by "Original Content Rewards."** `AGENTS.md`/`post_thread.py` cite "Original Content Rewards" already — that's the *current* program name, good. Any reference elsewhere to "Revenue Sharing" is now stale.
3. **The Developer Agreement bars using the X API or X Content to fine-tune or train a foundation/frontier model — full stop, no monetization-status exception.** A product whose pitch is "learns from results" must be careful that its learning loop trains on numbers (impressions, likes, follow deltas) it reads via the API, not on the text of posts (its own or others'), if that text ever nears a training/fine-tuning pipeline. Prompting a model per-session with recent post text is not "training," but the line is worth the operator's legal read before the product scales.
4. **"Automated means" is undefined by X anywhere found**, including whether AI-drafted-then-human-edited-then-manually-pasted content counts. This is the single biggest open question for a product built entirely around AI-assisted drafting (see Open Questions).
5. **A paid, multi-user product reading each user's own X data at scale will likely outgrow the Pay-Per-Use/Basic/Pro API tiers** ("early-stage... limited end-users") and need an Enterprise agreement — a cost/legal planning item, not just an engineering one. This lines up with the existing plan to research "X tiers" as a build layer (per `MEMORY.md`).
6. **Paid Partnership disclosure is a universal, content-triggered rule** (not gated by account tier) that this repo's current format skills don't mention at all — relevant the moment any user of the planned product does a sponsored post.

---

## Detailed table

Format: **Rule** — quote — URL — classification — repo coverage — fixed-check feasibility.

### Authenticity / platform manipulation / spam (X Rules — general)

**Unauthorized automation (inauthentic accounts)**
> "Unauthorized automation: Automated or scripted accounts that do not comply with our Developer Policy. Please note that as a user you are ultimately responsible for third-party applications you may authorize to access or use your account."
https://help.x.com/en/rules-and-policies/authenticity — **EVERYONE**.
Repo: the whole design of `AGENTS.md` ("Never post, schedule, or call an X write API") and `scripts/post_thread.py` (writes only a run sheet; the operator copies and pastes) exists to keep this account outside "automated or scripted." Covered by architecture, not a runtime check — a **fixed check is possible** in principle (the product could refuse to hold write credentials at all, as this repo already does by using read-only Keychain keys per `reference/x-api.md` P1), but "did a human actually paste this" can't be verified in code once the text leaves the tool.

**Content Spam**
> "You may not share or post content in a bulk, duplicative, irrelevant or unsolicited manner that disrupts people's experience."
https://help.x.com/en/rules-and-policies/authenticity — **EVERYONE**.
Repo: not directly checked. `scripts/post_thread.py` checks for a repeated card *number* within one draft, not duplicate text against post history. **Fixed check possible**: hash new draft text against the ledger's prior posts before allowing `/approve`.

**Engagement Spam**
> "We prohibit inauthentic use of X engagement features to artificially impact traffic or disrupt people's experience."
https://help.x.com/en/rules-and-policies/authenticity — **EVERYONE**.
Repo: `voice/exit-zero.md` "Boosting" section ("Don't boost") and "Replies" section (no duplicate reply text, no bulk replies) are the house response. Not code-enforced — replies aren't drafted through `post_thread.py`. **Needs human judgment** for "artificially impact"; duplicate-text detection is a **fixed check**.

**Malicious URLs**
> "You may not post malicious, harmful, or deceptive links on X that may cause harm."
https://help.x.com/en/rules-and-policies/authenticity — **EVERYONE**. Not covered; likely N/A to this account's own links (official vendor pages). **Fixed check possible** (domain allowlist/reputation check) but not implemented.

### Civic integrity

> "You may not use X's services for the purpose of manipulating or interfering in elections or other civic processes. This includes posting or sharing content that may suppress participation or mislead people about when, where, or how to participate in a civic process."
https://help.x.com/en/rules-and-policies/election-integrity-policy — **EVERYONE**.
Enforcement detail: a "Civic Integrity" label removes the post from For You/Following, restricts it to profile-only, and disables most engagement — a much harsher penalty than a generic strike.
Repo: `voice/exit-zero.md` "Replies" section only addresses whether to engage in politics/news *editorially* (lane fit), not the specific false-participation-info rule. Not covered; likely low-relevance for a tech-tips account but the planned product's other users (a news/politics creator) would need it. **Needs human/model judgment** — "verifiably false" claims about voting logistics aren't a fixed-pattern check.

### Misleading and Deceptive Identities (impersonation)

> "You may not impersonate individuals, groups, or organizations to mislead, confuse, or deceive others, nor use a fake identity in a manner that disrupts the experience of others on X."
https://help.x.com/en/rules-and-policies/x-rules (full detail folded into the Authenticity page) — **EVERYONE**.
Repo: `voice/exit-zero.md` "Makers" section (never tag a person, check the handle first with `scripts/x_api.py user <handle>`) is a related but distinct house safeguard against *mistagging/false association*, not impersonation by this account. Not directly the same rule. **Fixed check possible** for "does this handle exist and match the org" (already implemented per P17 in `reference/x-api.md`); "is this account impersonating someone" doesn't apply here since it's about the account's own identity, N/A.

### Synthetic and manipulated media

> "You may not deceptively share synthetic or manipulated media that are likely to cause harm."
https://help.x.com/en/rules-and-policies/x-rules — **EVERYONE**. Fuller version on the Authenticity page:
> "You may not share inauthentic media, including, manipulated, or out-of-context media that may result in widespread confusion on public issues, impact public safety, or cause serious harm ('misleading media')."
https://help.x.com/en/rules-and-policies/authenticity — **EVERYONE**.
Repo: `voice/exit-zero.md` "Images" section — "AI-made images are illustration only. Never present one as a screenshot, a menu, or proof." — a stricter house rule than X requires (X only bans *deceptive* sharing likely to cause *harm*; the account's rule bans presenting AI images as real at all, regardless of harm). Already covered and exceeds the X rule. `reference/x-algorithm.md` A15 also notes DMCA-flagged media is dropped from recommendations (a ranking fact, not a Rule). **Fixed check possible** (flag any image without a "generated" provenance tag presented alongside screenshot-style text) — not implemented, but the house rule is broader than needed so risk is low.

### Copyright and trademark

> "You may not violate others' intellectual property rights, including copyright and trademark."
https://help.x.com/en/rules-and-policies/x-rules — **EVERYONE**. Copyright policy detail (DMCA process, repeat-infringer suspension): https://help.x.com/en/rules-and-policies/copyright-policy.
Repo: `voice/exit-zero.md` "Images" — "Never attach vendor press images or anything in `images/sources/`." Directly covers the highest-risk case (using a vendor's own marketing image). **Fixed check implemented conceptually** (the `images/sources/` directory is excluded by convention; `scripts/post_thread.py`'s docstring says it "Refuses when... media comes from `images/sources/`" — a real fixed check).

### Paid Partnerships

> "Posts that are part of a Paid Partnership published as an organic Post must have the 'Paid Partnership' disclosure on... Once the toggle is on and you indicate that the post is on behalf of a third party, your content will be automatically labeled."
https://help.x.com/en/rules-and-policies/paid-partnerships-policy — **EVERYONE who does a paid partnership** (not gated by account tier; gated by the *transaction*: gifted product, payment, commission/affiliate link, or ambassador deal).
Also: a fixed list of "Prohibited Industries" for paid-partnership promotion (adult, alcohol, drugs, dating, geo-political/social-crisis commercial use, supplements, pharma, tobacco, weapons, weight-loss) — same URL, same binding scope.
Repo: **not covered at all.** No format skill or gate check mentions the Paid Partnership toggle or affiliate-link/gifted-product disclosure. Relevant now if PAID → FREE posts ever involve an affiliate link or a gifted tool from a maker (`voice/exit-zero.md` "Makers" section describes shout-outs and quotes but doesn't address whether any compensation/gifting occurs — currently it doesn't, per the repo's design, but worth a flag for the planned multi-user product). **Fixed check possible**: if a draft's `CLAIMS.md`/metadata records an affiliate link or gifted product, the gate could require a disclosure line/flag before `/approve`.

### Sensitive content / media marking

> "By appropriately marking your media settings, X can identify potentially sensitive content that other users may not wish to see, such as violence or nudity... X may also use automated techniques to detect and label potentially sensitive media, and to detect and label accounts that frequently post potentially sensitive media."
https://help.x.com/en/rules-and-policies/media-settings — **EVERYONE who posts such media** (not gated by tier).
Repo: not applicable to the current account's content (device/tech tips); not covered, correctly, as out of scope today. Relevant for the planned product's other users. **Needs human/model judgment** to classify an image as sensitive; the *marking action itself* (ticking the flag before posting) is a manual X UI step outside this tool's control, since posting stays manual.

### Creator Monetization Standards (binds creators who monetize)

Eligibility (excerpt):
> "You must have an active Premium, Premium Business, or Premium Organizations subscription... You maintain 2,000 or more active followers with Premium... subscriptions. Your posts have 5,000,000 or more organic impressions within the last 3 months."
https://help.x.com/en/rules-and-policies/content-monetization-standards — **SOME USERS** (Premium-subscribed, threshold-meeting creators pursuing Subscriptions specifically; Original Content Rewards has its own, lower/different thresholds — see below).

Conduct standards (excerpt):
> "Platform manipulation and spam: you must not engage in the type of behavior that is prohibited by our platform manipulation and spam policy... Videos depicting armed conflict: For any AI generated content depicting armed conflict, you must add a clear disclosure that it is AI generated."
Same URL — **SOME USERS** (monetizing creators).

Content standards — a fixed list of ineligible-for-monetization categories: illegal/regulated goods, adult/sexual content, graphic/violent content, hate/extremist content, "sensitive content" (tragedy, conflict, mass violence, "exploitation of controversial political or social issues"), strong language.
Same URL — **SOME USERS**.
Repo: not covered — the account isn't currently enrolled in a monetization program per anything in the repo, so these don't yet bind it. If/when it enrolls, several of these categories are **fixed-checkable by keyword/topic list** (drugs, weapons, gambling brand names, profanity list), while "hate/extremist," "graphic," and "exploitation of controversial political or social issues" need **human/model judgment**.

### Original Content Rewards Program (current program; replaced Creator Revenue Sharing 2026-09-07)

Program terms (verbatim, from https://help.x.com/en/using-x/original-content-rewards — **SOME USERS**, enrolled accounts only):

- Eligibility: "Hold an active X Premium, Premium+ or Premium Business subscription... Have at least 500,000 Home Timeline impressions from verified users in the last 90 days... Have at least 500 verified followers."
- Continuous eligibility conduct rules:
  > "Do not use automated tools, bots, or any tool or software to artificially generate likes, follows, views, comments, or shares."
  > "Do not tamper with the program, payout system, or recommendation algorithms."
  > "Do not solicit engagements: repeatedly instructing users to engage with posts, such as asking to like, reply, bookmark, follow, or repost."
- Content ineligibility list includes:
  > "Was created or posted using automated means"
  > "Contains disinformation or misleading content"
  > "Has a helpful Community Note"
  > "It is exclusively focused on monetization coaching, monetization discussion, or maximizing payouts"

Repo coverage: `scripts/post_thread.py` lines 52-63 (the `SOLICIT_RE` block) implement the "do not solicit engagements" rule as a **fixed regex check** today, and the code comment already correctly cites "X's Original Content Rewards rules" — this matches the current, live program name and wording exactly (verified word-for-word against the fetch above). `voice/exit-zero.md` "Asking for engagement" section quotes the same rule. **Classification nuance**: this rule is contractually **SOME USERS** (Original Content Rewards enrollees), even though the repo currently applies it to every draft — a defensible house-style choice (it's also good writing), but worth the operator knowing the rule itself doesn't bind a non-enrolled account. "Was created or posted using automated means" is **not currently checked anywhere** in the repo (see Open Questions — it's unclear what would even constitute a fixed check for it).

### Character limits and posting limits

> "Longer posts: Want to post more than 280 characters? Longer posts allow subscribers to post up to 25,000 characters... Everyone will be able to read longer posts, but only Premium subscribers can create them."
https://help.x.com/en/using-x/x-premium — **SOME USERS** (Premium/Basic/Premium+/Business subscribers can post over 280; everyone can read).
> "50 original posts and 200 replies per day for unverified accounts... post limit of 2,400 updates per day... broken down into smaller limits for semi-hourly intervals... These limits include actions from all devices, including web, mobile, phone, API, etc."
https://help.x.com/en/rules-and-policies/x-limits — **EVERYONE** (numbers vary by verification tier, but the existence of a technical cap binds every account).
Repo: `scripts/post_thread.py` (`X_ONE_WEIGHT`, `X_URL_LENGTH`, `ROOT_LIMIT`, `SHORT_LIMIT`, `LONG_POST` string) already implements X's own weighted character counting and enforces the free-tier 280 limit as a **fixed check**, correctly. Daily post-count limits are **not checked** — low risk at this account's cadence (about one thread every other day) but worth a guard if the planned product supports higher-volume posters.

### Developer Agreement (binds the product, as an X API client)

> "(k) use the X API or X Content to fine-tune or train a foundation or frontier model"
— listed under "Restrictions on Use," III.A. https://docs.x.com/developer-terms/agreement — **TOOL**.
> "Commercial Use" (…) "by or for a business... or... as part of a product or service that is monetized" — Section III.B. Same URL — **TOOL**.
> "The Pay-Per-Use, Basic, and Pro plans... are designed for hobbyists, commercial prototyping, initial development, early-stage X product integrations, and supporting applications with a limited number of end-users. If you use the X API beyond this scope, then you must apply... to an Enterprise plan." — Section III.L/M. Same URL — **TOOL**.
Repo: `reference/x-api.md` documents the current Pay-Per-Use plan, its $10/cycle spending cap, and read-only scope — consistent with today's single-account, low-volume use. Not yet relevant at multi-user product scale, but the Developer Agreement's own text already puts a ceiling on how far the current API approach scales before an Enterprise agreement (a business/legal step, not a code fix) is required. No code can check "have we exceeded a hobbyist use case" — that's a **business decision**, not a fixed check.

### Developer Policy (binds the product)

> "The use of the X API and developer products to create spam, or engage in any form of platform manipulation, is prohibited... Never post identical or substantially similar content across multiple accounts... Never perform bulk, aggressive, or spammy actions, including bulk following." — "Spam, bots, and automation" section. https://docs.x.com/developer-terms/policy — **TOOL** (governs what the product may automate) and **EVERYONE** (the underlying spam/manipulation rule it points back to).
> "Your service shouldn't compensate people to take actions on X... you may not sell or receive monetary or virtual compensation for any X actions." — "Pay to engage" section. Same URL — **TOOL**.
> "You must clearly identify your service so that people can understand its source and purpose." — "Service authenticity" section. Same URL — **TOOL**.
Repo: none of this is currently relevant since the product never writes to X (read-only Keychain keys, per `reference/x-api.md` P1) — but it's a hard boundary on any future feature that would post, reply, or follow on a user's behalf. **Not a fixed check today because the capability doesn't exist**; if it's ever added, per-user express consent (not just OAuth) would need to be a **product gate**, and "pay to engage" would need to be a **policy the product refuses to build**, not something code can catch after the fact.

### Automation Rules (binds the product; referenced by the Developer Agreement)

> "You may only take automated actions through another X user's account if you: clearly describe to the user the types of automated actions that will occur; receive express consent from the user to take those automated actions; and immediately honor a user's request to opt-out." — Section II.A. https://help.x.com/en/rules-and-policies/x-automation — **TOOL**.
> "You may leverage artificial intelligence (AI) technologies to create automated reply bots... However... the deployment or operation of any AI reply bot requires prior written and explicit approval from X." — Section II.B.3, "AI-Powered Automated Replies." Same URL — **TOOL**.
> "Automated following/unfollowing: You may not follow or unfollow X accounts in a bulk, aggressive, or indiscriminate manner... Note that applications that claim to get users more followers are also prohibited." — Section II.D. Same URL — **TOOL** and, by cross-reference, **EVERYONE** (the underlying aggressive-following ban is a general X Rule too).
Repo: N/A today — the product's core design (manual copy-paste, `AGENTS.md` "Never post, schedule, or call an X write API") keeps it outside every Automation Rule trigger. This is worth stating explicitly as the reason the current architecture is safe, and as the reason any future "auto-post" or "AI auto-reply" feature would need X's prior written approval before shipping, per this rule.

---

## Open questions (for the operator; nothing here is decided)

1. **Does AI-drafted, human-edited, manually-pasted content count as "created... using automated means" for Original Content Rewards eligibility?** X's help pages never define "automated means" (confirmed absent from every page fetched above, matching the existing note in `AGENTS.md`/`voice/exit-zero.md`). This is the single biggest unresolved question for a product whose entire pitch is AI-assisted drafting with mandatory human approval before manual posting. Unconfirmed either way — worth X support/legal clarification before any user of the planned product enrolls in Original Content Rewards.
2. **Is "no solicit engagement" a universal product rule, or a per-profile monetization setting?** Since the rule only contractually binds Original Content Rewards enrollees, should the planned product still refuse solicitation language for every user by default (as this repo does today, arguably for good editorial reasons), or make it a toggle tied to "I'm enrolled in / plan to enroll in Original Content Rewards"?
3. **At what usage level does the planned product's API access cross from Pay-Per-Use/Basic/Pro into "beyond... hobbyist... limited end-users," requiring an Enterprise agreement with X?** This is a business/legal threshold X hasn't published a hard number for (found only "hobbyist... early-stage... limited end-users" — subjective wording, unconfirmed as a hard trigger).
4. **Does the product's "learn from results" loop ever touch X Content (post text) in a training/fine-tuning pipeline**, as opposed to reading engagement numbers (impressions/likes/follow deltas) to steer a prompt or a heuristic each session? The Developer Agreement bans the former outright; the latter appears to be outside that clause's plain wording, but this is this researcher's reading, not a confirmed X position — worth a legal read given it's core to the product's premise.
5. **Should Paid Partnership disclosure become a first-class field in the draft pipeline** (a `CLAIMS.md`/metadata flag that the gate checks) given it's a universal, transaction-triggered rule that today's format skills don't mention at all?
6. **Sensitive-media marking**: since posting stays manual, is there any value in the product prompting the operator ("mark this as sensitive before you paste it") for image-heavy formats, or is that entirely out of scope since the X posting UI already asks?
7. **Amplify Pre-Roll Guidelines and Ads Policies were not reviewed in depth** (out of scope unless the product or its users run ads or are Amplify publishers) — flag if that ever becomes relevant.
8. One page could not be reached directly by automated fetch (`WebFetch` returned 402/403 on `help.x.com` and `legal.x.com` domains generally); all quotes above were instead retrieved via a live, authenticated-as-nobody Chrome browser session (`claude-in-chrome`) reading the same public URLs, so nothing here is a search-engine cache — every quote/URL pair above is a direct, current fetch except where noted.
