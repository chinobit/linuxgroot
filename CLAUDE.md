# CLAUDE.md — project context for Claude Code

## Project
Personal technical blog for linuxgroot.net. Complete rebuild — the old AdiDoks-based
site was never finished and is being fully replaced.

## Agent knowledge base (AGENT_KB)
This repo may have a knowledge base attached through the generic `AGENT_KB`
environment variable. The contract, in precedence order:
- **This repo's own instructions win.** Anything here overrides the attached KB's
  equivalent. A KB supplies the personal layer (prior decisions, working preferences),
  never this project's procedures.
- **When `AGENT_KB` is set**, read that KB's own agent instructions (its `AGENTS.md`)
  before any other file in it.
- **When it is unset, skip the KB entirely.** This file is sufficient on its own; no
  step here may depend on a KB being present.
- **Only the variable name is committed, never a value.** The KB path is per-machine
  and lives in `.claude/settings.local.json`, which is gitignored — it is an absolute
  home path, and this repo is public. Do not commit it, and do not name a specific KB,
  path or host anywhere in this repo.

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
- Private files and operational/security configuration are documented in the
  owner's private notes, not in this public repo. Do not add them here.
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
- Analytics: Cloudflare Web Analytics only (cookieless). Its beacon is the ONLY
  third-party script permitted in the CSP; do not add others.
- Edge configuration (headers beyond _headers, bot policy, TLS) is managed in the
  Cloudflare dashboard and documented privately. This repo carries only what the
  build itself needs.
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

## Authoring workflow — generated assets are committed, not built in CI
Both generators run locally and their output is committed. CI stays hermetic: no npm,
no browser, no network beyond the pinned Zola tarball. Run them before committing.
- **New or retitled page** -> `python3 scripts/render-social-cards.py` (add `--force`
  to regenerate all). Renders a 1200x630 card per page and writes `social_media_card`
  into front matter. Without it the page inherits its section's card, which the build
  gate rejects. Needs a local chromium.
- **Edited a diagram** -> `bash scripts/render-diagrams.sh` after changing
  `diagrams/*.mmd`; commit the `.mmd` and the generated `static/diagrams/*.svg`.
  Browser-rendered mermaid is NOT an option: enabling it makes tabi add
  `'unsafe-inline'` to style-src on that page, which the gate rejects.
- **Revising a published post** -> add `updated = YYYY-MM-DD` to its front matter.
  `post_listing_date = "both"` surfaces it; on a reference site the revision date is
  the credibility signal.
- **KaTeX** is safe to enable per page (`katex = true`): measured at zero CSP
  violations. **mermaid is not.**

## Conventions
- Content in content/blog/, tags taxonomy only. Feed: atom.xml.
- Series live in `content/blog/<series>/` with `template = "series.html"`,
  `series = true`, `transparent = true` (so posts still appear in /blog/ and the
  homepage), and `sort_by = "weight"` with `weight = 1, 2, ...` on each post. Weight
  beats date ordering here: posts often share a publication date, and tabi's date
  route needs `paginate_by = 9999` + `paginate_reversed = true` to put chapter one
  first. tabi shows NO series banner unless `[extra.series_intro_templates]` /
  `[extra.series_outro_templates]` are defined in the series `_index.md`; without them
  the series landing page is unreachable from its own posts.
- Front-matter sub-tables (`[extra.series_intro_templates]` and friends) go BELOW every
  bare `[extra]` key, same rule as config.toml.
- One-line shell commands in docs and scripts. Prefer system mechanisms over ad-hoc
  workarounds. Full-file examples over partial snippets.
- Validate config keys against upstream docs before changing:
  tabi: https://welpo.github.io/tabi/blog/mastering-tabi-settings/
  Zola: https://www.getzola.org/documentation/
  Wrangler: https://developers.cloudflare.com/workers/wrangler/configuration/
