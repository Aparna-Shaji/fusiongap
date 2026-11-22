// spikes/4E/copy_kernel.cu
//
// 4E - C++/CUDA readiness spike. out[i] = in[i] for i in [0, n).
//
// The arithmetic is trivial on purpose. This file exists to establish the
// shape every later CUDA kernel in this project copies: index, tail guard,
// current stream, launch check, and a wrapper that refuses inputs whose
// layout the kernel assumes away. Each of those is commented with the
// invariant it protects, because a reviewer will ask about each one.

#include <torch/extension.h>
#include <ATen/cuda/CUDAContext.h>
#include <c10/cuda/CUDAException.h>

namespace {

constexpr int kBlock = 256;  // must equal BLOCK in test_copy.py

__global__ void copy_kernel(const float* __restrict__ in,
                            float* __restrict__ out,
                            long long n) {
  // I1: blocks are numbered 0..G-1 and threads 0..kBlock-1, so b*kBlock+t
  // hits every index in [0, G*kBlock) exactly once. blockIdx and blockDim
  // are unsigned int; widen before multiplying so a large grid cannot wrap.
  long long i = static_cast<long long>(blockIdx.x) * blockDim.x + threadIdx.x;

  // I2: G = ceil(n/kBlock), so G*kBlock - n threads have an index past the
  // end. Without this line they write outside the allocation - silently,
  // because the CUDA allocator pads.
  if (i < n) {
    out[i] = in[i];
  }
}

}  // namespace

at::Tensor copy_cuda(const at::Tensor& in) {
  // I3: each of these inputs has a valid data pointer and the wrong
  // assumptions. A non-contiguous tensor is the dangerous one - it reads
  // garbage without erroring.
  TORCH_CHECK(in.is_cuda(),
              "copy_cuda: input must be a CUDA tensor, got ", in.device());
  TORCH_CHECK(in.scalar_type() == at::kFloat,
              "copy_cuda: input must be float32, got ", in.scalar_type());
  TORCH_CHECK(in.is_contiguous(),
              "copy_cuda: input must be contiguous");

  at::Tensor out = at::empty_like(in);
  const long long n = in.numel();

  // ceil(0/kBlock) is 0 blocks, and a launch with gridDim.x == 0 is an
  // invalid configuration. Return before launching.
  if (n == 0) {
    return out;
  }

  const long long blocks = (n + kBlock - 1) / kBlock;
  TORCH_CHECK(blocks <= 2147483647LL, "copy_cuda: grid too large for one dimension");

  // The kernel runs on the stream PyTorch is currently using, so it is
  // ordered against the caller's other work. Launching on the default
  // stream instead would silently race with it.
  auto stream = at::cuda::getCurrentCUDAStream();
  copy_kernel<<<static_cast<unsigned int>(blocks), kBlock, 0, stream>>>(
      in.data_ptr<float>(), out.data_ptr<float>(), n);

  // Launches are asynchronous and a failed launch is not reported here
  // unless we ask. Without this, the error surfaces later, somewhere
  // unrelated, and costs an afternoon.
  C10_CUDA_KERNEL_LAUNCH_CHECK();

  return out;
}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
  m.def("copy_cuda", &copy_cuda,
        "copy a contiguous float32 CUDA tensor (4E readiness spike)");
}
