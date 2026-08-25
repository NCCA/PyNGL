"""WebGPU rendering stack for PyNGL: widgets, pipelines, and shader helpers."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ncca-ngl")  # pragma: no cover
except PackageNotFoundError:
    __version__ = "0.0.0"  # pragma: no cover

__author__ = "Jon Macey jmacey@bournemouth.ac.uk"
__license__ = "MIT"

from .pipeline_factory import PipelineFactory, PipelineType
from .mesh import (
    STANDARD_MESH_TOPOLOGY,
    STANDARD_MESH_VERTEX_STRIDE,
    WebGPUMesh,
    standard_mesh_vertex_layout,
)
from .webgpu_constants import NGLToWebGPU
from .webgpu_widget import WebGPUWidget

__all__ = [
    "WebGPUWidget",
    "NGLToWebGPU",
    "PipelineFactory",
    "PipelineType",
    "STANDARD_MESH_TOPOLOGY",
    "STANDARD_MESH_VERTEX_STRIDE",
    "WebGPUMesh",
    "standard_mesh_vertex_layout",
]
