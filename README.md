# FusionGap

Where does `torch.compile` leave performance on the table? A measurement study of hand-written Triton and CUDA C++ kernels against PyTorch's compiler on a 4 GB consumer GPU (NVIDIA GTX 1650, Turing, compute capability 7.5).

**Status: work in progress**. The toolchain is verified on the target GPU: CUDA 13.2, PyTorch 2.15, Triton 3.9. Dated predictions will be published in this repository before any results exist. No kernel code yet.
