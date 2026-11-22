#!/usr/bin/env python3
"""4I - the fp64 correctness path (R3).

Three questions, each with a stated pass condition:

  A  a templated CUDA kernel compiles and is exact for half, float AND double.
     Copy is bit-exact in every type, so the bar is torch.equal, not a
     tolerance.

  B  Triton runs on fp64 tensors on SM_75. Consumer Turing runs fp64 at 1/32
     rate and Triton's fp64 support is thinner than its fp16 support, so this
     is genuinely open. y = 2x is exact in fp64, so the bar is again equality.
     A refusal here is adverse-but-valid and is recorded, not worked around.

  C  gradcheck in fp64 passes for the true backward (coeff 2) and FAILS for a
     planted wrong one (coeff 3). The second half is the point: the project's
     whole correctness gate is gradcheck, and a gradcheck that cannot fail
     would license every kernel in this repository on no evidence.

Exit: 0 every check behaved as stated
      1 a check did not
      2 the extension would not build
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("CXX", "g++-15")
os.environ.setdefault("MAX_JOBS", "1")
os.environ.setdefault("TORCH_CUDA_ARCH_LIST", "7.5")
os.environ.setdefault("TORCH_EXTENSIONS_DIR", os.path.expanduser("~/.tmp/torch_ext_4i"))
os.environ.setdefault("TRITON_DEFAULT_FP_FUSION", "1")
_venv_bin = os.path.dirname(sys.executable)
os.environ["PATH"] = _venv_bin + os.pathsep + os.environ.get("PATH", "")

import torch  # noqa: E402

PASSED, FAILED = [], []


def check(name, fn):
    try:
        fn()
    except Exception as exc:  # noqa: BLE001
        FAILED.append(name)
        print(f"FAIL  {name}: {type(exc).__name__}: {str(exc)[:300]}")
    else:
        PASSED.append(name)
        print(f"PASS  {name}")


def main():
    if not torch.cuda.is_available():
        print("FATAL: no CUDA device")
        return 2
    from torch.utils.cpp_extension import load
    try:
        mod = load(name="fusiongap_4i",
                   sources=[os.path.join(HERE, "fp64_kernels.cu")],
                   extra_cuda_cflags=["-O2"], verbose=False)
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL build failure: {type(exc).__name__}: {str(exc)[:1500]}")
        return 2

    print("=== A templated kernel across half, float, double ===")
    for dt in (torch.float16, torch.float32, torch.float64):
        def t(dt=dt):
            x = (torch.rand(5000, device="cuda", dtype=torch.float32) - 0.5).to(dt)
            y = mod.copy_any(x)
            assert y.dtype == dt, f"dtype {y.dtype}"
            assert torch.equal(y, x), "copy is not bit-exact"
        check(f"A  copy {str(dt).split('.')[-1]}", t)

    print("\n=== B Triton on fp64 tensors ===")

    def triton_fp64():
        import triton
        import triton.language as tl

        @triton.jit
        def double_it(X, Y, n, BLOCK: tl.constexpr):
            i = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
            m = i < n
            tl.store(Y + i, tl.load(X + i, mask=m, other=0.0) * 2.0, mask=m)

        n = 4096
        x = torch.rand(n, device="cuda", dtype=torch.float64) - 0.5
        y = torch.empty_like(x)
        double_it[(triton.cdiv(n, 256),)](x, y, n, BLOCK=256)
        torch.cuda.synchronize()
        assert torch.equal(y, x * 2.0), "fp64 result differs from x*2"
    check("B  triton elementwise fp64", triton_fp64)

    print("\n=== C gradcheck in fp64, with its negative control ===")

    class Square(torch.autograd.Function):
        @staticmethod
        def forward(ctx, x, coeff):
            ctx.save_for_backward(x)
            ctx.coeff = coeff
            return mod.square_fwd(x)

        @staticmethod
        def backward(ctx, gout):
            (x,) = ctx.saved_tensors
            return mod.square_bwd(gout.contiguous(), x, ctx.coeff), None

    def make(coeff):
        x = (torch.rand(8, device="cuda", dtype=torch.float64) + 0.5)
        x.requires_grad_(True)
        return lambda: torch.autograd.gradcheck(Square.apply, (x, coeff), eps=1e-6,
                                                atol=1e-8, rtol=1e-5)

    def correct():
        assert make(2.0)() is True, "gradcheck did not return True"
    check("C  gradcheck fp64, correct backward (coeff 2)", correct)

    def planted():
        try:
            make(3.0)()
        except Exception:
            return  # this is the required outcome
        raise AssertionError(
            "gradcheck PASSED a backward of 3x where the derivative is 2x - "
            "the correctness gate cannot detect a wrong gradient")
    check("C  gradcheck fp64, planted wrong backward (coeff 3) must FAIL", planted)

    print(f"\n{len(PASSED)} passed, {len(FAILED)} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
