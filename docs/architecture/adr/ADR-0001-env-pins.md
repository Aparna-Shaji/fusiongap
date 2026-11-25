# ADR-0001 — Environment pins, dependency lock mechanism and host compiler

Status: proposed
Date: 2026-11-19
Owner stage: 03 → frozen at 05

## Context
This is a measurement study: every number it reports is a measurement of one
configuration on one machine. A configuration that is not pinned and recorded makes a
result unattributable, and the fresh-distro rebuild that gate 05 requires has nothing to
follow. The brief fixes the hard constraints — $0, a GTX 1650 with 4 GB, 8 GB of shared
host RAM, WSL2. Decision D-18 fixed the virtual environment and deliberately left two
things to this stage: how dependencies are pinned, and the Python-version rule
(condition RV-16).

**On decision identifiers.** `D-nn` and `CR-nn` in this record refer to entries in the
project's state file, which is working memory and is not part of this repository. They are
secondary references and a reader outside the project cannot follow them. Everything
load-bearing here rests on the evidence paths named below and on the dated entries in
`../../project/AMENDMENTS.md`, all of which are in the repository.

## Decision
Four parts.

1. **Python.** The system interpreter, 3.14.4, used through a stdlib `venv` at
   `~/projects/fusiongap/.venv`, outside the repository. The Python version changes only
   by a dated amendment, because changing it invalidates the 4A and 4B evidence and every
   GPU measurement taken after it. This closes RV-16.
   **How a fresh distribution obtains it.** Which version is pinned and how it is reproduced
   are different decisions, and only the first was taken until now. The second: the
   distribution's own packages, `sudo apt-get install -y python3 python3-venv`, with no
   third-party archive and no source build. Both are installed here, measured 2026-11-23 -
   `python3` from `main` and `python3-venv` from `universe`, so a minimal rootfs that has not
   enabled `universe` cannot complete this step [VERIFY at 5D].
   **The package version is not the interpreter version, and that is the trap.** On
   2026-11-23 `apt-cache policy python3` reported 3.14.3-0ubuntu2 while the interpreter
   reported 3.14.4: `python3` is a metapackage naming the default Python series, and the
   binary at `/usr/bin/python3.14` is owned by `python3.14-minimal`. The package version
   therefore cannot detect a patch-release change, and a fresh distribution installing a later
   3.14.x would announce nothing. **The check at 5D is the interpreter itself** -
   `python3 --version` must print 3.14.4. If it does not, 5D **stops**: the rebuild is then
   not a reproduction, the difference is recorded as a dated amendment, and no measurement is
   taken under the new interpreter until it is.
2. **Dependency pinning.** `pip-tools >= 7.5.3`. `pip-compile --generate-hashes` produces
   `env/requirements.lock`; installation is always
   `pip install --require-hashes -r env/requirements.lock`. The 7.5.3 floor is not cosmetic
   and it is load-bearing: the stage-03 rubric did not decide this on its own - `../TECH-STACK.md`
   section 1 carries the scores and says so - so this option won on a tie-break, and the floor
   is what makes it credible. Three claims support
   the floor. None has been confirmed against this machine, and each carries its check:
   (a) that release declares Python 3.14 support
   [VERIFY at 5C: read the pip-tools changelog entry for 7.5.3 and its declared
   Requires-Python];
   (b) it is compatible with pip 26 - the installed pip is 26.3, measured 2026-11-23
   [VERIFY at 5C: `pip-compile --version` runs and resolves under that pip];
   (c) it fixes a defect where `pip-compile` dropped index-URL options while looking up
   hashes, which broke resolution for packages available only from an extra index — which is
   exactly how torch is published
   [VERIFY at 5C: the generated lock carries the index URL for the torch entry].
   If any of the three is wrong the floor is wrong, and after gate 05 that costs a dated
   amendment and a re-resolve inside stage 05's two-hour box.
3. **Host compiler.** `g++-15` is named explicitly wherever a host compiler is selected,
   never the unversioned `gcc` alias. nvcc 13.2 errors above GCC major 15 and this
   distribution's default is 15.2.0, so there is no headroom and an ordinary system
   update would otherwise break every CUDA build silently (RV-28).
4. **Pins**, as measured on 2026-11-19 and **read back against the machine at 5A on
   2026-11-25**. Every installed row matched its pinned value on that read, each by the
   command its own row names - including the two the Python row requires and the separate
   invariant the Triton row requires. The rows reading [UNKNOWN] are uninstalled by
   design and are filled at 5C: a deferral with a named owner, not a gap. Frozen here.

| Layer | Pin | Checked by |
|---|---|---|
| Windows build | Windows 11 Home Single Language, version 25H2, OS Build 26200.9974 | `winver` on Windows (Win+R, then winver); read 2026-11-23 |
| WSL kernel | 6.18.58.1 | `uname -r` |
| Ubuntu | 26.04.1 LTS | `lsb_release -d` - present at /usr/bin/lsb_release, confirmed 2026-11-23. Not guaranteed on a minimal rootfs, so 5D falls back to `grep PRETTY_NAME /etc/os-release` |
| NVIDIA KMD (Windows-side) | 621.01 | `nvidia-smi` |
| CUDA UMD | 13.5 | `nvidia-smi` |
| `nvidia-smi` (the telemetry instrument) | **620.67.01** - the tool's own version, distinct from KMD 621.01 and CUDA UMD 13.5 and lower than both | `nvidia-smi`, header line 3; read 2026-11-25. Pinned because this binary is the source of every telemetry number the project records (D-31, ADR-0003), and because all six instances of "verify the effect, not the return code" are behaviours *of this binary at this version* - the `-lms` interval that delivers 1.92 Hz, `-ac` and `-lmc` exiting 0 while setting nothing, the throttle counters that are a wall clock (RV-31), the `-q -d POWER` field split that `--query-gpu` collapses. A different version re-opens every one of them (F49) |
| CUDA toolkit | 13.2.2-1, nvcc 13.2.86, from the wsl-ubuntu repository | `nvcc --version` |
| Host compiler | g++-15 (15.2.0-16ubuntu1) | `g++-15 --version` |
| Python | 3.14.4 - the system interpreter **and** the project venv interpreter, which must agree | Two commands, both required: `python3 --version` and `.venv/bin/python --version`; both printed 3.14.4 on 2026-11-23. One command cannot verify this pin, because the two can disagree - on 2026-11-12 `python3 -m venv` over an existing environment kept a 3.12.16 interpreter while rewriting `pyvenv.cfg`. `python` is not a system name on this machine |
| torch | 2.15.0+cu132 at runtime; the distribution metadata reports **2.15.0**, so the lock entry will read `torch==2.15.0`. The version string alone does not identify this wheel - the lock must carry its hash **and** the index it came from | `.venv/bin/python -c "import torch; print(torch.__version__)"` gives 2.15.0+cu132 and `.venv/bin/python -m pip show torch` gives 2.15.0; both are expected and both must hold. From 5C also `env/requirements.lock` |
| Triton | **3.9.0**, changeable only by a dated amendment - the same rule as Python. Separate invariant: this version must satisfy the Triton requirement declared by the installed torch wheel, measured 2026-11-23 as `triton~=3.9.0; platform_system == "Linux" and python_version < "3.16"`. Divergence is a stop and an amendment, never a silent follow | `.venv/bin/python -m pip show triton`, **and** `.venv/bin/python -c "import importlib.metadata as m; print([r for r in m.requires('torch') if 'triton' in r])"`. From 5C also `env/requirements.lock` |
| numpy | [UNKNOWN] - **not installed**, confirmed absent 2026-11-23; installed and pinned at 5C. Required, not cosmetic: Triton's interpreter imports numpy at `@jit` decoration time, so `TRITON_INTERPRET=1` cannot import without it and no Triton kernel can be tested off the GPU (RV-36) | `.venv/bin/python -m pip show numpy` |
| pandas · matplotlib | [UNKNOWN] - not installed; pinned at 5C if and when the analysis stages need them | `.venv/bin/python -m pip show pandas matplotlib` |
| pytest · ruff · mypy | [UNKNOWN] - none installed, confirmed absent 2026-11-23; pinned at 5C | `.venv/bin/python -m pip show pytest ruff mypy` |
| pip-tools | [UNKNOWN] - not installed, confirmed absent 2026-11-23; installed and pinned at 5C, floor >= 7.5.3 | `.venv/bin/pip-compile --version` |
| ninja | 1.13.2 | `.venv/bin/python -m pip show ninja` - without it `cpp_extension.load` raises and no CUDA extension builds at all |
| build · wheel · twine | 1.6.1 · 0.48.0 · 7.0.0 | `.venv/bin/python -m pip show build wheel twine` |
| setuptools | 84.2.1 | `.venv/bin/python -m pip show setuptools` |
| pre-commit | 4.7.0 | `.venv/bin/pre-commit --version` — it lives in the environment, not on the system path; the git hook still fires without activation because the generated hook holds an absolute path |
| gitleaks | 8.16.0-1build2 (apt) | `dpkg -s gitleaks \| grep '^Version:'` returns `Version: 8.16.0-1build2`, confirmed 2026-11-23. `gitleaks version` prints "version is set by build process" and no version at all |
| `TRITON_DEFAULT_FP_FUSION` | 1, set explicitly | run metadata, from stage 08 onwards. Until the harness exists, each spike that runs a Triton kernel sets it in that spike's own environment (4I, 4J) and the setting is visible in that spike's evidence file |

## Evidence
`results/env/torch_env.txt`, `results/env/deviceQuery.txt`,
`results/env/4B1_triton_add.txt`, `results/env/4B2_output_code.log` (2026-11-14);
`results/env/03_stack_precheck.txt` (2026-11-19);
`results/env/4K_environment_capture.txt` (2026-11-23), which is where every value in the pin
table above was last read. The lock itself does not exist yet and is produced at 5C, so no
row's check may cite it before then. Every "Checked by" above is a command that runs today,
with one exception stated in its own row: `TRITON_DEFAULT_FP_FUSION` is checked against run
metadata and therefore has no check until stage 08. `env/requirements.lock` becomes an
additional check from 5C onwards.

**Correction, 2026-11-23.** The pin table previously carried a row reading
`numpy · pandas · matplotlib | 2.5.5 · 3.1.1 · 3.11.2` under a heading stating that the pins
were measured on 2026-11-19. None of the three is installed on this machine and none of those
versions was measured. They are removed rather than restated.

The 2026-11-03 draft that AM-04 cites as the provenance of this record's decision criteria
is committed beside it as `ADR-0001-draft-2026-11-03.md`. It is a skeleton — criteria,
weights and "Final selections: TBD" — and is kept as provenance for the four weights only,
not as an earlier version of this decision. `../TECH-STACK.md` section 1 states what it
does and does not establish.

## Alternatives rejected
| Alternative | Why it lost |
|---|---|
| uv end to end: uv-managed interpreter, `uv venv`, `pyproject.toml` and `uv.lock` | The strongest reproducibility of the four and the most current practice, but it wants to own the interpreter. Adopting it discards the environment that produced the only GPU evidence this project has, reopens D-18, and costs several hours of the 15-hour spike budget for no gain in any measurement |
| uv as resolver, pip as installer | A lockfile resolved by one tool and installed by another can be internally consistent and still unreachable, because the two resolve markers and extras differently. The first place that would show is the fresh-distro rebuild at 5D — the one test that must not be the first run of anything |
| conda or mamba | A second package world to learn against a beginner Python baseline, and several gigabytes on a disk with no headroom to spare. The CUDA torch wheels come from pip in any case |
| Keep the pre-existing Python 3.12.16 environment | Unknown provenance; cleared under D-18 |
| Resolve the host compiler through the unversioned `gcc` alias | A distribution update moving the default to GCC 16 breaks every CUDA build with no change to project code, and the failure would surface inside a kernel stage with nothing in the diff to blame |

## Consequences
- **Easier:** the lock is a plain hash-pinned requirements file, which is what stage 05
  already names and what a stranger can read without learning a new tool.
- **Harder:** pip-tools does not manage the interpreter, so the Python version is a
  recorded fact rather than a locked one. Part 1 is the rule that compensates, and until
  `tests/test_environment.py` exists at stage 16 **nothing enforces it mechanically**. Until
  then it is held by two things only: part 1's acquisition path, checked at the 5D rebuild,
  and the two-command check in the Python row above.
- **Must do:** add numpy at the 05 lock, and not for tidiness - its absence prints a warning
  into every torch run and run logs are evidence, but more seriously Triton's interpreter
  imports it at decoration time, so without numpy no Triton kernel can be tested off the GPU
  (RV-36). Assert every pin in `tests/test_environment.py` at stage 16 so drift fails CI
  instead of changing a measurement quietly. Record the host-compiler version in each run's
  metadata, and record the enforced GPU power ceiling **as a series sampled across the run**
  rather than as a single reading: on 2026-11-23 it moved from 50 W to 30 W inside one
  twenty-second window with the mains adapter untouched.

## Fallback
If `pip-compile --generate-hashes` cannot resolve a lock containing torch from the PyTorch
index inside stage 05's 2-hour box, use `uv pip compile --generate-hashes`.

**This is the combination the alternatives table rejects** - resolved by one tool, installed
by another - and it is taken only under the condition that rejection demands: 5D installs from
that lock on a fresh distro and `pip freeze` must match it **before any measurement is taken**,
and a dated amendment records that the rejected combination is in force and why. Without that
condition the fallback puts the project into the state this record calls unreachable, and 5D is
where it would be discovered. It is written to be taken under time pressure, which is exactly
when nobody re-reads the alternatives table, so the condition travels with it here.

## Reversal trigger
Looked for at 5C and 5D, and thereafter in every run's metadata. Five triggers, one per
failure, because the original conflated them:

1. **The lock mechanism failed** - any of: the lock does not resolve; `pip install
   --require-hashes` fails on a fresh distro; `pip freeze` differs from the lock after a
   clean install.
2. **The selected compiler no longer satisfies nvcc** - `g++-15 -dumpversion` reports
   anything other than 15.
3. **The distribution default has moved** - `gcc -dumpversion` reports a major above 15.
   This does not by itself invalidate the pin. It means that any build path which forgot to
   name `g++-15` now breaks, so part 3 has become load-bearing rather than precautionary.
4. **A build did not use the selected compiler** - the host compiler recorded in a run's
   metadata does not read `g++-15`. No version string above can detect this, and it is the
   failure part 3 exists to prevent: `g++-15` can be installed and valid while something in
   the build path still resolves `gcc`.
5. **The telemetry instrument changed** - `nvidia-smi`'s own version reads anything other
   than 620.67.01. Every behaviour recorded under "verify the effect, not the return code"
   was measured on that binary; a change makes all of them unverified until re-checked, and
   no number already recorded is comparable to one taken after it without that re-check.
