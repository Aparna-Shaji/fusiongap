# ADR-0006 — One repository for the library and the study

Status: proposed
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
If packaging from a mixed repository proves impossible at 4F, publish from a generated
subtree rather than splitting the history — history is what makes the dated
pre-registration worth anything, and it cannot be split without losing that.

## Reversal trigger
Looked for at 4F, and written as an **allowlist** rather than as a list of directories to
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
