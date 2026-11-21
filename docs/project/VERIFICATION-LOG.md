# FusionGap · Verification log
Every fact the project relies on (F) and every platform item to check (V), with status and evidence. Rule: a claim that is not VERIFIED never appears in the README, report or blog; a claim that cannot be verified is removed, not softened. Statuses: VERIFIED · PARTIAL · UNVERIFIED · REMOVED.

## Facts
| ID | Claim | Status | Evidence · date | Settled at |
|---|---|---|---|---|
| F1 | Triton compiles and runs on this GPU (compute capability 7.5) | VERIFIED | torch 2.15.0+cu132 / Triton 3.9.0 · `results/env/4B1_triton_add.txt` · 2026-11-14 | 4B |
| F2 | This GTX 1650 (TU117) has no tensor cores | UNVERIFIED | deviceQuery reports CC 7.5, which tensor-core Turing parts also report, so it cannot settle this. No tensor-core statement anywhere until settled | 7A, 7C |
| F3 | Memory bandwidth (variant-dependent: ~128 or ~192 GB/s) | PARTIAL | deviceQuery: 6001 MHz, 128-bit bus → theoretical 192 GB/s, GDDR6-consistent · `results/env/deviceQuery.txt`; achieved bandwidth not yet measured | 7B |
| F4 | Peak fp32 ≈ 2.9 TFLOP/s | UNVERIFIED | Spec range 2.7–3.2 TFLOP/s from two reported max clocks (deviceQuery 1515 MHz, nvidia-smi 1785 MHz); only the measured ceiling will be used | 7C |
| F5 | Turing supports DP4A INT8 dot products | UNVERIFIED | Needed only if the quantization arm is admitted | 26D, 27D |
| F6 | Nsight Systems and Nsight Compute run under WSL2 on this GPU | UNVERIFIED | Not attempted as of 2026-11-21; stack cell 11 owns it and is untouched | 4C (cell 11) |
| F7 | `torch.compile` generates a fused Triton kernel on this GPU (checked for silu(a)·b) | VERIFIED | `results/env/4B2_output_code.log` · 2026-11-14; K1 and K3 patterns checked separately | 4B; 19B, 23D |
| F8 | Liger Kernel, Unsloth and cut-cross-entropy implement these kernels | UNVERIFIED | — | 9A |
| F9 | Kaggle: ~30 GPU-h/week, 12-h sessions, T4 and P100, 20 GB storage | PARTIAL | Account lists T4 ×2, no P100 · 2026-11-09; terms from Kaggle docs pending | 4H |
| F10 | Target-role posting is open | VERIFIED (open) | Checked 2026-11-12; details recorded privately outside the repo; re-checked weekly | 1D, weekly review |
| F11 | GitHub Actions free runners have no GPU | UNVERIFIED | — | 4G |
| F12 | The CUDA toolkit was installed from NVIDIA's distro-agnostic wsl-ubuntu repository, and CUDA 13.2's validated-distribution tables cover Ubuntu 24.04 and 22.04 for amd64, not 26.04, which first appears with CUDA 13.3 | VERIFIED | apt source `cuda-wsl-ubuntu-x86_64.list`; NVIDIA CUDA Installation Guide for Linux 13.2 §2.1 and §2.3 · `results/env/03_stack_precheck.txt` · 2026-11-19 | 03; disclosed in TECH-STACK and ENVIRONMENT (RV-27) |

## Platform verification items
| ID | Item | Status | Evidence · date | Settled at |
|---|---|---|---|---|
| V1 | `sm_75` in torch's arch list; Inductor emits Triton | VERIFIED | Capability (7, 5); arch list sm_75…sm_120 · `results/env/torch_env.txt`, `results/env/4B2_output_code.log` · 2026-11-14 | 4A, 4B |
| V2 | GPU clock, temperature, power and throttle reasons readable under WSL2 | VERIFIED | One WSL `nvidia-smi` CSV query returned SM clock, memory clock, temperature, power draw and throttle reasons with no `[N/A]` at 2.37 Hz across a 43.6 s load above 90 % utilisation; idle median 300 MHz against a loaded median 1005 MHz · `results/env/run2_4C_loaded.csv`, graded by `spikes/4C/grade_4c.py` exit 0 · 2026-11-21 | 4C (cell 10 PASS) |
| V3 | Clock locking permitted on this laptop GPU | UNVERIFIED (likely no) | Application clocks reported as deprecated; `nvidia-smi -lgc` not yet tried. 2026-11-21 adds: `power.limit` returns `[N/A]` under WSL2, the enforced ceiling is set from Windows and moved between 50 W and 30 W the same morning, and no Linux driver may be installed, so the answer is probably no for power as well as clocks | 4D |
| V4 | Windows GPU watchdog (TDR) setting | PARTIAL | deviceQuery: "Run time limit on kernels: Yes"; registry value not yet read; no driver reset occurred across two 45 s loads of ~70 ms matmul kernels · 2026-11-21 | 4D |
| V5 | Free VRAM at idle; which GPU drives the display | PARTIAL | 3295 of 4096 MiB free at one reading; the WSLg display server runs on the GTX 1650, so free VRAM varies; 4C allocated 192 MiB with no pressure · 2026-11-21 | 4D |
| V6 | PyPI name `fusiongap` free; TestPyPI accepts the artifact | UNVERIFIED | — | 4F |
| V7 | `TRITON_INTERPRET=1` works on a CPU-only CI runner | UNVERIFIED | — | 4G |
| V8 | Liger fused linear + cross-entropy runs on compute capability 7.5 | UNVERIFIED | — | 10A |
| V9 | End-to-end model licence is permissive; stock forward + backward fits 4 GB | UNVERIFIED | — | 11D |
| V10 | Pinned stack runs on Kaggle; Inductor on Pascal (SM_60) | PARTIAL | T4 ×2 offered, P100 not offered · 2026-11-09; smoke run pending | 4H, gate 05 |
| V11 | `tl.dot` in fp16 and fp32 compiles and is correct on compute capability 7.5 | UNVERIFIED | — | 4J |
| V12 | What max-autotune actually tunes on this GPU | UNVERIFIED | — | 10A |
| V13 | nvcc major.minor equals `torch.version.cuda`, the pairing `cpp_extension` checks | VERIFIED | nvcc release 13.2 V13.2.86 against torch 2.15.0+cu132 reporting CUDA 13.2 · `results/env/03_stack_precheck.txt` · 2026-11-19 | 03; re-checked at 4E |
| V14 | nvcc 13.2 accepts the installed host compiler and compiles for sm_75 | VERIFIED | `crt/host_config.h` line 135 errors above GCC major 15 and the installed gcc is 15.2.0, so there is zero headroom (RV-28); `g++-15` is present at /usr/bin/g++-15 and a trivial `-arch=sm_75` compile passed · `results/env/03_stack_precheck.txt` · 2026-11-19 | 03; re-checked at 4E |
| V15 | numpy, pandas and matplotlib publish wheels for Python 3.14 | VERIFIED | Resolver reports numpy 2.5.5, pandas 3.1.1, matplotlib 3.11.2, all cp314 · `results/env/03_stack_precheck.txt` · 2026-11-19 | 03; pinned at the 05 lock |
| V16 | The Clocks Event Reasons duration counters measure throttle duration | REMOVED | Disproved: they increment with wall-clock time regardless of throttling. Two differentials on 2026-11-21 — +778.6 s over 778 s elapsed, then +758.5 s over 759 s — with `SW Power Capping` and `SW Thermal Slowdown` bit-identical at all three readings · `results/env/run1_4C_power_before.txt`, `run1_4C_power_after.txt` · 2026-11-21 | 4C (RV-31) |
| V17 | Bits 0, 2 and 5 of `clocks_event_reasons.active` are Idle, SW Power Cap and SW Thermal Slowdown | VERIFIED | Named by the driver rather than inferred: `nvidia-smi -q -d PERFORMANCE` captured every 10 s across the 4C run shows `Idle : Active` before and after the load and `SW Power Cap` with `SW Thermal Slowdown` throughout it, matching `0x01` and `0x24` in the CSV · `results/env/run2_4C_perf_during.txt` · 2026-11-21 | 4C (RV-32) |
| V18 | The project environment runs pip 26.3 | VERIFIED | `.venv/bin/pip --version` · 2026-11-21. Bears on C4 finding F5: ADR-0001's claim that pip-tools 7.5.3 is pip-26 compatible is live configuration and still carries no source | 03; gate 05 |
