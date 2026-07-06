"""Mat3: 3x3 float32 matrix built on MatrixBase."""

import math
from typing import TYPE_CHECKING

from .mat_base import MatrixBase, MatrixError  # noqa: F401  (re-export)

if TYPE_CHECKING:
    from .mat4 import Mat4


class Mat3(MatrixBase):
    """A 3x3 matrix for basic affine transforms."""

    SIZE = 3

    def _vec_type(self) -> type:
        from .vec3 import Vec3

        return Vec3

    @classmethod
    def scale(cls, x: float, y: float, z: float) -> "Mat3":
        """Return a scale matrix with the diagonal set to (x, y, z)."""
        a = cls()
        a._data[0, 0] = x
        a._data[1, 1] = y
        a._data[2, 2] = z
        return a

    @classmethod
    def rotate_x(cls, angle: float) -> "Mat3":
        """Return a rotation matrix around the X axis by angle degrees."""
        a = cls()
        beta = math.radians(angle)
        sr = math.sin(beta)
        cr = math.cos(beta)
        a._data[1, 1] = cr
        a._data[1, 2] = sr
        a._data[2, 1] = -sr
        a._data[2, 2] = cr
        return a

    @classmethod
    def rotate_y(cls, angle: float) -> "Mat3":
        """Return a rotation matrix around the Y axis by angle degrees."""
        a = cls()
        beta = math.radians(angle)
        sr = math.sin(beta)
        cr = math.cos(beta)
        a._data[0, 0] = cr
        a._data[0, 2] = -sr
        a._data[2, 0] = sr
        a._data[2, 2] = cr
        return a

    @classmethod
    def rotate_z(cls, angle: float) -> "Mat3":
        """Return a rotation matrix around the Z axis by angle degrees."""
        a = cls()
        beta = math.radians(angle)
        sr = math.sin(beta)
        cr = math.cos(beta)
        a._data[0, 0] = cr
        a._data[0, 1] = sr
        a._data[1, 0] = -sr
        a._data[1, 1] = cr
        return a

    @classmethod
    def from_mat4(cls, mat4: "Mat4") -> "Mat3":
        """Return the upper-left 3x3 of a Mat4."""
        result = cls()
        result._data = mat4._data[:3, :3].copy()
        return result
