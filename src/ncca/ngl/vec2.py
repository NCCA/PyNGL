"""
Simple float only Vec2 class for 3D graphics, very similar to the pyngl ones
NumPy-based implementation
"""

import ctypes
import math

import numpy as np

from .util import clamp, hash_combine


class Vec2:
    """
    A simple 2D vector class for graphics, using numpy for efficient operations.
    Attributes:
        x (float): The x-coordinate of the vector.
        y (float): The y-coordinate of the vector.
    """

    __slots__ = ["_data"]

    def __init__(self, x=0.0, y=0.0):
        """
        Initializes a new instance of the Vec2 class.

        Args:
            x (float, optional): The x-coordinate of the vector. Defaults to 0.0.
            y (float, optional): The y-coordinate of the vector. Defaults to 0.0.
        """
        self._data = np.array([x, y], dtype=np.float64)

    @classmethod
    def sizeof(cls):
        return 2 * ctypes.sizeof(ctypes.c_float)

    def __iter__(self):
        """
        Make the Vec2 class iterable.
        Yields:
            float: The x and y components of the vector.
        """
        yield self.x
        yield self.y

    def __hash__(self):
        # Use 32-bit float element hashes, then combine
        seed = 0
        for v in self._data:
            # ensure 32-bit float semantics
            h = hash(float(np.float32(v)))
            seed = hash_combine(seed, h)
        return seed

    def copy(self) -> "Vec2":
        """
        Create a copy of the vector.
        Returns:
            Vec2: A new instance of Vec2 with the same x and y values.
        """
        return Vec2(self.x, self.y)

    def __getitem__(self, index):
        """
        Get the component of the vector at the given index.
        Args:
            index (int): The index of the component (0 for x, 1 for y).
        Returns:
            float: The value of the component at the given index.
        Raises:
            IndexError: If the index is out of range.
        """
        if index < 0 or index > 1:
            raise IndexError("Index out of range. Valid indices are 0, 1,")
        return self._data[index]

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

    def __add__(self, rhs):
        """
        vector addition a+b

        Args:
            rhs (Vec2): The right-hand side vector to add.
        Returns:
            Vec2: A new vector that is the result of adding this vector and the rhs vector.
        """
        r = Vec2()
        r._data = self._data + rhs._data
        return r

    def __iadd__(self, rhs):
        """
        vector addition a+=b

        Args:
            rhs (Vec2): The right-hand side vector to add.
        Returns:
            Vec2: returns this vector after adding the rhs vector.
        """
        self._data += rhs._data
        return self

    def __sub__(self, rhs):
        """
        vector subtraction a-b

        Args:
            rhs (Vec2): The right-hand side vector to add.
        Returns:
            Vec2: A new vector that is the result of subtracting this vector and the rhs vector.
        """
        r = Vec2()
        r._data = self._data - rhs._data
        return r

    def __isub__(self, rhs):
        """
        vector subtraction a-=b

        Args:
            rhs (Vec2): The right-hand side vector to add.
        Returns:
            Vec2: returns this vector after subtracting the rhs vector.
        """
        self._data -= rhs._data
        return self

    def __eq__(self, rhs):
        """
        vector comparison a==b using math.isclose not we only compare to 6 decimal places
        Args:
            rhs (Vec2): The right-hand side vector to compare.
        Returns:
            bool: True if the vectors are close, False otherwise.
            NotImplemented: If the right-hand side is not a Vec2.
        """
        if not isinstance(rhs, Vec2):
            return NotImplemented
        return np.allclose(self._data, rhs._data)

    def __neq__(self, rhs):
        """
        vector comparison a!=b using math.isclose not we only compare to 6 decimal places
        Args:
            rhs (Vec2): The right-hand side vector to compare.
        Returns:
            bool: True if the vectors are not close, False otherwise.
            NotImplemented: If the right-hand side is not a Vec2.
        """
        if not isinstance(rhs, Vec2):
            return NotImplemented
        return not np.allclose(self._data, rhs._data)

    def __neg__(self):
        """
        negate a vector -a
        """
        self._data = -self._data
        return self

    def set(self, x, y):
        """
        set the x,y values of the vector
        Args:
            x (float): The x-coordinate of the vector.
            y (float): The y-coordinate of the vector.
        Raises :
            ValueError: if x,y are not float
        """
        try:
            self._data[0] = float(x)
            self._data[1] = float(y)
        except ValueError:
            raise ValueError(f"Vec2.set {x=} {y=} all need to be float")

    def dot(self, rhs):
        """
        dot product of two vectors a.b
        Args:
            rhs (Vec2): The right-hand side vector to dot product with.
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

    def inner(self, rhs):
        """
        inner product of two vectors a.b
        Args:
            rhs (Vec2): The right-hand side vector to inner product with.
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
            rhs (Vec2): The right-hand side vector to cross product with.
        Returns:
            float : 2D cross product or perpendicular dot product.
        """
        return self.x * rhs.y - self.y * rhs.x

    def normalize(self):
        """
        normalize the vector to unit length
        Returns:
            Vec2: A new vector that is the result of normalizing this vector.
        Raises:
            ZeroDivisionError: If the length of the vector is zero.
        """
        vector_length = self.length()
        if math.isclose(vector_length, 0.0):
            raise ZeroDivisionError(
                f"Vec2.normalize {vector_length} length is zero most likely calling normalize on a zero vector"
            )
        self._data /= vector_length
        return self

    def reflect(self, n):
        """
        reflect a vector about a normal
        Args:
            n (Vec2): The normal to reflect about.
        Returns:
            Vec2: A new vector that is the result of reflecting this vector about the normal.
        """
        d = self.dot(n)
        #  I - 2.0 * dot(N, I) * N
        return Vec2(self.x - 2.0 * d * n.x, self.y - 2.0 * d * n.y)

    def clamp(self, low, high):
        """
        clamp the vector to a range
        Args:
            low (float): The low end of the range.
            high (float): The high end of the range.
        """
        self._data[0] = clamp(self.x, low, high)
        self._data[1] = clamp(self.y, low, high)

    def __repr__(self):
        "object representation for debugging"
        return f"Vec2 [{self.x},{self.y}]"

    def __truediv__(self, rhs):
        if isinstance(rhs, (float, int)):
            if math.isclose(rhs, 0.0):
                raise ZeroDivisionError("division by zero")
            r = Vec2()
            r._data = self._data / rhs
            return r
        elif isinstance(rhs, Vec2):
            if np.any(np.isclose(rhs._data, 0.0)):
                raise ZeroDivisionError("division by zero")
            r = Vec2()
            r._data = self._data / rhs._data
            return r
        else:
            raise ValueError(f"can only do piecewise division with a scalar {rhs=}")

    def __str__(self):
        "object representation for debugging"
        return f"[{self.x},{self.y}]"

    def __mul__(self, rhs):
        """
        piecewise scalar multiplication
        Args:
            rhs (float): The scalar to multiply by.
        Returns:
            Vec2: A new vector that is the result of multiplying this vector by the scalar.
        Raises:
            ValueError: If the right-hand side is not a float.
        """
        if isinstance(rhs, (float, int)):
            r = Vec2()
            r._data = self._data * rhs
            return r
        else:
            raise ValueError(f"can only do piecewise multiplication with a scalar {rhs=}")

    def __rmul__(self, rhs):
        """
        piecewise scalar multiplication
        Args:
            rhs (float): The scalar to multiply by.
        Returns:
            Vec2: A new vector that is the result of multiplying this vector by the scalar.
        Raises:
            ValueError: If the right-hand side is not a float.
        """
        return self * rhs

    def __matmul__(self, rhs):
        """
        "Vec2 @ Mat2 matrix multiplication"
        Args:
            rhs (Mat2): The matrix to multiply by.
        Returns:
            Vec2: A new vector that is the result of multiplying this vector by the matrix.
        """
        return Vec2(
            self.x * rhs.m[0, 0] + self.y * rhs.m[1, 0],
            self.x * rhs.m[0, 1] + self.y * rhs.m[1, 1],
        )

    def to_list(self):
        return self._data.tolist()

    def to_numpy(self):
        return np.array(self._data)


# Helper function to create properties
def _create_property(index):
    def getter(self):
        return self._data[index]

    def setter(self, value):
        if not isinstance(value, (int, float, np.float32)):
            raise ValueError("need float or int")
        self._data[index] = value

    return property(getter, setter)


# Dynamically add properties for x, y
for i, attr in enumerate(["x", "y"]):
    setattr(Vec2, attr, _create_property(i))
