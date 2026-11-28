# ADR-0002 — Triton and Inductor on compute capability 7.5

Status: accepted 2026-11-28 (stage 5B review)
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

**None of the four bars carries a derivation, and that is now recorded rather than left
implicit.** The cited evidence `results/env/4J_tl_dot.txt` is seventeen lines and prints both
bars as bare numbers. The fp16 full-pipeline bar of `2.0e-02` admits a measured error of
`2.427e-04`, roughly 82x inside it, so it cannot fail on anything short of a gross defect -
which is the same objection the paragraph below raises about the bar it replaced.
`[VERIFY: how - derive all four bars at stage 17, from the unit in the last place of each dtype
and the reduction depth K = 64, before K1's and K3's tolerances inherit them under the two-bar
rule in Consequences.]` Until then these are working bars, not derived ones, and no tolerance
claim in this project rests on them.

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
  as this record — finding C4-F1's fix required both and only one was applied on 2026-11-23.

## Fallback
If a future torch moves its declared Triton requirement, the pair changes only by dated
amendment, and 4B and 4J are re-run on the new pair before any measurement is taken under it.
If the pinned pair stops running on this GPU, the charter's exception becomes available - but
only through a finite test. "If no pair runs on this GPU at all" quantifies over every
torch/Triton release that exists or will exist, and no experiment establishes it, so as
originally written the charter's one escape hatch for a never-cut item was gated on an
unopenable door (F71). The decidable form: the pinned pair fails spikes 4B and 4J on this GPU,
**and** the two adjacent torch releases either side of the pin, each re-resolved with its own
declared Triton, fail the same two spikes. Five pairs, a bounded afternoon, a reproducible
negative. If that test comes back all-fail the Triton arm is dropped through this record, by
amendment, with every failure reproduced and committed - and the re-charter at stage 01 must
address losing B2 at the same time, because the same failure takes both. The branch is dormant:
a pair runs (Decision part 1), and R1 is retired on two machines.

## Reversal trigger
Looked for at 5C, at 5D, and in every run's metadata thereafter. **Triggers 1 and 2 are
pre-run guards on the current environment; triggers 3 to 5 are read from a run's own recorded
metadata.** That distinction is load-bearing and was missing until 2026-11-28 (F70). A check
that reads the *current* environment cannot speak about a run taken weeks earlier: a historical
run compiled by a different Triton stays silent, and a later environment change fires against
runs that were valid when they were taken. Both directions fail, and they fail in opposite
ways.

1. **Pre-run guard, read before each measurement session.** `.venv/bin/python -m pip show
   triton` reports anything other than 3.9.0.
2. **Pre-run guard, read before each measurement session.** The installed torch's declared
   Triton requirement no longer names 3.9.
3. **From run metadata.** A run's own recorded Triton version is anything other than 3.9.0, or
   its recorded torch version is not the pinned pair's. This is the trigger that makes the
   Consequences claim above - that both arms share a compiler, so a difference between them is
   this project's finding rather than a version artefact - checkable after the fact. Without
   the version in run metadata that claim is unfalsifiable, which is how it stood until
   2026-11-28.
4. **From run metadata, for runs taken on or after 2026-11-23.** `TRITON_DEFAULT_FP_FUSION` is
   unset, or set to anything but 1. The scope matters twice (F29). Earlier runs - 4B and 4C
   among them - predate the pin, so an unset variable there is not evidence of drift. And in
   Triton 3.9.0 unset reads as ENABLED, arithmetically identical to 1, so an unset variable in
   a 3.9.0 run is a **recording** defect and not an arithmetic one. It becomes an arithmetic
   one at 3.10, which is the version bump this trigger exists to catch.
5. **From 5D onward, not before.** A Triton kernel passes under `TRITON_INTERPRET=1` and fails
   on the GPU, or the reverse. This cannot be looked for at 5C (F73): `TRITON_INTERPRET=1`
   imports numpy at `@jit` decoration time, and this record states twice that numpy is not
   installed. It installs at 5D (RV-36).
