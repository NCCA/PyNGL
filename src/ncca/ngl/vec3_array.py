"""
A container for ngl.Vec3 objects that mimics some of the behavior of a std::vector
Optimized for graphics APIs with contiguous numpy storage
"""

import numpy as np

from .vec3 import Vec3


class Vec3Array:
    """
    A class to hold Vec3 data in contiguous memory for efficient GPU transfer.
    Internally uses a numpy array of shape (N, 3) for optimal performance.
    """

    def __init__(self, values=None):
        """
        Initializes the Vec3Array.

        Args:
            values (iterable | int, optional): An iterable of Vec3 objects or an integer.
                If an integer, the array is initialized with that many default Vec3s.
                If an iterable, it's initialized with the Vec3s from the iterable.
                Defaults to None (an empty array).
        """
        if values is None:
            # Empty array - start with shape (0, 3)
            self._data = np.zeros((0, 3), dtype=np.float64)
        elif isinstance(values, int):
            # Initialize N default Vec3s (0, 0, 0)
            self._data = np.zeros((values, 3), dtype=np.float64)
        else:
            # Initialize from iterable of Vec3 objects
            vec_list = []
            for v in values:
                if not isinstance(v, Vec3):
                    raise TypeError("All elements must be of type Vec3")
                vec_list.append([v.x, v.y, v.z])
            self._data = np.array(vec_list, dtype=np.float64)

    def __getitem__(self, index):
        """
        Get the Vec3 at the specified index.

        Args:
            index (int | slice): The index or slice of the element(s).

        Returns:
            Vec3: The Vec3 object at the given index.
            Vec3Array: A new Vec3Array if slicing.
        """
        if isinstance(index, slice):
            # Return a new Vec3Array with sliced data
            result = Vec3Array()
            result._data = self._data[index].copy()
            return result
        else:
            # Return a single Vec3
            row = self._data[index]
            return Vec3(row[0], row[1], row[2])

    def __setitem__(self, index, value):
        """
        Set the Vec3 at the specified index.

        Args:
            index (int): The index of the element to set.
            value (Vec3): The new Vec3 object.
        """
        if not isinstance(value, Vec3):
            raise TypeError("Only Vec3 objects can be assigned")
        self._data[index] = [value.x, value.y, value.z]

    def __len__(self):
        """
        Return the number of elements in the array.
        """
        return len(self._data)

    def __iter__(self):
        """
        Return an iterator that yields Vec3 objects.
        """
        for i in range(len(self._data)):
            row = self._data[i]
            yield Vec3(row[0], row[1], row[2])

    def __eq__(self, other):
        """
        Compare two Vec3Array instances for equality.

        Args:
            other: Another Vec3Array instance to compare with.

        Returns:
            bool: True if the arrays contain the same data, False otherwise.
        """
        if not isinstance(other, Vec3Array):
            return NotImplemented
        return np.array_equal(self._data, other._data)

    def append(self, value):
        """
        Append a Vec3 object to the array.

        Args:
            value (Vec3): The Vec3 object to append.
        """
        if not isinstance(value, Vec3):
            raise TypeError("Only Vec3 objects can be appended")
        new_row = np.array([[value.x, value.y, value.z]], dtype=np.float64)
        self._data = np.vstack([self._data, new_row])

    def extend(self, values):
        """
        Extend the array by appending elements from the iterable.

        Args:
            values (iterable): An iterable of Vec3 objects to append.

        Raises:
            TypeError: If any element in values is not a Vec3.
        """
        vec_list = []
        for v in values:
            if not isinstance(v, Vec3):
                raise TypeError("All elements must be of type Vec3")
            vec_list.append([v.x, v.y, v.z])

        new_rows = np.array(vec_list, dtype=np.float64)
        if len(self._data) == 0:
            self._data = new_rows
        else:
            self._data = np.vstack([self._data, new_rows])

    def to_list(self):
        """
        Convert the array of Vec3 objects to a single flat list of floats.

        Returns:
            list: A list of x, y, z components concatenated.
        """
        return self._data.flatten().tolist()

    def to_numpy(self):
        """
        Convert the array of Vec3 objects to a numpy array.
        This is the primary method for GPU data transfer.

        Returns:
            numpy.ndarray: A float32 numpy array of shape (N*3,) for GPU transfer.
        """
        return self._data.astype(np.float32).flatten()

    def get_array(self):
        """
        Get the underlying numpy array in shape (N, 3).
        Useful for vectorized operations.

        Returns:
            numpy.ndarray: The internal float64 array of shape (N, 3).
        """
        return self._data

    def __repr__(self):
        vec_list = [Vec3(row[0], row[1], row[2]) for row in self._data]
        return f"Vec3Array({vec_list!r})"

    def __str__(self):
        vec_list = [Vec3(row[0], row[1], row[2]) for row in self._data]
        return str(vec_list)

    def sizeof(self):
        """
        Return the size of the array in bytes.

        Returns:
            int: The size of the array in bytes.
        """
        return len(self._data) * Vec3.sizeof()
