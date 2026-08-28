+++
title = "How the scheduler sees you"
description = "A series on batch scheduling from both sides of the queue: what the scheduler is actually optimising, and what that means for the person waiting on a job."
template = "series.html"
sort_by = "date"
transparent = true
insert_anchor_links = "left"

[extra]
series = true
+++

Most friction between cluster operators and the researchers using their clusters
is a translation problem. The scheduler is running a well-defined optimisation
that nobody explained, so its output looks arbitrary: your job waits while
someone else's starts, a smaller request finishes sooner than a large one that
was queued first, and the same script behaves differently on a Tuesday.

None of that is arbitrary. This series works through what the scheduler is
computing, in the order a person actually encounters it: first why a job waits,
then what it costs you, then how to ask for the right thing.

Everything here is written against stock Slurm with common defaults. No site is
quite like that, but the reasoning transfers, and the commands are the ones that
tell you what your site actually configured.
