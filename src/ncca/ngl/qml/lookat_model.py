"""QML-exposed model combining eye/look/up into a look_at view matrix."""

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtQml import QmlElement

from ncca.ngl import Mat4, Vec3, look_at

from .vec3_model import Vec3Model

QML_IMPORT_NAME = "ncca.ngl.qml"
QML_IMPORT_MAJOR_VERSION = 1

WORLD_UP = [Vec3(0, 1, 0), Vec3(1, 0, 0), Vec3(0, 0, 1)]
WORLD_UP_NAMES = ["y-up", "x-up", "z-up"]


@QmlElement
class LookAtModel(QObject):
    """Combines eye/look Vec3Models and a world-up choice into a view Mat4."""

    valueChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize eye/look child models and compute the initial view matrix.

        Args:
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._eye = Vec3Model(self)
        self._eye.x = 2.0
        self._eye.y = 2.0
        self._eye.z = 2.0
        self._look = Vec3Model(self)
        self._up_index = 0
        self._matrix = Mat4()
        self._eye.valueChanged.connect(self._update_matrix)
        self._look.valueChanged.connect(self._update_matrix)
        self._update_matrix()

    def get_eye(self) -> Vec3Model:
        """Return the eye child model.

        Returns:
            The eye Vec3Model.
        """
        return self._eye

    def get_look(self) -> Vec3Model:
        """Return the look-at child model.

        Returns:
            The look Vec3Model.
        """
        return self._look

    eye = Property(QObject, get_eye, constant=True)
    look = Property(QObject, get_look, constant=True)

    def get_up_index(self) -> int:
        """Return the index into WORLD_UP currently in use.

        Returns:
            The current world-up index.
        """
        return self._up_index

    def set_up_index(self, index: int) -> None:
        """Set the world-up vector by index and recompute the matrix.

        Args:
            index: An index into WORLD_UP.
        """
        self._up_index = index
        self._update_matrix()

    upIndex = Property(int, get_up_index, set_up_index, notify=valueChanged)

    @Slot(result=list)
    def up_names(self) -> list:
        """Return the ordered list of world-up display names.

        Returns:
            The world-up names, in combo-box order.
        """
        return list(WORLD_UP_NAMES)

    def _update_matrix(self) -> None:
        """Recompute the view matrix from the current eye/look/up values."""
        eye = self._eye.get_value()
        look = self._look.get_value()
        up = WORLD_UP[self._up_index]
        self._matrix = look_at(eye, look, up)
        self.valueChanged.emit()

    @Slot(result=Mat4)
    def get_matrix(self) -> Mat4:
        """Return the current view matrix.

        Returns:
            The current Mat4.
        """
        return self._matrix

    matrix = Property(Mat4, get_matrix, notify=valueChanged)

    @Slot(result=str)
    def matrix_text(self) -> str:
        """Return the current matrix formatted as a readable multi-line string.

        Returns:
            The matrix formatted with 2 decimal places per cell.
        """
        rows = [
            " ".join(f"{self._matrix[r][c]:6.2f}" for c in range(4)) for r in range(4)
        ]
        return "\n".join(rows)
