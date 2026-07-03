"""
Simple float only Vec3 class for 3D graphics, very similar to the pyngl ones
NumPy-based implementation with VectorBase inheritance for code reuse.
"""

import numpy as np

from .vector_base import VectorBase, _create_properties


class Vec3(VectorBase["Vec3"]):
    """
    A simple 3D vector class for 3D graphics, using numpy for efficient operations.

    Attributes:
        x (float): The x-coordinate of the vector.
        y (float): The y-coordinate of the vector.
        z (float): The z-coordinate of the vector.
    """

    DIMENSION = 3
    COMPONENT_NAMES = ("x", "y", "z")
    DEFAULT_VALUES = (0.0, 0.0, 0.0)

    __slots__ = ["_data"]

    def cross(self, rhs: "Vec3") -> "Vec3":
        """
        Cross product of two vectors a x b.

        Args:
            rhs (Vec3): The right-hand side vector to cross product with.

        Returns:
            Vec3: A new vector that is the result of the cross product.
        """
        result = Vec3()
        result._data = np.cross(self._data, rhs._data)
        return result

    def reflected(self, n: "Vec3") -> "Vec3":
        """
        Return a new vector reflected about a normal.

        Args:
            n (Vec3): The normal to reflect about.

        Returns:
            Vec3: A new vector that is the result of reflecting this vector about the normal.
        """
        d = self.dot(n)
        # I - 2.0 * dot(N, I) * N
        result = Vec3()
        result._data = self._data - 2.0 * d * n._data
        return result

    def outer(self, rhs: "Vec3"):
        """
        Outer product of two vectors a x b.

        Args:
            rhs (Vec3): The right-hand side vector to outer product with.

        Returns:
            Mat3: A new 3x3 matrix that is the result of the outer product.
        """
        from .mat3 import Mat3

        result = Mat3()
        result._data = np.outer(self._data, rhs._data).astype(np.float32)
        return result

    def __matmul__(self, rhs):
        """
        Vec3 @ Mat3 matrix multiplication.

        Args:
            rhs (Mat3): The matrix to multiply by.

        Returns:
            Vec3: A new vector that is the result of multiplying this vector by the matrix.
        """
        result = Vec3()
        result._data = rhs._data.T @ self._data  # More efficient
        return result

    def set(self, *args: float) -> None:
        """
        Set the x,y,z values of the vector.

        Args:
            *args: Component values (x, y, z).

        Raises:
            ValueError: If wrong number of arguments or they are not floats.
        """
        if len(args) != 3:
            raise ValueError(f"Vec3.set requires 3 arguments, got {len(args)}")
        try:
            self._data[0] = float(args[0])
            self._data[1] = float(args[1])
            self._data[2] = float(args[2])
        except ValueError:
            raise ValueError(f"Vec3.set {args=} all need to be float")


# Add properties for x, y, z components
_create_properties(Vec3)
