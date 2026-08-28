+++
title = "Hivemind: notes an agent can actually use"
date = 2026-08-28
description = "A file-based knowledge base designed for LLM agents rather than adapted to them. Plain Markdown, retrieval instead of ingestion, and rituals implemented as scripts rather than requests."
insert_anchor_links = "left"

[taxonomies]
tags = ["ai-agents", "knowledge-management", "automation", "llm"]

[extra]
toc = true
+++

Every coding-agent session starts from nothing. It has your repository and
whatever you paste, and when the window fills or the session ends, everything the
agent worked out is gone. The next session rediscovers it, usually slightly
differently, and occasionally rediscovers a decision you had already rejected for
good reasons.

The obvious fix is to write things down. The non-obvious part is that a knowledge
base written for humans is a poor knowledge base for an agent, and the failure
mode is expensive rather than obvious: the agent reads too much, spends its
context on preamble, and still misses the one paragraph that mattered.

Hivemind is the working name for the structure I settled on. It is not a product
and there is nothing to install. It is a directory of Markdown files in git, plus
about six small scripts, and the design decisions are the interesting part.

## Plain files, deliberately

Everything is Markdown in a git repository. No database, no proprietary
container, no embedded application state. This sounds like a limitation and it is
the single most valuable property of the system.

It means any agent can read it. Sessions get run through different models and
different tools depending on what is at hand, and none of them need an adapter or
a plugin. It means the diff is the audit log: when a note changes, `git log`
shows what changed, when, and in which session. It means I can edit a note in a
text editor at three in the morning without the tooling being involved at all.
And it means the failure mode of the whole system is *a folder of readable
notes*, which is a good floor to have.

Agent-neutral is worth more than agent-optimal. Formats that only one tool can
read acquire a migration cost the moment that tool changes, and these tools
change every few months.

## Retrieval, not ingestion

The instinct with a knowledge base is to load it. Point the agent at the folder,
let it read what it needs. This does not survive contact with a real vault: a few
hundred notes is far more than a context window should ever hold, and most of it
is irrelevant to any given task.

So the rule is that nothing is read in bulk, ever. Lookups go through a local
embedding search that returns the top few matching notes by meaning rather than
keyword, and the agent reads only the sections it named. A question like *have we
hit this before?* costs a few hundred tokens instead of a hundred thousand.

{{ invertible_image(src="diagrams/hivemind-retrieval.svg", alt="A session question goes to an embedding search, which returns the top three notes; only the named sections are read into agent context. Decisions flow back out as new notes committed to git, which the search reads from.") }}

The second-order effect matters more than the saving. When retrieval is cheap and
narrow, notes get written to be retrievable: one idea per file, a description in
the frontmatter that says what the note is *for*, and a title that matches how
the question would be asked. Long transcripts and meeting-minute style notes are
useless here, and the system's cost structure makes that obvious rather than a
matter of taste.

## Rituals as scripts, not requests

Two things happen every session: a start and an end. Both used to be prompts,
which meant both were unreliable, because asking a model to remember a checklist
is asking it to do the one thing it is worst at.

Now both are scripts. Session start reports the host, which repository is
primary, whether the vault is clean or diverged, and which instruction layer
applies here. Session end validates the frontmatter across every note, commits,
and pushes. The agent runs a command and reads its output; it does not
introspect, and it cannot forget a step it never performs.

This is the same argument as any other automation, but it lands differently with
agents. A human who skips a checklist item usually notices. A model that skips
one produces a confident summary that says it did not.

## Precedence over duplication

A shared instruction layer is useful right up to the point where a specific
repository needs different behaviour. The tempting fix is to copy the shared
instructions into the repository and edit them, and the result is two files that
agree today and diverge silently forever.

Instead there is a resolution order. A repository-specific instruction layer wins
over the shared one, and the resolver *reports which layer won* at session start.
Nothing is copied. When a repository has nothing special to say, it says nothing
and inherits. When it does, the override is visible and local, and the shared
layer keeps being the single place that general rules are edited.

## Lessons captured where they will be found again

The most valuable notes in the vault are the ones written immediately after
something failed in a way that wasted an hour. Not the fix, which is usually
obvious in hindsight, but the *signal that was misread*.

These live as small notes, one lesson each, retrieved by situation rather than by
topic. A representative one: a command that exits zero has told you nothing about
whether it did anything, so find evidence of the work before reporting the work.
That single sentence has caught more real problems than any test I have written,
and it earns its place because it is retrieved at the moment it applies rather
than filed in a document nobody opens.

The related discipline is the decision record. When an option is evaluated and
rejected, the note records the reasoning *and a revisit trigger*: the specific
condition under which the answer would change. Six months later that is the
difference between a decision and a prejudice.

## What it is not

It is not a memory feature bolted onto a chat product, and it is not trying to
be. There is nothing conversational in it. It holds decisions, project state,
durable lessons and reference pointers, and it deliberately holds no credentials
of any kind: secrets live in the operating system's own mechanisms, and notes
refer to them by name and path only.

It is also not automatic. Notes are written because a session decided something
worth keeping, not because everything is logged. Capture that is too easy
produces a vault where retrieval stops working, which is the failure mode the
whole design exists to avoid.

## Whether this is worth building

Honestly: the scripts took an afternoon each and the structure took several
iterations to stop fighting. What made it worth it was not any single capability
but the compounding one. Sessions now start with an agent that knows the state of
the work, why the last three decisions went the way they did, and which mistakes
have already been paid for once.

That is a fairly ordinary description of a competent colleague returning from
holiday, which is roughly the standard worth aiming at.
