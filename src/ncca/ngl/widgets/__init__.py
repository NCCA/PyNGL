"""PySide6 widgets for editing and displaying NGL math types."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ncca-ngl")  # pragma: no cover
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

__author__ = "Jon Macey jmacey@bournemouth.ac.uk"
__license__ = "MIT"


from .lookatwidget import LookAtWidget
from .mat2widget import Mat2Widget
from .mat3widget import Mat3Widget
from .mat4widget import Mat4Widget
from .perspectivewidget import PerspectiveWidget
from .rgbacolourwidget import RGBAColourWidget
from .rgbcolourwidget import RGBColourWidget
from .transformwidget import TransformWidget
from .vec2widget import Vec2Widget
from .vec3widget import Vec3Widget
from .vec4widget import Vec4Widget

__all__ = [
    "Vec2Widget",
    "Vec3Widget",
    "Vec4Widget",
    "TransformWidget",
    "LookAtWidget",
    "PerspectiveWidget",
    "RGBColourWidget",
    "RGBAColourWidget",
    "Mat2Widget",
    "Mat3Widget",
    "Mat4Widget",
]
