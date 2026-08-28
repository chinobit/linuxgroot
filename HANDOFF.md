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
     Confirmed absent as of this session, so CI currently fails at the deploy step.
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
- CI is green through `zola build`; the only failing step is the Cloudflare deploy,
  for lack of secrets. Run 33165472226 is the evidence.

## Open questions
- Skin: currently "teal". "monochrome" is the other candidate.
- Publish a base64-encoded email in the footer? Currently omitted entirely.
- Content plan beyond the inaugural post.

## Proposed: authenticated private section
Requested this session. Confirmed against Cloudflare's docs: the design keeps the site
fully static and adds **no auth code**. Put Cloudflare Access (Zero Trust) in front of
a path by creating a **self-hosted application** whose application domain is the path.

- Zero Trust > Access > Applications > self-hosted, domain `linuxgroot.net/private`.
  Access runs at the edge before the Worker, so an unauthenticated request to
  `/private/*` never reaches the assets.
- Policy: allow by email address (a fixed allowlist) or by email domain. Login via
  one-time email PIN needs no IdP at all. Free tier covers 50 users.
- Prerequisite: Zero Trust must be enabled on the account first.
- No change to wrangler.jsonc, no `main` script, no session code to get wrong.
- Note the alternative Cloudflare now offers — attaching Access to the *Worker* rather
  than a hostname — which covers every route and preview URL automatically. That is the
  better choice if the whole site should be private, and the wrong one here, since only
  `/private/*` should require sign-in.

Two decisions needed before implementing:
- **Where private files live.** Simplest is `content/private/` built into `public/` and
  gated by the Access policy. That means the files are also in the git repo, and a
  misconfigured Access policy exposes them. The safer split is an R2 bucket behind a
  separate Access-protected route, so private files never enter the repo or the static
  build at all. R2 is the recommendation if the content is genuinely sensitive.
- **Who gets in.** A fixed email allowlist, or a domain rule.
Do not build this until both are answered.
