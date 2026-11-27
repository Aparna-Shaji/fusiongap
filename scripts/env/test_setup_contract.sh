#!/usr/bin/env bash
# scripts/env/test_setup_contract.sh
#
# Asserts the shell-environment contract of docs/environment/ENVIRONMENT.md section 2,
# as applied by scripts/env/setup.sh (section 3 step 6).
# Run from the repository root:   bash scripts/env/test_setup_contract.sh
#
# Six of the seven contract rows are ABSENCES: four variables must end up unset.
# A setup.sh that merely exports TMPDIR and CUDA_HOME passes a naive test and
# fails cases 5-8 here. That is the defect this test exists to catch.

set -u
SETUP="scripts/env/setup.sh"
PASS=0; FAIL=0

ok(){ printf 'PASS  %s\n' "$1"; PASS=$((PASS+1)); }
no(){ printf 'FAIL  %s\n        expected: %s\n        actual:   %s\n' "$1" "$2" "$3"; FAIL=$((FAIL+1)); }

summary(){
  printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
  if [ "$FAIL" -eq 0 ]; then printf 'RESULT: PASS\n'; exit 0; else printf 'RESULT: FAIL\n'; exit 1; fi
}

# ---- case 0-1: the script exists and parses --------------------------------
if [ ! -f "$SETUP" ]; then
  no "case 0 - $SETUP exists" "a readable file" "not found"
  printf '\nNothing further can be checked until the script exists.\n'
  summary
fi
ok "case 0 - $SETUP exists"
if bash -n "$SETUP" 2>/dev/null; then ok "case 1 - $SETUP parses (bash -n)"
else no "case 1 - $SETUP parses (bash -n)" "exit 0" "syntax error"; fi

# ---- the probe: source the script in a shell with all four absences planted
PROBE="$(mktemp)"; trap 'rm -f "$PROBE"' EXIT
cat > "$PROBE" <<'INNER'
set +u
. "$SETUP_UNDER_TEST" >/dev/null 2>&1
printf 'TMPDIR=%s\n'    "${TMPDIR-<unset>}"
printf 'CUDA_HOME=%s\n' "${CUDA_HOME-<unset>}"
for v in TRITON_DEFAULT_FP_FUSION CC CXX TORCH_DONT_CHECK_COMPILER_ABI; do
  if [ -z "${!v+x}" ]; then printf '%s=<unset>\n' "$v"
  else printf '%s=<SET:%s>\n' "$v" "${!v}"; fi
done
INNER

run_probe(){
  env -i HOME="$HOME" PATH="$PATH" SETUP_UNDER_TEST="$PWD/$SETUP" \
      CC=/usr/bin/gcc CXX=/usr/bin/g++ \
      TRITON_DEFAULT_FP_FUSION=0 TORCH_DONT_CHECK_COMPILER_ABI=1 \
      bash "$PROBE"
}
OUT="$(run_probe)"
get(){ printf '%s\n' "$OUT" | grep "^$1=" | head -1 | cut -d= -f2-; }

# ---- case 2-3: the two variables that must be SET -------------------------
want_tmp="$HOME/.tmp"; got="$(get TMPDIR)"
[ "$got" = "$want_tmp" ] && ok "case 2 - TMPDIR set to \$HOME/.tmp (D-17)" \
  || no "case 2 - TMPDIR set to \$HOME/.tmp (D-17)" "$want_tmp" "$got"

[ -d "$want_tmp" ] && ok "case 3 - \$HOME/.tmp exists as a directory" \
  || no "case 3 - \$HOME/.tmp exists as a directory" "a directory" "missing"

got="$(get CUDA_HOME)"
[ "$got" = "/usr/local/cuda-13.2" ] && ok "case 4 - CUDA_HOME set to /usr/local/cuda-13.2" \
  || no "case 4 - CUDA_HOME set to /usr/local/cuda-13.2" "/usr/local/cuda-13.2" "$got"

# ---- case 5-8: the four variables that must end UNSET (negative controls) --
for v in TRITON_DEFAULT_FP_FUSION CC CXX TORCH_DONT_CHECK_COMPILER_ABI; do
  got="$(get "$v")"
  [ "$got" = "<unset>" ] && ok "case 5+ - $v unset after sourcing (planted before)" \
    || no "case 5+ - $v unset after sourcing (planted before)" "<unset>" "$got"
done

# ---- case 9: idempotence - sourcing twice equals sourcing once -------------
P1="$(mktemp)"; P2="$(mktemp)"
cat > "$P1" <<'INNER1'
set +u
. "$SETUP_UNDER_TEST" >/dev/null 2>&1
printf 'TMPDIR=%s\nCUDA_HOME=%s\nPATHLEN=%s\n' "${TMPDIR-<unset>}" "${CUDA_HOME-<unset>}" "${#PATH}"
INNER1
cat > "$P2" <<'INNER2'
set +u
. "$SETUP_UNDER_TEST" >/dev/null 2>&1
. "$SETUP_UNDER_TEST" >/dev/null 2>&1
printf 'TMPDIR=%s\nCUDA_HOME=%s\nPATHLEN=%s\n' "${TMPDIR-<unset>}" "${CUDA_HOME-<unset>}" "${#PATH}"
INNER2
ONCE="$(env -i HOME="$HOME" PATH="$PATH" SETUP_UNDER_TEST="$PWD/$SETUP" bash "$P1")"
TWICE="$(env -i HOME="$HOME" PATH="$PATH" SETUP_UNDER_TEST="$PWD/$SETUP" bash "$P2")"
rm -f "$P1" "$P2"
if [ "$ONCE" = "$TWICE" ]; then
  ok "case 9 - idempotent: sourcing twice equals once"
else
  no "case 9 - idempotent: sourcing twice equals once" "$(printf '%s' "$ONCE" | tr '\n' ' ')" "$(printf '%s' "$TWICE" | tr '\n' ' ')"
fi

summary
