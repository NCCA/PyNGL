# generate auto __version__
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ncca-ngl")  # pragma: no cover
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"
__author__ = "Jon Macey jmacey@bournemouth.ac.uk"
__license__ = "MIT"

from .abstract_vao import AbstractVAO, VertexData
from .base_mesh import BaseMesh, Face
from .bbox import BBox
from .bezier_curve import BezierCurve
from .first_person_camera import FirstPersonCamera
from .image import Image, ImageModes
from .log import logger
from .mat2 import Mat2, Mat2Error, Mat2NotSquare
from .mat3 import Mat3, Mat3Error, Mat3NotSquare
from .mat4 import Mat4, Mat4Error, Mat4NotSquare
from .multi_buffer_vao import MultiBufferVAO
from .obj import (
    Obj,
    ObjParseFaceError,
    ObjParseNormalError,
    ObjParseUVError,
    ObjParseVertexError,
)
from .plane import Plane
from .prim_data import PrimData, Prims
from .primitives import Primitives
from .pyside_event_handling_mixin import PySideEventHandlingMixin
from .quaternion import Quaternion
from .random import Random
from .shader import MatrixTranspose, Shader, ShaderType
from .shader_lib import DefaultShader, ShaderLib
from .shader_program import ShaderProgram
from .simple_index_vao import IndexVertexData, SimpleIndexVAO
from .simple_vao import SimpleVAO
from .text import Text
from .texture import Texture
from .transform import Transform, TransformRotationOrder
from .util import (
    PerspMode,
    calc_normal,
    clamp,
    frustum,
    lerp,
    look_at,
    ortho,
    perspective,
    prim_data_to_ri_points_polygons,
    renderman_look_at,
)
from .vao_factory import VAOFactory, VAOType
from .vec2 import Vec2
from .vec2_array import Vec2Array
from .vec3 import Vec3
from .vec3_array import Vec3Array
from .vec4 import Vec4
from .vec4_array import Vec4Array

__all__ = [
    "AbstractVAO",
    "VertexData",
    "BaseMesh",
    "Face",
    "BBox",
    "BezierCurve",
    "FirstPersonCamera",
    "Image",
    "ImageModes",
    "logger",
    "Mat2",
    "Mat2Error",
    "Mat2NotSquare",
    "Mat3",
    "Mat3Error",
    "Mat3NotSquare",
    "Mat4",
    "Mat4Error",
    "Mat4NotSquare",
    "MultiBufferVAO",
    "Obj",
    "ObjParseFaceError",
    "ObjParseNormalError",
    "ObjParseUVError",
    "ObjParseVertexError",
    "Plane",
    "PrimData",
    "Prims",
    "Primitives",
    "PySideEventHandlingMixin",
    "Quaternion",
    "Random",
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
    "Transform",
    "TransformRotationOrder",
    "PerspMode",
    "calc_normal",
    "clamp",
    "frustum",
    "lerp",
    "look_at",
    "ortho",
    "perspective",
    "prim_data_to_ri_points_polygons",
    "renderman_look_at",
    "VAOFactory",
    "VAOType",
    "Vec2",
    "Vec2Array",
    "Vec3",
    "Vec3Array",
    "Vec4",
    "Vec4Array",
]
