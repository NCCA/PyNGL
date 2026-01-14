"""
Base class for all vector types providing common functionality and eliminating code duplication.

This module implements a generic base class that provides all common vector operations
while allowing dimension-specific behavior through abstract methods.
"""

import ctypes
import math
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Self, Tuple

import numpy as np

from .util import clamp, hash_combine


class VectorBase[T](ABC):
    """
    Base class for all vector types providing common functionality.

    This class implements all common vector operations using numpy for efficiency
    while maintaining the same API as the original vector classes.

    Attributes:
        DIMENSION: The dimension of the vector (2, 3, or 4)
        COMPONENT_NAMES: Tuple of component names ('x', 'y', 'z', 'w')
        DEFAULT_VALUES: Tuple of default values for each component
    """

    # Class attributes to be defined by subclasses
    DIMENSION: ClassVar[int]
    COMPONENT_NAMES: ClassVar[Tuple[str, ...]]
    DEFAULT_VALUES: ClassVar[Tuple[float, ...]]

    def __init__(self, *args: float, **kwargs: float) -> None:
        """Initialize vector with components."""
        if kwargs:
            self._init_from_kwargs(args, kwargs)
        else:
            self._init_from_args(args)

    def _init_from_kwargs(self, args: tuple[float, ...], kwargs: dict[str, float]) -> None:
        """Initialize vector from keyword arguments."""
        self._validate_component_count(len(args) + len(kwargs))

        values = list(self.DEFAULT_VALUES)
        self._set_positional_args(values, args)
        self._set_keyword_args(values, kwargs)

        self._data = np.array(values, dtype=np.float64)

    def _init_from_args(self, args: tuple[float, ...]) -> None:
        """Initialize vector from positional arguments only."""
        if not args:
            self._data = np.array(self.DEFAULT_VALUES, dtype=np.float64)
            return

        self._validate_component_count(len(args))

        values = list(self.DEFAULT_VALUES)
        self._set_positional_args(values, args)

        self._data = np.array(values, dtype=np.float64)

    def _validate_component_count(self, count: int) -> None:
        """Validate the number of components doesn't exceed dimension."""
        if count > self.DIMENSION:
            raise ValueError(f"{self.__class__.__name__} requires at most {self.DIMENSION} components")

    def _set_positional_args(self, values: list[float], args: tuple[float, ...]) -> None:
        """Set positional argument values."""
        for i, arg in enumerate(args):
            values[i] = float(arg)

    def _set_keyword_args(self, values: list[float], kwargs: dict[str, float]) -> None:
        """Set keyword argument values."""
        for key, value in kwargs.items():
            if key in self.COMPONENT_NAMES:
                idx = self.COMPONENT_NAMES.index(key)
                values[idx] = float(value)
            else:
                raise ValueError(f"Unknown component name: {key}")

    @classmethod
    def sizeof(cls) -> int:
        """Return the size of the vector in bytes (for OpenGL compatibility)."""
        return cls.DIMENSION * ctypes.sizeof(ctypes.c_float)

    def __iter__(self):
        """
        Make the vector class iterable.

        Yields:
            float: The components of the vector.
        """
        for i in range(self.DIMENSION):
            yield self._data[i]

    def __getitem__(self, index: int) -> float:
        """
        Get the component of the vector at the given index.

        Args:
            index (int): The index of the component.

        Returns:
            float: The value of the component at the given index.

        Raises:
            IndexError: If the index is out of range.
        """
        if index < 0 or index >= self.DIMENSION:
            valid_indices = ", ".join(str(i) for i in range(self.DIMENSION))
            raise IndexError(f"Index out of range. Valid indices are {valid_indices}.")
        return self._data[index]

    def __hash__(self) -> int:
        """
        Compute hash for use in sets and dictionaries.

        Returns:
            int: Hash value for the vector.
        """
        # Use 32-bit float element hashes, then combine
        seed = 0
        for v in self._data:
            # ensure 32-bit float semantics
            h = hash(float(np.float32(v)))
            seed = hash_combine(seed, h)
        return seed

    def copy(self) -> Self:
        """
        Create a copy of the vector.

        Returns:
            VectorBase: A new vector instance with the same values.
        """
        return self.__class__(*self._data)

    def __add__(self, rhs: Self) -> Self:
        """
        Vector addition a+b.

        Args:
            rhs (VectorBase): The right-hand side vector to add.

        Returns:
            VectorBase: A new vector that is the result of adding this vector and the rhs vector.
        """
        if not isinstance(rhs, self.__class__):
            raise ValueError(f"Can only add {self.__class__.__name__} to {self.__class__.__name__}")
        result = self.__class__()
        result._data = self._data + rhs._data
        return result

    def __iadd__(self, rhs: Self) -> Self:
        """
        Vector addition a+=b.

        Args:
            rhs (VectorBase): The right-hand side vector to add.

        Returns:
            VectorBase: Returns this vector after adding the rhs vector.
        """
        if not isinstance(rhs, self.__class__):
            raise ValueError(f"Can only add {self.__class__.__name__} to {self.__class__.__name__}")
        self._data += rhs._data
        return self

    def __sub__(self, rhs: Self) -> Self:
        """
        Vector subtraction a-b.

        Args:
            rhs (VectorBase): The right-hand side vector to subtract.

        Returns:
            VectorBase: A new vector that is the result of subtracting this vector and the rhs vector.
        """
        if not isinstance(rhs, self.__class__):
            raise ValueError(f"Can only subtract {self.__class__.__name__} from {self.__class__.__name__}")
        result = self.__class__()
        result._data = self._data - rhs._data
        return result

    def __isub__(self, rhs: Self) -> Self:
        """
        Vector subtraction a-=b.

        Args:
            rhs (VectorBase): The right-hand side vector to subtract.

        Returns:
            VectorBase: Returns this vector after subtracting the rhs vector.
        """
        if not isinstance(rhs, self.__class__):
            raise ValueError(f"Can only subtract {self.__class__.__name__} from {self.__class__.__name__}")
        self._data -= rhs._data
        return self

    def __eq__(self, rhs: Any) -> bool:
        """
        Vector comparison a==b using numpy.allclose.

        Args:
            rhs (VectorBase): The right-hand side vector to compare.

        Returns:
            bool: True if the vectors are close, False otherwise.
            NotImplemented: If the right-hand side is not a VectorBase.
        """
        if not isinstance(rhs, self.__class__):
            return NotImplemented
        return np.allclose(self._data, rhs._data)

    def __ne__(self, rhs: Any) -> bool:
        """
        Vector comparison a!=b using numpy.allclose.

        Args:
            rhs (VectorBase): The right-hand side vector to compare.

        Returns:
            bool: True if the vectors are not close, False otherwise.
            NotImplemented: If the right-hand side is not a VectorBase.
        """
        if not isinstance(rhs, self.__class__):
            return NotImplemented
        return not np.allclose(self._data, rhs._data)

    def __neg__(self) -> Self:
        """
        Negate a vector -a.

        Returns:
            VectorBase: The negated vector.
        """
        result = self.__class__()
        result._data = -self._data
        return result

    def __mul__(self, rhs: float | int) -> Self:
        """
        Piecewise scalar multiplication.

        Args:
            rhs (float): The scalar to multiply by.

        Returns:
            VectorBase: A new vector that is the result of multiplying this vector by the scalar.

        Raises:
            ValueError: If the right-hand side is not a float or int.
        """
        if isinstance(rhs, (float, int)):
            result = self.__class__()
            result._data = self._data * rhs
            return result
        else:
            raise ValueError(f"Can only do piecewise multiplication with a scalar, got {type(rhs)}")

    def __rmul__(self, rhs: float | int) -> Self:
        """
        Piecewise scalar multiplication (right operand).

        Args:
            rhs (float): The scalar to multiply by.

        Returns:
            VectorBase: A new vector that is the result of multiplying this vector by the scalar.
        """
        return self * rhs

    def __truediv__(self, rhs: float | int | Self) -> Self:
        """
        Piecewise scalar or vector division.

        Args:
            rhs (Union[float, int, VectorBase]): The scalar or vector to divide by.

        Returns:
            VectorBase: A new vector that is the result of division.

        Raises:
            ZeroDivisionError: If division by zero is attempted.
            ValueError: If the right-hand side is not a valid type.
        """
        if isinstance(rhs, (float, int)):
            if rhs == 0.0:
                raise ZeroDivisionError("division by zero")
            result = self.__class__()
            result._data = self._data / rhs
            return result
        elif isinstance(rhs, self.__class__):
            if np.any(np.isclose(rhs._data, 0.0)):
                raise ZeroDivisionError("division by zero")
            result = self.__class__()
            result._data = self._data / rhs._data
            return result
        else:
            raise ValueError(
                f"Can only do piecewise division with a scalar or {self.__class__.__name__}, got {type(rhs)}"
            )

    def dot(self, rhs: Self) -> float:
        """
        Dot product of two vectors a.b.

        Args:
            rhs (VectorBase): The right-hand side vector to dot product with.

        Returns:
            float: The dot product of the two vectors.
        """
        if not isinstance(rhs, self.__class__):
            raise ValueError(f"Can only compute dot product with {self.__class__.__name__}")
        return np.dot(self._data, rhs._data)

    def length(self) -> float:
        """
        Length of vector.

        Returns:
            float: The length of the vector.
        """
        return np.linalg.norm(self._data)

    def length_squared(self) -> float:
        """
        Length of vector squared (sometimes used to avoid the sqrt for performance).

        Returns:
            float: The length of the vector squared.
        """
        return np.dot(self._data, self._data)

    def inner(self, rhs: Self) -> float:
        """
        Inner product of two vectors a.b (alias for dot product).

        Args:
            rhs (VectorBase): The right-hand side vector to inner product with.

        Returns:
            float: The inner product of the two vectors.
        """
        return self.dot(rhs)

    def normalize(self) -> Self:
        """
        Normalize the vector to unit length.

        Returns:
            VectorBase: This vector after normalization.

        Raises:
            ZeroDivisionError: If the length of the vector is zero.
        """
        vector_length = self.length()
        if math.isclose(vector_length, 0.0):
            raise ZeroDivisionError(
                f"{self.__class__.__name__}.normalize: length is zero, most likely calling normalize on a zero vector"
            )
        self._data /= vector_length
        return self

    def null(self) -> None:
        """Set the vector to zero."""
        self._data[:] = 0.0

    def clamp(self, low: float, high: float) -> None:
        """
        Clamp the vector to a range.

        Args:
            low (float): The low end of the range.
            high (float): The high end of the range.
        """
        for i in range(self.DIMENSION):
            self._data[i] = clamp(self._data[i], low, high)

    def to_list(self) -> list:
        """
        Convert vector to list.

        Returns:
            list: List of vector components.
        """
        return self._data.tolist()

    def to_numpy(self) -> np.ndarray:
        """
        Convert vector to numpy array.

        Returns:
            np.ndarray: Copy of the vector as numpy array.
        """
        return self._data.copy()

    def to_tuple(self) -> tuple:
        """
        Convert vector to tuple.

        Returns:
            tuple: Tuple of vector components.
        """
        return tuple(self._data)

    # Abstract methods that must be implemented by subclasses
    @abstractmethod
    def cross(self, rhs: Self) -> Self | float:
        """
        Cross product of two vectors a x b.

        Args:
            rhs (VectorBase): The right-hand side vector to cross product with.

        Returns:
            Union[VectorBase, float]: The cross product (scalar for 2D, vector for 3D/4D).
        """
        pass

    @abstractmethod
    def reflect(self, n: Self) -> Self:
        """
        Reflect a vector about a normal.

        Args:
            n (VectorBase): The normal to reflect about.

        Returns:
            VectorBase: A new vector that is the result of reflecting this vector about the normal.
        """
        pass

    @abstractmethod
    def outer(self, rhs: Self) -> Any:
        """
        Outer product of two vectors a x b.

        Args:
            rhs (VectorBase): The right-hand side vector to outer product with.

        Returns:
            Any: A matrix that is the result of the outer product.
        """
        pass

    @abstractmethod
    def __matmul__(self, rhs: Any) -> Self:
        """
        Matrix multiplication Vector @ Matrix.

        Args:
            rhs (Any): The matrix to multiply by.

        Returns:
            VectorBase: A new vector that is the result of multiplying this vector by the matrix.
        """
        pass

    @abstractmethod
    def set(self, *args: float) -> None:
        """
        Set the components of the vector.

        Args:
            *args: Component values to set.

        Raises:
            ValueError: If wrong number of arguments is provided or they are not floats.
        """
        pass

    @abstractmethod
    def __repr__(self) -> str:
        """Object representation for debugging."""
        pass

    @abstractmethod
    def __str__(self) -> str:
        """String representation of the vector."""
        pass

    def __getattr__(self, name: str):
        """
        Handle access to non-existent attributes.

        Args:
            name (str): The name of the attribute.

        Raises:
            AttributeError: If the attribute does not exist.
        """
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Control attribute setting to prevent non-component attributes.

        Args:
            name: The attribute name to set
            value: The value to set

        Raises:
            AttributeError: If trying to set non-component attributes
        """
        # Allow setting internal _data
        if name == "_data":
            super().__setattr__(name, value)
        # Allow setting component properties (x, y, z, w) during initialization
        elif name in self.COMPONENT_NAMES:
            super().__setattr__(name, value)
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


def _create_properties(cls: type) -> None:
    """
    Dynamically add properties for vector components.

    Args:
        cls: The vector class to add properties to.
    """

    def make_property(index: int):
        def getter(self):
            return self._data[index]

        def setter(self, value):
            if not isinstance(value, (int, float, np.float32)):
                raise ValueError("need float or int")
            self._data[index] = float(value)

        return property(getter, setter)

    # Add properties for each component (x, y, z, w)
    for i, attr in enumerate(cls.COMPONENT_NAMES):
        setattr(cls, attr, make_property(i))
