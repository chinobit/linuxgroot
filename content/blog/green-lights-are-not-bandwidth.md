+++
title = "Green lights are not bandwidth"
date = 2026-08-29
description = "Nobody accepts a server without counting the RAM, and almost everybody accepts an interconnect on the strength of some green lights. What an acceptance test for a GPU fabric is actually for, and a prompt to build yours."
insert_anchor_links = "left"

[taxonomies]
tags = ["hpc", "gpu", "infiniband", "nccl"]

[extra]
social_media_card = "/social_cards/blog-green-lights-are-not-bandwidth.png"
toc = true
+++

You cannot tell a healthy 400G fabric from a badly degraded one by looking at it.
Both have green lights, both pass ping, and both let a job start. The difference
turns up six weeks after sign-off, as a distributed training run slower than the same
GPUs were inside a single node, reported by someone who reasonably assumes the
problem is their own code.

Nobody would accept a delivery of servers without counting the memory. Interconnects
get accepted on the strength of the lights being the right colour, and then spend
three years as the prime suspect in every performance conversation, because at no
point did anyone write down what good looked like.

## An acceptance test is a security control wearing a performance costume

The usual argument for benchmarking a new fabric is that you want to know if it is
fast. That is the less interesting half.

The valuable half is that you end up with a number. Six weeks later, when the
complaint arrives, the question is never "is this fast" - it is "was it always like
this", and without a baseline the honest answer is a shrug with a maintenance window
attached. A fabric nobody measured is not a fast fabric or a slow one. It is a
hypothesis.

Everything else on this page is the same argument in different clothes: assume
nothing about a layer you have not observed, and keep the evidence somewhere your
future self can find it.

## Start at the bottom, even though the bottom is boring

The temptation is to skip straight to a collective benchmark, because that looks
like the workload. It is also the measurement with the most possible explanations,
which makes a bad result the beginning of a long day rather than the end of a short
one.

Climb instead. Each rung isolates one layer, so a failure names its own cause and
everything below it is already proven.

{{ invertible_image(src="diagrams/fabric-validation-ladder.svg", alt="Four rungs: link and fabric state; NIC to NIC bandwidth; GPU memory over RDMA; then the collective benchmark. A failure at each rung points at a specific layer: negotiated rate and subnet manager, the fabric or NIC, missing GPUDirect RDMA, and topology or transport selection.") }}

The fabric layer comes first because it is nearly free and it catches the
embarrassing things: a link that quietly trained down to a lower rate and is still
reporting itself as up, a second subnet manager somebody left running on a switch, a
host that is not in the partition it should be in. That last one is the reason this
rung belongs to security as much as to performance. Partition membership is an
isolation boundary, and an accidental one is a bad way to discover that.

Then a single pair of network cards with no GPUs in the path, which tells you
whether the wire is delivering what the invoice claimed. Then the same test moving
GPU memory instead of host memory, which is the one that proves the network card can
read the GPU directly rather than staging every byte through the host.

{{ invertible_image(src="diagrams/gpudirect-rdma-path.svg", alt="Without GPUDirect RDMA, data goes from GPU memory to a host bounce buffer, then to the NIC, then to the wire. With GPUDirect RDMA, data goes from GPU memory directly to the NIC and out to the wire.") }}

That detour is worth eliminating for reasons beyond raw speed: it burns host memory
bandwidth you were counting on for the data loader, and it gets worse as every GPU
in the node does it simultaneously.

Only then is a collective benchmark worth the allocation. The tools for all of this
ship with the fabric stack, and the exact flags depend on your generation of
hardware more than on anything I could usefully tell you, so:

**Prompt for your agent:**

```text
You are helping me build an acceptance test for a multi-node GPU fabric.

My hardware: <GPUs per node and model>, <NICs per node and model>,
<interconnect generation>, <switch model>, <node count>.

Produce a runnable script with four stages, cheapest first: fabric and link
state, NIC to NIC bandwidth, GPU memory over RDMA, and a collective benchmark
sweep. For each stage give me the exact command for my hardware, the number that
indicates health on this specific topology along with how you derived it from
line rate, and what a failure at that stage rules in and rules out.

Constraints: cite upstream NVIDIA, NCCL, perftest or subnet manager
documentation for every flag you use, and mark clearly any figure that is a rule
of thumb rather than a documented value. Ask me whether the fabric is native
InfiniBand or RoCE before using any flag that differs between them - I have
watched people debug the benchmark for a day because they pasted a RoCE flag
onto an InfiniBand cluster. Do not include a setting you cannot cite.
```

## Two numbers come out, and one of them will mislead you

Collective benchmarks report both algorithm bandwidth and bus bandwidth, and the
distinction is the one piece of arithmetic here worth carrying around in your head.

Algorithm bandwidth is bytes divided by time. Bus bandwidth corrects for how many
times the algorithm actually has to move each byte across the bottleneck, which
makes it comparable against the hardware ceiling regardless of how many ranks you
ran with.

Which means algorithm bandwidth for a reduction falls as you add nodes even on a
flawless fabric. Sooner or later somebody compares a two-node run against an
eight-node run using the wrong column, and reports a regression that never happened.
Nothing was wrong except the reading.

For a rough sanity band, published validation runs on dense H100 nodes land at
roughly ninety percent of the combined line rate of their network cards. Treat that
as orientation, not as a target. Your real baseline is your own first clean run,
recorded alongside the conditions that produced it.

## Presence is not use

If I could keep one check from this entire exercise, it would be this one: confirm
in the logs which transport was actually selected.

A machine with InfiniBand cards can run its collectives over ordinary TCP. It
happens through a misdetected interface or an unset variable, and the failure mode
is exquisite: the job runs, the results are correct, nothing is logged as an error,
and the very expensive network you specified carries nothing at all. The only
symptom is a number that seems low, to someone who has no baseline to compare it
against.

The same caution scales upward. Switches that can perform in-network reduction do
not do so because they are capable of it; the feature needs the plugin, the
configuration and the entitlement to line up, and then it needs you to go and read
the log to confirm a collective actually used it. Capability is a purchase.
Behaviour is a measurement.

## Copied configuration is inherited debt

There is a genre of tuning advice that consists of a block of environment variables
with no explanation, and it propagates beautifully, because pasting it is free and
nothing complains.

The problem is that these variables get renamed, deprecated and re-defaulted between
releases, and an unrecognised one is not an error. It is silence. One example that
is still doing the rounds: a widely copied setting for controlling direct GPU
transfers uses a numeric value outside the documented range, for a variable that was
renamed several major versions ago. Configs carrying it have been achieving nothing,
quietly, for years.

I am not going to hand you a replacement block, because mine would be stale by the
time you read it and you would paste that instead. Derive it against the version you
actually run:

**Prompt for your agent:**

```text
My NCCL version is <the version line from your job's startup log>.

Using the documentation for that exact version, and citing it, tell me for every
variable in the environment block below: its documented accepted values, its
default, and whether it has been renamed, deprecated or superseded.

<paste the environment block from your job scripts>

Flag every entry that is deprecated, outside its documented range, or has no
effect given my transport. Then explain what each surviving setting actually
does, in one sentence each, so I can decide whether I meant it.

Most importantly: list the settings for which you could find no documentation at
all, and say so plainly rather than inferring what they probably do.
```

That final instruction is the one worth keeping in every prompt you write. The
failure you are guarding against is not an agent that says "I don't know". It is an
agent that produces a confident paragraph about a variable that has not existed
since 2021.

## Defaults are a starting point, not an answer

Collective libraries pick algorithms for the general case. Your job is a specific
case, and published sweeps regularly find the automatic choice beaten by a
double-digit margin inside the range of message sizes a particular workload actually
produces.

Do not copy anyone's winning settings, including mine. Copy the method: sweep the
sizes your workload really generates, change one variable per run, keep the curve
each time, and pin something only when you can point at the difference on your own
hardware. Then write down when to re-check it, because a tuning decision nobody
revisits eventually becomes a performance bug with a changelog entry.

**Prompt for your agent:**

```text
Design a tuning experiment for GPU collectives on my cluster, then help me read
the results.

Workload: <framework, model size, typical gradient bucket or message size>.
Topology: <GPUs per node, NICs per node, node count, interconnect>.

I want one variable changed per run, a bus bandwidth curve recorded for each, and
a stated hypothesis before each run. Tell me which variables are worth testing in
which order and why, how many repetitions before a difference is real rather than
noise, and how large a result would have to be to justify pinning a setting.

Be sceptical of my results. If a change looks like an improvement, tell me what
else could explain it and what control run would rule that out. Finish with what
I should re-measure after an upgrade to the library, the driver or the firmware.
```

## Write the number down

The output of an acceptance test is not a good afternoon. It is an artifact: the
results, the commands that produced them, the topology, and the versions of
everything involved, committed somewhere durable and re-run whenever any of those
change.

That artifact is the difference between an incident and a diff. It is also, in my
experience, the single cheapest thing in this entire process and the first thing
everybody skips.
