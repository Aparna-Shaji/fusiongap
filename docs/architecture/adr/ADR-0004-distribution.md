# ADR-0004 — Distribution model: the published artefact is pure Python

Status: proposed
Date: 2026-11-23
Owner stage: 04 → frozen at 05

## Context
REQ-F5 requires `pip install fusiongap` to work on a clean CUDA machine, and REQ-Q3 makes
the install part of the reproducibility contract, so how this library is distributed is a
decision rather than a default. What forces it: the project ships two implementations of
every kernel. The Triton arm is compiled by Triton on the user's machine at first call. The
CUDA C++ arm is compiled ahead of time by nvcc and is therefore platform-specific and locked
to one torch build and one CUDA version. Risk R9 named that exposure before any evidence
existed, and review finding RV-12 predicted that a wheel carrying compiled code would be
refused by a public index. Hard constraints: a $0 budget, so no paid build infrastructure;
and 193 s with a 2.64 GiB host-memory peak per `.cu` translation unit, measured at 4E, so
compiling at install time is not free for the user either.

**On decision identifiers.** `D-nn` and `CR-nn` in this record refer to entries in the
project's state file, which is working memory and is not part of this repository. They are
secondary references. Everything load-bearing here rests on the evidence paths named below.

## Decision
The published distribution is a **pure-Python wheel tagged `py3-none-any`**, containing no
compiled extension. Three parts.

1. **Triton kernels ship as source** and are compiled by Triton on the user's machine at
   first call.
2. **The CUDA C++ extension is not published.** It is an optional component built from this
   repository by anyone who wants it. In this project it exists to be measured against the
   Triton arm, not to be distributed.
3. **Declared dependencies carry the whole install contract**, because nothing in the
   artefact is pre-built.

Specific enough for a command to check, at 4F and again at stage 15:

    python -m build --wheel
      -> exactly one file, matching *-py3-none-any.whl

    python -c "import zipfile; print([i.filename for i in
               zipfile.ZipFile(W).infolist()])"
      -> no path ending .so, and every path inside fusiongap/ or
         fusiongap-<version>.dist-info/   (the same allowlist as ADR-0006)

## Evidence
`results/env/4F_packaging.md` (2026-11-22, extended 2026-11-23). Two artefacts were uploaded
to TestPyPI with the same account and the same `twine` command.

**Arm 1, rejected.** `fusiongap_spike4f-0.0.1-cp314-cp314-linux_x86_64.whl`, 119854 bytes,
built around the 4E CUDA copy kernel. `twine upload --repository testpypi` returned HTTP 400
and, with `--verbose`, the server gave its reason verbatim: the binary wheel has an
unsupported platform tag `linux_x86_64`.

**Arm 2, accepted and published.** `fusiongap_spiked-0.0.1-py3-none-any.whl`, 1780 bytes,
carrying a Triton add kernel as source. Confirmed from outside the project on 2026-11-23 by
test.pypi.org's own JSON API — HTTP 200, one file, `bdist_wheel`, 1780 bytes — which needs no
credential and is therefore checkable by a stranger. Its contents are `__init__.py` plus five
`dist-info` entries and no compiled object.

**Three variables, not one.** The two arms differ in platform tag, package name and contents.
This is deliberately not presented as a single-variable comparison, and the conclusion does
not rest on one: the server stated the mechanism verbatim, so the rejection is attributable on
its own, and arm 2 is a positive control showing the pure-Python format is accepted.

**What arm 2 does not show.** Installed into a clean virtual environment with neither torch
nor Triton present, it installs and then fails to import with
`ModuleNotFoundError: No module named 'triton'`, because its `pyproject.toml` declares no
dependencies while its module imports triton and torch at module scope. Measured 2026-11-23.
That is the install contract failing, and it is recorded rather than repaired — see
Consequences.

## Alternatives rejected
| Alternative | Why it lost |
|---|---|
| (a) Source distribution, compiled at install | Every user needs nvcc and a matching CUDA toolkit, and pays 193 s per translation unit at a 2.64 GiB host-memory peak (4E). An install that requires a toolchain is not `pip install` |
| (b) Pre-compiled binary wheel pinned to one torch and CUDA pair | Not publishable as measured: a bare `linux_x86_64` tag is refused, and a manylinux tag requires a container build chain plus auditwheel, which a $0 budget does not reach. Even built, it is welded to one torch/CUDA pair and breaks on the next release of either |
| (c) JIT compilation of the CUDA extension on first import | Viable, and kept as the fallback. It does not remove the 193 s, it moves it to the user's first run, and it still requires nvcc on the machine exactly as (a) does |
| (e) Ship the CUDA extension as a separate platform-specific package | Considered at 4K and lost on (b)'s mechanism — the second package has the same platform tag problem — with a second release process and a version-skew pair to keep in step on top of it |

## Consequences
- **Easier:** one artefact serves every Linux CUDA machine, because there is no platform tag
  to match. No container, no auditwheel, no build infrastructure, and nothing to rebuild when
  torch or CUDA moves. The artefact is small; the spike's was 1780 bytes.
- **Harder, and this is the decision's real cost:** nothing ships pre-built, so the entire
  install contract moves into declared dependencies, where a mistake is silent until import.
  The spike demonstrates the failure. Finding F15 makes it harder than it looks: this
  project's torch reports distribution metadata version `2.15.0`, which on a public index does
  not by itself name the CUDA build in use here, so a declared dependency on torch must reckon
  with which index resolves it.
- **Harder:** the Triton compile moves to the user's first call. It is far cheaper than nvcc,
  but it is not free and it requires a GPU present at first use.
- **Must do:** stage 15's packaging configuration declares every runtime dependency and names
  exactly what ships, checked by ADR-0006's allowlist trigger; 5D installs from the lock on a
  fresh distribution and is the first real test of the install contract; stage 31's release
  checklist carries 4F's note that the real PyPI token must be project-scoped, which can only
  be created after the first upload.

## Fallback
If the Triton arm cannot ship as source — for instance if a future Triton requires a build
step at install time — fall back to option (c), JIT compilation on first import, which keeps
the artefact pure-Python and moves the compile to first use. Record it as a dated amendment.
Option (b) is not a fallback: it is unpublishable on the evidence above.

## Reversal trigger
Looked for at 4F whenever the packaging is rebuilt, and again at 27C.
1. `python -m build --wheel` produces any file not matching `*-py3-none-any.whl`.
2. The built wheel contains any path ending `.so`, or any path outside `fusiongap/` and
   `fusiongap-<version>.dist-info/` — the same check as ADR-0006's reversal trigger.
3. A clean-environment `pip install fusiongap` followed by `import fusiongap` raises
   `ModuleNotFoundError` — the failure arm 2 reproduced on 2026-11-23.
