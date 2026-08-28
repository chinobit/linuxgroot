# CLAUDE.md — project context for Claude Code

## Project
Personal technical blog for linuxgroot.net. Complete rebuild — the old AdiDoks-based
site was never finished and is being fully replaced.

## Stack & architecture
- Zola v0.22.1 (static site generator), pinned everywhere — CI binary, local container.
  Zola 0.22 is a breaking release: it replaced the syntect highlighter with giallo and
  moved the highlight keys into [markdown.highlighting]. tabi v4.1.0 still ships a
  0.21-era config.toml, so do not copy the theme's example config verbatim.
- Theme: tabi (welpo/tabi), git submodule at themes/tabi, pinned to v4.1.0 (23a1baf).
  Never track `main`; bump the pin deliberately.
  tabi requires compile_sass = true — its skins, layout and syntax palette are all
  sass/main.scss. With it false the build still exits 0 and serves HTML with no CSS.
- Hosting: Cloudflare Workers Static Assets. Worker name `linuxgroot` (replaces the
  old geolocation placeholder in the same slot). Config in wrangler.jsonc:
  assets-only (no `main`), directory ./public, custom_domain route linuxgroot.net.
- Private files: R2 bucket `linuxgroot-p` (EEUR, Standard) on custom domain
  files.linuxgroot.net, gated by a Cloudflare Access self-hosted application.
  Upload: `wrangler r2 object put linuxgroot-p/<key> --file <path> --remote`.
  No root listing — link objects directly. This is deliberately OUTSIDE the Zola
  build: private content never enters git, public/, the sitemap, or
  search_index.en.js. Do not add a `content/private/` section instead —
  build_search_index would publish its text at /search_index.en.js unauthenticated.
  The bucket's r2.dev Public Development URL must stay DISABLED; it bypasses Access.
- CI/CD: .github/workflows/deploy.yml — push to main -> checkout with submodules ->
  install Zola v0.22.1 -> `zola build` (never pass --drafts) -> wrangler-action deploy.
- Secrets: CLOUDFLARE_API_TOKEN (scoped: Workers Scripts:Edit, this account only),
  CLOUDFLARE_ACCOUNT_ID. GitHub Actions secrets only, never committed.

## Hard constraints — do not change without explicit approval
- Privacy: **this repo is PUBLIC** (decision 2026-08-28, after rewriting author
  metadata to remove a real name from history). The operative rule is therefore
  absolute: nothing identity-bearing may ever enter this repo. No real name, no
  personal email, no employer, institution or hostname, no internal URLs. Commit as
  LinuxGroot <31506370+chinobit@users.noreply.github.com>; the repo-local git identity
  is already set, but verify with `git log -1 --format='%an <%ae>'` before pushing.
  Private files belong in the R2 bucket, never in a commit.
  show_remote_source/show_remote_changes stay false and remote_repository_url stays
  unset regardless: the site does not advertise its own source.
  No comment backends, no webmentions, hcard disabled. Public identity is "LinuxGroot".
- Analytics: Cloudflare Web Analytics is ENABLED by explicit decision on 2026-08-28,
  relaxing the previous "no analytics" rule. It is cookieless and free. The cost is
  that script-src is no longer pure 'self' — see the allowed_domains note in
  config.toml. It remains the ONLY third-party script permitted; do not add others.
- HSTS: max-age 6 months with includeSubDomains, **preload OFF** (decision 2026-08-28).
  Do not enable the preload token without also raising max-age to 12 months and
  deliberately submitting to hstspreload.org; that step binds every subdomain of
  linuxgroot.net to valid HTTPS effectively permanently and takes months to undo.
- AI bots (Cloudflare Security Settings > Configure AI bot policies, from 2026-09-15):
  Training = Block all pages, Agent = Block all pages, Search = Allow. Managed
  robots.txt on. The site stays indexable and discoverable while refusing training
  scrapes. Cloudflare merges its managed robots.txt with the one Zola generates.
- Security: enable_csp = true with the tightened allowed_domains in config.toml
  (self-hosted assets only; img-src does NOT allow https://*). HTTP-only headers
  live in static/_headers; HSTS is set in the Cloudflare dashboard (SSL/TLS ->
  Edge Certificates), never in _headers.
- [markdown.highlighting] style = "class" — required so style-src needs no
  'unsafe-inline'. Do not switch to style = "inline"; it writes a style attribute onto
  every syntax token. (Pre-0.22 this key was highlight_theme = "css".)
- TOML ordering in config.toml: every bare key in [extra] MUST appear before the first
  [extra.*] sub-table. A sub-table opened mid-block silently captures every key below
  it; tabi then falls back to its own defaults and the build still succeeds. This
  previously shipped tabi's default CSP (img-src 'self' https://* data:) while the
  file appeared to specify the tightened one. Keep [extra.hcard] last.
- Drafts: unfinished posts use `draft = true` front matter. CI never builds drafts;
  preview locally with `zola serve --drafts` only.

## Commands
This host has podman, not docker, and no local zola/wrangler binary. Substitute
`docker` for `podman` on hosts that have it; the image and flags are identical.
- Local preview: podman run -u "$(id -u):$(id -g)" -v $PWD:/app --workdir /app -p 8080:8080 --rm ghcr.io/getzola/zola:v0.22.1 serve --interface 0.0.0.0 --port 8080 --base-url localhost --drafts
- Build: podman run --rm --security-opt label=disable -v $PWD:/app -w /app ghcr.io/getzola/zola:v0.22.1 build
- Deploy: push to main (CI) — avoid manual `wrangler deploy` outside CI.

## Verification — the build lies by exiting 0
A successful `zola build` proves nothing about the config taking effect. After any
config.toml change, check the built artifact, not the source:
- CSP actually emitted: `grep -o 'Content-Security-Policy[^>]*' public/index.html`
  (minify_html reorders attributes, so `content=` precedes `http-equiv=`).
- Stylesheets present: `ls public/main.css public/skins/`
- No inline styles: `grep -c 'style="' public/blog/*/index.html` must be 0.
- Zola writes giallo-{light,dark}.css into public/ that tabi never links (~44 KB of
  unreferenced assets). Harmless; do not wire them up without removing tabi's own
  sass/parts/_syntax_theme.scss first, or the two will fight.

## Cost and plan register — alert before exceeding
Standing instruction from the owner: flag anything that is not free-tier, not in the
current subscription, or approaching a free monthly limit. Everything in use today is
free. Verified 2026-08-28.

| Feature | Plan | Free allowance | Current use |
| --- | --- | --- | --- |
| Workers Static Assets | Workers Free | Requests to static assets are free and unlimited. The 100k/day cap applies to Worker *invocations*, and this Worker has no `main`, so it has none. Limits that do bite: 20,000 asset files per version, 25 MiB per file. | Site is far under both |
| R2 | Free tier | 10 GB-month, 1M Class A, 10M Class B ops. Egress always free. | Bucket `linuxgroot-p`, near-empty |
| Zero Trust Access | Free | 50 seats (confirmed by owner 2026-08-28) | 1 self-hosted app, 1 user |
| DNS, DNSSEC, SSL, HSTS, Always Use HTTPS | Free | n/a | Enabled |
| Bot Fight Mode | Free | n/a | Enabled |
| AI bot blocking / AI Crawl Control | Free | n/a | Enabled |
| Web Analytics | Free | Unsampled data retained 7 days, then aggregated to ~10% | Enabled |
| GitHub Actions | Free (private repo) | 2,000 min/month. Build is ~40 s/run. Note: making the repo private started this meter; public repos are unmetered. | Negligible |

NOT enabled and NOT free — do not turn these on without a plan change:
WAF Managed Rules (Pro+), Super Bot Fight Mode (Pro+), Bot Management (Enterprise),
Argo Smart Routing, Workers Paid ($5/mo), R2 Infrequent Access (no free tier).

## Pending (dashboard-only, as of 2026-08-28)
- HSTS: turn `preload` off (live header still carries it; decision above).
- Web Analytics: add linuxgroot.net (automatic setup). CSP already permits the beacon;
  afterwards `curl -s https://linuxgroot.net/ | grep -c beacon.min.js` should be 1.
- From 2026-09-15: Configure AI bot policies per the constraint above.
- Optional: www.linuxgroot.net has no DNS record (leave dead or redirect to apex).

## Conventions
- Content in content/blog/, tags taxonomy only. Feed: atom.xml.
- One-line shell commands in docs and scripts. Prefer system mechanisms over ad-hoc
  workarounds. Full-file examples over partial snippets.
- Validate config keys against upstream docs before changing:
  tabi: https://welpo.github.io/tabi/blog/mastering-tabi-settings/
  Zola: https://www.getzola.org/documentation/
  Wrangler: https://developers.cloudflare.com/workers/wrangler/configuration/
