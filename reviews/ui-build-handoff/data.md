# Data section: where every figure on screen comes from

Mock source: `ui/mock/src/main_script.js` (`MS`), `ui/mock/src/build_body.py` (`BB`, iPhone template, also the base Mac reuses), `ui/mock/src/build_mac.py` (`BM`, Mac-only re-slicing and hard-coded strings). Line numbers are from the current files on `main` (25 Sep 2026, mock version 22, reviewed in `reviews/ui-review-2026-09-25.md`).

Read this alongside `reviews/ui-direction.md` (decisions D1–D36, build notes) and `reviews/ui-review-2026-09-25.md` (finding numbers referenced below as "review #n").

## 1. Every figure, date, count, handle and claim on screen

Columns: **id** | **where** | **mock value** | **kind** | **real source** | **refresh cadence in the real app** | **privacy**.

Kind legend: `real` = traces to a committed repo file this session; `example` = explicitly tagged "example" on screen, fictional but shaped like real output; `placeholder` = looks like real content but is a stand-in with no backing store (dotted handles, per AGENTS.md/voice rule); `derived` = computed client-side from other real values or from `Date.now()`; `hard-coded-time` = a literal date/time string with no live computation; `decision-text` = policy/voice prose, not a metric.

### Today (iPhone `BB.TODAY` / Mac `BM.MAC_HEADER` + `BM.HOME`)

| id | where | mock value | kind | real source | refresh cadence | privacy |
|---|---|---|---|---|---|---|
| DATA-T01 | Today header, `todayLabel` | e.g. "Thursday, 25 Sep · Brisbane" | derived | `brisDay(Date.now())`, `MS:226` | live, client clock | own |
| DATA-T02 | Today headline, `headline` | "Today's post needs your read." / stage-dependent variants | derived | computed from `s.stage`, `slotMs`, `Date.now()` (`MS:350-374`); stage itself is UI-only React state, not persisted | live | own |
| DATA-T03 | Health dot + line | "Daily check ran 20:00 last night. 6 posts are still too new to measure." | real (partly hard-coded) | "20:00" from `ops/launchd/com.exitzerocode.thread-engine.snapshot.plist:26-30` (Hour 20) and the last `snapshot ok` line in `ledger/runs.log:7` (`2026-09-24T10:00:05Z` = 20:00 Brisbane); "6 posts" = count of `snapshot: pending` rows in `ledger/SUMMARY.md:14-19` (6 rows). The sentence itself is a hard-coded template in `BB:489` (Today) / mirrored in Mac sidebar — the "6" is not read live by the mock, it was typed in once | daily, after each 20:00 `snapshot.py` run | own |
| DATA-T04 | Health-bad alert (canvas tweak `health=failed`) | "Last night's daily check didn't run, probably because the Mac was asleep." | derived/example | triggered by a canvas prop (`this.props.health`), not real data; real trigger would be "no `snapshot ok` line in the last ~30h" per `.claude/skills/next/SKILL.md:18` | live | own |
| DATA-T05 | First-hour card, "Posted {{foundAt}}. The first like came 3 minutes later…" | "3 minutes later" | example | tagged `example` on screen (`BB:64`); not read from any ledger field. Real field would be a per-post "time to first like" (see §2 Time-to-first-like) | not implemented; would be per-post, first API read after posting | own |
| DATA-T06 | First-hour "Answer now" | "@builder.two asked whether Bruno handles GraphQL." | placeholder | hard-coded string, `BB:67`; `@builder.two` is not in any real reply data structure (not `WAITING`, not ledger) | not implemented | other people's (if real) |
| DATA-T07 | Next-post card eyebrow + title | "Next post" / "PAID → FREE: developer tools" | real | matches `queue/topics.yaml` `paid-free-developer` row (`status: drafted`, `category: developer`) and `drafts/2026-09-24-paid-free-developer/01-hook.md:1-2`; the literal title string is hard-coded in `BB:81` and `BB:301`, not read from `topics.yaml` | on draft/queue change | own |
| DATA-T08 | `whenLabel` / `whenShort` / countdown | "Today, 06:00" / "in 2 h 14 m" etc. | derived | `TARGET = Date.parse('2026-09-25T06:00:00+10:00')` (`MS:162`), matches `queue/topics.yaml` `paid-free-developer.post_at: 2026-09-25 06:00 Australia/Brisbane`; countdown computed against `Date.now()` (`MS:319-329`) | live | own |
| DATA-T09 | Step tracker (Plan/Draft/Approve/Post/Measure) | 5 labels, current step highlighted | real (labels) / derived (state) | labels = D15 in `reviews/ui-direction.md:25`; current step = UI-only `stage` state, not persisted anywhere | n/a (UI state) | own |
| DATA-T10 | Progress: Verified followers | "27 of 500" | real | `ledger/activity/account.json:7` (`verified_followers: 27`, `baseline: true`, `date: 2026-09-24`); target 500 = X's rewards threshold, `ledger/SUMMARY.md:23` | daily (`ledger/activity/account.json.days[]`, appended by `snapshot.py`) | own |
| DATA-T11 | Progress bar width for verified followers | "5.4%" | derived | 27/500 = 5.4%, hard-coded in `BB:110` (`width: 5.4%`), not computed from the 27/500 values shown next to it | should be computed, not hard-coded | own |
| DATA-T12 | "About 37 a week reaches X's rewards bar in 90 days." | "37 a week" | real | `reviews/week-2026-W39.md:9` ("about 5 verified followers a day (37 a week)"); hard-coded string in `BB:111`, not recomputed from the live 27/500 gap | should be recomputed weekly | own |
| DATA-T13 | Qualified impressions | "337 of 500,000" | real | `ledger/activity/account.json:15-16` (`eligibility[0]`: `qualified_impressions: 337`, read `2026-09-24T02:29:55Z`); target 500,000 = `ledger/SUMMARY.md:23` | X's eligibility screen has no API; read is manual/occasional (no script reads it automatically — see gap in §4) | own |
| DATA-T14 | Qualified-impressions bar width | "0.07%" | derived | 337/500,000 = 0.0674%, hard-coded `BB:115` | own |
| DATA-T15 | "Counted when a verified viewer scrolls past half of one of your original posts…" | sentence | decision-text | X's public rewards-program rule, paraphrased; source not in repo (not from `reference/x-algorithm.md`, which is the ranking algorithm, not the rewards program rules) — **gap: this claim has no cited file in the repo** | n/a | public vendor rule |
| DATA-T16 | Followers | "36" | real | `ledger/activity/account.json:6` (`followers: 36`, `2026-09-24`, `baseline: true`) | daily | own |
| DATA-T17 | "First daily count 24 Sep; the trend starts from there" | sentence | real | same source as DATA-T16; `baseline: true` marks it as day 1 | n/a | own |
| DATA-T18 | Analytics export | "Thu 1 Oct" | hard-coded-time | not computed; `BB:124`. Derivable as "last export date (18–24 Sep, used for `reviews/week-2026-W39.md`) + 7 days", but the mock does not compute it | weekly, manual (X → Premium → Analytics → Content → Export; no API) | own |
| DATA-T19 | Capture teaser count | "{{captureCount}} captures waiting" | derived | count of `DEFAULTS.captures` not yet `turned` (`MS:175-178`); seed data is 2 examples (`c1`, `c2`), both tagged `example: true` | UI-state only, not persisted (see §2 Capture) | own |
| DATA-T20 | Proposed post (canvas `proposal=shown`) | "Build log: Claude, Codex and Grok reviewing the same plan", "Tue 29 Sep · 22:00 · no experiment" | example | tagged `example` on screen (`BB:163`); a fabricated `/next` proposal, not backed by any queue row | would be `/next`'s live proposal, written to `queue/topics.yaml` on accept (`status: planned`) per `.claude/skills/next/SKILL.md:50-65` | own |
| DATA-T21 | Guardrail chip on avatar / health dot amber | n/a (visual only) | derived | `s.healthBad` UI state | n/a | own |

### Post / cards (`BB.POST`, `BB.SOURCE_INNER`)

| id | where | mock value | kind | real source | refresh cadence | privacy |
|---|---|---|---|---|---|---|
| DATA-P01 | Card 1 full text | `CARD1` (PAID → FREE header, 3 swap lines) | real | word-for-word match to `drafts/2026-09-24-paid-free-developer/01-hook.md:1-11` (confirmed in review §8: "match word for word") | on draft edit (`saveEdit`, UI-only until a real backend exists) | own |
| DATA-P02 | Shout-out preview text | "@use_bruno thanks for keeping API collections in plain files, and for shipping again this week." | real | matches `drafts/2026-09-24-paid-free-developer/02-shoutout.md:1` and `CARD2` (`MS:17`) | same | own |
| DATA-P03 | Character count | "{{cardCount}} characters as X counts · your limit 600" | derived | `xLength()` in `MS:181-191`, a JS reimplementation of `scripts/post_thread.py x_length()` (confirmed matching: link=23, code point weighting; `scripts/post_thread.py:69`); limit 600 = `scripts/post_thread.py:33` `ROOT_LIMIT = 600` | live, recomputed on edit | own |
| DATA-P04 | Fold marker "Strangers stop here unless they tap Show more" | position | derived | computed from the 280-char running total of the card lines (`MS:393-395`), approximating X's client-side truncation; not X's real fold algorithm (build note, `reviews/ui-direction.md:68`, "Fold line (D16)") | live | own |
| DATA-P05 | Source sheet, per swap | `paidFact`, `paidSrc`, `quote`, `freeSrc`, `limit` | real | `SWAPS` (`MS:2-14`) = condensed from `drafts/2026-09-24-paid-free-developer/CLAIMS.md` rows for Bruno (lines 10-16), Beekeeper Studio (21-28), Cloudflare Tunnel (33-39) | one-time per draft, until claims re-checked | public vendor pages |
| DATA-P06 | Source sheet header "CHECKED 24 SEP" | date | real | `CLAIMS.md:2` ("Checked: 2026-09-24") | per fact-check run | own |
| DATA-P07 | "95 characters as X counts · account checked 24 Sep" | count + date | real | count = `xLength(CARD2)`; date = `CLAIMS.md:62` (`@use_bruno` handle check, `python3 scripts/x_api.py user use_bruno`, 2026-09-24) | account check should be re-run before each shout-out | public (vendor org account) |
| DATA-P08 | "This format has a fixed header, so there's no hook to choose." | sentence | decision-text | from `.claude/skills/format-tool-swap/SKILL.md`'s fixed-header rule (not read in this session, referenced by `AGENTS.md` layout list) | n/a | own |

### Ready / Posting (`BB.READY`)

| id | where | mock value | kind | real source | refresh cadence | privacy |
|---|---|---|---|---|---|---|
| DATA-R01 | Final-check refusal reasons | e.g. "Card 1 asks for engagement" | derived | `gateRefusals()` in `MS:198-219`, a JS reimplementation of `scripts/post_thread.py card_refusals()` / `swap_root_refusals()` (`scripts/post_thread.py:86,180`) | live, recomputed on approve | own |
| DATA-R02 | Wait timer, shout-out window | "{{winStart}}–{{winEnd}}" = posted-time + 10 min to +20 min | derived | `WAIT_MS = 10*60000` (`MS:163`), matches `AGENTS.md`'s post_thread.py description ("a tool-swap's says to wait 10–20 minutes before the shout-out") and `drafts/…/CHECKLIST.md`/`POST.txt` convention | live | own |
| DATA-R03 | "Found it: posted {{foundAt}}." | timestamp | derived | `hhmm(Date.now())` at the moment "I've posted it" is tapped, in the mock; real app would poll `scripts/x_api.py`/read-only search for the just-posted root, not stored elsewhere yet | would be live, ~immediate after posting | own |
| DATA-R04 | "The first full read comes with the daily check on {{date}} at 20:00." | derived date | derived | `firstRead()` (`MS:234`): first 20:00 Brisbane check ≥36h after posting, matching `scripts/snapshot.py`'s 36–60h window (per AGENTS.md) and `ops/launchd/...plist` 20:00 schedule | live | own |

### Posts screen (`BB.POSTS`)

| id | where | mock value | kind | real source | refresh cadence | privacy |
|---|---|---|---|---|---|---|
| DATA-PS01 | "Also drafted" example | "Tool verdict: one fix, three reviewers", hook picker (3 `HOOKS` strings) | example | tagged `example` (`BB:306`); `HOOKS` (`MS:155-159`) are 3 fixed literal strings, not generated per draft — no script or skill in the repo currently produces hook candidates | not implemented; would need a hook-generation step in `/draft-thread` | own |
| DATA-PS02 | Queued list | `QUEUE` (`MS:44-49`): local-ai, productivity, privacy, storage, each with a `meta` tool list | real | matches `queue/topics.yaml` rows with `status: queued`, `format: tool-swap` (local-ai → Ollama/Cline; productivity → Obsidian/OnlyOffice; privacy → Bitwarden/AdGuard Home; storage → Syncthing/Nextcloud) | on `/next` or manual queue edit | own |
| DATA-PS03 | "The fact-check couldn't confirm one claim…" (canvas `draft=factcheck`) | sentence | example | canvas-prop-triggered, not real; real equivalent = a `VERIFY` row in a draft's `CLAIMS.md` per `voice/exit-zero.md` truth-budget rule | per draft run | own |
| DATA-PS04 | Posted list | `RPOSTS` (`MS:50-62`), 11 rows: title, lane, views, visits, follows, boosted flag | real | matches `ledger/SUMMARY.md:9-19` rows (see §3 for the one known numeric mismatch — review §6) and `reviews/week-2026-W39.md:16-26`. Titles ("Home Wi-Fi", "MacBook battery", etc.) are human labels with **no field in the ledger JSON** — only the kebab `slug` is stored (e.g. `home-wifi`); the display title is invented in the mock | daily snapshot + weekly export for follows | own |
| DATA-PS05 | "not counted" tag on the boosted post | flag | real | `RPOSTS[3].boosted: true` (`MS:54`) corresponds to `ledger/2102737637346095128.json`'s `nonorganic` object (`reason: "95% of 2,105 impressions non-organic (Premium Boost…)"`); the mock's `boosted` is a manually-set literal, not derived from the presence of a `nonorganic` key | should be derived: `post.nonorganic != null` | own |

### Capture (`BB.CAPTURE`)

| id | where | mock value | kind | real source | refresh cadence | privacy |
|---|---|---|---|---|---|---|
| DATA-CAP01 | Seed captures | c1 "Voice note · 0:42 … Codex and Claude disagreed…", c2 "Screenshot … Bruno collection … plain files" | example | `DEFAULTS.captures` (`MS:176-177`), both `example: true`; not backed by any file — no capture store exists in the repo | not implemented (see §2 Capture) | own |
| DATA-CAP02 | "From your readers" | "A reader asked how Grok compares with Codex and Claude Code…" | real | matches `reviews/week-2026-W39.md:77` reader question 1 | weekly review | own (reader is anonymous in text) |

### Replies (`BB.REPLIES`, `BB.WAITCARD`)

| id | where | mock value | kind | real source | refresh cadence | privacy |
|---|---|---|---|---|---|---|
| DATA-RP01 | "Waiting for you" cards | `WAITING` (`MS:30-37`), 3 entries: `@sec.minded` (breach reply, 8h), `@pixel.tools` (photo-editor suggestion, 14h), `@ship.daily` (builder reply, 1d) | placeholder | dotted handles per AGENTS.md convention ("Placeholder names: dots make them impossible X handles" — `MS:18`); the *content* (photo-editor suggestion) matches `reviews/week-2026-W39.md:78` reader question 2, but the "waiting/answered" mechanic itself has **no real data source** — see §4 gap on `referenced_tweets` | not implemented | other people's, anonymised |
| DATA-RP02 | "Worth joining" cards | `REPLIES` (`MS:19-29`), 3 entries: `@builder.one` (Codex reset story), `@lab.notes` (OpenAI breach logs), `@aus.indie` (NDIS leak) | placeholder | per `reviews/ui-direction.md:70` build note: "Worth joining" is `/next` chat output, i.e. transient text from a `/next` session, never written to a file. Content style matches what `/next`'s "Replies worth making today" section (`.claude/skills/next/SKILL.md:67-74`) would produce, via `scripts/x_read.py search` | would be live, from `/next`'s reply-leads step | other people's (public posts, via Grok-checked X read) |
| DATA-RP03 | Builders list | `BUILDERS` (`MS:38-43`), 4 entries with tags ("verified · follows you · you follow · on topic") | placeholder | no field anywhere tracks mutual-follow status or "on topic" per-person; entirely mock-only. Per `reviews/ui-direction.md` D28, this is a *decided* feature with **no data source yet** | not implemented (see §2 Builder/mutual) | other people's |
| DATA-RP04 | "2 mutuals on topic" | count | example | tagged `example` (`BB:412`); no computation exists | not implemented | own |
| DATA-RP05 | "Plus 37 greetings and connect requests this week." | "37" | example | tagged `example` (`BB:408`) per review finding #7 (fixed 25 Sep): "No reading of `ledger/activity/` gives 37… Tag it example" | not implemented; would need per-reply text classification | own |
| DATA-RP06 | Busiest-24h note | "Your busiest 24 hours (Wed to Thu) had 68 replies, and on 22 Sep one line went out 12 times." | real | 68 = `reviews/week-2026-W39.md:51` ("Busiest 24 hours: 68 replies from Wed 23 Sep 14:25"); 12 = `voice/exit-zero.md`'s Replies section ("On 22 Sep one line went out 12 times in 3 minutes") | weekly review + per-incident | own (about the account's own behaviour) |

### Results (`BB.RESULTS`, tabs Growth/Posts/Replies)

| id | where | mock value | kind | real source | refresh cadence | privacy |
|---|---|---|---|---|---|---|
| DATA-RES01 | Results header lines (D18) | "Every profile visit from an unboosted post came from one networking post." / "115 replies brought 14,220 views and 4 follows." | real | first line = `reviews/ui-direction.md:28` D18 (operator-edited 25 Sep to add "unboosted"), backed by `reviews/week-2026-W39.md:61-63` (all 20 visits from the connect pin); second line = `ledger/SUMMARY.md:38` reply row (115 items, 14,220 organic, 33 visits, 4 follows) — note the header cites 14,220 as "views" but the ledger column is "Organic impressions" | weekly | own |
| DATA-RES02 | Growth KPI: Verified followers | "27, of the 500 X's rewards need" | real | same as DATA-T10 | daily | own |
| DATA-RES03 | Growth KPI: New follows | "19, this week, from X's export" | real | `reviews/week-2026-W39.md:34` (X's analytics export, 18–24 Sep: 19 new follows) | weekly export (manual, no API) | own |
| DATA-RES04 | Growth KPI: Followers | "36, first daily count, 24 Sep" | real | same as DATA-T16 | daily | own |
| DATA-RES05 | Growth KPI: Follows per visit | "1 in 3 — 19 from 58 visits (posts 21 with the boosted one, thread cards 4, replies 33)" | derived | 58 = 21 (original visits, `ledger/SUMMARY.md:36`) + 4 (thread-card visits, `ledger/SUMMARY.md:39`) + 33 (reply visits, `ledger/SUMMARY.md:38`); 19/58 ≈ 1-in-3, hand-computed and hard-coded, not live-computed | weekly | own |
| DATA-RES06 | Posts KPI: New follows | "15 — posts 13, their thread cards 2" | derived | 13 (original follows) + 2 (thread-card follows) = 15, from `ledger/SUMMARY.md:36,39` | weekly | own |
| DATA-RES07 | Posts KPI: Profile visits | "20, boosted post left out" | derived | 21 (original visits, incl. boosted's 1) − 1 (boosted post's visit) = 20; boosted post = `paid-to-free-tools`, `ledger/2102737637346095128.json` `organic.profile_visits: 1` | weekly | own |
| DATA-RES08 | Posts KPI: Views | "2,230, organic, boosted post left out" | derived | (2,097 original organic + 232 quote organic, `ledger/SUMMARY.md:36-37`) − 99 (boosted post's organic impressions, `ledger/2102737637346095128.json` `organic.impressions: 99`) = 2,230 | weekly | own |
| DATA-RES09 | Posts KPI: Visits per 1,000 views | "9.0" | derived | 20/2,230 × 1,000 ≈ 8.97 → 9.0 | weekly | own |
| DATA-RES10 | Replies KPI (4 tiles) | "33 visits from 115 replies", "4 new follows", "2 mutuals on topic (example)", "115 replies" | real / example | first three fields = `ledger/SUMMARY.md:38`; "2 mutuals" is the same unsourced example as DATA-RP04 | weekly | own |
| DATA-RES11 | "Where this week's 19 follows came from" | `FOLLOW_SRC` (`MS:71`): Connect post 13, Replies 4, Thread cards 2 | real | `reviews/week-2026-W39.md:34` ("connect pin 13, replies 4, thread cards 2") | weekly export | own |
| DATA-RES12 | Followers-over-time chart | single bar "36", "Thu 24 Sep" | real, but hard-coded not data-driven | `ledger/activity/account.json.days[0]` (`{date: "2026-09-24", followers: 36}`); the chart is a literal single `<div>` in `BB:493`, not a loop over `account.json`'s `days[]` array — **the real app must read `days[]`, not hard-code one bar** | daily (once >1 day exists) | own |
| DATA-RES13 | On-topic strip (Posts tab) | `SHARE` (`MS:64`) 11 slots: 5 `main`, 6 `other`; label "On topic: 5 of your last 11 posts, 4 still to post. Target 12 of 15." | real | matches `reviews/week-2026-W39.md:60` ("5 of the last 11 originals are main… against a target of 12 of 15") and `reference/audience.md`'s 12-of-15 target | per post | own |
| DATA-RES14 | "X's code tracks topic share over your last 15 posts (A8); the penalty isn't proven." | claim | real | `reference/x-algorithm.md:21` fact A8 | n/a (reference doc, weekly SHA check) | public (X's open-sourced ranking code) |
| DATA-RES15 | Posts-by-what-they-brought table/list | `RPOSTS`/`postRows`, sorted by follows→visits→views | real | same source as DATA-PS04; sort order matches `reviews/ui-direction.md` D27 | daily/weekly | own |
| DATA-RES16 | "Replies that led somewhere" bars | `RTOPICS` (`MS:65-70`): Australian govt breach (15 visits, 1 follow, 6,680 views), Networking/intros (10, 3, 736), Quick answers (7, 0, 6,102), Builder conversations (1, 0, 702) | real | matches `reviews/week-2026-W39.md:44-47` reply-grouping table exactly (hand-classified by reading reply text, not an X-provided field) | weekly, manual classification | own (grouping is manual text reading) |
| DATA-RES17 | "Reply views (14,220) don't count toward X's rewards; only your own posts do." | claim | real | `ledger/SUMMARY.md:23` (rewards need impressions "on originals... no replies"); 14,220 = `ledger/SUMMARY.md:38` | n/a | public rule |
| DATA-RES18 | Date-range control | "7 days" selected, "30 days"/"90 days" disabled, "Data starts 20 Sep" | real | earliest ledger post = `home-wifi`, `2026-09-20T09:25:19Z` (`ledger/2101603601143803913.json:6`) | n/a until 30/90 days of data exist | own |
| DATA-RES19 | "Write this week's review" → Thinking mock answers | "Use 24 Sep's: 27 and 337" | real | same numbers as DATA-T10/DATA-T13 | weekly | own |
| DATA-RES20 | "The next one is due Thu 1 Oct, after your analytics export." | date | hard-coded-time | same gap as DATA-T18 | weekly | own |

### Cortex (`BB.CORTEX`)

| id | where | mock value | kind | real source | refresh cadence | privacy |
|---|---|---|---|---|---|---|
| DATA-CX01 | Pipeline tiles | `PIPELINE` (`MS:119`): 2 Open questions, 0 Experiments, 0 Lessons, 5 Weights | real | Open questions = `len(QUESTIONS)` (hard-coded to match, not computed); Experiments/Lessons = `experiments.md`/`learnings.md` (both "None yet"/"No lessons yet"), backed by `loop/state.json:14-15` (`experiments: []`, `lessons: []`); Weights = `len(WEIGHTS)` (hard-coded to match, not computed) | on loop state change | own |
| DATA-CX02 | "No lessons yet… first experiment can start around 8 Oct" | sentence | real | `.claude/skills/next/SKILL.md:28` ("Experiments are paused until the loop has two weeks of organic X API data"); daily reads started 24 Sep (`ledger/runs.log:4`) + 14 days ≈ 8 Oct | n/a | own |
| DATA-CX03 | Example lesson card | "Three-card threads bring more people to your profile than long ones", 24 vs 11 visits/1,000, "6 posts each · 20 Sep – 12 Oct", "Bar set before test: 1.5×. Result: 2.2×.", "Proven 14 Oct" | example | explicitly labelled "EXAMPLE OF A LESSON · NOT REAL DATA" (`BB:562`); entirely fictional, illustrating the `learnings.md` schema (Lesson/Status/Rule/Claim/Evidence columns) | n/a | own (fictional) |
| DATA-CX04 | Weights | `WEIGHTS` (`MS:92-98`): Opening, Daily limit, Series pace, Posting slots (marked "A guess", italic), On topic means | real (prose) | per `reviews/ui-direction.md` build note: "weights are prose in skills" — not `loop/state.json.rules` (empty array, `loop/state.json:16`). Sources cited inline: format skills, `queue/topics.yaml` operator plan, `reference/audience.md` | changes only via `/apply` (none applied yet) | own |
| DATA-CX05 | Guardrails | `GUARDRAILS` (`MS:99-106`), 6 lines | decision-text | matches `AGENTS.md` "What the loop may never change" and `.claude/skills/next/SKILL.md`/`scripts/post_thread.py` behaviour (approval gate, sourcing, fact-check fail-closed, 600-cap refusal, `/apply`-only rule changes) | never (guardrails are fixed) | own |
| DATA-CX06 | Experiments panel | "None running · Paused until about 8 Oct" | real | `loop/state.json:14` (`experiments: []`) + same 8 Oct math as DATA-CX02 | on loop state change | own |
| DATA-CX07 | "Up next, in order" | `NEXT_EXPERIMENTS` (`MS:107-114`), 6 items | real | verbatim from `.claude/skills/next/SKILL.md:32-38` (the 6-item experiment queue) | changes if skill changes | own |
| DATA-CX08 | Open questions | `QUESTIONS` (`MS:115-118`): pipeline-mining question (cites video breakout), "sending to a colleague" question (cites A9, 20 vs 0.5) | real | matches `queue/research-backlog.md` items 1 and 2 exactly, including the A9 weights (`reference/x-algorithm.md:22`) | manual (operator adds/resolves) | own |
| DATA-CX09 | Chat seed message | "I'm working from your 11 posts, 115 replies and the weights you've set…" | real | 11 = `SHARE.length` (last 11 originals, matches DATA-RES13); 115 = `ledger/SUMMARY.md:38` | per session | own |
| DATA-CX10 | Chat suggested Q&A (4 sets, `SUGGESTIONS*`) | e.g. "Why cap the first post at 600?" → "…The final checks hold every capped format to it…" | real (canned answers) | answers cite real facts (A1/A2 in `reference/x-algorithm.md:14-15`, `ROOT_LIMIT=600` in `scripts/post_thread.py:33`, the boosted-post rule from `ledger/2102737637346095128.json`) but are **hard-coded Q&A pairs**, not a live model call — `FALLBACK` text admits this: "In the real app I'd answer from your posts, weights and the X ranking notes. This mock only knows the suggested questions." (`MS:137`) | not implemented; real Cortex would call an LLM (Settings names "Claude") | own |

### Settings (`BB.SETTINGS_INNER`, `MS.SETTINGS`)

| id | where | mock value | kind | real source | refresh cadence | privacy |
|---|---|---|---|---|---|---|
| DATA-SET01 | Health → Daily check | "Ran 20:00 last night" | real | same as DATA-T03 | daily | own |
| DATA-SET02 | Health → "Still too new to measure" | "6 posts" | real | same as DATA-T03 | daily | own |
| DATA-SET03 | Health → X API | "Last read worked" | real | last line of `ledger/runs.log` being `snapshot ok` (`ledger/runs.log:7`) | daily | own |
| DATA-SET04 | Health → X API spend | "about US$0.42" | derived | sum of `cost_usd` in `ledger/runs.log:2-7` (0.265+0.037+0.047+0.036+0.036 = 0.421 ≈ 0.42); matches `reference/x-api.md:54`'s "$10/cycle limit, under $0.25/day" budget context; labelled US$ per `reviews/ui-direction.md` E2/D36 | monthly running total; not currently summed automatically anywhere but this mock string | own |
| DATA-SET05 | Health → Ranking notes | "Current · 24 Sep" | real | `reference/x-algorithm.md:6-7` (`Checked: 2026-09-24`, `Status: current`) | weekly SHA check per `.claude/skills/next/SKILL.md:24` | public |
| DATA-SET06 | Notifications toggles | "Before a post" / "Shout-out window" | decision-text | `reviews/ui-direction.md` D35; both default off; no persistence layer exists (UI-only React state) | not implemented | own |
| DATA-SET07 | Cortex → Model | "Claude" | decision-text | matches `loop/state.json` conceptually (no explicit "model" field there) and `AGENTS.md`'s "typed in Grok or Claude Code"; read-only per review finding #31 fix | manual | own |
| DATA-SET08 | Profile row | "@exitzerocode · 36 followers" (Mac) | real | handle from `AGENTS.md`/`loop/state.json:6` (`self_handles: ["exitzerocode", "awakenluke"]`); follower count same as DATA-T16 | daily | own |

## 2. Data model the real app needs

Entities the UI implies. "Where it lives today" cites the closest existing file; "not stored" means no repo file/field holds it.

### Post (root)
- **UI fields:** slug, display title, format, lane, posted_at, on-topic flag, boosted flag, views/organic, visits, follows, bookmarks, outside replies, snapshot status (valid/late/pending).
- **Today:** `ledger/<root_id>.json` — `slug`, `format`, `lane`, `posted_at`, `snapshots[]` (each with `root.views`, `organic.impressions`, `organic.profile_visits`, `followers`, `kind: early|late`), `nonorganic` (present only if boosted, with a `reason` string), `missed`, `amendments[]` (e.g. lane relabels, `ledger/2102737637346095128.json` `amendments[0]`).
- **Written by:** `scripts/loop.py` via `snapshot.py` (`--ingest` for backfill, the daily run) and manual amendment commands. Never hand-edited (AGENTS.md, CLAUDE.md).
- **Gaps:** no human-readable display title field (only kebab `slug`); `boosted` in the mock (`RPOSTS[i].boosted`) is a hand-set boolean, should be derived from `nonorganic != null`; the ledger's own summary render() mixes two different reads' numbers for one post (see §4).

### Draft
- **UI fields:** slug, format, stage (drafting/needs approval/approved/posted), fact-check status, hook choice, take line.
- **Today:** `drafts/<date>-<slug>/` directory — `FORMAT`, numbered card files (`01-hook.md`, `02-shoutout.md`…), `CLAIMS.md`/`PATHS.md`, `CHECKLIST.md`, `images.md`, `REPLIES.md`, `POST.txt` (written by `scripts/post_thread.py` once checks pass).
- **Written by:** `/draft-thread` skill (card files, `CLAIMS.md`), the `/verify-settings` skill, an agent research procedure with no script (`PATHS.md`, `CLAIMS.md`), `scripts/post_thread.py` (`POST.txt`).
- **Gaps:** no single "stage" field — stage is inferred from which files exist (`APPROVED` present? `POST.txt` present? posted in `ledger/`?); no hook-candidate generation exists (`HOOKS` in the mock is 3 fixed literals); no "fact-check couldn't confirm a claim" flag beyond a `VERIFY` string inside `CLAIMS.md` prose.

### Card
- **UI fields:** text, X-counted character length, fold position, per-swap source (paid fact, free quote, limit).
- **Today:** before posting, card text lives in the draft files (`01-hook.md` …). After posting it depends on how the post was recorded: `/posted` supplies `cards[{id, text}]` from the live thread and `loop.py` keeps them (`.claude/skills/posted/SKILL.md:22-31`; `scripts/loop.py:221-224,332-348`); posts the daily snapshot auto-records retrospectively may carry only ids and view counts.
- **Written by:** `/draft-thread` (draft text), `scripts/loop.py`/`snapshot.py` (id + views after posting).
- **Gaps:** the approved text isn't snapshotted at approval time (only its digest), and auto-recorded posts may lack text, so D17's found-vs-approved comparison needs the draft files or a new approved-text record; fold position is a client-side approximation, not X's real algorithm (build note, `reviews/ui-direction.md:68`).

### Approval
- **UI fields:** approvedAt, approvedText (snapshot), edited-after flag.
- **Today:** `drafts/<slug>/APPROVED` — plain text: `cards-sha256: <digest>`, `approved-at: <ISO stamp>`, `approved-by: operator, typed /approve` (`.claude/hooks/approve.py:56-60`). **Not committed** (gitignored per AGENTS.md "APPROVED files are ignored by git and never committed").
- **Written by:** `.claude/hooks/approve.py`, triggered only by the operator's literal `/approve <slug>` prompt; `.claude/hooks/guard_approved.py` blocks every other write path.
- **Gaps:** stores a digest, not the full approved text, so "approved text" for a diff-on-post-check must be re-derived from the draft file at approval time, or a full-text copy needs to be added; no approval history/log (only the current marker — a re-approval overwrites it).

### Snapshot / Read
- **UI fields:** observed_at, age_hours, kind (early/late/valid/pending), per-metric values, source (api/scrape).
- **Today:** `ledger/<root>.json.snapshots[]`, each with `observed_at`, `age_hours`, `kind`, `root.{views,likes,reposts,quotes,replies,bookmarks}`, optionally `organic.{impressions,likes,replies,reposts,profile_visits,url_clicks}`, `followers`, `raw_file`, `missing[]`.
- **Written by:** `scripts/snapshot.py` (daily 20:00 via `ops/launchd/com.exitzerocode.thread-engine.snapshot.plist`) calling `scripts/x_api.py`; raw API payloads kept in `ledger/raw/` (`ledger/raw/api/backfill-*.json`).
- **Gaps:** none major; this is the best-modeled entity in the repo. One rendering bug downstream (see §4).

### ActivityItem
- **UI fields:** kind (original/quote/reply/thread card), organic impressions, profile visits, likes, follows, date.
- **Today:** `ledger/activity/2026-09.json` (`{month, items[]}`) and rolled up into `ledger/SUMMARY.md`'s Account table.
- **Written by:** `scripts/snapshot.py` / `loop.py`.
- **Gaps:** none major for what's built; the mock's per-topic reply groupings (`RTOPICS`, DATA-RES16) are a **manual weekly classification of reply text**, not a field — a real app either needs the same manual step or an automated topic classifier.

### Reply-to-me (Waiting for you)
- **UI fields:** handle, where (which post), age, said (summary), point (suggested angle), status (answered/not answering).
- **Today:** **not stored anywhere.** Per `reviews/ui-direction.md:70`: "the ledger doesn't keep which post each of the operator's replies answered, so answered and unanswered can't be told apart yet… The X API returns this (`referenced_tweets`); the daily snapshot needs to store it. The daily read at 20:00 is too slow for the first hour after a post, so this view needs a fresh read of mentions when it opens (about a cent a read)."
- **Written by:** nobody yet.
- **Gaps:** this is a named, explicit build gap in the decision log — needs (a) `referenced_tweets` captured and stored per mention, (b) a fast on-open mentions read separate from the daily batch, (c) an answered/not-answering status field with undo (review finding #38, fixed in mock v22 as two distinct outcomes but with no backing store).

### Builder / mutual
- **UI fields:** handle, verified, follows-you, you-follow, on-topic, last exchange date.
- **Today:** not stored. No file tracks per-handle follow-relationship or exchange history.
- **Written by:** nobody.
- **Gaps:** entirely new entity for the build; needs a per-handle relationship record, likely derived from X API mentions/follows reads plus manual "on topic" judgement.

### WorthJoining candidate
- **UI fields:** handle, found time, kind (builder/AI news/etc.), summary, suggested point.
- **Today:** not stored; per `reviews/ui-direction.md:70` build note, this is `/next`'s chat output (the "Replies worth making today" step, `.claude/skills/next/SKILL.md:67-74`, using `scripts/x_read.py search`), which is printed to the operator in a session and never saved to a file.
- **Written by:** nobody (transient `/next` output).
- **Gaps:** needs persistence — a leads/candidates store written by `/next`, read by the UI, with a way to mark "answered" or expire it.

### Capture
- **UI fields:** kind (screenshot/recording/voice note/note), when, text, format it turns into, turned flag.
- **Today:** not stored. `DEFAULTS.captures` in the mock (`MS:175-178`) is React-state-only seed data; `saveCapture()` (`MS:619`) only appends to in-memory state, lost on reload.
- **Written by:** nobody.
- **Gaps:** entirely new entity for the build (this is D25 in `reviews/ui-direction.md:35`, "Product review, adopted" but never implemented past the mock) — needs a file or small local store, plus a way to attach real screenshots/recordings (not just text).

### Experiment
- **UI fields:** question, treatment, control, cohort, primary metric, effect size, status.
- **Today:** `loop/state.json.experiments` (currently `[]`); `experiments.md` (generated view, currently "None yet"); the 6-item queue order lives as prose in `.claude/skills/next/SKILL.md:32-38`, not as data.
- **Written by:** `scripts/loop.py open-experiment --json loop/inbox/experiment.json` (per `.claude/skills/next/SKILL.md:39`).
- **Gaps:** none structurally — the schema exists, it's just empty because experiments are paused until ~8 Oct.

### Lesson
- **UI fields:** statement, status (adopted/proposed), numbers (both arms), sample size, date range, bar-vs-result, proven date.
- **Today:** `loop/state.json.lessons` (`[]`); `learnings.md` (generated table, currently "No lessons yet").
- **Written by:** `scripts/loop.py`, only after an experiment closes.
- **Gaps:** none structural; the mock's example lesson card is explicitly fictional (DATA-CX03) — a real card needs the same shape once one exists.

### Weight
- **UI fields:** name, value, source, whether it's a guess (italic).
- **Today:** **prose inside format skills** (`.claude/skills/format-*/SKILL.md`) and `queue/topics.yaml`'s operator-plan comments — not `loop/state.json.rules` (`[]`). Per `reviews/ui-direction.md` build note: "weights are prose in skills."
- **Written by:** nobody structured; changes require editing skill files, or eventually `/apply` writing to `loop/state.json.rules` once a lesson is adopted.
- **Gaps:** no machine-readable weights store yet; the UI's 5 `WEIGHTS` are hand-transcribed from skill prose, will drift if skills change without the mock being re-synced.

### Guardrail
- **UI fields:** fixed text, 6 items.
- **Today:** enforced in code (`scripts/post_thread.py`'s refusal functions, `.claude/hooks/guard_approved.py`) and stated in `AGENTS.md`'s "What the loop may never change" section — not a data file, by design (guardrails must never be editable data).
- **Written by:** nobody (fixed).
- **Gaps:** none — this should stay hard-coded/code-enforced, not a data table, to preserve the "never changed by Cortex or the loop" property.

### Settings
- **UI fields:** notification toggles, theme choice, model choice.
- **Today:** not stored (no settings file exists in the repo).
- **Written by:** nobody.
- **Gaps:** new entity; needs a small local settings store (theme/toggles are pure client prefs; "model" ties into whichever future Cortex backend is chosen).

### Preference signal (edits, hook picks, take lines)
- **UI fields:** what was edited, before/after, hook chosen, take line text, timestamp.
- **Today:** `ledger/<root>.json.edits[]` exists as a schema (currently `[]` on every post — confirmed in `reviews/week-2026-W39.md:71-73`: "No `preference` or `violation` edits are recorded on any ledger post yet").
- **Written by:** intended to be `scripts/loop.py`, but nothing currently writes to it (`saveEdit`/`saveHook` in the mock are UI-state only).
- **Gaps:** the schema exists and is described (D26 in `reviews/ui-direction.md:36`: "Every edit is recorded as a preference signal for the loop") but the write path from "operator edits a card in the app" to `ledger/<root>.json.edits[]` doesn't exist yet.

### Time-to-first-like
- **UI fields:** minutes/seconds from posting to first like.
- **Today:** not stored. `ledger/<root>.json.snapshots[]` records views/likes at 6-60h granularity, not a first-like timestamp.
- **Written by:** nobody.
- **Gaps:** needs a much faster read than the daily 20:00 job (build note echoes the "Waiting for you" gap — a first-hour poller). DATA-T05's "3 minutes later" is explicitly tagged `example` because of this gap.

### Minutes-taken

- **Today:** `/posted` asks "Roughly how many minutes did this one take, start to finish?" (`.claude/skills/posted/SKILL.md`) and `loop.py record-post` stores it as `production_minutes` in `ledger/<root>.json` (`scripts/loop.py:227,346`). The field exists but is `null` on all 11 recorded posts so far.
- **UI:** the first-hour card's minutes chips (D34) answer the same question, so it needs one write path into `/posted`'s record, not a second store.

### Reply outcome (answered / not answering)
- **UI fields:** status, undo.
- **Today:** not stored (same gap as Reply-to-me above).
- **Gaps:** same as Reply-to-me; needs `referenced_tweets` storage plus a status field.

### Health / run status
- **UI fields:** last run time, ok/failed, items read, cost.
- **Today:** `ledger/runs.log` (append-only text log: timestamp, `snapshot ok/failed`, `read48`, `final`, `followers`, `api_items`, `cost_usd`).
- **Written by:** `scripts/snapshot.py`.
- **Gaps:** it's a log, not a queryable "current status" record — the UI's "Last daily check: Wed 20:00" / "Ran 20:00 last night" needs to parse the last line, which is fine for a script but the real app needs this as a structured read, not log-tailing.

### Spend
- **UI fields:** running month-to-date estimate.
- **Today:** per-run `cost_usd` in `ledger/runs.log`; no monthly rollup field exists.
- **Written by:** `scripts/x_api.py` (`self.cost`, `x_api.py:198`) via `snapshot.py`.
- **Gaps:** DATA-SET04's "$0.42" is a manual sum of 5 log lines; needs either a computed rollup or a stored running total.

## 3. Derived numbers: exact formulas

| Number on screen | Formula | Source values |
|---|---|---|
| "27 of 500" verified followers | direct read | `ledger/activity/account.json` `days[0].verified_followers` |
| "About 37 a week" | `(500 − 27) / (90 − days_elapsed) × 7`, hand-computed once, not live | `reviews/week-2026-W39.md:9` states "about 5 verified followers a day (37 a week)" as the pace needed to hit 500 in a 90-day rewards window |
| "5.4%" bar width | `27 / 500 × 100` | hard-coded, not computed from the adjacent 27/500 text |
| "337 of 500,000" | direct read | `account.json.eligibility[0].qualified_impressions` |
| "0.07%" bar width | `337 / 500000 × 100 = 0.0674` | hard-coded |
| "2,230" organic views (Posts KPI) | `(original_organic + quote_organic) − boosted_post_organic` | `2,097 + 232 − 99 = 2,230` (`ledger/SUMMARY.md` Account table; boosted post's organic from `ledger/2102737637346095128.json` `snapshots[1].organic.impressions`) |
| "20" profile visits (Posts KPI) | `original_visits − boosted_post_visits` | `21 − 1 = 20` |
| "9.0" visits per 1,000 views | `visits / views × 1000` | `20 / 2230 × 1000 = 8.97 ≈ 9.0` |
| "15" new follows (Posts KPI) | `original_follows + thread_card_follows` | `13 + 2 = 15` |
| "1 in 3" follows per visit (Growth KPI) | `follows / total_visits`, total visits = `original_visits(incl. boosted) + thread_card_visits + reply_visits` | `19 / (21+4+33) = 19/58 ≈ 0.328 ≈ 1-in-3` |
| "On topic: 5 of your last 11 posts… Target 12 of 15" | count of `main`-lane originals in the last N originals | `SHARE` array (`MS:64`), 11 slots (5 `main`, 6 `other`); target = `reference/audience.md`'s "at least 12 of the last 15 originals" |
| "US$0.42" API spend | `Σ cost_usd` across recent `snapshot ok`/`x_api backfill ok` lines | `ledger/runs.log` lines 2–7: `0.265+0.037+0.047+0.036+0.036 = 0.421` |
| First read time (Ready screen, DATA-R04) | `firstRead(posted_ms) = next 20:00-Brisbane check ≥ posted_ms + 36h` | `firstRead()`, `MS:234`, matching `scripts/snapshot.py`'s 36–60h read window per `AGENTS.md`'s description of `scripts/snapshot.py` |
| X-counted character length (`xLength`) | code points count 1 except U+2000–U+200D, U+2010–U+201F, U+2032–U+2037 which count 1 too (i.e., most punctuation ranges count 1); everything else (incl. most emoji) counts 2; every URL counts flat 23 | `MS:181-191`, mirroring `scripts/post_thread.py x_length()` (`scripts/post_thread.py:69`) |
| Card fold position (approximate "Show more" point) | first line index where cumulative `xLength` of joined lines exceeds 280 | `MS:393-395`; **not** X's real client-side fold algorithm (acknowledged gap, `reviews/ui-direction.md:68`) |
| "Boosted" flag | in the mock: a hand-set literal per post; **should be** `ledger post has a non-null "nonorganic" object` | `ledger/2102737637346095128.json` `nonorganic` key presence |
| Reply topic groups (`RTOPICS`) and their visit/follow/view counts | manual classification of 115 replies' text into 4 groups, then summed per group | `reviews/week-2026-W39.md:40-47` — **not automatable from any X field**, done by reading reply text |
| Countdown to next slot / "in 2h 14m" etc. | `slot_ms − Date.now()`, formatted | `MS:319-329`, `nextSlot()` (`MS:232`) picks the next 06:00 Brisbane ≥30 min away |

## 4. Known data issues

1. **`ledger/SUMMARY.md`'s two-read mix (review §6, `reviews/ui-review-2026-09-25.md:110-112`).** `render()` in `scripts/loop.py` (~lines 1124-1136) takes the "Views" column from the post's earliest/snapshot read but "Organic" from a later `x_api` activity read, so the same post shows different totals in the same row: `macbook-battery` 149 (Views) vs 151 (Organic), `connect-pin` 849 vs 856, `iphone-18-pro-aperture` 464 vs 509. Confirmed real in `ledger/SUMMARY.md:11-13`. The mock isn't affected because `RPOSTS` (`MS:50-62`) uses a single number per post (matches the Organic figure, e.g. `connect-pin: views: 856` at `MS:51`), but the real app's data layer must pick one read per post consistently, not blend two.

2. **Verified-follower count disagrees by 1 across two live sources on the same day.** `ledger/activity/account.json` daily read says 27; X's eligibility screen (`account.json.eligibility[0]`) says 26, both timestamped 2026-09-24. Dismissed in review §7 as "both real reads the same day; 27 is the later one" — not a bug, but the real app needs an explicit rule for which of two disagreeing same-day reads wins, and should show both with their read times rather than picking silently.

3. **Structured entities that are actually hard-coded prose, inconsistently labelled `example`.** Several UI regions look like live data but are typed-in constants with no backing file: `BUILDERS`, `WAITING`, `REPLIES` (Worth joining), `HOOKS`, the proposed build-log card, and the example lesson. Some are tagged "example" on screen (lesson card, "37 greetings", "2 mutuals", the tool-verdict draft); others (Builders, Waiting-for-you, Worth-joining) are **not** tagged and use dotted placeholder handles instead, per the mock's own convention comment (`MS:18`: "Placeholder names: dots make them impossible X handles, so no real account is shown"). The build must decide, screen by screen, which regions are wired to real data on day one vs. which stay stubs, and mark stubs consistently.

4. **`Followers over time` chart is a hard-coded single bar, not a loop over `account.json.days[]`.** `BB:493` writes the literal value `36` and date `Thu 24 Sep`; a second day's data (once it exists) would need code, not just data, to render. Confirmed no loop/map over `followerDays` exists for the chart path (only the table view maps over it, `BB:496`).

5. **Analytics export date and next-review date are hard-coded, not computed from a cadence.** "Thu 1 Oct" (`BB:124`, `BB:540`) is never derived from "last export + 7 days"; if the operator's actual export slips, the mock (and presumably a naive first build) would show a stale date.

6. **Qualified-impressions and eligibility-screen numbers have no automated read.** `reference/x-api.md` documents `scripts/x_api.py` as reading the account's own posts, mentions, followers and profile — but the eligibility screen (verified followers / qualified impressions for the rewards program) is read manually (`account.json.eligibility[0].at: "2026-09-24T02:29:55Z"`, a one-off entry, not part of the daily `days[]` array). The real app needs either a documented manual-entry flow for this number or confirmation that no API covers it.

7. **`production_minutes` field exists in the ledger schema but was `null` on every post read this session** (`ledger/2101603601143803913.json:17` and presumably all others) — worth confirming whether `/posted`'s "how long did this take" question (D34) is actually wired to write it, since `reviews/week-2026-W39.md` doesn't mention it being populated.

## 5. Privacy rules for data in a shared app

- **Own data** (the account's own posts, replies, followers, spend, run status) is read via `scripts/x_api.py` with read-only Keychain keys (service `thread-engine-x`) that "never enter a session" (`AGENTS.md`). This data lives in committed files: `ledger/*.json`, `ledger/SUMMARY.md`, `ledger/activity/2026-09.json`, `ledger/activity/account.json`, `ledger/runs.log`. Safe to commit and, per D3 (`reviews/ui-direction.md:13`), the app is meant to eventually be shared "to a standard fit to share."
- **Other people's data** (other accounts' posts, mentions, reply authors, followers, maker handles) goes through `scripts/x_read.py` (wraps one read-only Grok call, every result re-checked against the X API by id) or `python3 scripts/x_api.py user <handle>` for maker checks. Per `AGENTS.md`: `loop/followers/` and `ledger/raw/api/` "hold other people's data" and are **explicitly listed as uncommitted** (`loop/state.json:` — `loop/inbox/` is scratch; `loop/followers/` and `ledger/raw/api/` hold other people's data, none of the three is committed).
- **The mock's placeholder convention** (`MS:18`): real handles are never shown in the UI mock; every third-party handle is written with a dot that makes it an impossible real X handle (`@builder.one`, `@sec.minded`, `@aus.indie`, `@pixel.tools`, `@ship.daily`, `@lab.notes`). The real app must decide whether to show real handles (since it's the operator's own private data-viewing surface) or keep obfuscating — D3's "share it later" plan suggests real handles may need to stay out of any screen that could be screenshotted or shown to someone else.
- **Vendor/public data** (tool pricing, feature claims in `SWAPS`/`CLAIMS.md`, the X algorithm reference) comes from public vendor pages and `xai-org/x-algorithm` (a public GitHub repo, commit-pinned in `reference/x-algorithm.md`). No privacy restriction, but the truth-budget rule (`voice/exit-zero.md`) requires every figure to be sourced this session — the real app should keep the same "checked <date>" provenance the mock shows in the Source sheet (DATA-P05/P06).
- **X API keys** never enter any session per `AGENTS.md`/`CLAUDE.md`: "X API keys live in macOS Keychain and are not available here." `.claude/hooks/guard_approved.py` explicitly blocks any shell command matching `security find-generic-password`/`dump-keychain` patterns. A real app's backend must preserve this boundary — no LLM-driven agent process should ever see the raw keys, only `scripts/x_api.py`'s own process should.
- **Approval integrity as a privacy/safety boundary**, not just data: `.claude/hooks/guard_approved.py` blocks any tool from writing `loop/state.json`, `ledger/*.json`, `ledger/SUMMARY.md`, `experiments.md`, `learnings.md`, or the `APPROVED` marker, and blocks shell patterns that would nest another agent invocation of `/approve`. The real app's build must replicate this — no code path from "the AI drafted this" to "this is now approved" that skips the operator's own explicit action (D24, `reviews/ui-direction.md:34`).
