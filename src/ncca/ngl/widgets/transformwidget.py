from PySide6.QtCore import Property, QSignalBlocker, Qt, Signal
from PySide6.QtWidgets import QComboBox, QFrame, QLabel, QToolButton, QVBoxLayout, QWidget

from ncca.ngl import Mat4, Transform, TransformRotationOrder, Vec3

from .vec3widget import Vec3Widget


class TransformWidget(QFrame):
    """A widget for displaying and editing a Transform object, with foldable sections."""

    valueChanged = Signal(Mat4)
    _rotation_order = ["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"]

    def __init__(self, parent: QWidget | None = None, name: str = "") -> None:
        """
        Args:
            name: The name of the widget.
            parent: The parent widget.
        """
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._name = name

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)

        self._toggle_button = QToolButton(self)
        self._toggle_button.setText(self._name)
        self._toggle_button.setCheckable(True)
        self._toggle_button.setChecked(True)
        self._toggle_button.setStyleSheet("QToolButton { border: none; }")
        self._toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._toggle_button.setArrowType(Qt.ArrowType.DownArrow)
        self._toggle_button.clicked.connect(self.toggle_collapsed)

        self._content_widget = QWidget(self)
        content_layout = QVBoxLayout(self._content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self._position = Vec3Widget(self, "Position", Vec3(0.0, 0.0, 0.0))
        self._position.set_range(-20, 20)
        self._rotation = Vec3Widget(self, "Rotation", Vec3(0.0, 0.0, 0.0))
        self._rotation.set_range(-360, 360)
        self._scale = Vec3Widget(self, "Scale", Vec3(1.0, 1.0, 1.0))
        self._scale.set_range(-20, 20)

        self._rot_order = QComboBox(self)
        for v in self._rotation_order:
            self._rot_order.addItem(v)
        self._position.valueChanged.connect(self._update_matrix)
        self._rotation.valueChanged.connect(self._update_matrix)
        self._scale.valueChanged.connect(self._update_matrix)
        self._rot_order.currentIndexChanged.connect(self._update_matrix)
        content_layout.addWidget(self._position)
        content_layout.addWidget(self._rotation)
        content_layout.addWidget(self._scale)
        content_layout.addWidget(QLabel("Rotation Order"))
        content_layout.addWidget(self._rot_order)
        main_layout.addWidget(self._toggle_button)
        main_layout.addWidget(self._content_widget)

    def toggle_collapsed(self, checked: bool) -> None:
        """Toggles the visibility of the content widget."""
        if checked:
            self._toggle_button.setArrowType(Qt.ArrowType.DownArrow)
            self._content_widget.setVisible(True)
        else:
            self._toggle_button.setArrowType(Qt.ArrowType.RightArrow)
            self._content_widget.setVisible(False)

    def _update_matrix(self) -> None:
        """Updates the transformation matrix based on the widget values."""
        position = self._position.get_value()
        rotation = self._rotation.get_value()
        scale = self._scale.get_value()

        tx = Transform()
        tx.set_order(self._rot_order.currentText())
        tx.set_position(position.x, position.y, position.z)
        tx.set_rotation(rotation.x, rotation.y, rotation.z)
        tx.set_scale(scale.x, scale.y, scale.z)
        print(tx.get_matrix())
        self.valueChanged.emit(tx.get_matrix())

    def name(self) -> str:
        """
        Returns:
            The name of the widget.
        """
        return self._name

    def set_name(self, name: str) -> None:
        """Sets the name of the widget.

        Args:
            name: The new name of the widget.
        """
        self._name = name
        self._toggle_button.setText(name)

    name = Property(str, name, set_name)
