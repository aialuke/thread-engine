# Exit Zero voice

Shared tone for every format. Format rules live in `.claude/skills/format-*/`. For settings threads, the gold transcripts in `examples/` win only on beat order after the opening; the root's opening and length follow `.claude/skills/hidden-settings/SKILL.md`.

## Rules

- Short sentences. Fragments allowed.
- Never the same verb stem twice in one line ("makes … making", "building … build").
- One villain per post or thread.
- Concrete numbers only if sourced this session (truth budget below).
- The root post stands alone: a stranger who sees only the root gets the whole payoff.
- Locale default: Australia. Prices in AUD. Times in Australia/Brisbane.

## What every post delivers

The operator's own test, verdict, numbers, voice and lesson are the thing each post delivers. AI helps draft and the pipeline makes clips, but a generated clip or text is the evidence, never the product. X's rewards program makes a post ineligible if it "was created or posted using automated means" and doesn't define the phrase; posting stays manual, and the human judgement has to be visible in the post.

## Texture

Dry. Specific. Competent. Receipts.

Skip-if-missing is voice. Cut a card before guessing a path or a claim.

## Banned phrases

These read as engagement-farm or brochure posting, which is the genre this account is built against. The gate refuses all of them except "unlock", which stays guidance only because it is also a real settings word (Face ID unlock).

game changer · unlock · most people don't know · wait for it · 🚨🔥👇 · juggernaut · neural graph · zero server dependency · Hollywood-grade · drop-in replacement · let's grow together

## Farm tells (cut)

"You're only using N% of your Mac." Fake urgency. Em-dash stacks. Omniscient expert with no scene. Swapping a look every photo. "Drop a hi". Asking for thoughts instead of a specific reply. Brochure words ("elite", "amazing", "seamless") and feature sheets copied from a product page; the PAID → FREE roster is full of them (`queue/paid-free-roster.md`).

## Asking for engagement

X's rewards rules: "Do not solicit engagements: repeatedly instructing users to engage with posts, such as asking to like, reply, bookmark, follow, or repost." Breaking it can remove the account from the program.

- Ask a real question ("Which TV is yours? The menus differ."), never an instruction ("Reply with your model", "Save this before…", "Drop it below", "Follow for more", "Like and repost").
- The gate refuses these instructions (`scripts/post_thread.py`).

## Truth budget

Every figure is sourced this session: an official page, `PATHS.md` / `CLAIMS.md`, or the operator. Invented dB, %, and $ amounts stay out.

## Images

- AI-made images are illustration only. Never present one as a screenshot, a menu, or proof.
- Screenshots are real, taken on a real device.
- Never attach vendor press images or anything in `images/sources/`.

## Replies

- Never post the same reply twice, and never reply in bulk. On 22 Sep one line went out 12 times in 3 minutes, and a bare "👋" 6 times; duplicate reply text is clustered as spam (algorithm fact A13).
- Keep volume to what the operator would write by hand. The reply scorer sees the last 24 hours' reply count (A12); the peak so far was 68.
- Grok may suggest what a reply should say. The operator writes it in their own words (the reply scorer also sees whether a reply was pasted, A12).
- Politics and news: reply from this account when the story connects to tech (for example OpenAI and the government breach). Political replies with no tech link are the operator's call. X's monetisation standards list "exploitation of controversial political or social issues" as restricted content, and politics earned 1 follow from 5,901 impressions (18–24 Sep export).
- Off-topic replies and bare greetings ("gm", "👋") are ranked no better than spam (X's head of product, 2026). A reply earns its place by adding something specific to that conversation.
- Under your own post, answer the point the person raised in one or two sentences, from the draft's `CLAIMS.md` or `REPLIES.md` where it has one. Never edit a live post to add a caveat; say it in a reply.

## Networking

- Personal networking, yes: reply to a builder's progress post by naming the project and asking a real question.
- Bare "👋", repeated lines and "drop a hi" posts, no.
- An occasional connect post is allowed in the `other` lane, at most 1 in 15 originals, written for that moment and asked as a real question. "Drop a hi" and "drop it below" are instructions to engage, and the gate refuses them. The "Drop a hi" post brought 13 of the 19 follows on 18–24 Sep, so the loop watches whether those followers ever engage.

## Makers

The people who make the free tools the account posts about (PAID → FREE, `.claude/skills/format-tool-swap/SKILL.md`).

- Tag a free tool's organisation account, checked with `python3 scripts/x_api.py user <handle>` that session. Never tag a person, and never a premium vendor.
- Never post the same shout-out twice, and never paste one line under several makers' posts (A13).
- One maker touch a day: a specific reply on a maker's post, a quote of their release, or the shout-out under a PAID → FREE post.
- Repost only a maker's release post, never your own post and never someone's mega-list of alternatives. A repost with a caption is a quote.
- Quote only a maker's news. Never quote a premium vendor (Adobe, Maxon, Streamlabs) to pick a fight.
- A quote of a maker's release most likely counts toward X's rewards program (its rules exclude replies, not quotes); a reply doesn't.
- Off X, a real GitHub discussion, bug report or Discord answer is often seen by the maker more than an @.

## Boosting

- Don't boost. Boosted impressions are excluded from X's rewards program, and its terms list promoted posts among the ways of inflating views that can cost payouts and membership. The one boost so far (the tool-swap) bought about 2,000 impressions, about 4 profile visits and no follows.
- If a boost ever happens anyway, the loop marks the post non-organic (over 10% non-organic reach) and keeps it out of every comparison.
