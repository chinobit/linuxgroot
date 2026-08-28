# HANDOFF.md — session state as of 2026-08-28

Read CLAUDE.md first for stable project context. This file is the current working
state; delete or update it as items complete.

## Done
- Old AdiDoks site fully removed: sass/, templates/, netlify.toml, the adidoks
  submodule, all demo content (docs/, authors/, privacy-policy/, sample posts) and
  the doks-branded static assets.
- tabi added as a submodule at themes/tabi, pinned to v4.1.0 (23a1baf).
- Config files placed: config.toml, wrangler.jsonc, static/_headers,
  .github/workflows/deploy.yml, CLAUDE.md.
- Content skeleton: content/_index.md, content/blog/_index.md, content/archive/_index.md,
  and one published post (an empty site cannot build — tabi's atom.xml template
  dereferences `last_updated`, which is undefined with zero pages).
- Build verified green against the pinned Zola 0.22.1 container image.

### Three config bugs found and fixed (all of which built successfully first)
1. `compile_sass = false` — tabi is a Sass theme. Build exited 0 and served no CSS.
2. Zola 0.22 breaking change: `highlight_code` / `highlight_theme = "css"` replaced by
   `[markdown.highlighting] style = "class"`, and syntect replaced by giallo. This one
   was a hard parse error, so it surfaced immediately.
3. `[extra.hcard]` sat mid-block in config.toml, so every key below it (enable_csp,
   allowed_domains, toc, copy_button, show_reading_time) was silently nested inside
   extra.hcard and inert. The site was shipping tabi's DEFAULT CSP, including
   `img-src 'self' https://* data:` — the exact thing CLAUDE.md forbids.

Verified from the built artifact, not the source: CSP is now
`default-src 'self'; font-src 'self' data:; img-src 'self' data:; media-src 'self';
style-src 'self'; connect-src 'self'; script-src 'self'` with no frame-src, and zero
inline `style=` attributes in rendered posts.

### Privacy and identity
This repo is public. Author metadata across all history was rewritten to
LinuxGroot <31506370+chinobit@users.noreply.github.com>, and LICENSE, README and
site.webmanifest carry the handle only. The standing rule is in CLAUDE.md: nothing
identity-bearing enters this repo, ever. Private files live in the R2 bucket.

## Next steps (in order)
1. **Unblock the deploy.** Free the apex hostname (see the BLOCKER section above), then
   re-run the workflow. Everything else in the pipeline is already proven green.
2. After the first successful deploy, verify from outside:
   - `curl -sI https://linuxgroot.net | grep -Ei 'x-frame|nosniff|referrer|permissions'`
   - the old `access-control-allow-origin: *` header is gone
   - `curl -s https://linuxgroot.net/ | grep -c 'beacon.min.js'` is 1 once Web Analytics
     is enabled, and the browser console shows no CSP violation for it
3. Cloudflare dashboard, per the decisions recorded in CLAUDE.md:
   - SSL/TLS > Edge Certificates > HSTS: turn **preload off**, keep 6 months and
     includeSubDomains.
   - Security Settings > Configure AI bot policies (available from 2026-09-15):
     Training = Block all pages, Agent = Block all pages, Search = Allow. Turn on the
     managed robots.txt preference.
   - Analytics & Logs > Web Analytics: add linuxgroot.net, automatic setup.

## Done, verified
- Cloudflare API token authenticates and wrangler v4 uploads the Worker version.
- HSTS live at max-age 15552000 with includeSubDomains.
- Zero Trust: 50 free seats, one self-hosted Access application.
- R2 public development URL disabled.
- CSP emitted from the built artifact matches the intended policy.

## Cloudflare platform findings (verified via Cloudflare MCP, 2026-08-28)
- The Cloudflare MCP connector is already authenticated and working — nothing to enable.
- The account holds exactly one Worker: `linuxgroot`, created 2023-04-17. That is the
  geolocation placeholder, which the first successful deploy overwrites in place.
- **There is no Pages project to migrate from.** wrangler.jsonc is already in the exact
  end state Cloudflare's Pages-to-Workers guide targets: assets-only
  (`"assets": {"directory": "./public"}`, no `main`), deployed with `wrangler deploy`,
  never `wrangler pages deploy`. Nothing to do. (Caveat: the available MCP tools list
  Workers, not Pages projects, so this rests on the guide's criteria plus the Worker
  listing rather than a direct Pages enumeration.)
- CI is green through `zola build`. The deploy step failed, but NOT for lack of
  secrets as first assumed — run 33165472226 shows
  `Missing entry-point: ... or the \`main\` config field`. cloudflare/wrangler-action@v3
  defaults to wrangler 3.90.0, which predates assets-only Workers; those need
  wrangler v4+. Fixed by pinning `wranglerVersion: '4.127.0'` in the workflow.
  The secrets are still absent, so the next run will fail on authentication instead —
  that is the expected state until step 2 below is done.

## Open questions
- Skin: currently "teal". "monochrome" is the other candidate.
- Publish a base64-encoded email in the footer? Currently omitted entirely.
- Content plan beyond the inaugural post.

## Private section: BUILT and verified (2026-08-28)
R2 bucket `linuxgroot-p` (EEUR, Standard) on custom domain files.linuxgroot.net, behind
a Cloudflare Access self-hosted application. No Worker code, no repo changes: private
files never enter git, public/, the sitemap, or the search index.

Verified from outside: an unauthenticated GET to both `/` and `/test.txt` returns
302 to linuxgroot-pages.cloudflareaccess.com with `www-authenticate: Cloudflare-Access`.

Public Development URL confirmed **Disabled** by the owner on 2026-08-28, so the
pub-*.r2.dev bypass path is closed. Re-check this after any bucket settings change: it
is the one way to expose the bucket without touching Access.
Bucket root listing is not supported, so link objects directly.

Upload with: `wrangler r2 object put linuxgroot-p/<key> --file <path> --remote`
