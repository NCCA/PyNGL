"""
A simple Quaternion class for use in NCCA Python
NumPy-based implementation for efficient operations
Attributes:
    s (float): The scalar part of the quaternion.
    x (float): The x-coordinate of the vector part of the quaternion.
    y (float): The y-coordinate of the vector part of the quaternion.
    z (float): The z-coordinate of the vector part of the quaternion.
"""

import math

import numpy as np

from .mat4 import Mat4
from .vec3 import Vec3


class Quaternion:
    __slots__ = ["_data"]  # Store as [s, x, y, z]

    def __init__(self, s: float = 1.0, x: float = 0, y: float = 0, z: float = 0):
        """
        Initializes a new instance of the Quaternion class.

        Args:
            s (float): The scalar part of the quaternion.
            x (float): The x-coordinate of the vector part of the quaternion.
            y (float): The y-coordinate of the vector part of the quaternion.
            z (float): The z-coordinate of the vector part of the quaternion.
        """
        self._data = np.array(
            [float(s), float(x), float(y), float(z)], dtype=np.float64
        )

    @staticmethod
    def from_mat4(mat: "Mat4") -> "Quaternion":
        """
        Creates a new Quaternion from a Mat4 rotation matrix.

        Args:
            mat (Mat4): The rotation matrix to convert.

        Returns:
            Quaternion: A new Quaternion representing the rotation matrix.
        """
        matrix = mat.get_matrix()
        T = 1.0 + matrix[0] + matrix[5] + matrix[10]
        if T > 0.00000001:  # to avoid large distortions!
            scale = math.sqrt(T) * 2.0
            x = (matrix[6] - matrix[9]) / scale
            y = (matrix[8] - matrix[2]) / scale
            z = (matrix[1] - matrix[4]) / scale
            s = 0.25 * scale
        elif matrix[0] > matrix[5] and matrix[0] > matrix[10]:
            scale = math.sqrt(1.0 + matrix[0] - matrix[5] - matrix[10]) * 2.0
            x = 0.25 * scale
            y = (matrix[4] + matrix[1]) / scale
            z = (matrix[2] + matrix[8]) / scale
            s = (matrix[6] - matrix[9]) / scale
        elif matrix[5] > matrix[10]:
            scale = math.sqrt(1.0 + matrix[5] - matrix[0] - matrix[10]) * 2.0
            x = (matrix[4] + matrix[1]) / scale
            y = 0.25 * scale
            z = (matrix[9] + matrix[6]) / scale
            s = (matrix[8] - matrix[2]) / scale
        else:
            scale = math.sqrt(1.0 + matrix[10] - matrix[0] - matrix[5]) * 2.0
            x = (matrix[8] + matrix[2]) / scale
            y = (matrix[9] + matrix[6]) / scale
            z = 0.25 * scale
            s = (matrix[1] - matrix[4]) / scale

        return Quaternion(s, x, y, z)

    @staticmethod
    def from_axis_angle(axis: "Vec3", angle: float) -> "Quaternion":
        """
        Creates a new Quaternion from an axis and angle.

        Args:
            axis (Vec3): The axis of rotation.
            angle (float): The angle of rotation in degrees.

        Returns:
            Quaternion: A new Quaternion representing the rotation.
        """
        angle_rad = math.radians(angle)
        half_angle = angle_rad * 0.5
        s = math.cos(half_angle)
        sin_half_angle = math.sin(half_angle)
        x = axis.x * sin_half_angle
        y = axis.y * sin_half_angle
        z = axis.z * sin_half_angle
        return Quaternion(s, x, y, z)

    def __add__(self, rhs):
        result = Quaternion()
        result._data = self._data + rhs._data
        return result

    def __iadd__(self, rhs):
        self._data += rhs._data
        return self

    def __sub__(self, rhs):
        result = Quaternion()
        result._data = self._data - rhs._data
        return result

    def __isub__(self, rhs):
        self._data -= rhs._data
        return self

    def __mul__(self, rhs):
        if isinstance(rhs, Quaternion):
            # Quaternion multiplication
            s1, x1, y1, z1 = self._data
            s2, x2, y2, z2 = rhs._data

            return Quaternion(
                s1 * s2 - x1 * x2 - y1 * y2 - z1 * z2,
                s1 * x2 + x1 * s2 + y1 * z2 - z1 * y2,
                s1 * y2 - x1 * z2 + y1 * s2 + z1 * x2,
                s1 * z2 + x1 * y2 - y1 * x2 + z1 * s2,
            )
        elif isinstance(rhs, Vec3):
            # Quaternion-vector multiplication (rotate vector by quaternion)
            qw = self.s
            qx = self.x
            qy = self.y
            qz = self.z

            vx = rhs.x
            vy = rhs.y
            vz = rhs.z

            # pq (quaternion * pure quaternion from vector)
            pw = -qx * vx - qy * vy - qz * vz
            px = qw * vx + qy * vz - qz * vy
            py = qw * vy - qx * vz + qz * vx
            pz = qw * vz + qx * vy - qy * vx

            # pqp* (result * conjugate of quaternion)
            return Vec3(
                -pw * qx + px * qw - py * qz + pz * qy,
                -pw * qy + px * qz + py * qw - pz * qx,
                -pw * qz - px * qy + py * qx + pz * qw,
            )

    def normalize(self):
        """Normalize the quaternion to unit length"""
        length = np.linalg.norm(self._data)
        if length > 0:
            self._data /= length

    def length(self):
        """Return the length/magnitude of the quaternion"""
        return np.linalg.norm(self._data)

    def conjugate(self):
        """Return the conjugate of the quaternion (s, -x, -y, -z)"""
        result = Quaternion()
        result._data = self._data.copy()
        result._data[1:] *= -1  # Negate x, y, z components
        return result

    def dot(self, rhs):
        """Dot product of two quaternions"""
        return np.dot(self._data, rhs._data)

    def __str__(self) -> str:
        """
        Returns a string representation of the Quaternion.

        Returns:
            str: A string representation of the Quaternion.
        """
        return f"Quaternion({self.s}, [{self.x}, {self.y}, {self.z}])"

    def __repr__(self) -> str:
        return f"Quaternion({self.s}, [{self.x}, {self.y}, {self.z}])"

    def to_numpy(self):
        """Return the quaternion as a numpy array [s, x, y, z]"""
        return self._data.copy()

    def to_list(self):
        """Return the quaternion as a list [s, x, y, z]"""
        return self._data.tolist()


# Helper function to create properties
def _create_property(index):
    def getter(self):
        return self._data[index]

    def setter(self, value):
        if not isinstance(value, (int, float, np.float32)):
            raise ValueError("need float or int")
        self._data[index] = value

    return property(getter, setter)


# Dynamically add properties for s, x, y, z, w
for i, attr in enumerate(["s", "x", "y", "z"]):
    setattr(Quaternion, attr, _create_property(i))
