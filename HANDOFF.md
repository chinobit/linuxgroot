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

## SITE IS LIVE (2026-08-28, run 33176779761)
The apex was owned by the old Cloudflare Pages project serving the AdiDoks build; the
owner deleted it, wrangler attached the custom domain, and the deploy went green end
to end. Verified from outside:
- https://linuxgroot.net serves the tabi site ("I am LinuxGroot"); AdiDoks gone.
- All static/_headers headers live: X-Frame-Options DENY, nosniff, Referrer-Policy,
  Permissions-Policy, COOP/CORP. The old `access-control-allow-origin: *` is gone.
- Meta CSP live and identical to the built artifact, including the Web Analytics
  beacon allowance. Blog post and atom.xml return 200; bogus paths return 404.
- Repo is PUBLIC (owner's decision, accepting the dangling-SHA residual: pre-rewrite
  commits with the real name remain fetchable by SHA on GitHub).

Loose end: www.linuxgroot.net has no DNS record and does not resolve. Either leave it
dead deliberately or add an apex redirect (DNS record + redirect rule, free). HSTS
includeSubDomains will apply to it once it exists.

## Next steps (dashboard only)
1. SSL/TLS > Edge Certificates > HSTS: turn **preload off** (decision in CLAUDE.md);
   the live header still carries `preload`.
2. Analytics & Logs > Web Analytics: add linuxgroot.net, automatic setup. CSP already
   permits the beacon; after enabling, `curl -s https://linuxgroot.net/ | grep -c
   beacon.min.js` should be 1 and the console clean.
3. From 2026-09-15, Security Settings > Configure AI bot policies: Training = Block,
   Agent = Block, Search = Allow; enable managed robots.txt.
4. Optional: decide on www (redirect or leave dead).

## Done, verified
- Deploy pipeline green end to end; site, headers, CSP, feed, 404 verified live.
- Cloudflare API token authenticates; wrangler v4 handles the assets-only config.
- History rewritten to a single identity; repo public; git identity pinned repo-local.
- HSTS live at max-age 15552000 with includeSubDomains.
- Zero Trust: 50 free seats, one self-hosted Access application gating files.linuxgroot.net.
- R2 public development URL disabled.

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
