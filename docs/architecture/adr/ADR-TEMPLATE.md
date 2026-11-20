# ADR-NNNN — <short title>

Status: proposed | accepted | superseded by ADR-NNNN
Date: YYYY-MM-DD
Owner stage: <stage that drafts it> → frozen at <stage>

Copy this file to `ADR-NNNN-<short-title>.md` and fill every section. Numbers are
allocated by the project plan and listed in `../TECH-STACK.md`; never invent one.
A section with nothing to say is written `None — because <reason>`, never deleted.

## Context
What forces this decision: the constraint from the brief, the charter or the risk
register that makes it a decision rather than a default. If no constraint forces it,
it is a default and belongs in a commit message, not here.

## Decision
What was chosen, specific enough that a command could check it.

## Evidence
The command, file or document that supports it, with path and date. `[UNKNOWN]` where
there is none yet, naming the stage that will supply it. An ADR with no evidence and no
owning stage is an opinion.

## Alternatives rejected
| Alternative | Why it lost |
|---|---|

One row per real alternative, each with a specific mechanism. "Worse", "less modern"
and "not standard" are not reasons.

## Consequences
What becomes easier, what becomes harder, and what we now have to do because of this.

## Fallback
What is done if the decision does not hold — written before it is needed, not after.

## Reversal trigger
The observation that would make us revisit this, and the stage at which we look for it.
