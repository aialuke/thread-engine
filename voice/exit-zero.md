# Exit Zero voice

Shared tone for every format. Format rules live in `.claude/skills/format-*/`. For settings threads, the gold transcripts in `examples/` win only on beat order after the opening; the root's opening and length follow `.claude/skills/hidden-settings/SKILL.md`.

## Rules

- Short sentences. Fragments allowed.
- Never the same verb stem twice in one line ("makes … making", "building … build").
- One villain per post or thread.
- Concrete numbers only if the draft's verify run sourced them (truth budget below).
- The root post stands alone: a stranger who sees only the root gets the whole payoff.
- Locale default: Australia. Prices in AUD. Times in Australia/Brisbane.

## What every post delivers

Each post delivers the operator's own test, verdict, numbers, voice and lesson, with the human judgement visible in the post. AI drafts and the pipeline makes clips; a generated clip or text is evidence, never the product. The reason: X's rewards program makes a post ineligible if it "was created or posted using automated means".

## Texture

Dry. Specific. Competent. Receipts.

Skip-if-missing is voice. Cut a card before guessing a path or a claim.

## Banned phrases

The gate holds the list (`BANNED_RE` in `scripts/post_thread.py`) and refuses every match. Write plainly, like a builder reporting a result, and it never fires. Brochure and engagement-farm phrasing is the genre this account is built against.

## Farm tells (cut)

"You're only using N% of your Mac." Fake urgency. Em-dash stacks. Omniscient expert with no scene. Swapping a look every photo. Asking for thoughts instead of a specific reply. Brochure words ("elite", "amazing", "seamless") and feature sheets copied from a product page; the PAID → FREE roster is full of them (`queue/paid-free-roster.md`).

## Asking for engagement

End a post with one real question that only a reader of that post could answer ("Which TV is yours? The menus differ."). The gate refuses instructions to engage (`scripts/post_thread.py`).

X's rewards rules: "Do not solicit engagements: repeatedly instructing users to engage with posts, such as asking to like, reply, bookmark, follow, or repost." Breaking it can remove the account from the program.

## Truth budget

Every figure is sourced by the draft's verify run: an official page, a `PATHS.md` / `CLAIMS.md` row dated in that run, or the operator. Later sessions rely on the dated rows. Invented dB, %, and $ amounts stay out.

## Images

- AI-made images are illustration only. Never present one as a screenshot, a menu, or proof.
- Screenshots are real, taken on a real device.
- Never attach vendor press images or anything in `images/sources/`.

## Replies

- Every reply is written once, for one conversation. Duplicate reply text is clustered as spam (algorithm fact A13).
- Keep volume to what the operator would write by hand. The reply scorer sees the last 24 hours' reply count (A12).
- Give the point a reply should make, never paste-ready text. The operator writes every reply in their own words (the reply scorer also sees whether a reply was pasted, A12).
- Politics and news: reply from this account when the story connects to tech (for example OpenAI and the government breach). Political replies with no tech link are the operator's call. X's monetisation standards list "exploitation of controversial political or social issues" as restricted content.
- A reply earns its place by adding something specific to that conversation; X ranks off-topic replies and bare greetings no better than spam (X's head of product, 2026).
- Under your own post, answer the point the person raised in one or two sentences, from the draft's `CLAIMS.md` or `REPLIES.md` where it has one. Never edit a live post to add a caveat; say it in a reply.

## Networking

- Personal networking, yes: reply to a builder's progress post by naming the project and asking a real question.
- An occasional connect post is allowed in the `other` lane, at most 1 in 15 originals, written for that moment and asked as a real question (Asking for engagement). The loop watches whether followers it brings ever engage.

## Makers

The people who make the free tools the account posts about (PAID → FREE, `.claude/skills/format-tool-swap/SKILL.md`).

- Tag a free tool's organisation account, checked with `python3 scripts/x_api.py user <handle>` that session. Never tag a person, and never a premium vendor.
- A shout-out is a reply, so the Replies no-repeat rule covers it: never one line under several makers' posts (A13).
- One maker touch a day: a specific reply on a maker's post, a quote of their release, or the shout-out under a PAID → FREE post.
- Repost only a maker's release post, never your own post and never someone's mega-list of alternatives. A repost with a caption is a quote.
- Quote only a maker's news. Never quote a premium vendor (Adobe, Maxon, Streamlabs) to pick a fight.
- A quote of a maker's release most likely counts toward X's rewards program (its rules exclude replies, not quotes); a reply doesn't.
- Off X, a real GitHub discussion, bug report or Discord answer is often seen by the maker more than an @.

## Boosting

- Don't boost. Boosted impressions are excluded from X's rewards program, and its terms list promoted posts among the ways of inflating views that can cost payouts and membership.
- If a boost ever happens anyway, the loop marks the post non-organic (over 10% non-organic reach) and keeps it out of every comparison.
