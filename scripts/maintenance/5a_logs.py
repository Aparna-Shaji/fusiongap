#!/usr/bin/env python3
"""5A - append four verification rows and the 2026-11-24 status entry.

Two files, one transaction. Every assertion for BOTH files runs before
either is written, so a failure in the status log cannot leave the
verification log half-updated. Running it twice fails loudly.

Run from the repository root:  python3 scripts/maintenance/5a_logs.py
Exit 0 with ALL CHECKS OK  -> both files changed.
Any other exit code         -> neither file was touched.
"""

import sys
from pathlib import Path

VLOG = Path("docs/project/VERIFICATION-LOG.md")
SLOG = Path("docs/project/STATUS-LOG.md")
EXPECTED_FIELDS = 7          # '' + 5 cells + '' when a row is split on '|'
VLOG_ANCHOR = "V18"          # new rows go directly after this row
SLOG_ANCHOR = "| 2026-11-23" # the new entry goes directly after this row

VLOG_ROWS = [
    "| V19 | The GPU's enforced power ceiling under sustained load is 30.00 W, and NitroSense's "
    "AC power plan does not change it | VERIFIED | A controlled A/B over NitroSense's AC power "
    "plan, 140 samples per arm, both query forms per iteration, with idle windows as a negative "
    "control: Balance and High-Performance each returned the single distinct value 30.00 W, and "
    "`-q -d POWER`'s Current Power Limit never once disagreed with "
    "`--query-gpu=enforced.power.limit` across 280 samples - which falsifies the proposal that "
    "the two forms report different quantities. Requested, Default and Max all read 50.00 W. "
    "Pinned state (D-41): mains AC, Windows plan Balanced, NitroSense Mode AC, plan Balance, Fan "
    "Auto, CoolBoost off. The instrument is `spikes/4L/sample_power.py`, committed with the "
    "evidence, which closes finding F32 - the 4K reading D-39 rests on came from an uncommitted "
    "command. The Windows power plan itself is UNTESTED as the cause and the 50 W value remains "
    "[UNKNOWN] · `results/env/4L_balance.txt`, `4L_high-performance.txt` and their CSVs · "
    "2026-11-24 | 4L; D-41; re-checked at 07 |",

    "| V20 | TorchInductor passes a per-compile floating-point fusion override to Triton, so that "
    "`torch.compile` and a hand-written Triton kernel execute different arithmetic | UNVERIFIED | "
    "Not yet tested. Unset equals fusion ENABLED in Triton 3.9.0 (`knobs.py:499`), and this "
    "project sets `TRITON_DEFAULT_FP_FUSION` per spike environment (`spikes/4I` line 32, "
    "`spikes/4J` line 42) with the harness taking over at stage 08. If Inductor passes its own "
    "override, the primary baseline B2 (D-03) and the hand-written Triton arm are not running the "
    "same arithmetic, and no speedup between them is a like-for-like comparison. Raised as "
    "finding F31, beside RV-20 | 10B |",

    "| V21 | A 120 s run reaches thermal steady state on this GPU | VERIFIED (no) | Both 4L arms "
    "show the SM clock still falling across thirds of a 120 s run, so 120 s does not reach steady "
    "state. The two arms also started at 36.3 C and 47.3 C because the protocol has no cool-down "
    "(finding F34), which is why 4L's ceiling comparison stands and its clock comparison does "
    "not. Consequence: arms run as consecutive blocks start progressively hotter, clock lower, "
    "and the difference reads as a kernel result rather than a thermal one. Logging temperature "
    "records the confound without controlling it; the mitigation is RV-39 - interleaved or "
    "randomised arm ordering and a stated starting-temperature precondition, designed into the "
    "harness · `results/env/4L_balance.csv`, `4L_high-performance.csv` · 2026-11-24 | 4L "
    "(RV-39); capture.sh at 5C; harness at 08 |",

    "| V22 | PyTorch's build helper enforces a host-compiler version ceiling for the pinned CUDA "
    "13.2 | VERIFIED (no) | Read from `torch/utils/cpp_extension.py` in the project venv (torch "
    "2.15.0+cu132). `CUDA_GCC_VERSIONS` at line 63 has no `13.2` key - it ends at `13.0` with an "
    "exclusive upper bound of major 16 - and `_check_cuda_version` at lines 241-242 logs *There "
    "are no g++ version bounds defined for CUDA version 13.2* and continues, so the `RuntimeError` "
    "at line 259 is unreachable on this configuration. That warning is therefore EXPECTED output "
    "of every CUDA extension build in this project. The only host-compiler ceiling in force is "
    "nvcc's own `crt/host_config.h` above GCC major 15 (V14, RV-28). Two further reads from the "
    "same file, recorded as finding F42: `get_cxx_compiler` (line 271) takes `CXX` and defaults "
    "to the unversioned `c++`, while the nvcc path forwards `-ccbin` from `CC` (line 939) and "
    "only when the extension's own flags do not already set one (line 942) - so the g++-15 pin "
    "needs an explicit `-ccbin` in the build file, not an environment variable. "
    "`TORCH_DONT_CHECK_COMPILER_ABI` disables both this check and the ABI check (lines 170, 235) "
    "and is never set by this project · read 2026-11-25 | 5A. RV-27's torch-level half is "
    "DISCHARGED; its distribution-pairing half remains open under F12. Build channel owned by 15 |",
]

SLOG_ROW = (
    "| 2026-11-24 Tue | WD11 | **Gate 04 CLOSED - the last two conditions discharged and all six "
    "resolved.** C1: `docs/environment/ENVIRONMENT.md` written, 196 lines in five sections, every "
    "read command in it executed and matched before the commit, nine open items recorded rather "
    "than omitted (`7a87923`). **D-40 and D-41 chose the machine the study runs on by "
    "measurement rather than by whatever happened to be set.** A controlled A/B over NitroSense's "
    "AC power plan - 140 samples per arm, both query forms per iteration, idle windows as a "
    "negative control - returned the single value 30.00 W under Balance and under "
    "High-Performance with zero disagreements across 280 samples, so NitroSense does not control "
    "the enforced ceiling and adopting High-Performance would have invalidated every reading "
    "taken so far for no gain. Pinned: mains AC, Windows plan Balanced, NitroSense Mode AC, plan "
    "Balance, Fan Auto, CoolBoost off. The sampler is committed (`42a091d`), closing F32, which "
    "held that the evidence D-39 rests on was produced by an uncommitted command. **The history "
    "was rewritten under an approved ruling (D-42, D-43).** 24 of 50 commits carried the AI "
    "co-author and session trailers; `git-filter-repo 2.47.0-3` stripped both across all refs, 31 "
    "commits took new hashes, and tree hashes, author names, emails and author dates were "
    "verified byte-for-byte identical across all 53 parsed commits before anything was pushed. "
    "Twenty citations repointed from the commit map with no ambiguous entries (`e88f752`). Both "
    "branches force-pushed; the pre-rewrite mirror is kept outside the repository. The rewrite is "
    "disclosed in the Notes section below, deliberately. The attribution policy was strengthened "
    "the same evening into D-42 and D-43, with a pre-commit verification and a clause covering "
    "what the mentor does when its own environment injects attribution. F37 closed (`d3be4c6`): "
    "this log's own note gave a reason for never rewriting that the rewrite had overtaken. "
    "Sixteen findings raised and one withdrawn; RV-39 raised at HIGH; five process notes (P-20 to "
    "P-24); four decisions. Five commits | Stage 05 - 5A approve the environment | 5.0 h stage + "
    "1.0 h learning inside the stage box (E5) = 6.0 h stage total; parallel track unreported. "
    "Zero boxed hours converted - the fourth consecutive such day |"
)


def fail(message: str) -> None:
    print(f"MISMATCH - STOP: {message}")
    sys.exit(1)


def sole_index(lines: list[str], prefix: str, where: str) -> int:
    hits = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    if len(hits) != 1:
        fail(f"{where}: expected exactly 1 line starting '{prefix}', found {len(hits)}")
    return hits[0]


def main() -> None:
    for path in (VLOG, SLOG):
        if not path.is_file():
            fail(f"{path} not found - run this from the repository root")

    vlines = VLOG.read_text(encoding="utf-8").split("\n")
    slines = SLOG.read_text(encoding="utf-8").split("\n")

    # ---- every assertion for BOTH files, before either is written ----
    v_at = sole_index(vlines, f"| {VLOG_ANCHOR} |", "VERIFICATION-LOG") + 1
    last_v = max(i for i, line in enumerate(vlines) if line.startswith("| V"))
    if last_v != v_at - 1:
        fail(f"VERIFICATION-LOG: {VLOG_ANCHOR} is not the last V row (last is line {last_v + 1})")

    for row in VLOG_ROWS:
        cells = row.split("|")
        new_id = cells[1].strip()
        if len(cells) != EXPECTED_FIELDS:
            fail(f"{new_id}: splits into {len(cells)} fields, expected {EXPECTED_FIELDS}")
        if any(line.startswith(f"| {new_id} |") for line in vlines):
            fail(f"{new_id} is already present - this script has already run")

    s_at = sole_index(slines, SLOG_ANCHOR, "STATUS-LOG") + 1
    notes = sole_index(slines, "## Notes", "STATUS-LOG")
    if notes <= s_at:
        fail(f"STATUS-LOG: '## Notes' at line {notes + 1} is not below the last data row")
    if any(line.startswith("| 2026-11-24") for line in slines):
        fail("STATUS-LOG: a 2026-11-24 entry already exists")
    if len(SLOG_ROW.split("|")) != EXPECTED_FIELDS:
        fail(f"STATUS-LOG: new entry splits into {len(SLOG_ROW.split('|'))} fields, "
             f"expected {EXPECTED_FIELDS}")

    print("ALL ASSERTIONS PASSED")

    # ---- edits, after every assertion has passed ----
    vlines[v_at:v_at] = VLOG_ROWS
    for offset, row in enumerate(VLOG_ROWS):
        print(f"  appended to VERIFICATION-LOG.md: "
              f"{row.split('|')[1].strip()} (line {v_at + offset + 1})")

    slines[s_at:s_at] = [SLOG_ROW]
    print(f"  inserted into STATUS-LOG.md: 2026-11-24 (line {s_at + 1})")

    VLOG.write_text("\n".join(vlines), encoding="utf-8")
    SLOG.write_text("\n".join(slines), encoding="utf-8")
    print("ALL CHECKS OK")


if __name__ == "__main__":
    main()
