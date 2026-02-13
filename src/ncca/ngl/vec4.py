"""
Simple Float only Vec4 class for 3D graphics, very similar to the pyngl ones
NumPy-based implementation with VectorBase inheritance for code reuse.
"""

import numpy as np

from .vector_base import VectorBase, _create_properties


class Vec4(VectorBase["Vec4"]):
    """
    A simple 4D vector class for graphics, using numpy for efficient operations.

    Attributes:
        x (float): The x-coordinate of the vector.
        y (float): The y-coordinate of the vector.
        z (float): The z-coordinate of the vector.
        w (float): The w-coordinate of the vector.
    """

    DIMENSION = 4
    COMPONENT_NAMES = ("x", "y", "z", "w")
    DEFAULT_VALUES = (0.0, 0.0, 0.0, 1.0)

    __slots__ = ["_data"]

    def cross(self, rhs: "Vec4") -> "Vec4":
        """
        Cross product of two vectors a x b (4D version uses first 3 components).

        Args:
            rhs (Vec4): The right-hand side vector to cross product with.

        Returns:
            Vec4: A new vector that is the result of the cross product.
        """
        result = Vec4()
        # Cross product only makes sense for 3D vectors, use first 3 components
        result._data[:3] = np.cross(self._data[:3], rhs._data[:3])
        result._data[3] = 0.0
        return result

    def reflect(self, n: "Vec4") -> "Vec4":
        """
        Reflect a vector about a normal.

        Args:
            n (Vec4): The normal to reflect about.

        Returns:
            Vec4: A new vector that is the result of reflecting this vector about the normal.
        """
        d = self.dot(n)
        # I - 2.0 * dot(N, I) * N
        result = Vec4()
        result._data = self._data - 2.0 * d * n._data
        return result

    def outer(self, rhs: "Vec4"):
        """
        Outer product of two vectors a x b.

        Args:
            rhs (Vec4): The right-hand side vector to outer product with.

        Returns:
            Mat4: A new 4x4 matrix that is the result of the outer product.
        """
        from .mat4 import Mat4

        result = Mat4()
        result.m = np.outer(self._data, rhs._data).astype(np.float64)
        return result

    def __matmul__(self, rhs):
        """
        Vec4 @ Mat4 matrix multiplication.

        Args:
            rhs (Mat4): The matrix to multiply by.

        Returns:
            Vec4: A new vector that is the result of multiplying this vector by the matrix.
        """
        return Vec4(*self._data @ rhs.m)

    def set(self, *args: float) -> None:
        """
        Set the x,y,z,w values of the vector.

        Args:
            *args: Component values (x, y, z, w). w defaults to 1.0 if not provided.

        Raises:
            ValueError: If wrong number of arguments or they are not floats.
        """
        if len(args) == 3:
            # Allow (x, y, z) with default w=1.0 for backward compatibility
            args = args + (1.0,)
        elif len(args) != 4:
            raise ValueError(f"Vec4.set requires 3 or 4 arguments, got {len(args)}")

        try:
            for i in range(4):
                self._data[i] = float(args[i])
        except ValueError:
            raise ValueError(f"Vec4.set {args=} all need to be float")

    def __repr__(self) -> str:
        """Object representation for debugging."""
        return f"Vec4 [{self._data[0]},{self._data[1]},{self._data[2]},{self._data[3]}]"

    def __str__(self) -> str:
        """String representation of the vector."""

        # Format numbers without decimal point if they're whole numbers
        def fmt(val):
            return str(int(val)) if val == int(val) else str(val)

        return f"[{fmt(self._data[0])},{fmt(self._data[1])},{fmt(self._data[2])},{fmt(self._data[3])}]"


# Add properties for x, y, z, w components
_create_properties(Vec4)
