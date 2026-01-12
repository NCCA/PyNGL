"""
Mat2 class with NumPy implementation
"""

import numpy as np

from .vec2 import Vec2


class Mat2Error(Exception):
    pass


class Mat2NotSquare(Exception):
    """If we try to construct from a non square (2x2) value or 4 elements this exception will be thrown"""

    pass


class Mat2:
    __slots__ = ["m"]

    def __init__(self):
        """
        Initialize a 2x2 matrix.


        """
        self.m = np.eye(2, dtype=np.float64)

    @classmethod
    def from_list(cls, lst):
        "class method to create mat2 from list"
        v = Mat2()
        if isinstance(lst, list) and len(lst) == 2 and all(isinstance(row, list) for row in lst):
            # 2D list
            if all(len(row) == 2 for row in lst):
                v.m = np.array(lst, dtype=np.float64)
                return v
            elif any(len(row) != 2 for row in lst):
                raise Mat2NotSquare
        elif isinstance(lst, list) and len(lst) == 4:
            # flat list - reshape to 2x2 in row-major order
            v.m = np.array(lst, dtype=np.float64).reshape(2, 2, order="C")
            return v
        else:
            raise Mat2NotSquare

    def get_matrix(self) -> list[float]:
        """
        Get the current matrix representation as a flat list in column-major order.

        Returns:
            list[float]: A flat list of floats.
        """
        return self.m.flatten("C").tolist()

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

    @classmethod
    def zero(cls):
        """class method to return a new zero matrix

        Returns
        -------
        Mat2
            new Mat2 matrix as all zeros

        """
        v = Mat2()
        v.m = np.zeros((2, 2), dtype=np.float64)
        return v

    def _mat_mul(self, rhs):
        "matrix mult for 3D OpenGL style graphics"
        result = Mat2()
        # Use numpy's @ operator which does standard matrix multiplication
        result.m = rhs.m @ self.m
        return result

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
            return self._mat_mul(rhs)
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
        return self.m.flatten("C").tolist()

    def copy(self) -> "Mat2":
        """Create a copy of the matrix.

        Returns:
            A new Mat2 instance with the same values.
        """
        new_mat = Mat2()
        new_mat.m = self.m.copy()
        return new_mat

    def __eq__(self, rhs):
        """Value-based equality for Mat2: compare underlying matrices numerically.
        Returns NotImplemented for non-Mat2 types so Python can try reflected comparisons
        or handle it appropriately.
        """
        if not isinstance(rhs, Mat2):
            return NotImplemented
        # self.m and other.m should be numpy arrays; compare with tolerance
        return bool(np.allclose(self.m, rhs.m, rtol=1e-8, atol=1e-12))

    def __ne__(self, rhs):
        """Value-based equality for Mat2: compare underlying matrices numerically.
        Returns NotImplemented for non-Mat2 types so Python can try reflected comparisons
        or handle it appropriately.
        """
        if not isinstance(rhs, Mat2):
            return NotImplemented
        # self.m and other.m should be numpy arrays; compare with tolerance
        return not bool(np.allclose(self.m, rhs.m, rtol=1e-8, atol=1e-12))
