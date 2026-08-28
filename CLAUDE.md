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
- CI/CD: .github/workflows/deploy.yml — push to main -> checkout with submodules ->
  install Zola v0.22.1 -> `zola build` (never pass --drafts) -> wrangler-action deploy.
- Secrets: CLOUDFLARE_API_TOKEN (scoped: Workers Scripts:Edit, this account only),
  CLOUDFLARE_ACCOUNT_ID. GitHub Actions secrets only, never committed.

## Hard constraints — do not change without explicit approval
- Privacy: repo is private (it was found PUBLIC on 2026-08-28 and switched; see
  HANDOFF.md for the residual-exposure follow-ups). show_remote_source/show_remote_changes stay false;
  remote_repository_url stays unset. No comment backends, no webmentions, no
  analytics, hcard disabled. Public author identity is the handle "LinuxGroot".
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

## Conventions
- Content in content/blog/, tags taxonomy only. Feed: atom.xml.
- One-line shell commands in docs and scripts. Prefer system mechanisms over ad-hoc
  workarounds. Full-file examples over partial snippets.
- Validate config keys against upstream docs before changing:
  tabi: https://welpo.github.io/tabi/blog/mastering-tabi-settings/
  Zola: https://www.getzola.org/documentation/
  Wrangler: https://developers.cloudflare.com/workers/wrangler/configuration/
