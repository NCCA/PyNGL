"""Widget for editing a Mat2 as an editable 2x2 grid."""

from PySide6.QtCore import Property, Signal
from PySide6.QtWidgets import QWidget

from ncca.ngl import Mat2

from .mat_grid_widget import _MatGridWidget


class Mat2Widget(_MatGridWidget):
    """A widget for displaying and editing a Mat2 object as an editable grid."""

    valueChanged = Signal(Mat2)

    def __init__(
        self,
        parent: QWidget | None = None,
        name: str = "",
        read_only: bool = False,
    ) -> None:
        """Initialize the widget.

        Args:
            parent: The parent widget.
            name: The name of the widget.
            read_only: If True, the grid is a view-only display: no
                editing, no reset buttons.
        """
        super().__init__(Mat2, 2, parent, name, read_only)

    value = Property(Mat2, _MatGridWidget.get_value, _MatGridWidget.set_value)
