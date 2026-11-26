#!/usr/bin/env python3
"""Bring the three public registers current after task 5C, 2026-11-26.

Eleven edits across three files. Four kinds, each with its own assertion:

  append_cell     append text inside a table row's LAST cell, located by a
                  row prefix that must match exactly one line
  append_eof      append a whole row at the end of the file
  insert_before   insert rows immediately before a unique anchor

EVERY edit also asserts its own distinctive text is ABSENT from the file
first. That is finding F67's lesson: scripts/maintenance/5c_pins.py refused a
second run only because two inserted rows happened to collide with two
anchors, and its section insert had no "already applied" check at all.

Nothing is written unless every assertion passes. Run from the repository root:
    python3 scripts/maintenance/5c_registers.py
"""
from __future__ import annotations

import pathlib
import sys

RISK = "docs/project/RISK-REGISTER.md"
VERIF = "docs/project/VERIFICATION-LOG.md"
STATUS = "docs/project/STATUS-LOG.md"

# --------------------------------------------------------------------------
# content
# --------------------------------------------------------------------------

RV40 = (
    "| RV-40 | MED | pip-tools calls private pip internals, so its version is coupled to pip's and "
    "the two can never be bumped independently. Three consecutive pip-tools releases exist for no "
    "reason other than tracking pip 26.0, 26.1 and 26.2, and 7.7.0 now hard-requires pip >= 26.2.2. "
    "At 5D a fresh distribution installs whatever pip its Python ships with, and if that pip is "
    "newer than the pinned pip-tools supports, 5D fails on the tool rather than on the lock "
    "| `pip-compile` raising a `TypeError` from inside `piptools/`, or a pip upgrade the pinned "
    "pip-tools does not declare support for | 5C record - 5D test - every pip bump "
    "| Both versions are pinned together in `env/requirements.lock` and in ADR-0001, and the "
    "pip-tools pin row carries a functional check rather than `--version`, which cannot detect an "
    "incompatibility. 5D installs the lock, which pins pip itself because the resolve used "
    "`--allow-unsafe`, so the rebuilt environment gets the pinned pair rather than the "
    "distribution's | OPEN: raised 2026-11-26 after pip-tools 7.5.3, pinned the previous day, "
    "crashed on this machine's pip 26.3 with `make_requirement_preparer() missing 1 required "
    "keyword-only argument: 'allow_editables'` before any network access (finding F57). 7.7.0 "
    "installed and verified by a functional resolve, not by `--version` |"
)

RV29_ADD = (
    "2026-11-26: the criterion gains a second clause. `pre-commit install` wires only the "
    "`pre-commit` stage; D-42's commit-message guard needs `pre-commit install --hook-type "
    "commit-msg` as a separate command, and without it the most common form of attribution breach "
    "goes unchecked (F63). Gate 05's rebuild criterion therefore checks that **both** "
    "`.git/hooks/pre-commit` and `.git/hooks/commit-msg` exist on the rebuilt environment and that "
    "each one fires"
)

RV30_ADD = (
    "2026-11-26: the cost F45 raised is now sized. `scripts/env/budget.py` computes the 5D download "
    "at 3,063,596,226 bytes (2.85 GiB) from the lock's own pins against PyPI's reported file sizes, "
    "with the installed footprint measured at 5.28 GiB and pip retaining every wheel it fetches - "
    "so 8.13 GiB on the Python side, or 5.28 GiB if 5D installs with `--no-cache-dir`, which it "
    "should. Evidence `results/env/5C_disk_budget.txt` (V26). The Ubuntu root filesystem, the apt "
    "packages and the CUDA toolkit are not in that figure and remain [UNKNOWN]. Readings that day: "
    "65 GB at 09:20, 63 GB at 15:30, 62 GB at 20:03, with nothing downloaded by this project "
    "between them - a 3 GB wander across eleven hours, which is the noise this row exists to "
    "describe"
)

RV36_ADD = (
    "2026-11-26: numpy is resolved and hash-pinned at **2.5.5** in `env/requirements.lock` and is "
    "**still not installed** - the mitigation above says \"installed at 5C\", which was the plan "
    "and is not what happened. It installs at 5D, which is the first time this pin is exercised. "
    "The absence remains observable: importing torch that day emitted `UserWarning: Failed to "
    "initialize NumPy: No module named 'numpy'`"
)

V23 = (
    "| V23 | pip-tools 7.5.3 satisfies this project's configuration: Python 3.14 support, operation "
    "under pip 26.3, and the index-URL fix | **VERIFIED (no)** on the clause that matters | Three "
    "claims were tagged `[VERIFY at 5C]` in ADR-0001 on 2026-11-23. **(a)** Python 3.14 support: "
    "CONFIRMED - upstream tests against 3.14 and 3.14t and marks them supported in the core "
    "packaging metadata. **(c)** The index-URL fix: CONFIRMED - 7.5.3's changelog records that "
    "`pip-compile` lost index URL options when looking up hashes, citing issues 2220, 2294 and "
    "2305, and the pull request was milestoned to 7.5.3. **(b) Operation under pip 26.3: FALSE, "
    "measured.** `pip-compile` crashes with `TypeError: RequirementCommand."
    "make_requirement_preparer() missing 1 required keyword-only argument: 'allow_editables'` at "
    "`piptools/resolver.py` line 608, before any network access. Upstream declares 7.5.3 against "
    "pip 26.0, 7.6.0 against 26.1, 7.6.1 against 26.2. The claim had been recorded CONFIRMED on "
    "the evidence of `pip-compile --version`, a command that prints a string and exits 0 whether "
    "or not the resolver runs (finding F57). Resolved by pinning **7.7.0**, which requires pip "
    ">= 26.2.2, tests against 26.3, is compatible with click 8.5, and fixes the metadata-lookup "
    "defect 7.6.x carried · 2026-11-26 | 5C; ADR-0001; RV-40 |"
)

V24 = (
    "| V24 | The torch wheel this project installed is published on PyPI and on neither PyTorch "
    "index, so the version string identifies it after all | VERIFIED | For linux x86_64, plain "
    "`2.15.0` exists on PyPI and nowhere else: `download.pytorch.org/whl/cu132` publishes only "
    "`2.15.0+cu132` (21 files) and `/whl/cpu` only `2.15.0+cpu` plus plain-versioned macOS arm64 "
    "wheels (36 files), both listings read 2026-11-26. PyPI publishes exactly one file matching "
    "this interpreter and platform: `torch-2.15.0-cp314-cp314-manylinux_2_28_x86_64.whl`, sha256 "
    "`1412c79b0338ea61fa31e74a59d74e412c56307e226d3c6e61ccd6d4613ffc3f`, **539,172,352 bytes** - "
    "measured twice by independent routes, a `curl -sSIL` against the simple index and "
    "`scripts/env/budget.py` against the JSON API, identical to the byte. Settles finding F52, "
    "whose premise was that the version string could not discriminate. **Not proved:** that the "
    "bytes in the current venv are that artefact - there is no `direct_url.json` and pip records "
    "no wheel digest. The `--require-hashes` install at 5D is that test, and a mismatch there "
    "means the index, not the lock · 2026-11-26 | 5C (F52); origin confirmed at 5D |"
)

V25 = (
    "| V25 | Every hash in `env/requirements.lock` matches a file the index currently publishes, "
    "and every file the index publishes for a pinned version is in the lock | VERIFIED | 1152 "
    "hashes across 82 packages compared in both directions against PyPI's JSON metadata by "
    "`scripts/env/budget.py`: **not one mismatch**. torch alone has 28 files on PyPI and the lock "
    "holds all 28. This is the check finding F55 called for - a published digest can disagree with "
    "the file it names, as it did in an upstream incident on PyTorch's nightly index - and on the "
    "index this lock actually uses it does not occur. F55 therefore narrows to "
    "`download.pytorch.org`, which D-45 means this project never queries · "
    "`results/env/5C_disk_budget.txt` · 2026-11-26 | 5C; re-run whenever the lock changes |"
)

V26 = (
    "| V26 | The 5D rebuild's disk cost is known before the import, as ENVIRONMENT.md section 3 "
    "step 1 requires | VERIFIED for the Python side only | Download **3,063,596,226 bytes "
    "(2.85 GiB)**, computed from the lock's pins against PyPI's reported file sizes with no file "
    "downloaded: 82 packages, 79 selected exactly, 3 ambiguous, 0 failed, spread 12.9 MB or "
    "0.42 %. All three ambiguities are a pure-Python fallback wheel competing with a compiled "
    "platform wheel, and pip prefers the more specific tag, so the maximum is the correct reading "
    "(finding F66). Installed footprint **5.28 GiB**, measured from the venv holding 72 of the 82, "
    "of which three packages are 96 %: the nvidia payload 2.98 GiB, torch 1.12 GiB, triton "
    "0.97 GiB. pip retains every wheel it fetches, so the total is **8.13 GiB** unless the cache "
    "is disabled - **5D installs with `--no-cache-dir`**, which removes 2.85 GiB and is correct in "
    "any case, because a rebuild warmed by the old machine's cache is not a fresh-distribution "
    "rebuild. The Ubuntu root filesystem, apt packages and the CUDA toolkit are **not** in this "
    "figure and remain [UNKNOWN] · `scripts/env/budget.py`, `results/env/5C_disk_budget.txt` · "
    "2026-11-26 | 5C (F45); completed when ENVIRONMENT.md section 3 is costed |"
)

V15_ADD = (
    "2026-11-26: numpy's resolver-reported 2.5.5 is now hash-pinned in `env/requirements.lock` and "
    "is still not installed; pandas and matplotlib are in neither the lock nor the environment"
)

V18_ADD = (
    "**2026-11-26: the floor met this configuration and failed it.** pip-tools 7.5.3 crashes under "
    "pip 26.3 (V23, finding F57); 7.7.0 is installed and functionally verified. The warning in "
    "this cell - that the 7.5.3 claim was live configuration carrying no source - was correct"
)

STATUS_25 = (
    "| 2026-11-25 Wed | WD12 | Stage 05 opened. **5A CLOSED:** every installed pin read back "
    "against the machine by its own row's command, the `nvidia-smi` instrument pinned as the "
    "source of every telemetry number (F49), and the 5D disk budget made a precondition of the "
    "import (F45) - `0bb336c`. **F43 CLOSED:** the public risk register was not the register, "
    "holding 23 of 38 RV identifiers with five of the absent still open and one of them a hard "
    "non-waivable condition on gate 05; five rows restored, RV-17 accounted for by an "
    "evidence-bounded note, and D-44 ruled how a row with no source text is restored - `fa28b44`. "
    "V19 to V22 and the 24 November entry committed (`043a588`); RV-38 and RV-39 added "
    "(`8991698`). **PyTorch defines no host-compiler bounds for CUDA 13.2** (V22), discharging "
    "RV-27's torch-level half by reading the source. **The attribution guard protecting D-42 was "
    "found unsound twice and proved once:** it matched bare substrings and fired on a legitimate "
    "path, and it read a file nothing in the project creates, so on a missing file it reported a "
    "pass with no input (F46); the repair's `^\\+[^+]` anchor then consumed the first character of "
    "every added line, so a trailer at column 1 passed (F48). The third version was proved against "
    "four planted cases. 5B's document review stopped on a FAIL: the ADR-0002 review carried no "
    "line numbers, attributed a verification to the mentor that was never run, and recorded a "
    "known defective reversal trigger as \"very precise\". Fourteen findings, six of them the "
    "mentor's own in one family (P-25). Four commits | 5B reading -> 5C the hash-pinned lock "
    "| 7.0 h stage, 0.0 h parallel - reported rather than unreported, which makes RV-23's trigger "
    "readable for the first time, and it reads TRUE |"
)

STATUS_26 = (
    "| 2026-11-26 Thu | WD13 | **5C's core is complete: `env/requirements.lock` exists, is "
    "verified and is pushed.** The index question was settled by measurement rather than by a "
    "ruling - plain `torch==2.15.0` for linux x86_64 is published on PyPI and on neither PyTorch "
    "index, so the version string discriminates and D-45 pins PyPI as the sole index (V24, F52). "
    "That ruling also bounds the cost: PyPI exposes a JSON metadata API and `download.pytorch.org` "
    "does not, so an extra index would have forced every platform wheel of every pin it served to "
    "be downloaded. The resolve fetched **metadata only** - 82 `.whl.metadata` files, no archives, "
    "both volumes unchanged before and after. **Two defects stopped it first.** pip-tools 7.5.3, "
    "pinned the previous day, does not run on this machine's pip 26.3 at all, and the record had "
    "marked that claim CONFIRMED on the evidence of `pip-compile --version`, a command that cannot "
    "fail for an incompatibility (F57, V23); 7.7.0 fixes both the crash and the defect 7.5.3 was "
    "pinned to avoid. The first lock then declared itself possibly uninstallable: `--allow-unsafe` "
    "was missing, so pip and setuptools were commented out, and under hash-checking one unpinned "
    "entry fails the whole install (F61, F40). The second drifted eight transitive packages newer "
    "than measured, one of them `cuda-pathfinder` in the CUDA discovery path, so `env/measured.txt` "
    "was added as a resolve constraint (F62). Final: **82 packages, 1152 hashes**, and the "
    "old-versus-new diff showed exactly the ten predicted changes and nothing else - `b402e1e`. "
    "**D-42's guard was found to be enforced by the mentor's memory and nothing else** (F63): four "
    "of its six steps were omitted on that very commit. It is now two pre-commit hooks, proved "
    "against fifteen assertions including real `git commit` refusals in a throwaway clone, with "
    "the commit count as the assertion that cannot be faked - `69ee20c`. **F45 answered for the "
    "Python side:** `scripts/env/budget.py`, oracle-validated against a figure measured twice by "
    "independent routes, puts the 5D download at 2.85 GiB and the total at 8.13 GiB (V26) - "
    "`a281b7a`. ADR-0001 brought current, five of its rows factually wrong, one being the row F57 "
    "is about - `4fc1eaa`. Fourteen findings (F54 to F67), three process notes (P-29 to P-31), one "
    "decision (D-45), one risk (RV-40). Four commits | `scripts/env/setup.sh` and `capture.sh` -> "
    "5B's reading -> 5D | Builder's figure owed at the close; the session spanned 09:07 to the "
    "evening and elapsed is not worked (P-19). Apportionment between boxed 5C work and unboxed "
    "instrument repair owed at the 2026-11-28 review under D-30, on D-38's precedent |"
)

# --------------------------------------------------------------------------
# edit plan
# --------------------------------------------------------------------------

EDITS = [
    # file,   kind,            locator,                  payload,  absent-guard
    (RISK,  "append_eof",    None,                       RV40,     "| RV-40 |"),
    (RISK,  "append_cell",   "| RV-29 | ",               RV29_ADD, "criterion gains a second clause"),
    (RISK,  "append_cell",   "| RV-30 | ",               RV30_ADD, "cost F45 raised is now sized"),
    (RISK,  "append_cell",   "| RV-36 | ",               RV36_ADD, "which was the plan and is not what happened"),
    (VERIF, "append_eof",    None,                       V23,      "| V23 |"),
    (VERIF, "append_eof",    None,                       V24,      "| V24 |"),
    (VERIF, "append_eof",    None,                       V25,      "| V25 |"),
    (VERIF, "append_eof",    None,                       V26,      "| V26 |"),
    (VERIF, "append_cell",   "| V15 | ",                 V15_ADD,  "pandas and matplotlib are in neither the lock"),
    (VERIF, "append_cell",   "| V18 | ",                 V18_ADD,  "floor met this configuration and failed it"),
    (STATUS, "insert_before", "\n\n## Notes",            STATUS_25 + "\n" + STATUS_26, "| 2026-11-26 Thu |"),
]


def main() -> int:
    files: dict[str, list[str]] = {}
    problems: list[str] = []

    for path in (RISK, VERIF, STATUS):
        p = pathlib.Path(path)
        if not p.is_file():
            print(f"REFUSED: {path} not found. Run from the repository root.", file=sys.stderr)
            return 1
        files[path] = p.read_text(encoding="utf-8").splitlines(keepends=True)

    print("checking every edit before writing anything\n")
    for path, kind, locator, payload, guard in EDITS:
        joined = "".join(files[path])
        if guard in joined:
            problems.append(f"{path}: already applied - {guard!r} is present")
            print(f"  {kind:14} {guard[:46]:48} ALREADY PRESENT")
            continue
        if kind == "append_cell":
            n = sum(1 for ln in files[path] if ln.startswith(locator))
            print(f"  {kind:14} {locator!r:48} -> {n}")
            if n != 1:
                problems.append(f"{path}: row anchor {locator!r} matched {n}, need exactly 1")
        elif kind == "insert_before":
            n = joined.count(locator)
            print(f"  {kind:14} {locator!r:48} -> {n}")
            if n != 1:
                problems.append(f"{path}: anchor {locator!r} matched {n}, need exactly 1")
        else:
            print(f"  {kind:14} {'(end of file)':48} -> ok")

    if problems:
        print("\nREFUSED, nothing written:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1

    for path, kind, locator, payload, _ in EDITS:
        lines = files[path]
        if kind == "append_eof":
            if lines and not lines[-1].endswith("\n"):
                lines[-1] += "\n"
            lines.append(payload + "\n")
        elif kind == "append_cell":
            i = next(i for i, ln in enumerate(lines) if ln.startswith(locator))
            core = lines[i].rstrip("\n")
            if not core.endswith("|"):
                print(f"REFUSED: row {locator!r} does not end with a pipe", file=sys.stderr)
                return 1
            lines[i] = core[:-1].rstrip() + " " + payload + " |\n"
        else:
            joined = "".join(lines)
            joined = joined.replace(locator, "\n" + payload + "\n\n## Notes", 1)
            files[path] = joined.splitlines(keepends=True)
            continue
        files[path] = lines

    for path in (RISK, VERIF, STATUS):
        pathlib.Path(path).write_text("".join(files[path]), encoding="utf-8")
        print(f"WROTE {path}: {len(files[path])} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
