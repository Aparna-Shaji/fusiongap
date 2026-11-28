#!/usr/bin/env python3
"""scripts/maintenance/5c_capture_preflight.py - F103's fix, 2026-11-28.

capture.py's `run` sampled without invoking the floor, the cool-down or the
precondition. All three existed as subcommands and were proved by the contract
test; none was reachable from the command a measurement would actually use. A
guard that is correct and not installed is finding F63's shape, reproduced
inside the artefact built to remove the thermal confound.

Two new test cases close the hole the other seventeen left: every component was
proved, the assembly was not.

Same guard as 5b_adr_fixes.py: each target must occur exactly once, each
replacement must be absent, nothing is written unless all six edits match.

Run from the repository root:  python3 scripts/maintenance/5c_capture_preflight.py
"""
import sys
from pathlib import Path

PY = Path("scripts/env/capture.py")
TS = Path("scripts/env/test_capture_contract.sh")
EDITS = []


def edit(tag, path, old, new):
    EDITS.append({"id": tag, "path": path, "old": old, "new": new})


# --- 1. the preflight helper, and run() calling it before anything else -----
edit("preflight+run", PY,
     '''def cmd_run(args):
    replaying = bool(args.replay)
    if replaying and not args.out:
        # A replayed file is not a measurement. It must never be able to land in
        # results/env by default.
        die("run --replay requires an explicit --out DIR: a replayed run is not "
            "a measurement and must not default into results/env")
    outdir = Path(args.out) if args.out else (REPO / "results" / "env")''',
     '''def preflight(args):
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

    outdir = Path(args.out) if args.out else (REPO / "results" / "env")''')

# --- 2. the preflight result is part of the written record ------------------
edit("summary line", PY,
     '    lines.append("label: %s" % args.label)',
     '''    lines.append("label: %s" % args.label)
    for ln in pf_lines:
        lines.append(ln)''')

# --- 3. the new flag --------------------------------------------------------
edit("flag", PY,
     '''    sp = sub.add_parser("run")
    sp.add_argument("--label", required=True)
    sp.add_argument("--replay")''',
     '''    sp = sub.add_parser("run")
    sp.add_argument("--label", required=True)
    sp.add_argument("--replay")
    sp.add_argument("--preflight-replay")''')

# --- 4. two fixtures: a preflight that passes, and one that cannot ----------
edit("fixtures", TS,
     '} > "$FIX/run_valid.csv"',
     '''} > "$FIX/run_valid.csv"

# 11. a preflight that passes: 24 idle floor rows, then one cool, idle-clock row
{
  printf '%s\\n' "$HDR"
  for t in 42.30 42.30 42.40 42.40 42.40 42.30 42.40 42.40 42.30 42.40 \\
           42.30 42.50 42.40 42.40 42.50 42.40 42.40 42.40 42.40 42.50 \\
           42.60 42.40 42.30 42.40; do
    printf 'idle,%s,300,3.30,0,30.00,30.00\\n' "$t"
  done
  printf 'idle,42.50,300,3.30,0,30.00,30.00\\n'
} > "$FIX/pre_ok.csv"

# 12. the same floor, then a card that never cools: the GPU has just finished an
#     arm. This is the state F103 let through.
{
  printf '%s\\n' "$HDR"
  for t in 42.30 42.30 42.40 42.40 42.40 42.30 42.40 42.40 42.30 42.40 \\
           42.30 42.50 42.40 42.40 42.50 42.40 42.40 42.40 42.40 42.50 \\
           42.60 42.40 42.30 42.40; do
    printf 'idle,%s,300,3.30,0,30.00,30.00\\n' "$t"
  done
  for _ in $(seq 1 8); do printf 'idle,51.00,1005,12.00,0,30.00,30.00\\n'; done
} > "$FIX/pre_hotstart.csv"''')

# --- 5. two cases: the assembly, which seventeen cases never tested ---------
edit("cases", TS,
     '''     "exit 0 and 'VERDICT VALID' on line 1" \\
     "$([ -f "$OUTD/capture_t2.txt" ] && head -1 "$OUTD/capture_t2.txt" || echo 'file not written')"
fi

summary''',
     '''     "exit 0 and 'VERDICT VALID' on line 1" \\
     "$([ -f "$OUTD/capture_t2.txt" ] && head -1 "$OUTD/capture_t2.txt" || echo 'file not written')"
fi

# ---------------------------------------------------------------------------
# cases 16-17 - THE ASSEMBLY (F103). Cases 3-9 prove the floor, the cool-down
# and the precondition as standalone subcommands. Until 2026-11-28 nothing
# asserted that `run` CALLS them, and it did not: a hot, still-boosted card was
# sampled and written out as VERDICT VALID. Every component passed; the
# assembly was never tested.
# ---------------------------------------------------------------------------
rm -f "$OUTD"/capture_t3.* "$OUTD"/capture_t4.*
RO="$(bash "$SH" run --label t3 --replay "$FIX/run_valid.csv" \\
        --preflight-replay "$FIX/pre_hotstart.csv" --out "$OUTD" 2>&1)"; rc=$?
if [ "$rc" -ne 0 ] \\
   && printf '%s\\n' "$RO" | grep -q 'PREFLIGHT REFUSE' \\
   && [ ! -f "$OUTD/capture_t3.csv" ] && [ ! -f "$OUTD/capture_t3.txt" ]; then
  ok "case 16 - run REFUSES a hot, still-boosted start and writes nothing (F103)"
else
  no "case 16 - run REFUSES a hot, still-boosted start and writes nothing (F103)" \\
     "non-zero exit, PREFLIGHT REFUSE, and no files written" \\
     "rc=$rc files=$(ls "$OUTD" | tr '\\n' ' ') out=$(printf '%s' "$RO" | tr '\\n' ' ')"
fi

RO="$(bash "$SH" run --label t4 --replay "$FIX/run_valid.csv" \\
        --preflight-replay "$FIX/pre_ok.csv" --out "$OUTD" 2>&1)"; rc=$?
if [ "$rc" -eq 0 ] \\
   && [ -f "$OUTD/capture_t4.txt" ] \\
   && head -1 "$OUTD/capture_t4.txt" | grep -q 'VERDICT VALID' \\
   && grep -q 'PREFLIGHT OK' "$OUTD/capture_t4.txt"; then
  ok "case 17 - run PROCEEDS from a cool start and records the preflight (P-31)"
else
  no "case 17 - run PROCEEDS from a cool start and records the preflight (P-31)" \\
     "exit 0, VERDICT VALID on line 1, PREFLIGHT OK in the summary" \\
     "rc=$rc out=$(printf '%s' "$RO" | tr '\\n' ' ')"
fi

summary''')


def main():
    if not PY.exists() or not TS.exists():
        print("FATAL: run from the repository root; capture.py or the test is missing")
        return 1
    texts, problems, applied = {}, [], []
    for e in EDITS:
        p = e["path"]
        if p not in texts:
            texts[p] = p.read_text(encoding="utf-8")
        body = texts[p]
        if e["new"] in body:
            problems.append("%s: ALREADY APPLIED in %s" % (e["id"], p.name))
            continue
        n = body.count(e["old"])
        if n != 1:
            problems.append("%s: target occurs %d times in %s (need exactly 1)\\n"
                            "        first line: %s"
                            % (e["id"], n, p.name, e["old"].split("\\n")[0][:70]))
            continue
        texts[p] = body.replace(e["old"], e["new"], 1)
        applied.append("%s  ->  %s" % (e["id"], p.name))
    if problems:
        print("NOTHING WRITTEN. %d of %d edits failed:\\n" % (len(problems), len(EDITS)))
        for pr in problems:
            print("  " + pr)
        return 1
    for p, body in texts.items():
        p.write_text(body, encoding="utf-8")
    print("ALL %d EDITS APPLIED\\n" % len(applied))
    for a in applied:
        print("  " + a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
