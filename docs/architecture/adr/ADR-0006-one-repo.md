# ADR-0006 — One repository for the library and the study

Status: accepted 2026-11-28 (stage 5B review)
Date: 2026-11-19
Owner stage: 03 → frozen at 05

## Context
The brief assumed two repositories: an installable library and a separate measurement
study. Plan-review finding R18 argued that this makes the study irreproducible from any
single clone, and change request CR-01 replaced it with one repository on 2026-11-09.
This record exists because the brief said otherwise and a reader will want to know why
the brief was overridden.

## Decision
One public repository, `fusiongap`. `src/fusiongap/` is the published package.
`bench/`, `results/`, `analysis/`, `tests/`, `spikes/` and `docs/` live in the same
repository and are not published to PyPI.

## Evidence
The override of the brief's two-repository design was adopted on 2026-11-09 with the plan
approval that opened this project. What a reader can check from this repository alone: the
history begins as one repository and has never been split (`git log --reverse`), and
`../TECH-STACK.md` row 14 records the same decision as FIXED BY DECISION with nothing able to
drift. The repository has been public since 2026-11-14 - a date this record asserts and cannot
itself evidence, because a commit date says nothing about a repository's visibility.

**On decision identifiers.** `CR-01`, `D-06` and `D-20` refer to entries in the project's
state file, which is working memory and is not part of this repository. They are secondary
references and a reader outside the project cannot follow them.

## Alternatives rejected
| Alternative | Why it lost |
|---|---|
| Two repositories: library and study | A measurement study whose instrument lives elsewhere cannot be reproduced from one clone. Every result would have to carry a pair of commit hashes, and the pre-registration tag would cover the protocol without covering the code that produced the numbers — which is the specific thing a pre-registration is supposed to prevent |
| One repository, kept private until release | Loses a dated public pre-registration, which is what makes predictions P1 to P4 credible rather than merely written down (D-20) |

## Consequences
- **Easier:** one clone reproduces the whole study, and the `prereg-v1` tag covers the
  instrument and the protocol together.
- **Harder:** packaging has to exclude `bench/`, `results/` and the study documents
  deliberately rather than by accident of repository boundaries.
- **Must do:** the packaging configuration at stage 15 names exactly what ships; ADR-0004
  settles the distribution model; the publish check at 29F and 31 confirms nothing
  private travelled with the artefact.

## Fallback
**Condition, re-scoped on 2026-11-28 (F51).** This was written against 4F, which ran on
2026-11-22 and is closed. A fallback whose condition can only be evaluated at a closed stage
can never be taken. It is read from **stage 15 onward at every wheel build, and again at 27C
and 31** - the stages that write the packaging configuration and build the published artefact.
The condition: a wheel built by stage 15's configuration contains any path outside the
allowlist in this record's reversal trigger, and no change to that configuration removes it.

**First action, not only an outcome (F50).** This previously named a destination and no step,
so under time pressure there was nothing to do first. The order is:
1. Record the offending paths from `unzip -l` on the built wheel, so the fallback is taken
   against evidence rather than against a suspicion.
2. Generate a publish-only subtree containing `src/fusiongap/` alone, via `git subtree split`
   into a throwaway branch that is never pushed.
3. Build the wheel from that subtree and check it against the same allowlist.
4. Record a dated amendment naming the paths from step 1 and the subtree commit.

**The history is never split.** History is what makes the dated pre-registration worth
anything, and it cannot be split without losing that - which is why the subtree is generated
per release and discarded, never maintained as a second line of development.

## Reversal trigger
Looked for at 4F (done, 2026-11-22), from stage 15 onward at every wheel build, and again at
27C and 31. Written as an **allowlist** rather than as a list of directories to
exclude: a denylist fails open, because it misses anything not yet invented - a future
`notebooks/`, `env/` or `scripts/` would ship in silence. The trigger fires when `unzip -l` on
the built wheel lists any path outside `fusiongap/`, `fusiongap.libs/` and
`fusiongap-<version>.dist-info/`.

Three details make that executable rather than merely strict. A valid wheel always contains its
`fusiongap-<version>.dist-info/` directory - METADATA, WHEEL, RECORD and any licence file - so
an allowlist of `fusiongap/` alone would fire on every correct build, and a criterion that
always fires is as useless as one that never does. Inside the wheel the package appears as
`fusiongap/` and not `src/fusiongap/`, because the src layout strips `src` at build time, so a
check written against the repository path would never match. And if ADR-0004 ever takes the
manylinux route, `auditwheel` adds `fusiongap.libs/` at the wheel root, which is why it is
allowed explicitly.
