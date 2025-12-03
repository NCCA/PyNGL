from PySide6.QtCore import Property, QSignalBlocker, Signal
from PySide6.QtWidgets import QDoubleSpinBox, QFrame, QHBoxLayout, QLabel, QWidget

from ncca.ngl import Vec2


class Vec2Widget(QFrame):
    """A widget for displaying and editing a Vec3 object."""

    valueChanged = Signal(Vec2)
    xValueChanged = Signal(float)
    yValueChanged = Signal(float)

    def __init__(self, parent: QWidget | None = None, name: str = "", value: Vec2 = Vec2(0.0, 0.0)) -> None:
        """
        Args:
            name: The name of the widget.
            value: The initial value of the widget.
            parent: The parent widget.
        """
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._value = value
        self._name = name
        layout = QHBoxLayout()

        self.x_spinbox = self._create_spinbox(self._value.x)
        self.y_spinbox = self._create_spinbox(self._value.y)

        self._label = QLabel(self._name)
        layout.addWidget(self._label)
        layout.addWidget(self.x_spinbox)
        layout.addWidget(self.y_spinbox)
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
        spinbox.setRange(-5.0, 5.0)
        spinbox.setSingleStep(0.01)
        spinbox.valueChanged.connect(self._on_value_changed)
        return spinbox

    def get_value(self) -> Vec2:
        """
        Returns:
            The current value of the widget.
        """
        return self._value

    def _on_value_changed(self, value: float) -> None:
        """This slot is called when the value of a spinbox changes.

        Args:
            value: The new value of the spinbox.
        """
        sender = self.sender()
        if sender == self.x_spinbox:
            self._value.x = value
            self.xValueChanged.emit(value)
        elif sender == self.y_spinbox:
            self._value.y = value
            self.yValueChanged.emit(value)
        # emit the Vec2 value changed signal
        self.valueChanged.emit(self._value)

    def set_value(self, value: Vec2) -> None:
        """Sets the value of the widget.

        Args:
            value: The new value of the widget.
        """
        with QSignalBlocker(self.x_spinbox), QSignalBlocker(self.y_spinbox), QSignalBlocker(self.z_spinbox):
            self.x_spinbox.setValue(value.x)
            self.y_spinbox.setValue(value.y)
        self._value = value
        self.valueChanged.emit(self._value)

    def get_name(self) -> str:
        """
        Returns:
            The name of the widget.
        """
        return self._name

    def set_range(self, min_val: float, max_val: float) -> None:
        """Sets the range for all spinboxes.

        Args:
            min_val: The minimum value.
            max_val: The maximum value.
        """
        for spinbox in (self.x_spinbox, self.y_spinbox):
            spinbox.setRange(min_val, max_val)

    def set_x_range(self, min_val: float, max_val: float) -> None:
        """Sets the range for the x spinbox.

        Args:
            min_val: The minimum value.
            max_val: The maximum value.
        """
        self.x_spinbox.setRange(min_val, max_val)

    def set_y_range(self, min_val: float, max_val: float) -> None:
        """Sets the range for the y spinbox.

        Args:
            min_val: The minimum value.
            max_val: The maximum value.
        """
        self.y_spinbox.setRange(min_val, max_val)

    def set_single_step(self, step: float) -> None:
        """Sets the single step for all spinboxes.

        Args:
            step: The single step value.
        """
        for spinbox in (self.x_spinbox, self.y_spinbox):
            spinbox.setSingleStep(step)

    def set_name(self, name: str) -> None:
        """Sets the name of the widget.

        Args:
            name: The new name of the widget.
        """
        self._name = name
        self._label.setText(name)

    value = Property(Vec2, get_value, set_value)
    name = Property(str, get_name, set_name)
