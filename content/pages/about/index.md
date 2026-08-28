+++
title = "About"
template = "info-page.html"
path = "/about"
insert_anchor_links = "left"

[extra]
social_media_card = "/social_cards/pages-about.png"
+++

I run Linux systems for a living: batch schedulers, GPU nodes, the storage and
networking underneath them, and the long tail of scientific software that has to
compile and run on top of all of it.

This site collects the notes I wish I had found first. How a scheduler actually
decides what runs next. Why a build that exits zero can still be shipping the
wrong thing. What an AI agent needs from your documentation before it becomes
useful rather than merely fast.

## Two audiences, one set of problems

Cluster operators, and the researchers whose work is the entire reason clusters
exist. A lot of the friction between those groups turns out to be a translation
problem rather than a technical one, and translation problems are fixable in an
afternoon once somebody writes the thing down.

So the posts here try to work from both directions: what the system is really
computing, and what that means for the person waiting on it.

## What is not here

Everything on this site is written generically, on purpose. Nothing about any
particular employer, cluster, hostname or internal practice appears here, and
nothing will. The techniques travel between sites perfectly well; the specifics
belong to the people who run them.

That constraint has been good for the writing. It forces each post to be about
the mechanism rather than the anecdote, which is the part that was worth reading
anyway.

## Colophon

This site is static and deliberately boring: Markdown rendered by
[Zola](https://www.getzola.org) into plain HTML, served from the edge, deployed
by a push to `main`. No comment backend, no third-party fonts, no tracking
scripts beyond aggregate, cookieless page counts.

The security posture is enforced against the built output rather than the
configuration that produced it, because every real bug this site has had
compiled successfully and served the wrong thing. That story is
[its own post](@/blog/rebuilding-on-zola-0-22.md).

## A note of thanks

The kernel, the compiler toolchains, the scheduler, the editor, the static site
generator that rendered this page: every layer of the stack I work on is open
source, and a great deal of it was written by people who were not paid to write
it. I have built an entire career on that generosity. Writing down what I have
learned is a modest way of putting something back.
