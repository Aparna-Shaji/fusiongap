#!/usr/bin/env python3
"""5A - record the pin approval and today's findings in ADR-0001 and ENVIRONMENT.md.

Nine exact-text edits. Every anchor must occur exactly once in its file, every
new table row must match the pipe count of the header of the table it joins,
and every assertion for BOTH files runs before either is written - so a
mistranscribed anchor or a malformed row leaves both files untouched.

Table shapes are read from each table's own header line rather than asserted,
because an expected value computed by hand is one more thing that can be wrong.

Run from the repository root:  python3 scripts/maintenance/5a_pins.py
Exit 0 with ALL CHECKS OK  -> both files changed.
Any other exit code         -> neither file was touched.
"""

import sys
from pathlib import Path

ADR = Path("docs/architecture/adr/ADR-0001-env-pins.md")
ENV = Path("docs/environment/ENVIRONMENT.md")

NVIDIA_SMI_ROW = (
    "| `nvidia-smi` (the telemetry instrument) | **620.67.01** - the tool's own version, distinct "
    "from KMD 621.01 and CUDA UMD 13.5 and lower than both | `nvidia-smi`, header line 3; read "
    "2026-11-25. Pinned because this binary is the source of every telemetry number the project "
    "records (D-31, ADR-0003), and because all six instances of \"verify the effect, not the "
    "return code\" are behaviours *of this binary at this version* - the `-lms` interval that "
    "delivers 1.92 Hz, `-ac` and `-lmc` exiting 0 while setting nothing, the throttle counters "
    "that are a wall clock (RV-31), the `-q -d POWER` field split that `--query-gpu` collapses. "
    "A different version re-opens every one of them (F49) |"
)

TRIGGER_5 = (
    "5. **The telemetry instrument changed** - `nvidia-smi`'s own version reads anything other\n"
    "   than 620.67.01. Every behaviour recorded under \"verify the effect, not the return code\"\n"
    "   was measured on that binary; a change makes all of them unverified until re-checked, and\n"
    "   no number already recorded is comparable to one taken after it without that re-check."
)

ENV_VAR_ROWS = (
    "| `CC` and `CXX` | **Both unset in the interactive shell, deliberately.** The host compiler "
    "is named by the build file, not by shell state | `echo \"CC=[$CC] CXX=[$CXX]\"` - both must "
    "print empty brackets | `torch.utils.cpp_extension` reads `CXX` for C++ translation units and "
    "defaults to the unversioned `c++` (`cpp_extension.py:271`), and passes `-ccbin` to nvcc from "
    "**`CC`** only, and only when the extension's own flags do not already set one (lines 939 and "
    "942). Unset therefore selects the alias silently - 15.2.0 today, whatever apt installs "
    "tomorrow. Exporting them is the wrong fix for the same reason as the fp-fusion variable "
    "below: it makes which compiler built a run depend on whose shell launched it. The stage-15 "
    "build file is the authority; ADR-0001 reversal trigger 4 is the check (F42) |\n"
    "| `TORCH_DONT_CHECK_COMPILER_ABI` | **Never set, in any shell or script of this project** | "
    "`echo \"[$TORCH_DONT_CHECK_COMPILER_ABI]\"` must print `[]` | Set to any of `ON 1 YES TRUE "
    "Y` it disables **both** of torch's build-time guards at once: the ABI-compatibility check "
    "(`cpp_extension.py:170`) and the CUDA-version and compiler-bound check (line 235). Those are "
    "the only automatic compiler guards this stack has, and on CUDA 13.2 the second already does "
    "nothing - see section 5 item 10 |"
)

ENV_OPEN_ITEMS = (
    "| 10 | PyTorch defines **no host-compiler version bounds for CUDA 13.2**: `CUDA_GCC_VERSIONS` "
    "ends at 13.0, so `_check_cuda_version` logs *There are no g++ version bounds defined for CUDA "
    "version 13.2* and continues. **That warning is expected output of every CUDA build here, not "
    "a defect.** The only ceiling in force is nvcc's own `crt/host_config.h` above GCC major 15 "
    "(V22, RV-28) | recorded |\n"
    "| 11 | **Installing `g++-15` does not select it.** The C++ path reads `CXX` and defaults to "
    "`c++`; the nvcc path takes `-ccbin` from `CC` and only when the build's own flags do not set "
    "one. The stage-15 build file must name `-ccbin /usr/bin/g++-15` explicitly and set `CXX`, "
    "because a shell variable is lost the moment a build runs without it (F42) | 15 |\n"
    "| 12 | **The disk cost of the 5D rebuild has never been computed.** Free space read 59 GB on "
    "2026-11-25 against RV-30's 45 GB trigger and 30 GB floor, so a rebuild costing more than "
    "about 14 GB arms that trigger by this project's own action. Section 3 step 1 now requires the "
    "budget before the import (F45) | 5D |"
)

EDITS = {
    ADR: [
        (
            "4. **Pins**, as measured on 2026-11-19. Blank entries are filled at 5A and frozen there.",
            "4. **Pins**, as measured on 2026-11-19 and **read back against the machine at 5A on\n"
            "   2026-11-25**. Every installed row matched its pinned value on that read, each by the\n"
            "   command its own row names - including the two the Python row requires and the "
            "separate\n"
            "   invariant the Triton row requires. The rows reading [UNKNOWN] are uninstalled by\n"
            "   design and are filled at 5C: a deferral with a named owner, not a gap. Frozen here.",
        ),
        (
            "| CUDA UMD | 13.5 | `nvidia-smi` |",
            "| CUDA UMD | 13.5 | `nvidia-smi` |\n" + NVIDIA_SMI_ROW,
        ),
        (
            "metadata. Four triggers, one per",
            "metadata. Five triggers, one per",
        ),
        (
            "   the build path still resolves `gcc`.",
            "   the build path still resolves `gcc`.\n" + TRIGGER_5,
        ),
    ],
    ENV: [
        (
            "\n\n### The fp-fusion scope, stated exactly,",
            "\n" + ENV_VAR_ROWS + "\n\n### The fp-fusion scope, stated exactly,",
        ),
        (
            "   after; RV-30's trigger is two consecutive session-start readings below 45 GB.",
            "   after; RV-30's trigger is two consecutive session-start readings below 45 GB.\n"
            "   **Compute the budget before the import, not after:** the rootfs, the CUDA toolkit's\n"
            "   apt download and installed size, and the torch wheel. Free space read 59 GB on\n"
            "   2026-11-25, so a rebuild costing more than about 14 GB arms RV-30 by this project's\n"
            "   own action. If the budget does not clear the 30 GB floor, free space first -\n"
            "   `rm -rf ~/.cache/pip` recovers about 3.4 GB - or place the second distribution's\n"
            "   virtual disk on another volume (F45).",
        ),
        (
            "   there is zero headroom).",
            "   there is zero headroom). **Installing it is necessary and not sufficient: nothing\n"
            "   selects it automatically.** `torch.utils.cpp_extension` reads `CXX` for C++\n"
            "   translation units and defaults to the unversioned `c++`, and passes `-ccbin` to nvcc\n"
            "   from `CC` only, and only when the extension's own flags do not already set one. The\n"
            "   build file written at stage 15 therefore names `-ccbin /usr/bin/g++-15` explicitly\n"
            "   and sets `CXX`; reversal trigger 4 of ADR-0001 is what catches a build that did\n"
            "   neither (F42).",
        ),
        (
            "(the CUDA extension, roughly 193 s for one translation unit).",
            "(the CUDA extension, roughly 193 s for one translation unit). That build prints\n"
            "   *There are no g++ version bounds defined for CUDA version 13.2* - expected, not a\n"
            "   defect; section 5 item 10.",
        ),
        (
            "| 9 | `pre-commit` is installed inside the venv only, so gate 05's criterion must check "
            "that **the hook fires**, not that the command exists (RV-29) | gate 05 |",
            "| 9 | `pre-commit` is installed inside the venv only, so gate 05's criterion must check "
            "that **the hook fires**, not that the command exists (RV-29) | gate 05 |\n"
            + ENV_OPEN_ITEMS,
        ),
    ],
}

# (file, the table's own header line, the rows being added to it).
# The expected pipe count is read from the header, never written down here.
TABLES = [
    (ADR, "| Layer | Pin | Checked by |", [NVIDIA_SMI_ROW]),
    (ENV, "| Variable | Pinned | Read how | Mismatch means |", ENV_VAR_ROWS.split("\n")),
    (ENV, "| # | Item | Owner |", ENV_OPEN_ITEMS.split("\n")),
]


def fail(message: str) -> None:
    print(f"MISMATCH - STOP: {message}")
    sys.exit(1)


def main() -> None:
    for path in EDITS:
        if not path.is_file():
            fail(f"{path} not found - run this from the repository root")

    texts = {path: path.read_text(encoding="utf-8") for path in EDITS}

    # ---- assertions for BOTH files, before either is written ----
    for path, pairs in EDITS.items():
        for i, (old, _new) in enumerate(pairs, start=1):
            n = texts[path].count(old)
            if n != 1:
                fail(f"{path.name} edit {i}: anchor occurs {n} times, expected exactly 1\n"
                     f"           anchor begins: {old[:70]!r}")

    for path, header, rows in TABLES:
        if texts[path].count(header) != 1:
            fail(f"{path.name}: header {header!r} occurs "
                 f"{texts[path].count(header)} times, expected exactly 1")
        want = header.count("|")
        for row in rows:
            got = row.count("|")
            if got != want:
                fail(f"{path.name}: a row for {header!r} carries {got} pipes, "
                     f"but that table's header carries {want}\n"
                     f"           row begins: {row[:70]!r}")

    print("ALL ASSERTIONS PASSED")

    # ---- edits ----
    for path, pairs in EDITS.items():
        for i, (old, new) in enumerate(pairs, start=1):
            texts[path] = texts[path].replace(old, new, 1)
            print(f"  {path.name}: edit {i} applied")

    for path, text in texts.items():
        path.write_text(text, encoding="utf-8")

    print("ALL CHECKS OK")


if __name__ == "__main__":
    main()
