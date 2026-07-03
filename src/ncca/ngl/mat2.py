"""Mat2: 2x2 float32 matrix built on MatrixBase."""

from .mat_base import MatrixBase, MatrixError  # noqa: F401  (re-export)


class Mat2(MatrixBase):
    """A 2x2 matrix for 2D transforms."""

    SIZE = 2

    def _vec_type(self) -> type:
        from .vec2 import Vec2

        return Vec2
