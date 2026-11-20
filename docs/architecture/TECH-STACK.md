# FusionGap · Technology stack (provisional)

Status: draft (stage 03) · updated at 04 · frozen at 05
Date: 2026-11-19

Every cell in section 3 is closed by evidence, fixed by a recorded decision, or open with
an owning spike and a written pass criterion. A cell with no evidence plan is what gate 03
fails on.

## 1 · Criteria

Pass/fail filters, applied before any scoring: $0 cost · WSL2 support.

| Criterion | Weight |
|---|---|
| Compute-capability-7.5 evidence | 40 |
| Reproducibility (pinnable) | 25 |
| Ease of learning | 20 |
| Interview relevance | 15 |

The four names, the weights and the two filters above are quoted from AM-04 rather
than paraphrased. This project's glosses, which are glosses and not criteria:
*pinnable* means recreatable from a written document; *ease of learning* is read
against the skills ledger; *interview relevance* means relevance to the target role.

Provenance, stated only as far as this repository can prove it. The weights entered
the repository in commit `3a738ef` at 2026-11-18T07:42:22Z, which is an ancestor of
every commit in which a candidate was scored, verified with
`git merge-base --is-ancestor` and never with a date filter (RV-25). That is the
claim gate 03 rests on, and it holds.

AM-04 additionally dates its own decision 2026-11-15 and attributes the weights to an
ADR-0001 draft dated 2026-11-03. Neither date is verifiable from this repository: the
amendments log was seeded in a single commit on 2026-11-18, and a date written inside
a file is author-settable, which is the weakness risk R5 raises about commit dates.
Both are recorded here as AM-04's attribution and not as established fact. The
2026-11-03 draft it cites is held outside this repository, so the attribution cannot
be checked from here; bringing that draft into the history is an open item. No weight
has moved since, and none moves after a score is seen.

Where a criterion cannot distinguish the candidates in a cell, it is recorded CONSTANT
with the evidence that makes it constant, and the discriminating subtotal is shown
separately. That is not a reweighting: a 100-point rubric that silently decides on 60
points misleads whoever reads the score.

## 2 · Fixed inputs — recorded, never scored

These were decided before this stage and are not candidates here. Scoring them would
reopen an approved decision without a change request.

| Input | Source |
|---|---|
| Three kernels: K1 RMSNorm + residual, K2 SiLU-multiply, K3 chunked linear + cross-entropy | brief; D-01 |
| Each kernel in Triton and in CUDA C++, forward and backward | brief; D-02 |
| `torch.compile` (Inductor) is the primary baseline | brief; D-03 |
| Predictions P1 to P4, pre-registered before any result | brief; D-04, D-07 |
| One repository | CR-01; ADR-0006 |
| Zero budget · GTX 1650 with 4 GB · 8 GB shared host RAM · WSL2 | brief; D-05 |
| Cut order C2, recorded and currently dormant | D-09; D-23 |

## 3 · Stack cells

Status values are not interchangeable:

- **DECIDED + VERIFIED** — chosen, and a command has confirmed it on this machine
- **DECIDED, UNVERIFIED** — chosen, never checked. Carries an enforcement check, so drift
  fails a test instead of quietly changing a measurement
- **FIXED BY DECISION** — chosen, with nothing that can drift
- **OPEN** — not yet chosen. The owning spike and the pass criterion are named

| # | Cell | Status | Pick | Owning spike · pass criterion |
|---|---|---|---|---|
| 1 | Environment manager and lock format | OPEN — decided at this stage | venv + pip + pip-tools >= 7.5.3; `pip-compile --generate-hashes` to `env/requirements.lock`; `pip install --require-hashes` | 5D: a fresh distro installs from the lock alone and re-passes the 4B and 4E smokes; `pip freeze` diffs empty against the lock. Scoring in section 7; decision in ADR-0001 |
| 2 | torch | DECIDED + VERIFIED | 2.15.0+cu132 | 4B passed 2026-11-14: first pair where both the Triton kernel and Inductor-emitted Triton worked. Enforced by `tests/test_environment.py` |
| 3 | Triton | DECIDED, UNVERIFIED | 3.9.0 — whatever the torch wheel pins; never chosen separately | CR-01; reason in ADR-0002. Enforcement: `tests/test_environment.py` asserts the installed version equals torch's pin and that `TRITON_DEFAULT_FP_FUSION=1` is set — 3.9 warns the default flips in 3.10, so an unset variable is a silent change of arithmetic (R22) |
| 4 | CUDA toolkit | DECIDED + VERIFIED | 13.2.2-1, nvcc 13.2.86, wsl-ubuntu repository | V13, 2026-11-19: nvcc major.minor equals `torch.version.cuda`. Re-checked under `cpp_extension` at 4E |
| 5 | Host compiler | DECIDED + VERIFIED, zero headroom | `g++-15` named explicitly, never the unversioned `gcc` alias | V14, 2026-11-19: `crt/host_config.h` errors above GCC major 15, the installed gcc is 15.2.0, and an `-arch=sm_75` compile passed. RV-28 carries the headroom risk. 4E confirms under `cpp_extension` |
| 6 | Binding | DECIDED, UNVERIFIED | `cpp_extension.load` for development, `BuildExtension` for release | 4E (load) and 4F (release): the built wheel installs into a fresh venv, imports, and `torch.equal` holds at n = 1, n = block size, and n not a multiple of block size |
| 7 | Build backend | OPEN | setuptools with torch's `BuildExtension` | 4F, same criterion as cell 6. CMake rejected: a second build language to explain at stage 15 for no capability this project needs |
| 8 | Distribution model | OPEN | ADR-0004 option (d): pure-Python Triton plus an optional CUDA extension | 4F: TestPyPI accepts the artefact and a fresh venv installs and runs it. Covers RV-12, since PyPI rejects bare `linux_x86_64` wheels |
| 9 | Test, lint and type tools | DECIDED, UNVERIFIED | pytest, ruff, mypy; versions pinned at 5C | 4G: all three run green on a CPU-only GitHub Actions runner |
| 10 | Telemetry source | OPEN | undecided between WSL `nvidia-smi`, `nvidia-smi.exe` through interop, and pynvml | 4C: a **single** source, sampled from a separate process at 2 Hz or faster, returns all five fields — SM clock, memory clock, temperature, power draw, throttle reasons — for the whole of a sustained load of at least 30 s above 90 % utilisation, **and** the SM clock changes between the idle baseline and the loaded window by more than the read-to-read spread of the idle samples. Fields assembled across sources fail, even if each field individually returns a value. Fallback: ADR-0003's spin-kernel clock probe, temperature disclosed as unavailable |
| 11 | Profilers | PARTLY FIXED | `torch.profiler` fixed; nsys and ncu conditional on F6 | 4C: an adverse pass requires the error text **and** the named Windows-side NVIDIA setting that produces it, matched to each other. Any other failure — a crash, a hang, an unexplained non-zero exit — is STOP-AND-FIX, not an adverse-but-valid result. A profiler that fails for an unknown reason is an open defect, not a documented limitation |
| 12 | Analysis | DECIDED + VERIFIED | numpy 2.5.5, pandas 3.1.1, matplotlib 3.11.2; CSV with JSON sidecars | V15, 2026-11-19. No spike: nothing about the GPU is in question. numpy is added at the 05 lock — its absence prints a warning into every torch run, and run logs are evidence |
| 13 | Continuous integration | DECIDED, UNVERIFIED | GitHub Actions, public repository, CPU runners | 4G: `TRITON_INTERPRET=1` runs the 4B kernel under pytest; `nvcc -arch=sm_75 -c` compiles the 4E kernel; job runtime and public-repository minute terms recorded (F11) |
| 14 | Repository | FIXED BY DECISION | one repository; `src/fusiongap/` published, `bench/` not | CR-01; ADR-0006. Nothing can drift |
| 15 | Python version | OPEN — closes RV-16 | 3.14.4, the system interpreter | 5C: the lock resolves with a 3.14 wheel for every pin; 5D installs it on a fresh distro. Rule in ADR-0001: changes only by dated amendment |
| 16 | Operating system, toolkit and host-compiler compatibility | OPEN | Ubuntu 26.04.1 LTS + CUDA 13.2 from the wsl-ubuntu repository + g++-15 | 5D is the criterion: the fresh-distro rebuild reproduces the stack from `ENVIRONMENT.md` alone and re-passes 4B and 4E. Carried by RV-27 and RV-28; disclosed in section 4 |

## 4 · Disclosure — unvalidated operating-system and toolkit pairing

NVIDIA's installation guide for CUDA 13.2 lists Ubuntu 24.04 and 22.04 for amd64 among
its validated distributions and does not list Ubuntu 26.04, which first appears with
CUDA 13.3. The toolkit here came from NVIDIA's `wsl-ubuntu` repository, which is not keyed
to an Ubuntu release, so most of the exposure is removed — but the glibc and kernel
pairing underneath is not one NVIDIA states it has tested. The host-compiler major
version, which is the only version nvcc checks, is inside the documented range and has
been confirmed by compiling rather than by reading.

Consequence, written down before it is needed: a build or run failure in 4E, 4I or 4J is
attributed to this pairing **only after** the pairing has been eliminated as a cause. The
fallback is a fresh Ubuntu 24.04 distribution as the 5D rebuild target, never a toolkit
upgrade — that would break torch's `cu132` pairing and reopen cell 4.

Facts: `../project/VERIFICATION-LOG.md` F12, V13, V14. Risks: RV-27, RV-28.

## 5 · Enforcement — `tests/test_environment.py`

Three cells are decided but unverified, which means the documented stack and the installed
stack can diverge without anything failing. Written at stage 16 and run in CI from 15C,
this test asserts the configuration rather than describing it:

- `torch.__version__` and `torch.version.cuda` match the pins
- the installed Triton version equals the version the torch wheel pins
- `sm_75` appears in `torch.cuda.get_arch_list()`
- `gcc -dumpversion` reports a major no greater than 15
- `TRITON_DEFAULT_FP_FUSION` is set to 1
- nvcc's reported release matches `torch.version.cuda`

This makes gate 05's rule — no work on an unpinned stack — something a machine can fail.

## 6 · Decision-record number allocation

Numbers come from the project plan. Never invent one.

| Record | Subject | Drafted | Frozen |
|---|---|---|---|
| ADR-0001 | Environment pins, lock mechanism, host compiler | 03 | 05 |
| ADR-0002 | Triton and Inductor on compute capability 7.5 | 04 | 05 |
| ADR-0003 | Telemetry source | 04 | 05 |
| ADR-0004 | Distribution model | 04 | 05 |
| ADR-0005 | CI scope | 04 | 05 |
| ADR-0006 | One repository | 03 | 05 |
| ADR-0007 | fp64 test builds | 12 | 14 |
| ADR-0008 | Baselines | 10 | 10 |
| ADR-0009 | K3 per-chunk GEMMs | 12 | 20 |
| ADR-0010 | K3 backward strategy | 20 | 20 |
| ADR-0011 | End-to-end model | 11 | 24 |
| ADR-0012 | Extension scope | 23 | 23 |

## 7 · Scoring — the environment-manager cell

The only cell this stage scores. Filters: both candidates and the two rejected options
cost nothing and run under WSL2.

| Criterion (weight) | venv + pip + pip-tools | venv + pip, uv as resolver | uv end to end | conda / mamba |
|---|---|---|---|---|
| CC 7.5 evidence (40) | CONSTANT | CONSTANT | CONSTANT | CONSTANT |
| Reproducibility (25) | 22 | 22 | 25 | 15 |
| Learnability (20) | 18 | 12 | 8 | 6 |
| Role relevance (15) | 9 | 12 | 15 | 5 |
| **Discriminating subtotal / 60** | **49** | 46 | 48 | 26 |

CONSTANT because none of the four changes which wheels exist or whether `sm_75` code runs;
the 4A and 4B evidence was produced under the first option.

One point separates the first and third options, so the rubric did not decide this and is
not presented as having done so. The tie-break is a cost: uv end to end wants to own the
interpreter, so adopting it discards the environment that produced the only GPU evidence
this project has and reopens D-18, for roughly 4.5 hours of the 15-hour spike budget and
no gain in any measurement. Full reasoning, alternatives and reversal trigger:
`adr/ADR-0001-env-pins.md`.
