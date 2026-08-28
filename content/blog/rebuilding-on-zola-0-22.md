+++
title = "Three ways a static site build lies to you"
date = 2026-08-28
description = "Migrating to Zola 0.22.1 on a theme built for 0.21: one loud failure, and two that exit zero while quietly shipping the wrong site."

[taxonomies]
tags = ["zola", "static-sites", "csp", "cloudflare"]
+++

This site is a static build: [Zola](https://www.getzola.org) renders Markdown into
`public/`, and Cloudflare Workers Static Assets serves it. No server code, no
database, no third-party JavaScript. The whole deploy is a `git push`.

Pinning Zola to 0.22.1 while the theme's latest release still targets 0.21 turned up
three problems. The first one stopped the build. The other two did not, which is why
they are worth writing down.

## The loud one: `[markdown]` highlighting moved

Zola 0.22 replaced the flat highlight keys with a sub-table, and the old ones are a
hard parse error rather than a deprecation warning:

```toml
# 0.21 and earlier
[markdown]
highlight_code = true
highlight_theme = "css"

# 0.22
[markdown.highlighting]
style = "class"
light_theme = "catppuccin-latte"
dark_theme = "catppuccin-frappe"
```

0.22 also swapped the syntect highlighter for
[giallo](https://github.com/getzola/giallo). Encouragingly, giallo still emits the
same semantic class names -- `z-comment`, `z-string`, `z-punctuation` -- so a theme
carrying its own hand-written syntax stylesheet keeps working across the swap.

`style = "class"` is the setting that matters for security. Inline highlighting
writes a `style` attribute onto every token, which forces
`style-src 'unsafe-inline'` into your Content-Security-Policy, and at that point the
policy is decorative. Class-based output keeps `style-src 'self'` honest. Verified,
not assumed: the rendered post has zero `style="` attributes in it.

## The quiet one: a theme that needs Sass, and a config that said no

The config carried `compile_sass = false`, on the reasoning that the theme shipped
plain CSS. It does not -- its skins, layout and syntax palette are all
`sass/main.scss`. Zola does not warn about this. It builds, exits zero, and serves
HTML with no stylesheet at all.

There is no clever lesson here beyond the obvious one: a build that succeeds has told
you nothing about whether it produced the site you wanted.

## The quietest one: TOML sub-tables capture everything below them

This is the one worth the whole post. The config's `extra` table looked fine:

```toml
[extra]
author = "LinuxGroot"

[extra.hcard]
enable = false

# ...forty lines later, still "in" [extra]?
enable_csp = true
allowed_domains = [
    { directive = "img-src", domains = ["'self'", "data:"] },
]
```

It is not fine. In TOML, a table header is in effect until the next one, so every
key after `[extra.hcard]` belongs to `extra.hcard` -- not to `extra`. The CSP
settings, the table of contents, the reading time, the copy button: all of them
landed in a sub-table nothing reads.

No error. No warning. The theme simply fell back to its own defaults, and the site
shipped with a policy including `img-src 'self' https://* data:` -- which permits
loading an image from any host on the internet -- rather than the tightened one the
config plainly appeared to specify. Reading the config file, the policy is right.
Reading the rendered page, it is not.

The rule that falls out of this: put every bare key before the first sub-table, and
verify the policy from the built artifact rather than the source that was supposed to
produce it.

```
grep -o 'Content-Security-Policy[^>]*' public/index.html
```

Which is the same rule as the previous section, and honestly the same rule as most
sections. Exit code zero is not evidence. The artifact is evidence.

## Where headers actually live

One structural note, since the CSP came up. A `<meta http-equiv>` CSP covers
resource-loading directives, but it cannot express `frame-ancestors` -- that
directive is ignored in `<meta>` by specification -- and it has no business carrying
HSTS. So the split here is three places, each holding the directives that are
enforceable there:

- `<meta>` CSP from the theme: `default-src`, `script-src`, `style-src`, `img-src`.
- `static/_headers`, copied verbatim into `public/` and read by Workers:
  `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`,
  `Permissions-Policy`, the cross-origin isolation pair.
- HSTS in the Cloudflare edge configuration, set once, so nothing can emit a
  duplicate `Strict-Transport-Security`.

Three places is one more than anyone wants. Each directive lives where it is actually
enforced.
