// spikes/4I/fp64_kernels.cu
//
// 4I - the fp64 correctness path (R3).
//
// One kernel body per operation, templated on the scalar type and dispatched
// by torch across half, float and double. This is the shape every kernel in
// the library will use: the project's correctness gate runs gradcheck in
// fp64, so every kernel must have a double instantiation that compiles and
// is numerically exact enough for finite differences to be meaningful.

#include <torch/extension.h>
#include <ATen/cuda/CUDAContext.h>
#include <c10/cuda/CUDAException.h>

namespace {

constexpr int kBlock = 256;

template <typename scalar_t>
__global__ void copy_kernel_t(const scalar_t* __restrict__ in,
                              scalar_t* __restrict__ out, long long n) {
  long long i = static_cast<long long>(blockIdx.x) * blockDim.x + threadIdx.x;
  if (i < n) out[i] = in[i];
}

template <typename scalar_t>
__global__ void square_fwd_kernel(const scalar_t* __restrict__ x,
                                  scalar_t* __restrict__ y, long long n) {
  long long i = static_cast<long long>(blockIdx.x) * blockDim.x + threadIdx.x;
  if (i < n) y[i] = x[i] * x[i];
}

// d/dx (x*x) = 2x. coeff is the derivative's leading constant and is passed
// in rather than hard-coded, so the planted-wrong control (coeff = 3) runs
// through this exact kernel instead of a separate copy that might differ in
// some other way as well.
template <typename scalar_t>
__global__ void square_bwd_kernel(const scalar_t* __restrict__ gout,
                                  const scalar_t* __restrict__ x,
                                  scalar_t* __restrict__ gin,
                                  scalar_t coeff, long long n) {
  long long i = static_cast<long long>(blockIdx.x) * blockDim.x + threadIdx.x;
  if (i < n) gin[i] = gout[i] * coeff * x[i];
}

inline long long grid_for(long long n) { return (n + kBlock - 1) / kBlock; }

void check_input(const at::Tensor& t, const char* who) {
  TORCH_CHECK(t.is_cuda(), who, ": expected a CUDA tensor, got ", t.device());
  TORCH_CHECK(t.is_contiguous(), who, ": expected a contiguous tensor");
}

}  // namespace

at::Tensor copy_any(const at::Tensor& in) {
  check_input(in, "copy_any");
  at::Tensor out = at::empty_like(in);
  const long long n = in.numel();
  if (n == 0) return out;
  auto stream = at::cuda::getCurrentCUDAStream();
  AT_DISPATCH_FLOATING_TYPES_AND_HALF(in.scalar_type(), "copy_any", ([&] {
    copy_kernel_t<scalar_t><<<grid_for(n), kBlock, 0, stream>>>(
        in.data_ptr<scalar_t>(), out.data_ptr<scalar_t>(), n);
    C10_CUDA_KERNEL_LAUNCH_CHECK();
  }));
  return out;
}

at::Tensor square_fwd(const at::Tensor& x) {
  check_input(x, "square_fwd");
  at::Tensor y = at::empty_like(x);
  const long long n = x.numel();
  if (n == 0) return y;
  auto stream = at::cuda::getCurrentCUDAStream();
  AT_DISPATCH_FLOATING_TYPES_AND_HALF(x.scalar_type(), "square_fwd", ([&] {
    square_fwd_kernel<scalar_t><<<grid_for(n), kBlock, 0, stream>>>(
        x.data_ptr<scalar_t>(), y.data_ptr<scalar_t>(), n);
    C10_CUDA_KERNEL_LAUNCH_CHECK();
  }));
  return y;
}

at::Tensor square_bwd(const at::Tensor& gout, const at::Tensor& x, double coeff) {
  check_input(gout, "square_bwd");
  check_input(x, "square_bwd");
  TORCH_CHECK(gout.sizes() == x.sizes(), "square_bwd: shape mismatch");
  TORCH_CHECK(gout.scalar_type() == x.scalar_type(), "square_bwd: dtype mismatch");
  at::Tensor gin = at::empty_like(x);
  const long long n = x.numel();
  if (n == 0) return gin;
  auto stream = at::cuda::getCurrentCUDAStream();
  AT_DISPATCH_FLOATING_TYPES_AND_HALF(x.scalar_type(), "square_bwd", ([&] {
    scalar_t c = static_cast<scalar_t>(coeff);
    square_bwd_kernel<scalar_t><<<grid_for(n), kBlock, 0, stream>>>(
        gout.data_ptr<scalar_t>(), x.data_ptr<scalar_t>(),
        gin.data_ptr<scalar_t>(), c, n);
    C10_CUDA_KERNEL_LAUNCH_CHECK();
  }));
  return gin;
}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
  m.def("copy_any", &copy_any, "typed copy (half/float/double)");
  m.def("square_fwd", &square_fwd, "y = x*x");
  m.def("square_bwd", &square_bwd, "dx = gout * coeff * x");
}
