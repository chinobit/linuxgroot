+++
title = "Three ways a static site build lies to you"
date = 2026-08-28
updated = 2026-08-29
description = "Migrating to Zola 0.22.1 on a theme built for 0.21: one loud failure, and two that exit zero while quietly shipping the wrong site."

[taxonomies]
tags = ["zola", "static-sites", "csp", "cloudflare"]

[extra]
social_media_card = "/social_cards/blog-rebuilding-on-zola-0-22.png"
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

No error. No warning. The theme simply fell back to its own defaults and shipped a
much looser policy than the one the config plainly appeared to specify. Reading the
config file, the policy is right. Reading the rendered page, it is not.

The rule that falls out of this: put every bare key before the first sub-table, and
verify the policy from the built artifact rather than the source that was supposed to
produce it.

```
grep -o 'Content-Security-Policy[^>]*' public/index.html
```

Which is the same rule as the previous section, and honestly the same rule as most
sections. That grep is the beginning of a check, not the whole of one, and the whole
of one is specific to whatever you are building:

**Prompt for your agent:**

```text
I want to verify my static site's built output rather than trusting its config,
because a build that exits zero has told me nothing about what it produced.

My generator is <generator and version>, my theme is <theme and version>, and my
build directory is <path>.

Write me a check script that runs against the built HTML rather than the source,
and asserts: that every page carries the Content-Security-Policy I intended, that
no page has quietly acquired 'unsafe-inline' or a wildcard host, that no page
carries inline style attributes, and that nothing loads a subresource from a
domain I did not approve.

For each check, tell me the specific failure it exists to catch, and cite the
generator or theme documentation for the setting involved. Then prove each check
can fail: give me a way to plant a violation and confirm the check reports it. A
check that matches nothing passes silently, which is the same class of problem as
the ones above.
```

Exit code zero is not evidence. The artifact is evidence.
