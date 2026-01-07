"""
Simple Float only Vec4 class for 3D graphics, very similar to the pyngl ones
NumPy-based implementation
"""

import ctypes
import math

import numpy as np

from .log import logger
from .util import hash_combine


class Vec4:
    __slots__ = ["_data"]
    "by using slots we fix our class attributes"

    def __init__(self, x=0.0, y=0.0, z=0.0, w=1.0):
        """simple ctor"""
        self._data = np.array([x, y, z, w], dtype=np.float64)

    @classmethod
    def sizeof(cls):
        return 4 * ctypes.sizeof(ctypes.c_float)

    def _validate_and_set(self, v, name):
        """
        check if v is a float or int
        Args:
            v (number): The value to check.
        Raises:
            ValueError: If v is not a float or int.
        """
        if not isinstance(v, (int, float, np.float32)):
            raise ValueError("need float or int")
        else:
            setattr(self, name, v)

    def __iter__(self):
        """
        Make the Vec4 class iterable.
        Yields:
            float: The x, y, z, and w components of the vector.
        """
        yield self.x
        yield self.y
        yield self.z
        yield self.w

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
        return Vec4(self.x, self.y, self.z, self.w)

    def __hash__(self):
        # Use 32-bit float element hashes, then combine
        seed = 0
        for v in self._data:
            # ensure 32-bit float semantics
            h = hash(float(np.float32(v)))
            seed = hash_combine(seed, h)
        return seed

    def __add__(self, rhs):
        "return a+b vector addition"
        r = Vec4()
        r._data = self._data + rhs._data
        return r

    def __iadd__(self, rhs):
        "return a+=b vector addition"
        self._data += rhs._data
        return self

    def __sub__(self, rhs):
        "return a-b vector subtraction"
        r = Vec4()
        r._data = self._data - rhs._data
        return r

    def __isub__(self, rhs):
        "return a-=b vector subtraction"
        self._data -= rhs._data
        return self

    def set(self, x, y, z, w=1.0):
        "set from x,y,z,w will convert to float an raise value error if problem"
        try:
            self._data[0] = float(x)
            self._data[1] = float(y)
            self._data[2] = float(z)
            self._data[3] = float(w)
        except ValueError:
            logger.warning("need float values")
            raise

    def dot(self, rhs):
        return np.dot(self._data, rhs._data)

    def length(self):
        "length of vector"
        return np.linalg.norm(self._data)

    def length_squared(self):
        "square length of vector"
        return np.dot(self._data, self._data)

    def normalize(self):
        "normalize this vector"
        length = self.length()
        if length == 0.0:
            raise ZeroDivisionError("cannot normalize the zero vector")
        self._data /= length
        return self

    def __eq__(self, rhs):
        "test a==b using math.isclose"
        if not isinstance(rhs, Vec4):
            return NotImplemented
        return np.allclose(self._data, rhs._data)

    def __neq__(self, rhs):
        "test a!=b using math.isclose"
        if not isinstance(rhs, Vec4):
            return NotImplemented
        return not np.allclose(self._data, rhs._data)

    def __neg__(self):
        self._data = -self._data
        return self

    def __mul__(self, rhs):
        if isinstance(rhs, (float, int)):
            "Vec4 * scalar multiplication"
            r = Vec4()
            r._data = self._data * rhs
            return r
        else:
            raise ValueError

    def __rmul__(self, rhs):
        return self * rhs

    def __truediv__(self, rhs):
        if isinstance(rhs, (float, int)):
            if rhs == 0.0:
                raise ZeroDivisionError("division by zero")
            r = Vec4()
            r._data = self._data / rhs
            return r
        elif isinstance(rhs, Vec4):
            if np.any(rhs._data == 0.0):
                raise ZeroDivisionError("division by zero")
            r = Vec4()
            r._data = self._data / rhs._data
            return r
        else:
            raise ValueError(f"can only do piecewise division with a scalar {rhs=}")

    def __matmul__(self, rhs):
        "Vec4 @ Mat4 matrix multiplication"
        return Vec4(
            self.x * rhs.m[0, 0] + self.y * rhs.m[1, 0] + self.z * rhs.m[2, 0] + self.w * rhs.m[3, 0],
            self.x * rhs.m[0, 1] + self.y * rhs.m[1, 1] + self.z * rhs.m[2, 1] + self.w * rhs.m[3, 1],
            self.x * rhs.m[0, 2] + self.y * rhs.m[1, 2] + self.z * rhs.m[2, 2] + self.w * rhs.m[3, 2],
            self.x * rhs.m[0, 3] + self.y * rhs.m[1, 3] + self.z * rhs.m[2, 3] + self.w * rhs.m[3, 3],
        )

    def __repr__(self):
        "repr for debugging purposes"
        return f"Vec4 [{self.x},{self.y},{self.z},{self.w}]"

    def __str__(self):
        "print out the vector as a string"

        # Format numbers without decimal point if they're whole numbers
        def fmt(val):
            return str(int(val)) if val == int(val) else str(val)

        return f"[{fmt(self.x)},{fmt(self.y)},{fmt(self.z)},{fmt(self.w)}]"

    def to_list(self):
        return self._data.tolist()

    def to_numpy(self):
        return self._data.copy()


# Helper function to create properties
def _create_property(index):
    def getter(self):
        return self._data[index]

    def setter(self, value):
        if not isinstance(value, (int, float, np.float32)):
            raise ValueError("need float or int")
        self._data[index] = value

    return property(getter, setter)


# Dynamically add properties for x, y, z, w
for i, attr in enumerate(["x", "y", "z", "w"]):
    setattr(Vec4, attr, _create_property(i))
