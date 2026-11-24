#!/usr/bin/env python3
"""spikes/4L/sample_power.py - sample the GPU power ceiling under sustained load.

Why this exists: finding F32. results/env/4K_power_under_load.txt was produced by an
uncommitted command, so D-39's founding measurement could not be reproduced. This is the
committed instrument; 5C's capture.sh adopts it.

Per sample it records BOTH power-limit forms, because they have disagreed:
  enforced.power.limit  - the single-number form (has read 50 W and 30 W)
  Current Power Limit   - from `nvidia-smi -q -d POWER`, which separates
                          Current / Requested / Default

Protocol: IDLE_S idle -> LOAD_S sustained load -> IDLE_S idle. The idle windows are the
negative control: if the clock and utilisation do not rise in between, the load never ran.

Usage: .venv/bin/python spikes/4L/sample_power.py <label>
Exit 0 only if the load demonstrably ran.
"""
import subprocess
import sys
import time
from pathlib import Path

IDLE_S = 10
LOAD_S = 120
PERIOD = 1.0
TEMP_ABORT_C = 85.0

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "env"
VENV_PY = REPO / ".venv" / "bin" / "python"

QUERY = ("timestamp,enforced.power.limit,clocks.sm,power.draw,"
         "utilization.gpu,temperature.gpu")

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


def smi(args):
    return subprocess.run(["nvidia-smi"] + args, capture_output=True,
                          text=True).stdout


def sample_query():
    out = smi(["--query-gpu=" + QUERY, "--format=csv,noheader,nounits"]).strip()
    return [f.strip() for f in out.split(",")]


def sample_current_limit():
    # The FIRST 'Current Power Limit' is the GPU ceiling. A later one appears under
    # 'Module Power Readings' and reads N/A on this card - do not match that one.
    for line in smi(["-q", "-d", "POWER"]).splitlines():
        if "Current Power Limit" in line:
            return line.split(":", 1)[1].strip().replace(" W", "")
    return "NOT_FOUND"


def median(xs):
    s = sorted(xs)
    n = len(s)
    if not n:
        return float("nan")
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def main():
    if len(sys.argv) != 2:
        print("usage: sample_power.py <label>")
        return 2
    label = sys.argv[1]
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / ("4L_%s.csv" % label)
    txt_path = OUT / ("4L_%s.txt" % label)

    header = []
    header.append("=== 4L power-ceiling sample - label: %s ===" % label)
    header.append("protocol: %ds idle -> %ds load -> %ds idle, period %.1fs"
                  % (IDLE_S, LOAD_S, IDLE_S, PERIOD))
    header.append("load: inline 4096x4096 fp32 matmul loop (this file, not 4C's generator)")
    header.append("")
    header.append("--- device limits at start, read from the device ---")
    header.append(smi(["-q", "-d", "TEMPERATURE"]).strip())
    header.append("")
    header.append(smi(["-q", "-d", "POWER"]).strip())
    header.append("")

    rows = []
    load = None
    aborted = ""
    total = IDLE_S + LOAD_S + IDLE_S
    t0 = time.time()
    try:
        while True:
            el = time.time() - t0
            if el >= total:
                break
            if load is None and el >= IDLE_S:
                load = subprocess.Popen(
                    [str(VENV_PY), "-c", LOAD_SRC, str(LOAD_S)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            phase = "load" if IDLE_S <= el < IDLE_S + LOAD_S else "idle"
            q = sample_query()
            cur = sample_current_limit()
            try:
                temp = float(q[5])
            except (IndexError, ValueError):
                temp = 0.0
            rows.append({"t": "%.1f" % el, "phase": phase, "stamp": q[0],
                         "enforced": q[1], "current": cur, "sm": q[2],
                         "draw": q[3], "util": q[4], "temp": q[5]})
            if temp >= TEMP_ABORT_C:
                aborted = "THERMAL ABORT at %.1f C" % temp
                break
            left = PERIOD - ((time.time() - t0) - el)
            if left > 0:
                time.sleep(left)
    finally:
        if load is not None and load.poll() is None:
            load.terminate()
            try:
                load.wait(timeout=10)
            except subprocess.TimeoutExpired:
                load.kill()

    with csv_path.open("w", encoding="utf-8") as fh:
        fh.write("t_s,phase,timestamp,enforced_w,current_w,sm_mhz,draw_w,util_pct,temp_c\n")
        for r in rows:
            fh.write(",".join([r["t"], r["phase"], r["stamp"], r["enforced"],
                               r["current"], r["sm"], r["draw"], r["util"],
                               r["temp"]]) + "\n")

    loadrows = [r for r in rows if r["phase"] == "load"]
    idlerows = [r for r in rows if r["phase"] == "idle"]

    def nums(rs, k):
        out = []
        for r in rs:
            try:
                out.append(float(r[k]))
            except ValueError:
                pass
        return out

    lines = []
    lines.append("samples: %d total, %d load, %d idle" % (len(rows), len(loadrows), len(idlerows)))
    if aborted:
        lines.append("!! " + aborted)

    enf_set = sorted({r["enforced"] for r in loadrows})
    cur_set = sorted({r["current"] for r in loadrows})
    lines.append("enforced.power.limit distinct set, load window : %s" % enf_set)
    lines.append("Current Power Limit  distinct set, load window : %s" % cur_set)

    disagree = [r for r in rows
                if r["enforced"].strip() != r["current"].strip()]
    lines.append("samples where the two forms disagree: %d of %d" % (len(disagree), len(rows)))
    if disagree:
        lines.append("  first disagreement: t=%s enforced=%s current=%s"
                     % (disagree[0]["t"], disagree[0]["enforced"], disagree[0]["current"]))

    util = nums(loadrows, "util")
    sm_load = nums(loadrows, "sm")
    sm_idle = nums(idlerows, "sm")
    draw = nums(loadrows, "draw")
    temp_all = nums(rows, "temp")

    lines.append("load window : util max %.0f%%  sm median %.0f MHz  sm min/max %.0f/%.0f"
                 % (max(util or [0]), median(sm_load), min(sm_load or [0]), max(sm_load or [0])))
    lines.append("load window : draw median %.2f W  max %.2f W" % (median(draw), max(draw or [0])))
    lines.append("idle window : sm median %.0f MHz" % median(sm_idle))
    lines.append("temperature : max %.0f C over the whole run" % max(temp_all or [0]))

    third = max(1, len(sm_load) // 3)
    if len(sm_load) >= 6:
        lines.append("steady state: first-third sm median %.0f MHz, last-third %.0f MHz"
                     % (median(sm_load[:third]), median(sm_load[-third:])))

    ok = True
    if not util or max(util) < 90:
        lines.append("FAIL: load window never reached 90%% utilisation - the load did not run")
        ok = False
    if not sm_load or not sm_idle or median(sm_load) <= median(sm_idle):
        lines.append("FAIL: load-window clock did not exceed idle - negative control failed")
        ok = False
    if aborted:
        ok = False

    lines.append("ALL CHECKS OK" if ok else "MISMATCH - STOP")

    body = "\n".join(header + lines) + "\n"
    txt_path.write_text(body, encoding="utf-8")
    print(body)
    print("written: %s" % csv_path)
    print("written: %s" % txt_path)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
