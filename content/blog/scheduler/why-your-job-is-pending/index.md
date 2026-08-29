+++
title = "Why your job is still pending"
date = 2026-08-28
updated = 2026-08-29
weight = 1
description = "Fairshare is not a queue and priority is not a position. What Slurm computes while your job waits, and the three commands that tell you which part of it you are losing to."
insert_anchor_links = "left"

[taxonomies]
tags = ["slurm", "hpc", "scheduling", "gpu"]

[extra]
social_media_card = "/social_cards/blog-scheduler-why-your-job-is-pending.png"
katex = true
toc = true
+++

The most common question a cluster admin gets is some version of *my job has been
sitting there for six hours, is something broken?* Usually nothing is broken. The
scheduler is doing exactly what it was configured to do, and the reasoning is
legible if you know which three commands to run.

This is the explanation I would rather link to than retype, written for the
person waiting as much as for the person who configured the wait.

## A queue that is not a queue

The first thing to unlearn: a Slurm partition is not a line at a bank. Nothing
holds a position. On every scheduling cycle, Slurm recomputes a priority number
for every pending job and considers them in that order. A job submitted after
yours can be given a higher number on the next pass and start first, forever, and
no rule has been broken.

With the multifactor plugin, that number is a weighted sum:

```
Job_priority =
      site_factor
    + PriorityWeightAge       * age_factor
    + PriorityWeightAssoc     * assoc_factor
    + PriorityWeightFairshare * fairshare_factor
    + PriorityWeightJobSize   * job_size_factor
    + PriorityWeightPartition * partition_factor
    + PriorityWeightQOS       * qos_factor
    + SUM(TRES_weight_* * TRES_factor_*)
    - nice_factor
```

Each factor is normalised to the range 0 to 1. The weights are integers set by
the site, and they are where local policy actually lives. A site that sets
`PriorityWeightFairshare=1000000` and `PriorityWeightAge=1000` has decided that
history matters a thousand times more than patience. You can read the decision
rather than guess at it:

```
scontrol show config | grep -i ^Priority
```

That single command answers more support tickets than any amount of speculation.

## Fairshare is a debt, not a rank

Fairshare is the factor people find least intuitive, because the name suggests
everyone gets a turn. What it actually encodes is: *relative to the share you
were allocated, how much have you consumed lately?*

In the classic formulation the factor for an association is

$$F = 2^{-U_{\text{eff}} / S_{\text{norm}}}$$

where $S_{\text{norm}}$ is your normalised share of the machine and
$U_{\text{eff}}$ is your effective normalised usage. Two consequences fall
straight out of the exponent. Consume exactly your share and the factor sits at
0.5. Consume nothing and it approaches 1.0, but it never exceeds it, so idling
for a month buys you no more priority than idling for a week.

Modern Slurm defaults to Fair Tree rather than this formula directly: it walks
the association tree, ranks siblings at each level by shares over usage, and
assigns factors from that ordering. The practical difference is that a
well-behaved user inside a heavily-consuming account is still ranked below users
in an account that has been quiet. Fairshare is inherited. This surprises people,
and it is working as designed: the share was allocated to the group.

The other half is decay. Usage is aged out with a half-life, seven days by
default (`PriorityDecayHalfLife`). A large job stops counting against you
gradually, not at midnight, and not at the start of the month. Two weeks after a
big run, roughly a quarter of it still weighs on you.

```
sshare -U -u $USER
```

`RawShares`, `NormShares`, `EffectvUsage` and `FairShare` in that output are the
whole story. If `FairShare` is near zero, no amount of waiting fixes it quickly;
the fix is time, or a conversation about shares.

## Which factor are you actually losing to?

Priority is a sum, so "low priority" is not a diagnosis. Decompose it:

```
sprio -j <jobid> -l
```

This prints your job's per-factor contribution next to the weights. In practice
one column dominates, and it tells you what to do next. Losing on `FAIRSHARE` is
a usage conversation. Losing on `AGE` means you are simply early and the answer
is patience. Losing on `PARTITION` or `QOS` means you submitted to the wrong
place, which is the one case that is fixable in the next thirty seconds.

And before any of that, check whether priority is even the reason:

```
squeue -j <jobid> -o "%.18i %.9P %.8T %.10M %.11l %.6D %R"
```

The last column is the reason code, and it is frequently not `Priority` at all:

- `Resources`: you are next, the hardware is not free yet. Nothing to fix.
- `Dependency`: waiting on another job that may itself be pending or failed.
- `QOSMaxJobsPerUserLimit`, `AssocGrpGPURunMinutes` and friends: you have hit a
  configured cap. More submissions will not help; they queue behind the same cap.
- `ReqNodeNotAvail`: you asked for a specific node or feature that is down,
  drained, or reserved. Often a stale `--nodelist` copied from an old script.
- `BeginTime`, `JobHeldUser`, `JobHeldAdmin`: the job is not competing at all.

A job pending on `Resources` and a job pending on `AssocGrpGPURunMinutes` look
identical in `squeue` without that column, and they have nothing in common.

## Backfill, and the walltime you guessed

The scheduler runs two passes. The main pass walks jobs in priority order. The
backfill pass then looks for jobs further down that can fit in the gaps ahead of
the next high-priority start, *provided they finish before that start time*.

This is where the single most actionable habit comes from. Backfill can only
place your job if its declared walltime fits the gap, and Slurm has to trust the
number you wrote. Ask for 24 hours for a job that takes 40 minutes and you have
made yourself ineligible for almost every gap on the machine. Ask for 50 minutes
and you become the job that fits everywhere.

The number to write is not a guess:

```
sacct -u $USER -X --format=JobID,JobName%20,State,Elapsed,Timelimit,ReqTRES%40
```

Look at `Elapsed` against `Timelimit` across your recent work. If the ratio is
routinely below a fifth, your walltimes are the reason you wait, not fairshare
and not the admins.

The same logic applies to size. `job_size_factor` may be weighted in either
direction, but backfill is unambiguous: a job asking for two GPUs has vastly more
places it can fit than one asking for sixteen. If your code scales sublinearly
past four GPUs, asking for sixteen can easily be slower end to end once queue
time is counted. Wall-clock-to-result is the metric, not GPUs acquired.

## What this looks like from the other side

Operators reading this: most of the above is a documentation problem, and it is
cheap to fix. Publish the output of `scontrol show config | grep -i ^Priority`
with a paragraph of prose next to it. Put `sprio -j` and the reason-code list in
whatever the local getting-started page is. Nearly every "the scheduler is
broken" ticket is a user who had no way to see which factor they were losing to,
and no reason to believe the number meant anything.

The scheduler is one of the few parts of a cluster whose behaviour is fully
inspectable from an unprivileged shell. That is a gift. It only pays off if
people know the commands exist.

## The short version

Three commands, in order:

```
squeue -j <jobid> -o "%.18i %.9P %.8T %.10M %.11l %.6D %R"   # is it even priority?
sprio -j <jobid> -l                                          # which factor?
sshare -U -u $USER                                           # how deep is the hole?
```

And one habit: declare a walltime you would bet on, not one you cannot lose with.
Accurate walltimes are the closest thing to free priority that a scheduler
offers, and almost nobody claims it.

Those three commands produce three walls of text. Turning them into an answer is
tedious and highly site-specific, which makes it worth delegating:

**Prompt for your agent:**

```text
My job has been pending and I want to know which part of the scheduler's decision
I am losing to, without guessing at my site's policy.

Here is my scheduler's own output:
<paste the output of the three commands above>
<paste the resource request from your job script>

Working only from those outputs, tell me which priority component is dominating,
and whether the job is waiting on priority, on available resources, or on a
limit. Explain each factor using my site's configured weights as shown in the
output, not the defaults from the documentation, because the two are rarely the
same.

Then separate your answer into two lists: what is a policy decision my
administrators made, and what is a property of the scheduler itself. Those need
very different conversations. If part of the output has no explanation you can
support from what I gave you, say so rather than filling the gap.
```
