"""Represents a mathematical plane defined by a point and a normal."""

from .vec3 import Vec3


class Plane:
    """A mathematical plane."""

    def __init__(
        self,
        p1: Vec3 | None = None,
        p2: Vec3 | None = None,
        p3: Vec3 | None = None,
    ) -> None:
        """Construct a plane, optionally through three points.

        Args:
            p1: First point on the plane.
            p2: Second point on the plane.
            p3: Third point on the plane.
        """
        self._normal = Vec3(0.0, 1.0, 0.0)
        self._point = Vec3()
        self._d = 0.0
        if p1 and p2 and p3:
            self.set_points(p1, p2, p3)

    @property
    def normal(self) -> Vec3:
        """The plane's unit normal vector."""
        return self._normal

    @property
    def point(self) -> Vec3:
        """A point known to lie on the plane."""
        return self._point

    @property
    def d(self) -> float:
        """The plane's distance term in the equation normal.p + d = 0."""
        return self._d

    def set_points(self, p1: Vec3, p2: Vec3, p3: Vec3) -> None:
        """Define the plane from three points."""
        aux1 = p1 - p2
        aux2 = p3 - p2
        self._normal = aux2.cross(aux1)
        self._normal = self._normal.normalized()
        self._point = p2
        self._d = -(self._normal.inner(self._point))

    def set_normal_point(self, normal: Vec3, point: Vec3) -> None:
        """Define the plane from a normal and a point on the plane."""
        self._normal = normal
        self._normal = self._normal.normalized()
        self._point = point
        self._d = -(self._normal.inner(self._point))

    def set_floats(self, a: float, b: float, c: float, d: float) -> None:
        """Define the plane from the coefficients of ax + by + cz + d = 0."""
        self._normal.set(a, b, c)
        length = self._normal.length()
        self._normal = self._normal.normalized()
        self._d = d / length

    def distance(self, p: Vec3) -> float:
        """Return the signed distance from point p to the plane."""
        return self._d + self._normal.inner(p)
