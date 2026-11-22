"""4G - the 4B Triton kernel, run on CPU under Triton's interpreter (V7).

TRITON_INTERPRET=1 executes a @triton.jit kernel in Python instead of
compiling it for a device. Useless for timing, and exactly what a GPU-less
CI runner needs to catch a logic error in a kernel before it reaches
hardware. The workflow sets the variable; it is set here too so the file
is runnable on its own.
"""
import os

os.environ.setdefault("TRITON_INTERPRET", "1")
os.environ.setdefault("TRITON_DEFAULT_FP_FUSION", "1")

import torch
import triton
import triton.language as tl


@triton.jit
def add_kernel(X, Y, Z, n, BLOCK: tl.constexpr):
    i = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
    m = i < n
    tl.store(Z + i, tl.load(X + i, mask=m, other=0.0)
             + tl.load(Y + i, mask=m, other=0.0), mask=m)


def _run(n, block=256):
    x = torch.rand(n)
    y = torch.rand(n)
    z = torch.empty(n)
    add_kernel[(triton.cdiv(n, block),)](x, y, z, n, BLOCK=block)
    return x, y, z


def test_exact_multiple():
    x, y, z = _run(1024)
    assert torch.allclose(z, x + y)


def test_not_a_multiple():
    # leaves 123 lanes past the end, so the mask is doing work
    x, y, z = _run(98437)
    assert torch.allclose(z, x + y)


def test_single_element():
    x, y, z = _run(1)
    assert torch.allclose(z, x + y)
