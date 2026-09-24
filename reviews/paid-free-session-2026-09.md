# PAID → FREE: the Grok session, and what changed

The operator designed the PAID → FREE series in a Grok chat on 23–24 Sep 2026. Grok exported the brief below, and it is kept verbatim except that people's names are replaced by roles. **The rules in force are `.claude/skills/format-tool-swap/SKILL.md` and `voice/exit-zero.md`; where this record disagrees with them, they win.** Reviewed on 24 Sep 2026 against the repo, the ledger and an independent line-by-line audit.

## Superseded or corrected

- **Boost trial (section 10): superseded.** Don't boost (`voice/exit-zero.md`). Post 1 was boosted within hours of posting anyway, before the session's own ~150-view bar: 95% of its 2,105 impressions were paid, and it earned 1 profile visit and 0 follows.
- **Timing (section 9): superseded** by `/next`'s US-overlap slots (22:00–23:00 and 05:00–07:00 Brisbane), which the operator confirmed on 24 Sep.
  - The ledger contradicts "mid-afternoon parents died": the aperture comparison posted at 15:45 has 509 organic impressions, and the 13:17 post had 217 at its early read.
  - The repo's research notes cite Buffer finding local 6–11pm evenings the weakest window, against "6–11pm AEST evenings".
- **Cadence (section 6 and "done" #8): changed.** One PAID → FREE parent every other day stays. "No second parent that day" became up to two originals a day, hours apart (operator, 24 Sep).
- **Rows: changed.** 2 to 5 swaps, plus singles for tools held back for one. This replaces "usually one swap, sometimes a 4–6 line list".
- **"Next one is…" reply (section 6, step 4): dropped.** A post gets one card at most.
- **Shout-out (section 5): changed.**
  - The five-tag block was for post 1 only; later posts tag one organisation account, checked with `x_api.py user`.
  - `@Krita_Painting` didn't exist on 24 Sep. Krita's active account on X is the community's `@kritaartists`.
  - Post 1's shout-out went up 19 seconds after the parent, not 10–20 minutes later.
- **Ready replies (end of file): changed.** They become talking points, not text to paste; the operator writes every reply.
- **"Research notes an agent should not re-litigate" (section 8): narrowed.** The editorial choices stay settled. The facts are re-checked in `CLAIMS.md` for each post (truth budget). "Locked" isn't approval: a locked line with no source is cut.
- **Drafts (section 7): fixes needed.** They're listed on each row in `queue/topics.yaml`:
  - unnamed or doubled paid sides;
  - paid tools that have free plans;
  - Focalboard is unmaintained;
  - ngrok's free plan already includes a fixed domain.
- **Unchecked:** the claims about what travels on X never had a post-id check (`x_read.py` didn't exist yet). They include:
  - label-first lists travel;
  - After Effects is discussed more than Cinema 4D;
  - Streamlabs is where the live conversation is;
  - the Australian posting pattern.
- **Refined:** "cold start depends more on first-hour replies". The gate to strangers is the first like (`reference/x-algorithm.md` A6), and a reply from a mutual carries the most weight (A10).

## Inconsistencies inside the brief

1. "Complete sentences" (voice section), while every proof line is a fragment.
2. "Sentence case", with an all-caps `PAID → FREE` label.
3. The row count changes three times: one swap or 4–6 lines, then five rows, then 2–5, with singles held back as well.
4. "Pick the one paid target people talk about", then "Navicat / DataGrip" and "1Password / LastPass" in the drafts.
5. "Paid name visible first", then "Paid chat apps", "Router ads / paid DNS" and "Paid VPN mesh".
6. "Never imply a 1:1 substitute", then swaps the brief itself calls loose: After Effects → Blender, Streamlabs Ultra → OBS (the free comparison is Streamlabs Desktop), and Copilot → Cline.
7. "Confirm `@Krita_Painting` before send", after the post had gone out.
8. The parent order leaves out the system category.
9. "Repost … short caption": a repost can't carry a caption; with one, it's a quote.
10. "No second parent that day", broken the day post 1 went up (an intro post came that afternoon).
11. The Resolve UHD 60 limit is hedged in the notes and stated flatly in the ready reply.
12. Roster wording is paraphrased into proof lines ("Modelling, animation, render"; "Graph and plugins"; "files stay in shape"; "collections as files in the repo").
13. Feature sheets are rejected, but the locked Blender line is a short feature list.
14. "Changelog tone is slop", then "they still post the changelog" in the developer shout-out.
15. Paid targets that aren't the roster's: After Effects (the roster has Cinema 4D and Maya), LastPass (roster: Dashlane) and Microsoft 365 (roster: Office 365).
16. "Check X talk before substituting a roster row", with no check recorded for Cline or LastPass.
17. The "support" category word, while PostHog is analytics.
18. "Done" #5 implies a shout-out on every parent; the local AI and privacy drafts have none.
19. The brief never records that the boost happened.
20. The "Next one is…" reply promises an order in public that section 6 only calls "suggested".

---

# PAID → FREE X format — session brief for an agent

**Account:** @exitzerocode (Exit Zero Code)  
**Owner context:** the operator, Brisbane (AEST, Queensland does not use DST). SuperGrok.  
**Profile bio:** `🇦🇺 Building idea → script → finished video. Struggling through AI slop.`  
**Account size at session:** ~35 followers, Blue Verified.  
**Source roster:** attached `Paid → Free.md` (premium apps + free/open-source alternatives, grouped by category). Treat roster notes as claims to verify, not as copy.  
**Session window:** 23–24 Sep 2026 AEST.  
**This file’s job:** Reconstruct how the X series format was decided, not only the final text. Prefer the user’s constraints over generic “best practices.”

---

## How to read this file

- **USER** blocks are the human’s actual direction. Treat them as overrides.
- **AGENT** blocks are what was proposed, researched, or rejected.
- **LOCKED** means stop rewriting unless the user asks.
- Do not revive rejected hooks, brochure adjectives, or premium-vendor tags.
- Voice is not optional. If a line sounds like a carousel or a changelog, it is wrong.

---

## Non-negotiable voice and mechanics

From the original brief (user):

- Small builder account, Brisbane.
- Product direction: idea → script → finished video. Tired of AI slop.
- Voice: normal sentence case, complete sentences. Sound like a person.
- Do **not** write connect-flyer copy (`Hey @X, drop a hi, let’s grow together`).
- Do **not** use brochure adjectives (`juggernaut`, `neural graph`, `elite`, `zero server dependency`, `amazing`).
- Do **not** stack the same verb stem twice in one line (`makes/making`, `building/building`).
- Posts: short. Usually one swap, sometimes a 4–6 line list. Never a 50-row dump unless asked.
- Group by the file’s categories. Do not mix categories in one tweet (no Bitwarden + Photopea).
- Research before writing: what “free” means (OSS, free tier, ads, Studio edition). Be honest if there is a catch — **but later the user forbade putting those catches in the parent**.
- If a row names several premium targets, pick the one people on X actually talk about.
- Prefer a specific reply or quote on a **free-alternative** maker’s post. A single `@` can live in a reply under the parent. Do not assume an `@` in the parent helps For You.
- Do not stack vendor handles or paste the same “love this tool” under five official accounts.
- Replies and quotes matter more than likes. Do not fire many parent posts in the same short window.
- Do not imply a 1:1 professional substitute when it is not.

**Observed on the live account (important):** the highest-reach organic post was exactly the flyer the brief forbids (`Hey @X` / “drop a hi” / “let’s grow together”, ~843 views, 32 replies). Do not treat that post as a template or a Boost candidate. Settings-listicle threads (router / iPhone camera / MacBook battery) are a second, off-series format.

---

## Decision log (process, not just outcome)

### 1. Starting shape vs hook

**USER:** Should each category post start with a few options for value/intrigue? `Photoshop → Photopea` has no context. How do other accounts post this format?

**AGENT (rejected later):** Job-first hooks (`Need to open a PSD and don't have Photoshop`). Category openers with 2–3 swaps.

**USER:** These miss the point. The move is `PAID VERSION → FREE ALTERNATIVE`, not “if you need to open a PSD.” Intrigue and value = there are genuinely good free versions.

**USER:** The opener isn’t landing. You said “video stack” but Photoshop is not video. Show higher-reach versions others use.

**AGENT finding (high-reach pattern on X):** Label-first lists travel. Examples in the lane: mega “paid → free” dumps (a list account's 300-row), “10 things I stopped paying for,” short 3–8 row alternative lists. Flyer posts open with `Stop paying for subscriptions… Here are 10 FREE alternatives`. User explicitly does not want that flyer.

**LOCKED implication:** Paid name visible first. Category context in a header line. Proof line under each swap. Not a job scenario.

---

### 2. Header + series stem

**USER proposed layout:**

```
PAID → FREE
Discovering amazing free alternatives for creator software.

Photoshop → Photopea
▷ …
```

**AGENT:** Keep the label. Cut `amazing` (brochure). `Discovering` reads like a blog title.

**USER:** Open to rewording, but the line does two jobs: (1) context + category, (2) signals the poster researched, unlike flyer copy (`Stop paying… Here are 10 FREE alternatives`).

**USER:** `I found free versions of Creator Software that actually hold up.`

**AGENT:** Use it; sentence-case `creator software`. Shorter option: `I found free creator tools that actually hold up.`

**USER:** Yes, the shorter line is better. Maybe even `Finding free creator tools that actually hold up.`

**AGENT:** `I found` = sentence, past tense, work already done. `Finding` = title. Use `Finding` only if it is a recurring series label.

**USER:** Yes — reuse it across every category. Drop the category word into that slot:

- `Finding free creator tools that actually hold up.`
- `Finding free productivity tools that actually hold up.`

**LOCKED header:**

```
PAID → FREE
Finding free [category] tools that actually hold up.
```

Category adjectives (not the file’s long titles):

| File category | Stem word |
|---|---|
| Creative & Motion Graphics | creator |
| Productivity & Office Suites | productivity |
| Developer Tools | developer |
| Network Security & Privacy | privacy |
| System Utilities | system |
| Cloud Storage | storage |
| Diagrams & Vector | diagram |
| Finance | finance |
| Local AI | local AI |
| Self-Hosting | self-hosting |
| Product Analytics & Support | support |

---

### 3. Proof-line style

**USER locked structure:** `Paid → Free` then `▷` one proof line.

**USER:** Stop including negatives in the parent (`Ads on the free side`, `Free export stops at UHD 60`, `Not an AE timeline`).

**USER:** What does “Not an AE timeline” mean?

**AGENT explanation (for replies only):** After Effects is layers on a 2D composition. Blender is a 3D scene. Same job for some motion, different desk. Do not put that warning in the parent.

**LOCKED parent proof lines:** positive, specific, short. Limits live in a reply if someone asks.

Rejected proof styles:

- Blender feature sheet: `3D Modeling, Sculpting and printing, Animation and Rigging, Rendering and Lighting` (title case + product page + 3D printing off-topic next to Premiere).
- Changelog / LTS copy: `Blender ships full releases on a short cycle, with LTS in between` — user called this slop.

---

### 4. Which swaps go in the creator opener

Started as three rows: Photopea, Resolve, OBS (Camtasia).

**USER:** Weakest is Camtasia → OBS. Would Cinema 4D → Blender or Procreate → Krita beat it?

**AGENT:** Blender beats OBS on reach. Krita probably does not in this slot (Procreate is iPad; Krita is desktop/Android; replies will argue the device).

**USER:** Search X: Cinema 4D vs After Effects talk volume.

**AGENT research (X + release/context):** After Effects is talked about far more. AE appears in everyday editor/creator chat and in paid→free dumps as `After Effects → Blender`. Cinema 4D talk is a smaller 3D/motion-design circle (plugins, Redshift, product viz). Caveat: AE → Blender is the wider hook and the looser like-for-like; C4D → Blender is the fairer 3D swap. User chose **After Effects** for the opener.

**USER:** Why not post all five creator options (add OBS and Krita)?

**AGENT:** You can. Held back for pairing quality, not because five rows is a dump. If the point is “here is the creator bucket,” five rows finishes the category in one parent.

**USER:** Is Camtasia the best premium to highlight vs Streamlabs Ultra? Research wider appeal.

**AGENT research:**

- Streamlabs (Desktop + Ultra) is the live X conversation: overlays, going live, “is Ultra worth it to multistream.”
- Camtasia appears in scraped `Camtasia → OBS` dumps and tutorial/corporate corners.
- Streamlabs Desktop is built on OBS; Ultra is the paid layer. Closer like-for-like than Camtasia (recorder + editor; OBS does not edit).
- Catch for later replies: Streamlabs Desktop is already free. Ultra is the subscription.

**LOCKED creator parent (posted by user 23 Sep 2026 ~10:31pm AEST, id `2102737637346095128`):**

```
PAID → FREE
Finding free creator tools that actually hold up.

Photoshop → Photopea
▷ Browser editor. Opens PSDs.

Premiere Pro → DaVinci Resolve
▷ Edit, colour, and audio. No watermark.

After Effects → Blender
▷ 3D and motion. Modelling, animation, render.

Streamlabs Ultra → OBS Studio
▷ Record and stream. Scenes, camera, separate audio.

Procreate → Krita
▷ Painting and illustration. Desktop and Android.
```

`No watermark` stayed because the user treats it as the reason people look at Resolve, not as a limit.

---

### 5. Maker notice / replies (free side only)

**USER:** Do not try to get the attention of premium vendors. Notice the **free alternative** makers.

**USER:** Concept — a reply “sub list” on a benefit (updates, support, forum, GitHub). Example: `@Blender provides frequent updates`. As it is a reply, why not tag each?

**AGENT first pass (too literal, user rejected):** version numbers, LTS dates, issue IDs, forum topic counts.

**USER:** Too literal and specific. Should be a little shoutout. `@Blender — provides consistent updates and releases.` Changelog tone is slop.

**USER draft:**

```
@photopeacom — still ships features and answers people on their Github page.
@Blackmagic_News — steady Resolve releases and an active forum.
@Blender — consistent updates and releases.
```

**AGENT:** Photopea's developer answers more on X than on GitHub (GitHub is the issue list, product is not OSS). Prefer dropping GitHub.

**USER:** Your version works: `@photopeacom — still ships features and answers people.`

**LOCKED shoutout reply (post 1 only; five tags because five rows):**

```
@photopeacom — still ships features and answers people.
@Blackmagic_News — steady Resolve releases and an active forum.
@Blender — consistent updates and releases.
@OBSProject — regular Studio builds and a public tracker.
@Krita_Painting — steady desktop releases and a real painter community.
```

Confirm `@Krita_Painting` before send. Expect a human reply from Photopea; Blender and Blackmagic are broadcast accounts.

**Rule refinement:** Five-tag shoutout is for post 1 only. Later parents: one free-side handle max. Do not paste the same block under every category.

**Handles (free side):**

| Row | Handle | Notes |
|---|---|---|
| Photopea | `@photopeacom` | Its developer still answers. Best real notice target. Prior post: “What did you use before Photopea?” |
| Resolve | `@Blackmagic_News` | News account, low chat. Forum is where help lives. |
| Blender | `@Blender` | Official, high volume. |
| OBS | `@OBSProject` | Release-focused. |
| Krita | `@Krita_Painting` | Confirm. |
| Bruno | `@use_bruno` | Thanks migrations. Its founder has a personal account (a person; not tagged). |
| Obsidian | `@obsdmd` | **Not** `@Obsidian` (game studio). |
| Ollama | `@ollama` | Broadcast. |

Off-platform (GitHub discussion, Discord, a real bug) is often more visible than an `@` in For You.

---

### 6. Series operations

Cadence agreed: one **parent** every other day. Replies/quotes on the off day. Two parents in 24 hours reads as a dump.

Day plan:

1. Parent. No handles, no hashtags, no `1/5`.
2. Wait.
3. Shoutout reply (10–20 minutes later, not the same second).
4. Optional breadcrumb reply: `Next one is developer tools. Postman, SQL, tunnels.`
5. Answer humans. Same voice. One or two sentences.
6. One extra maker touch per day max (reply on their post **or** the shoutout, not both plus quotes).

**Repost:** Maker release only, short caption. Do not repost own parent. Do not repost other people’s 300-row dumps.

**Quote:** Maker news only. Never quote Adobe / Maxon / Streamlabs to pick a fight.

**Pin:** Pin post 1 until post 2 needs the slot.

OBS and Krita are spent in post 1. Do not give them later parents unless the thread demands a deep single.

Suggested parent order after creator: developer → productivity → local AI → privacy → storage → diagram → finance → self-hosting → support. Finance/support can wait if they feel off-brand after week two.

---

### 7. Follow-up parents (draft, not all posted)

**2 Developer**

```
PAID → FREE
Finding free developer tools that actually hold up.

Postman → Bruno
▷ API collections as files in the repo.

Navicat / DataGrip → Beekeeper Studio
▷ SQL client for Postgres, MySQL, SQLite.

Ngrok → Cloudflare Tunnels
▷ Share localhost on a real hostname.
```

Shoutout: `@use_bruno — collections stay files, and they still post the changelog.`

**3 Productivity**

```
PAID → FREE
Finding free productivity tools that actually hold up.

Notion → Obsidian
▷ Local markdown. Graph and plugins on your machine.

Microsoft 365 → OnlyOffice
▷ Word, Excel, PowerPoint files stay in shape.

Trello → Focalboard
▷ Kanban boards. Desktop or self-hosted.
```

Shoutout: `@obsdmd — local files, and the app keeps moving.`

**4 Local AI**

```
PAID → FREE
Finding free local AI tools that actually hold up.

Paid chat apps → Ollama + Open WebUI
▷ Models run on your machine. Chat UI in the browser.

GitHub Copilot → Cline
▷ Agent in the editor, pointed at a local model.
```

**Substitution:** Roster had Continue. Cursor acquired it (2026); product line messy. Cline is the stand-in.

**5 Privacy** (draft)

```
PAID → FREE
Finding free privacy tools that actually hold up.

1Password / LastPass → Bitwarden
▷ Passwords in a vault you can self-host.

Router ads / paid DNS → AdGuard Home
▷ Block lists on your network.

Paid VPN mesh → Tailscale
▷ Devices on one tailnet.
```

KeePassXC / Pi-hole held as later singles if needed.

---

### 8. Research notes an agent should not re-litigate unless asked

**Photopea.** Browser editor. Opens PSDs. Not open source. GitHub = issues, not the app. Free side has ads (parent stays silent). Its developer ships features on site/X and answers people.

**Resolve.** Free install from Blackmagic. Edit + colour + Fairlight. No watermark. Free export still has limits (UHD 60 was the catch named in research). 21.0 (Jun 2026) then point releases into 21.1 (Sep 2026). Free-tier help = Blackmagic forum.

**Blender.** OSS. Three numbered releases a year (~4 months). 5.2 LTS dated 14 Jul 2026 in this session’s research. Not an AE timeline.

**OBS.** OSS recorder/streamer. Not an editor. Pair with Streamlabs Ultra, not Camtasia, for this opener.

**Krita.** Desktop + Android painter. Not Procreate on iPad.

**Bruno.** Collections as files. Daily client free; some Git UI / extras paid.

**Obsidian.** App free; Sync/Publish paid.

---

### 9. Timing (account + clocks)

Own originals in Brisbane time (AEST, UTC+10): morning (~9–10:30am) and Sunday evening did less badly; mid-afternoon parents died (~21–55 views). Highest reach was the flyer at Tue ~10:35am.

Australia X pattern cited: weekday mornings and ~6–11pm AEST evenings. Saturday weak.

**USER asked “what about now?”** (~10:30–10:37pm AEST 23 Sep 2026):

| Place | Local | Fit |
|---|---|---|
| Brisbane | 10:30pm | Late; user should sleep |
| SG/HK | 8:30pm | Evening OK |
| Tokyo | 9:30pm | Evening OK; JP Blender posts live |
| India | 6:00pm | After work OK |
| London | 1:30pm | Afternoon work-tab |
| EU | 2:30pm | Same |
| New York | 8:30am | Best US slice |
| LA | 5:30am | Asleep |

Live tech feed at that minute: constant drip, low heat (0–16 views on latest builder posts). Overlap clock was decent; session for this account was not (already posted an intro parent that afternoon, then the creator list went up ~10:31pm anyway).

Preferred future slots if choosing: Thu 7:30–8:30am AEST or 6:00–8:00pm AEST, and be present for replies.

---

### 10. Boost trial (if they pay)

**USER:** If boosting one post, which, what region, what age?

**Do not boost:** `Hey @X` flyer; settings threads.

**Boost candidate:** the creator `PAID → FREE` list, **after** it beats the settings baseline (~150 views) or collects bookmarks from non-followers. Do not boost at 13 views the night it ships.

**Region:** United States + United Kingdom + Australia + Canada. English only. Not worldwide. Not Brisbane-only.

**Age UI available to user:** `18 and up`, `21 and up`, `25 and up`, `35 and up`, `50 and up` (floors only).

**USER:** What suits the creator category?

**LOCKED suggestion:** **25 and up.** People who have paid for a CC/Ultra seat.  
- 18+: noisiest, list-farm.  
- 21+: keeps streamer/Procreate students; use only if OBS/Krita are the priority.  
- 35+: drops Streamlabs/Procreate skew; too tight for this five-row post.  
- 50+: skip.

Judge the trial on bookmarks, profile visits, and whether replies are about the tools — not follower count.

---

## Blind spots to keep in the prompt

- Five-row creator post is a grab bag (stills / NLE / 3D / stream / paint). Answer the row they pick; do not defend all five.
- `Streamlabs Desktop` is free; Ultra is paid. Ready reply: `Streamlabs Desktop is free. Ultra is the paid layer. OBS is the thing people move to when they drop that.`
- iPad vs Krita and AE vs Blender will appear. One honest sentence in the thread. Do not edit the parent to add caveats unless the user asks.
- Photopea is not OSS. Do not call it that.
- Tagging five official accounts can look like mention-bait if reused.
- Quoting other mega-lists puts the account in the flyer lane.
- Developer + local AI match the bio; finance/helpdesk are in the roster but optional.
- Cold-start / For You at 35 followers depends more on replies in the first hour than on Boost or tags.

---

## Ready replies if someone argues under post 1

Ads / limits (only if asked):

```
Photopea’s free side has ads. Resolve’s free export stops at UHD 60. Blender is not After Effects’ timeline. It still covers a lot of the motion work.
```

Streamlabs:

```
Streamlabs Desktop is free. Ultra is the paid layer. OBS is the thing people move to when they drop that.
```

Krita:

```
Krita is desktop and Android. It is not Procreate on the iPad.
```

---

## What “done” looks like for a future agent

When asked for the next post:

1. Use the locked two-line header with the category adjective from the table.
2. Stay inside one roster category.
3. 2–5 rows, same `Paid → Free` + `▷` proof shape.
4. Positive proof lines. Catches in replies only.
5. Free-side shoutout in a reply; one handle after post 1.
6. Do not reopen Cinema 4D vs After Effects, Camtasia vs Streamlabs, `I found` vs `Finding`, or job-first hooks unless the user does.
7. Check X talk + what “free” means before substituting a roster row.
8. If they already posted a parent that day, plan replies, not a second parent.
