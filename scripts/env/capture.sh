#!/usr/bin/env bash
# scripts/env/capture.sh
#
# Entry point for the stage-5C telemetry capture. Thin on purpose.
#
# WHY A SHELL SCRIPT AT ALL, when every line of logic is in capture.py:
# ENVIRONMENT.md section 2 pins seven shell items and FOUR OF THEM ARE ABSENCES.
# setup.sh is the only thing that applies them, and a Python process cannot
# source a shell script into its own parent. So this is the only construction in
# which a capture CANNOT run outside the pinned environment - the difference
# between recording a run's environment and enforcing it, and 4L's defect was
# recording a confound without controlling it (RV-39).
#
#   REJECTED: capture.py alone, with the environment recorded in the output
#             header. That is the same shape of error one level up.
#   REJECTED: implementing the sampling here. median, the thirds comparison and
#             float comparison in bash are all places defects hide, and the
#             Python in spikes/4L/sample_power.py is already proved.
#
# Usage:  bash scripts/env/capture.sh <subcommand> [args]
# Specified by: scripts/env/test_capture_contract.sh

set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"

# Apply section 2. setup.sh refuses to be executed (D-46), so it is sourced.
# shellcheck source=/dev/null
. "$HERE/setup.sh"

# Assert it TOOK. Sourcing a script that did nothing exits 0 - section 5.5
# rule 1, which setup.sh's own refusal-to-be-executed guard exists for.
if [ "${TMPDIR-}" != "$HOME/.tmp" ] || [ "${CUDA_HOME-}" != "/usr/local/cuda-13.2" ]; then
  printf 'capture.sh: setup.sh did not apply section 2 (TMPDIR=[%s] CUDA_HOME=[%s])\n' \
    "${TMPDIR-<unset>}" "${CUDA_HOME-<unset>}" >&2
  exit 1
fi

# The venv interpreter when it exists, because a live capture's load needs torch.
# PATH is not relied on: these scripts run as .venv/bin/python directly, and 5D
# rebuilds on a fresh distribution where nothing will be activated.
PY="$REPO/.venv/bin/python"
if [ ! -x "$PY" ]; then
  PY="$(command -v python3 || true)"
fi
if [ -z "$PY" ]; then
  printf 'capture.sh: no python interpreter found\n' >&2
  exit 1
fi

exec "$PY" "$HERE/capture.py" "$@"
