#!/usr/bin/env bash
# scripts/env/test_capture_contract.sh
#
# Contract test for scripts/env/capture.sh and scripts/env/capture.py (stage 5C).
# Run from the repository root:   bash scripts/env/test_capture_contract.sh
#
# WHY EACH CASE EXISTS
#   RV-39  Thermal ordering is a confound across this study's arms, and logging
#          temperature records it without controlling it. The three controls are a
#          starting-temperature precondition, a cool-down, and interleaved arm
#          ordering. Cases 3-10 are those three controls and their wrong versions.
#   RV-33  The GPU holds its boosted clock after work stops, so the precondition is
#          TWO-dimensional - temperature AND clock. Cases 6 and 7 are the two
#          one-dimensional wrong versions, each of which passes a state the other
#          catches.
#   F34    spikes/4L/sample_power.py has no cool-down. Its two arms started at
#          36.3 C and 47.3 C, which is why 4L's ceiling comparison stands and its
#          clock comparison does not.
#   F81    sample_power.py COMPUTES D-39's invalidity condition (lines 158-161) and
#          does not act on it (lines 187-196). Case 12 is that condition, enforced.
#   F82    sample_power.py puts its verdict on the LAST line, below two full
#          nvidia-smi device dumps. Case 13 is the verdict on line 1.
#   D-39   A run whose set of distinct enforced-limit values has more than one
#          member is INVALID, not adjusted.
#   D-31   Telemetry is one CSV query per sample from a separate process.
#   ENVIRONMENT.md section 2  Every timestamp is labelled UTC explicitly, because
#          this clock runs in UTC and the driver's own stamp does not say so -
#          measured 2026-11-28: "2026/11/28 10:58:22.733" at 16:28 local.
#   P-31   Cases 5, 9 and 15 EXPECT SUCCESS. A proof set in which every case expects
#          failure cannot tell a correct block from a broken harness.
#
# MEASURED CONSTANTS - 2026-11-28, 24 samples at 5 s, GPU idle
#   temperature  median 42.40 C   min 42.30   max 42.60   range 0.30
#                thirds drift +0.06 C, below the sensor's 0.1 C quantisation,
#                which is what makes that reading a FLOOR and not a snapshot
#   SM clock     300 MHz on all 24 samples, zero variance
#   utilisation  0 on all 24 samples
#
#   Targets are FLOOR-RELATIVE, not absolute. An absolute 40 C target - the
#   obvious choice from 4L's 36.3 C arm - would be UNSATISFIABLE on this machine
#   today. That is measured, not argued.
#
# COMMAND SURFACE THIS FILE PINS
#   capture.sh <sub> [args]   sources setup.sh, asserts it took, execs capture.py
#                             (.venv/bin/python when present, else python3)
#   capture.py env-report                     -> the six section-2 rows, one per line
#   capture.py floor        [--replay F] [--period S]
#   capture.py precondition --floor-temp T --floor-clock C [--replay F]
#   capture.py cooldown     --floor-temp T --floor-clock C --timeout S
#                           [--replay F] [--period S]
#   capture.py sequence     --arms N --repeats R
#   capture.py verify       [--replay F]
#   capture.py run          --label L [--replay F] [--out DIR]
#
#   --replay F replaces the live nvidia-smi reader with a CSV replay. It is a FLAG
#   and not an environment variable, deliberately: section 2 pins four variables as
#   absences, and letting shell state select a measurement's data source is the
#   mechanism D-46 unsets CC and CXX for.
#
# REPLAY FIXTURE FORMAT - one header line, then one row per sample:
#   phase,temp_c,sm_mhz,draw_w,util_pct,enforced_w,current_w

set -u
SH="scripts/env/capture.sh"
PY="scripts/env/capture.py"
PASS=0; FAIL=0

FLOOR_T=42.40     # measured 2026-11-28
FLOOR_C=300       # measured 2026-11-28
# Targets, for the reader: floor + 2.0 C and floor + 100 MHz. The implementation
# derives them; this file only passes the floor in.

ok(){ printf 'PASS  %s\n' "$1"; PASS=$((PASS+1)); }
no(){ printf 'FAIL  %s\n        expected: %s\n        actual:   %s\n' "$1" "$2" "$3"; FAIL=$((FAIL+1)); }

summary(){
  printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
  if [ "$FAIL" -eq 0 ]; then printf 'RESULT: PASS\n'; exit 0; else printf 'RESULT: FAIL\n'; exit 1; fi
}

FIX="$(mktemp -d)"; OUTD="$(mktemp -d)"
trap 'rm -rf "$FIX" "$OUTD"' EXIT

HDR='phase,temp_c,sm_mhz,draw_w,util_pct,enforced_w,current_w'

# ---------------------------------------------------------------------------
# Fixtures. Thermal states cannot be ordered up on a real GPU, so they are
# replayed. Fixture 1 is the REAL measurement, not an invented series.
# ---------------------------------------------------------------------------

# 1. the measured idle floor, 2026-11-28, 24 samples at 5 s
{
  printf '%s\n' "$HDR"
  for t in 42.30 42.30 42.40 42.40 42.40 42.30 42.40 42.40 42.30 42.40 \
           42.30 42.50 42.40 42.40 42.50 42.40 42.40 42.40 42.40 42.50 \
           42.60 42.40 42.30 42.40; do
    printf 'idle,%s,300,3.30,0,30.00,30.00\n' "$t"
  done
} > "$FIX/floor_good.csv"

# 2. a "floor" window taken while the GPU is working. Not a floor at all.
{
  printf '%s\n' "$HDR"
  for _ in $(seq 1 24); do printf 'idle,44.00,1005,28.40,97,30.00,30.00\n'; done
} > "$FIX/floor_loaded.csv"

# 3. a window taken while still cooling. The real reading drifted +0.06 C across
#    thirds; this one falls 3.15 C, which is what a snapshot during cooling is.
{
  printf '%s\n' "$HDR"
  for t in 47.00 46.80 46.60 46.40 46.20 46.00 45.80 45.60 \
           45.40 45.20 45.00 44.80 44.60 44.40 44.20 44.00 \
           43.80 43.60 43.40 43.20 43.10 43.00 43.00 43.00; do
    printf 'idle,%s,300,3.30,0,30.00,30.00\n' "$t"
  done
} > "$FIX/floor_cooling.csv"

# 4. cool enough, clock still boosted (RV-33). A temperature-only precondition
#    passes this. It must not.
printf '%s\nidle,42.50,1005,12.00,0,30.00,30.00\n' "$HDR" > "$FIX/pre_boosted.csv"

# 5. idle clock, but hot. A clock-only precondition passes this. It must not.
printf '%s\nidle,48.00,300,3.30,0,30.00,30.00\n' "$HDR" > "$FIX/pre_hot.csv"

# 6. never reaches the target before the rows run out -> TIMEOUT
{
  printf '%s\n' "$HDR"
  for _ in $(seq 1 10); do printf 'idle,48.00,300,3.30,0,30.00,30.00\n'; done
} > "$FIX/cool_timeout.csv"

# 7. cools below floor+2.0 (= 44.40) at row 5, with rows to spare
{
  printf '%s\n' "$HDR"
  for t in 48.00 47.00 46.00 45.00 44.30 44.20 44.10 44.00 43.90 43.80; do
    printf 'idle,%s,300,3.30,0,30.00,30.00\n' "$t"
  done
} > "$FIX/cool_ok.csv"

# 8. a run whose load window never reached load - 4L's negative control
{
  printf '%s\n' "$HDR"
  for _ in $(seq 1 3);  do printf 'idle,42.40,300,3.30,0,30.00,30.00\n'; done
  for _ in $(seq 1 12); do printf 'load,42.50,300,3.35,0,30.00,30.00\n'; done
  for _ in $(seq 1 3);  do printf 'idle,42.40,300,3.30,0,30.00,30.00\n'; done
} > "$FIX/run_noload.csv"

# 9. valid in EVERY other respect, but the enforced ceiling takes two distinct
#    values across the load window. D-39: invalid, not adjusted. This fixture
#    isolates F81 - nothing else about it fails.
{
  printf '%s\n' "$HDR"
  for _ in $(seq 1 3); do printf 'idle,42.40,300,3.30,0,30.00,30.00\n'; done
  for _ in $(seq 1 6); do printf 'load,50.00,1005,28.40,99,30.00,30.00\n'; done
  for _ in $(seq 1 6); do printf 'load,52.00,1005,28.60,99,50.00,50.00\n'; done
  for _ in $(seq 1 3); do printf 'idle,44.00,300,3.30,0,30.00,30.00\n'; done
} > "$FIX/run_twolimits.csv"

# 10. a fully valid run (P-31)
{
  printf '%s\n' "$HDR"
  for _ in $(seq 1 3);  do printf 'idle,42.40,300,3.30,0,30.00,30.00\n'; done
  for _ in $(seq 1 12); do printf 'load,50.00,1005,28.40,99,30.00,30.00\n'; done
  for _ in $(seq 1 3);  do printf 'idle,44.00,300,3.30,0,30.00,30.00\n'; done
} > "$FIX/run_valid.csv"

# ---------------------------------------------------------------------------
# case 0 - both artefacts exist. Everything else is unreadable without them.
# ---------------------------------------------------------------------------
MISSING=""
[ -f "$SH" ] || MISSING="$MISSING $SH"
[ -f "$PY" ] || MISSING="$MISSING $PY"
if [ -n "$MISSING" ]; then
  no "case 0 - both artefacts exist" "$SH and $PY" "missing:$MISSING"
  printf '\nNothing further can be checked until both exist.\n'
  printf 'At stage 5C step 1 this is the EXPECTED result: the test precedes the code.\n'
  summary
fi
ok "case 0 - both artefacts exist"

# ---------------------------------------------------------------------------
# case 1 - both parse. P-30: a structure check before anything uses the file.
# ---------------------------------------------------------------------------
if bash -n "$SH" 2>/dev/null; then ok "case 1a - $SH parses (bash -n)"
else no "case 1a - $SH parses (bash -n)" "exit 0" "syntax error"; fi

if python3 -c 'import ast,sys; ast.parse(open(sys.argv[1]).read())' "$PY" 2>/dev/null; then
  ok "case 1b - $PY parses (ast)"
else
  no "case 1b - $PY parses (ast)" "exit 0" "syntax error"
fi

# ---------------------------------------------------------------------------
# case 2 - the environment is APPLIED, not merely recorded. All four absences
# are planted before the call, exactly as test_setup_contract.sh plants them.
# ---------------------------------------------------------------------------
ENVOUT="$(env -i HOME="$HOME" PATH="$PATH" \
            CC=/usr/bin/gcc CXX=/usr/bin/g++ \
            TRITON_DEFAULT_FP_FUSION=0 TORCH_DONT_CHECK_COMPILER_ABI=1 \
            bash "$SH" env-report 2>&1)"
have(){ printf '%s\n' "$ENVOUT" | grep -qx "$1"; }
if have "TMPDIR=$HOME/.tmp" \
   && have "CUDA_HOME=/usr/local/cuda-13.2" \
   && have "CC=<unset>" \
   && have "CXX=<unset>" \
   && have "TRITON_DEFAULT_FP_FUSION=<unset>" \
   && have "TORCH_DONT_CHECK_COMPILER_ABI=<unset>"; then
  ok "case 2 - capture.sh applies section 2's contract before Python runs"
else
  no "case 2 - capture.sh applies section 2's contract before Python runs" \
     "six section-2 rows, four of them <unset>" \
     "$(printf '%s' "$ENVOUT" | tr '\n' ' ')"
fi

# ---------------------------------------------------------------------------
# cases 3-5 - the floor measurement, and the two ways it is not a floor
# ---------------------------------------------------------------------------
if bash "$SH" floor --replay "$FIX/floor_loaded.csv" >/dev/null 2>&1; then
  no "case 3 - floor refuses a window with utilisation > 0" "exit 1" "exit 0"
else
  ok "case 3 - floor refuses a window with utilisation > 0"
fi

if bash "$SH" floor --replay "$FIX/floor_cooling.csv" >/dev/null 2>&1; then
  no "case 4 - floor refuses a window still cooling (thirds differ > 0.5 C)" "exit 1" "exit 0"
else
  ok "case 4 - floor refuses a window still cooling (thirds differ > 0.5 C)"
fi

FOUT="$(bash "$SH" floor --replay "$FIX/floor_good.csv" 2>&1)"; rc=$?
if [ "$rc" -eq 0 ] \
   && printf '%s\n' "$FOUT" | grep -q 'temp_c=42\.4' \
   && printf '%s\n' "$FOUT" | grep -q 'clock_mhz=300'; then
  ok "case 5 - floor ACCEPTS the measured 2026-11-28 series and reports its medians"
else
  no "case 5 - floor ACCEPTS the measured 2026-11-28 series and reports its medians" \
     "exit 0, temp_c=42.4, clock_mhz=300" \
     "rc=$rc out=$(printf '%s' "$FOUT" | tr '\n' ' ')"
fi

# ---------------------------------------------------------------------------
# cases 6-7 - the precondition is two-dimensional. Each fixture passes the
# one-dimensional version the other case catches.
# ---------------------------------------------------------------------------
if bash "$SH" precondition --floor-temp "$FLOOR_T" --floor-clock "$FLOOR_C" \
        --replay "$FIX/pre_boosted.csv" >/dev/null 2>&1; then
  no "case 6 - precondition refuses a COOL gpu with a BOOSTED clock (RV-33)" "exit 1" "exit 0"
else
  ok "case 6 - precondition refuses a COOL gpu with a BOOSTED clock (RV-33)"
fi

if bash "$SH" precondition --floor-temp "$FLOOR_T" --floor-clock "$FLOOR_C" \
        --replay "$FIX/pre_hot.csv" >/dev/null 2>&1; then
  no "case 7 - precondition refuses a HOT gpu with an IDLE clock" "exit 1" "exit 0"
else
  ok "case 7 - precondition refuses a HOT gpu with an IDLE clock"
fi

# ---------------------------------------------------------------------------
# cases 8-9 - the cool-down's timeout is a FAILURE, not a silent continue
# ---------------------------------------------------------------------------
TOUT="$(bash "$SH" cooldown --floor-temp "$FLOOR_T" --floor-clock "$FLOOR_C" \
          --timeout 50 --replay "$FIX/cool_timeout.csv" 2>&1)"; rc=$?
if [ "$rc" -ne 0 ] && printf '%s\n' "$TOUT" | grep -q 'TIMEOUT'; then
  ok "case 8 - a cool-down that cannot reach target exits non-zero and says TIMEOUT"
else
  no "case 8 - a cool-down that cannot reach target exits non-zero and says TIMEOUT" \
     "non-zero exit, TIMEOUT in output" \
     "rc=$rc out=$(printf '%s' "$TOUT" | tr '\n' ' ')"
fi

COUT="$(bash "$SH" cooldown --floor-temp "$FLOOR_T" --floor-clock "$FLOOR_C" \
          --timeout 100 --replay "$FIX/cool_ok.csv" 2>&1)"; rc=$?
if [ "$rc" -eq 0 ] && printf '%s\n' "$COUT" | grep -q 'COOLDOWN OK'; then
  ok "case 9 - cool-down SUCCEEDS when the gpu reaches target in time"
else
  no "case 9 - cool-down SUCCEEDS when the gpu reaches target in time" \
     "exit 0, COOLDOWN OK" "rc=$rc out=$(printf '%s' "$COUT" | tr '\n' ' ')"
fi

# ---------------------------------------------------------------------------
# case 10 - interleaving. The PROPERTY is tested, not a literal string: no two
# consecutive cells are the same arm. A blocked order AAAABBBB fails it.
# ---------------------------------------------------------------------------
SEQ="$(bash "$SH" sequence --arms 2 --repeats 4 2>/dev/null)"
NTOK="$(printf '%s\n' "$SEQ" | tr ' ' '\n' | sed '/^$/d' | wc -l | tr -d ' ')"
NREP="$(printf '%s\n' "$SEQ" | tr ' ' '\n' | sed '/^$/d' \
        | awk 'NR>1 && $0==p {c++} {p=$0} END{print c+0}')"
if [ "$NTOK" -eq 8 ] && [ "$NREP" -eq 0 ]; then
  ok "case 10 - arm sequence is interleaved: 8 cells, no two consecutive the same"
else
  no "case 10 - arm sequence is interleaved: 8 cells, no two consecutive the same" \
     "8 cells, 0 consecutive repeats" "cells=$NTOK repeats=$NREP seq=[$SEQ]"
fi

# ---------------------------------------------------------------------------
# cases 11-12 - run validity. 4L's negative control, and D-39 enforced.
# ---------------------------------------------------------------------------
if bash "$SH" verify --replay "$FIX/run_noload.csv" >/dev/null 2>&1; then
  no "case 11 - verify rejects a load window that never reached load" "exit 1" "exit 0"
else
  ok "case 11 - verify rejects a load window that never reached load"
fi

VOUT="$(bash "$SH" verify --replay "$FIX/run_twolimits.csv" 2>&1)"; rc=$?
if [ "$rc" -ne 0 ] && printf '%s\n' "$VOUT" | grep -qi 'enforced'; then
  ok "case 12 - two distinct enforced limits in the load window is INVALID (D-39, F81)"
else
  no "case 12 - two distinct enforced limits in the load window is INVALID (D-39, F81)" \
     "non-zero exit, the enforced set named in the reason" \
     "rc=$rc out=$(printf '%s' "$VOUT" | tr '\n' ' ')"
fi

# ---------------------------------------------------------------------------
# cases 13-15 - the written record: verdict first, timestamps labelled, and one
# case that expects success end to end.
# ---------------------------------------------------------------------------
bash "$SH" run --label t1 --replay "$FIX/run_valid.csv" --out "$OUTD" >/dev/null 2>&1
TXT="$OUTD/capture_t1.txt"; CSV="$OUTD/capture_t1.csv"

if [ -f "$TXT" ] && head -1 "$TXT" | grep -q 'VERDICT'; then
  ok "case 13 - the summary's FIRST line carries the verdict (F82)"
else
  no "case 13 - the summary's FIRST line carries the verdict (F82)" \
     "line 1 of $TXT contains VERDICT" \
     "$([ -f "$TXT" ] && head -1 "$TXT" || echo 'file not written')"
fi

if [ -f "$CSV" ]; then
  TOTAL="$(tail -n +2 "$CSV" | sed '/^$/d' | wc -l | tr -d ' ')"
  BAD="$(tail -n +2 "$CSV" | sed '/^$/d' | awk -F, '$1 !~ /Z$/ {c++} END{print c+0}')"
  if [ "$TOTAL" -gt 0 ] && [ "$BAD" -eq 0 ]; then
    ok "case 14 - all $TOTAL data rows carry an explicit UTC marker (section 2)"
  else
    no "case 14 - every data row carries an explicit UTC marker (section 2)" \
       "0 rows without a trailing Z, from a non-empty file" "rows=$TOTAL unlabelled=$BAD"
  fi
else
  no "case 14 - every data row carries an explicit UTC marker (section 2)" \
     "$CSV written" "file not written"
fi

if bash "$SH" run --label t2 --replay "$FIX/run_valid.csv" --out "$OUTD" >/dev/null 2>&1 \
   && [ -f "$OUTD/capture_t2.txt" ] \
   && head -1 "$OUTD/capture_t2.txt" | grep -q 'VERDICT VALID'; then
  ok "case 15 - a fully valid run PASSES end to end and says so on line 1 (P-31)"
else
  no "case 15 - a fully valid run PASSES end to end and says so on line 1 (P-31)" \
     "exit 0 and 'VERDICT VALID' on line 1" \
     "$([ -f "$OUTD/capture_t2.txt" ] && head -1 "$OUTD/capture_t2.txt" || echo 'file not written')"
fi

summary
