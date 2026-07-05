from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ncca-ngl")  # pragma: no cover
except PackageNotFoundError:
    __version__ = "0.0.0"  # pragma: no cover

__author__ = "Jon Macey jmacey@bournemouth.ac.uk"
__license__ = "MIT"

from .abstract_vao import AbstractVAO, VertexData
from .base_mesh import BaseMesh, Face
from .multi_buffer_vao import MultiBufferVAO
from .primitives import Primitives
from .pyside_event_handling_mixin import PySideEventHandlingMixin
from .shader import MatrixTranspose, Shader, ShaderType
from .shader_lib import DefaultShader, ShaderLib
from .shader_program import ShaderProgram
from .simple_index_vao import IndexVertexData, SimpleIndexVAO
from .simple_vao import SimpleVAO
from .text import Text
from .texture import Texture
from .vao_factory import VAOFactory, VAOType

__all__ = [
    "AbstractVAO",
    "VertexData",
    "BaseMesh",
    "Face",
    "MultiBufferVAO",
    "Primitives",
    "PySideEventHandlingMixin",
    "MatrixTranspose",
    "Shader",
    "ShaderType",
    "DefaultShader",
    "ShaderLib",
    "ShaderProgram",
    "IndexVertexData",
    "SimpleIndexVAO",
    "SimpleVAO",
    "Text",
    "Texture",
    "VAOFactory",
    "VAOType",
]
