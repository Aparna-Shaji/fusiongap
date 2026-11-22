#!/usr/bin/env python3
"""4J - does tl.dot compile and compute correctly on SM_75, which has no
tensor cores? Evidence for ADR-0009 (R4, V11).

CRITERION, fixed before the run and derived from arithmetic:

  compile   the kernel compiles and launches for a dtype, or its failure text
            is recorded and ADR-0009 takes the cuBLAS-only branch for that
            dtype. A failure here is adverse-but-valid, not a defect.

  accuracy  TWO measurements, because the first version of this file had one
            bar that could not fail. Both use torch.matmul in float64.

            rel_acc  kernel output vs fp64 arithmetic on the IDENTICAL rounded
                     inputs the kernel saw. Input rounding cancels from both
                     sides, so this measures the accumulator alone. An
                     fp16*fp16 product needs 22 mantissa bits and fp32 has 24,
                     so each product is exact and only the sum rounds:
                     bar 1e-5, from K*u_fp32 = 64*2^-24 = 3.8e-6. Same bar for
                     both dtypes - that is the point.

            rel_pipe kernel output vs fp64 arithmetic on the PRE-CAST fp32
                     inputs. This one carries the input rounding and is the
                     measurement the fp16 bar was derived for:
                     fp16 bar 2e-2, from K*u_fp16 = 64*2^-11 = 3.1e-2
                     fp32 bar 1e-5 - identical to rel_acc by construction,
                     since nothing is cast.

            Bars are not moved after seeing a number, in either direction. The
            fp16 rel_pipe bar is unchanged from the first version; what changed
            is that the measurement it belongs to now exists.

Exit: 0 every dtype attempted compiled and met its bar
      1 compiled but outside tolerance
      2 failed to compile or launch for every dtype (ADR-0009 branch)
"""
import os
import sys

# Pinned explicitly: Triton 3.9 warns this is unset and flips the default in
# 3.10. Setting it to the current default keeps this run reproducible later.
os.environ.setdefault("TRITON_DEFAULT_FP_FUSION", "1")

import torch
import triton
import triton.language as tl


@triton.jit
def matmul_kernel(A, B, C, M, N, K,
                  stride_am, stride_ak, stride_bk, stride_bn,
                  stride_cm, stride_cn,
                  BLOCK_M: tl.constexpr, BLOCK_N: tl.constexpr,
                  BLOCK_K: tl.constexpr):
    pid_m = tl.program_id(0)
    pid_n = tl.program_id(1)
    offs_m = pid_m * BLOCK_M + tl.arange(0, BLOCK_M)
    offs_n = pid_n * BLOCK_N + tl.arange(0, BLOCK_N)
    offs_k = tl.arange(0, BLOCK_K)
    acc = tl.zeros((BLOCK_M, BLOCK_N), dtype=tl.float32)
    for k0 in range(0, K, BLOCK_K):
        k = k0 + offs_k
        a = tl.load(A + offs_m[:, None] * stride_am + k[None, :] * stride_ak,
                    mask=(offs_m[:, None] < M) & (k[None, :] < K), other=0.0)
        b = tl.load(B + k[:, None] * stride_bk + offs_n[None, :] * stride_bn,
                    mask=(k[:, None] < K) & (offs_n[None, :] < N), other=0.0)
        acc += tl.dot(a, b)
    tl.store(C + offs_m[:, None] * stride_cm + offs_n[None, :] * stride_cn, acc,
             mask=(offs_m[:, None] < M) & (offs_n[None, :] < N))


def run(dtype, bar_acc, bar_pipe, M=128, N=128, K=64, BM=64, BN=64, BK=32):
    torch.manual_seed(0)
    a32 = torch.rand((M, K), device="cuda", dtype=torch.float32) - 0.5
    b32 = torch.rand((K, N), device="cuda", dtype=torch.float32) - 0.5
    a, b = a32.to(dtype), b32.to(dtype)
    c = torch.empty((M, N), device="cuda", dtype=torch.float32)
    grid = (triton.cdiv(M, BM), triton.cdiv(N, BN))
    matmul_kernel[grid](a, b, c, M, N, K,
                        a.stride(0), a.stride(1), b.stride(0), b.stride(1),
                        c.stride(0), c.stride(1),
                        BLOCK_M=BM, BLOCK_N=BN, BLOCK_K=BK)
    torch.cuda.synchronize()

    ref_same = torch.matmul(a.double(), b.double())
    ref_full = torch.matmul(a32.double(), b32.double())
    rel_acc = ((c.double() - ref_same).abs().max() / ref_same.abs().max()).item()
    rel_pipe = ((c.double() - ref_full).abs().max() / ref_full.abs().max()).item()
    ok_acc, ok_pipe = rel_acc <= bar_acc, rel_pipe <= bar_pipe

    print(f"  shapes M={M} N={N} K={K}, tiles {BM}x{BN}x{BK}")
    print(f"  rel_acc  = {rel_acc:.3e}  bar {bar_acc:.1e}  -> "
          f"{'PASS' if ok_acc else 'FAIL'}   (accumulator only)")
    print(f"  rel_pipe = {rel_pipe:.3e}  bar {bar_pipe:.1e}  -> "
          f"{'PASS' if ok_pipe else 'FAIL'}   (includes input rounding)")
    if dtype == torch.float32:
        print("  (for fp32 the two are identical by construction - nothing is cast)")
    return ok_acc and ok_pipe


def main():
    print(f"triton {triton.__version__} | torch {torch.__version__}")
    print(f"device {torch.cuda.get_device_name(0)} | capability "
          f"{torch.cuda.get_device_capability(0)}")
    compiled_any, all_ok = False, True
    for dtype, bar_acc, bar_pipe in ((torch.float16, 1e-5, 2e-2),
                                    (torch.float32, 1e-5, 1e-5)):
        print(f"\n=== tl.dot with {dtype} inputs ===")
        try:
            ok = run(dtype, bar_acc, bar_pipe)
            compiled_any = True
            all_ok = all_ok and ok
        except Exception as exc:  # noqa: BLE001
            print(f"  DID NOT COMPILE OR LAUNCH: {type(exc).__name__}")
            print(f"  {str(exc)[:1200]}")
            all_ok = False
    if not compiled_any:
        print("\nRESULT: tl.dot is unusable on this device -> ADR-0009 cuBLAS branch")
        return 2
    print(f"\nRESULT: {'all attempted dtypes within tolerance' if all_ok else 'out of tolerance or partly unsupported'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
