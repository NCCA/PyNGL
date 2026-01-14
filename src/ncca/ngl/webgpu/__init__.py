from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ncca-ngl")  # pragma: no cover
except PackageNotFoundError:
    __version__ = "0.0.0"  # pragma: no cover

__author__ = "Jon Macey jmacey@bournemouth.ac.uk"
__license__ = "MIT"

from .pipeline_factory import PipelineFactory, PipelineType
from .webgpu_constants import NGLToWebGPU
from .webgpu_widget import WebGPUWidget

__all__ = ["WebGPUWidget", "NGLToWebGPU", "PipelineFactory", "PipelineType"]
