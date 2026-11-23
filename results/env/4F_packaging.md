# 4F - packaging path (R9, V6, RV-12)

Spike package `fusiongap-spike4f` 0.0.1, built around the 4E copy kernel with
setuptools and torch's `BuildExtension`. Deliberately not named `fusiongap`:
the question is whether the artefact format is accepted, which does not depend
on the name, and uploading the real name to a throwaway index would claim it
there.

## V6 - is the name free?

| Index | HTTP status for /pypi/fusiongap/json | Meaning |
|---|---|---|
| pypi.org | 404 | free |
| test.pypi.org | 404 | free |

## The wheel

Built in about 3 minutes with `MAX_JOBS=1 CXX=g++-15 TORCH_CUDA_ARCH_LIST=7.5`
and `python -m build --wheel --no-isolation`:

    fusiongap_spike4f-0.0.1-cp314-cp314-linux_x86_64.whl   119854 bytes

It installs and works. Installed with `--no-deps` into an empty directory, it
contained `__init__.py` and `_C.cpython-314-x86_64-linux-gnu.so`, imported from
there, ran the kernel on 98437 elements and returned `torch.equal: True`.

Limitation stated rather than hidden: that install borrowed torch from the
project environment. A genuinely clean install, with dependency resolution,
belongs to 5D, which rebuilds everything from nothing.

## RV-12 - CONFIRMED BY MEASUREMENT, not by documentation

`twine upload --repository testpypi` returned 400, and with `--verbose` the
server gave its reason verbatim:

    Binary wheel 'fusiongap_spike4f-0.0.1-cp314-cp314-linux_x86_64.whl'
    has an unsupported platform tag 'linux_x86_64'.

## Consequence for ADR-0004

| Option | Status after 4F |
|---|---|
| (a) sdist, compiles at install | viable; requires nvcc on the user's machine |
| (b) wheel pinned to exact torch + CUDA | **not publishable** without a manylinux build chain (container plus auditwheel), and welded to one torch/CUDA pair besides |
| (c) JIT `load()` on first use | viable; first import pays the 193 s compile measured at 4E |
| (d) pure-Python Triton, CUDA extension optional | **leading candidate** - the published artefact carries no compiled code, so no platform tag problem exists |

ADR-0004 is decided at 4K with this evidence under it.

## Note for stage 31

The TestPyPI token used here was account-scoped, because a project-scoped token
cannot be created before the project exists on the server. On the real PyPI the
token must be project-scoped, created after the first upload. The release
checklist carries this.


## 2026-11-23 - the accepted arm, recorded

Everything above covers the rejected arm. The accepted arm was missing from this file, which
is where ADR-0004's evidence is read from. Added here, from readings taken 2026-11-23, none
of which needed a token.

Artefact: `spikes/4F/pured/dist/fusiongap_spiked-0.0.1-py3-none-any.whl`, 1780 bytes; source
committed at `spikes/4F/pured/`. Package name `fusiongap-spiked`, another throwaway name, for
the reason given at the top of this file.

**Published**, read from test.pypi.org's own JSON API, which needs no credential:

    HTTP 200
    name: fusiongap-spiked | version: 0.0.1
    file: fusiongap_spiked-0.0.1-py3-none-any.whl | bdist_wheel | 1780 bytes

**Contents** - no compiled object, and every path inside the package or its dist-info, which
is also the allowlist check ADR-0006's reversal trigger specifies:

    fusiongap_spiked/__init__.py                     828
    fusiongap_spiked-0.0.1.dist-info/METADATA        160
    fusiongap_spiked-0.0.1.dist-info/WHEEL            91
    fusiongap_spiked-0.0.1.dist-info/top_level.txt    17
    fusiongap_spiked-0.0.1.dist-info/RECORD          417

**Installs, does not import.** Into a clean venv holding neither torch nor Triton:

    install OK
    ModuleNotFoundError: No module named 'triton'

The spike's `pyproject.toml` declares no dependencies while its module imports triton and
torch at module scope. Recorded, not repaired: it is the exact failure REQ-F5 exists to
prevent, and under option (d) the install contract is carried entirely by declared
dependencies. ADR-0004 carries it as the decision's main cost; stage 15 declares them and 5D
is where the contract is first tested for real. TECH-STACK cell 8 is therefore DECIDED,
UNVERIFIED and not DECIDED.

**Three variables, not one.** The two arms differ in platform tag, package name and contents.
The conclusion does not rest on comparing them: the server stated its reason verbatim, so the
rejection is attributable on its own, and arm 2 is a positive control showing the pure-Python
format is accepted.
