"""Grades a 4C telemetry capture against TECH-STACK cell 10's criterion as
revised by CR-10 / AM-07.

Both windows are cut from the load generator's own printed timestamps rather
than inferred from the telemetry. The idle reference is the settle period
between SETTLE_START and LOAD_START, which by construction follows all CUDA
setup and precedes any load; the loaded window lies between LOAD_START and
LOAD_END. Run 1 on 2026-11-21 failed clause 2 because the idle reference was
taken as "every sample before the window", which swept in the cuBLAS warm-up
burst and placed a 1380 MHz sample in the idle baseline -- a grader defect,
not a telemetry result. One-second margins trim transition samples. The
criterion itself is unchanged.

Exit 0 = PASS, 1 = FAIL (a result, not an error), 2 = malformed input.
Usage: grade_4c.py <telemetry.csv> <load_log.txt>"""
import sys, statistics
from datetime import datetime, timedelta

COLS = ["timestamp","clocks.sm","clocks.mem","power.draw","enforced.power.limit",
        "temperature.gpu","utilization.gpu","utilization.memory","memory.used",
        "clocks_event_reasons.active"]
FIVE = ["clocks.sm","clocks.mem","temperature.gpu","power.draw","clocks_event_reasons.active"]
IDLE_BIT = 0x1
FMT = "%Y/%m/%d %H:%M:%S.%f"
MARGIN = timedelta(seconds=1.0)

mark = {}
for line in open(sys.argv[2]):
    p = line.split()
    if len(p) >= 3 and p[0] in ("IDLE_START", "IDLE_END", "WARM_END",
                               "LOAD_START", "LOAD_END", "SETTLE_END"):
        mark[p[0]] = datetime.strptime(p[1] + " " + p[2], FMT)
for k in ("IDLE_START", "IDLE_END", "LOAD_START", "LOAD_END"):
    if k not in mark:
        print(f"MALFORMED load log: {k} missing"); sys.exit(2)

rows, na = [], []
for i, line in enumerate(open(sys.argv[1]), 1):
    line = line.strip()
    if not line:
        continue
    p = [x.strip() for x in line.split(",")]
    if len(p) != len(COLS):
        print(f"MALFORMED line {i}: {len(p)} fields, expected {len(COLS)}"); sys.exit(2)
    r = dict(zip(COLS, p))
    for k in FIVE:
        if "N/A" in r[k] or r[k] == "":
            na.append((i, k))
    rows.append(r)

num = lambda r, k: float(r[k])
tim = lambda r: datetime.strptime(r["timestamp"], FMT)

idle = [r for r in rows if mark["IDLE_START"] + MARGIN <= tim(r) <= mark["IDLE_END"] - MARGIN]
inld = [r for r in rows if mark["LOAD_START"] <= tim(r) <= mark["LOAD_END"]]

best, cur = (0, 0, 0), None
for i, r in enumerate(inld):
    if num(r, "utilization.gpu") >= 90.0:
        cur = i if cur is None else cur
    elif cur is not None:
        best, cur = max(best, (i - cur, cur, i)), None
if cur is not None:
    best = max(best, (len(inld) - cur, cur, len(inld)))
L, s, e = best
win = inld[s:e]

print(f"samples={len(rows)}  idle_ref={len(idle)}  in_load={len(inld)}  window={L}")
if L < 3 or len(idle) < 3:
    print("CLAUSE 1 coverage: FAIL - no usable window or too little idle reference")
    print("\n4C CELL 10 VERDICT: FAIL"); sys.exit(1)

secs = (tim(win[-1]) - tim(win[0])).total_seconds()
span = (tim(rows[-1]) - tim(rows[0])).total_seconds()
rate = (len(rows) - 1) / span if span else 0.0
gap  = max((tim(rows[i]) - tim(rows[i-1])).total_seconds() for i in range(1, len(rows)))
c1 = (not na) and secs >= 30.0 and rate >= 2.0 and gap <= 0.75
print(f"CLAUSE 1 coverage: {'PASS' if c1 else 'FAIL'}")
print(f"  window={secs:.1f}s (need >=30)  rate={rate:.2f}Hz (need >=2)"
      f"  max_gap={gap:.2f}s (need <=0.75)  N/A_hits={len(na)}")
if na:
    print("  N/A at:", na[:10])

isl = [num(r, "clocks.sm") for r in idle]
wsl = [num(r, "clocks.sm") for r in win]
trim = wsl[1:-1]
med, bar = statistics.median(wsl), 2.0 * statistics.median(isl)
c2 = med >= bar and min(trim) > max(isl)
print(f"CLAUSE 2 clock response: {'PASS' if c2 else 'FAIL'}")
print(f"  idle median={statistics.median(isl):.0f} max={max(isl):.0f}"
      f" | loaded median={med:.0f} min(trimmed)={min(trim):.0f} | bar={bar:.0f}")

spread = lambda v: max(abs(v[i]-v[i-1]) for i in range(1, len(v))) if len(v) > 1 else 0.0
moved = []
for k in ("temperature.gpu", "power.draw"):
    iv, wv = [num(r, k) for r in idle], [num(r, k) for r in win]
    d, sp = abs(statistics.median(wv) - statistics.median(iv)), spread(iv)
    print(f"  {k}: idle={statistics.median(iv):.2f} loaded={statistics.median(wv):.2f}"
          f" delta={d:.2f} idle_spread={sp:.2f} -> {'MOVED' if d > sp else 'no'}")
    if d > sp:
        moved.append(k)
bit = lambda r: int(r["clocks_event_reasons.active"], 16) & IDLE_BIT
ip, iw = all(bit(r) for r in idle), any(bit(r) for r in win)
print(f"  throttle flags: idle bit set through idle={bool(ip)} set in window={bool(iw)}"
      f" -> {'MOVED' if (ip and not iw) else 'no'}")
if ip and not iw:
    moved.append("clocks_event_reasons.active")
c3 = len(moved) >= 2
print(f"CLAUSE 3 liveness: {'PASS' if c3 else 'FAIL'}  moved={moved}")

print(f"\n4C CELL 10 VERDICT: {'PASS' if (c1 and c2 and c3) else 'FAIL'}")
print("flags in idle:", sorted({r["clocks_event_reasons.active"] for r in idle}))
print("flags in window:", sorted({r["clocks_event_reasons.active"] for r in win}))
print("enforced.power.limit seen:", sorted({r["enforced.power.limit"] for r in rows}))

# observations, never pass criteria
if "SETTLE_END" in mark:
    cool = [r for r in rows if mark["LOAD_END"] < tim(r) <= mark["SETTLE_END"]]
    idle_med = statistics.median(isl)
    print("\nCOOL-DOWN after LOAD_END (observation):")
    back = None
    for r in cool:
        dt = (tim(r) - mark["LOAD_END"]).total_seconds()
        print(f"  +{dt:5.1f}s  sm={num(r,'clocks.sm'):6.0f}  util={num(r,'utilization.gpu'):3.0f}"
              f"  flags={r['clocks_event_reasons.active']}")
        if back is None and num(r, "clocks.sm") <= idle_med:
            back = dt
    print(f"  returned to idle clock after: {back if back is not None else 'not within this window'}")
if "WARM_END" in mark:
    warm = [r for r in rows if mark["WARM_END"] <= tim(r) <= mark["LOAD_START"]]
    if warm:
        print(f"POST-WARM-UP window (the one that fooled run 1): n={len(warm)} "
              f"sm_median={statistics.median([num(r,'clocks.sm') for r in warm]):.0f} "
              f"flags={sorted({r['clocks_event_reasons.active'] for r in warm})}")
sys.exit(0 if (c1 and c2 and c3) else 1)
