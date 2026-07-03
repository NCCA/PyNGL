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
    __slots__ = ("_data",)  # Store as [s, x, y, z]

    def __init__(
        self, s: float = 1.0, x: float = 0.0, y: float = 0.0, z: float = 0.0
    ) -> None:
        """
        Initializes a new instance of the Quaternion class.

        Args:
            s (float): The scalar part of the quaternion.
            x (float): The x-coordinate of the vector part of the quaternion.
            y (float): The y-coordinate of the vector part of the quaternion.
            z (float): The z-coordinate of the vector part of the quaternion.
        """
        self._data = np.array(
            [float(s), float(x), float(y), float(z)], dtype=np.float32
        )

    @classmethod
    def from_mat4(cls, mat: "Mat4") -> "Quaternion":
        """
        Creates a new Quaternion from a Mat4 rotation matrix.

        Args:
            mat (Mat4): The rotation matrix to convert.

        Returns:
            Quaternion: A new Quaternion representing the rotation matrix.
        """
        matrix = mat.to_list()
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

        return cls(s, x, y, z)

    @classmethod
    def from_axis_angle(cls, axis: "Vec3", angle: float) -> "Quaternion":
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
        return cls(s, x, y, z)

    def __add__(self, rhs: "Quaternion") -> "Quaternion":
        result = Quaternion()
        result._data = self._data + rhs._data
        return result

    def __sub__(self, rhs: "Quaternion") -> "Quaternion":
        result = Quaternion()
        result._data = self._data - rhs._data
        return result

    def __matmul__(self, rhs: "Quaternion") -> "Quaternion":
        """Quaternion product (Hamilton), returning a new quaternion."""
        if not isinstance(rhs, Quaternion):
            raise TypeError("@ requires a Quaternion")
        s1, x1, y1, z1 = self._data
        s2, x2, y2, z2 = rhs._data
        return Quaternion(
            s1 * s2 - x1 * x2 - y1 * y2 - z1 * z2,
            s1 * x2 + x1 * s2 + y1 * z2 - z1 * y2,
            s1 * y2 - x1 * z2 + y1 * s2 + z1 * x2,
            s1 * z2 + x1 * y2 - y1 * x2 + z1 * s2,
        )

    def __mul__(self, rhs):
        """Scalar scale or Vec3 rotation. Quaternion product uses @."""
        if isinstance(rhs, Quaternion):
            raise TypeError("use q1 @ q2 for the quaternion product")
        if isinstance(rhs, (int, float)):
            result = Quaternion()
            result._data = self._data * np.float32(rhs)
            return result
        if isinstance(rhs, Vec3):
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
        raise TypeError(f"cannot multiply Quaternion by {type(rhs)}")

    def __rmul__(self, rhs: float) -> "Quaternion":
        if isinstance(rhs, (int, float)):
            return self * rhs
        raise TypeError(f"cannot multiply {type(rhs)} by Quaternion")

    def __neg__(self) -> "Quaternion":
        """Return a new quaternion with every component negated."""
        result = Quaternion()
        result._data = -self._data
        return result

    def __truediv__(self, rhs: float | int) -> "Quaternion":
        """Scalar division, returning a new quaternion.

        Raises:
            ZeroDivisionError: If rhs is zero.
            TypeError: If rhs is not a scalar.
        """
        if isinstance(rhs, (int, float)):
            if rhs == 0:
                raise ZeroDivisionError("division by zero")
            result = Quaternion()
            result._data = self._data / np.float32(rhs)
            return result
        raise TypeError(f"cannot divide Quaternion by {type(rhs)}")

    def __getitem__(self, index: int) -> float:
        """Return the component at index (0=s, 1=x, 2=y, 3=z).

        Raises:
            IndexError: If the index is out of range.
        """
        if index < 0 or index >= 4:
            raise IndexError("Index out of range. Valid indices are 0, 1, 2, 3.")
        return float(self._data[index])

    def normalized(self) -> "Quaternion":
        """Return a new unit-length quaternion.

        Raises:
            ZeroDivisionError: If the quaternion has zero length.
        """
        length = self.length()
        if math.isclose(length, 0.0):
            raise ZeroDivisionError("Quaternion.normalized: length is zero")
        result = Quaternion()
        result._data = self._data / np.float32(length)
        return result

    def length(self) -> float:
        """Return the length/magnitude of the quaternion"""
        return float(np.linalg.norm(self._data))

    def length_squared(self) -> float:
        """Return the squared magnitude."""
        return float(np.dot(self._data, self._data))

    def conjugate(self) -> "Quaternion":
        """Return the conjugate of the quaternion (s, -x, -y, -z)"""
        result = Quaternion()
        result._data = self._data.copy()
        result._data[1:] *= -1  # Negate x, y, z components
        return result

    def inverse(self) -> "Quaternion":
        """Return the multiplicative inverse (conjugate / |q|^2)."""
        lsq = self.length_squared()
        if math.isclose(lsq, 0.0):
            raise ZeroDivisionError("Quaternion.inverse: zero quaternion")
        result = self.conjugate()
        result._data = result._data / np.float32(lsq)
        return result

    def dot(self, rhs: "Quaternion") -> float:
        """Dot product of two quaternions"""
        return float(np.dot(self._data, rhs._data))

    def slerp(self, rhs: "Quaternion", t: float) -> "Quaternion":
        """Spherical linear interpolation from self to rhs at t in [0, 1]."""
        dot = float(np.dot(self._data, rhs._data))
        rhs_data = rhs._data.copy()
        if dot < 0.0:
            dot = -dot
            rhs_data = -rhs_data
        if dot > 0.9995:
            data = self._data + np.float32(t) * (rhs_data - self._data)
            data = data / np.linalg.norm(data)
        else:
            theta0 = math.acos(max(-1.0, min(1.0, dot)))
            theta = theta0 * t
            s0 = math.cos(theta) - dot * math.sin(theta) / math.sin(theta0)
            s1 = math.sin(theta) / math.sin(theta0)
            data = np.float32(s0) * self._data + np.float32(s1) * rhs_data
        result = Quaternion()
        result._data = data.astype(np.float32)
        return result

    def to_mat4(self) -> Mat4:
        """Return the equivalent rotation matrix (row-vector convention)."""
        s, x, y, z = (float(v) for v in self._data)
        m = Mat4()
        m._data[0, 0] = 1.0 - 2.0 * (y * y + z * z)
        m._data[0, 1] = 2.0 * (x * y + s * z)
        m._data[0, 2] = 2.0 * (x * z - s * y)
        m._data[1, 0] = 2.0 * (x * y - s * z)
        m._data[1, 1] = 1.0 - 2.0 * (x * x + z * z)
        m._data[1, 2] = 2.0 * (y * z + s * x)
        m._data[2, 0] = 2.0 * (x * z + s * y)
        m._data[2, 1] = 2.0 * (y * z - s * x)
        m._data[2, 2] = 1.0 - 2.0 * (x * x + y * y)
        return m

    def set(self, s: float, x: float, y: float, z: float) -> None:
        """Set all four components."""
        self._data[:] = (float(s), float(x), float(y), float(z))

    def copy(self) -> "Quaternion":
        """Return a new quaternion with the same values."""
        return Quaternion(*self._data)

    def to_numpy(self) -> np.ndarray:
        """Return the quaternion as a numpy array [s, x, y, z]"""
        return self._data.copy()

    def to_list(self) -> list[float]:
        """Return the quaternion as a list [s, x, y, z]"""
        return self._data.tolist()

    def to_tuple(self) -> tuple[float, float, float, float]:
        """Return (s, x, y, z) as plain floats."""
        return tuple(float(v) for v in self._data)

    @classmethod
    def from_list(cls, lst: list[float]) -> "Quaternion":
        """Create from [s, x, y, z]."""
        if len(lst) != 4:
            raise ValueError("Quaternion.from_list requires 4 values")
        return cls(*lst)

    @classmethod
    def from_numpy(cls, arr: np.ndarray) -> "Quaternion":
        """Create from an array [s, x, y, z]."""
        arr = np.asarray(arr, dtype=np.float32)
        if arr.shape != (4,):
            raise ValueError("Quaternion.from_numpy requires shape (4,)")
        return cls(*arr)

    def __eq__(self, rhs: object) -> bool:
        if not isinstance(rhs, Quaternion):
            return NotImplemented
        return bool(np.allclose(self._data, rhs._data, rtol=1e-5, atol=1e-6))

    def __ne__(self, rhs: object) -> bool:
        result = self.__eq__(rhs)
        return result if result is NotImplemented else not result

    def __hash__(self) -> int:
        from .util import hash_combine

        seed = 0
        for v in self._data:
            seed = hash_combine(seed, hash(float(np.float32(v))))
        return seed

    def __len__(self) -> int:
        return 4

    def __iter__(self):
        return iter(self._data.tolist())

    def __repr__(self) -> str:
        args = ", ".join(repr(float(v)) for v in self._data)
        return f"Quaternion({args})"

    def __str__(self) -> str:
        s, x, y, z = (float(v) for v in self._data)
        return f"Quaternion({s}, [{x}, {y}, {z}])"


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
