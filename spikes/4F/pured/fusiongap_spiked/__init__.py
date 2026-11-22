"""4F repeat under ADR-0004 option (d): the published artefact is pure Python.

The Triton kernel is source, compiled by Triton at first call on the user's
machine. No compiled code is in the wheel, so there is no platform tag for an
index to reject. The CUDA extension is not shipped here; under (d) it is an
optional, separately built component.
"""
import triton
import triton.language as tl
import torch

__version__ = "0.0.1"


@triton.jit
def _add_kernel(X, Y, Z, n, BLOCK: tl.constexpr):
    i = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
    m = i < n
    tl.store(Z + i, tl.load(X + i, mask=m, other=0.0)
             + tl.load(Y + i, mask=m, other=0.0), mask=m)


def add(x, y, block=256):
    z = torch.empty_like(x)
    _add_kernel[(triton.cdiv(x.numel(), block),)](x, y, z, x.numel(), BLOCK=block)
    return z
