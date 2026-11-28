#!/usr/bin/env python3
"""scripts/maintenance/5c_environment_md.py - ENVIRONMENT.md brought current, 2026-11-28.

Closes F69 (three stale spots), F76 (a path that will never exist), F78 (no
apt-get clean, so the transient peak exceeds the budget), F77 (the space-recovery
remedy may recover nothing), F81 (step 9 reads a script whose exit code does not
enforce D-39), and V27's stated exclusion (CUDA_HOME is checked as a variable,
never as a path that holds a toolkit). Carries the measured 19.53 GiB budget.

F104's lesson applied: newline escapes in this script's own output are \\n in
source and a real newline at runtime. The payload strings below are markdown and
contain no escapes at all, so there is no second convention to confuse it with.

Same guard as 5b_adr_fixes.py: exactly-once target, absent replacement, nothing
written unless all ten match.

Run from the repository root:  python3 scripts/maintenance/5c_environment_md.py
"""
import sys
from pathlib import Path

ENV = Path("docs/environment/ENVIRONMENT.md")
EDITS = []


def edit(tag, old, new):
    EDITS.append({"id": tag, "old": old, "new": new})


# --- 1. step 1: the budget is measured, and the C: reading moved -----------
edit("step1 budget (F45/F77/F56)",
     """   **Compute the budget before the import, not after:** the rootfs, the CUDA toolkit's
   apt download and installed size, and the torch wheel. Free space read 59 GB on
   2026-11-25, so a rebuild costing more than about 14 GB arms RV-30 by this project's
   own action. If the budget does not clear the 30 GB floor, free space first -
   `rm -rf ~/.cache/pip` recovers about 3.4 GB - or place the second distribution's
   virtual disk on another volume (F45).""",
     """   **The budget is MEASURED, 2026-11-27, and is no longer computed at this step** (F45).
   Four components, bottom-up, agreeing with the top-down figure: Ubuntu rootfs and base
   apt **6.93 GiB** (by subtraction) - CUDA toolkit **4.8 GiB** (`du /usr/local/cuda-13.2`)
   - Nsight Compute and Systems **2.4 GiB** (`du /opt/nvidia`: they install OUTSIDE the
   toolkit directory, so the two footprints add rather than overlap) - Python environment
   **5.4 GiB** (`du .venv`) - pip cache excluded, because step 5 installs with
   `--no-cache-dir`. **Total 19.53 GiB.**
   Free space on `C:` read **69.04 GiB (74,134,622,208 bytes) on 2026-11-28**, so the
   rebuild leaves about **49.5 GiB - above** RV-30's 45 GB trigger. That reverses the
   conclusion of 2026-11-27, when 61.15 GiB would have left about 41.6 GiB and armed it:
   **7.89 GiB appeared overnight with no recorded cause** (F56), so the margin is real but
   not yet explained, and a future reading may undo it.
   **Read exact bytes, never `-h`.** `df --block-size=1 /mnt/c` - the human-readable form
   rounds in ways that hid gigabyte-scale movement earlier in the week.
   The transient peak during installation is higher than the installed figure, because apt
   stages every `.deb` before installing it; the `apt-get clean` steps below remove that
   peak (F78). If a future reading does not clear the 30 GB floor, place the second
   distribution's virtual disk on another volume. **`rm -rf ~/.cache/pip` may recover
   nothing on `C:`**: a WSL2 virtual disk grows on write and does not shrink when files
   inside it are deleted, unless it is sparse or explicitly compacted. Whether this one is
   sparse is `[UNKNOWN]`; step 11 tests it (F77).""")

# --- 2. step 3: the toolkit path check, and the first apt-get clean --------
edit("step3 nvcc + clean (V27/F78)",
     """   and sets `CXX`; reversal trigger 4 of ADR-0001 is what catches a build that did
   neither (F42).""",
     """   and sets `CXX`; reversal trigger 4 of ADR-0001 is what catches a build that did
   neither (F42).
   **Then two checks this procedure lacked until 2026-11-28.** First
   `test -x "$CUDA_HOME/bin/nvcc"`. Step 6 pins `CUDA_HOME` to `/usr/local/cuda-13.2`, and
   `scripts/env/test_setup_contract.sh` checks only that the variable is *set* - it never
   looks for a toolkit at that path, which is V27's stated exclusion. If apt lands the
   toolkit at a different patch path the variable still passes every assertion and the CUDA
   arm fails at step 8 with nothing upstream to blame. Second `sudo apt-get clean`: apt
   stages every `.deb` in `/var/cache/apt/archives` before installing, so without this the
   transient disk peak exceeds step 1's installed figure by several gigabytes (F78).""")

# --- 3. step 5: the lock exists ------------------------------------------
edit("step5 lock exists (F69)",
     """5. Install from the hash-pinned lock: `pip install --require-hashes -r env/requirements.lock`.
   **[NOT YET — `env/requirements.lock` is produced at stage 5C.]**""",
     """5. Install from the hash-pinned lock, **with `--no-cache-dir`**:
   `pip install --no-cache-dir --require-hashes -r env/requirements.lock`.
   The lock exists as of 2026-11-26: **82 packages, 1152 hashes**, resolved from PyPI alone
   (D-45) against `env/measured.txt` as a constraint so it reproduces what was measured
   rather than what was newest (F62). `--no-cache-dir` is not tidiness - a rebuild warmed
   by the old machine's pip cache is not a fresh-distribution rebuild, and it keeps
   2.85 GiB out of the footprint. Hash-checking is all-or-nothing across every requirement
   and every transitive dependency (F40), so one failure fails the whole install, and that
   is the intended behaviour rather than a problem to work around.""")

# --- 4. step 6: the path that will never exist ---------------------------
edit("step6 wrong path (F76)",
     "6. Apply the shell environment of section 2. **[`env/setup.sh` is produced at stage 5C.]**",
     """6. Apply the shell environment of section 2 by **sourcing** it, never executing it:
   `. scripts/env/setup.sh`.
   **The path is `scripts/env/`, not `env/`.** `env/` holds declarations and `scripts/env/`
   holds executables, ruled 2026-11-26 (F60) - a ruling recorded in project memory and never
   propagated into this file, so this step named a path that will never exist until
   2026-11-28 (F76). The script refuses to be executed rather than sourced, because an
   executed copy exits 0 having changed nothing, which is this project's most-repeated
   failure mode (D-46). Four of section 2's seven pinned items are **absences**, so a script
   that exports `TMPDIR` and `CUDA_HOME` and stops has done two sevenths of the job and
   looks finished; `scripts/env/test_setup_contract.sh` is the ten-assertion check that
   plants all four absences before sourcing.""")

# --- 5. step 7: Nsight, the second clean, and where it lands --------------
edit("step7 nsight + clean (F78)",
     """7. Install the five Nsight packages of row 3. They sit outside the lock by nature; a rebuild that
   stops after step 5 has no profiler at all.""",
     """7. Install the five Nsight packages of row 3, then `sudo apt-get clean` a second time (F78).
   They sit outside the lock by nature; a rebuild that stops after step 5 has no profiler at
   all. They install to **`/opt/nvidia`, outside `/usr/local/cuda-13.2`**, which is why step
   1's budget adds their 2.4 GiB rather than counting it inside the toolkit - a
   toolkit-directory measurement misses them entirely.""")

# --- 6. step 9: the exit code is not the answer --------------------------
edit("step9 D-39 by hand (F81)",
     """9. Run `.venv/bin/python spikes/4L/sample_power.py rebuild` and compare the load-window distinct
   set against row 1.""",
     """9. Run `.venv/bin/python spikes/4L/sample_power.py rebuild` and compare the load-window distinct
   set against row 1. **Compare it by hand, and do not read the script's exit code as the
   answer.** `sample_power.py` computes that distinct set and prints it, and does **not** make
   a set with more than one member a failure - so a run whose ceiling wobbled exits 0 and
   writes a plausible summary (F81). D-39's rule is that such a run is **invalid, not
   adjusted**. `scripts/env/capture.py` enforces it by construction from 5C; this spike has
   not yet been given the same three lines.""")

# --- 7. steps 11 and 12 --------------------------------------------------
edit("steps 11-12 (F77/RV-30)",
     "10. Record the whole comparison in `docs/project/VERIFICATION-LOG.md`.",
     """10. Record the whole comparison in `docs/project/VERIFICATION-LOG.md`.
11. **Test F77 before unregistering anything.** Read `df --block-size=1 /mnt/c`, then
    `rm -rf ~/.cache/pip`, then read it again. If `C:` free space does not move, a WSL2
    virtual disk does not return deleted space to the host without compaction, and step 1's
    space-recovery remedy is void for every future rebuild. The cost of the test is
    re-downloading 2.85 GiB later, which is why it is the builder's call and not automatic.
12. **Unregister the test distribution**, which returns the whole 19.53 GiB. This is the
    load-bearing mitigation for RV-30 rather than a tidy-up: RV-30 reads session-start
    values, so a peak inside one session never produces two consecutive low readings, but a
    distribution left registered does. Unregistering is **irreversible** - confirm the name
    against `wsl --list -v` first, and take the free-space reading afterwards.""")

# --- 8-10. section 5's three stale rows ----------------------------------
edit("s5 item 4 (F34 closed)",
     "| 4 | `spikes/4L/sample_power.py` has **no cool-down between runs**, so consecutive runs are not thermally matched and their clock medians are not comparable. `capture.sh` gains one (F34) | 5C |",
     "| 4 | `spikes/4L/sample_power.py` has **no cool-down between runs**, so consecutive runs are not thermally matched and their clock medians are not comparable (F34). **CLOSED for new work 2026-11-28:** `scripts/env/capture.sh` cools down to a floor-relative target on **two** dimensions - temperature and SM clock, because the card holds its boosted clock after work stops (RV-33) - with the timeout as a failure rather than a silent continue, invoked by `run` before any sampling (F103). `sample_power.py` itself is unchanged and still has none, which is why step 9 runs it as a comparison only | closed |")

edit("s5 item 6 (F69/F76)",
     "| 6 | `env/requirements.lock` and `env/setup.sh` do not exist yet | 5C |",
     "| 6 | **CLOSED 2026-11-28: all three 5C artefacts exist.** `env/requirements.lock` (2026-11-26), `scripts/env/setup.sh` (2026-11-27) and `scripts/env/capture.sh` (2026-11-28). Note the path - `scripts/env/`, not `env/`; this row carried the wrong one until today (F76) | closed |")

edit("s5 item 12 (F45 measured)",
     "| 12 | **The disk cost of the 5D rebuild has never been computed.** Free space read 59 GB on 2026-11-25 against RV-30's 45 GB trigger and 30 GB floor, so a rebuild costing more than about 14 GB arms that trigger by this project's own action. Section 3 step 1 now requires the budget before the import (F45) | 5D |",
     "| 12 | **MEASURED 2026-11-27: 19.53 GiB**, four components by two agreeing routes (F45). Section 3 step 1 is the single home for the figure; this row is a pointer. Against the 2026-11-28 reading of 69.04 GiB free the rebuild leaves about 49.5 GiB, **above** RV-30's 45 GB trigger - reversing the conclusion that held on 2026-11-27. **Two parts stay open:** the apt download peak, mitigated by the `apt-get clean` steps rather than measured (F78), and whether deleting the pip cache returns anything to `C:` at all, which step 11 tests (F77) | 5D |")


def main():
    if not ENV.exists():
        print("FATAL: run from the repository root; %s not found" % ENV)
        return 1
    body = ENV.read_text(encoding="utf-8")
    problems, applied = [], []
    for e in EDITS:
        if e["new"] in body:
            problems.append("%s: ALREADY APPLIED" % e["id"])
            continue
        n = body.count(e["old"])
        if n != 1:
            problems.append("%s: target occurs %d times (need exactly 1)\n"
                            "        first line: %s"
                            % (e["id"], n, e["old"].split("\n")[0][:70]))
            continue
        body = body.replace(e["old"], e["new"], 1)
        applied.append(e["id"])
    if problems:
        print("NOTHING WRITTEN. %d of %d edits failed:\n" % (len(problems), len(EDITS)))
        for pr in problems:
            print("  " + pr)
        return 1
    ENV.write_text(body, encoding="utf-8")
    print("ALL %d EDITS APPLIED\n" % len(applied))
    for a in applied:
        print("  " + a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
