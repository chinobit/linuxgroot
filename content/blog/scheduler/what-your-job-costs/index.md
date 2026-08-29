+++
title = "What your job actually costs"
date = 2026-08-28
updated = 2026-08-29
weight = 2
description = "Fairshare charges you for what you reserved, not what you used. Billing weights, why an idle GPU costs exactly as much as a busy one, and the one over-request that is genuinely free."
insert_anchor_links = "left"

[taxonomies]
tags = ["slurm", "hpc", "scheduling", "gpu"]

[extra]
social_media_card = "/social_cards/blog-scheduler-what-your-job-costs.png"
toc = true
+++

The previous post ended on fairshare: your priority falls as your recent usage
rises. That leaves the obvious question unanswered, and it is the one almost
nobody is told the answer to.

What, precisely, counts as usage?

It is not CPU cycles burned. It is not GPU utilisation. It is not how much of
your allocation you actually touched. Slurm charges you for **what you reserved,
for as long as you held it**, and the exchange rate between resource types is a
local policy decision you can read in one command.

## The exchange rate

A cluster has to compare unlike things. Is one GPU-hour worth more than sixteen
CPU-hours? More than 200 GB of memory held for an hour? There is no universal
answer, so each site declares one, per partition, as billing weights:

```bash
scontrol show partition <partition> | grep -i tresbilling
```

You will get something along these lines:

```
TRESBillingWeights=CPU=1.0,Mem=0.25G,GRES/gpu=10.0
```

Read that as an exchange rate. One CPU-second costs 1. One gigabyte of memory
held for a second costs 0.25. One GPU-second costs 10, which is to say a GPU on
this hypothetical partition is worth ten CPUs. Your job's billing figure is
normally the weighted sum across everything it holds, and that number, multiplied
by seconds held, is what accrues against your fairshare.

Sites can change the arithmetic (`PriorityFlags=MAX_TRES` bills on the largest
component rather than a straight sum, which stops a large-memory GPU job being
charged twice for what is effectively one decision). Check rather than assume:

```bash
scontrol show config | grep -i priorityflags
```

You do not have to compute any of this by hand. Slurm records the result:

```bash
sacct -j <jobid> --format=JobID,Elapsed,AllocTRES%60
```

The `billing=` field in `AllocTRES` is the number. That is the figure your
fairshare is charged per second, and seeing it once tends to reframe how people
size requests.

## Reserved, not used

Here is the part that costs people the most, and it follows directly from the
sentence above: billing counts **allocated** resources, not utilised ones.

A job holding four GPUs at 3% utilisation is billed exactly the same as a job
holding four GPUs at 99%. The scheduler cannot give the idle three to anyone
else, because you are holding them. From the cluster's point of view there is no
difference between the two jobs, and from the fairshare accountant's point of
view there is no difference either.

This is why "I only ran a small test" is not a defence for an eight-GPU
interactive session left open over lunch. The bill is the reservation.

Two corollaries that surprise people:

**Memory is a resource, not a safety margin.** Requesting 480 GB on a 512 GB node
does not just cost memory-billing; it makes the node effectively unusable by
anyone else, so you have quietly reserved the whole machine. Check what you
actually peaked at:

```bash
sacct -j <jobid> --format=JobID,MaxRSS,ReqMem,AllocTRES%60
```

**Exclusive means exclusive.** `--exclusive` bills you for the entire node's
resources regardless of what you asked for or touched. It is the right flag for
benchmarking and for jobs sensitive to noisy neighbours. It is an expensive
accident otherwise.

## The over-request that is free

Now the useful inversion, and the reason this post follows the one about pending
jobs rather than preceding it.

Billing accrues over **elapsed** time, not requested time. A job that asks for 24
hours and finishes in 40 minutes is charged for 40 minutes. Padding your walltime
does not cost you a single unit of fairshare.

So the two over-requests are not remotely equivalent, and they fail in different
directions:

- Over-requesting **resources** costs you real fairshare, every second, and
  pushes your future priority down.
- Over-requesting **time** costs you nothing in fairshare, but excludes you from
  backfill windows, so it costs you *queue* time instead.

People routinely have this backwards. They pad the walltime "to be safe" and then
ask for more GPUs than the code can use "since I'm waiting anyway", which is
precisely the wrong trade in both directions. The correct instinct is the
opposite: be honest about time, be stingy about resources.

Neither is free. They are simply charged to different accounts, and knowing which
is which is the whole skill.

## Where the money actually goes

If you want to know what your recent work has cost, in the same units the
scheduler thinks in:

```bash
sreport cluster AccountUtilizationByUser start=now-30days -t hours
```

And for your own jobs, the efficiency view that turns billing into a decision:

```bash
seff <jobid>
```

`seff` reports what you reserved against what you used. A job showing 6% CPU
efficiency and 4 GB peak against a 64 GB request is not a job that ran badly; it
is a job that was *sized* badly, and the difference between those two readings is
worth a great deal over a year.

## The short version

You are billed for the reservation, for as long as you hold it, at your site's
exchange rate. An idle GPU is a full-price GPU. Padding time is free, padding
resources is not.

```bash
scontrol show partition <partition> | grep -i tresbilling   # the exchange rate
sacct -j <jobid> --format=JobID,Elapsed,MaxRSS,AllocTRES%60 # what you were charged
seff <jobid>                                                # what you needed
```

Run the third one on your last five jobs. Most people discover their next request
should be about half the size, which is also the request that starts sooner.

Doing that arithmetic across five jobs by hand is exactly the sort of thing nobody
gets around to, so hand it over:

**Prompt for your agent:**

```text
Help me work out what my recent jobs actually cost, and what I should be
requesting instead.

Here is what my cluster and my jobs report:
<paste your partition's billing configuration>
<paste the accounting output for your last five jobs>

For each job, tell me what I was charged, what I actually used, and what the
request should have been. Show the arithmetic against my site's own billing
weights rather than assuming a standard exchange rate, since every site sets its
own and the difference is the whole point.

Then rank my habits by what they cost me: over-requesting memory, over-requesting
GPUs, or holding an allocation idle. If my configuration is missing something you
need to answer properly, tell me what is missing instead of substituting a
default value.
```
