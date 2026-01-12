"""
Simple Float only Vec4 class for 3D graphics, very similar to the pyngl ones
NumPy-based implementation
"""

import ctypes
import math

import numpy as np

from .log import logger
from .util import clamp, hash_combine


class Vec4:
    """
    A simple 4D vector class for graphics, using numpy for efficient operations.
    Attributes:
        x (float): The x-coordinate of the vector.
        y (float): The y-coordinate of the vector.
        z (float): The z-coordinate of the vector.
        w (float): The w-coordinate of the vector.
    """

    __slots__ = ["_data"]

    def __init__(self, x=0.0, y=0.0, z=0.0, w=1.0):
        """
        Initializes a new instance of the Vec4 class.

        Args:
            x (float, optional): The x-coordinate of the vector. Defaults to 0.0.
            y (float, optional): The y-coordinate of the vector. Defaults to 0.0.
            z (float, optional): The z-coordinate of the vector. Defaults to 0.0.
            w (float, optional): The w-coordinate of the vector. Defaults to 1.0.
        """
        self._data = np.array([x, y, z, w], dtype=np.float64)

    @classmethod
    def sizeof(cls):
        return 4 * ctypes.sizeof(ctypes.c_float)

    def __iter__(self):
        """
        Make the Vec4 class iterable.
        Yields:
            float: The x, y, z, and w components of the vector.
        """
        yield self._data[0]
        yield self._data[1]
        yield self._data[2]
        yield self._data[3]

    def __getitem__(self, index):
        """
        Get the component of the vector at the given index.
        Args:
            index (int): The index of the component (0 for x, 1 for y, 2 for z, 3 for w).
        Returns:
            float: The value of the component at the given index.
        Raises:
            IndexError: If the index is out of range.
        """
        if index < 0 or index > 3:
            raise IndexError("Index out of range. Valid indices are 0, 1, 2, and 3.")
        return self._data[index]

    def copy(self) -> "Vec4":
        """
        Create a copy of the vector.
        Returns:
            Vec4: A new Vec4 instance with the same values.
        """
        return Vec4(self._data[0], self._data[1], self._data[2], self._data[3])

    def __hash__(self):
        # Use 32-bit float element hashes, then combine
        seed = 0
        for v in self._data:
            # ensure 32-bit float semantics
            h = hash(float(np.float32(v)))
            seed = hash_combine(seed, h)
        return seed

    def __add__(self, rhs):
        """
        vector addition a+b

        Args:
            rhs (Vec4): The right-hand side vector to add.
        Returns:
            Vec4: A new vector that is the result of adding this vector and the rhs vector.
        """
        r = Vec4()
        r._data = self._data + rhs._data
        return r

    def __iadd__(self, rhs):
        """
        vector addition a+=b

        Args:
            rhs (Vec4): The right-hand side vector to add.
        Returns:
            Vec4: returns this vector after adding the rhs vector.
        """
        self._data += rhs._data
        return self

    def __sub__(self, rhs):
        """
        vector subtraction a-b

        Args:
            rhs (Vec4): The right-hand side vector to subtract.
        Returns:
            Vec4: A new vector that is the result of subtracting this vector and the rhs vector.
        """
        r = Vec4()
        r._data = self._data - rhs._data
        return r

    def __isub__(self, rhs):
        """
        vector subtraction a-=b

        Args:
            rhs (Vec4): The right-hand side vector to subtract.
        Returns:
            Vec4: returns this vector after subtracting the rhs vector.
        """
        self._data -= rhs._data
        return self

    def set(self, x, y, z, w=1.0):
        """
        set the x,y,z,w values of the vector
        Args:
            x (float): The x-coordinate of the vector.
            y (float): The y-coordinate of the vector.
            z (float): The z-coordinate of the vector.
            w (float): The w-coordinate of the vector.
        Raises :
            ValueError: if x,y,z,w are not float
        """
        try:
            self._data[0] = float(x)
            self._data[1] = float(y)
            self._data[2] = float(z)
            self._data[3] = float(w)
        except ValueError:
            raise ValueError(f"Vec4.set {x=} {y=} {z=} {w=} all need to be float")

    def dot(self, rhs):
        """
        dot product of two vectors a.b
        Args:
            rhs (Vec4): The right-hand side vector to dot product with.
        """
        return np.dot(self._data, rhs._data)

    def length(self):
        """
        length of vector
        Returns:
            float: The length of the vector.
        """
        return np.linalg.norm(self._data)

    def length_squared(self):
        """
        length of vector squared sometimes used to avoid the sqrt for performance
        Returns:
            float: The length of the vector squared
        """
        return np.dot(self._data, self._data)

    def normalize(self):
        """
        normalize the vector to unit length
        Returns:
            Vec4: A new vector that is the result of normalizing this vector.
        Raises:
            ZeroDivisionError: If the length of the vector is zero.
        """
        vector_length = self.length()
        if math.isclose(vector_length, 0.0):
            raise ZeroDivisionError(
                f"Vec4.normalize {vector_length} length is zero most likely calling normalize on a zero vector"
            )
        self._data /= vector_length
        return self

    def __eq__(self, rhs):
        """
        vector comparison a==b using math.isclose not we only compare to 6 decimal places
        Args:
            rhs (Vec4): The right-hand side vector to compare.
        Returns:
            bool: True if the vectors are close, False otherwise.
            NotImplemented: If the right-hand side is not a Vec4.
        """
        if not isinstance(rhs, Vec4):
            return NotImplemented
        return np.allclose(self._data, rhs._data)

    def __ne__(self, rhs):
        """
        vector comparison a!=b using math.isclose not we only compare to 6 decimal places
        Args:
            rhs (Vec4): The right-hand side vector to compare.
        Returns:
            bool: True if the vectors are not close, False otherwise.
            NotImplemented: If the right-hand side is not a Vec4.
        """
        if not isinstance(rhs, Vec4):
            return NotImplemented
        return not np.allclose(self._data, rhs._data)

    def __neg__(self):
        """
        negate a vector -a
        """
        self._data = -self._data
        return self

    def __mul__(self, rhs):
        """
        piecewise scalar multiplication
        Args:
            rhs (float): The scalar to multiply by.
        Returns:
            Vec4: A new vector that is the result of multiplying this vector by the scalar.
        Raises:
            ValueError: If the right-hand side is not a float.
        """
        if isinstance(rhs, (float, int)):
            r = Vec4()
            r._data = self._data * rhs
            return r
        else:
            raise ValueError(
                f"can only do piecewise multiplication with a scalar {rhs=}"
            )

    def __rmul__(self, rhs):
        """
        piecewise scalar multiplication
        Args:
            rhs (float): The scalar to multiply by.
        Returns:
            Vec4: A new vector that is the result of multiplying this vector by the scalar.
        Raises:
            ValueError: If the right-hand side is not a float.
        """
        return self * rhs

    def __truediv__(self, rhs):
        if isinstance(rhs, (float, int)):
            if rhs == 0.0:
                raise ZeroDivisionError("division by zero")
            r = Vec4()
            r._data = self._data / rhs
            return r
        elif isinstance(rhs, Vec4):
            if np.any(np.isclose(rhs._data, 0.0)):
                raise ZeroDivisionError("division by zero")
            r = Vec4()
            r._data = self._data / rhs._data
            return r
        else:
            raise ValueError(f"can only do piecewise division with a scalar {rhs=}")

    def __matmul__(self, rhs):
        """
        "Vec4 @ Mat4 matrix multiplication"
        Args:
            rhs (Mat4): The matrix to multiply by.
        Returns:
            Vec4: A new vector that is the result of multiplying this vector by the matrix.
        """
        return Vec4(*self._data @ rhs.m)

    def __repr__(self):
        "object representation for debugging"
        return f"Vec4 [{self._data[0]},{self._data[1]},{self._data[2]},{self._data[3]}]"

    def __str__(self):
        "print out the vector as a string"

        # Format numbers without decimal point if they're whole numbers
        def fmt(val):
            return str(int(val)) if val == int(val) else str(val)

        return f"[{fmt(self._data[0])},{fmt(self._data[1])},{fmt(self._data[2])},{fmt(self._data[3])}]"

    def to_list(self):
        return self._data.tolist()

    def to_numpy(self):
        return self._data.copy()

    def outer(self, rhs):
        """
        outer product of two vectors a x b
        Args:
            rhs (Vec4): The right-hand side vector to outer product with.
        Returns:
            Mat4: A new 4x4 matrix that is the result of the outer product.
        """
        from .mat4 import Mat4

        result = Mat4()
        result.m = np.outer(self._data, rhs._data)
        return result

    def inner(self, rhs):
        """
        inner product of two vectors a.b
        Args:
            rhs (Vec4): The right-hand side vector to inner product with.
        Returns:
            float: The inner product of the two vectors.
        """
        return np.dot(self._data, rhs._data)

    def null(self):
        """
        set the vector to zero
        """
        self._data[:] = 0.0

    def cross(self, rhs):
        """
        cross product of two vectors a x b
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

    def reflect(self, n):
        """
        reflect a vector about a normal
        Args:
            n (Vec4): The normal to reflect about.
        Returns:
            Vec4: A new vector that is the result of reflecting this vector about the normal.
        """
        d = self.dot(n)
        #  I - 2.0 * dot(N, I) * N
        result = Vec4()
        result._data = self._data - 2.0 * d * n._data
        return result

    def clamp(self, low, high):
        """
        clamp the vector to a range
        Args:
            low (float): The low end of the range.
            high (float): The high end of the range.
        """
        self._data[0] = clamp(self._data[0], low, high)
        self._data[1] = clamp(self._data[1], low, high)
        self._data[2] = clamp(self._data[2], low, high)
        self._data[3] = clamp(self._data[3], low, high)


# Helper function to create properties
def _create_property(index):
    def getter(self):
        return self._data[index]

    def setter(self, value):
        if not isinstance(value, (int, float)):
            raise ValueError("need float or int")
        self._data[index] = value

    return property(getter, setter)


# Dynamically add properties for x, y, z, w
for i, attr in enumerate(["x", "y", "z", "w"]):
    setattr(Vec4, attr, _create_property(i))
