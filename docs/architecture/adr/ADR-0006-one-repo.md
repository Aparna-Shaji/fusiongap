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
CR-01 adopted 2026-11-09 (STATE.md decision D-06). The repository has been public since
2026-11-14 under decision D-20.

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
Looked for at 4F: the wheel built from this repository contains any file from `bench/`,
`results/`, `spikes/` or `docs/study/`.
