"""Shared base class for square matrix types (Mat2, Mat3, Mat4).

All matrices are numpy float32 backed and follow the immutable-style API:
operations return new matrices; the only mutation is element assignment
via ``m[row][col] = value`` or ``m[row] = [...]``.
"""

import ctypes
from typing import Any, ClassVar, Self

import numpy as np


class MatrixError(Exception):
    """Raised for invalid matrix construction or operations."""


class MatrixBase:
    """Base class providing the common square-matrix API.

    Attributes:
        SIZE: The row/column count (2, 3 or 4), set by subclasses.
    """

    SIZE: ClassVar[int]
    __slots__ = ("_data",)

    def __init__(self, *args: float) -> None:
        """Construct an identity matrix, or from SIZE*SIZE row-major values.

        Args:
            *args: Either nothing (identity) or SIZE*SIZE floats row-major.

        Raises:
            MatrixError: If the wrong number of components is given.
        """
        n = self.SIZE
        if not args:
            self._data = np.eye(n, dtype=np.float32)
        elif len(args) == n * n:
            self._data = np.array(args, dtype=np.float32).reshape(n, n)
        else:
            raise MatrixError(
                f"{self.__class__.__name__} requires 0 or {n * n} components"
            )

    # -- factories ---------------------------------------------------------
    @classmethod
    def identity(cls) -> Self:
        """Return a new identity matrix."""
        return cls()

    @classmethod
    def zero(cls) -> Self:
        """Return a new all-zero matrix."""
        result = cls()
        result._data = np.zeros((cls.SIZE, cls.SIZE), dtype=np.float32)
        return result

    @classmethod
    def from_list(cls, lst: list) -> Self:
        """Create a matrix from a nested or flat row-major list.

        Args:
            lst: Either SIZE lists of SIZE floats, or a flat list of
                SIZE*SIZE floats.

        Raises:
            MatrixError: If the shape is wrong.
        """
        n = cls.SIZE
        result = cls()
        if (
            isinstance(lst, list)
            and len(lst) == n
            and all(isinstance(row, list) and len(row) == n for row in lst)
        ):
            result._data = np.array(lst, dtype=np.float32)
            return result
        if isinstance(lst, list) and len(lst) == n * n:
            result._data = np.array(lst, dtype=np.float32).reshape(n, n)
            return result
        raise MatrixError(f"{cls.__name__}.from_list requires {n}x{n} values")

    @classmethod
    def from_numpy(cls, arr: np.ndarray) -> Self:
        """Create a matrix from a numpy array of shape (n, n) or (n*n,).

        Raises:
            MatrixError: If the shape is wrong.
        """
        n = cls.SIZE
        arr = np.asarray(arr, dtype=np.float32)
        if arr.shape == (n * n,):
            arr = arr.reshape(n, n)
        if arr.shape != (n, n):
            raise MatrixError(f"{cls.__name__}.from_numpy requires shape ({n},{n})")
        result = cls()
        result._data = arr.copy()
        return result

    # -- exports -----------------------------------------------------------
    def to_numpy(self) -> np.ndarray:
        """Return a float32 copy of the matrix as a (n, n) numpy array."""
        return self._data.copy()

    def to_list(self) -> list[float]:
        """Return the matrix as a flat row-major list of floats."""
        return self._data.flatten("C").tolist()

    def to_tuple(self) -> tuple[float, ...]:
        """Return the matrix as a flat row-major tuple of floats."""
        return tuple(float(v) for v in self._data.flatten("C"))

    def copy(self) -> Self:
        """Return a new matrix with the same values."""
        result = self.__class__()
        result._data = self._data.copy()
        return result

    @classmethod
    def sizeof(cls) -> int:
        """Return the size of the matrix in bytes (for OpenGL compatibility)."""
        return cls.SIZE * cls.SIZE * ctypes.sizeof(ctypes.c_float)

    # -- linear algebra ----------------------------------------------------
    def transposed(self) -> Self:
        """Return a new matrix that is the transpose of this one."""
        result = self.__class__()
        result._data = self._data.T.copy()
        return result

    def determinant(self) -> float:
        """Return the determinant of the matrix."""
        return float(np.linalg.det(self._data))

    def inverse(self) -> Self:
        """Return a new matrix that is the inverse of this one.

        Raises:
            MatrixError: If the matrix is singular.
        """
        try:
            result = self.__class__()
            result._data = np.linalg.inv(self._data).astype(np.float32)
            return result
        except np.linalg.LinAlgError as e:
            raise MatrixError("matrix is not invertible") from e

    # -- operators ----------------------------------------------------------
    def _vec_type(self) -> type:
        """Return the vector type this matrix transforms (set by subclass)."""
        raise NotImplementedError  # pragma: no cover

    def __matmul__(self, rhs: Any) -> Any:
        """Matrix @ matrix (row-vector convention) or matrix @ vector.

        Raises:
            MatrixError: If rhs is not a compatible matrix or vector.
        """
        if isinstance(rhs, self.__class__):
            result = self.__class__()
            result._data = rhs._data @ self._data
            return result
        vec_type = self._vec_type()
        if isinstance(rhs, vec_type):
            res = self._data @ np.asarray(list(rhs), dtype=np.float32)
            return vec_type(*res)
        raise MatrixError(
            f"can only multiply {self.__class__.__name__} by "
            f"{self.__class__.__name__} or {vec_type.__name__}"
        )

    def __mul__(self, rhs: float | int) -> Self:
        """Multiply every element by a scalar, returning a new matrix.

        Raises:
            MatrixError: If rhs is not a scalar.
        """
        if isinstance(rhs, (int, float)):
            result = self.__class__()
            result._data = self._data * np.float32(rhs)
            return result
        raise MatrixError("matrices only scale by scalars; use @ for products")

    def __rmul__(self, rhs: float | int) -> Self:
        """Scalar * matrix."""
        return self * rhs

    def __neg__(self) -> Self:
        """Return a new matrix with every element negated."""
        result = self.__class__()
        result._data = -self._data
        return result

    def __truediv__(self, rhs: float | int) -> Self:
        """Divide every element by a scalar, returning a new matrix.

        Raises:
            ZeroDivisionError: If rhs is zero.
            MatrixError: If rhs is not a scalar.
        """
        if isinstance(rhs, (int, float)):
            if rhs == 0:
                raise ZeroDivisionError("division by zero")
            result = self.__class__()
            result._data = self._data / np.float32(rhs)
            return result
        raise MatrixError("matrices only scale by scalars; use @ for products")

    def __add__(self, rhs: Self) -> Self:
        """Piecewise addition, returning a new matrix."""
        if not isinstance(rhs, self.__class__):
            raise MatrixError(f"can only add {self.__class__.__name__}")
        result = self.__class__()
        result._data = self._data + rhs._data
        return result

    def __sub__(self, rhs: Self) -> Self:
        """Piecewise subtraction, returning a new matrix."""
        if not isinstance(rhs, self.__class__):
            raise MatrixError(f"can only subtract {self.__class__.__name__}")
        result = self.__class__()
        result._data = self._data - rhs._data
        return result

    def __getitem__(self, idx: int) -> np.ndarray:
        """Return row idx as a numpy view (element writes go through)."""
        return self._data[idx]

    def __setitem__(self, idx: int, item: Any) -> None:
        """Assign row idx from an iterable of floats."""
        self._data[idx] = np.asarray(item, dtype=np.float32)

    def __len__(self) -> int:
        """Return the row count."""
        return self.SIZE

    def __iter__(self):
        """Yield the elements flat, row-major, as floats."""
        for v in self._data.flatten("C"):
            yield float(v)

    def __eq__(self, rhs: Any) -> bool:
        """Tolerant value equality."""
        if not isinstance(rhs, self.__class__):
            return NotImplemented
        return bool(np.allclose(self._data, rhs._data, rtol=1e-5, atol=1e-6))

    def __ne__(self, rhs: Any) -> bool:
        """Tolerant value inequality."""
        result = self.__eq__(rhs)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self) -> int:
        """Hash combining all elements (32-bit float semantics)."""
        # local import to avoid the util -> mat4 -> mat_base import cycle
        from .util import hash_combine

        seed = 0
        for v in self._data.flatten("C"):
            seed = hash_combine(seed, hash(float(np.float32(v))))
        return seed

    def __repr__(self) -> str:
        """Eval-able representation, e.g. Mat2(1.0, 0.0, 0.0, 1.0)."""
        args = ", ".join(repr(float(v)) for v in self._data.flatten("C"))
        return f"{self.__class__.__name__}({args})"

    def __str__(self) -> str:
        """Pretty row-per-line representation."""
        rows = [str(self._data[i].tolist()) for i in range(self.SIZE)]
        return "[" + "\n ".join(rows) + "]"
