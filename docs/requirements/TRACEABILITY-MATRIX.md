# FusionGap · Traceability matrix v0

**Status: v0, DRAFT. Gate 02 returned NO-GO on 2026-11-18; corrections applied, re-review pending.** Identifiers per decision D-25: brief section 20's core list as
DoD-1 to DoD-17, its strongly-expected list as SE-1 to SE-6. Design and test columns are deliberately
empty and are filled at stage 14 (control C4); an entry there before the design exists would claim
coverage that does not.

## View 1 · By requirement

| REQ | Tier | Closes | Owner stage(s) | Design (st. 14) | Test (st. 16) | Status |
|---|---|---|---|---|---|---|
| REQ-F1 K1 fused residual-add + RMSNorm | CORE | DoD-5 | 17, 18, gate 19 | | | not started |
| REQ-F2 K3 chunked linear + cross-entropy | CORE | DoD-6 | 20, 21, 22, gate 23 | | | not started |
| REQ-F3 K2 fused SiLU-multiply | STRONGLY EXPECTED | SE-1 | 26B | | | not started |
| REQ-F4 Weight-only quantization | STRONGLY EXPECTED | SE-2 | 26D, in/out at gate 23 | | | not started |
| REQ-F5 Installable on a clean machine | CORE | DoD-16 | 4F, 27, 31 | | | not started |
| REQ-F6 Four-way benchmark harness | CORE | DoD-8; evidence for DoD-4 | 08, 10B, 13A | | | not started |
| REQ-F7 End-to-end step, three configurations | CORE | DoD-11 | 11D, 24, gate 25 | | | not started |
| REQ-S1 Measured hardware ceilings | CORE | DoD-3 | 07 | | | not started |
| REQ-S2 Harness validation oracles | CORE | DoD-4 | 08, 8D | | | not started |
| REQ-S3 Measurement hygiene per cell | CORE | DoD-8 | 08, 10B, 13A | | | not started |
| REQ-S4 Inductor-generated code as evidence | CORE | DoD-9 | 19B, 23D, 26B | | | not started |
| REQ-S5 Roofline per kernel | CORE | DoD-10 | 19C, 23E | | | not started |
| REQ-S6 End-to-end attribution | CORE | DoD-11 | 24, gate 25 | | | not started |
| REQ-S7 K3 memory boundary and demo | CORE | DoD-12 | 23C, 29 | | | not started |
| REQ-S8 Every loss reported | CORE | DoD-13 | 25A, 29 | | | not started |
| REQ-S9 Predictions scored by pre-registered rules | CORE | DoD-15 | 10, 25A | | | not started |
| REQ-S10 Ridge-point limitation in the abstract | CORE | DoD-14 | 28, 29 | | | not started |
| REQ-S11 Portability check, T4 only | STRONGLY EXPECTED | SE-3 (T4 half) | 26A | | | not started |
| REQ-S12 Prior-art positioning | CORE | DoD-1 | 09 | | | not started |
| REQ-S13 Profiler traces, or a recorded failure | STRONGLY EXPECTED | SE-4 | 4C, 26C | | | not started |
| REQ-S14 Autotuning search documented | STRONGLY EXPECTED | SE-5 | 10A, 17, 18, 21, 22 | | | not started |
| REQ-S15 Compilation time as its own cost | STRONGLY EXPECTED | SE-6 | 08, 10B, 28 | | | not started |
| REQ-Q1 Correctness suite before any timing | CORE | DoD-7 | 16, 17, 18, 21, 22, 26B | | | not started |
| REQ-Q2 Determinism or measured variance | CORE | DoD-7 | 16, 17, 18, 21, 22 | | | not started |
| REQ-Q3 Reproducibility contract | CORE | DoD-17 | 05, 13A, 27, 29, 31 | | | not started |
| REQ-Q4 Continuous integration on every push | CORE | DoD-17 | 15, 16 | | | not started |
| REQ-Q5 Environment metadata in every result | CORE | DoD-17 | 05, 08, 13A | | | not started |
| REQ-Q6 Pre-registration integrity | CORE | DoD-2 | 10, 25A, 29 | | | not started |

## View 2 · By definition-of-done line — the gate-02 view

| DoD | Core line | Covered by | Owner stage(s) |
|---|---|---|---|
| DoD-1 | Positioning paragraph, 5+ sources, before the first kernel | REQ-S12 | 09 |
| DoD-2 | Pre-registered predictions committed and dated before results | REQ-Q6 | 10, 25A |
| DoD-3 | Measured peak bandwidth and FLOP/s, method published | REQ-S1 | 07 |
| DoD-4 | Harness self-validation: sync versus no-sync demonstrated | REQ-S2; evidence REQ-F6 | 08 |
| DoD-5 | K1 in both languages, forward and backward | REQ-F1 | 17, 18 |
| DoD-6 | K3 in both languages, forward and backward | REQ-F2 | 20, 21, 22 |
| DoD-7 | Full correctness suite, gradcheck fp64, edge cases, ragged shapes, Triton = CUDA | REQ-Q1, REQ-Q2 | 16 |
| DoD-8 | Four-way benchmark over a shape sweep, median + IQR, 5+ repeats | REQ-F6, REQ-S3 | 08, 10B |
| DoD-9 | Inductor-generated code inspected, committed, discussed | REQ-S4 | 19B, 23D |
| DoD-10 | Roofline per kernel, denominator stated | REQ-S5 | 19C, 23E |
| DoD-11 | End-to-end step measurement with attribution table | REQ-F7, REQ-S6 | 24 |
| DoD-12 | K3 out-of-memory demo configuration | REQ-S7 | 23C |
| DoD-13 | Every configuration where a baseline won, with the number | REQ-S8 | 25A |
| DoD-14 | Ridge-point portability limitation in the abstract | REQ-S10 | 28 |
| DoD-15 | All four predictions scored | REQ-S9 | 25A |
| DoD-16 | Install works on a clean machine | REQ-F5 | 4F, 27 |
| DoD-17 | Pinned versions and environment metadata in every result file | REQ-Q3, REQ-Q4, REQ-Q5 | 05, 13A, 15 |
| SE-1 | K2 both languages, scoped as activation fusion | REQ-F3 | 26B |
| SE-2 | Quantization arm, speed and quality | REQ-F4 | 26D |
| SE-3 | Kaggle portability, T4 and P100, ranking stability | REQ-S11 covers the T4 half; the P100 half is CUT, recorded by amendment at gate 05 (CR-04) | 26A |
| SE-4 | Nsight traces committed, if the tooling runs | REQ-S13 (conditional on F6) | 4C, 26C |
| SE-5 | Autotuning configuration search documented | REQ-S14 | 10A |
| SE-6 | torch.compile compile time reported as its own cost | REQ-S15 | 08, 10B, 28 |

## Optional items — no definition-of-done line, so no requirement

| Item | Where it lives | Notes |
|---|---|---|
| B5 Liger Kernel reference | REQ-F6 optional clause; 10A install, 23A comparison | Runs only if it supports compute capability 7.5. Install with no dependencies and diff against the lock (RV-11) |
| K3 backward strategy (b) measured alongside (a) | ADR-0010; 20B decision, 26E measurement | Primary strategy is unchanged either way |

## Open coverage notes

- Gate 02 returned NO-GO on its first run, 2026-11-18. This is the corrected matrix: 28 requirements
  cover 17 core lines and 6 strongly-expected lines, each with a criterion and a verification method.
- DoD-1 had no covering requirement until REQ-S12 was added at 2B. DoD-2 was covered only as a clause
  inside REQ-Q3 and now has REQ-Q6, because it states a temporal-integrity condition and carries its
  own hard checkpoint at gate 10. SE-4, SE-5 and SE-6 had owner stages but no criterion, so stage 30
  could not have adjudicated DONE; they now have REQ-S13, REQ-S14 and REQ-S15, each written with a
  real criterion rather than relabelled from the earlier note.
- Temporal checks use ancestry (`git merge-base --is-ancestor`), never date comparison: commit-date
  filtering misbehaved in this repository on 2026-11-18 (friction log), and ancestry is a structural
  fact of the history rather than a parsed timestamp.
- Design and test columns stay empty until stage 14 (control C4).
