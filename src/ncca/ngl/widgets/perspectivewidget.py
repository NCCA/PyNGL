"""Widget for editing fov/aspect/near/far and producing a perspective matrix."""

from PySide6.QtCore import Property, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ncca.ngl import Mat4, PerspMode, perspective

_MODE_NAMES = ["OpenGL", "Vulkan", "WebGPU"]
_MODE_BY_NAME = {
    "OpenGL": PerspMode.OpenGL,
    "Vulkan": PerspMode.Vulkan,
    "WebGPU": PerspMode.WebGPU,
}


class PerspectiveWidget(QFrame):
    """A widget for editing fov/aspect/near/far and viewing the resulting perspective Mat4."""

    valueChanged = Signal(Mat4)

    def __init__(
        self,
        parent: QWidget | None = None,
        name: str = "",
        fov: float = 45.0,
        aspect: float = 1.333,
        near: float = 0.1,
        far: float = 100.0,
        show_mode: bool = False,
    ) -> None:
        """Initialize the widget.

        Args:
            parent: The parent widget.
            name: The name of the widget.
            fov: Initial field of view in degrees.
            aspect: Initial aspect ratio.
            near: Initial near clipping plane distance.
            far: Initial far clipping plane distance.
            show_mode: If True, show a combo box to choose the clip-space
                convention (OpenGL/Vulkan/WebGPU); otherwise mode is fixed
                to PerspMode.OpenGL (but can still be set programmatically).
        """
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._name = name
        self._mode = PerspMode.OpenGL
        self._matrix = Mat4()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)

        self._toggle_button = QToolButton(self)
        self._toggle_button.setText(self._name)
        self._toggle_button.setCheckable(True)
        self._toggle_button.setChecked(True)
        self._toggle_button.setStyleSheet("QToolButton { border: none; }")
        self._toggle_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self._toggle_button.setArrowType(Qt.ArrowType.DownArrow)
        self._toggle_button.clicked.connect(self.toggle_collapsed)

        self._content_widget = QWidget(self)
        content_layout = QVBoxLayout(self._content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self._fov_spinbox = self._create_row(
            content_layout, "Fov", fov, 1.0, 179.0, 1.0
        )
        self._aspect_spinbox = self._create_row(
            content_layout, "Aspect", aspect, 0.1, 4.0, 0.01
        )
        self._near_spinbox = self._create_row(
            content_layout, "Near", near, 0.01, 10.0, 0.01
        )
        self._far_spinbox = self._create_row(
            content_layout, "Far", far, 1.0, 1000.0, 1.0
        )

        if show_mode:
            self._mode_combo = QComboBox(self)
            for item in _MODE_NAMES:
                self._mode_combo.addItem(item)
            self._mode_combo.currentIndexChanged.connect(self._on_mode_index_changed)
            row = QHBoxLayout()
            row.addWidget(QLabel("Mode"))
            row.addWidget(self._mode_combo)
            content_layout.addLayout(row)

        main_layout.addWidget(self._toggle_button)
        main_layout.addWidget(self._content_widget)
        self._update_matrix()

    def _create_row(
        self,
        layout: QVBoxLayout,
        label: str,
        value: float,
        minimum: float,
        maximum: float,
        step: float,
    ) -> QDoubleSpinBox:
        """Create a labelled spinbox row and add it to the content layout.

        Args:
            layout: The layout to add the row to.
            label: The row's label text.
            value: The spinbox's initial value.
            minimum: The spinbox's minimum value.
            maximum: The spinbox's maximum value.
            step: The spinbox's single step.

        Returns:
            The created QDoubleSpinBox.
        """
        spinbox = QDoubleSpinBox()
        spinbox.setRange(minimum, maximum)
        spinbox.setSingleStep(step)
        spinbox.setDecimals(3)
        spinbox.setValue(value)
        spinbox.valueChanged.connect(self._update_matrix)
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        row.addWidget(spinbox)
        layout.addLayout(row)
        return spinbox

    def _on_mode_index_changed(self, index: int) -> None:
        """Update the mode from the combo box index and recompute the matrix.

        Args:
            index: The new combo box index.
        """
        self._mode = _MODE_BY_NAME[_MODE_NAMES[index]]
        self._update_matrix()

    def _update_matrix(self) -> None:
        """Recompute the perspective matrix from the current widget values."""
        self._matrix = perspective(
            self._fov_spinbox.value(),
            self._aspect_spinbox.value(),
            self._near_spinbox.value(),
            self._far_spinbox.value(),
            self._mode,
        )
        self.valueChanged.emit(self._matrix)

    def matrix(self) -> Mat4:
        """Return the current perspective matrix.

        Returns:
            The current Mat4.
        """
        return self._matrix

    def toggle_collapsed(self, checked: bool) -> None:
        """Toggle the visibility of the content widget.

        Args:
            checked: Whether the section should be expanded.
        """
        if checked:
            self._toggle_button.setArrowType(Qt.ArrowType.DownArrow)
            self._content_widget.setVisible(True)
        else:
            self._toggle_button.setArrowType(Qt.ArrowType.RightArrow)
            self._content_widget.setVisible(False)

    def get_fov(self) -> float:
        """Return the field of view in degrees."""
        return self._fov_spinbox.value()

    def set_fov(self, fov: float) -> None:
        """Set the field of view in degrees."""
        self._fov_spinbox.setValue(fov)

    def get_aspect(self) -> float:
        """Return the aspect ratio."""
        return self._aspect_spinbox.value()

    def set_aspect(self, aspect: float) -> None:
        """Set the aspect ratio."""
        self._aspect_spinbox.setValue(aspect)

    def get_near(self) -> float:
        """Return the near clipping plane distance."""
        return self._near_spinbox.value()

    def set_near(self, near: float) -> None:
        """Set the near clipping plane distance."""
        self._near_spinbox.setValue(near)

    def get_far(self) -> float:
        """Return the far clipping plane distance."""
        return self._far_spinbox.value()

    def set_far(self, far: float) -> None:
        """Set the far clipping plane distance."""
        self._far_spinbox.setValue(far)

    def get_mode(self) -> PerspMode:
        """Return the current clip-space convention."""
        return self._mode

    def set_mode(self, mode: PerspMode | int) -> None:
        """Set the clip-space convention.

        Args:
            mode: A PerspMode, or an index into the mode combo box order
                (OpenGL, Vulkan, WebGPU).
        """
        if isinstance(mode, int):
            mode = _MODE_BY_NAME[_MODE_NAMES[mode]]
        self._mode = mode
        if hasattr(self, "_mode_combo"):
            self._mode_combo.setCurrentIndex(_MODE_NAMES.index(mode.value))
        else:
            self._update_matrix()

    def get_name(self) -> str:
        """Return the widget name shown on the toggle button."""
        return self._name

    def set_name(self, name: str) -> None:
        """Set the widget name shown on the toggle button."""
        self._name = name
        self._toggle_button.setText(name)

    name = Property(str, get_name, set_name)
    fov = Property(float, get_fov, set_fov)
    aspect = Property(float, get_aspect, set_aspect)
    near = Property(float, get_near, set_near)
    far = Property(float, get_far, set_far)
    mode = Property(PerspMode, get_mode, set_mode)
