from dataclasses import dataclass

import numpy as np
import OpenGL.GL as gl

from . import vao_factory
from .abstract_vao import VertexData
from .bbox import BBox
from .log import logger


class Face:
    """
    Simple face structure for mesh geometry.
    Holds indices for vertices, UVs, and normals.
    """

    slots = ("vertex", "uv", "normal")

    def __init__(self):
        self.vertex: list[int] = []
        self.uv: list[int] = []
        self.normal: list[int] = []


class BaseMesh:
    """
    Base class for mesh geometry.
    Provides storage for vertices, normals, UVs, faces, and VAO management.
    """

    def __init__(self):
        self.vertex: list = []
        self.normals: list = []
        self.uv: list = []
        self.faces: list[Face] = []
        self.vao = None
        self.bbox = None
        self.min_x: float = 0.0
        self.max_x: float = 0.0
        self.min_y: float = 0.0
        self.max_y: float = 0.0
        self.min_z: float = 0.0
        self.max_z: float = 0.0
        self.texture_id: int = 0
        self.texture: bool = False

    def is_triangular(self) -> bool:
        """
        Check if all faces in the mesh are triangles.

        Returns:
            bool: True if all faces are triangles, False otherwise.
        """
        return all(len(f.vertex) == 3 for f in self.faces)

    def create_vao(self, reset_vao: bool = False) -> None:
        """
        Create a Vertex Array Object (VAO) for the mesh.
        Only supports triangular meshes.

        Args:
            reset_vao: If True, will not create a new VAO if one already exists.
        Raises:
            RuntimeError: If the mesh is not composed entirely of triangles.
        """
        if reset_vao:
            if self.vao is not None:
                logger.warning("VAO exist so returning")
                return
        else:
            if self.vao is not None:
                logger.warning("Creating new VAO")

        data_pack_type = 0
        if self.is_triangular():
            data_pack_type = gl.GL_TRIANGLES
        if data_pack_type == 0:
            logger.error("Can only create VBO from all Triangle data at present")
            raise RuntimeError("Can only create VBO from all Triangle data at present")

        @dataclass
        class VertData:
            """
            Structure for a single vertex's data, including position, normal, and UV.
            """

            x: float = 0.0
            y: float = 0.0
            z: float = 0.0
            nx: float = 0.0
            ny: float = 0.0
            nz: float = 0.0
            u: float = 0.0
            v: float = 0.0

            def as_array(self) -> np.ndarray:
                return np.array(
                    [self.x, self.y, self.z, self.nx, self.ny, self.nz, self.u, self.v],
                    dtype=np.float32,
                )

        vbo_mesh: list[VertData] = []
        for face in self.faces:
            for i in range(3):
                d = VertData()
                d.x = self.vertex[face.vertex[i]].x
                d.y = self.vertex[face.vertex[i]].y
                d.z = self.vertex[face.vertex[i]].z
                if self.normals and self.uv:
                    d.nx = self.normals[face.normal[i]].x
                    d.ny = self.normals[face.normal[i]].y
                    d.nz = self.normals[face.normal[i]].z
                    d.u = self.uv[face.uv[i]].x
                    d.v = 1 - self.uv[face.uv[i]].y  # Flip V for OpenGL
                elif self.normals and not self.uv:
                    d.nx = self.normals[face.normal[i]].x
                    d.ny = self.normals[face.normal[i]].y
                    d.nz = self.normals[face.normal[i]].z
                elif not self.normals and self.uv:
                    d.u = self.uv[face.uv[i]].x
                    d.v = 1 - self.uv[face.uv[i]].y
                vbo_mesh.append(d)

        mesh_data = np.concatenate([v.as_array() for v in vbo_mesh]).astype(np.float32)
        self.vao = vao_factory.VAOFactory.create_vao(
            vao_factory.VAOType.SIMPLE, data_pack_type
        )
        with self.vao as vao:
            mesh_size = len(mesh_data) // 8
            vao.set_data(VertexData(mesh_data, mesh_size))
            # vertex
            vao.set_vertex_attribute_pointer(0, 3, gl.GL_FLOAT, 8 * 4, 0)
            # normals
            vao.set_vertex_attribute_pointer(1, 3, gl.GL_FLOAT, 8 * 4, 3 * 4)
            # uvs
            vao.set_vertex_attribute_pointer(2, 2, gl.GL_FLOAT, 8 * 4, 6 * 4)
            vao.set_num_indices(mesh_size)
        self.calc_dimensions()
        self.bbox = BBox.from_extents(
            self.min_x, self.max_x, self.min_y, self.max_y, self.min_z, self.max_z
        )

    def calc_dimensions(self) -> None:
        """
        Calculate the bounding box extents for the mesh.
        Updates min_x, max_x, min_y, max_y, min_z, max_z.
        """
        if not self.vertex:
            return
        self.min_x = self.max_x = self.vertex[0].x
        self.min_y = self.max_y = self.vertex[0].y
        self.min_z = self.max_z = self.vertex[0].z
        for v in self.vertex:
            self.min_x = min(self.min_x, v.x)
            self.max_x = max(self.max_x, v.x)
            self.min_y = min(self.min_y, v.y)
            self.max_y = max(self.max_y, v.y)
            self.min_z = min(self.min_z, v.z)
            self.max_z = max(self.max_z, v.z)

    def draw(self) -> None:
        """
        Draw the mesh using its VAO and bound texture (if any).
        """
        if self.vao:
            if self.texture_id:
                gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)
            with self.vao as vao:
                vao.draw()
