"""Spike 4B.1: does a hand-written Triton kernel compile and run correctly on this GPU (F1)?"""
import sys

import torch
import triton
import triton.language as tl

BLOCK = 1024  # elements per program; tl.arange needs a power of two


@triton.jit
def add_kernel(x_ptr, y_ptr, out_ptr, n, BLOCK: tl.constexpr):
    pid = tl.program_id(axis=0)                  # which block of the array this program owns
    offsets = pid * BLOCK + tl.arange(0, BLOCK)  # the element indices this program touches
    mask = offsets < n                           # ragged-tail guard: lanes past n do nothing
    x = tl.load(x_ptr + offsets, mask=mask)
    y = tl.load(y_ptr + offsets, mask=mask)
    tl.store(out_ptr + offsets, x + y, mask=mask)


def triton_add(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    out = torch.empty_like(x)
    n = x.numel()
    grid = (triton.cdiv(n, BLOCK),)              # number of programs = ceil(n / BLOCK)
    add_kernel[grid](x, y, out, n, BLOCK=BLOCK)
    return out


def check(n: int, dtype: torch.dtype) -> bool:
    x = torch.randn(n, device="cuda", dtype=dtype)
    y = torch.randn(n, device="cuda", dtype=dtype)
    out = triton_add(x, y)
    ref = x + y
    if dtype == torch.float32:
        ok = torch.equal(out, ref)               # fp32 add: bitwise identical expected
    else:
        ok = torch.allclose(out, ref, rtol=1e-3, atol=1e-3)
    print(f"n={n:>6} {dtype!s:>13}: {'PASS' if ok else 'FAIL'}")
    return ok


def main() -> int:
    torch.manual_seed(0)
    cases = [(1, torch.float32), (BLOCK, torch.float32),
             (98_437, torch.float32), (98_437, torch.float16)]
    results = [check(n, d) for n, d in cases]
    print("4B.1 PASS" if all(results) else "4B.1 FAIL")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
