"""Simple float only Vec2 class for 3D graphics, very similar to the pyngl ones.

NumPy-based implementation with VectorBase inheritance for code reuse.
"""

from typing import TYPE_CHECKING

import numpy as np

from .vector_base import VectorBase, _create_properties

if TYPE_CHECKING:
    from .mat2 import Mat2


class Vec2(VectorBase["Vec2"]):
    """A simple 2D vector class for graphics, using numpy for efficient operations.

    Attributes:
        x (float): The x-coordinate of the vector.
        y (float): The y-coordinate of the vector.
    """

    DIMENSION = 2
    COMPONENT_NAMES = ("x", "y")
    DEFAULT_VALUES = (0.0, 0.0)

    __slots__ = ["_data"]

    def cross(self, rhs: "Vec2") -> float:
        """Cross product of two vectors a x b (2D version returns scalar).

        Args:
            rhs (Vec2): The right-hand side vector to cross product with.

        Returns:
            float: 2D cross product (perpendicular dot product).
        """
        return self._data[0] * rhs._data[1] - self._data[1] * rhs._data[0]

    def reflected(self, n: "Vec2") -> "Vec2":
        """Return a new vector reflected about a normal.

        Args:
            n (Vec2): The normal to reflect about.

        Returns:
            Vec2: A new vector that is the result of reflecting this vector about the normal.
        """
        d = self.dot(n)
        # I - 2.0 * dot(N, I) * N
        return Vec2(
            self._data[0] - 2.0 * d * n._data[0], self._data[1] - 2.0 * d * n._data[1]
        )

    def outer(self, rhs: "Vec2") -> "Mat2":
        """Outer product of two vectors a x b.

        Args:
            rhs (Vec2): The right-hand side vector to outer product with.

        Returns:
            Mat2: A new 2x2 matrix that is the result of the outer product.
        """
        from .mat2 import Mat2

        result = Mat2()
        result._data = np.outer(self._data, rhs._data).astype(np.float32)
        return result

    def __matmul__(self, rhs: "Mat2") -> "Vec2":
        """Vec2 @ Mat2 matrix multiplication.

        Args:
            rhs (Mat2): The matrix to multiply by.

        Returns:
            Vec2: A new vector that is the result of multiplying this vector by the matrix.
        """
        return Vec2(
            self._data[0] * rhs._data[0, 0] + self._data[1] * rhs._data[1, 0],
            self._data[0] * rhs._data[0, 1] + self._data[1] * rhs._data[1, 1],
        )

    def set(self, *args: float) -> None:
        """Set the x,y values of the vector.

        Args:
            *args: Component values (x, y).

        Raises:
            ValueError: If wrong number of arguments or they are not floats.
        """
        if len(args) != 2:
            raise ValueError(f"Vec2.set requires 2 arguments, got {len(args)}")
        try:
            self._data[0] = float(args[0])
            self._data[1] = float(args[1])
        except ValueError:
            raise ValueError(f"Vec2.set {args=} all need to be float")


# Add properties for x, y components
_create_properties(Vec2)
