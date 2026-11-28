# ENVIRONMENT — the host state a rebuild does not reproduce

Owner stage: 05 · condition C1 of gate 04 · re-read at every gate that measures anything
Date: 2026-11-24

## What this file is, and is not

Stage 5D rebuilds this project's stack on a fresh Ubuntu installation **from this file and from
nothing else**. What belongs here is therefore exactly what that rebuild will *not* reproduce by
itself: state that lives on the Windows host, or in apt outside the hash-pinned lock.

**This file pins no version numbers.** Those have owners:

| What | Owner | Why not here |
|---|---|---|
| Python, torch, Triton, CUDA toolkit, host compiler pins | `docs/architecture/adr/ADR-0001-env-pins.md` | One fact, one home. A second copy goes stale and is then two claims |
| Python package versions and hashes | `env/requirements.lock`, from stage 5C | Generated, not written |
| Device facts — SM count, VRAM, L2, compute capability | `docs/environment/SUPPORT-MATRIX.md` | That file is the repository's home for them |

**No row below is a performance claim.** No timing number exists in this project yet; the harness
is built at stage 08.

---

## 1 · Host-state rows (class established by AM-08 / CR-11; row 1 refined by AM-09 / CR-13)

Each row carries the pinned value, the command that reads it, and the consequence of a mismatch.
Gate 05's rebuild criterion reads **every** row on the fresh distribution and compares.

### Row 1 · Enforced GPU power ceiling — and the Windows power state that accompanies it

| Field | Value |
|---|---|
| **Pinned** | `Current Power Limit` = **30.00 W**, against Requested 50.00 W, Default 50.00 W, Max 50.00 W, Min 1.00 W |
| **Accompanying host state, all pinned together** | Power source **AC (mains)** · Windows power plan **Balanced** (`381b4222-f694-41f0-9685-ff5bb260df2e`) · NitroSense Mode tab **AC**, plan **Balance**, Fan Control **Auto**, CoolBoost **off** |
| **Read how** | **Under sustained load, never at idle.** `.venv/bin/python spikes/4L/sample_power.py <label>` — read the line `Current Power Limit distinct set, load window`. Context read, idle: `nvidia-smi -q -d POWER` |
| **Mismatch means** | A run whose distinct-value set across the run has **more than one member is invalid, not adjusted**. Any loaded reading other than 30.00 W is invalid. A run is comparable only to a roofline denominator measured under the same ceiling (AM-09) |
| **Evidence** | `results/env/4L_balance.txt` · `results/env/4L_high-performance.txt` · `results/env/4K_power_under_load.txt` |

**Why under load.** At idle this reading is not stable: `enforced.power.limit` returned 50 W and
then 30 W inside one twenty-second window on 2026-11-23 with the mains adapter untouched. Pinning
an idle value gives a criterion that cannot *pass*. Under sustained load it is exact.

**Why this profile, measured rather than assumed.** On 2026-11-24 the same 140-sample protocol was
run under NitroSense **Balance** and **High-Performance**, changing nothing else. Both produced
`Current Power Limit` = `['30.00']` across the load window, 0 samples disagreeing out of 140 each.
**NitroSense does not control this ceiling.** Balance is pinned because it is the state every
measurement in this repository was taken under, and the alternative was shown to buy nothing.
The two runs were **not** thermally matched (36.3 °C against 47.3 °C at start), so their clock
medians — 1035 MHz and 998 MHz — are not comparable and no conclusion is drawn from them (F34).

**Known unknown, recorded rather than hidden.** What moves the ceiling between 50 W and 30 W is
unexplained. Both `nvidia-smi` query forms agree with each other in 280 samples, so the 50 W
reading was `Current Power Limit` genuinely being 50 W, not a different quantity. Nothing this
project controls induces that state; `nvidia-smi -pl` is refused even as root under WSL2. The
distinct-set rule catches a run taken in it without needing the mechanism.

**This part is power-limited, not thermally limited.** The device reports Slowdown 94 °C,
Shutdown 99 °C, Target Specification 87 °C. Peak observed under 120 s of 100 % load: 60 °C and
63 °C, with draw at 94–98 % of the 30 W cap throughout.

### Row 2 · GPU performance-counter permission

| Field | Value |
|---|---|
| **Pinned** | **RESTRICTED** — "Restrict access to the GPU performance counters to admin users only (recommended)", the Windows default |
| **Set where** | Windows NVIDIA Control Panel → Desktop/Developer → Manage GPU Performance Counters. Not readable from inside WSL |
| **Read how** | Run Nsight Compute against any kernel and observe the refusal. `nsys status -e` does **not** check this and is silent on it |
| **Mismatch means** | Counters becoming available is a host-state change that alters what evidence this project is permitted to hold. It is recorded as a change, never silently accepted. **No hardware-counter data appears anywhere in this project** (D-32). Nsight Systems tracing is unaffected and works |
| **Evidence** | `results/env/4C_cell11_profilers.txt:73` — `ERR_NVGPUCTRPERM - The user does not have permission to access NVIDIA GPU Performance Counters on the target device 0` |

Stage 26C is **blocked by evidence, not cut**: one setting reverses it, and a cut is not reversible.

### Row 3 · Nsight packages — installed by apt, outside the lock

| Field | Value |
|---|---|
| **Pinned** | **Five** packages: `cuda-nsight-13-2` 13.2.86-1 · `cuda-nsight-compute-13-2` 13.2.2-1 · `cuda-nsight-systems-13-2` 13.2.2-1 · `nsight-compute-2026.1.1` 2026.1.1.2-1 · `nsight-systems-2025.6.3` 2025.6.3.541-256337736014v0 |
| **Read how** | `dpkg -l \| grep -i nsight` — **then read every line returned.** `ubuntu-insights` matches this pattern because `ubuntu-i·nsight·s` contains the letters, and it is not an Nsight package (F27) |
| **Mismatch means** | These are system-wide apt packages that no `requirements.lock` will ever mention. A rebuild that installs the locked Python environment and stops has no profiler at all, and REQ-S13's Nsight Systems half becomes unsatisfiable |

### Row 4 · WSL memory and swap allocation

| Field | Value |
|---|---|
| **Pinned** | `[wsl2]` · `memory=5GB` · `swap=8GB`, in `%USERPROFILE%\.wslconfig` on the Windows host |
| **Read how** | `cat /mnt/c/Users/*/.wslconfig` for the setting; **`free -h` for the effect.** Verify the effect, never the file (§5.5 Rule 1) |
| **Mismatch means** | On WSL's default allocation (50 % of an 8 GB host = 3.5 GiB), a single `nvcc` compiling `torch/extension.h` was **OOM-killed**. **The CUDA arm of this project — which the charter forbids cutting — is unbuildable on the default host configuration** (D-34, RV-34) |
| **Reversal trigger** | If Windows becomes unresponsive during builds, lower to `memory=4GB`, which still clears the measured requirement. Any build peaking above 4.0 GiB, or any OOM kill, reopens RV-34 |

The file carries its own reason and reversal trigger as comments. **Every host-state row should
copy that pattern:** a pinned value that does not say why it is pinned gets changed by someone who
does not know what it protects.

---

## 2 · Shell environment

| Variable | Pinned | Read how | Mismatch means |
|---|---|---|---|
| `TMPDIR` | `$HOME/.tmp` | `echo "$TMPDIR"` — the **value in a live shell**, not the line in `~/.bashrc` | `/tmp` on this distribution is a **1.8 GB tmpfs**. With `TMPDIR` unset, `pip install torch` fails with "No space left on device" while the disk has over 900 GB free (D-17) |
| `CUDA_HOME` | `/usr/local/cuda-13.2` | `echo "$CUDA_HOME"` | `torch.utils.cpp_extension` cannot locate `nvcc`; the CUDA arm does not build |
| `TRITON_DEFAULT_FP_FUSION` | **Deliberately unset in the shell.** Set to `1` per-run, inside each spike's own environment | `grep -n TRITON_DEFAULT_FP_FUSION spikes/*/*.py` | See the scope note below — an exported value here would be the wrong fix |
| `CC` and `CXX` | **Both unset in the interactive shell, deliberately.** The host compiler is named by the build file, not by shell state | `echo "CC=[$CC] CXX=[$CXX]"` - both must print empty brackets | `torch.utils.cpp_extension` reads `CXX` for C++ translation units and defaults to the unversioned `c++` (`cpp_extension.py:271`), and passes `-ccbin` to nvcc from **`CC`** only, and only when the extension's own flags do not already set one (lines 939 and 942). Unset therefore selects the alias silently - 15.2.0 today, whatever apt installs tomorrow. Exporting them is the wrong fix for the same reason as the fp-fusion variable below: it makes which compiler built a run depend on whose shell launched it. The stage-15 build file is the authority; ADR-0001 reversal trigger 4 is the check (F42) |
| `TORCH_DONT_CHECK_COMPILER_ABI` | **Never set, in any shell or script of this project** | `echo "[$TORCH_DONT_CHECK_COMPILER_ABI]"` must print `[]` | Set to any of `ON 1 YES TRUE Y` it disables **both** of torch's build-time guards at once: the ABI-compatibility check (`cpp_extension.py:170`) and the CUDA-version and compiler-bound check (line 235). Those are the only automatic compiler guards this stack has, and on CUDA 13.2 the second already does nothing - see section 5 item 10 |

### The fp-fusion scope, stated exactly, because "pinned to 1" is misleading on its own

Triton 3.9.0 reads this variable at `knobs.py:499` as `env_bool("TRITON_DEFAULT_FP_FUSION", True)`.
**Unset therefore means fusion ENABLED**, identical in arithmetic to `=1`, and 3.9 warns that the
default flips to DISABLED in 3.10 (R22). The pin is real but **scoped**, as ADR-0001 states: until
the harness exists at stage 08, each spike that runs a Triton kernel sets it in that spike's own
environment and the setting is visible in that spike's evidence file. `spikes/4I/test_fp64.py:32`
and `spikes/4J/tl_dot_sm75.py:42` both do. From stage 08 the harness sets it and records it in run
metadata; the stage-16 environment test asserts it.

Exporting it in `~/.bashrc` would be the wrong fix: it would make a run's arithmetic depend on
whose shell launched it, which is the opposite of recording it per run.

**Open:** which process sets it for a GPU-less CI run, where no harness runs, is undecided
(owner 15C/16).

### The WSL clock runs in UTC

Not a variable, but it changes how every record is read. `date` here returns UTC, roughly 5½ hours
behind local time. Two consequences:

1. `capture.sh` (5C) labels every timestamp UTC explicitly, so a reader never has to guess.
2. **Git stamps commits in UTC.** Work done between 00:00 and 05:30 IST is dated the *previous*
   calendar day in git history, while the status log is keyed by local worked day. A day's commit
   count therefore comes from an explicit range — `git rev-list --count <base>..HEAD` — never from
   a date filter. This is the same rule RV-25 already forces on gate checks.

---

## 3 · The rebuild procedure stage 5D follows

Performed on a **fresh Ubuntu 26.04 WSL2 distribution on the same Windows host**. The host state
of section 1 is not reinstalled by this procedure — it is *compared against*, because it belongs
to Windows or to apt, not to the distribution image.

1. Install a fresh Ubuntu 26.04.1 LTS WSL2 distribution. Record free space on `C:` before and
   after; RV-30's trigger is two consecutive session-start readings below 45 GB.
   **The budget is MEASURED, 2026-11-27, and is no longer computed at this step** (F45).
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
   sparse is `[UNKNOWN]`; step 11 tests it (F77).
2. **Before installing anything else, read every row of section 1 and compare.** Record each
   result, pass or fail. A mismatch is recorded, never silently accepted (AM-08).
3. Install the distribution prerequisites named in ADR-0001 — `python3`, `python3-venv`, the build
   toolchain, the CUDA toolkit and `g++-15` **by explicit name, never the bare `gcc`/`g++` alias**
   (RV-28: nvcc 13.2 hard-errors above GCC major 15, and the distribution default is 15.2.0, so
   there is zero headroom). **Installing it is necessary and not sufficient: nothing
   selects it automatically.** `torch.utils.cpp_extension` reads `CXX` for C++
   translation units and defaults to the unversioned `c++`, and passes `-ccbin` to nvcc
   from `CC` only, and only when the extension's own flags do not already set one. The
   build file written at stage 15 therefore names `-ccbin /usr/bin/g++-15` explicitly
   and sets `CXX`; reversal trigger 4 of ADR-0001 is what catches a build that did
   neither (F42).
   **Then two checks this procedure lacked until 2026-11-28.** First
   `test -x "$CUDA_HOME/bin/nvcc"`. Step 6 pins `CUDA_HOME` to `/usr/local/cuda-13.2`, and
   `scripts/env/test_setup_contract.sh` checks only that the variable is *set* - it never
   looks for a toolkit at that path, which is V27's stated exclusion. If apt lands the
   toolkit at a different patch path the variable still passes every assertion and the CUDA
   arm fails at step 8 with nothing upstream to blame. Second `sudo apt-get clean`: apt
   stages every `.deb` in `/var/cache/apt/archives` before installing, so without this the
   transient disk peak exceeds step 1's installed figure by several gigabytes (F78).
4. Create the virtual environment on the pinned interpreter. Check it with **`python3 --version`**,
   never with the apt package version: `apt-cache policy python3` reports 3.14.3 while the
   interpreter reports 3.14.4, because `python3` is a metapackage and the binary belongs to
   `python3.14-minimal` (F19). A pin checked against the package can never detect an interpreter
   change.
5. Install from the hash-pinned lock, **with `--no-cache-dir`**:
   `pip install --no-cache-dir --require-hashes -r env/requirements.lock`.
   The lock exists as of 2026-11-26: **82 packages, 1152 hashes**, resolved from PyPI alone
   (D-45) against `env/measured.txt` as a constraint so it reproduces what was measured
   rather than what was newest (F62). `--no-cache-dir` is not tidiness - a rebuild warmed
   by the old machine's pip cache is not a fresh-distribution rebuild, and it keeps
   2.85 GiB out of the footprint. Hash-checking is all-or-nothing across every requirement
   and every transitive dependency (F40), so one failure fails the whole install, and that
   is the intended behaviour rather than a problem to work around.
6. Apply the shell environment of section 2 by **sourcing** it, never executing it:
   `. scripts/env/setup.sh`.
   **The path is `scripts/env/`, not `env/`.** `env/` holds declarations and `scripts/env/`
   holds executables, ruled 2026-11-26 (F60) - a ruling recorded in project memory and never
   propagated into this file, so this step named a path that will never exist until
   2026-11-28 (F76). The script refuses to be executed rather than sourced, because an
   executed copy exits 0 having changed nothing, which is this project's most-repeated
   failure mode (D-46). Four of section 2's seven pinned items are **absences**, so a script
   that exports `TMPDIR` and `CUDA_HOME` and stops has done two sevenths of the job and
   looks finished; `scripts/env/test_setup_contract.sh` is the ten-assertion check that
   plants all four absences before sourcing.
7. Install the five Nsight packages of row 3, then `sudo apt-get clean` a second time (F78).
   They sit outside the lock by nature; a rebuild that stops after step 5 has no profiler at
   all. They install to **`/opt/nvidia`, outside `/usr/local/cuda-13.2`**, which is why step
   1's budget adds their 2.4 GiB rather than counting it inside the toolkit - a
   toolkit-directory measurement misses them entirely.
8. Run the committed spikes as smoke tests, in this order, and keep every output:
   `spikes/4G/test_triton_interpret.py` (no GPU needed) → `spikes/4I/` (fp64 `gradcheck`, which
   carries a planted-wrong control that must be rejected) → `spikes/4J/` (`tl.dot` against two
   derived bars) → `spikes/4E/` (the CUDA extension, roughly 193 s for one translation unit). That build prints
   *There are no g++ version bounds defined for CUDA version 13.2* - expected, not a
   defect; section 5 item 10.
9. Run `.venv/bin/python spikes/4L/sample_power.py rebuild` and compare the load-window distinct
   set against row 1. **Compare it by hand, and do not read the script's exit code as the
   answer.** `sample_power.py` computes that distinct set and prints it, and does **not** make
   a set with more than one member a failure - so a run whose ceiling wobbled exits 0 and
   writes a plausible summary (F81). D-39's rule is that such a run is **invalid, not
   adjusted**. `scripts/env/capture.py` enforces it by construction from 5C; this spike has
   not yet been given the same three lines.
10. Record the whole comparison in `docs/project/VERIFICATION-LOG.md`.
11. **Test F77 before unregistering anything.** Read `df --block-size=1 /mnt/c`, then
    `rm -rf ~/.cache/pip`, then read it again. If `C:` free space does not move, a WSL2
    virtual disk does not return deleted space to the host without compaction, and step 1's
    space-recovery remedy is void for every future rebuild. The cost of the test is
    re-downloading 2.85 GiB later, which is why it is the builder's call and not automatic.
12. **Unregister the test distribution**, which returns the whole 19.53 GiB. This is the
    load-bearing mitigation for RV-30 rather than a tidy-up: RV-30 reads session-start
    values, so a peak inside one session never produces two consecutive low readings, but a
    distribution left registered does. Unregistering is **irreversible** - confirm the name
    against `wsl --list -v` first, and take the free-space reading afterwards.

**A sanitizer run from stage 17 onward disables the caching allocator or it is not a sanitizer
run:** `compute-sanitizer` reported 0 errors on a kernel writing 200 floats out of bounds, and
205 errors once `PYTORCH_NO_CUDA_MEMORY_CACHING=1` was set.

---

## 4 · What gate 05 checks

Gate 05's rebuild criterion gains one step over its original wording (AM-08):

> Read **every** host-state row in section 1 on the fresh distribution and compare it against its
> pinned value. Record each comparison. A mismatch is recorded and ruled, never silently accepted.

A rebuild that reproduces the Python environment and skips section 1 has not tested the thing
this file exists for.

---

## 5 · Open items and known gaps, recorded rather than omitted

| # | Item | Owner |
|---|---|---|
| 1 | What moves the enforced ceiling between 50 W and 30 W is **unexplained**. NitroSense is ruled out by measurement; the Windows power plan has **not** been tested as the cause (R21, narrowed) | 07 |
| 2 | **Thermal ordering is a confound for every later timing comparison.** Arms run as consecutive blocks start progressively hotter and clock lower, and the difference reads as a kernel result. Logging temperature does not remove the bias; interleaved or randomised arm ordering plus a stated starting-temperature precondition does (RV-39) | 07 · 08 |
| 3 | **120 s does not reach steady state.** The SM clock was still falling across thirds in both 4L runs (1065→1005 and 1005→982 MHz). Measured ceilings need longer runs | 07 |
| 4 | `spikes/4L/sample_power.py` has **no cool-down between runs**, so consecutive runs are not thermally matched and their clock medians are not comparable (F34). **CLOSED for new work 2026-11-28:** `scripts/env/capture.sh` cools down to a floor-relative target on **two** dimensions - temperature and SM clock, because the card holds its boosted clock after work stops (RV-33) - with the timeout as a failure rather than a silent continue, invoked by `run` before any sampling (F103). `sample_power.py` itself is unchanged and still has none, which is why step 9 runs it as a comparison only | closed |
| 5 | `results/env/4K_power_under_load.txt` was produced by an uncommitted command and cannot be regenerated. `spikes/4L/sample_power.py` is the committed replacement (F32) | closed |
| 6 | **CLOSED 2026-11-28: all three 5C artefacts exist.** `env/requirements.lock` (2026-11-26), `scripts/env/setup.sh` (2026-11-27) and `scripts/env/capture.sh` (2026-11-28). Note the path - `scripts/env/`, not `env/`; this row carried the wrong one until today (F76) | closed |
| 7 | Which process sets `TRITON_DEFAULT_FP_FUSION` for a GPU-less CI run is undecided (F33) | 15C · 16 |
| 8 | Build-memory peaks recorded in GiB may be decimal GB mislabelled — 2785948 kB is 2.79 GB or **2.66 GiB**. The direction is favourable, more headroom than recorded (F23) | next docs pass |
| 9 | `pre-commit` is installed inside the venv only, so gate 05's criterion must check that **the hook fires**, not that the command exists (RV-29) | gate 05 |
| 10 | PyTorch defines **no host-compiler version bounds for CUDA 13.2**: `CUDA_GCC_VERSIONS` ends at 13.0, so `_check_cuda_version` logs *There are no g++ version bounds defined for CUDA version 13.2* and continues. **That warning is expected output of every CUDA build here, not a defect.** The only ceiling in force is nvcc's own `crt/host_config.h` above GCC major 15 (V22, RV-28) | recorded |
| 11 | **Installing `g++-15` does not select it.** The C++ path reads `CXX` and defaults to `c++`; the nvcc path takes `-ccbin` from `CC` and only when the build's own flags do not set one. The stage-15 build file must name `-ccbin /usr/bin/g++-15` explicitly and set `CXX`, because a shell variable is lost the moment a build runs without it (F42) | 15 |
| 12 | **MEASURED 2026-11-27: 19.53 GiB**, four components by two agreeing routes (F45). Section 3 step 1 is the single home for the figure; this row is a pointer. Against the 2026-11-28 reading of 69.04 GiB free the rebuild leaves about 49.5 GiB, **above** RV-30's 45 GB trigger - reversing the conclusion that held on 2026-11-27. **Two parts stay open:** the apt download peak, mitigated by the `apt-get clean` steps rather than measured (F78), and whether deleting the pip cache returns anything to `C:` at all, which step 11 tests (F77) | 5D |
