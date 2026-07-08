"""QML-exposed model combining position/rotation/scale into a Transform matrix."""

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtQml import QmlElement

from ncca.ngl import Mat4, Transform

from .vec3_model import Vec3Model

QML_IMPORT_NAME = "ncca.ngl.qml"
QML_IMPORT_MAJOR_VERSION = 1

ROTATION_ORDERS = ["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"]


@QmlElement
class TransformModel(QObject):
    """Combines position/rotation/scale Vec3Models into a Mat4 transform."""

    valueChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize child position/rotation/scale models and compute the matrix.

        Args:
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._position = Vec3Model(self)
        self._rotation = Vec3Model(self)
        self._scale = Vec3Model(self)
        self._scale.x = 1.0
        self._scale.y = 1.0
        self._scale.z = 1.0
        self._rotation_order_index = 0
        self._matrix = Mat4()
        self._position.valueChanged.connect(self._update_matrix)
        self._rotation.valueChanged.connect(self._update_matrix)
        self._scale.valueChanged.connect(self._update_matrix)
        self._update_matrix()

    def get_position(self) -> Vec3Model:
        """Return the position child model.

        Returns:
            The position Vec3Model.
        """
        return self._position

    def get_rotation(self) -> Vec3Model:
        """Return the rotation child model.

        Returns:
            The rotation Vec3Model.
        """
        return self._rotation

    def get_scale(self) -> Vec3Model:
        """Return the scale child model.

        Returns:
            The scale Vec3Model.
        """
        return self._scale

    position = Property(QObject, get_position, constant=True)
    rotation = Property(QObject, get_rotation, constant=True)
    scale = Property(QObject, get_scale, constant=True)

    def get_rotation_order_index(self) -> int:
        """Return the index into ROTATION_ORDERS currently in use.

        Returns:
            The current rotation order index.
        """
        return self._rotation_order_index

    def set_rotation_order_index(self, index: int) -> None:
        """Set the rotation order by index and recompute the matrix.

        Args:
            index: An index into ROTATION_ORDERS.
        """
        self._rotation_order_index = index
        self._update_matrix()

    rotationOrderIndex = Property(
        int, get_rotation_order_index, set_rotation_order_index, notify=valueChanged
    )

    @Slot(result=list)
    def rotation_orders(self) -> list:
        """Return the ordered list of valid rotation order strings.

        Returns:
            The rotation order names, in combo-box order.
        """
        return list(ROTATION_ORDERS)

    def _update_matrix(self) -> None:
        """Recompute the transform matrix from the current child values."""
        position = self._position.get_value()
        rotation = self._rotation.get_value()
        scale = self._scale.get_value()

        tx = Transform()
        tx.set_order(ROTATION_ORDERS[self._rotation_order_index])
        tx.set_position(position.x, position.y, position.z)
        tx.set_rotation(rotation.x, rotation.y, rotation.z)
        tx.set_scale(scale.x, scale.y, scale.z)
        self._matrix = tx.matrix()
        self.valueChanged.emit()

    @Slot(result=Mat4)
    def get_matrix(self) -> Mat4:
        """Return the current transform matrix.

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
