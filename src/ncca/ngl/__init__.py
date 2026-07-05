# generate auto __version__
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ncca-ngl")  # pragma: no cover
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"
__author__ = "Jon Macey jmacey@bournemouth.ac.uk"
__license__ = "MIT"

from .bbox import BBox
from .bezier_curve import BezierCurve
from .first_person_camera import FirstPersonCamera
from .image import Image, ImageModes
from .log import logger
from .mat2 import Mat2
from .mat3 import Mat3
from .mat4 import Mat4
from .mat_base import MatrixError
from .obj import (
    Obj,
    ObjParseFaceError,
    ObjParseNormalError,
    ObjParseUVError,
    ObjParseVertexError,
)
from .plane import Plane
from .prim_data import PrimData, Prims
from .quaternion import Quaternion
from .random import Random
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
from .vec2 import Vec2
from .vec2_array import Vec2Array
from .vec3 import Vec3
from .vec3_array import Vec3Array
from .vec4 import Vec4
from .vec4_array import Vec4Array

__all__ = [
    "BBox",
    "BezierCurve",
    "FirstPersonCamera",
    "Image",
    "ImageModes",
    "logger",
    "Mat2",
    "Mat3",
    "Mat4",
    "MatrixError",
    "Obj",
    "ObjParseFaceError",
    "ObjParseNormalError",
    "ObjParseUVError",
    "ObjParseVertexError",
    "Plane",
    "PrimData",
    "Prims",
    "Quaternion",
    "Random",
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
    "Vec2",
    "Vec2Array",
    "Vec3",
    "Vec3Array",
    "Vec4",
    "Vec4Array",
]
