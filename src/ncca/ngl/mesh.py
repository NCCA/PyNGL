"""Backend-neutral mesh data used by the OpenGL and WebGPU renderers."""

from dataclasses import dataclass, field

import numpy as np

from .bbox import BBox
from .vec2 import Vec2
from .vec3 import Vec3


@dataclass(slots=True)
class Face:
    """Indices for one polygon face."""

    vertex: list[int] = field(default_factory=list)
    uv: list[int] = field(default_factory=list)
    normal: list[int] = field(default_factory=list)


class MeshValidationError(RuntimeError):
    """Raised when mesh data cannot be converted into renderable triangles."""


class MeshData:
    """CPU-side mesh geometry shared by rendering back ends."""

    def __init__(self) -> None:
        """Create an empty CPU-side mesh."""
        self.vertex: list[Vec3] = []
        self.normals: list[Vec3] = []
        self.uv: list[Vec2 | Vec3] = []
        self.faces: list[Face] = []
        self.colour: list[Vec3] = []
        self.bbox: BBox | None = None
        self.min_x = self.max_x = 0.0
        self.min_y = self.max_y = 0.0
        self.min_z = self.max_z = 0.0

    def is_triangular(self) -> bool:
        """Return True when every face has exactly three vertices."""
        return all(len(face.vertex) == 3 for face in self.faces)

    def validate(self) -> None:
        """Validate indices and optional vertex attributes."""
        if self.colour and len(self.colour) != len(self.vertex):
            raise MeshValidationError("colour data must be empty or match vertex data")
        for face in self.faces:
            for name, values, limit in (
                ("vertex", face.vertex, len(self.vertex)),
                ("normal", face.normal, len(self.normals)),
                ("uv", face.uv, len(self.uv)),
            ):
                if name != "vertex" and not values:
                    continue
                if name == "vertex" and len(values) != 3:
                    raise MeshValidationError(
                        "faces must contain exactly three vertices"
                    )
                if name != "vertex" and len(values) != len(face.vertex):
                    raise MeshValidationError(f"face {name} indices must be complete")
                if any(index < 0 or index >= limit for index in values):
                    raise MeshValidationError(f"face {name} index is out of range")

    def calc_dimensions(self) -> None:
        """Calculate extents and bounding box from the vertex positions."""
        if not self.vertex:
            self.min_x = self.max_x = self.min_y = self.max_y = 0.0
            self.min_z = self.max_z = 0.0
            self.bbox = None
            return
        self.min_x = self.max_x = self.vertex[0].x
        self.min_y = self.max_y = self.vertex[0].y
        self.min_z = self.max_z = self.vertex[0].z
        for vertex in self.vertex[1:]:
            self.min_x, self.max_x = (
                min(self.min_x, vertex.x),
                max(self.max_x, vertex.x),
            )
            self.min_y, self.max_y = (
                min(self.min_y, vertex.y),
                max(self.max_y, vertex.y),
            )
            self.min_z, self.max_z = (
                min(self.min_z, vertex.z),
                max(self.max_z, vertex.z),
            )
        self.bbox = BBox.from_extents(
            self.min_x, self.max_x, self.min_y, self.max_y, self.min_z, self.max_z
        )

    def triangle_vertex_data(self, *, flip_v: bool = False) -> np.ndarray:
        """Pack expanded triangle data as position, normal and UV float32 values."""
        self.validate()
        if not self.faces:
            return np.empty(0, dtype=np.float32)
        data: list[float] = []
        for face in self.faces:
            for corner, vertex_index in enumerate(face.vertex):
                vertex = self.vertex[vertex_index]
                normal = self.normals[face.normal[corner]] if face.normal else Vec3()
                texcoord = self.uv[face.uv[corner]] if face.uv else Vec2()
                data.extend(
                    (
                        vertex.x,
                        vertex.y,
                        vertex.z,
                        normal.x,
                        normal.y,
                        normal.z,
                        texcoord.x,
                        1.0 - texcoord.y if flip_v else texcoord.y,
                    )
                )
        return np.ascontiguousarray(data, dtype=np.float32)
