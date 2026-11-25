#!/usr/bin/env python3
"""F43 - restore five missing RV rows, account for RV-17, fix F47 in RV-38.

One file: docs/project/RISK-REGISTER.md. Every assertion runs before a byte is
written. Table shape is read from the register's own header line rather than
written down here. Running it twice fails loudly.

In-place edits are applied first because they do not change the line count;
insertions are then applied from the bottom up so earlier anchors stay valid.

Run from the repository root:  python3 scripts/maintenance/f43_register_rows.py
Exit 0 with ALL CHECKS OK  -> the file changed.
Any other exit code         -> the file was not touched.
"""

import sys
from pathlib import Path

PATH = Path("docs/project/RISK-REGISTER.md")
HEADER_PREFIX = "| ID | Sev | Risk | Trigger | Owner | Mitigation |"
MITIGATION_INDEX = 6   # '' + 7 cells + '' when a row is split on '|'

UNFOLLOWABLE = (
    " — a section of the project's state file, which is working memory and is not part of "
    "this repository; a reader outside the project cannot follow it"
)
RESTORED = (
    " Restored to this register 2026-11-25 (F43); until then the row existed only in the "
    "project's working memory |"
)

ROW_RV05 = (
    "| RV-05 | MED | Python readiness | [UNKNOWN] — never written; owed at 08 | 08 | "
    "[UNKNOWN] — never written; owed at 08 | OPEN." + RESTORED
)

ROW_RV08 = (
    "| RV-08 | MED | Explain-backs ≤ 1 h per phase inside the weekly review | "
    "[UNKNOWN] — never written; owed at §7 | §7" + UNFOLLOWABLE + " | "
    "[UNKNOWN] — never written; owed at §7 | OPEN · NOT WAIVABLE. The 4E item is a hard "
    "condition on gate 05." + RESTORED
)

ROW_RV09 = (
    "| RV-09 | MED | Light audit A1/A3/A5 at each weekly review | "
    "[UNKNOWN] — never written; owed at §8 | §8" + UNFOLLOWABLE + " | "
    "[UNKNOWN] — never written; owed at §8 | ADOPTED; run 14, 21, 22, 23, 24 Nov." + RESTORED
)

ROW_RV11 = (
    "| RV-11 | LOW | Install Liger (B5) with `--no-deps`; diff `pip freeze` against the lock | "
    "[UNKNOWN] — never written; owed at 10A | 10A | [UNKNOWN] — never written; owed at 10A | "
    "OPEN. Restored to this register 2026-11-25 (F43). The requirement side of the same "
    "instruction is recorded in `docs/requirements/TRACEABILITY-MATRIX.md` in its B5 Liger "
    "Kernel row, which references this identifier but is not a register row |"
)

ROW_RV18 = (
    "| RV-18 | LOW | Plan file name mismatch | [UNKNOWN] — never written; owed at §1.2 | "
    "§1.2" + UNFOLLOWABLE + " | [UNKNOWN] — never written; owed at §1.2 | OPEN." + RESTORED
)

# (the row that each block is inserted ABOVE, the rows to insert)
INSERTIONS = [
    ("| RV-06 |", [ROW_RV05]),
    ("| RV-10 |", [ROW_RV08, ROW_RV09]),
    ("| RV-20 |", [ROW_RV11, ROW_RV18]),
]

INTRO_ANCHOR = "Severity: CRIT · HIGH · MED · LOW."
INTRO_ADDITION = (
    " No RV-17 row appears in this register, and a repository-wide search of `docs/` on "
    "2026-11-25 found no RV-17 record anywhere; its provenance and status are unresolved."
)

RV38_MITIGATION_ADDITION = (
    ". That file is held in the project's working memory and is not part of this repository; "
    "it is a secondary reference and a reader outside the project cannot follow it"
)


def fail(message: str) -> None:
    print(f"MISMATCH - STOP: {message}")
    sys.exit(1)


def sole_index(lines, prefix, what):
    hits = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    if len(hits) != 1:
        fail(f"{what}: expected exactly 1 line starting {prefix!r}, found {len(hits)}")
    return hits[0]


def main() -> None:
    if not PATH.is_file():
        fail(f"{PATH} not found - run this from the repository root")

    lines = PATH.read_text(encoding="utf-8").split("\n")

    # ---- assertions, all of them, before any edit ----
    header_i = sole_index(lines, HEADER_PREFIX, "header")
    want_pipes = lines[header_i].count("|")

    new_rows = [ROW_RV05, ROW_RV08, ROW_RV09, ROW_RV11, ROW_RV18]
    for row in new_rows:
        rid = row.split("|")[1].strip()
        if row.count("|") != want_pipes:
            fail(f"{rid}: carries {row.count('|')} pipes, header carries {want_pipes}")
        if any(line.startswith(f"| {rid} |") for line in lines):
            fail(f"{rid} is already present - this script has already run")

    anchors = {}
    for prefix, _rows in INSERTIONS:
        anchors[prefix] = sole_index(lines, prefix, "insertion anchor")

    intro_hits = sum(line.count(INTRO_ANCHOR) for line in lines)
    if intro_hits != 1:
        fail(f"intro anchor occurs {intro_hits} times, expected exactly 1")
    if any(INTRO_ADDITION.strip() in line for line in lines):
        fail("the RV-17 sentence is already present - this script has already run")

    rv38_i = sole_index(lines, "| RV-38 |", "RV-38")
    rv38_cells = lines[rv38_i].split("|")
    if len(rv38_cells) != want_pipes + 1:
        fail(f"RV-38 splits into {len(rv38_cells)} fields, expected {want_pipes + 1}")
    if RV38_MITIGATION_ADDITION.strip(". ") in lines[rv38_i]:
        fail("RV-38 already carries the F47 clause - this script has already run")

    print("ALL ASSERTIONS PASSED")

    # ---- in-place edits first: they do not change the line count ----
    for i, line in enumerate(lines):
        if INTRO_ANCHOR in line:
            lines[i] = line.replace(INTRO_ANCHOR, INTRO_ANCHOR + INTRO_ADDITION, 1)
            print(f"  intro: RV-17 accounting sentence added (line {i + 1})")
            break

    rv38_cells[MITIGATION_INDEX] = (
        rv38_cells[MITIGATION_INDEX].rstrip() + RV38_MITIGATION_ADDITION + " "
    )
    lines[rv38_i] = "|".join(rv38_cells)
    print(f"  RV-38: F47 clause appended to the Mitigation cell (line {rv38_i + 1})")

    # ---- insertions bottom-up, so earlier anchors stay valid ----
    for prefix, rows in sorted(INSERTIONS, key=lambda p: anchors[p[0]], reverse=True):
        at = anchors[prefix]
        lines[at:at] = rows
        for offset, row in enumerate(rows):
            print(f"  inserted {row.split('|')[1].strip()} above {prefix.strip()} "
                  f"(line {at + offset + 1})")

    PATH.write_text("\n".join(lines), encoding="utf-8")
    print("ALL CHECKS OK")


if __name__ == "__main__":
    main()
