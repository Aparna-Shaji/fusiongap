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

## Decision
Four parts.

1. **Python.** The system interpreter, 3.14.4, used through a stdlib `venv` at
   `~/projects/fusiongap/.venv`, outside the repository. The Python version changes only
   by a dated amendment, because changing it invalidates the 4A and 4B evidence and every
   GPU measurement taken after it. This closes RV-16.
2. **Dependency pinning.** `pip-tools >= 7.5.3`. `pip-compile --generate-hashes` produces
   `env/requirements.lock`; installation is always
   `pip install --require-hashes -r env/requirements.lock`. The 7.5.3 floor is not
   cosmetic: that release declares Python 3.14 support, is compatible with pip 26, and
   fixes a defect where `pip-compile` dropped index-URL options while looking up hashes,
   which broke resolution for packages available only from an extra index — which is
   exactly how torch is published.
3. **Host compiler.** `g++-15` is named explicitly wherever a host compiler is selected,
   never the unversioned `gcc` alias. nvcc 13.2 errors above GCC major 15 and this
   distribution's default is 15.2.0, so there is no headroom and an ordinary system
   update would otherwise break every CUDA build silently (RV-28).
4. **Pins**, as measured on 2026-11-19. Blank entries are filled at 5A and frozen there.

| Layer | Pin | Checked by |
|---|---|---|
| Windows build | [UNKNOWN] — recorded at 5A | `ver` on Windows |
| WSL kernel | 6.18.58.1 | `uname -r` |
| Ubuntu | 26.04.1 LTS | `lsb_release -d` |
| NVIDIA KMD (Windows-side) | 621.01 | `nvidia-smi` |
| CUDA UMD | 13.5 | `nvidia-smi` |
| CUDA toolkit | 13.2.2-1, nvcc 13.2.86, from the wsl-ubuntu repository | `nvcc --version` |
| Host compiler | g++-15 (15.2.0-16ubuntu1) | `g++-15 --version` |
| Python | 3.14.4, system interpreter | `python --version` |
| torch | 2.15.0+cu132 | `env/requirements.lock` |
| Triton | 3.9.0 — whatever the torch wheel pins; never chosen separately | `env/requirements.lock` |
| numpy · pandas · matplotlib | 2.5.5 · 3.1.1 · 3.11.2 | `env/requirements.lock` |
| pytest · ruff · mypy | [UNKNOWN] — pinned at 5C | `env/requirements.lock` |
| pre-commit | 4.7.0 | `.venv/bin/pre-commit --version` — it lives in the environment, not on the system path; the git hook still fires without activation because the generated hook holds an absolute path |
| gitleaks | 8.16.0-1build2 (apt) | `gitleaks version` |
| `TRITON_DEFAULT_FP_FUSION` | 1, set explicitly | run metadata |

## Evidence
`results/env/torch_env.txt`, `results/env/deviceQuery.txt`,
`results/env/4B1_triton_add.txt`, `results/env/4B2_output_code.log` (2026-11-14);
`results/env/03_stack_precheck.txt` (2026-11-19). The lock itself does not exist yet and
is produced at 5C; until then every pin above is a recorded observation, not a lock entry.

## Alternatives rejected
| Alternative | Why it lost |
|---|---|
| uv end to end: uv-managed interpreter, `uv venv`, `pyproject.toml` and `uv.lock` | The strongest reproducibility of the four and the most current practice, but it wants to own the interpreter. Adopting it discards the environment that produced the only GPU evidence this project has, reopens D-18, and costs roughly 4.5 hours of the 15-hour spike budget for no gain in any measurement |
| uv as resolver, pip as installer | A lockfile resolved by one tool and installed by another can be internally consistent and still unreachable, because the two resolve markers and extras differently. The first place that would show is the fresh-distro rebuild at 5D — the one test that must not be the first run of anything |
| conda or mamba | A second package world to learn against a beginner Python baseline, and several gigabytes on a disk losing about 2 GB a day. The CUDA torch wheels come from pip in any case |
| Keep the pre-existing Python 3.12.16 environment | Unknown provenance; cleared under D-18 |
| Resolve the host compiler through the unversioned `gcc` alias | A distribution update moving the default to GCC 16 breaks every CUDA build with no change to project code, and the failure would surface inside a kernel stage with nothing in the diff to blame |

## Consequences
- **Easier:** the lock is a plain hash-pinned requirements file, which is what stage 05
  already names and what a stranger can read without learning a new tool.
- **Harder:** pip-tools does not manage the interpreter, so the Python version is a
  recorded fact rather than a locked one. Part 1 is what compensates for that.
- **Must do:** add numpy at the 05 lock — its absence prints a warning into every torch
  run and run logs are evidence; assert every pin in `tests/test_environment.py` at
  stage 16 so drift fails CI instead of changing a measurement quietly; record the
  host-compiler version in each run's metadata alongside the power limit.

## Fallback
If `pip-compile --generate-hashes` cannot resolve a lock containing torch 2.15.0+cu132
from the PyTorch index inside stage 05's 2-hour box, use `uv pip compile
--generate-hashes`, which emits the same requirements format and changes neither the
installer nor the lock format. Record it as a dated amendment.

## Reversal trigger
Looked for at 5C and 5D. Any of: the lock does not resolve; `pip install
--require-hashes` fails on a fresh distro; `pip freeze` differs from the lock after a
clean install; `gcc -dumpversion` reports a major above 15.
