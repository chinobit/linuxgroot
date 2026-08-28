+++
title = "Toolbox"
template = "info-page.html"
path = "/toolbox"
description = "Copy-paste diagnostics for Slurm jobs and GPU nodes: why a job is pending, whether it is really using the GPU, and what to ask for next time."
insert_anchor_links = "left"

[extra]
toc = true
+++

Commands worth having in a scratch file. All of them are read-only and safe to
run as an unprivileged user, all of them work on stock Slurm with common
defaults, and none of them require an admin to be awake.

## Why is my job waiting?

Start with the reason code. It is frequently not what people assume:

```bash
squeue -j <jobid> -o "%.18i %.9P %.8T %.10M %.11l %.6D %R"
```

If that says `Priority`, decompose it before drawing conclusions:

```bash
sprio -j <jobid> -l
```

One column normally dominates. If it is `FAIRSHARE`, see how deep the hole is:

```bash
sshare -U -u $USER
```

And read the local policy rather than guessing at it, since the weights are
where every site's actual priorities live:

```bash
scontrol show config | grep -i ^Priority
```

The reasoning behind all four is in
[Why your job is still pending](@/blog/scheduler/why-your-job-is-pending/index.md).

## What did I actually ask for?

Full job record, including the resources that were granted rather than requested:

```bash
scontrol show job <jobid>
```

Recent history, which is the honest input to your next walltime estimate:

```bash
sacct -u $USER -X --starttime now-14days \
  --format=JobID,JobName%20,State,Elapsed,Timelimit,ReqTRES%45
```

If `Elapsed` is routinely a small fraction of `Timelimit`, that is the single
biggest thing standing between you and the backfill scheduler.

## Am I actually using the GPU?

The most common expensive mistake: a job that holds four GPUs and uses one, or
holds one and uses none because the framework silently fell back to CPU.

Attach to your own running job and look:

```bash
srun --jobid=<jobid> --overlap --pty nvidia-smi
```

Or watch utilisation over time rather than sampling once, which is what makes
the difference between "it looked busy" and "it is busy":

```bash
srun --jobid=<jobid> --overlap --pty \
  nvidia-smi --query-gpu=index,utilization.gpu,utilization.memory,memory.used,memory.total \
  --format=csv -l 5
```

A GPU sitting near zero utilisation while memory is allocated usually means the
bottleneck is data loading, not compute. More GPUs will not help that; more
workers or faster storage might.

After the job finishes, the summary view:

```bash
seff <jobid>
```

`seff` reports CPU efficiency and peak memory against what you reserved. It is
the fastest way to find out that a 64 GB request was really an 8 GB job.

## Right-sizing the next request

Peak memory actually used, per step:

```bash
sacct -j <jobid> --format=JobID,JobName%20,State,Elapsed,MaxRSS,MaxVMSize,ReqTRES%45,AllocTRES%45
```

Two habits follow from that output, and they are worth more than any flag:

Declare a walltime you would bet on. An overestimate does not protect you, it
excludes you from every backfill gap shorter than the number you wrote.

Ask for the smallest allocation that still finishes in reasonable time. If your
code scales sublinearly past a handful of GPUs, a smaller request often reaches a
result sooner end to end, because it starts sooner. Wall-clock-to-result is the
metric that matters, not devices acquired.

## A batch script worth copying

Deliberately minimal, with the parts people forget:

```bash
#!/bin/bash
#SBATCH --job-name=example
#SBATCH --output=logs/%x-%j.out      # %x job name, %j job id
#SBATCH --error=logs/%x-%j.err
#SBATCH --time=00:50:00              # honest estimate, not a safety blanket
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8            # match your dataloader workers
#SBATCH --mem=32G
#SBATCH --gpus=1
#SBATCH --mail-type=END,FAIL

set -euo pipefail                    # fail loudly, not silently
mkdir -p logs

echo "job $SLURM_JOB_ID on $(hostname) at $(date -Is)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

srun python train.py --epochs 10
```

Three details that repeatedly matter. `set -euo pipefail` turns a silent
mid-script failure into a job that fails where the problem is. Logging the node
and GPU model at the top makes an irreproducible result traceable weeks later.
And `--cpus-per-task` should reflect the dataloader workers you actually spawn,
since an under-provisioned input pipeline is the usual reason an expensive GPU
idles.

## Interactive work without wasting an allocation

A short interactive shell for debugging, rather than holding a large batch job
open while you think:

```bash
srun --time=00:30:00 --cpus-per-task=4 --mem=16G --gpus=1 --pty bash -l
```

Keep it short. Interactive allocations are the least backfillable thing on a
cluster, and a forgotten one is pure waste that somebody else is waiting on.
