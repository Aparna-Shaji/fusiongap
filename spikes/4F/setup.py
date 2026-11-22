"""4F - the smallest real package that contains a compiled CUDA extension.

Deliberately named fusiongap-spike4f, not fusiongap: the question is whether
the artefact format is accepted, which does not depend on the name, and
uploading the real name to TestPyPI would claim it there for a throwaway.
"""
from setuptools import setup
from torch.utils.cpp_extension import BuildExtension, CUDAExtension

setup(
    name="fusiongap-spike4f",
    version="0.0.1",
    description="Packaging feasibility spike for FusionGap (4F). Not a library.",
    packages=["fusiongap_spike4f"],
    ext_modules=[
        CUDAExtension(
            name="fusiongap_spike4f._C",
            sources=["fusiongap_spike4f/copy_kernel.cu"],
            extra_compile_args={"cxx": ["-O2"], "nvcc": ["-O2"]},
        )
    ],
    cmdclass={"build_ext": BuildExtension},
    python_requires=">=3.14",
)
