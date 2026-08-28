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

### Privacy remediation
- **The GitHub repo was PUBLIC.** CLAUDE.md asserted it was private; it was not.
  Switched to private on 2026-08-28.
- Scrubbed from tracked files: LICENSE copyright (real name -> "LinuxGroot"), README
  (removed the repo URL and stale Zola 0.17.2 commands), static/site.webmanifest
  (was branded "Zola Theme AdiDoks").
- Repo-local git identity set to LinuxGroot <31506370+chinobit@users.noreply.github.com>
  so future commits carry no real name or personal email.

## Next steps (in order)
1. **Decide on the residual public exposure.** While the repo was public, the real name
   and personal email were visible in LICENSE and in all five commit author fields.
   Making it private stops new exposure but does not retract what was already fetched,
   forked, or indexed. Options: leave it (history is only visible to collaborators now),
   or rewrite author metadata with `git filter-repo --mailmap` and force-push. The
   second is destructive and changes every commit SHA — your call, not the agent's.
2. Manual dashboard work, not scriptable here:
   - Create scoped Cloudflare API token (Workers Scripts:Edit, this account only).
   - Add CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID as GitHub Actions secrets.
     Confirmed absent as of this session; the deploy step cannot succeed without them.
   - Enable HSTS in Cloudflare SSL/TLS -> Edge Certificates (max-age >= 6 months,
     includeSubDomains, no preload yet).
3. First real deploy: once secrets exist, push to main and verify
   `curl -sI https://linuxgroot.net | grep -Ei 'x-frame|nosniff|referrer|permissions'`.
4. Decide the private/authenticated section design (see below).

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

Still to confirm in the dashboard (cannot be read via the MCP tools):
- R2 > linuxgroot-p > Settings > **Public Development URL must show Disabled**. If it is
  enabled, the bucket is reachable at its pub-*.r2.dev address and **Access is bypassed
  entirely**. This is the single most important check on this setup.
- Bucket root listing is not supported, so link objects directly.

Upload with: `wrangler r2 object put linuxgroot-p/<key> --file <path> --remote`
