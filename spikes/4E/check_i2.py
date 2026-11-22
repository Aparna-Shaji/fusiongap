#!/usr/bin/env python3
"""4E invariant I2: nothing is written outside [0, n).

Python cannot see this. The CUDA allocator pads, so 123 threads writing past
a 98437-element tensor usually land in memory that is still ours, and every
assertion still passes. compute-sanitizer's memcheck tool sees it.

Usage:
  compute-sanitizer --tool memcheck --error-exitcode 1 \
      .venv/bin/python spikes/4E/check_i2.py {good|noguard}
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("CXX", "g++-15")
os.environ.setdefault("MAX_JOBS", "1")
os.environ.setdefault("TORCH_CUDA_ARCH_LIST", "7.5")
os.environ.setdefault("TORCH_EXTENSIONS_DIR", os.path.expanduser("~/.tmp/torch_ext_4e"))
_venv_bin = os.path.dirname(sys.executable)
os.environ["PATH"] = _venv_bin + os.pathsep + os.environ.get("PATH", "")

import torch  # noqa: E402
from torch.utils.cpp_extension import load  # noqa: E402

which = sys.argv[1] if len(sys.argv) > 1 else "good"
src = {"good": "copy_kernel.cu", "noguard": "copy_kernel_noguard.cu"}[which]
name = {"good": "fusiongap_4e", "noguard": "fusiongap_4e_noguard"}[which]

mod = load(name=name, sources=[os.path.join(HERE, src)],
           extra_cuda_cflags=["-O2"], verbose=False)

# n is chosen so the overrun cannot hide in allocator padding.
# 98360 -> 385 blocks of 256 = 98560 threads, so 200 run past the end:
# 800 bytes, against at most 511 bytes of 512-byte alignment padding.
# Run this under PYTORCH_NO_CUDA_MEMORY_CACHING=1 or the caching
# allocator hides the overrun inside one large cudaMalloc and
# compute-sanitizer reports nothing - measured 2026-11-22.
n = 98360
x = torch.arange(n, dtype=torch.float32, device="cuda")
y = mod.copy_cuda(x)
torch.cuda.synchronize()
print(f"{which}: kernel ran, torch.equal={torch.equal(y, x)}")
