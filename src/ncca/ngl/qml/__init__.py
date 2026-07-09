"""QML widgets exposing NGL math types to Qt Quick applications."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from PySide6.QtQml import QQmlEngine

try:
    __version__ = version("ncca-ngl")  # pragma: no cover
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

__author__ = "Jon Macey jmacey@bournemouth.ac.uk"
__license__ = "MIT"

from .lookat_model import LookAtModel
from .mat2_model import Mat2Model
from .mat3_model import Mat3Model
from .mat4_model import Mat4Model
from .rgb_colour_model import RGBColourModel
from .rgba_colour_model import RGBAColourModel
from .transform_model import TransformModel
from .vec2_model import Vec2Model
from .vec3_model import Vec3Model
from .vec4_model import Vec4Model

__all__ = [
    "Vec2Model",
    "Vec3Model",
    "Vec4Model",
    "Mat2Model",
    "Mat3Model",
    "Mat4Model",
    "TransformModel",
    "LookAtModel",
    "RGBColourModel",
    "RGBAColourModel",
    "import_path",
    "add_import_path",
]


def import_path() -> Path:
    """Return the directory to add to a QML engine's import path.

    ``ncca.ngl.qml`` is a file-based QML module whose ``qmldir`` declares
    ``module ncca.ngl.qml``, so ``import ncca.ngl.qml 1.0`` only resolves from
    an external ``.qml`` file if the engine's import path is the directory that
    *contains* the ``ncca/`` package (``parents[3]`` of this file:
    ``qml -> ngl -> ncca -> containing dir``), not the ``qml/`` leaf directory.

    This is derived from the module file rather than ``ncca.__file__`` because
    ``ncca`` is a PEP 420 namespace package and so has no ``__file__``.
    """
    return Path(__file__).parents[3]


def add_import_path(engine: QQmlEngine) -> None:
    """Register ``ncca.ngl.qml``'s import path on a QML engine.

    Call this once after constructing the engine so that ``import ncca.ngl.qml``
    resolves in your own ``.qml`` files. Works for both ``QQmlApplicationEngine``
    and ``QQuickWidget.engine()`` (both are ``QQmlEngine``).
    """
    engine.addImportPath(str(import_path()))
