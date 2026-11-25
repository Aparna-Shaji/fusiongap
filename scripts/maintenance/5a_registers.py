#!/usr/bin/env python3
"""5A - bring docs/project/RISK-REGISTER.md current to 2026-11-25.

Five status rewrites (R21, RV-23, RV-30, RV-33, RV-37) and two new rows
(RV-38, RV-39).

Nothing partial is possible: every assertion runs before any byte is
written, and the file is written once at the end or not at all. Running
it twice fails loudly, because RV-38 will already be present.

Run from the repository root:  python3 scripts/maintenance/5a_registers.py
Exit 0 with ALL CHECKS OK  -> the file changed.
Any other exit code         -> the file was not touched.
"""

import sys
from pathlib import Path

PATH = Path("docs/project/RISK-REGISTER.md")
EXPECTED_FIELDS = 9   # '' + 7 cells + '' when a row is split on '|'
STATUS_INDEX = 7      # the 7th cell is Status
ANCHOR = "RV-37"      # the new rows go directly after this row

UPDATES = {
    "R21": (
        "ANSWERED and NARROWED. 2026-11-21: 30.00 W enforced across all 297 samples of the 4C "
        "run against a 50 W default, with the loaded clock at 1005 MHz against deviceQuery's "
        "1515 MHz ceiling. 2026-11-24: the assumption previously recorded in this cell was "
        "TESTED and its NitroSense half FALSIFIED. A controlled A/B over NitroSense's AC power "
        "plan returned the single distinct value 30.00 W on 140 samples per arm under Balance "
        "and under High-Performance, with zero disagreements between the two query forms across "
        "280 samples, so NitroSense does not control the enforced ceiling (D-41; evidence "
        "`results/env/4L_balance.txt`, `4L_high-performance.txt` and their CSVs). The Windows "
        "power-plan half is UNTESTED: Balanced is now pinned by D-41 and no other plan has been "
        "measured. Pinned state: mains AC - Windows plan Balanced - NitroSense Mode AC, plan "
        "Balance, Fan Auto, CoolBoost off - Current 30.00 W against Requested, Default and Max "
        "50.00 W. The mechanism that sets 30 W remains [UNKNOWN]"
    ),
    "RV-23": (
        "OPEN: 2026-11-25. The rising run previously recorded here BROKE on 2026-11-24. Stage "
        "hours ran 8.0 on 11-21, 10.0 on 11-22, 11.0 on 11-23, then 6.0 on 11-24, so neither "
        "\"the mechanism is absent\" (the 11-21 reading) nor \"the mechanism is present\" (the "
        "11-23 reading) describes the series - four days support neither claim, and this cell "
        "has now asserted both. Parallel-track hours went unreported on 11-22, 11-23 and "
        "11-24, and finding F24 holds that this row's trigger cannot be evaluated at all while "
        "that is true: \"parallel-track hours at zero\" is not satisfied by hours that were "
        "never reported, so the clause can be neither met nor missed. A change request on the "
        "trigger is owed at the 2026-11-28 review. Whether the rate is sustainable is that "
        "review's question and not this row's"
    ),
    "RV-30": (
        "OPEN: 79 GB 11-14, 71 GB 11-18, 69 GB 11-20, 58 GB 11-21 09:17, 68 GB 11-21 10:26, "
        "67 GB 11-21 20:00, 59 GB 11-25 11:23 - an 11 GB fall and a 10 GB recovery inside one "
        "day, with the Ubuntu virtual disk not found under the Canonical package path and the "
        "Windows page, swap and hibernation files invisible to WSL. NOT TRIGGERED: two "
        "consecutive session-start readings below 45 GB are required and the lowest reading to "
        "date is 58 GB. Four further readings exist in project memory as the undated sequence "
        "68, 68, 65, 67 ending 2026-11-24; they cannot be matched to the dated series above and "
        "are deliberately not merged into it rather than being given invented dates. "
        "2026-11-25, finding F45 raises the part of this risk that is not noise: 5D imports a "
        "second distribution and installs the toolkit and torch into it, and no step in stage "
        "05 computes that cost before the import, so a project action can carry the drive "
        "toward the trigger from today's 59 GB. `rm -rf ~/.cache/pip` frees 3.4 GB and is a "
        "3 GB lever against a cost nobody has yet sized"
    ),
    "RV-33": (
        "OPEN: 2026-11-21, utilisation reached 0 at +1.6 s, the flags cleared at +2.8 s and the "
        "clock reached 300 MHz at +3.6 s; a 10 s post-warm-up settle held a 1380 MHz median, "
        "and run 1's 8 s settle was still at 1380 MHz throughout the 6 s measured. THIRD "
        "MEASUREMENT 2026-11-24: 4L's trailing idle windows report medians of 615-622 MHz "
        "because the window mixes post-load samples with idle ones - the same mechanism at a "
        "different sampling rate, on a different workload, and under a different power profile. "
        "Three independent observations of a boost hold that no fixed settle interval can "
        "bound. Evidence `results/env/4L_balance.csv`, `4L_high-performance.csv`"
    ),
    "RV-37": (
        "OPEN: 2026-11-23. At idle, 50 W then 30 W inside one twenty-second window with the "
        "mains adapter untouched. Under sustained 100 % load it held 30.00 W across 28 "
        "consecutive samples, with draw at 28.1-29.1 W - 94 to 97 % of the cap - and the SM "
        "clock oscillating 945-1050 MHz at a 1005 MHz median that reproduces 2026-11-21's "
        "independent median on a different workload. Evidence "
        "`results/env/4K_power_under_load.txt`. RULED 2026-11-23 as D-39 (AM-09): the ceiling "
        "is read under load, pinned at 30 W, and a run whose recorded set of distinct values "
        "has more than one member is invalid rather than adjusted - CR-13 is ADOPTED, not "
        "proposed, and this cell previously said otherwise. PINNED 2026-11-24 by D-41 using the "
        "committed instrument `spikes/4L/sample_power.py`: 30.00 W across 280 samples spanning "
        "two NitroSense profiles, with the two query forms never once disagreeing, which "
        "falsifies the proposal that they report different quantities. Finding F32 - that the "
        "4K evidence came from an uncommitted command - is CLOSED by commit `42a091d`. The 50 W "
        "mechanism remains [UNKNOWN]"
    ),
}

NEW_ROWS = [
    "| RV-38 | MED | Gate 06's own GO criterion is written in the retired D1-D48 calendar that "
    "AM-05 replaced with the hours plan, so the criterion deciding whether Phase II closes "
    "cannot be evaluated in the units the project now uses | Gate 06 is reached and its GO "
    "criterion is read | gate 06 - 2026-11-28 review | A change request at the 2026-11-28 "
    "review restates the criterion in hours and worked days. Until then "
    "`claude/PLAN-FILE-CORRECTIONS.md` records it as the sixth place the plan-file upload "
    "contradicts an approved decision, and is read beside the upload | OPEN: raised "
    "2026-11-24, recorded in the corrections file the same day and in this register "
    "2026-11-25. Change request owed at the 2026-11-28 review |",

    "| RV-39 | HIGH | Thermal ordering is a confound across the study's arms and logging "
    "temperature does not remove it. Both 4L arms show the SM clock still falling across "
    "thirds of a 120 s run, so 120 s does not reach steady state; arms run as consecutive "
    "blocks therefore start progressively hotter, clock lower, and the difference reads as a "
    "kernel result rather than a thermal one | Any comparison whose arms ran as consecutive "
    "blocks with no stated starting-temperature precondition, or any run whose clock median "
    "differs across thirds | 07 - 08 | Interleaved or randomised arm ordering designed into "
    "the harness rather than added afterwards, a stated starting-temperature precondition "
    "checked before each timed cell, and a cool-down between arms. `capture.sh` adopts "
    "`spikes/4L/sample_power.py` and adds both at 5C. Logging temperature is necessary and "
    "not sufficient: it records the confound without controlling it | OPEN: raised 2026-11-24 "
    "from the 4L A/B, whose two arms started at 36.3 C and 47.3 C with no cool-down (finding "
    "F34) - which is why 4L's ceiling comparison stands and its clock comparison does not. "
    "Related to RV-33 and F34 |",
]


def fail(message: str) -> None:
    print(f"MISMATCH - STOP: {message}")
    sys.exit(1)


def main() -> None:
    if not PATH.is_file():
        fail(f"{PATH} not found - run this from the repository root")

    lines = PATH.read_text(encoding="utf-8").split("\n")

    # ---- every assertion runs before any edit ----
    index: dict[str, int] = {}
    for row_id in list(UPDATES) + [ANCHOR]:
        hits = [i for i, line in enumerate(lines) if line.startswith(f"| {row_id} |")]
        if len(hits) != 1:
            fail(f"{row_id}: expected exactly 1 row, found {len(hits)}")
        index[row_id] = hits[0]

    for row_id in UPDATES:
        n = len(lines[index[row_id]].split("|"))
        if n != EXPECTED_FIELDS:
            fail(
                f"{row_id}: row splits into {n} fields, expected {EXPECTED_FIELDS} "
                "- a literal '|' inside a cell would cause this"
            )

    for row in NEW_ROWS:
        cells = row.split("|")
        new_id = cells[1].strip()
        if len(cells) != EXPECTED_FIELDS:
            fail(f"{new_id}: new row splits into {len(cells)} fields, expected {EXPECTED_FIELDS}")
        if any(line.startswith(f"| {new_id} |") for line in lines):
            fail(f"{new_id} is already present - this script has already run")

    for text in list(UPDATES.values()):
        if "|" in text:
            fail("a replacement status contains a '|', which would create a new column")

    if index[ANCHOR] != max(index.values()):
        fail(f"{ANCHOR} is not the last row this script knows about - inspect the file by hand")

    print("ALL ASSERTIONS PASSED")

    # ---- edits ----
    for row_id, new_status in UPDATES.items():
        cells = lines[index[row_id]].split("|")
        cells[STATUS_INDEX] = f" {new_status} "
        lines[index[row_id]] = "|".join(cells)
        print(f"  rewrote status: {row_id} (line {index[row_id] + 1})")

    at = index[ANCHOR] + 1
    lines[at:at] = NEW_ROWS
    for offset, row in enumerate(NEW_ROWS):
        print(f"  inserted: {row.split('|')[1].strip()} (line {at + offset + 1})")

    PATH.write_text("\n".join(lines), encoding="utf-8")
    print("ALL CHECKS OK")


if __name__ == "__main__":
    main()
