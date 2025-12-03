from PySide6.QtCore import Property, QSignalBlocker, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from ncca.ngl import Vec3


class RGBColourWidget(QFrame):
    """A widget for displaying and editing a Vec3 object."""

    colourChanged = Signal(Vec3)
    rValueChanged = Signal(float)
    gValueChanged = Signal(float)
    bValueChanged = Signal(float)

    def __init__(
        self, parent: QWidget | None = None, name: str = "", r: float = 1.0, g: float = 1.0, b: float = 1.0
    ) -> None:
        """
        Args:
            name: The name of the widget.
            r: The initial red component of the colour.
            g: The initial green component of the colour.
            b: The initial blue component of the colour.
            parent: The parent widget.
        """
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._colour = Vec3(r, g, b)
        self._name = name
        layout = QHBoxLayout()

        self.r_spinbox = self._create_spinbox(self._colour.x)
        self.g_spinbox = self._create_spinbox(self._colour.y)
        self.b_spinbox = self._create_spinbox(self._colour.z)

        self._label = QLabel(self._name)
        self._color_button = QPushButton()
        self._color_button.setFixedSize(20, 20)
        self._color_button.clicked.connect(self._show_color_dialog)
        self._update_button_color()

        layout.addWidget(self._label)
        layout.addWidget(self.r_spinbox)
        layout.addWidget(self.g_spinbox)
        layout.addWidget(self.b_spinbox)
        layout.addWidget(self._color_button)
        self.setLayout(layout)

    def _create_spinbox(self, value: float) -> QDoubleSpinBox:
        """Helper method to create and configure a QDoubleSpinBox.

        Args:
            value: The initial value of the spinbox.

        Returns:
            A configured QDoubleSpinBox.
        """
        spinbox = QDoubleSpinBox()
        spinbox.setValue(value)
        spinbox.setRange(0.0, 1.0)
        spinbox.setSingleStep(0.01)
        spinbox.valueChanged.connect(self._on_value_changed)
        return spinbox

    def colour(self) -> Vec3:
        """
        Returns:
            The current value of the widget.
        """
        return self._colour

    def _on_value_changed(self, value: float) -> None:
        """This slot is called when the value of a spinbox changes.

        Args:
            value: The new value of the spinbox.
        """
        sender = self.sender()
        if sender == self.r_spinbox:
            self._colour.x = value
            self.rValueChanged.emit(value)
        elif sender == self.g_spinbox:
            self._colour.y = value
            self.gValueChanged.emit(value)
        elif sender == self.b_spinbox:
            self._colour.z = value
            self.bValueChanged.emit(value)
        # emit the Vec3 value changed signal
        self.colourChanged.emit(self._colour)
        self._update_button_color()

    def set_colour(self, value: Vec3) -> None:
        """Sets the value of the widget.

        Args:
            value: The new value of the widget.
        """
        with QSignalBlocker(self.r_spinbox), QSignalBlocker(self.g_spinbox), QSignalBlocker(self.b_spinbox):
            self.r_spinbox.setValue(value.x)
            self.g_spinbox.setValue(value.y)
            self.b_spinbox.setValue(value.z)
        self._colour = value
        self.colourChanged.emit(self._colour)
        self._update_button_color()

    def _update_button_color(self) -> None:
        """Updates the background color of the color button."""
        color = QColor.fromRgbF(self._colour.x, self._colour.y, self._colour.z)
        self._color_button.setStyleSheet(f"background-color: {color.name()}")

    def _show_color_dialog(self) -> None:
        """Shows a QColorDialog to select a new color."""
        current_color = QColor.fromRgbF(self._colour.x, self._colour.y, self._colour.z)
        color = QColorDialog.getColor(current_color, self, "Select Color")
        if color.isValid():
            new_colour = Vec3(color.redF(), color.greenF(), color.blueF())
            self.set_colour(new_colour)

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
        self._label.setText(name)

    value = Property(Vec3, colour, set_colour)
    name = Property(str, name, set_name)
