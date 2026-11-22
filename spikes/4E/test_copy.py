#!/usr/bin/env python3
"""4E - C++/CUDA readiness spike: the tests, written before the kernel.

Why this file exists: 4E measures whether a CUDA kernel can be written, built
and called on this machine, and how long that takes. The kernel it builds is
the template every later CUDA kernel in this project copies, so its invariants
are pinned down here, before the kernel exists.

Invariants under test:
  I1  every element of the input reaches the same position of the output
  I2  nothing is written outside [0, n)   <- NOT testable here; compute-sanitizer
                                             owns it in 4E-3, because the CUDA
                                             allocator pads and a stray write
                                             usually lands in memory that is
                                             still ours
  I3  the wrapper rejects inputs whose layout the kernel assumes away

Run:   .venv/bin/python spikes/4E/test_copy.py
Exit:  0  every test passed
       1  a test failed
       2  the extension could not be built (or does not exist yet)
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

# Set before torch is imported.
# D-26 part 3: the host compiler is named explicitly, never the bare gcc alias.
# 4D: 3.5 GiB of RAM against 12 logical CPUs is 300 MiB per parallel job, so one.
# 7.5 is this GPU; naming it stops the build probing and makes it reproducible.
os.environ.setdefault("CXX", "g++-15")
os.environ.setdefault("MAX_JOBS", "1")
os.environ.setdefault("TORCH_CUDA_ARCH_LIST", "7.5")
os.environ.setdefault("TORCH_EXTENSIONS_DIR", os.path.expanduser("~/.tmp/torch_ext_4e"))

# ninja is a pip package inside this venv, and torch finds it by running
# "ninja --version" against PATH. PATH carries the venv only when it has been
# activated, and these spikes run as .venv/bin/python directly. Derive the
# venv's bin directory from the running interpreter so the spike works either
# way - 5D rebuilds on a fresh distro where nothing will be activated.
_venv_bin = os.path.dirname(sys.executable)
os.environ["PATH"] = _venv_bin + os.pathsep + os.environ.get("PATH", "")

import torch  # noqa: E402

BLOCK = 256  # must equal the block size in copy_kernel.cu

PASSED, FAILED = [], []


def check(name, fn):
    try:
        fn()
    except Exception as exc:  # noqa: BLE001
        FAILED.append(name)
        print(f"FAIL  {name}: {type(exc).__name__}: {exc}")
    else:
        PASSED.append(name)
        print(f"PASS  {name}")


def expect_rejection(fn, what):
    try:
        fn()
    except Exception:
        return
    raise AssertionError(f"expected {what} to be rejected; it was accepted")


def main():
    if not torch.cuda.is_available():
        print("FATAL: no CUDA device visible")
        return 2

    src = os.path.join(HERE, "copy_kernel.cu")
    if not os.path.exists(src):
        print(f"FATAL: {src} does not exist yet.")
        print("This is the expected result at 4E-1: the tests exist before the kernel.")
        return 2

    from torch.utils.cpp_extension import load
    t0 = time.time()
    try:
        mod = load(name="fusiongap_4e", sources=[src],
                   extra_cuda_cflags=["-O2"], verbose=True)
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL build failure: {type(exc).__name__}: {exc}")
        return 2
    print(f"[build] {time.time() - t0:.1f} s")

    dev = "cuda"

    # I1. n=1 is the smallest case. n=BLOCK and n=BLOCK*3 are exact multiples,
    # which CANNOT catch a missing tail guard - they are here to prove the happy
    # path, not to test the guard. 98437 leaves 123 threads past the end.
    for n in (1, BLOCK, BLOCK * 3, 98437):
        def t(n=n):
            x = torch.arange(n, dtype=torch.float32, device=dev)
            y = mod.copy_cuda(x)
            assert y.shape == x.shape, f"shape {tuple(y.shape)} != {tuple(x.shape)}"
            assert y.dtype == x.dtype, f"dtype {y.dtype} != {x.dtype}"
            assert torch.equal(y, x), "contents differ"
        check(f"I1  copy n={n} (arange)", t)

    def t_rand():
        x = torch.rand(98437, dtype=torch.float32, device=dev)
        assert torch.equal(mod.copy_cuda(x), x), "contents differ"
    check("I1  copy n=98437 (random)", t_rand)

    def t_empty():
        # grid = ceil(0/256) = 0 blocks, and a launch with gridDim 0 is an
        # invalid configuration, so the wrapper must return before launching.
        x = torch.empty(0, dtype=torch.float32, device=dev)
        assert mod.copy_cuda(x).numel() == 0, "empty input did not give empty output"
    check("I1  copy n=0 (no launch)", t_empty)

    # I3. Each of these has a valid data pointer and the wrong assumptions.
    check("I3  rejects a CPU tensor", lambda: expect_rejection(
        lambda: mod.copy_cuda(torch.arange(16, dtype=torch.float32)), "a CPU tensor"))
    check("I3  rejects float64", lambda: expect_rejection(
        lambda: mod.copy_cuda(torch.arange(16, dtype=torch.float64, device=dev)),
        "a float64 tensor"))
    check("I3  rejects a non-contiguous view", lambda: expect_rejection(
        lambda: mod.copy_cuda(torch.rand(16, 16, device=dev).t()),
        "a transposed view"))

    print(f"\n{len(PASSED)} passed, {len(FAILED)} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
