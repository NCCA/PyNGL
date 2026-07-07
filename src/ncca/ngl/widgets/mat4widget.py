"""Widget for editing a Mat4 as an editable 4x4 grid."""

from PySide6.QtCore import Property, Signal
from PySide6.QtWidgets import QWidget

from ncca.ngl import Mat4

from .mat_grid_widget import _MatGridWidget


class Mat4Widget(_MatGridWidget):
    """A widget for displaying and editing a Mat4 object as an editable grid."""

    valueChanged = Signal(Mat4)

    def __init__(self, parent: QWidget | None = None, name: str = "") -> None:
        """Initialize the widget.

        Args:
            parent: The parent widget.
            name: The name of the widget.
        """
        super().__init__(Mat4, 4, parent, name)
        self._add_method_combo(
            {
                "rotate_x": ("angle", Mat4.rotate_x),
                "rotate_y": ("angle", Mat4.rotate_y),
                "rotate_z": ("angle", Mat4.rotate_z),
                "scale": ("xyz", Mat4.scale),
                "translate": ("xyz", Mat4.translate),
            }
        )

    value = Property(Mat4, _MatGridWidget.get_value, _MatGridWidget.set_value)
