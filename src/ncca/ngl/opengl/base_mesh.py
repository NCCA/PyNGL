"""Compatibility mesh class for existing OpenGL applications."""

from ..log import logger
from ..mesh import Face as CoreFace
from ..mesh import MeshData
from .abstract_vao import AbstractVAO
from .mesh import OpenGLMesh

Face = CoreFace


class BaseMesh(MeshData):
    """MeshData with the legacy OpenGL drawing API."""

    def __init__(self) -> None:
        """Create an empty mesh with a legacy OpenGL renderer."""
        super().__init__()
        self.texture_id = 0
        self.texture = False
        self._renderer = OpenGLMesh(self)

    @property
    def vao(self) -> AbstractVAO | None:
        """Return the VAO owned by the compatibility renderer."""
        return self._renderer.vao

    def _should_skip_vao_creation(self, reset_vao: bool) -> bool:
        if self.vao is None:
            return False
        if reset_vao:
            logger.warning("VAO exists so returning")
            return True
        logger.warning("Creating new VAO")
        return False

    def _validate_triangular_mesh(self) -> None:
        if not self.is_triangular():
            raise RuntimeError("Can only create VBO from all Triangle data at present")

    def create_vao(self, reset_vao: bool = False) -> None:
        """Create the legacy VAO using the OpenGLMesh adapter."""
        if self._should_skip_vao_creation(reset_vao):
            return
        self._validate_triangular_mesh()
        self._renderer.texture_id = self.texture_id
        self._renderer.upload(force=self.vao is not None)

    def draw(self) -> None:
        """Draw if the VAO has been created, matching the old no-op behaviour."""
        if self.vao is not None:
            self._renderer.texture_id = self.texture_id
            self._renderer.draw()
