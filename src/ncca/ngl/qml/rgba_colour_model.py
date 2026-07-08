"""QML-exposed model for an RGBA colour (Vec4) with a hex swatch string."""

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtQml import QmlElement

from ncca.ngl import Vec4

QML_IMPORT_NAME = "ncca.ngl.qml"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class RGBAColourModel(QObject):
    """Holds an RGBA Vec4 colour and exposes r/g/b/a plus a hex swatch colour."""

    colourChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the model with opaque white (1, 1, 1, 1).

        Args:
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._colour = Vec4(1.0, 1.0, 1.0, 1.0)

    def get_r(self) -> float:
        """Return the red channel.

        Returns:
            The current red value.
        """
        return float(self._colour.x)

    def set_r(self, value: float) -> None:
        """Set the red channel and emit colourChanged.

        Args:
            value: The new red value.
        """
        self._colour.x = value
        self.colourChanged.emit()

    def get_g(self) -> float:
        """Return the green channel.

        Returns:
            The current green value.
        """
        return float(self._colour.y)

    def set_g(self, value: float) -> None:
        """Set the green channel and emit colourChanged.

        Args:
            value: The new green value.
        """
        self._colour.y = value
        self.colourChanged.emit()

    def get_b(self) -> float:
        """Return the blue channel.

        Returns:
            The current blue value.
        """
        return float(self._colour.z)

    def set_b(self, value: float) -> None:
        """Set the blue channel and emit colourChanged.

        Args:
            value: The new blue value.
        """
        self._colour.z = value
        self.colourChanged.emit()

    def get_a(self) -> float:
        """Return the alpha channel.

        Returns:
            The current alpha value.
        """
        return float(self._colour.w)

    def set_a(self, value: float) -> None:
        """Set the alpha channel and emit colourChanged.

        Args:
            value: The new alpha value.
        """
        self._colour.w = value
        self.colourChanged.emit()

    r = Property(float, get_r, set_r, notify=colourChanged)
    g = Property(float, get_g, set_g, notify=colourChanged)
    b = Property(float, get_b, set_b, notify=colourChanged)
    a = Property(float, get_a, set_a, notify=colourChanged)

    def get_hex(self) -> str:
        """Return the colour as a `#AARRGGBB` hex string.

        Returns:
            The hex colour string, including alpha.
        """
        colour = QColor.fromRgbF(
            self._colour.x, self._colour.y, self._colour.z, self._colour.w
        )
        return colour.name(QColor.NameFormat.HexArgb)

    hex = Property(str, get_hex, notify=colourChanged)

    @Slot(result=Vec4)
    def get_value(self) -> Vec4:
        """Return the current colour as a Vec4.

        Returns:
            The current colour.
        """
        return self._colour

    @Slot(Vec4)
    def set_value(self, value: Vec4) -> None:
        """Replace the current colour and emit colourChanged.

        Args:
            value: The new colour value.
        """
        self._colour = value
        self.colourChanged.emit()
