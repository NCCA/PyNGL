"""QML-exposed model for editing a Vec3."""

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtQml import QmlElement

from ncca.ngl import Vec3

QML_IMPORT_NAME = "ncca.ngl.qml"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class Vec3Model(QObject):
    """Holds a Vec3 and exposes its components as QML properties."""

    valueChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the model with a zero Vec3.

        Args:
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._value = Vec3(0.0, 0.0, 0.0)

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

    def get_z(self) -> float:
        """Return the z component.

        Returns:
            The current z value.
        """
        return float(self._value.z)

    def set_z(self, value: float) -> None:
        """Set the z component and emit valueChanged.

        Args:
            value: The new z value.
        """
        self._value.z = value
        self.valueChanged.emit()

    x = Property(float, get_x, set_x, notify=valueChanged)
    y = Property(float, get_y, set_y, notify=valueChanged)
    z = Property(float, get_z, set_z, notify=valueChanged)

    @Slot(result=Vec3)
    def get_value(self) -> Vec3:
        """Return the current Vec3 value.

        Returns:
            The current value.
        """
        return self._value

    @Slot(Vec3)
    def set_value(self, value: Vec3) -> None:
        """Replace the current value and emit valueChanged.

        Args:
            value: The new Vec3 value.
        """
        self._value = value
        self.valueChanged.emit()
