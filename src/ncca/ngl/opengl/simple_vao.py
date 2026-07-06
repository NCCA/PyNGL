"""A basic VAO implementation using a single buffer for non-indexed drawing."""

from typing import Any

import OpenGL.GL as gl

from .abstract_vao import AbstractVAO, VertexData
from ..log import logger


class SimpleVAO(AbstractVAO):
    """A basic VAO implementation that uses a single buffer for non-indexed drawing."""

    def __init__(self, mode: int = gl.GL_TRIANGLES) -> None:
        """Create the VAO and generate its single vertex buffer."""
        super().__init__(mode)
        self.buffer = gl.glGenBuffers(1)

    def draw(self) -> None:
        """Draw the VAO's vertices using glDrawArrays."""
        if self.bound and self.allocated:
            gl.glDrawArrays(self.mode, 0, self.indices_count)
        else:
            logger.error("SimpleVAO not bound or not allocated")

    def set_data(self, data: VertexData) -> None:
        """Upload vertex data to the buffer.

        Raises:
            TypeError: If data is not a VertexData instance.
            RuntimeError: If the VAO is not currently bound.
        """
        if not isinstance(data, VertexData):
            logger.error("SimpleVAO: Invalid data type")
            raise TypeError("data must be of type VertexData")
        if not self.bound:
            logger.error("SimpleVAO not bound")
            raise RuntimeError("SimpleVAO not bound")
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.buffer)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, data.data.nbytes, data.data, data.mode)
        self.allocated = True
        self.indices_count = data.size

    def num_indices(self) -> int:
        """Return the number of vertices to draw."""
        return self.indices_count

    def remove_vao(self) -> None:
        """Delete the VAO's buffer and vertex array."""
        gl.glDeleteBuffers(1, [self.buffer])
        gl.glDeleteVertexArrays(1, [self.id])

    def get_buffer_id(self, index: int = 0) -> int:
        """Return the OpenGL buffer id (index is ignored, only one buffer)."""
        return self.buffer

    def map_buffer(self, index: int = 0, access_mode: int = gl.GL_READ_WRITE) -> Any:
        """Map the buffer into client memory (index is ignored, only one buffer)."""
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.buffer)
        return gl.glMapBuffer(gl.GL_ARRAY_BUFFER, access_mode)
