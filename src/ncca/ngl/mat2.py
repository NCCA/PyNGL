"""
Mat2 class with NumPy implementation
"""

import numpy as np

from .vec2 import Vec2


class Mat2Error(Exception):
    pass


class Mat2:
    __slots__ = ["m"]

    def __init__(self, m=None):
        """
        Initialize a 2x2 matrix.

        Args:
            m (list): A 2D list representing the matrix.
                        If not provided, an identity matrix is created.
        """
        if m is None:
            self.m = np.eye(2, dtype=np.float64)
        elif isinstance(m, list) and len(m) == 4 and not isinstance(m[0], list):
            # Flat list - reshape to 2x2
            self.m = np.array(m, dtype=np.float64).reshape(2, 2, order="C")
        else:
            # 2D list
            self.m = np.array(m, dtype=np.float64)

    @classmethod
    def from_list(cls, m: list[float]):
        """
        Initialize a 2x2 matrix from a flat list.

        Args:
            m (list[float]): A flat list representing the matrix.
        """
        return cls(m)

    def get_matrix(self) -> list[float]:
        """
        Get the current matrix representation as a flat list in column-major order.

        Returns:
            list[float]: A flat list of floats.
        """
        # Transpose then flatten for column-major order
        return self.m.T.flatten().tolist()

    def to_numpy(self):
        """
        Convert the current matrix to a NumPy array.

        Returns:
            np.ndarray: The matrix as a NumPy array.
        """
        return self.m.astype(np.float32)

    @classmethod
    def identity(cls) -> "Mat2":
        """
        Create an identity matrix.

        Returns:
            Mat2: A new identity Mat2 object.
        """
        return cls()

    def __matmul__(self, rhs):
        """
        Matrix multiplication or vector transformation with a 2D matrix.

        Args:
            rhs (Mat2 | Vec2): The right-hand side operand.
                                If Mat2, perform matrix multiplication.
                                If Vec2, transform the vector by the matrix.

        Returns:
            Mat2: Resulting matrix from matrix multiplication.
            Vec2: Transformed vector.

        Raises:
            ValueError: If rhs is neither a Mat2 nor Vec2 object.
        """
        if isinstance(rhs, Mat2):
            return Mat2(self.m @ rhs.m)
        elif isinstance(rhs, Vec2):
            vec = np.array([rhs.x, rhs.y], dtype=np.float64)
            res = self.m @ vec
            return Vec2(res[0], res[1])
        else:
            raise ValueError(f"Can only multiply by Mat2 or Vec2, not {type(rhs)}")

    def __str__(self) -> str:
        """
        String representation of the matrix.

        Returns:
            str: The string representation.
        """
        return f"Mat2({self.m[0].tolist()}, {self.m[1].tolist()})"

    def to_list(self):
        "convert matrix to list in column-major order"
        return self.m.T.flatten().tolist()

    def copy(self) -> "Mat2":
        """Create a copy of the matrix.

        Returns:
            A new Mat2 instance with the same values.
        """
        new_mat = Mat2()
        new_mat.m = self.m.copy()
        return new_mat
