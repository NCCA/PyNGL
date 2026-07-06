"""A VAO implementation that manages multiple vertex buffers."""

from typing import Any

import numpy as np
import OpenGL.GL as gl

from .abstract_vao import AbstractVAO, VertexData
from ..log import logger


class MultiBufferVAO(AbstractVAO):
    """A VAO implementation that can manage multiple vertex buffers.

    Useful for separating different types of vertex attributes (e.g.
    positions, colors, normals) into different buffers.
    """

    def __init__(self, mode: int = gl.GL_TRIANGLES) -> None:
        """Create the VAO with no buffers allocated yet."""
        super().__init__(mode)
        self.vbo_ids: list[int] = []

    def draw(self) -> None:
        """Draw the VAO's vertices using glDrawArrays."""
        if self.bound and self.allocated:
            gl.glDrawArrays(self.mode, 0, self.indices_count)
        else:
            logger.error("MultiBufferVAO is not bound or not allocated")

    def set_data(self, data: VertexData, index: int | None = None) -> None:
        """Upload vertex data to the buffer at index, creating buffers as needed.

        Args:
            data: The vertex data to upload.
            index: Buffer index to upload to; appends a new buffer if None.

        Raises:
            TypeError: If data is not a VertexData instance.
        """
        if not isinstance(data, VertexData):
            logger.error("MultiBufferVAO: Invalid data type")
            raise TypeError("data must be of type VertexData")
        if index is None:
            index = len(self.vbo_ids)

        if index >= len(self.vbo_ids):
            new_buffers = index - len(self.vbo_ids) + 1
            new_ids = gl.glGenBuffers(new_buffers)
            if isinstance(new_ids, np.ndarray):
                self.vbo_ids.extend(new_ids)
            else:
                self.vbo_ids.append(new_ids)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo_ids[index])
        gl.glBufferData(gl.GL_ARRAY_BUFFER, data.data.nbytes, data.data, data.mode)
        self.allocated = True
        if index == 0:  # Assume first buffer determines the number of indices
            self.indices_count = data.size

    def remove_vao(self) -> None:
        """Delete all of the VAO's buffers and its vertex array."""
        gl.glDeleteBuffers(len(self.vbo_ids), self.vbo_ids)
        gl.glDeleteVertexArrays(1, [self.id])

    def get_buffer_id(self, index: int = 0) -> int:
        """Return the OpenGL buffer id at the given index."""
        return self.vbo_ids[index]

    def map_buffer(self, index: int = 0, access_mode: int = gl.GL_READ_WRITE) -> Any:
        """Map the buffer at the given index into client memory."""
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo_ids[index])
        return gl.glMapBuffer(gl.GL_ARRAY_BUFFER, access_mode)
