"""QML-exposed model combining fov/aspect/near/far into a perspective matrix."""

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtQml import QmlElement

from ncca.ngl import Mat4, PerspMode, perspective

QML_IMPORT_NAME = "ncca.ngl.qml"
QML_IMPORT_MAJOR_VERSION = 1

MODE_NAMES = ["OpenGL", "Vulkan", "WebGPU"]
MODES = [PerspMode.OpenGL, PerspMode.Vulkan, PerspMode.WebGPU]


@QmlElement
class PerspectiveModel(QObject):
    """Combines fov/aspect/near/far and a clip-space mode into a perspective Mat4."""

    valueChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the model with default projection parameters.

        Args:
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._fov = 45.0
        self._aspect = 1.333
        self._near = 0.1
        self._far = 100.0
        self._mode_index = 0
        self._matrix = Mat4()
        self._update_matrix()

    def get_fov(self) -> float:
        """Return the field of view in degrees.

        Returns:
            The current fov value.
        """
        return self._fov

    def set_fov(self, value: float) -> None:
        """Set the field of view and recompute the matrix.

        Args:
            value: The new fov value in degrees.
        """
        self._fov = value
        self._update_matrix()

    fov = Property(float, get_fov, set_fov, notify=valueChanged)

    def get_aspect(self) -> float:
        """Return the aspect ratio.

        Returns:
            The current aspect ratio.
        """
        return self._aspect

    def set_aspect(self, value: float) -> None:
        """Set the aspect ratio and recompute the matrix.

        Args:
            value: The new aspect ratio.
        """
        self._aspect = value
        self._update_matrix()

    aspect = Property(float, get_aspect, set_aspect, notify=valueChanged)

    def get_near(self) -> float:
        """Return the near clipping plane distance.

        Returns:
            The current near value.
        """
        return self._near

    def set_near(self, value: float) -> None:
        """Set the near clipping plane distance and recompute the matrix.

        Args:
            value: The new near value.
        """
        self._near = value
        self._update_matrix()

    near = Property(float, get_near, set_near, notify=valueChanged)

    def get_far(self) -> float:
        """Return the far clipping plane distance.

        Returns:
            The current far value.
        """
        return self._far

    def set_far(self, value: float) -> None:
        """Set the far clipping plane distance and recompute the matrix.

        Args:
            value: The new far value.
        """
        self._far = value
        self._update_matrix()

    far = Property(float, get_far, set_far, notify=valueChanged)

    def get_mode_index(self) -> int:
        """Return the index into MODE_NAMES currently in use.

        Returns:
            The current mode index.
        """
        return self._mode_index

    def set_mode_index(self, index: int) -> None:
        """Set the clip-space mode by index and recompute the matrix.

        Args:
            index: An index into MODE_NAMES/MODES.
        """
        self._mode_index = index
        self._update_matrix()

    modeIndex = Property(int, get_mode_index, set_mode_index, notify=valueChanged)

    @Slot(result=list)
    def mode_names(self) -> list:
        """Return the ordered list of clip-space mode display names.

        Returns:
            The mode names, in combo-box order.
        """
        return list(MODE_NAMES)

    def _update_matrix(self) -> None:
        """Recompute the perspective matrix from the current property values."""
        self._matrix = perspective(
            self._fov, self._aspect, self._near, self._far, MODES[self._mode_index]
        )
        self.valueChanged.emit()

    @Slot(result=Mat4)
    def get_matrix(self) -> Mat4:
        """Return the current perspective matrix.

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
