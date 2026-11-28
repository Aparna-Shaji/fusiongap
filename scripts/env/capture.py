#!/usr/bin/env python3
"""scripts/env/capture.py - the telemetry capture instrument, stage 5C.

Adopts spikes/4L/sample_power.py (see its own header: "5C's capture.sh adopts
it") and adds the three controls RV-39 names, which 4L has none of.

WHAT IT FIXES ON THE WAY IN
  F34   4L has no cool-down. Its two arms started at 36.3 C and 47.3 C, which is
        why 4L's ceiling comparison stands and its clock comparison does not.
  RV-39 Thermal ordering is a confound and logging temperature does not remove
        it. Controls: a starting-temperature precondition, a cool-down to a
        target, and interleaved arm ordering.
  RV-33 The GPU holds its boosted clock after work stops, so the precondition is
        two-dimensional. A temperature-only precondition passes a GPU that is
        cool and still boosted.
  F81   4L COMPUTES D-39's invalidity condition and does not act on it. Here a
        load window with more than one distinct enforced limit is INVALID.
  F82   4L puts its verdict on the last line, under two device dumps. Here the
        verdict is line 1.
  Sec 2 Every written timestamp carries an explicit Z. This clock runs in UTC and
        the driver's own stamp does not say so - measured 2026-11-28,
        "2026/11/28 10:58:22.733" while the wall clock read 16:28 local.

SCOPE, stated rather than implied. 5C CONTROLS temperature and clock. It RECORDS
the other shared state between arms and hands it to stage 08: the CUDA caching
allocator pool, the Inductor and Triton compile caches, and free VRAM. 5C's box
is under two hours; the harness is stage 08's.

NO numpy and NO pytest: both are hash-pinned in env/requirements.lock and not
installed until 5D (RV-36). Standard library only.

Specified by scripts/env/test_capture_contract.sh. Read that file for why each
check exists.
"""
import argparse
import csv
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# --- constants, each with its basis ----------------------------------------
# Measured 2026-11-28, 24 samples at 5 s with the GPU idle:
#   temperature  median 42.40 C, range 0.30 C, thirds drift +0.06 C
#   SM clock     300 MHz, zero variance
#   utilisation  0 throughout
# Targets are FLOOR-RELATIVE. An absolute 40 C target - the obvious reading of
# 4L's 36.3 C arm - is unsatisfiable on this machine today. Measured, not argued.
DTEMP_C = 2.0          # 6.7x the measured idle spread, 20x sensor quantisation,
                       # 5.5x smaller than the 11.0 C gap that produced F34.
                       # REVERSAL TRIGGER: re-derive from stage 07's measurement
                       # of SM clock against temperature. Today's basis is the
                       # instrument's noise floor, which is weaker.
DCLOCK_MHZ = 100.0     # 100 MHz over a zero-variance floor; 580 MHz below the
                       # lowest boosted clock ever observed here (982 MHz).
EQ_TOL_C = 0.5         # 8x today's measured thirds drift. Rejects a window
                       # cooling faster than 0.25 C/min, which is what makes a
                       # floor reading a floor and not a snapshot.
FLOOR_WINDOW_S = 120.0 # The configuration proved on 2026-11-28. Not shortened:
PERIOD_S = 5.0         # a shorter window is unmeasured.
COOLDOWN_TIMEOUT_S = 300.0  # [VERIFY: provisional] No cooling-rate measurement
                       # exists. Set generously, FAILS loudly, and every
                       # cool-down's actual duration is logged so this becomes
                       # empirical after a few runs.
TEMP_ABORT_C = 85.0    # inherited from 4L
IDLE_S = 10.0          # inherited from 4L: the idle windows are the negative
LOAD_S = 120.0         # control. 120 s does NOT reach steady state (V21, open
                       # item 3, owner 07) - raised there, not guessed here.
UTIL_MIN_PCT = 90.0    # inherited from 4L

FIELDS = ["phase", "temp_c", "sm_mhz", "draw_w", "util_pct", "enforced_w", "current_w"]
CSV_COLS = ["stamp_utc", "t_s"] + FIELDS

QUERY = "temperature.gpu,clocks.sm,power.draw,utilization.gpu,enforced.power.limit"

LOAD_SRC = """
import sys, time, torch
d = torch.device('cuda')
a = torch.randn(4096, 4096, device=d)
b = torch.randn(4096, 4096, device=d)
end = time.time() + float(sys.argv[1])
while time.time() < end:
    c = a @ b
torch.cuda.synchronize()
"""


# --- small helpers ---------------------------------------------------------
def die(msg, code=2):
    sys.stderr.write("capture.py: %s\n" % msg)
    sys.exit(code)


def utc_stamp():
    """Explicit Z. Section 2: a reader never has to guess the zone."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def median(xs):
    s = sorted(xs)
    n = len(s)
    if not n:
        return float("nan")
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def w2(x):
    """Normalise a power reading to 2 dp BEFORE set comparison. 4L compares raw
    strings, so '30.0' and '30.00' would count as two distinct values and fire
    D-39 on a formatting difference."""
    return "%.2f" % float(x)


def f(row, key):
    return float(str(row[key]).strip())


# --- sample sources: one live query per sample (D-31), or a replay ----------
def smi(args):
    return subprocess.run(["nvidia-smi"] + args, capture_output=True, text=True).stdout


def live_current_limit():
    """The FIRST 'Current Power Limit' is the GPU ceiling. A later one appears
    under 'Module Power Readings' and reads N/A on this card - 4L's note."""
    for line in smi(["-q", "-d", "POWER"]).splitlines():
        if "Current Power Limit" in line:
            return line.split(":", 1)[1].strip().replace(" W", "")
    return "NOT_FOUND"


def live_sample(phase):
    out = smi(["--query-gpu=" + QUERY, "--format=csv,noheader,nounits"]).strip()
    parts = [x.strip() for x in out.split(",")]
    if len(parts) < 5:
        die("nvidia-smi returned %d fields, expected 5: %r" % (len(parts), out))
    return {"phase": phase, "temp_c": parts[0], "sm_mhz": parts[1],
            "draw_w": parts[2], "util_pct": parts[3], "enforced_w": parts[4],
            "current_w": live_current_limit()}


class Replay:
    def __init__(self, path):
        with open(path, newline="", encoding="utf-8") as fh:
            self.rows = [{k: (v or "").strip() for k, v in r.items()}
                         for r in csv.DictReader(fh)]
        if not self.rows:
            die("replay file %s has no data rows" % path)
        self.i = 0

    def take(self):
        if self.i >= len(self.rows):
            return None
        row = dict(self.rows[self.i])
        self.i += 1
        return row

    def all(self):
        return [dict(r) for r in self.rows]


def source(args):
    return Replay(args.replay) if getattr(args, "replay", None) else None


# --- floor -----------------------------------------------------------------
def collect_floor(rep, period, window):
    if rep is not None:
        return rep.all()
    rows, t0 = [], time.time()
    while time.time() - t0 < window:
        rows.append(live_sample("idle"))
        time.sleep(period)
    return rows


def cmd_floor(args):
    rows = collect_floor(source(args), args.period, FLOOR_WINDOW_S)
    n = len(rows)
    if n < 6:
        print("FLOOR REFUSE reason=too_few_samples samples=%d need>=6" % n)
        return 1

    temps = [f(r, "temp_c") for r in rows]
    clocks = [f(r, "sm_mhz") for r in rows]
    utils = [f(r, "util_pct") for r in rows]

    reasons = []
    # Not a floor if the GPU is doing anything.
    if max(utils) > 0.5:
        reasons.append("utilisation reached %.0f%% - this window is not a floor"
                       % max(utils))
    # Not a floor if it is still cooling. Thirds, as V21 reads 4L's clocks.
    k = n // 3
    first, last = median(temps[:k]), median(temps[-k:])
    if abs(first - last) > EQ_TOL_C:
        reasons.append("thirds differ by %.2f C (> %.2f) - still cooling, so "
                       "this is a snapshot not an equilibrium"
                       % (abs(first - last), EQ_TOL_C))

    t_med, c_med = median(temps), median(clocks)
    if reasons:
        print("FLOOR REFUSE samples=%d temp_c=%.2f clock_mhz=%.0f" % (n, t_med, c_med))
        for r in reasons:
            print("  reason: %s" % r)
        return 1

    print("FLOOR OK temp_c=%.2f clock_mhz=%.0f samples=%d "
          "range_c=%.2f thirds_drift_c=%.2f"
          % (t_med, c_med, n, max(temps) - min(temps), last - first))
    print("  targets: temp_c<=%.2f  clock_mhz<=%.0f  (floor + %.1f C / + %.0f MHz)"
          % (t_med + DTEMP_C, c_med + DCLOCK_MHZ, DTEMP_C, DCLOCK_MHZ))
    return 0


# --- precondition ----------------------------------------------------------
def check_precondition(row, floor_t, floor_c):
    t_target = floor_t + DTEMP_C
    c_target = floor_c + DCLOCK_MHZ
    temp, clock = f(row, "temp_c"), f(row, "sm_mhz")
    bad = []
    if temp > t_target:
        bad.append("temperature %.2f C above target %.2f C" % (temp, t_target))
    # RV-33: the GPU holds its boosted clock after work stops, so temperature
    # alone can pass a GPU that is cool and still boosted.
    if clock > c_target:
        bad.append("SM clock %.0f MHz above target %.0f MHz (post-boost, RV-33)"
                   % (clock, c_target))
    return bad, temp, clock, t_target, c_target


def cmd_precondition(args):
    rep = source(args)
    row = rep.take() if rep is not None else live_sample("idle")
    if row is None:
        die("replay exhausted before a single sample")
    bad, temp, clock, tt, ct = check_precondition(row, args.floor_temp, args.floor_clock)
    state = "REFUSE" if bad else "PASS"
    print("PRECONDITION %s temp_c=%.2f clock_mhz=%.0f t_target=%.2f c_target=%.0f"
          % (state, temp, clock, tt, ct))
    for b in bad:
        print("  reason: %s" % b)
    return 1 if bad else 0


# --- cooldown --------------------------------------------------------------
def cmd_cooldown(args):
    rep = source(args)
    waited = 0.0
    last = None
    while True:
        row = rep.take() if rep is not None else live_sample("idle")
        if row is None:
            print("COOLDOWN TIMEOUT waited_s=%.1f reason=replay_exhausted "
                  "last_temp_c=%s last_clock_mhz=%s"
                  % (waited, last["temp_c"] if last else "none",
                     last["sm_mhz"] if last else "none"))
            return 1
        last = row
        bad, temp, clock, tt, ct = check_precondition(
            row, args.floor_temp, args.floor_clock)
        if not bad:
            print("COOLDOWN OK waited_s=%.1f temp_c=%.2f clock_mhz=%.0f "
                  "t_target=%.2f c_target=%.0f" % (waited, temp, clock, tt, ct))
            return 0
        if waited >= args.timeout:
            # A cool-down that gives up and PROCEEDS produces exactly the
            # confound it exists to remove, while looking like a controlled run.
            print("COOLDOWN TIMEOUT waited_s=%.1f timeout_s=%.1f "
                  "temp_c=%.2f clock_mhz=%.0f" % (waited, args.timeout, temp, clock))
            for b in bad:
                print("  still: %s" % b)
            return 1
        if rep is None:
            time.sleep(args.period)
        waited += args.period


# --- sequence --------------------------------------------------------------
def cmd_sequence(args):
    """Interleaved, not randomised. The confound here is MEASURED and monotone
    (V21: the SM clock falls across thirds), and interleaving guarantees balance
    where randomisation achieves it only in expectation - with n small, a random
    draw can still land heavily blocked. Generated in one place so a future
    pinned ordering is an option, not a rewrite."""
    if args.arms < 1 or args.repeats < 1:
        die("sequence needs --arms >= 1 and --repeats >= 1")
    if args.arms > 26:
        die("sequence supports at most 26 arms")
    labels = [chr(ord("A") + i) for i in range(args.arms)]
    cells = []
    for _ in range(args.repeats):
        cells.extend(labels)
    print(" ".join(cells))
    return 0


# --- verify ----------------------------------------------------------------
def verify_samples(rows):
    loads = [r for r in rows if str(r.get("phase", "")).strip() == "load"]
    idles = [r for r in rows if str(r.get("phase", "")).strip() == "idle"]
    reasons, stats = [], []

    if not loads:
        reasons.append("no load-window samples")
    if not idles:
        reasons.append("no idle-window samples - the negative control is absent")
    if reasons:
        return False, reasons, stats

    utils = [f(r, "util_pct") for r in loads]
    sm_load = [f(r, "sm_mhz") for r in loads]
    sm_idle = [f(r, "sm_mhz") for r in idles]
    draws = [f(r, "draw_w") for r in loads]
    temps = [f(r, "temp_c") for r in rows]

    # 4L's negative control, kept verbatim in intent.
    if max(utils) < UTIL_MIN_PCT:
        reasons.append("load window never reached %.0f%% utilisation (max %.0f%%)"
                       " - the load did not run" % (UTIL_MIN_PCT, max(utils)))
    if median(sm_load) <= median(sm_idle):
        reasons.append("load-window clock median %.0f MHz does not exceed idle "
                       "%.0f MHz - negative control failed"
                       % (median(sm_load), median(sm_idle)))

    # D-39, enforced rather than reported. This is F81.
    enf = sorted({w2(r["enforced_w"]) for r in loads})
    if len(enf) != 1:
        reasons.append("enforced.power.limit took %d distinct values across the "
                       "load window %s - D-39: INVALID, not adjusted"
                       % (len(enf), enf))

    if max(temps) >= TEMP_ABORT_C:
        reasons.append("thermal abort: %.1f C reached" % max(temps))

    cur = sorted({w2(r["current_w"]) for r in loads
                  if str(r["current_w"]).strip() not in ("NOT_FOUND", "")})
    dis = sum(1 for r in rows
              if str(r["enforced_w"]).strip() and str(r["current_w"]).strip()
              not in ("NOT_FOUND", "")
              and w2(r["enforced_w"]) != w2(r["current_w"]))

    stats.append("samples: %d total, %d load, %d idle" % (len(rows), len(loads), len(idles)))
    stats.append("enforced.power.limit distinct set, load window: %s" % enf)
    stats.append("Current Power Limit  distinct set, load window: %s" % cur)
    stats.append("samples where the two power-limit forms disagree: %d of %d "
                 "(recorded, not a validity condition - D-39 governs the "
                 "enforced form only)" % (dis, len(rows)))
    stats.append("load window: util max %.0f%%  sm median %.0f MHz  "
                 "sm min/max %.0f/%.0f" % (max(utils), median(sm_load),
                                           min(sm_load), max(sm_load)))
    stats.append("load window: draw median %.2f W  max %.2f W"
                 % (median(draws), max(draws)))
    stats.append("idle window: sm median %.0f MHz" % median(sm_idle))
    stats.append("temperature: max %.1f C over the whole run" % max(temps))
    k = max(1, len(sm_load) // 3)
    if len(sm_load) >= 6:
        stats.append("steady state: first-third sm median %.0f MHz, last-third "
                     "%.0f MHz (V21: 120 s does not reach steady state)"
                     % (median(sm_load[:k]), median(sm_load[-k:])))
    stats.append("NOT CONTROLLED AT 5C, recorded for stage 08: CUDA caching "
                 "allocator pool, Inductor and Triton compile caches, free VRAM")
    return (not reasons), reasons, stats


def cmd_verify(args):
    rep = source(args)
    if rep is None:
        die("verify needs --replay FILE; live verification happens inside 'run'")
    ok, reasons, stats = verify_samples(rep.all())
    print("VERDICT %s" % ("VALID" if ok else "INVALID"))
    for r in reasons:
        print("  reason: %s" % r)
    for s in stats:
        print("  %s" % s)
    return 0 if ok else 1


# --- run -------------------------------------------------------------------
def live_cell(period):
    rows, load, t0 = [], None, time.time()
    total = IDLE_S + LOAD_S + IDLE_S
    venv_py = REPO / ".venv" / "bin" / "python"
    try:
        while True:
            el = time.time() - t0
            if el >= total:
                break
            if load is None and el >= IDLE_S:
                load = subprocess.Popen([str(venv_py), "-c", LOAD_SRC, str(LOAD_S)],
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.PIPE)
            phase = "load" if IDLE_S <= el < IDLE_S + LOAD_S else "idle"
            row = live_sample(phase)
            row["_t"] = el
            rows.append(row)
            if f(row, "temp_c") >= TEMP_ABORT_C:
                break
            left = period - ((time.time() - t0) - el)
            if left > 0:
                time.sleep(left)
    finally:
        if load is not None and load.poll() is None:
            load.terminate()
            try:
                load.wait(timeout=10)
            except subprocess.TimeoutExpired:
                load.kill()
    return rows


def preflight(args):
    """RV-39's controls, INVOKED rather than merely available (F103).

    Until 2026-11-28 `run` sampled without calling any of these, so a measurement
    taken on a hot, still-boosted GPU was written out as VERDICT VALID - the exact
    confound this artefact exists to remove. Returns (ok, lines).
    """
    rep = Replay(args.preflight_replay) if args.preflight_replay else None
    if rep is None and args.replay:
        return True, ["PREFLIGHT SKIPPED - replay with no --preflight-replay"]

    # 1. the floor, measured this session: the targets are relative to it, because
    #    an absolute target is unsatisfiable on a warm day (measured 2026-11-28).
    rows = collect_floor(rep, args.period, FLOOR_WINDOW_S)
    if len(rows) < 6:
        return False, ["PREFLIGHT REFUSE - floor window has %d samples, need >= 6"
                       % len(rows)]
    temps = [f(r, "temp_c") for r in rows]
    clocks = [f(r, "sm_mhz") for r in rows]
    utils = [f(r, "util_pct") for r in rows]
    if max(utils) > 0.5:
        return False, ["PREFLIGHT REFUSE - floor taken under load, utilisation %.0f%%"
                       % max(utils)]
    k = len(rows) // 3
    drift = abs(median(temps[:k]) - median(temps[-k:]))
    if drift > EQ_TOL_C:
        return False, ["PREFLIGHT REFUSE - floor still cooling, thirds differ %.2f C "
                       "(> %.2f): that is a snapshot, not an equilibrium" % (drift, EQ_TOL_C)]
    ft, fc = median(temps), median(clocks)

    # 2. cool down on BOTH dimensions. The timeout is a FAILURE: a cool-down that
    #    gives up and proceeds produces the confound it exists to remove while
    #    looking like a controlled run.
    waited = 0.0
    while True:
        row = rep.take() if rep is not None else live_sample("idle")
        if row is None:
            return False, ["PREFLIGHT REFUSE - cool-down samples exhausted after %.1f s"
                           % waited]
        bad, temp, clock, tt, ct = check_precondition(row, ft, fc)
        if not bad:
            return True, ["PREFLIGHT OK floor_temp=%.2f floor_clock=%.0f "
                          "start_temp=%.2f start_clock=%.0f t_target=%.2f "
                          "c_target=%.0f waited_s=%.1f"
                          % (ft, fc, temp, clock, tt, ct, waited)]
        if waited >= COOLDOWN_TIMEOUT_S:
            msg = ["PREFLIGHT REFUSE - cool-down timed out after %.1f s" % waited]
            return False, msg + ["  still: " + b for b in bad]
        if rep is None:
            time.sleep(args.period)
        waited += args.period


def cmd_run(args):
    replaying = bool(args.replay)
    if replaying and not args.out:
        # A replayed file is not a measurement. It must never be able to land in
        # results/env by default.
        die("run --replay requires an explicit --out DIR: a replayed run is not "
            "a measurement and must not default into results/env")

    # RV-39's controls run BEFORE any sampling, and a refusal writes NOTHING.
    # Taking a measurement on a hot or still-boosted card and labelling it valid
    # is worse than not taking it at all (F103).
    pf_ok, pf_lines = preflight(args)
    if not pf_ok:
        for ln in pf_lines:
            print(ln)
        print("VERDICT REFUSED - no measurement taken, nothing written")
        return 1

    outdir = Path(args.out) if args.out else (REPO / "results" / "env")
    outdir.mkdir(parents=True, exist_ok=True)

    if replaying:
        rows = Replay(args.replay).all()
        for i, r in enumerate(rows):
            r["_t"] = i * args.period
    else:
        rows = live_cell(args.period)

    csv_path = outdir / ("capture_%s.csv" % args.label)
    txt_path = outdir / ("capture_%s.txt" % args.label)

    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(CSV_COLS)
        for r in rows:
            wr.writerow([utc_stamp(), "%.1f" % r.get("_t", 0.0)]
                        + [str(r[k]).strip() for k in FIELDS])

    ok, reasons, stats = verify_samples(rows)
    lines = ["VERDICT %s" % ("VALID" if ok else "INVALID")]   # F82: line 1.
    if replaying:
        lines.append("SOURCE REPLAY %s - NOT A MEASUREMENT" % args.replay)
    else:
        lines.append("SOURCE LIVE nvidia-smi, one query per sample (D-31)")
    lines.append("label: %s" % args.label)
    for ln in pf_lines:
        lines.append(ln)
    lines.append("clock: WSL, UTC. Every stamp above carries an explicit Z "
                 "(ENVIRONMENT.md section 2)")
    lines.append("protocol: %.0fs idle -> %.0fs load -> %.0fs idle, period %.1fs"
                 % (IDLE_S, LOAD_S, IDLE_S, args.period))
    for r in reasons:
        lines.append("reason: %s" % r)
    lines.extend(stats)
    body = "\n".join(lines) + "\n"
    txt_path.write_text(body, encoding="utf-8")
    if replaying:
        (outdir / ("capture_%s.REPLAY" % args.label)).write_text(
            "replayed from %s - not a measurement\n" % args.replay, encoding="utf-8")

    print(body, end="")
    print("written: %s" % csv_path)
    print("written: %s" % txt_path)
    return 0 if ok else 1


# --- env-report ------------------------------------------------------------
def cmd_env_report(args):
    """The six section-2 rows as the Python process sees them. Four are
    ABSENCES, so '<unset>' is the correct value and an empty string is not."""
    for key in ("TMPDIR", "CUDA_HOME", "TRITON_DEFAULT_FP_FUSION", "CC", "CXX",
                "TORCH_DONT_CHECK_COMPILER_ABI"):
        print("%s=%s" % (key, os.environ[key] if key in os.environ else "<unset>"))
    return 0


def main():
    p = argparse.ArgumentParser(description="FusionGap telemetry capture (5C)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("env-report")

    sp = sub.add_parser("floor")
    sp.add_argument("--replay")
    sp.add_argument("--period", type=float, default=PERIOD_S)

    sp = sub.add_parser("precondition")
    sp.add_argument("--floor-temp", type=float, required=True)
    sp.add_argument("--floor-clock", type=float, required=True)
    sp.add_argument("--replay")

    sp = sub.add_parser("cooldown")
    sp.add_argument("--floor-temp", type=float, required=True)
    sp.add_argument("--floor-clock", type=float, required=True)
    sp.add_argument("--timeout", type=float, default=COOLDOWN_TIMEOUT_S)
    sp.add_argument("--replay")
    sp.add_argument("--period", type=float, default=PERIOD_S)

    sp = sub.add_parser("sequence")
    sp.add_argument("--arms", type=int, required=True)
    sp.add_argument("--repeats", type=int, required=True)

    sp = sub.add_parser("verify")
    sp.add_argument("--replay")

    sp = sub.add_parser("run")
    sp.add_argument("--label", required=True)
    sp.add_argument("--replay")
    sp.add_argument("--preflight-replay")
    sp.add_argument("--out")
    sp.add_argument("--period", type=float, default=PERIOD_S)

    args = p.parse_args()
    table = {"env-report": cmd_env_report, "floor": cmd_floor,
             "precondition": cmd_precondition, "cooldown": cmd_cooldown,
             "sequence": cmd_sequence, "verify": cmd_verify, "run": cmd_run}
    sys.exit(table[args.cmd](args))


if __name__ == "__main__":
    main()
