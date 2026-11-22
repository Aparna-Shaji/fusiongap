"""4F packaging spike - a real installable package around the 4E kernel."""
from . import _C  # noqa: F401

copy_cuda = _C.copy_cuda
__all__ = ["copy_cuda"]
