"""Spike 4B.2: does torch.compile (Inductor) generate and run a Triton kernel on this GPU?"""
import sys
import time

import torch
import torch.nn.functional as F


def silu_mul(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    return F.silu(a) * b


def main() -> int:
    torch.manual_seed(0)
    a = torch.randn(1024, 4096, device="cuda")
    b = torch.randn(1024, 4096, device="cuda")
    compiled = torch.compile(silu_mul)

    t0 = time.perf_counter()
    out = compiled(a, b)            # first call = compile + run
    torch.cuda.synchronize()        # GPU work is asynchronous: wait before reading the clock
    first_call_s = time.perf_counter() - t0

    ref = silu_mul(a, b)            # eager PyTorch reference
    torch.testing.assert_close(out, ref)   # float32 default tolerances; raises on mismatch
    print(f"first call (compile + run): {first_call_s:.1f} s")
    print("4B.2 PASS: compiled output matches eager")
    return 0


if __name__ == "__main__":
    sys.exit(main())