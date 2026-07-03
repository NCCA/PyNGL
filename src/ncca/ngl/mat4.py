"""Mat4: 4x4 float32 matrix built on MatrixBase."""

import math

from .mat_base import MatrixBase, MatrixError  # noqa: F401  (re-export)


class Mat4(MatrixBase):
    """A 4x4 matrix for 3D affine and projective transforms."""

    SIZE = 4

    def _vec_type(self) -> type:
        from .vec4 import Vec4

        return Vec4

    @classmethod
    def scale(cls, x: float, y: float, z: float) -> "Mat4":
        """Return a scale matrix with the diagonal set to (x, y, z, 1)."""
        a = cls()
        a._data[0, 0] = x
        a._data[1, 1] = y
        a._data[2, 2] = z
        return a

    @classmethod
    def translate(cls, x: float, y: float, z: float) -> "Mat4":
        """Return a translation matrix."""
        a = cls()
        a._data[3, 0] = x
        a._data[3, 1] = y
        a._data[3, 2] = z
        return a

    @classmethod
    def rotate_x(cls, angle: float) -> "Mat4":
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
    def rotate_y(cls, angle: float) -> "Mat4":
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
    def rotate_z(cls, angle: float) -> "Mat4":
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
    def from_mat3(cls, mat3) -> "Mat4":
        """Return a Mat4 with the given Mat3 as its upper-left block."""
        result = cls()
        result._data[:3, :3] = mat3._data
        return result
