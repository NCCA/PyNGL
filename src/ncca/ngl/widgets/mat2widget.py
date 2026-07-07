"""Widget for editing a Mat2 as an editable 2x2 grid."""

from PySide6.QtCore import Property, Signal
from PySide6.QtWidgets import QWidget

from ncca.ngl import Mat2

from .mat_grid_widget import _MatGridWidget


class Mat2Widget(_MatGridWidget):
    """A widget for displaying and editing a Mat2 object as an editable grid."""

    valueChanged = Signal(Mat2)

    def __init__(self, parent: QWidget | None = None, name: str = "") -> None:
        """Initialize the widget.

        Args:
            parent: The parent widget.
            name: The name of the widget.
        """
        super().__init__(Mat2, 2, parent, name)

    value = Property(Mat2, _MatGridWidget.get_value, _MatGridWidget.set_value)
