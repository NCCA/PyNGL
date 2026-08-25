"""QML-exposed model for editing a Vec2."""

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtQml import QmlElement

from ncca.ngl import Vec2

QML_IMPORT_NAME = "ncca.ngl.qml"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class Vec2Model(QObject):
    """Holds a Vec2 and exposes its components as QML properties."""

    valueChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the model with a zero Vec2.

        Args:
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._value = Vec2(0.0, 0.0)

    def get_x(self) -> float:
        """Return the x component.

        Returns:
            The current x value.
        """
        return float(self._value.x)

    def set_x(self, value: float) -> None:
        """Set the x component and emit valueChanged.

        Args:
            value: The new x value.
        """
        self._value.x = value
        self.valueChanged.emit()

    def get_y(self) -> float:
        """Return the y component.

        Returns:
            The current y value.
        """
        return float(self._value.y)

    def set_y(self, value: float) -> None:
        """Set the y component and emit valueChanged.

        Args:
            value: The new y value.
        """
        self._value.y = value
        self.valueChanged.emit()

    x = Property(float, get_x, set_x, notify=valueChanged)
    y = Property(float, get_y, set_y, notify=valueChanged)

    @Slot(result=Vec2)
    def get_value(self) -> Vec2:
        """Return the current Vec2 value.

        Returns:
            The current value.
        """
        return self._value

    @Slot(Vec2)
    def set_value(self, value: Vec2) -> None:
        """Replace the current value and emit valueChanged.

        Args:
            value: The new Vec2 value.
        """
        self._value = value
        self.valueChanged.emit()
