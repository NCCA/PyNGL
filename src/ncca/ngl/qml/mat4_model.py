"""QML-exposed model for editing a Mat4 as a 4x4 grid with a method combo."""

from PySide6.QtCore import Slot
from PySide6.QtQml import QmlElement

from ncca.ngl import Mat4

from .mat_grid_model import MatGridModel

QML_IMPORT_NAME = "ncca.ngl.qml"
QML_IMPORT_MAJOR_VERSION = 1

_METHODS = {
    "rotate_x": ("angle", Mat4.rotate_x),
    "rotate_y": ("angle", Mat4.rotate_y),
    "rotate_z": ("angle", Mat4.rotate_z),
    "scale": ("xyz", Mat4.scale),
    "translate": ("xyz", Mat4.translate),
}


@QmlElement
class Mat4Model(MatGridModel):
    """Grid model for a Mat4, with a rotate/scale/translate method combo."""

    mat_cls = Mat4
    size = 4

    @Slot(result=list)
    def method_names(self) -> list:
        """Return the ordered list of available method names for the combo box.

        Returns:
            The method display names, in combo-box order.
        """
        return list(_METHODS)

    @Slot(str, result=str)
    def method_kind(self, name: str) -> str:
        """Return the parameter kind for a method name.

        Args:
            name: One of the names returned by `method_names()`.

        Returns:
            `"angle"` for a single-degrees method, `"xyz"` for a 3-component one.
        """
        return _METHODS[name][0]

    @Slot(str, float)
    def apply_angle_method(self, name: str, degrees: float) -> None:
        """Apply an angle-based method (rotate_x/y/z) by degrees.

        Args:
            name: The method name (must have kind `"angle"`).
            degrees: The rotation angle in degrees.
        """
        _, factory = _METHODS[name]
        self.set_value(factory(degrees))

    @Slot(str, float, float, float)
    def apply_xyz_method(self, name: str, x: float, y: float, z: float) -> None:
        """Apply an xyz-based method (scale/translate) with the given components.

        Args:
            name: The method name (must have kind `"xyz"`).
            x: The x component.
            y: The y component.
            z: The z component.
        """
        _, factory = _METHODS[name]
        self.set_value(factory(x, y, z))
