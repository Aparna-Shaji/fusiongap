#!/usr/bin/env bash
# scripts/env/setup.sh
#
# Applies the shell environment pinned in docs/environment/ENVIRONMENT.md section 2.
# Invoked by section 3 step 6 of the 5D rebuild procedure.
#
# MUST BE SOURCED, never executed. Exports in a child process die with it, and an
# executed copy would exit 0 having changed nothing - the failure mode section 5.5
# rule 1 names nine times over.
#
#     . scripts/env/setup.sh

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  printf 'setup.sh must be sourced, not executed:\n\n    . scripts/env/setup.sh\n\n' >&2
  exit 1
fi

# --- the two variables pinned SET ------------------------------------------
# TMPDIR: /tmp on this distribution is a 1.8 GB tmpfs. With TMPDIR unset,
# `pip install torch` fails with "No space left on device" while the disk has
# hundreds of GB free (D-17). The directory is created because a TMPDIR pointing
# at nothing fails the same way.
mkdir -p "$HOME/.tmp"
export TMPDIR="$HOME/.tmp"

# CUDA_HOME: torch.utils.cpp_extension locates nvcc through it; without it the
# CUDA arm does not build.
export CUDA_HOME=/usr/local/cuda-13.2

# --- the four variables pinned UNSET --------------------------------------
# Each is an absence on purpose, and each has a stated mechanism in section 2:
#   TRITON_DEFAULT_FP_FUSION      set per run inside each spike, so a run's
#                                 arithmetic never depends on whose shell
#                                 launched it (R22, and the fp-fusion scope note)
#   CC, CXX                       the stage-15 build file names the host compiler
#                                 explicitly; shell state must not select it (F42)
#   TORCH_DONT_CHECK_COMPILER_ABI set to any truthy value it disables BOTH of
#                                 torch's build-time guards at once
unset TRITON_DEFAULT_FP_FUSION CC CXX TORCH_DONT_CHECK_COMPILER_ABI
