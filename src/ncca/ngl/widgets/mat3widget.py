"""Widget for editing a Mat3 as an editable 3x3 grid."""

from PySide6.QtCore import Property, Signal
from PySide6.QtWidgets import QWidget

from ncca.ngl import Mat3

from .mat_grid_widget import _MatGridWidget


class Mat3Widget(_MatGridWidget):
    """A widget for displaying and editing a Mat3 object as an editable grid."""

    valueChanged = Signal(Mat3)

    def __init__(self, parent: QWidget | None = None, name: str = "") -> None:
        """Initialize the widget.

        Args:
            parent: The parent widget.
            name: The name of the widget.
        """
        super().__init__(Mat3, 3, parent, name)
        self._add_method_combo(
            {
                "rotate_x": ("angle", Mat3.rotate_x),
                "rotate_y": ("angle", Mat3.rotate_y),
                "rotate_z": ("angle", Mat3.rotate_z),
                "scale": ("xyz", Mat3.scale),
            }
        )

    value = Property(Mat3, _MatGridWidget.get_value, _MatGridWidget.set_value)
