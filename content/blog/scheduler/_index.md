+++
title = "How the scheduler sees you"
description = "A series on batch scheduling from both sides of the queue: what the scheduler is actually optimising, and what that means for the person waiting on a job."
template = "series.html"
sort_by = "weight"
transparent = true
insert_anchor_links = "left"

[extra]
social_media_card = "/social_cards/blog-scheduler.png"
series = true

# Sub-tables MUST stay below every bare key above: a TOML table header is in effect
# until the next one, so a key placed after these would silently belong to them.
# Without these templates tabi shows no series information at all, which left the
# series landing page unreachable from its own posts.
[extra.series_intro_templates]
next_only = "Part 1 of $SERIES_PAGES_NUMBER in $SERIES_HTML_LINK."
middle = "Part $SERIES_PAGE_INDEX of $SERIES_PAGES_NUMBER in $SERIES_HTML_LINK. Previously: $PREV_HTML_LINK"
prev_only = "Part $SERIES_PAGE_INDEX of $SERIES_PAGES_NUMBER in $SERIES_HTML_LINK. Previously: $PREV_HTML_LINK"
default = "Part $SERIES_PAGE_INDEX of $SERIES_PAGES_NUMBER in $SERIES_HTML_LINK."

[extra.series_outro_templates]
next_only = "Next: $NEXT_HTML_LINK"
middle = "Next: $NEXT_HTML_LINK"
prev_only = "That is the series so far. The index is $SERIES_HTML_LINK."
+++

Most friction between cluster operators and the researchers using their clusters
is a translation problem. The scheduler is running a well-defined optimisation
that nobody explained, so its output looks arbitrary: your job waits while
someone else's starts, a smaller request finishes sooner than a large one that
was queued first, and the same script behaves differently on a Tuesday.

None of that is arbitrary. This series works through what the scheduler is
computing, in the order a person actually encounters it: first why a job waits,
then what holding those resources actually costs you. The two halves answer each
other, and between them they cover most of what a support ticket is really
asking.

Everything here is written against stock Slurm with common defaults. No site is
quite like that, but the reasoning transfers, and the commands are the ones that
tell you what your site actually configured.
