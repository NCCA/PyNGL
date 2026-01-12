"""
A container for ngl.Vec4 objects that mimics some of the behavior of a std::vector
Optimized for graphics APIs with contiguous numpy storage
"""

import numpy as np

from .vec4 import Vec4


class Vec4Array:
    """
    A class to hold Vec4 data in contiguous memory for efficient GPU transfer.
    Internally uses a numpy array of shape (N, 4) for optimal performance.
    """

    def __init__(self, values=None):
        """
        Initializes the Vec4Array.

        Args:
            values (iterable | int, optional): An iterable of Vec4 objects or an integer.
                If an integer, the array is initialized with that many default Vec4s.
                If an iterable, it's initialized with the Vec4s from the iterable.
                Defaults to None (an empty array).
        """
        if values is None:
            # Empty array - start with shape (0, 4)
            self._data = np.zeros((0, 4), dtype=np.float64)
        elif isinstance(values, int):
            # Initialize N default Vec4s (0, 0, 0, 1)
            self._data = np.zeros((values, 4), dtype=np.float64)
            self._data[:, 3] = 1.0  # Set w component to 1.0
        else:
            # Initialize from iterable of Vec4 objects
            vec_list = []
            for v in values:
                if not isinstance(v, Vec4):
                    raise TypeError("All elements must be of type Vec4")
                vec_list.append([v.x, v.y, v.z, v.w])
            self._data = np.array(vec_list, dtype=np.float64)

    def __getitem__(self, index):
        """
        Get the Vec4 at the specified index.

        Args:
            index (int | slice): The index or slice of the element(s).

        Returns:
            Vec4: The Vec4 object at the given index.
        """
        if isinstance(index, slice):
            # Return a new Vec4Array with sliced data
            result = Vec4Array()
            result._data = self._data[index].copy()
            return result
        else:
            # Return a single Vec4
            row = self._data[index]
            return Vec4(row[0], row[1], row[2], row[3])

    def __setitem__(self, index, value):
        """
        Set the Vec4 at the specified index.

        Args:
            index (int): The index of the element to set.
            value (Vec4): The new Vec4 object.
        """
        if not isinstance(value, Vec4):
            raise TypeError("Only Vec4 objects can be assigned")
        self._data[index] = [value.x, value.y, value.z, value.w]

    def __len__(self):
        """
        Return the number of elements in the array.
        """
        return len(self._data)

    def __iter__(self):
        """
        Return an iterator that yields Vec4 objects.
        """
        for i in range(len(self._data)):
            row = self._data[i]
            yield Vec4(row[0], row[1], row[2], row[3])

    def __eq__(self, other):
        """
        Compare two Vec4Array instances for equality.

        Args:
            other: Another Vec4Array instance to compare with.

        Returns:
            bool: True if the arrays contain the same data, False otherwise.
        """
        if not isinstance(other, Vec4Array):
            return NotImplemented
        return np.array_equal(self._data, other._data)

    def append(self, value):
        """
        Append a Vec4 object to the array.

        Args:
            value (Vec4): The Vec4 object to append.
        """
        if not isinstance(value, Vec4):
            raise TypeError("Only Vec4 objects can be appended")
        new_row = np.array([[value.x, value.y, value.z, value.w]], dtype=np.float64)
        self._data = np.vstack([self._data, new_row])

    def extend(self, values):
        """
        Extend the array with a list of Vec4 objects.

        Args:
            values (list): A list of Vec4 objects to extend.
        """
        if not all(isinstance(v, Vec4) for v in values):
            raise TypeError("All elements must be of type Vec4")

        new_rows = np.array([[v.x, v.y, v.z, v.w] for v in values], dtype=np.float64)
        if len(self._data) == 0:
            self._data = new_rows
        else:
            self._data = np.vstack([self._data, new_rows])

    def to_list(self):
        """
        Convert the array of Vec4 objects to a single flat list of floats.

        Returns:
            list: A list of x, y, z, w components concatenated.
        """
        return self._data.flatten().tolist()

    def to_numpy(self):
        """
        Convert the array of Vec4 objects to a numpy array.
        This is the primary method for GPU data transfer.

        Returns:
            numpy.ndarray: A float32 numpy array of shape (N*4,) for GPU transfer.
        """
        return self._data.astype(np.float32).flatten()

    def get_array(self):
        """
        Get the underlying numpy array in shape (N, 4).
        Useful for vectorized operations.

        Returns:
            numpy.ndarray: The internal float64 array of shape (N, 4).
        """
        return self._data

    def __repr__(self):
        vec_list = [Vec4(row[0], row[1], row[2], row[3]) for row in self._data]
        return f"Vec4Array({vec_list!r})"

    def __str__(self):
        vec_list = [Vec4(row[0], row[1], row[2], row[3]) for row in self._data]
        return str(vec_list)

    def sizeof(self):
        """
        Return the size of the array in bytes.

        Returns:
            int: The size of the array in bytes.
        """
        return len(self._data) * Vec4.sizeof()
