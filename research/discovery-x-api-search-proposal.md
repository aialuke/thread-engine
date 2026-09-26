# Discovery via X API search: decision and proposal (26 Sep 2026)

For the next session, which picks this up once the Discovery test is settled. It comes from the Discovery test pilot, run on 26 Sep (`research/discovery-test/plan.md`, `HANDOFF.md`). Raw data and the facts table are in `research/discovery-test/private/` (gitignored; `facts.md` holds every figure below with its call ids). This file quotes no one else's posts.

**Decided 26 Sep (D88, `reviews/ui-direction.md`): Grok is dropped from the product.** So D-A1, D-A2 and D-A3 are settled: X API search is the source for every Discovery job. Stages 1 and 3 now test X API query design only (sorts, phrasings, spam control), not the source. D-C, D-D and D-E stay hypotheses.

**Status (before D88):** interim, from the pilot. Revised after Codex's blind adversarial review (`research/discovery-test/codex-proposal-review.md`). Only §1.1 is proposed as settled. Everything in §1.2 is a hypothesis for its job's stage to confirm or overturn. Spam and off-topic handling has its own plan (`research/discovery-test/spam-research-plan.md`).

## 1. Decisions

### 1.1 Proposed as settled now (supported by the pilot's API facts)

- **D-B (narrow). Stable X API mechanics live in product code,** not in skill prose or model output:
  - X API v2 syntax only, refusing website operators;
  - the 512-character check;
  - exact-window enforcement with `start_time`/`end_time`;
  - one eligibility rule for every source: X says English, not a retweet, inside the window;
  - logging of every sighting (source, query variant, sort, rank, time);
  - a backend cost cap per search run.

  Spam and off-topic rules are **not** part of this. They stay versioned, job-specific and able to pass uncertain posts through until tested.

### 1.2 Hypotheses, decided job by job after each stage

| # | Hypothesis | Decided after |
|---|---|---|
| D-A1 | Worth joining's source is X API search, with no Grok | Stage 1 |
| D-A2 | Demand's source is X API search, with queries built from model-supplied phrases. **Stage 2 (26 Sep):** X API wins per dollar in both Demand cells (tech, comedy). Grok found 15 of 54 useful posts that X API didn't, about 11 likely through semantic search (about 1 in 5), mostly for reaction and running-joke ideas (`private/stage-2.md`). The plan's tie-breaker, simplicity, favours dropping Grok; the cost is those posts | Operator, from Stage 2's data |
| D-A3 | Tool research's source is X API search | Stage 3 |
| D-C | MJ2 returns **structured phrase groups with explicit AND/OR composition**, not a query string, and any engine can fill it. The first draft's asking, alternative, products shape fits only the free-alternative idea (Codex High 3) | Once all four Stage 2 Demand ideas can be expressed in it without special cases |
| D-D | Search settings split into the user's setup, bounded Weights and rules for everyone. The Weight ranges below are **experimental defaults**, promoted to Weights only when a stage has tested them (Codex Low 1) | Per job, after its stage |
| D-E | The loop learns which phrasings produce leads. Needs every sighting kept (multi-touch), rotation or holdouts between variants, and a minimum sample before a Weight moves (Codex Medium 4) | After Stage 2 shows how often the same post is found by several variants |

## 2. Evidence

**What the pilot measured:**
- Grok's prompt styles for one Demand idea ("people asking for a free alternative to a paid creator or developer tool"), 24 h window, rerun with fixes.
- X API search on the same idea and window.
- X API facts F1–F11 and Grok facts G1–G6.
- All scoring by Codex, blind: text only, opaque ids, sources hidden. I re-scored 20%.

**How much this evidence can bear** (Codex review, High 1, 2 and 4):
- One idea, one 24 h window, about 5 genuine posts.
- Unequal query sets: X API ran one query family, while Grok's styles ran two or three phrasings.
- The X API pool mixes sort orders and filters from P1, P1b, P1c and P1d.
- Codex's relevance errors are systematic, not random (they moved the headline from 8 against 2 to 5 against 1–2).
- Treat every comparison below as direction, not a result.

### Demand: X API against Grok, scored together (39 posts)

| Source | Posts | Good (on-idea, a real person) | Spam |
|---|---|---|---|
| X API search (one query family) | 14 | 1–2 | 8 |
| Grok, all five styles | 30 | 5 (Codex said 8; 3 were video-game questions it scored too kindly) | 9 |
| Grok, semantic search only (G-hinted) | 14 | **0** | 4 |

- **Semantic search added no good posts in this test.** Grok's advantage came from **keyword phrasings** X API didn't run:
  - "is there a free", "any free alternative";
  - "free alternative" without a category word.
  X API ran one query family; the second frozen variant, which contains "is there a free", wasn't run.
- **The best Grok style (G-self, Grok's own recommended prompt)** found 9 of 11 good posts in its own scoring. Its two keyword queries were this test's frozen X API queries, translated into X's website syntax.
- **Pools are thin:** about 5 genuine requests in 24 hours, among many spam posts from both sources.

### What makes a query find demand (from the 9 good posts)

| Lesson | Evidence |
|---|---|
| Search the asking words ("is there a free", "anyone know", "looking for") joined with the alternative words | The good posts are questions. G-free's best query was *asking phrase* AND *alternative phrase* |
| Keep replies for Demand | 5 of 9 good posts were replies; `-is:reply` removed them all |
| No engagement floor for Demand | 7 of 9 had 0 likes; `min_likes:5` left 3 posts in 24 h |
| Don't require a category word | `(tool OR app OR software)` missed a request naming the product directly |
| Name the paid products | Grok's low-effort G-free added a list of paid products; the PAID → FREE roster has one |
| Run 2–3 narrow queries of 10, not one broad one | Every Grok style did; at $0.005 a post, 3 × 10 ≈ $0.15 |

### X API facts settled

- Query limit **512 characters**. X's own error: "query length must be <= 512".
- `min_likes:`, `min_replies:` and `-is:reply` work on pay-per-use.
- `sort_order=relevancy` reorders the same pool (7 of 10 overlap). It ranks up older, high-engagement posts (median 16 h against 13 h; top post 1,333 likes against 2).
- Fresh: the following timeline's newest post was 25 minutes old, and search is near real time.
- The counts and usage endpoints need an OAuth 2.0 app-only Bearer token. A product app has one; the factory's Keychain doesn't.
- Cost: the console fell $0.34 against the harness's $0.455 estimate. That's one aggregate reading; same-day repeats, author reads and failed calls can't be separated. Use a range (estimate × 0.75 to × 1.0) until billing is measured in isolation (Codex Medium 5).

### Grok facts that bear on the choice

- **Semantic search is fresh:** the newest hit was 1.1 h old, once the dates are set right.
- **The date rule:** `to_date` is exclusive and the days are UTC. Grok sets it wrong itself: it used 25→26 for "last 24 hours", which misses today.
- **0 invented, 0 misquoted** across about 100 checked posts. Checking still needs the X API, and the CLI shows Grok's retelling, never raw results.
- **Grok's own choice of posts is a poor filter.** Its "kept" flag kept 1 of G-self's 9 good posts, and steered "kept" 2 spam posts.
- **Cost and limits:**
  - $0.05–0.19 per prompt on the Grok Build subscription;
  - the subscription balance ran out after $0.63;
  - a product would need the xAI API with zero data retention for other people's posts (xAI terms §11.2);
  - the search runs outside the backend (conflict K11).

## 3. Proposal

### 3.1 Query builder (product code)

- **Settled mechanics (§1.1):** X API v2 syntax only, refusing website operators (`min_faves:`, `-filter:`, `within_time:`, `since:`); the 512-character check before sending; exact windows; eligibility; logging; the cost cap.
- **Per-job defaults, experimental until each stage** (the pilot tested only the Demand row, for one idea):

| Job | Replies | Engagement floor | Window | Sort |
|---|---|---|---|---|
| Demand | kept | none | 24 h, `start_time`/`end_time` | newest first **and** relevancy, both reported in Stage 2 (Codex High 2) |
| Worth joining | `-is:reply` | `min_replies:` (a Weight) | 6 h | newest first |
| Tool research | kept | none | 7 days | relevancy (engagement-weighted), logged |

- Spam and off-topic control: versioned, job-specific rules that pass uncertain posts through, set by the spam research (§5).
- Cost cap per search run, enforced in the backend (L2-C3). Default 2–3 queries × 10 posts.

### 3.2 MJ2 output shape (any engine), a hypothesis (D-C)

A general form: named phrase groups, plus how they combine.

```json
{"groups": {"asking": ["is there a free", "anyone know", "looking for"],
            "target": ["free alternative", "free version", "open source alternative"],
            "products": ["Canva", "Premiere"]},
 "queries": [["asking", "target"], ["asking", "products"]],
 "exclude": ["game"]}
```

Each inner list is one query: groups joined by AND, phrases within a group by OR. Code builds and checks each one: lengths, characters, the 512 limit, API syntax. A model can't mix syntaxes or drop the job's defaults.

The pilot's free-alternative idea fits this. It has to be checked against the other three Demand ideas before it's settled:
- frustration with coding agents: complaint words AND tool names;
- collective annoyance: reaction phrases, no fixed target;
- running jokes: meme words AND a current event.

### 3.3 Profile and Weights (D62–D64), a hypothesis (D-D)

- **Setup:** topics, the product list (roster or the user's own), language.
- **Experimental defaults**, not yet Weights: queries per search (2–3), results per query (10–20), the Worth-joining reply floor (1–10), phrase-group preference. Each becomes a bounded Weight only once its stage has tested it.
- **Rules for everyone (code):** syntax, limit, eligibility, the cost cap. The spam lists are versioned and vendor-maintained (§5), not fixed rules.

### 3.4 Learning (D42), a hypothesis (D-E)

- Each lead keeps **every** sighting: query variant, phrase groups, sort, rank and time. One post found by several variants is common (pilot: 3 good posts found by four styles, 5 by both sources).
- The outcomes:
  - the user uses or dismisses a Worth-joining lead;
  - a Demand lead becomes a post.
- Learning needs:
  - controlled rotation, or holdouts, between variants;
  - an explicit rule for sharing credit between variants that found the same post;
  - a minimum sample before a lesson moves a Weight.

## 4. Changes this implies in existing documents

| Document | Change |
|---|---|
| `research/layer-1-switches-profiles.md` N12, MJ2 | After Stage 2 confirms D-A2 and D-C: "the model writes the query, Grok returns `SEARCH_SCHEMA`" becomes "the model returns phrase groups; code builds and runs X API queries" |
| same, N18, MJ3, W10 | After Stage 1: reply leads come from the same builder with Worth joining's defaults |
| `research/layer-2-x-data-tiers.md` L2-C6 | Pilot evidence added, labelled directional: semantic search showed no measured value on one Demand idea |
| same, L2-C7 | Unchanged, but Grok without an X API check is weaker on the evidence (terms, pool size, no raw output) |
| `reviews/ui-direction.md` D62–D64 | Search settings named once D-D is confirmed |
| Factory (optional, now) | `.claude/skills/next/SKILL.md:46`: drop `-filter:replies` from the demand example (replies held 5 of 9 good posts) |

## 5. Open: spam and off-topic (plan: `research/discovery-test/spam-research-plan.md`)

What the pilot showed:
- About half of retrieved posts from both sources were spam or promotion: X API 8 of 14, Grok 9 of 30. The types seen:
  - premium-account selling (10 of 10 on one Grok keyword search, 26 Sep);
  - promotional "paid vs free" listicles;
  - engagement bait;
  - product marketing.
- Off-topic lookalikes: video-game "free version" questions matched the demand phrasings.
- The frozen Tool research queries carry a spam-control variant (`-is:nullcast`, `-has:links`, `-giveaway`, `-discount`), not yet tested.

Its result replaces this section.

## 6. What's still unmeasured

- **Worth joining and Tool research:** no pilot data (Stages 1 and 3).
- **Only one idea and one window,** with small numbers. Codex is lenient on relevance even under the tightened brief (the game questions). From Stage 1 on, every positive and every unclear post gets a second, independent score. Disagreements are settled and agreement is reported per axis.
- **Per-step X billing:** only the pilot total was read, by operator choice.
- **Whether a model's extra phrasings recover everything semantic search finds on other ideas:** Stage 2, with all four demand ideas, is the test.
