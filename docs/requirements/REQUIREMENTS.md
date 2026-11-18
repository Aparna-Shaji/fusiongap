# FusionGap · Requirements and acceptance criteria

**Status: BASELINED at gate 02 on 2026-11-18.** Changed only by a dated entry in
`docs/project/AMENDMENTS.md`. Gate 02's first run returned NO-GO on eight findings; all eight were
corrected and independently re-reviewed before this baseline. 28 requirements covering 17 core and 6
strongly-expected definition-of-done lines.
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
match the reference within REQ-Q1 tolerances; gradcheck passes in fp64; the memory-scaling claim is
checked as two measurements — at fixed chunk size, measured peak memory stays flat within a tolerance
fixed in PROTOCOL as the total row count rises by at least a factor of four, and at fixed row count it
rises approximately linearly across at least three chunk sizes; a chunk size that does not evenly
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

## 2B · Study requirements

Each requirement names the measurement that settles it. REQ-S12 was added here: mapping the 23
requirements the plan defines against DoD-1 to DoD-17 showed DoD-1 (prior-art positioning) covered by
none of them. Gate 02's own NO-GO branch prescribes adding the requirement, so no change request is
needed.

### REQ-S1 · Measured hardware ceilings
**Statement:** This GPU's ceilings are measured, never taken from specifications: peak
device-to-device copy bandwidth in GB/s, and peak FLOP/s for fp32 and fp16 separately from a large
dense GEMM. The measurement method is published alongside the numbers.
**Criterion:** both ceilings recorded under results/ with the script that produced them, the dtype
named for each FLOP/s figure, and the gap against the vendor specification noted. The ridge point per
dtype is computed from these measured values, and no roofline claim anywhere uses a specification
number.
**Method:** test (the benchmarks), analysis (the ridge point), inspection (method published) ·
**Owner stage:** 07 · **Closes:** DoD-3; supplies the denominator REQ-S5 requires
**Tier:** CORE
**Note:** deviceQuery reports a 1515 MHz maximum clock against nvidia-smi's 1785 MHz — about an 18 %
spread in theoretical fp32 peak — which is why only measured ceilings are used (finding R16).

### REQ-S2 · Harness validation oracles
**Statement:** The harness passes oracles O1 to O7 before any comparative number is reported. O1 is
the sync-versus-no-sync demonstration: the same workload timed with and without
`torch.cuda.synchronize()` must differ by at least the factor fixed in PROTOCOL (10B), proving the
harness measures execution rather than launch overhead.
**Criterion:** O1 passes only when the no-sync median falls below a stated fraction of the sync
median, with that fraction fixed in PROTOCOL before the harness is accepted and recorded with the
reasoning that set it; a threshold chosen after seeing the measurement is a tuned threshold and voids
the oracle. Every oracle has a recorded pass with its output. O1 is named explicitly because the
charter generalises this definition-of-done line to "passes its validation oracles" while the brief's
line is specifically the sync-versus-no-sync difference. O2 degrades to a linearity check if no clock
is readable, a two-timer oracle checks the host clock against summed CUDA-event times (finding RV-07),
and O7 requires the same cell timed with the telemetry sampler on and off to agree within IQR
(finding RV-06).
**Method:** test · **Owner stage:** 08, with 8D adding the oracles from the plan review ·
**Closes:** DoD-4
**Tier:** CORE. A failed oracle stops everything downstream — this is the week-one hard gate.

### REQ-S3 · Measurement hygiene per reported cell
**Statement:** Every reported cell is a median with inter-quartile range over at least five repeats,
with at least twenty warm-up iterations discarded, variant order shuffled within each repeat, a
cooldown between benchmark groups, and GPU clock, temperature and power limit logged per run. No bare
single number appears anywhere.
**Criterion:** the raw CSV holds every repeat, including discarded and throttled runs; throttling
events are reported rather than dropped; any cell whose telemetry shows the power limit changing
during the run is invalidated and re-measured (risk R21).
**Method:** test (the harness emits it), inspection (raw data committed) · **Owner stage:** 08,
10B (PROTOCOL fixes repeats, warm-up and cooldown), 13A (schema) · **Closes:** DoD-8, jointly with
REQ-F6
**Tier:** CORE

### REQ-S4 · Inductor-generated code as evidence
**Statement:** The Triton code Inductor generates for each kernel pattern is dumped, committed, and
discussed in the report: what it fused, whether it fused more or less than the hand-written kernel,
and what that implies about where automatic fusion stops.
**Criterion:** one committed dump per kernel pattern under results/inductor/, each tied to the pinned
torch version, plus a report section stating, per kernel pattern, which operations Inductor fused,
whether that set is the same as, larger than, or smaller than the hand-written kernel's, and at least
one named mechanism for any difference. A section that attaches the dump without answering those three
points does not satisfy this requirement.
**Method:** inspection · **Owner stage:** 19B (K1), 23D (K3), 26B (K2 if built) · **Closes:** DoD-9
**Tier:** CORE
**Note:** the stage-4B spike already showed Inductor specialising a kernel to its exact size (constant
element count, all-true mask) — a mechanism to discuss at stage 19.

### REQ-S5 · Roofline per kernel
**Statement:** For each kernel the report gives arithmetic intensity (FLOPs per byte moved to and from
global memory), the ridge point computed from the measured ceilings, whether the kernel is
memory-bound or compute-bound against that ridge point, and achieved bandwidth as a percentage of the
measured peak. The denominator is named at every use.
**Criterion:** written from the brief's full wording rather than the charter's one-line summary. Every
figure states which peak and which dtype it uses; a roofline figure without a named denominator is
incomplete — the same error as a utilisation figure with no peak.
**Method:** analysis, with inspection of the denominator statement · **Owner stage:** 19C (K1),
23E (K3), on REQ-S1's ceilings · **Closes:** DoD-10
**Tier:** CORE

### REQ-S6 · End-to-end attribution
**Statement:** The report states what fraction of baseline training-step time each kernel occupied
before substitution, and interprets the end-to-end effect against that fraction.
**Criterion:** the attribution table states each kernel's measured share of baseline step time, and
the report states, beside the measured end-to-end result, the maximum end-to-end gain that share
permits — a kernel that was 3 % of step time cannot deliver more than a 3 % end-to-end gain. A measured
gain reported without that ceiling next to it does not satisfy this requirement.
**Method:** analysis from profiler data · **Owner stage:** 24, gate 25 · **Closes:** DoD-11, jointly
with REQ-F7
**Tier:** CORE

### REQ-S7 · K3 memory boundary and demo configuration
**Statement:** The K3 result is reported as an out-of-memory boundary curve over (batch x sequence,
vocabulary) for variants B1 to B4, plus one exact configuration where the reference fails on 4 GB and
the fusiongap kernel completes.
**Criterion:** the curve covers a grid, not a single favourable point (finding R13); the demo
configuration is recorded exactly — batch, sequence, vocabulary, dtype and logits policy — and
rehearsed before it is shown; the logits-precision policy is the one fixed in PROTOCOL, because that
choice moves the boundary by up to roughly 3x (finding RV-02).
**Method:** demonstration for the configuration, test for the curve · **Owner stage:** 23C, rehearsed
at 29 · **Closes:** DoD-12
**Tier:** CORE

### REQ-S8 · Every loss reported
**Statement:** Every configuration where a baseline beat the hand-written kernel is reported with its
number, in the body of the report.
**Criterion:** a script derives the losing cells from the raw results and the report contains each
one, with the count stated rather than left implicit. Prediction P4 anticipates at least one such
cell, so an empty list is itself a result that needs explaining.
**Method:** inspection against the raw data · **Owner stage:** 25A, 29 (claims audit) ·
**Closes:** DoD-13
**Tier:** CORE

### REQ-S9 · Predictions scored by their pre-registered rules
**Statement:** Predictions P1 to P4 are scored by the decision rules fixed before the prereg-v1 tag,
including those that turn out false.
**Criterion:** scoring uses the operational rules in PROTOCOL and PREDICTIONS — P1 counts only cells
where the Triton kernel beats eager with non-overlapping IQRs and is unscorable if more than half the
cells are undefined; P4 requires the loss to exceed the minimum effect size fixed before tagging, with
non-overlapping IQRs, and to recur when re-measured in a fresh session. A scoring script and a hand
check must agree. Neither file is edited after the tag; any deviation is disclosed, not hidden.
**Method:** test (the scoring script), inspection (script against hand check) · **Owner stage:**
10 (rules tagged), 25A (scored) · **Closes:** DoD-15
**Tier:** CORE

### REQ-S10 · Ridge-point portability limitation in the abstract
**Statement:** The abstract states that this GPU's ridge point is far below a datacenter GPU's, so the
roofline conclusions drawn here do not transfer, and that an optimisation which wins on consumer
Turing may be the wrong optimisation elsewhere.
**Criterion:** the statement appears in the abstract, not only in a limitations section, and uses this
project's own measured ridge points rather than illustrative figures.
**Method:** inspection · **Owner stage:** 28 (report), checked at 29 · **Closes:** DoD-14
**Tier:** CORE

### REQ-S11 · Portability check on a second device
**Statement:** The benchmark suite runs unattended on a Kaggle T4 — the same Turing family but with
tensor cores — and the report states whether the ranking of variants is stable against the GTX 1650,
explaining any instability from each device's own roofline.
**Criterion:** one unattended script per device writing to results/kaggle/; the correctness suite runs
first on that device before any timing; device-specific ceilings measured by the stage-07 method; and
profiler kernel names recorded rather than inferred wherever a GEMM may take a tensor-core path.
**Method:** test · **Owner stage:** 26A · **Closes:** SE-3
**Tier:** STRONGLY EXPECTED, T4 only. The P100 half of SE-3 is unachievable — Kaggle no longer offers
P100 and the pinned torch drops Pascal — and is recorded as CUT BY AMENDMENT at gate 05 (change
request CR-04), never silently omitted. Note: the plan-file upload labels this OPTIONAL; the charter
places the Kaggle check in the strongly-expected tier and governs.

### REQ-S12 · Prior-art positioning
**Statement:** A positioning paragraph is written and committed before the first file under
src/fusiongap/, citing at least five sources actually read, stating plainly that the kernels are not
novel, and naming what this study measures that the cited work does not publish.
**Criterion:** at least five citations, each confirmed to resolve to a real source (fact-check item F8
requires confirming each before citing); for at least three of them the paragraph states what that
source does and does not publish about these kernels, which is the check that distinguishes reading
from listing; the paragraph is the README's first substantive paragraph; and its commit is an ancestor
of the first commit of any file under src/fusiongap/, checked with `git merge-base --is-ancestor`
rather than by comparing dates.
**Method:** inspection, with the ordering check run against git log · **Owner stage:** 09 ·
**Closes:** DoD-1
**Tier:** CORE — first item on the never-cut list.
**Added at 2B:** DoD-1 was covered by no requirement in the plan's set. Gate 02's NO-GO branch for a
definition-of-done line with no requirement prescribes adding one, so this is the gate's remedy rather
than a change to the plan.

### REQ-S13 · Profiler traces, or a recorded failure
**Statement:** Nsight Systems and Nsight Compute traces are committed, at least one per kernel, if the
tooling runs on this GPU under WSL2.
**Criterion:** one trace per kernel under results/traces/ with the tool version recorded; or, where
the tooling does not run, a recorded reproduction of the failure (command, error output, date) plus a
dated AMENDMENTS entry cutting SE-4, and a report statement that the roofline rests on hand-computed
arithmetic and PyTorch profiler data instead. Counter data is never fabricated where the tool was
unavailable (fact-check item F6).
**Method:** inspection · **Owner stage:** 4C (does it run), 26C (traces) · **Closes:** SE-4
**Tier:** STRONGLY EXPECTED, conditional on F6. DONE with evidence or CUT by amendment; never
relabelled.

### REQ-S14 · Autotuning search documented
**Statement:** The autotuning configuration search is documented: the space searched, the
configurations tried, the winner per shape, and the wall-clock cost of searching.
**Criterion:** a committed record per autotuned kernel listing the search space and the selected
configuration for each shape, plus the search's wall-clock cost reported as its own number, so a tuned
result is not presented as though the tuning were free.
**Method:** inspection · **Owner stage:** 10A, then per kernel at 17, 18, 21, 22 · **Closes:** SE-5
**Tier:** STRONGLY EXPECTED

### REQ-S15 · Compilation time reported as its own cost
**Statement:** `torch.compile` compilation time is measured separately from execution and reported as
its own number, at both default and max-autotune settings.
**Criterion:** the first compiled call's wall-clock time is recorded per cell and excluded from the
timed region as warm-up, and the report carries a compile-time table beside the speed tables. A
speedup reported without its compilation cost overstates the compiler's practical value.
**Method:** test (the harness records it), inspection (the table exists) · **Owner stage:** 08,
10B (PROTOCOL), 28 (report) · **Closes:** SE-6
**Tier:** STRONGLY EXPECTED

## 2C · Quality requirements

Written before 2B because REQ-Q1 fixes the per-dtype tolerances that REQ-F1, REQ-F2, REQ-F3 and
REQ-F4 all refer to. Plan order was restored at 2F; this note records the order the sections were written in.

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
the failure mode of widening them later until a test passes, which destroys the gate. Once recorded,
a tolerance is widened only by a dated AMENDMENTS entry naming the measurement that justified it.

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

### REQ-Q6 · Pre-registration integrity
**Statement:** Predictions P1 to P4, together with the decision rules that score them, are committed
and tagged `prereg-v1` on the public remote before any comparative result between a baseline and a
hand-written kernel exists. Neither PROTOCOL nor PREDICTIONS is edited after the tag; a deviation is
disclosed in AMENDMENTS, never silently applied.
**Criterion:** six checks, all mechanical — (1) the predictions file and the `prereg-v1` tag both
exist on the public remote; (2) the tagged commit contains both the predictions and the scoring rules;
(3) that commit carries a date; (4) that commit is an ancestor of every commit containing a
comparative result, checked with `git merge-base --is-ancestor` rather than a date filter; (5) the
rules used to score P1 to P4 at 25A are byte-identical to the tagged ones; (6) any post-tag change to
either file appears as a dated AMENDMENTS entry.
**Method:** inspection, with checks 4 and 5 run as commands · **Owner stage:** 10 (tag), 25A
(scoring), 29 (claims audit) · **Closes:** DoD-2
**Tier:** CORE — second item on the never-cut list.
**Why its own requirement:** DoD-2 states a temporal-integrity condition, not a packaging one, and it
carries its own hard checkpoint at gate 10. Inside REQ-Q3 it was one clause among a dozen and could be
satisfied by inspection of the wrong thing. Check 4 uses ancestry deliberately: date filtering
misbehaved in this repository on 18 Nov 2026 (friction log), and ancestry is a structural fact of the
history rather than a parsed timestamp.

## 2D · End-to-end model criteria

These fix what REQ-F7 runs on. The model is chosen at stage 11D against these criteria and frozen
there; it is not written from scratch.

**(a) Architecture.** A Llama-style decoder block: RMSNorm, SwiGLU, and a residual add feeding the
norm, so that K1 and K2 actually execute in the step. A model that routes around either kernel makes
the attribution table meaningless.

**(b) Vocabulary and head.** A realistic vocabulary, at least the V = 32000 case, with an LM head and
loss that K3 can replace. Without a realistic vocabulary the K3 memory result has nothing to act on.

**(c) Fit and provenance.** Stock forward and backward fit in 4 GB with free VRAM to spare at the
chosen configuration, the licence is permissive, and the reference implementation is known-good.
Free VRAM varies on this machine because the display compositor also runs on the GTX 1650, so the
margin is measured rather than assumed (verification item V5).

**(d) Data.** Random token IDs are sufficient for step-time measurement. Real text is required only if
the quantization arm needs a quality number (26D).

## 2E · Acceptance criteria and non-goals

**Acceptance criteria.** Every requirement in 2A, 2B and 2C carries its criterion, its verification
method, its owner stage and the definition-of-done line it closes, recorded inline rather than in a
separate list, so a requirement and its acceptance test cannot drift apart.

**Coverage result (the evidence gate 02 is scored against).** All seventeen core lines are covered by
at least one requirement:

- DoD-1 → REQ-S12 · DoD-2 → REQ-Q6 · DoD-3 → REQ-S1 · DoD-4 → REQ-S2, evidence from REQ-F6
- DoD-5 → REQ-F1 · DoD-6 → REQ-F2 · DoD-7 → REQ-Q1, REQ-Q2 · DoD-8 → REQ-F6, REQ-S3
- DoD-9 → REQ-S4 · DoD-10 → REQ-S5 · DoD-11 → REQ-F7, REQ-S6 · DoD-12 → REQ-S7
- DoD-13 → REQ-S8 · DoD-14 → REQ-S10 · DoD-15 → REQ-S9 · DoD-16 → REQ-F5
- DoD-17 → REQ-Q3, REQ-Q4, REQ-Q5
- SE-1 → REQ-F3 · SE-2 → REQ-F4 · SE-3 → REQ-S11 (T4 only) · SE-4 → REQ-S13 · SE-5 → REQ-S14 ·
  SE-6 → REQ-S15

Gate 02's first run returned NO-GO on 2026-11-18. These are the corrections: DoD-1 had no requirement
until REQ-S12 was added at 2B; DoD-2 was covered only as a clause of REQ-Q3 and now has REQ-Q6; SE-4,
SE-5 and SE-6 had no criterion and now have REQ-S13, REQ-S14 and REQ-S15; and four criteria with
untestable wording — REQ-S2's oracle threshold, REQ-F2's memory scaling, and the report conclusions in
REQ-S4 and REQ-S6 — were rewritten as named measurements.

**Non-goals** are recorded in docs/requirements/NON-GOALS.md — the charter's EXCLUDED tier, which
already reconciles the brief's eight refused items with the scaling-law exclusion named in the brief's
role-alignment table.

## 2F · Traceability matrix

Recorded as its own file: docs/requirements/TRACEABILITY-MATRIX.md (v0). It carries two views — by
requirement, and by definition-of-done line — because gate 02 is scored on the second. Design and test
columns stay empty until stage 14 (control C4), so the matrix cannot claim coverage that does not yet
exist.

B5 Liger and K3 backward strategy (b) appear there as optional rows with no requirement of their own:
neither is a definition-of-done line in brief section 20, so gate 02 does not ask for them. B5 is
covered by REQ-F6's optional clause and strategy (b) by ADR-0010; both sit in the cut order.
