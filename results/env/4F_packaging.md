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
