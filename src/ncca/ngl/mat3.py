"""
Simple Mat3 class which can be used with the Vec3 class. By default it will be set to the identity matrix
NumPy-based implementation
"""

import copy
import functools
import math
import operator

import numpy as np


class Mat3Error(Exception):
    """This exception will be raised if we have issues with matrix multiplication or other mathematical operations"""

    pass


class Mat3NotSquare(Exception):
    """If we try to construct from a non square (3x3) value or 9 elements this exception will be thrown"""

    pass


class Mat3:
    """Simple Mat3 class for basic affine transforms"""

    __slots__ = ["m"]
    """m : list
        the matrix values
    """

    def __init__(self):
        """construct to identity matrix"""
        self.m = np.eye(3, dtype=np.float64)

    def get_matrix(self):
        """return matrix elements as list ideal for OpenGL

        Returns
        -------
        list
           the 9 float elements of the matrix, ideal
           for OpenGL or Renderman consumption
        """
        return self.m.flatten("C").tolist()

    def to_numpy(self):
        "return matrix as a numpy array ideal for WebGPU etc"
        return self.m.astype(np.float32)

    @classmethod
    def identity(cls):
        """class method to return a new identity matrix

        Returns
        -------
        Mat3
            new Mat3 matrix as Identity

        """
        v = Mat3()
        return v

    @classmethod
    def zero(cls):
        """class method to return a new zero matrix

        Returns
        -------
        Mat3
            new Mat3 matrix as all zeros

        """
        v = Mat3()
        v.m = np.zeros((3, 3), dtype=np.float64)
        return v

    @classmethod
    def from_list(cls, lst):
        "class method to create mat3 from list"
        v = Mat3()
        if isinstance(lst, list) and len(lst) == 3 and all(isinstance(row, list) for row in lst):
            # 2D list
            if all(len(row) == 3 for row in lst):
                v.m = np.array(lst, dtype=np.float64)
                return v
            elif any(len(row) != 3 for row in lst):
                raise Mat3NotSquare
        elif isinstance(lst, list) and len(lst) == 9:
            # flat list - reshape to 3x3 in row-major order
            v.m = np.array(lst, dtype=np.float64).reshape(3, 3, order="C")
            return v
        else:
            raise Mat3NotSquare

    def transpose(self):
        """transpose this matrix"""
        self.m = self.m.T

    def get_transpose(self):
        "return a new matrix as the transpose of ourself"
        m = Mat3()
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

            scale=Mat3.scale(2.0,1.0,3.0)

        Returns
        -------
            Mat3
                matrix with diagonals set to the scale

        """
        a = Mat3()
        a.m[0, 0] = x
        a.m[1, 1] = y
        a.m[2, 2] = z
        return a

    @classmethod
    def rotate_x(cls, angle: float):
        """return a matrix as the rotation around the Cartesian X axis by angle degrees

        Parameters
        ----------

            angle : float
                the angle in degrees to rotate

        .. highlight:: python
        .. code-block:: python

            rotx=Mat3.rotateX(45.0)

        Returns
        -------
            Mat3
                rotation matrix
        """
        a = Mat3()
        beta = math.radians(angle)
        sr = math.sin(beta)
        cr = math.cos(beta)
        a.m[1, 1] = cr
        a.m[1, 2] = sr
        a.m[2, 1] = -sr
        a.m[2, 2] = cr
        return a

    @classmethod
    def rotate_y(cls, angle: float):
        """return a matrix as the rotation around the Cartesian Y axis by angle degrees

        Parameters
        ----------

            angle : float
                the angle in degrees to rotate

        .. highlight:: python
        .. code-block:: python

            roty=Mat3.rotateY(45.0)

        Returns
        -------
            Mat3
                rotation matrix
        """
        a = Mat3()
        beta = math.radians(angle)
        sr = math.sin(beta)
        cr = math.cos(beta)
        a.m[0, 0] = cr
        a.m[0, 2] = -sr
        a.m[2, 0] = sr
        a.m[2, 2] = cr
        return a

    @classmethod
    def rotate_z(cls, angle: float):
        """return a matrix as the rotation around the Cartesian Z axis by angle degrees

        Parameters
        ----------

            angle : float
                the angle in degrees to rotate

        .. highlight:: python
        .. code-block:: python

            rotz=Mat3.rotateZ(45.0)

        Returns
        -------
            Mat3
                rotation matrix
        """
        a = Mat3()
        beta = math.radians(angle)
        sr = math.sin(beta)
        cr = math.cos(beta)
        a.m[0, 0] = cr
        a.m[0, 1] = sr
        a.m[1, 0] = -sr
        a.m[1, 1] = cr
        return a

    def __getitem__(self, idx):
        """access array elements remember this is a list of lists [[3],[3],[3]]
        Parameters
        ----------
            idx : int
                the index into the list to get the sub list


        """
        return self.m[idx].tolist()

    def __setitem__(self, idx, item):
        """set array elements remember this is a list of lists [[3],[3],[3]]

        Parameters
        ----------
            idx : int
                the index into the list to set the sub list
        """
        self.m[idx] = item

    def __mul__(self, rhs):
        """Multiply matrix by scalar

        Parameters
        __________
            rhs : float int
                multiply each matrix element by rhs

        raises : Mat3Error
            if rhs is not a number
        """
        if isinstance(rhs, (int, float)):
            result = Mat3()
            result.m = self.m * rhs
            return result
        raise Mat3Error

    def _mat_mul(self, rhs):
        "matrix mult for 3D OpenGL style graphics"
        result = Mat3()
        # Use numpy's @ operator which does standard matrix multiplication
        result.m = rhs.m @ self.m
        return result

    def __matmul__(self, rhs):
        "multiply matrix by another matrix"
        from .vec3 import Vec3

        "multiply matrix by another matrix or vector"
        if isinstance(rhs, Mat3):
            return self._mat_mul(rhs)
        elif isinstance(rhs, Vec3):
            # Vector transformation
            vec = np.array([rhs.x, rhs.y, rhs.z], dtype=np.float64)
            res = self.m @ vec
            return Vec3(res[0], res[1], res[2])
        else:
            raise Mat3Error

    def __add__(self, rhs):
        "piecewise addition of elements"
        result = Mat3()
        result.m = self.m + rhs.m
        return result

    def __iadd__(self, rhs):
        "piecewise addition of elements to this"
        result = Mat3()
        result.m = self.m + rhs.m
        return result

    def __sub__(self, rhs):
        "piecewise subtraction of elements"
        result = Mat3()
        result.m = self.m - rhs.m
        return result

    def __isub__(self, rhs):
        "piecewise subtraction of elements to this"
        result = Mat3()
        result.m = self.m - rhs.m
        return result

    def determinant(self):
        "determinant of matrix"
        return np.linalg.det(self.m)

    def to_list(self):
        "convert matrix to list"
        # flatten to single array
        return self.m.flatten("C").tolist()

    def copy(self) -> "Mat3":
        """Create a copy of the matrix.

        Returns:
            A new Mat3 instance with the same values.
        """
        new_mat = Mat3()
        new_mat.m = copy.deepcopy(self.m)
        return new_mat

    def inverse(self):
        "Inverse of matrix raise MatrixError if not calculable"
        try:
            result = Mat3()
            result.m = np.linalg.inv(self.m)
            return result
        except np.linalg.LinAlgError:
            raise Mat3Error

    def __str__(self):
        rows = [self.m[i].tolist() for i in range(3)]
        return f"[{rows[0]}\n{rows[1]}\n{rows[2]}]"

    def __repr__(self):
        rows = [self.m[i].tolist() for i in range(3)]
        return f"Mat3({rows})"

    @classmethod
    def from_mat4(cls, mat4):
        """Create a Mat3 from a Mat4"""
        m = Mat3()
        m.m = mat4.m[:3, :3].copy()
        return m

    def __eq__(self, other):
        """Value-based equality for Mat3: compare underlying matrices numerically.

        Returns NotImplemented for non-Mat3 types so Python can try reflected comparisons
        or handle it appropriately.
        """
        if not isinstance(other, Mat3):
            raise NotImplementedError
        # self.m and other.m should be numpy arrays; compare with tolerance
        return np.allclose(self.m, other.m, rtol=1e-8, atol=1e-12)
