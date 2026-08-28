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

## Cloudflare platform findings (2026-08-28, corrected)
- The account now holds one Worker, `linuxgroot`, serving the site as assets-only
  (no `main`) — the end state Cloudflare's Pages-to-Workers guide targets.
- An earlier finding here claimed "there is no Pages project to migrate from". That
  was wrong: workers_list does not enumerate Pages projects, and a Pages project in
  fact owned the apex and served the old AdiDoks build until the owner deleted it.
  Lesson recorded: absence from one API listing is not absence from the account.
- cloudflare/wrangler-action@v3 defaults to wrangler 3.90.0, which predates
  assets-only Workers and fails with "Missing entry-point". The workflow pins
  `wranglerVersion: '4.127.0'`.

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
