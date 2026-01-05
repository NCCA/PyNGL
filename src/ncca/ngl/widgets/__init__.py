from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ncca-ngl")
except PackageNotFoundError:
    __version__ = "0.0.0"

__author__ = "Jon Macey jmacey@bournemouth.ac.uk"
__license__ = "MIT"


from .lookatwidget import LookAtWidget
from .rgbacolourwidget import RGBAColourWidget
from .rgbcolourwidget import RGBColourWidget
from .transformwidget import TransformWidget
from .vec2widget import Vec2Widget
from .vec3widget import Vec3Widget
from .vec4widget import Vec4Widget

__all__ = ["Vec2Widget", "Vec3Widget", "Vec4Widget", "TransformWidget", "LookAtWidget", "RGBColourWidget"]
