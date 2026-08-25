"""OpenGL renderer for backend-neutral mesh data."""

import OpenGL.GL as gl

from ..mesh import MeshData
from .abstract_vao import AbstractVAO, VertexData
from .vao_factory import VAOFactory, VAOType


class OpenGLMesh:
    """Upload and draw a MeshData instance with an OpenGL VAO."""

    def __init__(self, mesh: MeshData, *, texture_id: int = 0) -> None:
        """Store the CPU mesh and an optional borrowed texture ID."""
        self.mesh = mesh
        self.texture_id = texture_id
        self._vao: AbstractVAO | None = None

    @property
    def vao(self) -> AbstractVAO | None:
        """Return the VAO after upload."""
        return self._vao

    def upload(self, *, force: bool = False) -> None:
        """Create the VAO, replacing an existing one only when requested."""
        if self._vao is not None and not force:
            return
        if self._vao is not None:
            self.cleanup()
        data = self.mesh.triangle_vertex_data(flip_v=True)
        if not data.size:
            raise RuntimeError("cannot upload an empty mesh")
        self._vao = VAOFactory.create_vao(VAOType.SIMPLE, gl.GL_TRIANGLES)
        with self._vao as vao:
            count = data.size // 8
            vao.set_data(VertexData(data, count))
            vao.set_vertex_attribute_pointer(0, 3, gl.GL_FLOAT, 32, 0)
            vao.set_vertex_attribute_pointer(1, 3, gl.GL_FLOAT, 32, 12)
            vao.set_vertex_attribute_pointer(2, 2, gl.GL_FLOAT, 32, 24)
            vao.set_num_indices(count)
        self.mesh.calc_dimensions()

    def draw(self) -> None:
        """Draw the uploaded mesh."""
        if self._vao is None:
            raise RuntimeError("mesh must be uploaded before drawing")
        if self.texture_id:
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)
        with self._vao as vao:
            vao.draw()

    def cleanup(self) -> None:
        """Release the VAO whilst an OpenGL context is current."""
        if self._vao is not None:
            self._vao.remove_vao()
            self._vao = None
