"""
Simple Mat4 class which can be used with the Vec4 class
NumPy-based implementation
"""

import copy
import math

import numpy as np


class Mat4Error(Exception):
    """An exception class for Mat4"""

    pass


class Mat4NotSquare(Exception):
    """Make sure we have 4x4"""

    pass


class Mat4:
    __slots__ = ["m"]

    def __init__(self):
        "construct to identity matrix"
        self.m = np.eye(4, dtype=np.float64)

    def get_matrix(self):
        "return matrix elements as list ideal for OpenGL etc"
        # Flatten in row-major order (C-style)
        return self.m.flatten("C").tolist()

    def to_numpy(self):
        "return matrix as a numpy array ideal for WebGPU etc"
        return self.m.astype(np.float32)

    @classmethod
    def identity(cls):
        "class method to return a new identity matrix"
        v = Mat4()
        return v

    @classmethod
    def zero(cls):
        "class method to return a zero matrix"
        v = Mat4()
        v.m = np.zeros((4, 4), dtype=np.float64)
        return v

    @classmethod
    def from_list(cls, lst):
        "class method to create mat4 from list"
        v = Mat4()
        if isinstance(lst, list) and len(lst) == 4 and all(isinstance(row, list) for row in lst):
            # 2D list
            if all(len(row) == 4 for row in lst):
                v.m = np.array(lst, dtype=np.float64)
                return v
            elif any(len(row) != 4 for row in lst):
                raise Mat4NotSquare
        elif isinstance(lst, list) and len(lst) == 16:
            # flat list - reshape to 4x4 in row-major order
            v.m = np.array(lst, dtype=np.float64).reshape(4, 4, order="C")
            return v
        else:
            raise Mat4NotSquare

    def _is_square(self) -> bool:
        "ensure matrix is square"
        return self.m.shape == (4, 4)

    def to_list(self):
        "convert matrix to list"
        return self.m.flatten("C").tolist()

    def copy(self) -> "Mat4":
        """Create a copy of the matrix.

        Returns:
            A new Mat4 instance with the same values.
        """
        new_mat = Mat4()
        new_mat.m = self.m.copy()
        return new_mat

    def transpose(self):
        "transpose this matrix"
        self.m = self.m.T

    def get_transpose(self):
        "return a new matrix as the transpose of ourself"
        m = Mat4()
        m.m = self.m.T.copy()
        return m

    @classmethod
    def scale(cls, x: float, y: float, z: float):
        """return a scale matrix resetting to identity first

        Parameters
        ----------
            x : float
                uniform scale in the x axis
            y : float
                uniform scale in the y axis
            z : float
                uniform scale in the z axis

        .. highlight:: python
        .. code-block:: python

            scale=Mat4.scale(2.0,1.0,3.0)

        Returns
        -------
            Mat3
                matrix with diagonals set to the scale

        """
        a = Mat4()
        a.m[0, 0] = x
        a.m[1, 1] = y
        a.m[2, 2] = z
        return a

    @classmethod
    def translate(cls, x: float, y: float, z: float):
        "return a new matrix as translation"
        a = Mat4()
        a.m[3, 0] = x
        a.m[3, 1] = y
        a.m[3, 2] = z
        return a

    @classmethod
    def rotate_x(cls, angle):
        """return a rotation around the X axis by angle degrees

        Parameters
        ----------
            angle : float
                angle in degrees

        .. highlight:: python
        .. code-block:: python

            rotate_x=Mat3.rotate_x(90.0)

        Returns
        -------
            Mat3
                matrix with rotation set to the angle

        """
        a = Mat4()
        beta = math.radians(angle)
        sr = math.sin(beta)
        cr = math.cos(beta)
        a.m[1, 1] = cr
        a.m[1, 2] = sr
        a.m[2, 1] = -sr
        a.m[2, 2] = cr
        return a

    @classmethod
    def rotate_y(cls, angle):
        "return a rotation around the Y axis by angle degrees"
        a = Mat4()
        beta = math.radians(angle)
        sr = math.sin(beta)
        cr = math.cos(beta)
        a.m[0, 0] = cr
        a.m[0, 2] = -sr
        a.m[2, 0] = sr
        a.m[2, 2] = cr
        return a

    @classmethod
    def rotate_z(cls, angle):
        "return a rotation around the Z axis by angle degrees"
        a = Mat4()
        beta = math.radians(angle)
        sr = math.sin(beta)
        cr = math.cos(beta)
        a.m[0, 0] = cr
        a.m[0, 1] = sr
        a.m[1, 0] = -sr
        a.m[1, 1] = cr
        return a

    def __getitem__(self, idx):
        "access array elements"
        return self.m[idx].tolist()

    def __setitem__(self, idx, item):
        "set items"
        self.m[idx] = item

    def __mul__(self, rhs):
        """Multiply matrix by scalar

        Parameters
        __________
            rhs : float int
                multiply each matrix element by rhs

        raises : Mat4Error
            if rhs is not a number
        """
        if isinstance(rhs, (int, float)):
            result = Mat4()
            result.m = self.m * rhs
            return result
        raise Mat4Error

    def _mat_mul(self, rhs):
        "matrix mult for 3D OpenGL style graphics"
        result = Mat4()
        # Use numpy's @ operator which does standard matrix multiplication
        result.m = rhs.m @ self.m
        return result

    def __matmul__(self, rhs):
        from .vec4 import Vec4

        "multiply matrix by another matrix or vector"
        if isinstance(rhs, Mat4):
            return self._mat_mul(rhs)
        elif isinstance(rhs, Vec4):
            # Vector transformation
            vec = np.array([rhs.x, rhs.y, rhs.z, rhs.w], dtype=np.float64)
            res = self.m @ vec
            return Vec4(res[0], res[1], res[2], res[3])
        else:
            raise Mat4Error

    def __str__(self):
        rows = [self.m[i].tolist() for i in range(4)]
        return f"[{rows[0]}\n{rows[1]}\n{rows[2]}\n{rows[3]}]"

    def __add__(self, rhs):
        "piecewise addition of elements"
        result = Mat4()
        result.m = self.m + rhs.m
        return result

    def __iadd__(self, rhs):
        "piecewise addition of elements to this"
        result = Mat4()
        result.m = self.m + rhs.m
        return result

    def __sub__(self, rhs):
        "piecewise subtraction of elements"
        result = Mat4()
        result.m = self.m - rhs.m
        return result

    def __isub__(self, rhs):
        "piecewise subtraction of elements to this"
        result = Mat4()
        result.m = self.m - rhs.m
        return result

    def determinant(self):
        "determinant of matrix"
        return np.linalg.det(self.m)

    def inverse(self):
        "Inverse of matrix raise MatrixError if not calculable"
        try:
            result = Mat4()
            result.m = np.linalg.inv(self.m)
            return result
        except np.linalg.LinAlgError:
            raise Mat4Error

    def __repr__(self) -> str:
        rows = [self.m[i].tolist() for i in range(4)]
        return f"Mat4({rows})"
