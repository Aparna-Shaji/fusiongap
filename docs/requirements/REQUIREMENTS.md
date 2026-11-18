# FusionGap · Requirements and acceptance criteria

**Status: DRAFT — sections 2B, 2C, 2D, 2E are not written. Gate 02 has NOT run. Not baselined.**
Authority: project brief v1 section 20 (definition of done) and section 14 (non-goals), as amended by
`docs/project/AMENDMENTS.md`. Where the charter summarises a brief line, the brief's fuller wording
is used for the criterion. Baselined only when gate 02 passes.

## 0 · Definition-of-done identifiers

Canonical numbering is the brief's section 20 core list, DoD-1 to DoD-17, and its strongly-expected
list, SE-1 to SE-6. The charter's CORE list merges brief lines 5 and 6 (K1 and K3) into its line 5;
this document keeps them separate so each kernel receives its own PASS or FAIL verdict at stage 30.
No charter amendment is needed: the charter's text already covers both kernels.

| ID | Core line (brief section 20) |
|---|---|
| DoD-1 | Positioning paragraph, 5 or more sources actually read and cited, committed before the first kernel file |
| DoD-2 | Pre-registered predictions committed, dated before the results commit |
| DoD-3 | Measured peak bandwidth and peak FLOP/s for this device, with the measurement method published |
| DoD-4 | Harness self-validation: the sync-versus-no-sync timing difference demonstrated |
| DoD-5 | K1 (RMSNorm + residual) in both Triton and CUDA, forward and backward |
| DoD-6 | K3 (chunked linear + cross-entropy) in both Triton and CUDA, forward and backward |
| DoD-7 | Full correctness suite passing for every kernel: forward, gradcheck in fp64, edge cases, ragged shapes, Triton-versus-CUDA agreement |
| DoD-8 | Four-way benchmark (eager, torch.compile, Triton, CUDA) across a shape sweep, median + IQR over 5 or more repeats |
| DoD-9 | Inductor's generated code inspected, committed and discussed |
| DoD-10 | Roofline analysis per kernel: arithmetic intensity, ridge point, achieved bandwidth as a percentage of measured peak, denominator stated |
| DoD-11 | End-to-end training-step measurement with the attribution table |
| DoD-12 | The K3 out-of-memory demo: the exact configuration where the reference fails on 4 GB and ours does not |
| DoD-13 | Every configuration where a baseline beat us, reported with the number |
| DoD-14 | Ridge-point portability limitation stated in the abstract |
| DoD-15 | All four predictions scored, including the ones we got wrong |
| DoD-16 | `pip install fusiongap` works on a clean machine |
| DoD-17 | Pinned versions and full environment metadata in every result file |

| ID | Strongly expected (done, or cut by dated amendment; never relabelled) |
|---|---|
| SE-1 | K2 fused SiLU-multiply, both languages, scoped honestly as activation fusion |
| SE-2 | Quantization arm with both speed and quality numbers |
| SE-3 | Kaggle portability check on T4 and P100, with ranking stability reported |
| SE-4 | Nsight Systems and Nsight Compute traces committed, if the tooling runs |
| SE-5 | Autotuning configuration search documented |
| SE-6 | torch.compile compilation time reported as its own cost |

Verification methods used throughout: **test** (run it, compare against an expected result) ·
**inspection** (examine the artefact) · **demonstration** (operate it and observe) ·
**analysis** (derive it).

## 2A · Functional requirements

### REQ-F1 · Fused residual-add + RMSNorm (K1)
**Statement:** The library provides a fused residual-add + RMSNorm operator implemented twice, once in
Triton and once in CUDA C++, each supporting forward and backward and exposed as one autograd-aware
PyTorch operator. The sum of squares accumulates in fp32 even when inputs are fp16.
**Criterion:** for each implementation, forward output and the gradients with respect to input,
residual and weight match the unfused PyTorch reference within the per-dtype tolerances fixed in
REQ-Q1, and `torch.autograd.gradcheck` passes in fp64 on small shapes.
**Method:** test · **Owner stage:** 17 (Triton), 18 (CUDA), gate 19 · **Closes:** DoD-5
**Tier:** CORE

### REQ-F2 · Chunked fused linear + cross-entropy (K3)
**Statement:** The library provides a chunked fused linear + cross-entropy operator in Triton and in
CUDA C++, forward and backward, which never materialises the full logits tensor or its gradient.
Peak memory scales with chunk size times vocabulary, not with batch times sequence times vocabulary.
**Criterion:** forward loss and the gradients with respect to hidden states and vocabulary weights
match the reference within REQ-Q1 tolerances; gradcheck passes in fp64; measured peak memory grows
with chunk size and not with total rows across the swept grid; a chunk size that does not evenly
divide the row count is covered.
**Method:** test, plus analysis for the memory-scaling claim · **Owner stage:** 20 (strategy),
21 (Triton), 22 (CUDA), gate 23 · **Closes:** DoD-6
**Tier:** CORE

### REQ-F3 · Fused SiLU-multiply (K2)
**Statement:** The library provides a fused SiLU-multiply operator in Triton and in CUDA C++, forward
and backward. The surrounding feed-forward matrix multiplies remain cuBLAS and are not reimplemented;
the operator is named and reported as activation fusion, not as a fused SwiGLU.
**Criterion:** as REQ-F1, against the unfused `silu(a) * b` reference; the report and README use the
activation-fusion wording.
**Method:** test, plus inspection of the naming in the report · **Owner stage:** 26B · **Closes:** SE-1
**Tier:** STRONGLY EXPECTED. Note: the plan-file upload labels this OPTIONAL; the charter and finding
RV-15 place K2 in the strongly-expected tier, and the charter governs.

### REQ-F4 · Weight-only quantization on the K2 path
**Statement:** The library provides weight-only quantization for the decode-shaped, small-M
dequantise-fused GEMV on the K2 path: INT8 per-channel weights dequantised to fp16 in registers, and
INT4 weight storage unpacked and dequantised in-kernel. Activations stay fp16, DP4A is not used, and
the INT4 result is reported as a memory-traffic win rather than an arithmetic one.
**Criterion:** speed and quality reported together — memory saved, bytes saved, achieved percentage of
the measured bandwidth ceiling, and either a perplexity delta on held-out text with a permissively
licensed checkpoint, or output divergence against the fp16 baseline labelled as such.
**Method:** test for correctness, analysis for the traffic claim, inspection for the quality number ·
**Owner stage:** 26D, in-or-out decided at gate 23 (decision D-08) · **Closes:** SE-2
**Tier:** STRONGLY EXPECTED. Note: the plan-file upload labels this OPTIONAL; the charter governs.

### REQ-F5 · Installable on a clean machine
**Statement:** `pip install fusiongap` succeeds on a machine that has a CUDA GPU and no prior
fusiongap installation, and the documented smoke example then runs to completion.
**Criterion:** performed on a freshly built environment, not the development machine, with the
transcript committed; the packaging approach is whichever ADR-0004 option survives the stage-4F test,
since bare `linux_x86_64` wheels are rejected by PyPI (finding RV-12).
**Method:** demonstration · **Owner stage:** 4F (TestPyPI), 27 (fresh rebuild), 31 (release) ·
**Closes:** DoD-16
**Tier:** CORE. Owned by the measurement-validity role as an evidence-bound claim (decision D-10).

### REQ-F6 · Four-way benchmark harness
**Statement:** The harness measures variants B1 (eager), B2 (torch.compile), B3 (Triton) and B4 (CUDA)
on identical inputs, dtypes, shapes and memory layout, over the shape sweep fixed in PROTOCOL, and
optionally B5 (Liger) as an external reference. It reports median and inter-quartile range over at
least five repeats, discards warm-up iterations, shuffles variant order, cools down between groups,
and records clocks, temperature and power limit per run.
**Criterion:** the harness passes validation oracles O1 to O7, including the sync-versus-no-sync
difference (O1) and the sampler-on-versus-off agreement (O7); each result row asserts that the
compiled path actually executed, so an Inductor recompilation or eager fallback cannot be recorded as
B2 (finding RV-20); every row carries the metadata required by REQ-Q5.
**Method:** test (the oracles), inspection (the output schema) · **Owner stage:** 08 (harness),
10B (PROTOCOL), 13A (schema) · **Closes:** DoD-8, and supplies the evidence for DoD-4
**Tier:** CORE

### REQ-F7 · End-to-end training step in three configurations
**Statement:** A compact Llama-style decoder training step runs in three configurations — stock
PyTorch modules, torch.compile, and fusiongap kernels — on a model meeting the 2D criteria, reporting
step time, peak memory and tokens per second for each.
**Criterion:** all three configurations complete at the chosen configuration within 4 GB; the
attribution table states what fraction of baseline step time each kernel occupied before substitution,
and the end-to-end result is reported even where the gain is small or negative.
**Method:** test for the measurements, analysis for the attribution · **Owner stage:** 11D (model
choice), 24 (end-to-end), gate 25 · **Closes:** DoD-11
**Tier:** CORE

## 2C · Quality requirements

Written before 2B because REQ-Q1 fixes the per-dtype tolerances that REQ-F1, REQ-F2, REQ-F3 and
REQ-F4 all refer to. Plan order is restored at 2F, before gate 02.

### REQ-Q1 · Correctness suite, passing before any timing run
**Statement:** Every kernel passes the brief section 8 suite before it is benchmarked: forward
comparison against the PyTorch reference across shapes and dtypes with rtol and atol stated per dtype
and justified; `torch.autograd.gradcheck` in fp64 on small shapes; analytic gradients compared against
the reference's on realistic shapes in the working dtype; the section 8 edge cases (all-zero input,
fp16 overflow range, underflow and denormals, non-contiguous inputs, shapes that are not a multiple of
the block size, batch size 1, hidden dim 1, sequence length 1, and for K3 a chunk size that does not
evenly divide the row count); and Triton-versus-CUDA agreement within the stated tolerance.
**Criterion:** the suite exists as tests and runs green, and the tolerance values are recorded together
with the reasoning that produced them. A red gradcheck blocks benchmarking outright — the hard gate.
A disagreement between the Triton and CUDA implementations means one of them is wrong and is resolved
before anything else proceeds.
**Method:** test, plus inspection of the recorded tolerance justification · **Owner stage:** 16 (suite
built and mutation-tested), 17 and 18 (K1), 21 and 22 (K3), 26B (K2) · **Closes:** DoD-7
**Tier:** CORE
**Note — deliberately not fixed here:** the numeric tolerances are derived and recorded at stage 16,
before the first kernel is timed. This requirement demands that they be stated and justified, not that
they take any particular value. Choosing numbers before a measured error distribution exists invites
the failure mode of widening them later until a test passes, which destroys the gate.

### REQ-Q2 · Determinism verified, or variance measured and reported
**Statement:** For each kernel, determinism is either verified — same input, same kernel, same result
across runs — or, where a reduction uses atomics and is not deterministic, the non-determinism is
declared and the observed run-to-run variance is reported.
**Criterion:** a test asserts repeatability wherever determinism is claimed; where it is not claimed,
the report carries the measured spread and names the reduction responsible. Silence on this point is
not acceptable in either direction.
**Method:** test, plus inspection of the report statement · **Owner stage:** 16, then per kernel at
17, 18, 21, 22 · **Closes:** DoD-7 (determinism clause)
**Tier:** CORE

### REQ-Q3 · Reproducibility contract
**Statement:** The repository satisfies the brief section 16 contract: install on a clean machine;
a REPRODUCE document giving exact commands per figure with expected runtime and expected hardware;
pinned PyTorch, Triton, CUDA toolkit and driver versions; every result file carrying git SHA, device
name, compute capability, driver version, clock and temperature; one command regenerating every plot
from raw CSV; raw benchmark data committed including discarded and throttled runs; the
Inductor-generated code committed as evidence; at least one profiler trace per kernel; the
pre-registered predictions committed before the results commit; a known-limitations section; and every
configuration where a baseline won reported with its number.
**Criterion:** each clause maps to a named artefact in the repository, checked clause by clause at
stage 27 (rebuild from scratch on a fresh distribution) and again at gate 30.
**Method:** inspection, with the clean-machine clause by demonstration (shared with REQ-F5) ·
**Owner stage:** 05 (pins), 13A (result schema), 27 (rebuild), 29 (claims audit), 31 (release) ·
**Closes:** DoD-17, and supports DoD-1, DoD-2, DoD-9, DoD-13, DoD-16
**Tier:** CORE. Owned by the measurement-validity role as an evidence-bound claim (decision D-10).

### REQ-Q4 · Continuous integration on every push
**Statement:** GitHub Actions runs build, lint, type check, the CPU-reference tests and a gitleaks
secret scan on every push. GPU tests run locally and their output is committed against the SHA that
produced it, because free runners have no GPU (fact-check item F11).
**Criterion:** a green CI run on the current SHA, and a committed GPU test log for every SHA that
claims a GPU test passed. A GPU claim with no log for that SHA counts as unproven.
**Method:** inspection of the CI run and the per-SHA logs · **Owner stage:** 15 (CI, including the
gitleaks job that closes finding RV-03), 16 (test suite) · **Closes:** DoD-17 metadata-and-evidence
clause; supports DoD-7
**Tier:** CORE

### REQ-Q5 · Environment metadata in every result file
**Statement:** Every file under results/ carries: git SHA, device name, compute capability, driver and
KMD version, CUDA UMD version, PyTorch, Triton and CUDA toolkit versions, the
TRITON_DEFAULT_FP_FUSION setting, GPU clock, temperature and power limit during the run, the fixed
NitroSense setting, and a UTC timestamp.
**Criterion:** the schema is fixed at 13A and a validator rejects any result file missing a field. The
power limit is recorded because this GPU's limit was observed changing between 30 W and 50 W on AC
power, and a change to it invalidates the run (risk R21). Timestamps are UTC because the WSL clock
runs in UTC. The schema excludes hostname and username (finding RV-10).
**Method:** test (the validator), inspection (the schema document) · **Owner stage:** 13A (schema),
08 (harness emits it), 05 (pins) · **Closes:** DoD-17
**Tier:** CORE

<!-- PENDING 2B · Study requirements REQ-S1 to REQ-S11. REQ-S2 must name oracle O1 (sync versus
     no-sync) explicitly, because the charter generalised that definition-of-done line to "passes its
     validation oracles". REQ-S5's roofline criterion is written from the brief's fuller wording.
     REQ-S11 states the T4-only scope, with the P100 half recorded as cut by amendment at gate 05
     (change request CR-04) and never silently omitted. -->
<!-- PENDING 2D · End-to-end model criteria. -->
<!-- PENDING 2E · Acceptance criteria summary and NON-GOALS.md; reconcile the brief's nine refused
     items against the charter's EXCLUDED tier rather than writing a third list. -->
<!-- PENDING 2F · TRACEABILITY-MATRIX.md v0 on DoD-1 to DoD-17 and SE-1 to SE-6; restore plan section
     order in this file at the same time. -->
