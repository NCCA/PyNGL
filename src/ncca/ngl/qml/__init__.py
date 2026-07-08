"""QML widgets exposing NGL math types to Qt Quick applications."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ncca-ngl")  # pragma: no cover
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

__author__ = "Jon Macey jmacey@bournemouth.ac.uk"
__license__ = "MIT"

from .mat2_model import Mat2Model
from .vec2_model import Vec2Model
from .vec3_model import Vec3Model
from .vec4_model import Vec4Model

__all__ = [
    "Vec2Model",
    "Vec3Model",
    "Vec4Model",
    "Mat2Model",
]
