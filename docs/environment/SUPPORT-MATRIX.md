# SUPPORT-MATRIX — devices, baseline arms, and what has actually run

Owner stage: 04 · updated at every stage that runs an arm on a device · final form at 27D
Date: 2026-11-23

## What this file is, and is not
This is the repository's home for **device facts** and for the record of which baseline arm
has been shown to run on which device. Other documents point here rather than repeating the
numbers.

**No cell in this matrix is a performance claim.** Every status below means a correctness
check executed and passed, or that nothing has been run. Timing numbers do not exist yet:
the harness is built at stage 08, and until it exists this project has no number it is
permitted to report.

## The arms
From REQ-F6 and the charter:

| Arm | What it is |
|---|---|
| B1 | PyTorch eager, unfused |
| **B2** | **`torch.compile`** — the primary baseline (the whole study is measured against it) |
| B3 | Hand-written Triton |
| B4 | Hand-written CUDA C++ |
| B5 | Liger Kernel, an external reference, optional and only if it runs on compute capability 7.5 |

## Status vocabulary
- **RUNS** — executed on this device, a correctness check passed, evidence path given.
- **NOT ATTEMPTED** — no run exists. Not a claim that it would fail.
- **CUT BY AMENDMENT** — removed from scope by a dated amendment, recorded here rather than
  silently absent.
- **BLOCKED** — attempted and refused, with the mechanism named. No arm is in this state
  today; the status exists so that a future refusal has somewhere to go that is not silence.

## Devices
| | GTX 1650 (local) | Tesla T4 (Kaggle) | Tesla P100 |
|---|---|---|---|
| Compute capability | 7.5 | 7.5 | 6.0 |
| Tensor cores | none | present, unused by this project | none |
| Host | Windows 11 + WSL2, Ubuntu 26.04.1 | Kaggle notebook, no WSL | — |
| Usable VRAM | 3.2 GiB after a 641 MiB CUDA context | 14806 MiB free of 14911 | — |
| Enforced power limit | 30 W under load, set from Windows and not settable from inside WSL | 70 W | — |
| One `.cu` via `cpp_extension` | 193 s | 62.5 s and 67.0 s on two runs | — |
| Driver | KMD 621.01 / CUDA UMD 13.5 | 580.178.04 | — |
| Status | primary measurement device | portability check only (REQ-S11, T4 only) | **CUT BY AMENDMENT at gate 05** |

Evidence: `results/env/4K_environment_capture.txt`, `results/env/4K_power_under_load.txt`,
`results/env/kaggle-smoke/4H_t4_smoke.json` and its README, `results/env/4E_readiness.txt`.

## The matrix
| Arm | GTX 1650 (local) | Tesla T4 (Kaggle) | Tesla P100 |
|---|---|---|---|
| B1 eager | **RUNS** — torch 2.15.0+cu132, `cuda_available` true (`results/env/torch_env.txt`, 4A) | **RUNS** — both phases report `cuda_available` true (4H) | CUT BY AMENDMENT |
| **B2 torch.compile** | **RUNS** — Inductor emitted a Triton kernel and executed it (`results/env/4B2_output_code.log`, 4B.2) | **NOT ATTEMPTED** — 4H ran no `torch.compile` at all. See Gaps | CUT BY AMENDMENT |
| B3 Triton | **RUNS** — elementwise at n = 1, 1024, 98437 in fp32 and fp16 (4B.1); `tl.dot` fp16 and fp32 within two stated bars (4J); fp64 elementwise (4I) | **RUNS** — Triton add PASS under Kaggle's stock stack (triton 3.6.0) and under this project's pins (triton 3.9.0) (4H) | CUT BY AMENDMENT |
| B4 CUDA C++ | **RUNS** — templated kernel across half, float and double; `gradcheck` fp64 with its planted-wrong control correctly rejected (4E, 4I) | **RUNS** — templated CUDA square kernel and both gradchecks PASS, built in 62.5 s and 67.0 s (4H) | CUT BY AMENDMENT |
| B5 Liger | **NOT ATTEMPTED** | **NOT ATTEMPTED** | CUT BY AMENDMENT |

## Gaps this matrix exists to surface
1. **B2 has never run on the T4, and REQ-S11 needs it.** REQ-S11 is strongly expected and
   T4-only, and a portability check that omits the primary baseline checks the wrong thing.
   The 4H smoke covered B3 and B4 and both gradchecks; `torch.compile` was not exercised.
   Owner: the stage that runs REQ-S11.
2. **B5 has never been attempted anywhere.** The method is already decided — install Liger
   with `--no-deps` and diff `pip freeze` against the lock, so it cannot quietly move a pin —
   and stage 10A owns it. B5 is optional and sits in the cut order; it is listed here so that
   "optional" never becomes "forgotten".
3. **Nothing in this table has been measured.** Every cell is a correctness result. The first
   timing numbers can exist only after the harness passes its own gate at stage 08.

## The P100 is cut, not absent
Kaggle offers T4 x2 and TPU v5e-8 and no P100; CUDA 13 drops Pascal; and the pinned torch
wheel publishes nothing covering `sm_60`. The P100 half of REQ-S11 is therefore removed from
scope. Under the project's own rule a strongly-expected line ends DONE with evidence or CUT
by a dated amendment and is never relabelled, so **the amendment recording this cut is owed
at gate 05** and is not yet written. Until it is, this row is the only place the cut is
recorded, which is exactly the condition the rule exists to prevent.

## What this file becomes
At 27D it carries install-tested platforms alongside the Kaggle results, and every cell that
still reads NOT ATTEMPTED at that point is either filled or explained in the report's
limitations section.
