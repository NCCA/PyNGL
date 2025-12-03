from PySide6.QtCore import Property, QSignalBlocker, Qt, Signal, Slot
from PySide6.QtWidgets import QComboBox, QFrame, QLabel, QToolButton, QVBoxLayout, QWidget

from ncca.ngl import Mat4, Vec3, look_at

from .vec3widget import Vec3Widget


class LookAtWidget(QFrame):
    """A widget for displaying and editing a Transform object, with foldable sections."""

    valueChanged = Signal(Mat4)
    world_up = [Vec3(0, 1, 0), Vec3(1, 0, 0), Vec3(0, 0, 1)]

    def __init__(self, parent: QWidget | None = None, name: str = "", eye=Vec3(2, 2, 2), look=Vec3(0, 0, 0)) -> None:
        """
        Args:
            name: The name of the widget.
            parent: The parent widget.
        """
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._name = name
        self._view = Mat4()
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

        self._eye = Vec3Widget(self, "Eye", eye)
        self._look = Vec3Widget(self, "Look", look)
        self._up = QComboBox(self)
        for v in ["y-up", "x-up", "z-up"]:
            self._up.addItem(v)
        self._eye.valueChanged.connect(self._update_matrix)
        self._look.valueChanged.connect(self._update_matrix)
        self._up.currentIndexChanged.connect(self._update_matrix)
        content_layout.addWidget(self._eye)
        content_layout.addWidget(self._look)
        content_layout.addWidget(QLabel("World Up"))
        content_layout.addWidget(self._up)
        main_layout.addWidget(self._toggle_button)
        main_layout.addWidget(self._content_widget)

    def set_eye(self, eye):
        self._eye.set_value(eye)

    def set_look(self, look):
        self._look.set_value(look)

    def set_up(self, up):
        self._up.setCurrentIndex(up)

    def set_name(self, name):
        self._name = name
        self._toggle_button.setText(name)

    def get_name(self):
        return self._name.text()

    def get_eye(self):
        return self._eye.value

    def get_look(self):
        return self._look.value

    def get_up(self):
        return self.world_up[self._up.currentIndex()]

    def toggle_collapsed(self, checked: bool) -> None:
        """Toggles the visibility of the content widget."""
        if checked:
            self._toggle_button.setArrowType(Qt.ArrowType.DownArrow)
            self._content_widget.setVisible(True)
        else:
            self._toggle_button.setArrowType(Qt.ArrowType.RightArrow)
            self._content_widget.setVisible(False)

    def _update_matrix(self) -> None:
        """Updates the view matrix based on the widget values."""
        eye = self._eye.value
        look = self._look.value

        up = self.world_up[self._up.currentIndex()]

        self._view = look_at(eye, look, up)
        self.valueChanged.emit(self._view)

    def view(self) -> Mat4:
        """Returns the current view matrix."""
        return self._view

    name = Property(str, get_name, set_name)
    eye = Property(Vec3, get_eye, set_eye)
    look = Property(Vec3, get_look, set_look)
    up = Property(Vec3, get_up, set_up)
