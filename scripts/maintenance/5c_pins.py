#!/usr/bin/env python3
"""Bring ADR-0001's pin table current after task 5C, 2026-11-26.

Five rows are replaced whole and one section is inserted. Each row is located
by a short prefix that must match exactly one line; if any anchor matches zero
times or more than once the script writes nothing and says which. A second run
therefore refuses, because the old anchors are gone.

Run from the repository root:
    python3 scripts/maintenance/5c_pins.py
"""
from __future__ import annotations

import pathlib
import sys

TARGET = pathlib.Path("docs/architecture/adr/ADR-0001-env-pins.md")

ROW_EDITS: list[tuple[str, str]] = [
    (
        "| pip-tools | ",
        r"| pip-tools | **7.7.0**, exactly, not a floor. 7.5.3 was pinned on 2026-11-25 to avoid an upstream defect in 7.6.x and **crashed on this machine's pip 26.3**: `TypeError: RequirementCommand.make_requirement_preparer() missing 1 required keyword-only argument: 'allow_editables'`, raised at `piptools/resolver.py` line 608 before any network access. Upstream declares 7.5.3 against pip 26.0, 7.6.0 against 26.1, 7.6.1 against 26.2; **7.7.0 requires pip >= 26.2.2, tests against 26.3, is compatible with click 8.5, and fixes the metadata-lookup defect 7.6.x carried** - this environment needs all four. pip and pip-tools can never be bumped independently (RV-40). D-26's `>= 7.5.3` floor is satisfied, so no change request was needed | **Two commands, both required, because the first cannot fail for an incompatibility.** Surface: `.venv/bin/pip-compile --version` prints `pip-compile, version 7.7.0`. Function: `printf 'filelock==4.2.10\n' > \"$HOME/.tmp/pc.in\" && .venv/bin/pip-compile --generate-hashes --allow-unsafe --rebuild -o \"$HOME/.tmp/pc.lock\" \"$HOME/.tmp/pc.in\" && grep -c -- '--hash=sha256:' \"$HOME/.tmp/pc.lock\"` must exit 0 and print `2`. The surface check alone is finding F57 |",
    ),
    (
        "| numpy | ",
        r"| numpy | **2.5.5** - resolved and hash-pinned in `env/requirements.lock` on 2026-11-26, and **still not installed**. It installs at 5D, which is the first time this pin is exercised. Required, not cosmetic: Triton's interpreter imports numpy at `@jit` decoration time, so `TRITON_INTERPRET=1` cannot import without it and no Triton kernel can be tested off the GPU (RV-36). The absence is still observable - importing torch on 2026-11-26 emitted `UserWarning: Failed to initialize NumPy: No module named 'numpy'` | `grep -n '^numpy==' env/requirements.lock` gives the pin today; `.venv/bin/python -m pip show numpy` gives the installation, and will not answer until 5D |",
    ),
    (
        "| pytest · ruff · mypy | ",
        r"| pytest · ruff · mypy | **9.2.0 · 0.17.6 · 2.4.1** - resolved and hash-pinned in `env/requirements.lock` on 2026-11-26, **none installed**. They install at 5D. Versions chosen by the resolver, not by hand: no compatibility evidence existed for any of the three on Python 3.14.4, and writing a version that has not been installed is finding F13 repeated. mypy 2.4.1 brings two compiled dependencies new to this project, `librt` and `ast-serialize` | `grep -n -E '^(pytest|ruff|mypy)==' env/requirements.lock` today; `.venv/bin/python -m pip show pytest ruff mypy` from 5D |",
    ),
    (
        "| torch | ",
        r"| torch | 2.15.0+cu132 at runtime; the distribution metadata reports **2.15.0**, and the lock entry reads `torch==2.15.0`. **The index question is answered, 2026-11-26.** The version string *is* a discriminator after all: for linux x86_64, plain `2.15.0` is published on PyPI and on neither PyTorch index - `/whl/cu132` publishes only `2.15.0+cu132` (21 files) and `/whl/cpu` only `2.15.0+cpu` plus plain-versioned macOS arm64 wheels (36 files), both read on 2026-11-26. PyPI publishes exactly one matching file, `torch-2.15.0-cp314-cp314-manylinux_2_28_x86_64.whl`, sha256 `1412c79b0338ea61fa31e74a59d74e412c56307e226d3c6e61ccd6d4613ffc3f`, 539,172,352 bytes. `torch==2.15.0` therefore means the CUDA 13.2 build **because that is PyPI's default build for this version**, not because of anything in the lock - and there is no `+cu132` anywhere in it, which is correct. **The lock does not record the index** (F59), so D-45 lives in `env/requirements.in`'s header and in this record. What is *not* proved is that the bytes installed in this venv are that artefact: there is no `direct_url.json` and pip records no wheel digest. The `--require-hashes` install at 5D is that test, and a mismatch there means the index, not the lock (F55) | `.venv/bin/python -c \"import torch; print(torch.__version__)\"` gives 2.15.0+cu132 and `.venv/bin/python -m pip show torch` gives 2.15.0; both expected, both must hold. Plus `grep -n -A1 '^torch==' env/requirements.lock` |",
    ),
    (
        "| pre-commit | ",
        r"| pre-commit | 4.7.0 - it lives in the environment, not on the system path; the git hook still fires without activation because the generated hook holds an absolute path. **From 2026-11-26 it carries D-42's attribution guard as well as gitleaks**, and that needs two installations, not one: `pre-commit install` wires the `pre-commit` stage, `pre-commit install --hook-type commit-msg` wires the message guard, **and the second is not installed by the first**. Without it the most common form of breach - a trailer appended to the message - goes unchecked (F63) | `.venv/bin/pre-commit --version`, **and** `ls .git/hooks/` must list both `pre-commit` and `commit-msg`. The version alone does not tell you whether either is wired |",
    ),
]

SECTION_ANCHOR = "## Evidence"

NEW_SECTION = r"""### What each check reads - added 2026-11-26 after F57

A pin whose check reads a tool's **surface** can pass on a tool that does not work. That is not
hypothetical. On 2026-11-25 the pip-tools row was approved as verified on the evidence of
`pip-compile --version`, a command that prints a string and exits 0 whether or not the resolver
runs. It did not run, and the approval commit claimed every pin had been "read back by its own
row's command and matched". The pip-tools row above now carries a surface check and a functional
one, labelled as such.

| Row | What its check reads | Exercised in anger? |
|---|---|---|
| `nvidia-smi` | function | Yes - 280 samples across the D-41 A/B |
| build · wheel · twine | surface | Yes, indirectly - the 4F two-arm upload experiment put all four through a real publish |
| pre-commit | surface, plus a wiring check from 2026-11-26 | Yes - the hooks fire on every commit |
| ninja | surface | Probably - the CUDA extension builds at 4E and 4G go through it, but nothing in this record states that. [VERIFY at 15] |
| pip-tools | **both**, from 2026-11-26 | Yes - the functional check is in the row |
| numpy · pytest · ruff · mypy | not installed | No - first exercised at 5D |

**Owed:** every row gains this as a fourth column rather than a footnote. Deferred to 5B's pass over
this record.

### The lock, from 5C

`env/requirements.lock` is what these pins resolve into: **82 packages, 1152 hashes**, produced on
2026-11-26 by

    pip-compile --generate-hashes --strip-extras --allow-unsafe \
                --constraint env/measured.txt \
                --output-file env/requirements.lock env/requirements.in

`env/measured.txt` is the environment as measured that day, used as a constraint so the lock
reproduces what was measured rather than what was newest; without it eight transitive packages
resolved newer, one of them `cuda-pathfinder`, which sits in the CUDA library discovery path (F62).
`--allow-unsafe` is required, not optional: without it pip and setuptools are commented out and the
lock fails under `--require-hashes`, where one unpinned entry fails the whole install (F40, F61).
`--strip-extras` is explicit because pip-tools makes it the default at 8.0.0 and the same input
would otherwise produce a differently shaped lock across that boundary (F58).

The resolve fetched **metadata only** - 82 `.whl.metadata` files, no package archives, both volumes
unchanged before and after. That is D-45 working: PyPI exposes a JSON metadata API and
`download.pytorch.org` does not, so an extra index would have forced every platform wheel of every
pin it served to be downloaded.

**5D's cost, Python side only:** download **3,063,596,226 bytes (2.85 GiB)**, computed by
`scripts/env/budget.py` and recorded in `results/env/5C_disk_budget.txt`; installed footprint
**5.28 GiB**, measured from the venv holding 72 of the 82; pip's cache retains every wheel it
fetches, so the total is **8.13 GiB** unless the cache is disabled. **5D installs with
`--no-cache-dir`** - it removes 2.85 GiB, and a rebuild warmed by the old machine's cache is not a
fresh-distribution rebuild. The Ubuntu root filesystem, the apt packages and the CUDA toolkit are
not in that figure and remain [UNKNOWN] here.

"""


def main() -> int:
    if not TARGET.is_file():
        print(f"REFUSED: {TARGET} not found. Run from the repository root.", file=sys.stderr)
        return 1

    lines = TARGET.read_text(encoding="utf-8").splitlines(keepends=True)
    text_joined = "".join(lines)

    # --- assert every anchor before changing anything -------------------
    problems: list[str] = []
    hits: dict[str, int] = {}
    for prefix, _ in ROW_EDITS:
        idxs = [i for i, ln in enumerate(lines) if ln.startswith(prefix)]
        hits[prefix] = len(idxs)
        if len(idxs) != 1:
            problems.append(f"row anchor {prefix!r} matched {len(idxs)} lines, need exactly 1")
    n_sections = text_joined.count(SECTION_ANCHOR)
    if n_sections != 1:
        problems.append(f"section anchor {SECTION_ANCHOR!r} matched {n_sections}, need exactly 1")

    print(f"file: {TARGET}  lines: {len(lines)}")
    for prefix, count in hits.items():
        print(f"  anchor {prefix!r:32} -> {count}")
    print(f"  anchor {SECTION_ANCHOR!r:32} -> {n_sections}")

    if problems:
        print("\nREFUSED, nothing written:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1

    # --- apply -----------------------------------------------------------
    for prefix, new_row in ROW_EDITS:
        i = next(i for i, ln in enumerate(lines) if ln.startswith(prefix))
        lines[i] = new_row.rstrip("\n") + "\n"

    out = "".join(lines).replace(SECTION_ANCHOR, NEW_SECTION + SECTION_ANCHOR, 1)
    TARGET.write_text(out, encoding="utf-8")

    after = out.splitlines()
    print(f"\nWROTE {TARGET}: {len(lines)} -> {len(after)} lines")
    print(f"  rows replaced: {len(ROW_EDITS)}")
    print(f"  section inserted before: {SECTION_ANCHOR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
