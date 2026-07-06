"""A container for ngl.Vec2 objects that mimics some of the behavior of a std::vector.

Optimized for graphics APIs with contiguous numpy storage.
"""

from typing import Iterable

import numpy as np

from .vec2 import Vec2


class Vec2Array:
    """A class to hold Vec2 data in contiguous memory for efficient GPU transfer.

    Internally uses a numpy array of shape (N, 2) for optimal performance.
    Mutable container — intentionally not hashable.
    """

    def __init__(self, values: "Iterable[Vec2] | int | None" = None) -> None:
        """Initializes the Vec2Array.

        Args:
            values (iterable | int, optional): An iterable of Vec2 objects or an integer.
                If an integer, the array is initialized with that many default Vec2s.
                If an iterable, it's initialized with the Vec2s from the iterable.
                Defaults to None (an empty array).
        """
        if values is None:
            # Empty array - start with shape (0, 2)
            self._data = np.zeros((0, 2), dtype=np.float32)
        elif isinstance(values, int):
            # Initialize N default Vec2s (0, 0)
            self._data = np.zeros((values, 2), dtype=np.float32)
        else:
            # Initialize from iterable of Vec2 objects
            vec_list = []
            for v in values:
                if not isinstance(v, Vec2):
                    raise TypeError("All elements must be of type Vec2")
                vec_list.append([v.x, v.y])
            self._data = np.array(vec_list, dtype=np.float32)

    def __getitem__(self, index: int | slice) -> "Vec2 | Vec2Array":
        """Get the Vec2 at the specified index.

        Args:
            index (int | slice): The index or slice of the element(s).

        Returns:
            Vec2: The Vec2 object at the given index.
            Vec2Array: A new Vec2Array if slicing.
        """
        if isinstance(index, slice):
            # Return a new Vec2Array with sliced data
            result = Vec2Array()
            result._data = self._data[index].copy()
            return result
        else:
            # Return a single Vec2
            row = self._data[index]
            return Vec2(row[0], row[1])

    def __setitem__(self, index: int, value: Vec2) -> None:
        """Set the Vec2 at the specified index.

        Args:
            index (int): The index of the element to set.
            value (Vec2): The new Vec2 object.
        """
        if not isinstance(value, Vec2):
            raise TypeError("Only Vec2 objects can be assigned")
        self._data[index] = [value.x, value.y]

    def __len__(self) -> int:
        """Return the number of elements in the array."""
        return len(self._data)

    def __iter__(self) -> "Iterable[Vec2]":
        """Return an iterator that yields Vec2 objects."""
        for i in range(len(self._data)):
            row = self._data[i]
            yield Vec2(row[0], row[1])

    def __eq__(self, other: object) -> bool:
        """Compare two Vec2Array instances for equality.

        Args:
            other: Another Vec2Array instance to compare with.

        Returns:
            bool: True if the arrays contain the same data, False otherwise.
        """
        if not isinstance(other, Vec2Array):
            return NotImplemented
        return np.array_equal(self._data, other._data)

    def append(self, value: Vec2) -> None:
        """Append a Vec2 object to the array.

        Args:
            value (Vec2): The Vec2 object to append.
        """
        if not isinstance(value, Vec2):
            raise TypeError("Only Vec2 objects can be appended")
        new_row = np.array([[value.x, value.y]], dtype=np.float32)
        self._data = np.vstack([self._data, new_row])

    def extend(self, values: "Iterable[Vec2]") -> None:
        """Extend the array with a list of Vec2 objects.

        Args:
            values (list): A list of Vec2 objects to extend.
        """
        if not all(isinstance(v, Vec2) for v in values):
            raise TypeError("All elements must be of type Vec2")

        new_rows = np.array([[v.x, v.y] for v in values], dtype=np.float32)
        if len(self._data) == 0:
            self._data = new_rows
        else:
            self._data = np.vstack([self._data, new_rows])

    def to_list(self) -> list[float]:
        """Convert the array of Vec2 objects to a single flat list of floats.

        Returns:
            list: A list of x, y components concatenated.
        """
        return self._data.flatten().tolist()

    def to_numpy(self) -> np.ndarray:
        """Convert the array of Vec2 objects to a numpy array.

        This is the primary method for GPU data transfer.

        Returns:
            numpy.ndarray: A float32 numpy array of shape (N*2,) for GPU transfer.
        """
        return self._data.flatten().copy()

    def to_tuple(self) -> tuple[float, ...]:
        """Return all components as one flat tuple of floats."""
        return tuple(float(v) for v in self._data.flatten())

    def __repr__(self) -> str:
        """Eval-able representation, e.g. Vec2Array([Vec2(0.0, 0.0)])."""
        vec_list = [Vec2(row[0], row[1]) for row in self._data]
        return f"Vec2Array({vec_list!r})"

    def __str__(self) -> str:
        """Pretty representation as a list of Vec2 values."""
        vec_list = [Vec2(row[0], row[1]) for row in self._data]
        return str(vec_list)

    def sizeof(self) -> int:
        """Return the size of the array in bytes.

        Returns:
            int: The size of the array in bytes.
        """
        return len(self._data) * Vec2.sizeof()
