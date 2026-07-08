"""Shared base model for editable NxN matrix grids (Mat2/Mat3/Mat4)."""

from PySide6.QtCore import Property, QObject, Signal, Slot

from ncca.ngl.mat_base import MatrixBase, MatrixError


class MatGridModel(QObject):
    """Base QObject exposing an NxN MatrixBase value to QML.

    Not registered as a QML type directly; Mat2Model/Mat3Model/Mat4Model
    subclass it, setting the `mat_cls` and `size` class attributes.
    """

    valueChanged = Signal()
    statusMessageChanged = Signal()

    mat_cls: type[MatrixBase]
    size: int

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the model with an identity matrix.

        Args:
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._value = self.mat_cls.identity()
        self._status_message = ""

    @Slot(int, int, result=float)
    def get_cell(self, row: int, col: int) -> float:
        """Return the value at (row, col).

        Args:
            row: The row index.
            col: The column index.

        Returns:
            The cell's current value.
        """
        return float(self._value[row][col])

    @Slot(int, int, float)
    def set_cell(self, row: int, col: int, value: float) -> None:
        """Set the value at (row, col) and emit valueChanged.

        Args:
            row: The row index.
            col: The column index.
            value: The new cell value.
        """
        self._value[row][col] = value
        self.valueChanged.emit()

    def get_value(self) -> MatrixBase:
        """Return the current matrix value.

        Returns:
            The current matrix.
        """
        return self._value

    def set_value(self, value: MatrixBase) -> None:
        """Replace the current matrix value and emit valueChanged.

        Args:
            value: The new matrix value.
        """
        self._value = value
        self.valueChanged.emit()

    @Slot()
    def identity(self) -> None:
        """Reset the matrix to identity."""
        self.set_value(self.mat_cls.identity())

    @Slot()
    def zero(self) -> None:
        """Reset the matrix to all zeros."""
        self.set_value(self.mat_cls.zero())

    @Slot()
    def transpose(self) -> None:
        """Replace the matrix with its transpose."""
        self.set_value(self._value.transposed())

    @Slot()
    def inverse(self) -> None:
        """Replace the matrix with its inverse, or set a status message if singular."""
        try:
            inverted = self._value.inverse()
        except MatrixError:
            self._status_message = "Matrix is singular"
            self.statusMessageChanged.emit()
            return
        self._status_message = ""
        self.statusMessageChanged.emit()
        self.set_value(inverted)

    def get_status_message(self) -> str:
        """Return the current status message.

        Returns:
            The status message, or an empty string if none.
        """
        return self._status_message

    statusMessage = Property(str, get_status_message, notify=statusMessageChanged)
