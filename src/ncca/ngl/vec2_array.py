"""
A container for ngl.Vec2 objects that mimics some of the behavior of a std::vector
Optimized for graphics APIs with contiguous numpy storage
"""

import numpy as np

from .vec2 import Vec2


class Vec2Array:
    """
    A class to hold Vec2 data in contiguous memory for efficient GPU transfer.
    Internally uses a numpy array of shape (N, 2) for optimal performance.
    """

    def __init__(self, values=None):
        """
        Initializes the Vec2Array.

        Args:
            values (iterable | int, optional): An iterable of Vec2 objects or an integer.
                If an integer, the array is initialized with that many default Vec2s.
                If an iterable, it's initialized with the Vec2s from the iterable.
                Defaults to None (an empty array).
        """
        if values is None:
            # Empty array - start with shape (0, 2)
            self._data = np.zeros((0, 2), dtype=np.float64)
        elif isinstance(values, int):
            # Initialize N default Vec2s (0, 0)
            self._data = np.zeros((values, 2), dtype=np.float64)
        else:
            # Initialize from iterable of Vec2 objects
            vec_list = []
            for v in values:
                if not isinstance(v, Vec2):
                    raise TypeError("All elements must be of type Vec2")
                vec_list.append([v.x, v.y])
            self._data = np.array(vec_list, dtype=np.float64)

    def __getitem__(self, index):
        """
        Get the Vec2 at the specified index.

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

    def __setitem__(self, index, value):
        """
        Set the Vec2 at the specified index.

        Args:
            index (int): The index of the element to set.
            value (Vec2): The new Vec2 object.
        """
        if not isinstance(value, Vec2):
            raise TypeError("Only Vec2 objects can be assigned")
        self._data[index] = [value.x, value.y]

    def __len__(self):
        """
        Return the number of elements in the array.
        """
        return len(self._data)

    def __iter__(self):
        """
        Return an iterator that yields Vec2 objects.
        """
        for i in range(len(self._data)):
            row = self._data[i]
            yield Vec2(row[0], row[1])

    def append(self, value):
        """
        Append a Vec2 object to the array.

        Args:
            value (Vec2): The Vec2 object to append.
        """
        if not isinstance(value, Vec2):
            raise TypeError("Only Vec2 objects can be appended")
        new_row = np.array([[value.x, value.y]], dtype=np.float64)
        self._data = np.vstack([self._data, new_row])

    def extend(self, values):
        """
        Extend the array with a list of Vec2 objects.

        Args:
            values (list): A list of Vec2 objects to extend.
        """
        if not all(isinstance(v, Vec2) for v in values):
            raise TypeError("All elements must be of type Vec2")

        new_rows = np.array([[v.x, v.y] for v in values], dtype=np.float64)
        if len(self._data) == 0:
            self._data = new_rows
        else:
            self._data = np.vstack([self._data, new_rows])

    def to_list(self):
        """
        Convert the array of Vec2 objects to a single flat list of floats.

        Returns:
            list: A list of x, y components concatenated.
        """
        return self._data.flatten().tolist()

    def to_numpy(self):
        """
        Convert the array of Vec2 objects to a numpy array.
        This is the primary method for GPU data transfer.

        Returns:
            numpy.ndarray: A float32 numpy array of shape (N*2,) for GPU transfer.
        """
        return self._data.astype(np.float32).flatten()

    def get_array(self):
        """
        Get the underlying numpy array in shape (N, 2).
        Useful for vectorized operations.

        Returns:
            numpy.ndarray: The internal float64 array of shape (N, 2).
        """
        return self._data

    def __repr__(self):
        vec_list = [Vec2(row[0], row[1]) for row in self._data]
        return f"Vec2Array({vec_list!r})"

    def __str__(self):
        vec_list = [Vec2(row[0], row[1]) for row in self._data]
        return str(vec_list)

    def sizeof(self):
        """
        Return the size of the array in bytes.

        Returns:
            int: The size of the array in bytes.
        """
        return len(self._data) * Vec2.sizeof()
