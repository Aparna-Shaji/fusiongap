"""Spike 4A: record what PyTorch sees on this machine (verification item V1).

Prints facts only; changes nothing. Output is saved to results/env/torch_env.txt.
"""
import platform
import sys

import torch


def main() -> int:
    print(f"python          : {sys.version.split()[0]}")
    print(f"platform        : {platform.platform()}")
    print(f"torch           : {torch.__version__}")
    print(f"torch CUDA      : {torch.version.cuda}")   # CUDA version this wheel was built with
    print(f"cuda available  : {torch.cuda.is_available()}")
    if not torch.cuda.is_available():
        print("V1 FAIL: PyTorch cannot see the GPU")
        return 1

    cap = torch.cuda.get_device_capability(0)
    arches = torch.cuda.get_arch_list()               # GPU architectures compiled into this wheel
    free, total = torch.cuda.mem_get_info(0)          # bytes free / total on the device right now
    print(f"device          : {torch.cuda.get_device_name(0)}")
    print(f"capability      : {cap}")
    print(f"arch list       : {arches}")
    print(f"free/total VRAM : {free / 2**20:.0f} / {total / 2**20:.0f} MiB")

    try:
        import triton  # installed by torch as a dependency
        print(f"triton          : {triton.__version__}")
    except ImportError:
        print("triton          : NOT INSTALLED")

    ok = cap == (7, 5) and "sm_75" in arches
    print("V1 PASS" if ok else "V1 FAIL: capability is not (7, 5) or sm_75 is missing")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
