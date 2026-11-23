# ADR-0002 — Triton and Inductor on compute capability 7.5

Status: proposed
Date: 2026-11-23
Owner stage: 04 → frozen at 05

## Context
This record exists because it is the one place the charter allows a never-cut item to be
cut: the Triton arm may be dropped, by amendment and through this record alone, if no
torch/Triton pair runs on this GPU. Risk R1 is rated CRIT for a reason that doubles the
stakes — Inductor's GPU backend emits Triton, so a Triton failure would remove not only the
hand-written Triton arm but also B2, `torch.compile`, which is this project's **primary**
baseline. One failure would take the arm and the comparison together and force a re-charter.
That is why the Triton smoke ran first, as spike 4B, before any infrastructure existed.

**On decision identifiers.** `D-nn` and `CR-nn` refer to entries in the project's state
file, which is working memory and is not part of this repository. They are secondary
references. Everything load-bearing here rests on the evidence paths named below.

## Decision
The exception does not apply. A pair runs, and it is pinned.

1. **The pair is torch 2.15.0+cu132 with Triton 3.9.0**, on compute capability 7.5.
2. **Triton is never chosen separately**, and that is two statements, both of which must
   hold. The pin is **3.9.0**, changeable only by a dated amendment. The invariant is that
   this version satisfies the Triton requirement the installed torch wheel declares —
   measured 2026-11-23 as `triton~=3.9.0; platform_system == "Linux" and python_version <
   "3.16"`. If the two ever diverge that is a stop and an amendment, never a silent follow.
3. **`TRITON_DEFAULT_FP_FUSION=1` is set explicitly** in every run and recorded in run
   metadata. Triton 3.9 warns that this default flips in 3.10, and an unset variable is a
   change of arithmetic that would arrive with a version bump and announce nothing (R22).
4. **Off-GPU testing is `TRITON_INTERPRET=1`**, which executes the kernel on the CPU and
   requires numpy.

## Evidence
**4B.1, 2026-11-14** — `results/env/4B1_triton_add.txt`. A Triton elementwise kernel at
n = 1, 1024 and 98437 in fp32, and at n = 98437 in fp16: all PASS, including the n = 1 and
non-power-of-two cases that exercise the tail guard.

**4B.2, 2026-11-14** — `results/env/4B2_output_code.log`. Inductor emitted a Triton kernel
on this device, which is what makes B2 a real baseline rather than an aspiration. It
specialised the kernel to the exact size it was given; that is a mechanism to discuss at
stage 19, not a defect.

**4J, 2026-11-22** — `results/env/4J_tl_dot.txt`. `tl.dot` on capability (7, 5), shapes
M = 128, N = 128, K = 64, tiles 64 x 64 x 32.

| dtype | accumulator only | bar | full pipeline | bar |
|---|---|---|---|---|
| fp16 | 2.664e-07 | 1.0e-05 | 2.427e-04 | 2.0e-02 |
| fp32 | 2.938e-07 | 1.0e-05 | 2.938e-07 | 1.0e-05 |

For fp32 the two are identical by construction, because nothing is cast.

**Two bars, because the first version of the first bar could not fail.** 4J's original fp16
check had five orders of magnitude of slack: the reference was built from the already-rounded
inputs, so input rounding cancelled from both sides and the comparison measured almost
nothing. Splitting it into an accumulator-only bar and a full-pipeline bar is the fix, and it
is why this table has four numbers rather than two.

**4I, 2026-11-22** — `results/env/4I_fp64.txt`. Triton elementwise on fp64 tensors PASS; a
templated CUDA kernel across half, float and double PASS; `gradcheck` in fp64 PASS **with its
planted-wrong backward correctly failing**. Six checks, zero failures. The negative control
matters more than the positives: without it the suite is a check that has never been shown to
fail on the defect it exists to catch.

**4G, 2026-11-22** — `results/env/4G_ci.md`. The same kernel under `TRITON_INTERPRET=1` on a
GPU-less runner: 3 passed in 1.27 s, and only with numpy installed.

**4H, 2026-11-22** — `results/env/kaggle-smoke/4H_t4_smoke.json`. The pair re-verified on a
Kaggle Tesla T4, also compute capability 7.5, under both Kaggle's own stack and this
project's pins. A second machine, which is why R1 is retired rather than merely unfired.

## Alternatives rejected
| Alternative | Why it lost |
|---|---|
| Choose a Triton version independently of torch | The two are coupled through Inductor: torch declares `triton~=3.9.0` and its GPU backend emits Triton for that version. An independently chosen Triton can satisfy pip and still leave B2 compiled by a different Triton than the hand-written arm — which would make a compiler difference look like this project's result |
| Pin an older torch/Triton pair believed friendlier to Turing | No evidence any other pair works better here, and four spikes plus a second machine saying this one works. Changing it discards every GPU measurement taken under it |
| Drop the Triton arm and ship CUDA only | The charter's named exception, available only by amendment and only if no pair runs. A pair runs. Taking it anyway would delete B2 along with the arm (R1), leaving the study without its primary baseline |
| Leave `TRITON_DEFAULT_FP_FUSION` at its default | Triton 3.9 warns the default flips in 3.10. Inside a measurement study, arithmetic that changes silently with a version bump is not a default, it is a defect waiting for a date |

## Consequences
- **Easier:** the hand-written Triton arm and the `torch.compile` baseline rest on one
  verified pair and share a compiler, so a difference between them is the project's finding
  rather than a version artefact.
- **Easier:** `tl.dot` works on SM_75 for fp16 and fp32 inputs within stated tolerances, so
  K3's per-chunk GEMMs can be written in Triton and ADR-0009's cuBLAS-only fallback need not
  be taken. This is a correctness result and says nothing about speed: this card has no
  tensor cores, so `tl.dot` runs on the ordinary pipelines.
- **Harder:** every Triton tolerance needs two bars, one for the accumulator and one for the
  full pipeline. A reference built from already-rounded inputs cancels input rounding from
  both sides and produces a bar that cannot fail.
- **Harder:** testing a Triton kernel without a GPU requires numpy, which is not installed in
  the project environment and is pinned at 5C.
- **Must do:** `tests/test_environment.py` at stage 16 asserts the pinned version, that the
  installed torch still declares a 3.9 requirement, and that `TRITON_DEFAULT_FP_FUSION=1` is
  set. TECH-STACK cell 3 is brought into line with ADR-0001's Triton row in the same commit
  as this record — finding F1's fix required both and only one was applied on 2026-11-23.

## Fallback
If a future torch moves its declared Triton requirement, the pair changes only by dated
amendment, and 4B and 4J are re-run on the new pair before any measurement is taken under it.
If no pair runs on this GPU at all, the charter's exception applies: the Triton arm is dropped
through this record, by amendment, with the failure reproduced and committed — and the
re-charter at stage 01 must address losing B2 at the same time, because the same failure takes
both.

## Reversal trigger
Looked for at 5C, at 5D, and in every run's metadata thereafter.
1. `.venv/bin/python -m pip show triton` reports anything other than 3.9.0.
2. The installed torch's declared Triton requirement no longer names 3.9.
3. `TRITON_DEFAULT_FP_FUSION` is unset, or set to anything but 1, in a recorded run.
4. A Triton kernel passes under `TRITON_INTERPRET=1` and fails on the GPU, or the reverse.
