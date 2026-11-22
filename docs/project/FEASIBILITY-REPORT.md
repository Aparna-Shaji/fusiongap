# FEASIBILITY REPORT - stage 04 spikes

Every spike, its criterion, its result and where the evidence lives. Written
for a reader who trusts nothing in this document and wants to check each row.

Hardware: GTX 1650 4 GB, compute capability 7.5, under WSL2 on Windows 11.
Second device: Kaggle Tesla T4, also 7.5. Dates 2026-11-12 to 2026-11-22.

## Results

| Spike | Question | Result | Evidence |
|---|---|---|---|
| 4A | Does the toolchain come up: driver, nvcc, deviceQuery, torch on sm_75? | **PASS** 11-14 | `results/env/torch_env.txt`, `deviceQuery.txt` |
| 4B | Do Triton and Inductor work on sm_75 at all? | **PASS** 11-14 | `results/env/4B1_triton_add.txt`, `4B2_output_code.log` |
| 4C cell 10 | Can one source sample all five telemetry fields under load, at 2 Hz, with a clock response and liveness? | **PASS at run 2** 11-21 | `results/env/run2_4C_*`, graded by `spikes/4C/grade_4c.py` exit 0 |
| 4C cell 11 | Do nsys and ncu run here? | **ADVERSE PASS** 11-21: Nsight Systems traces and names the kernel; Nsight Compute is refused counters by `ERR_NVGPUCTRPERM`, matched to the Windows control-panel setting, observed restricted | `results/env/4C_cell11_profilers.txt` |
| 4D | What are the host limits, and can any clock or power setting be pinned? | **PASS**, and **V3 = NO**: four mechanisms, four refusals, state unchanged either side | `results/env/4D_host_limits.txt`, `4D_clock_control.txt` |
| 4E | Can a CUDA kernel be written, built and called here, and at what cost? | **PASS**, readiness band **GREEN** | `results/env/4E_readiness.txt` |
| 4F | Will a real index accept our package? | **ADVERSE PASS**: rejected, with the reason named by the server | `results/env/4F_packaging.md` |
| 4G | What can a GPU-less CI runner check? | **PASS**: Triton under the interpreter, and nvcc compile-only | `results/env/4G_ci.md`, branch `spike/ci` |
| 4H | Does any of this work on another machine? | **PASS** on a Kaggle T4, both its stack and ours | `results/env/kaggle-smoke/` |
| 4I | Does the fp64 correctness path work, and can gradcheck fail? | **PASS**: half, float and double exact; Triton fp64 exact; gradcheck accepted 2x and **rejected 3x** | `results/env/4I_fp64.txt` |
| 4J | Does `tl.dot` work on a card with no tensor cores? | **PASS** for fp16 and fp32 against fp64 references | `results/env/4J_tl_dot.txt` |

## Numbers this stage produced

| Measurement | Value | Where it matters |
|---|---|---|
| Usable VRAM after a CUDA context | **3.2 GiB** of 4.0 | gate 23's OOM boundary denominator |
| CUDA context cost | 641 MiB | the same |
| One `.cu` translation unit, `MAX_JOBS=1` | **193 s**, peak **2.64 GiB** | stages 18 and 22 iteration cost |
| Three templated kernels, three dtypes | 118 s, peak **2.79 GiB** | the trend, not the point value |
| Same compile on a Kaggle T4 | **63 s** | comparison only |
| Windows TDR timeout | **2 s**, default (keys absent) | no single kernel near that |
| Enforced power limit | **30 W** local, set from Windows and observed to move; 70 W on T4 | every measured ceiling |
| GPU-less CI | 51 s interpreter, 4 m 11 s compile, free | stage 15's CI design |

## Four findings that point the same way

Separating host code (`.cpp`, torch, ATen, pybind) from device code (`.cu`, raw
pointers) at stage 15 is supported by four independent measurements:

1. Build memory 2.64 GiB, rising to 2.79 GiB as kernels gain templates, against
   a 5 GB WSL allocation that itself had to be raised from 3.5 GiB.
2. Build time 193 s per translation unit, most of it nvcc parsing torch headers.
3. A GPU-less compile fails on `cusparse.h` - a library this project never calls.
4. The same compile fails on `cuda_cmake_macros.h` unless a 2.5 GB CUDA torch
   wheel is downloaded purely for headers, on every CI run.

## A platform habit worth writing down

Four times in this stage a tool reported success or silence for work it had not
done:

- `nvidia-smi -lms 500` delivered 1.92 Hz, not 2 Hz
- `nsys status -e` checks the CPU profiling environment and is silent on GPU
  counter permission, which is the thing that actually fails
- `nvidia-smi -ac` and `-lmc` exit 0 and print "All done" while setting nothing
- the Clocks Event Reasons duration counters increment with wall-clock time
  regardless of throttling (RV-31)

Rule for every stage after this one: **verify the effect, never the return code.**

## Checks that could not fail, and were caught by negative controls

Three times a check was found incapable of failing, each caught by deliberately
breaking the thing it was meant to catch:

- cell 10's original clock clause reduced to "> 0 MHz" (replaced by CR-10)
- compute-sanitizer reported 0 errors on a kernel writing out of bounds, because
  PyTorch's caching allocator hid the overrun (4E)
- 4J's first fp16 bar had five orders of magnitude of slack, because the
  reference used the already-rounded inputs

Rule: **no check is believed until it has been shown to fail on a defect it is
supposed to catch.**

## Not done at 4K, carried as a gate-04 condition

`ENVIRONMENT.md`, `SUPPORT-MATRIX.md`, and ADRs 0002 to 0005 drafted. These are
real work and are not gate-blocking: gate 04 asks whether every spike recorded a
result against its criterion with evidence, and the table above answers that.
The risk register and verification log updates for 11-21 and 11-22 are carried
with them.

## 4F repeated under ADR-0004 option (d) - the gate-04 remedy

Gate 04's NO-GO branch "TestPyPI rejects the artifact" fired, and its remedy is
to switch ADR-0004 and repeat 4F with the chosen option. Done, as a controlled
comparison: same server, same credentials, same twine invocation, two wheels
differing in one property.

| Wheel | What it contains | Result |
|---|---|---|
| `fusiongap_spike4f-0.0.1-cp314-cp314-linux_x86_64.whl` | a compiled CUDA extension | **400 rejected**: "has an unsupported platform tag 'linux_x86_64'" |
| `fusiongap_spiked-0.0.1-py3-none-any.whl` | Triton source only, nothing compiled | **accepted**, published at test.pypi.org/project/fusiongap-spiked/0.0.1/ |

**ADR-0004 = option (d)**: the published artefact is pure Python, Triton kernels
compiled by Triton on the user's machine at first call; the CUDA extension is an
optional, separately built component. This matches what the library is - the
Triton arm is primary, and the CUDA arm exists to be compared against it.

Build cost of the (d) wheel: seconds, 1780 bytes, because nothing is compiled.

## GATE 04 - PROCEED WITH CONDITION, 2026-11-22

Question: did every spike record pass or fail against its written criterion,
with evidence from the real GTX 1650 or a named runner? **Yes** - eleven rows
above, each with an evidence path.

NO-GO branches: Triton and Inductor work (4B, re-confirmed on a T4); a clock is
readable (4C cell 10); local nvcc 13.2 matches torch's CUDA 13.2; TestPyPI
rejected the artefact and the remedy is discharged above.

Adverse-but-valid GO branches taken and recorded: ncu blocked, so F6 = no and no
counter data appears anywhere in this project; the 4E readiness band is green.

Conditions, none gate-blocking, all owed before the stage-05 freeze:
  C1 ENVIRONMENT.md - 5D rebuilds the stack from it and from nothing else
  C2 SUPPORT-MATRIX.md
  C3 ADR-0002, 0003, 0004, 0005 drafted
  C4 risk register and verification log current to 2026-11-22
  C5 the seven C4 findings against ADR-0001 and ADR-0006
  CR-12 ruled at gate 05
