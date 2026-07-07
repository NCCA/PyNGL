"""Shared base widget for editable NxN matrix grids (Mat2/Mat3/Mat4)."""

from contextlib import ExitStack
from typing import Callable

from PySide6.QtCore import Property, QSignalBlocker
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ncca.ngl import Vec3
from ncca.ngl.mat_base import MatrixBase, MatrixError

from .vec3widget import Vec3Widget


class _MatGridWidget(QFrame):
    """Base widget providing a shared editable NxN matrix grid.

    Not intended to be used directly; subclassed by Mat2Widget, Mat3Widget
    and Mat4Widget.
    """

    def __init__(
        self,
        mat_cls: type[MatrixBase],
        size: int,
        parent: QWidget | None = None,
        name: str = "",
    ) -> None:
        """Initialize the widget.

        Args:
            mat_cls: The matrix class this widget edits (Mat2, Mat3 or Mat4).
            size: The row/column count of the matrix.
            parent: The parent widget.
            name: The name of the widget.
        """
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._mat_cls = mat_cls
        self._size = size
        self._name = name
        self._value = mat_cls()

        self._main_layout = QVBoxLayout(self)
        self._name_label = QLabel(self._name)
        self._main_layout.addWidget(self._name_label)
        self._cells = self._build_grid()
        self._build_buttons()

    def _build_grid(self) -> list[list[QDoubleSpinBox]]:
        """Build the NxN grid of spinboxes and add it to the main layout.

        Returns:
            A row-major list of lists of the created spinboxes.
        """
        grid_layout = QGridLayout()
        cells = []
        for row in range(self._size):
            cell_row = []
            for col in range(self._size):
                spinbox = QDoubleSpinBox()
                spinbox.setRange(-20.0, 20.0)
                spinbox.setSingleStep(0.01)
                spinbox.setValue(self._value[row][col])
                spinbox.valueChanged.connect(
                    lambda value, r=row, c=col: self._on_cell_changed(r, c, value)
                )
                grid_layout.addWidget(spinbox, row, col)
                cell_row.append(spinbox)
            cells.append(cell_row)
        self._main_layout.addLayout(grid_layout)
        return cells

    def _build_buttons(self) -> None:
        """Build the Identity/Zero/Transpose/Inverse reset buttons."""
        button_layout = QHBoxLayout()

        self._identity_button = QPushButton("Identity")
        self._identity_button.clicked.connect(
            lambda: self.set_value(self._mat_cls.identity())
        )
        button_layout.addWidget(self._identity_button)

        self._zero_button = QPushButton("Zero")
        self._zero_button.clicked.connect(lambda: self.set_value(self._mat_cls.zero()))
        button_layout.addWidget(self._zero_button)

        self._transpose_button = QPushButton("Transpose")
        self._transpose_button.clicked.connect(
            lambda: self.set_value(self._value.transposed())
        )
        button_layout.addWidget(self._transpose_button)

        self._inverse_button = QPushButton("Inverse")
        self._inverse_button.clicked.connect(self._on_inverse_clicked)
        button_layout.addWidget(self._inverse_button)

        self._main_layout.addLayout(button_layout)

        self._status_label = QLabel("")
        self._main_layout.addWidget(self._status_label)

    def _add_method_combo(self, methods: dict[str, tuple[str, Callable]]) -> None:
        """Add a combo box that sets the matrix via a classmethod.

        Args:
            methods: Maps a display label to (param_kind, factory), where
                param_kind is "angle" (a single degrees spinbox) or "xyz"
                (an embedded Vec3Widget), and factory is the matrix
                classmethod called with the resulting parameter(s).
        """
        self._methods = methods

        self._method_combo = QComboBox()
        for label in methods:
            self._method_combo.addItem(label)
        self._main_layout.addWidget(self._method_combo)

        self._angle_spinbox = QDoubleSpinBox()
        self._angle_spinbox.setRange(-360.0, 360.0)
        self._angle_spinbox.setSingleStep(0.5)

        self._xyz_widget = Vec3Widget(self, "xyz", Vec3(1.0, 1.0, 1.0))

        self._param_stack = QStackedWidget()
        self._param_stack.addWidget(self._angle_spinbox)
        self._param_stack.addWidget(self._xyz_widget)
        self._main_layout.addWidget(self._param_stack)

        first_label = next(iter(methods))
        self._show_panel_for(first_label)

        self._method_combo.currentIndexChanged.connect(self._on_method_selected)
        self._angle_spinbox.valueChanged.connect(self._on_method_param_changed)
        self._xyz_widget.valueChanged.connect(self._on_method_param_changed)

    def _show_panel_for(self, label: str) -> None:
        """Switch the parameter panel to match the given method's kind.

        Args:
            label: The method's display label, as shown in the combo box.
        """
        kind, _ = self._methods[label]
        if kind == "angle":
            self._param_stack.setCurrentWidget(self._angle_spinbox)
        else:
            self._param_stack.setCurrentWidget(self._xyz_widget)

    def _on_method_selected(self, index: int) -> None:
        """Switch panels and reapply the newly selected method.

        Args:
            index: The index of the newly selected combo box item.
        """
        self._show_panel_for(self._method_combo.itemText(index))
        self._apply_selected_method()

    def _apply_selected_method(self) -> None:
        """Recompute the matrix from the selected method and its parameters."""
        kind, factory = self._methods[self._method_combo.currentText()]
        if kind == "angle":
            self.set_value(factory(self._angle_spinbox.value()))
        else:
            xyz = self._xyz_widget.get_value()
            self.set_value(factory(xyz.x, xyz.y, xyz.z))

    def _on_method_param_changed(self) -> None:
        """Recompute the matrix when the visible parameter panel changes."""
        self._apply_selected_method()

    def _on_inverse_clicked(self) -> None:
        """Invert the current value, or show a status message if singular."""
        try:
            inverted = self._value.inverse()
        except MatrixError:
            self._status_label.setText("Matrix is singular")
            return
        self._status_label.setText("")
        self.set_value(inverted)

    def _on_cell_changed(self, row: int, col: int, value: float) -> None:
        """Update the matrix value when a grid cell is edited.

        Args:
            row: The row index of the edited cell.
            col: The column index of the edited cell.
            value: The new value of the cell.
        """
        self._value[row][col] = value
        self.valueChanged.emit(self._value)

    def get_value(self) -> MatrixBase:
        """Get the current matrix value.

        Returns:
            The current value of the widget.
        """
        return self._value

    def set_value(self, value: MatrixBase) -> None:
        """Set the matrix value, updating the grid and emitting valueChanged.

        Args:
            value: The new value of the widget.
        """
        with ExitStack() as stack:
            for row in self._cells:
                for spinbox in row:
                    stack.enter_context(QSignalBlocker(spinbox))
            for row in range(self._size):
                for col in range(self._size):
                    self._cells[row][col].setValue(value[row][col])
        self._value = value
        self.valueChanged.emit(self._value)

    def get_name(self) -> str:
        """Get the widget's name.

        Returns:
            The name of the widget.
        """
        return self._name

    def set_name(self, name: str) -> None:
        """Set the widget's name.

        Args:
            name: The new name of the widget.
        """
        self._name = name
        self._name_label.setText(name)

    name = Property(str, get_name, set_name)

    def set_range(self, min_val: float, max_val: float) -> None:
        """Set the range for all cell spinboxes.

        Args:
            min_val: The minimum value.
            max_val: The maximum value.
        """
        for row in self._cells:
            for spinbox in row:
                spinbox.setRange(min_val, max_val)

    def set_single_step(self, step: float) -> None:
        """Set the single step for all cell spinboxes.

        Args:
            step: The single step value.
        """
        for row in self._cells:
            for spinbox in row:
                spinbox.setSingleStep(step)
