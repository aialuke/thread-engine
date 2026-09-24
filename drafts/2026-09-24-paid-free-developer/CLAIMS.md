# CLAIMS
Checked: 2026-09-24

Mode: claims. Every claim in `01-hook.md` and `02-shoutout.md`, plus the limits that feed `REPLIES.md`. Nothing here is `tested`: the operator hasn't run any of these tools for this post.

## Swap 1: Postman Team → Bruno

| Claim | Card | Task or model it applies to | Source URL | Date checked | Vendor-stated or tested | Confidence | Notes |
|-------|------|-----------------------------|------------|--------------|-------------------------|------------|-------|
| Bruno is free | 01 | API client | https://www.usebruno.com/ , https://www.usebruno.com/pricing | 2026-09-24 | vendor-stated | high | Homepage: "Free and open source". Pricing: "Open Source" plan, free |
| API collections are plain-text files in your repo | 01 | Keeping API requests with the code | https://www.usebruno.com/ | 2026-09-24 | vendor-stated | high | "Your collections are plain-text files in your repo." Docs: "store collections as files and review API changes like code" (https://docs.usebruno.com/introduction/what-is-bruno) |
| No account | 01 | Using the desktop app | https://www.usebruno.com/ | 2026-09-24 | vendor-stated | high | "Your data never leaves your machine. No cloud sync. No account. No login." |
| Bruno is open source (MIT) | reply | – | https://github.com/usebruno/bruno | 2026-09-24 | vendor-stated | high | GitHub license MIT. Not said on the card; the root says "free" |
| Postman's free plan is 1 user; Team is the paid tier | 01 | Sharing collections with a team | https://www.postman.com/pricing/ | 2026-09-24 | vendor-stated | high | Free $0, 1 user. Solo $9/month (1 user). Team $19/user/month billed annually, unlimited users. Enterprise custom. Card names "Postman Team" |
| Limit: Bruno's in-app Git buttons are paid | reply | Clone, commit, pull from inside Bruno | https://www.usebruno.com/pricing | 2026-09-24 | vendor-stated | high | Git UI is Pro ($6/user/month, annual) and Ultimate ($11). Free plan lists 2 workspaces and "Public" Git repositories. The collection files themselves are plain text in the repo (homepage), so any Git client works on them. That last step is a reading of the homepage, not a line on the pricing page |
| Limit: Bruno's free plan caps OpenAPI syncs | reply | Syncing from an OpenAPI spec | https://www.usebruno.com/pricing | 2026-09-24 | vendor-stated | high | 5 a month free; unlimited on paid plans. Collection Runner reports are paid too |

## Swap 2: Navicat Premium → Beekeeper Studio

| Claim | Card | Task or model it applies to | Source URL | Date checked | Vendor-stated or tested | Confidence | Notes |
|-------|------|-----------------------------|------------|--------------|-------------------------|------------|-------|
| Beekeeper Studio Community is free | 01 | SQL editor | https://www.beekeeperstudio.io/pricing | 2026-09-24 | vendor-stated | high | Community: "100% free to use". README: "free to download … no sign-up, registration, or credit card required" (https://github.com/beekeeper-studio/beekeeper-studio) |
| It's a SQL editor | 01 | Writing and running queries | https://www.beekeeperstudio.io/ | 2026-09-24 | vendor-stated | high | "The SQL Editor and Database Manager Of Your Dreams". "Built-in editor provides syntax highlighting and auto-complete suggestions" |
| Postgres, MySQL and SQLite in the free edition | 01 | Connecting to those databases | https://www.beekeeperstudio.io/pricing | 2026-09-24 | vendor-stated | high | Community list: PostgreSQL, MySQL, SQLite, SQL Server, Redshift, MariaDB, BigQuery, Redis, Cassandra, ClickHouse, DuckDB and more |
| Community Edition is open source (GPLv3) | reply | – | https://github.com/beekeeper-studio/beekeeper-studio | 2026-09-24 | vendor-stated | high | README: "Beekeeper Studio Community Edition (the code in this repository) is licensed under the GPLv3 license." Paid features sit in the same repo under a commercial source-available licence. Not said on the card |
| Navicat Premium is paid; Lite is the free edition | 01 | Multi-database client | https://www.navicat.com/en/store/navicat-premium , https://www.navicat.com/en/products/navicat-premium-lite | 2026-09-24 | vendor-stated | high | The store sells Navicat Premium as a per-user perpetual licence with maintenance plans (prices load in the browser, not in the fetched page). "Navicat Premium Lite is a free version of Navicat", for commercial and non-commercial use, up to 5 users per organisation. Card names "Navicat Premium" |
| Limit: some databases are paid-only in Beekeeper | reply | Oracle, MongoDB, Snowflake, DynamoDB, CockroachDB | https://www.beekeeperstudio.io/pricing | 2026-09-24 | vendor-stated | high | CockroachDB from Indie ($9/user/month annual); Oracle, MongoDB, Trino, SurrealDB from Professional ($14); DynamoDB, Snowflake from Business ($18). AI Shell and cloud workspaces are paid |
| Limit: who the free edition is meant for | reply | Use at work | https://www.beekeeperstudio.io/pricing | 2026-09-24 | vendor-stated | medium | Pricing page: Community is for "students, individuals, non-profits and small businesses with fewer than 10 employees and/or annual revenue below $1m." The README asks people using it for their job to buy a licence, and says "If you can't afford a license, please use the free version". The code is GPLv3. Say it's their request, not a licence term we've checked |

## Swap 3: ngrok Pay-as-you-go → Cloudflare Tunnel

| Claim | Card | Task or model it applies to | Source URL | Date checked | Vendor-stated or tested | Confidence | Notes |
|-------|------|-----------------------------|------------|--------------|-------------------------|------------|-------|
| Cloudflare Tunnel is free | 01 | Publishing a local app | https://developers.cloudflare.com/tunnel/ | 2026-09-24 | vendor-stated | high | "Available on all plans", Free included. "You do not need a paid Cloudflare Access plan to publish an application via Cloudflare Tunnel" (https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/routing-to-tunnel/) |
| Localhost on your own domain | 01 | Serving a local app at a public hostname | https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/routing-to-tunnel/ , https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/get-started/create-remote-tunnel/ | 2026-09-24 | vendor-stated | high | "Cloudflare Tunnel allows you to publish local applications to the Internet via a public hostname." "Before you publish an application through your tunnel, you must add a website to Cloudflare." |
| No open ports | 01 | Network setup | https://developers.cloudflare.com/tunnel/ | 2026-09-24 | vendor-stated | high | "an outbound-only, post-quantum encrypted connection"; no "open inbound ports" or "public IPs" needed |
| ngrok's own-domain plan is paid | 01 | Serving on your own domain | https://ngrok.com/pricing | 2026-09-24 | vendor-stated | high | Free: 1 assigned dev domain, interstitial page, 1 GB, 20k requests. Hobbyist $10/month: 10 ngrok-branded domains, no interstitial, **no custom domains**. Pay-as-you-go $20/month plus usage: "Bring your own domain". Card names "ngrok Pay-as-you-go" |
| Limit: you need a domain on Cloudflare | reply | Named hostnames | https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/get-started/create-remote-tunnel/ | 2026-09-24 | vendor-stated | high | The tunnel is free; the domain isn't something Cloudflare gives you. Anyone without a domain gets no named hostname |
| Limit: Quick Tunnels need no account but are for testing | reply | A throwaway public URL | https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/ | 2026-09-24 | vendor-stated | high | Random `trycloudflare.com` subdomain; "No Cloudflare account, API token, DNS record, or custom domain required"; "intended for testing and development only"; 200 in-flight requests; no Server-Sent Events; no SLA |

## Cut

| Row | Why |
|---|---|
| Docker Desktop → Podman Desktop | Docker Desktop is free for "small businesses (fewer than 250 employees AND less than $10 million in annual revenue)", personal use, education and non-commercial open source (https://docs.docker.com/subscription/desktop-license/). For most of this audience the paid side isn't paid, and "Docker Business" isn't a product people talk about by that name. Podman Desktop itself holds up ("Free & Open Source", https://podman-desktop.io/); keep it for a single or a later post |
| DataGrip as the SQL row's paid side | DataGrip is free for non-commercial use since Oct 2025 (https://blog.jetbrains.com/datagrip/2025/10/01/datagrip-is-now-free-for-non-commercial-use/), so it would need "DataGrip commercial". Navicat Premium has a clean paid name. X talk is about even (below) |
| OrbStack | Not open source, and the roster's other Docker Desktop row. Same reason as Docker Desktop |

## Paid sides people on X talk about

Checked with `python3 scripts/x_read.py search` (every post checked against the X API, at most 10 returned):

- **Postman:** `"postman alternative"` returned 7 posts, including `2101965724382286092` (developers paying for Postman instead of free tools) and `2100279289036099721` (a colleague recommending Bruno).
- **ngrok:** `"ngrok alternative"` and similar returned 10, including `2092266377499558009` (a self-hosted ngrok alternative, 18k views, 332 bookmarks).
- **Navicat:** 9 posts, users among them: `2098165104147870068` (someone replacing Navicat with an open-source client), `2101547708582617131`, `2100280327872680105` (a Navicat 18 review).
- **DataGrip:** 9 posts, mostly JetBrains' own accounts.

## Shout-out

| Claim | Card | Task or model it applies to | Source URL | Date checked | Vendor-stated or tested | Confidence | Notes |
|-------|------|-----------------------------|------------|--------------|-------------------------|------------|-------|
| `@use_bruno` is Bruno's organisation account | 02 | – | `python3 scripts/x_api.py user use_bruno` | 2026-09-24 | – | high | Handle checked with `python3 scripts/x_api.py user use_bruno` on 2026-09-24: name "Bruno", verified (blue), 8,594 followers, last post 2026-09-23 |
| "keeping API collections in plain files" | 02 | – | https://www.usebruno.com/ | 2026-09-24 | vendor-stated | high | "Your collections are plain-text files in your repo." |
| "shipping again this week" | 02 | – | https://github.com/usebruno/bruno/releases | 2026-09-24 | vendor-stated | high | v4.2.0 published 2026-09-23 14:25 UTC. Still true on 25 Sep; if the post slips past 30 Sep, change or cut the phrase |
