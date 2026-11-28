# ADR-0005 — CI scope: what a GPU-less runner checks, and what it cannot

Status: accepted 2026-11-28 (stage 5B review)
Date: 2026-11-23
Owner stage: 04 → frozen at 05

## Context
REQ-Q4 requires CPU continuous integration on every commit and a GPU test log per commit,
so the boundary between what CI checks and what it cannot is a decision rather than a
default. The constraint that forces it: every result this project reports comes from one
GPU in one place, and risk R10 recorded from the start that CI has none. A $0 budget rules
out hosted GPU runners. The question 4G answered is therefore not whether CI is possible
but what is left for it to do once the GPU is taken out of it.

**On decision identifiers.** `D-nn` and `CR-nn` refer to entries in the project's state
file, which is working memory and is not part of this repository. They are secondary
references. Everything load-bearing here rests on the evidence paths named below.

## Decision
CI runs on GitHub-hosted, GPU-less runners against the public repository.

**In scope, on every push:**
1. Triton kernel correctness under `TRITON_INTERPRET=1`, which executes the kernel on the
   CPU. numpy is a hard dependency of this path, not a convenience.
2. Compile-only validation of every `.cu` for `sm_75` with `nvcc -c`, which needs no GPU
   and no driver.
3. The quality gates that need no GPU: lint, type check, the CPU test suite, secret
   scanning, lockfile consistency.

**Out of scope permanently, stated so that nothing silently pretends otherwise:**
4. **No GPU test runs in CI.** Numerical agreement against references, gradcheck, timing
   and telemetry are produced on this project's own GPU and committed as logs per commit
   (REQ-Q4). A green CI run never means a kernel is numerically correct on hardware.
5. **No performance measurement of any kind in CI.** A shared runner cannot produce a
   timing number this project is permitted to report.

**Deferred to stage 15**, which writes the real workflow: branch protection and merge
gating. Until CI exists on `main`, commits go directly to `main`, and the `spike/ci` branch
stays unmerged — it is a feasibility spike, not the start of that workflow.

Checkable: every CI job passes on a runner where `torch.cuda.is_available()` is False,
which 4G's green run demonstrates. A job that would fail without a GPU is therefore out of
scope by construction rather than by intention.

## Evidence
`results/env/4G_ci.md`; branch `spike/ci`; green run 45020691646 of 2026-11-22, with two
earlier red runs kept at 45019060150 and 45019801067, because the failures are the findings.

- Interpreter job: **51 s**. `pytest -v spikes/4G/test_triton_interpret.py` reported
  `3 passed in 1.27s`.
- Compile job: **4 m 11 s**, producing `copy_kernel.cu.o` at 467368 bytes and
  `fp64_kernels.cu.o` at 536008 bytes. **Verified by the object files, not by the green
  tick** — a job can be green because it compiled nothing.
- Cost: free on a public repository, about five minutes of wall time per push.
- The runner has no GPU, and neither check needs one.

Three failures on the way, each one a finding:
1. numpy absent produced a `ModuleNotFoundError` from `triton/runtime/interpreter.py`,
   raised while `triton.language` was importing, because `@jit` pulls the interpreter in at
   decoration time. numpy is a hard requirement of the only mechanism that tests a Triton
   kernel without a GPU.
2. `cuda-nvcc` alone produced `fatal error: cusparse.h`. `ATen/cuda/CUDAContextLight.h`
   wants cuSPARSE, cuBLAS and cuSOLVER headers for libraries this project never calls.
3. The CPU torch wheel produced `fatal error: c10/cuda/impl/cuda_cmake_macros.h`, a file
   generated during a CUDA build and absent from CPU wheels. A translation unit including
   `ATen/cuda` cannot compile against CPU torch at all.

**The workflow is also direct evidence for ADR-0001's torch row.** Both jobs install
`torch==2.15.0`; one from `download.pytorch.org/whl/cpu`, the other from `.../whl/cu132`.
The same version string resolves to two different builds and only the index distinguishes
them — the mechanism behind that row's requirement that the lock carry the index, shown
rather than argued.

## Alternatives rejected
| Alternative | Why it lost |
|---|---|
| A self-hosted runner on the builder's machine | It puts the project's only measurement GPU into a service that accepts jobs triggered from a public repository. Security aside, a CI job and a timing run would contend for the same card, and a contended run is not a measurement this project may report |
| Hosted GPU runners | Not free, and nothing in the definition of done requires a GPU in CI. The $0 constraint is a hard one |
| No CI, local hooks only | A local hook is skippable with `git commit --no-verify`, on exactly the commit where it matters. CI's value is that the author cannot skip it |
| Triton job only, dropping the nvcc compile | The CUDA arm is a never-cut item. A compile break would then surface at the next local build rather than at the push that caused it, with an unrelated diff in front of it |

## Consequences
- **Easier:** the Triton arm is checked for correctness on every push without a GPU, in
  under a minute, and CUDA code cannot be pushed in a state that does not compile.
- **Harder, with a number:** the compile job costs **4 m 11 s** against the interpreter
  job's 51 s, and nearly all of the difference is a roughly 2.5 GB CUDA torch wheel
  downloaded for header files, on every push, for the life of the project. This is the
  fourth independent argument for separating host code from device code at stage 15,
  beside 4E's 2.64 GiB build memory and 193 s build time: a `.cu` with no `ATen` include
  needs no torch wheel and none of the cuBLAS, cuSPARSE or cuSOLVER headers.
- **Harder:** a green CI run is weaker evidence than it looks. It says the Triton kernel is
  right under an interpreter and that the CUDA code compiles. It says nothing about
  numerical agreement on hardware and nothing about speed.
- **Must do:** stage 15 writes the real workflow and adds branch protection; the per-commit
  GPU log required by REQ-Q4 needs a committed location and a naming convention; and before
  CI is trusted it is shown to fail on a deliberately broken kernel, under the standing rule
  that no check is believed until it has failed on a defect it is supposed to catch.

## Fallback
If GitHub-hosted runners stop being free for this repository — the repository going private
is the likeliest cause — keep the interpreter job, which costs 51 s, and move the compile
check to a pre-push hook, recorded as a dated amendment. The order is deliberate: the cheap
check that protects the primary arm survives, and the expensive one moves off CI.

## Reversal trigger
Looked for at stage 15, and at every weekly review afterwards.
1. CI runs green against a deliberately broken kernel. Then the scope is wrong, not the
   implementation.
2. Wall time per push stays above about five minutes once the stage-15 host/device split has
   landed. Then the split did not deliver what findings 2 and 3 above predict.
3. Any CI job begins reporting a duration as a result, or any claim in the README, report or
   post traces to a CI run rather than to a GPU run record.
