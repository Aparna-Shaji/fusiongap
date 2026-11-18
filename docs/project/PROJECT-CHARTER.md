# FusionGap · Project Charter

Version 1.0 · baselined at gate 01 on 2026-11-18 · changed only by a dated entry in `docs/project/AMENDMENTS.md`
Sources: project brief v1 (Sep 2026) and plan Revision 1 (approved 2026-11-09), both kept outside this repository. This page carries everything a reader needs.

## 1 · Question
> `torch.compile` performs automatic operator fusion. For three common transformer operations, how much of the achievable speedup and memory reduction does it capture, how much remains available to hand-written Triton and CUDA, and can the residual gap be explained from first principles using a roofline model and profiler evidence?

The measurement is the project; the kernels are the instrument. FusionGap claims no novel kernel.

## 2 · Fixed inputs (decided before this charter; not re-scored at technology evaluation)
| Item | Decision |
|---|---|
| Kernels | K1 fused residual add + RMSNorm · K2 fused SiLU-multiply · K3 chunked fused linear + cross-entropy |
| Implementations | Every kernel in Triton **and** CUDA C++, forward **and** backward |
| Variants compared | B1 PyTorch eager, unfused · **B2 `torch.compile` (primary baseline)** · B3 Triton · B4 CUDA |
| Predictions | P1–P4 with formulas and decision rules, tagged `prereg-v1` on the public remote before any B2-vs-B3/B4 measurement exists |
| Plan | 33 stage gates (00–32), each with written GO / NO-GO criteria |

## 3 · Constraints
- Budget $0. Solo.
- Hardware: NVIDIA GeForce GTX 1650 4 GB (Turing, compute capability 7.5), laptop · Ryzen 5 4600H · 8 GB RAM shared by Windows and WSL2 · Ubuntu on WSL2.
- The laptop is the execution device for every kernel, test and timing run. Free cloud GPUs (Kaggle) are used only for the scripted portability check.
- Calendar: D1 = Mon 2026-11-09 · D56 = Sun 2027-01-03. Capacity: 8.5 h/day of project work, 6 days/week; Sundays rest (one exception: AM-03).
- Releases: v1.0.0 (core) directly after the MVP gate, by D46 (Thu 2026-12-24); extensions, blog and talk → v1.1.0 by D55 (Sat 2027-01-02) (AM-02). Current projection: AM-01.

## 4 · Scope
**CORE — never cut; v1.0.0 does not ship without every line**
1. Positioning paragraph citing ≥ 5 sources actually read, pushed before the first kernel file
2. `prereg-v1` tag before any comparative result
3. Measured bandwidth and compute ceilings, with the method published
4. Benchmark harness passes its validation oracles
5. K1 and K3, each in Triton and CUDA, forward and backward
6. Full correctness suite for every kernel, including `gradcheck` in fp64
7. Four-way comparison including B2 over a shape sweep: median + IQR over ≥ 5 repeats
8. Inductor-generated code committed and discussed
9. Roofline per kernel with the denominator named
10. End-to-end training step with an attribution table
11. K3 out-of-memory boundary curve and one demo configuration
12. Every cell where a baseline wins, reported with the number
13. Ridge-point portability limit stated in the abstract
14. P1–P4 all scored by the pre-registered rules
15. `pip install fusiongap` works on a clean machine
16. Environment metadata in every result file

Sole exception, by amendment only: the Triton arm may be dropped via ADR-0002 if no torch/Triton pair runs on this GPU (stop criterion S1; not triggered).

**STRONGLY EXPECTED — done, or cut by a dated amendment; never relabelled**
K2 in both languages · weight-only quantization arm with speed **and** quality numbers · Kaggle portability check · Nsight traces if the tools run under WSL2 · autotune search documented · `torch.compile` compile time reported as its own cost

**OPTIONAL — external reference and extra measurement**
B5 Liger Kernel fused linear + cross-entropy, if it runs on compute capability 7.5 · K3 backward strategy (b) measured alongside (a)

Cut order when behind, first → last: quantization · K3 strategy (b) · B5 · Nsight deep-dive · K2 CUDA · K2 Triton · Kaggle P100 · Kaggle T4 · talk and blog polish beyond outline. Extensions run in the reverse order.

**EXCLUDED**
A GEMM that beats cuBLAS · FlashAttention · compiler or IR construction (this project does compiler *analysis*) · multi-GPU or distributed kernels · sparsity · Rust · beating Liger Kernel or Unsloth · inference serving, batching, KV-cache · scaling-law experiments

## 5 · Definitions
- **First kernel** = the first file committed under `src/fusiongap/`. Spike code under `spikes/` is not library code and is never imported by it.
- **Baselined** = frozen; changed only by an AMENDMENTS entry stating what, why, evidence and Definition-of-Done impact.

## 6 · Minimum bar and stop criteria
**Minimum bar (target):** every CORE line on one commit, with every reported timing row valid under one fixed thermal and power regime. The bar does not depend on which way the results go: `torch.compile` capturing the whole gain, a false prediction, or K3 being slower than eager in time are findings, reported as measured.

**Stop and re-charter if:**
- **S1** `torch.compile` (Inductor) or Triton cannot run on compute capability 7.5 with any pinned torch release, so B2 cannot be measured as decided. 2026-11-15: not triggered (spike 4B passed for torch 2.15.0+cu132 / Triton 3.9.0); re-opened only by a version-pin change.
- **S2** Timing cannot be made valid: the harness oracles still fail after one fix cycle (gate 08), or no fixed laptop setting holds the GPU power limit at one value for a whole session (stages 4C, 7E). Until resolved, no comparative timing row is reported.
- **S3** The CORE list does not fit by D55 even after every cut in the cut order (gate 06 and every hard checkpoint). Duration or scope is re-chartered; no CORE line is relabelled complete.

**Not a stop:** prior art already publishing this comparison on consumer Turing. The thesis wording is narrowed by amendment and the study proceeds as an independent replication (gate 09).

## 7 · Assumptions and routing
| ID | Assumption | Tested at | Status 2026-11-15 |
|---|---|---|---|
| A1 | 51 h/week of project work is available | Weekly review actuals | Week 1: 16 h worked → AM-01 |
| A2 | A public GitHub repository is acceptable | 1E | VERIFIED 2026-11-14 |
| A3 | Kaggle GPU access on a verified account | 4H | T4 ×2 listed 2026-11-09; no session run yet |
| A4 | AC power and one fixed power setting for all timing | 4C, 7E | Always on AC; power limit read 30 W and 50 W on 2026-11-12 → OPEN (R21) |
| A5 | Nothing costs money | Every gate | HOLDS |

Facts F1–F11 and verification items V1–V12: `VERIFICATION-LOG.md`.
Open decisions and their owning stage: Triton on this GPU → 4B (done) · C++/CUDA readiness → 4E · K3 backward strategy → 20 · K3 chunk size, swept, never hard-coded → 20/23 · end-to-end model → 11D · Nsight under WSL2 → 4C · quantization in or out → gate 23 · INT4 storage-only vs arithmetic → 26D · PyTorch pin → 5A · Kaggle check in or out → gate 23.

## 8 · Outcome
Career outcome is tracked privately, outside this repository. Target-role posting status: `VERIFICATION-LOG.md`, F10.