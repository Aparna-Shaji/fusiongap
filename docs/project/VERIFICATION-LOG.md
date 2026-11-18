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
| F6 | Nsight Systems and Nsight Compute run under WSL2 on this GPU | UNVERIFIED | — | 4C |
| F7 | `torch.compile` generates a fused Triton kernel on this GPU (checked for silu(a)·b) | VERIFIED | `results/env/4B2_output_code.log` · 2026-11-14; K1 and K3 patterns checked separately | 4B; 19B, 23D |
| F8 | Liger Kernel, Unsloth and cut-cross-entropy implement these kernels | UNVERIFIED | — | 9A |
| F9 | Kaggle: ~30 GPU-h/week, 12-h sessions, T4 and P100, 20 GB storage | PARTIAL | Account lists T4 ×2, no P100 · 2026-11-09; terms from Kaggle docs pending | 4H |
| F10 | Target-role posting is open | VERIFIED (open) | Checked 2026-11-12; details recorded privately outside the repo; re-checked weekly | 1D, weekly review |
| F11 | GitHub Actions free runners have no GPU | UNVERIFIED | — | 4G |

## Platform verification items
| ID | Item | Status | Evidence · date | Settled at |
|---|---|---|---|---|
| V1 | `sm_75` in torch's arch list; Inductor emits Triton | VERIFIED | Capability (7, 5); arch list sm_75…sm_120 · `results/env/torch_env.txt`, `results/env/4B2_output_code.log` · 2026-11-14 | 4A, 4B |
| V2 | GPU clock, temperature, power and throttle reasons readable under WSL2 | PARTIAL | Readable at idle via WSL `nvidia-smi` · 2026-11-12; under load pending | 4C |
| V3 | Clock locking permitted on this laptop GPU | UNVERIFIED (likely no) | Application clocks reported as deprecated; `nvidia-smi -lgc` not yet tried | 4C |
| V4 | Windows GPU watchdog (TDR) setting | PARTIAL | deviceQuery: "Run time limit on kernels: Yes"; registry value not yet read | 4D |
| V5 | Free VRAM at idle; which GPU drives the display | PARTIAL | 3295 of 4096 MiB free at one reading; the WSLg display server runs on the GTX 1650, so free VRAM varies | 4D |
| V6 | PyPI name `fusiongap` free; TestPyPI accepts the artifact | UNVERIFIED | — | 4F |
| V7 | `TRITON_INTERPRET=1` works on a CPU-only CI runner | UNVERIFIED | — | 4G |
| V8 | Liger fused linear + cross-entropy runs on compute capability 7.5 | UNVERIFIED | — | 10A |
| V9 | End-to-end model licence is permissive; stock forward + backward fits 4 GB | UNVERIFIED | — | 11D |
| V10 | Pinned stack runs on Kaggle; Inductor on Pascal (SM_60) | PARTIAL | T4 ×2 offered, P100 not offered · 2026-11-09; smoke run pending | 4H, gate 05 |
| V11 | `tl.dot` in fp16 and fp32 compiles and is correct on compute capability 7.5 | UNVERIFIED | — | 4J |
| V12 | What max-autotune actually tunes on this GPU | UNVERIFIED | — | 10A |