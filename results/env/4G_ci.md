# 4G - CI feasibility on a GPU-less runner (R10, V7, F11)

Branch: spike/ci (kept, never merged to main - stage 15 designs the real CI)
Green run: 45020691646, 2026-11-22. Earlier red runs kept: 45019060150, 45019801067.

## Result

| Question | Answer |
|---|---|
| Can a GPU-less runner test a Triton kernel? | Yes, TRITON_INTERPRET=1, 51 s - and only with numpy installed (V7) |
| Can a GPU-less runner compile our CUDA code? | Yes, nvcc -c -arch=sm_75, 4 m 11 s - with the CUDA torch wheel's headers, not the CPU wheel's |
| Cost on a public repository | Free; about 5 minutes of wall time per push (F11) |
| Does the runner have a GPU? | No, and neither check needs one |

## Three failures on the way, each one a finding

1. numpy absent -> ModuleNotFoundError from triton/runtime/interpreter.py,
   raised while triton.language was importing, because @jit pulls the
   interpreter in at decoration time. numpy is a hard requirement of the
   only mechanism that tests a Triton kernel without a GPU. It was recorded
   here as a cosmetic warning; it is not.
2. cuda-nvcc alone -> fatal error: cusparse.h. ATen/cuda/CUDAContextLight.h
   wants cuSPARSE, cuBLAS and cuSOLVER headers for libraries this project
   never calls.
3. CPU torch wheel -> fatal error: c10/cuda/impl/cuda_cmake_macros.h, a file
   generated during a CUDA build and absent from CPU wheels. A translation
   unit including ATen/cuda cannot compile against CPU torch at all.

Findings 2 and 3 join 4E's build memory (2.64 GiB) and build time (193 s)
as the third and fourth independent arguments for separating host code
(.cpp, torch and pybind) from device code (.cu, raw pointers) at stage 15.
A .cu with no ATen include needs none of the above and would turn a 4 m 11 s
job into a ~30 s one, on every push, for the life of the project.

## Raw proof extracted from run 45020691646
```
Cuda compilation tools, release 13.2, V13.2.86
-rw-r--r-- 1 runner runner 467368 Nov 22 12:11 /tmp/copy_kernel.cu.o
-rw-r--r-- 1 runner runner 536008 Nov 22 12:12 /tmp/fp64_kernels.cu.o
============================== 3 passed in 1.27s ===============================
```
