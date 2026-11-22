# 4H - Kaggle T4 smoke, 2026-11-22

A second SM_75 device, on a different machine, with a different driver and no
WSL underneath. Run unattended from a Kaggle notebook with a GPU T4 x2
accelerator; only device 0 was used.

## What passed

Both phases: the Triton add kernel, the templated CUDA square kernel, gradcheck
in fp64 on the true backward, and gradcheck rejecting a planted 3x backward.

- Phase 1, Kaggle's stock stack: torch 2.11.0+cu130, triton 3.6.0, nvcc 13.0.88
- Phase 2, this project's pins:   torch 2.15.0+cu132, triton 3.9.0, nvcc 13.0.88

## What it tells us

| | GTX 1650 (local) | Tesla T4 (Kaggle) |
|---|---|---|
| Compute capability | 7.5 | 7.5 |
| Usable VRAM | 3.2 GiB after context | 14.5 GiB |
| Enforced power limit | 30 W, set from Windows | 70 W |
| cpp_extension build, one .cu | 193 s | 63 s |

1. The pinned stack installs and runs on a non-WSL Linux. Evidence for 5D.
2. nvcc 13.0.88 built an extension against torch's CUDA 13.2 without complaint,
   so the "toolkit major.minor must equal torch.version.cuda" rule in the stage
   03 evaluation is stricter than reality. [VERIFY: read the version check in
   torch/utils/cpp_extension.py at 5A.] If major-only is the real rule, RV-27's
   exposure narrows.
3. Installing pinned torch over a populated environment leaves torchvision
   demanding the old version. Harmless here; a trap at 5D if the rebuild starts
   from anything other than a clean distro.

## Closed by this run

- V10 Kaggle accelerators: T4 only, confirmed in the session panel
- F9  quota: 30 GPU hours per week, 30 remaining before this run
- R11 Kaggle smoke: executed
