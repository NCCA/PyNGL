"""A VAO implementation that uses an index buffer for indexed drawing."""

from typing import Any

import numpy as np
import OpenGL.GL as gl

from .abstract_vao import AbstractVAO, VertexData
from ..log import logger


class IndexVertexData(VertexData):
    """Vertex data paired with an index buffer for indexed drawing."""

    def __init__(
        self,
        data: np.ndarray | list[float],
        size: int,
        indices: np.ndarray | list[int],
        index_type: int,
        mode: int = gl.GL_STATIC_DRAW,
    ) -> None:
        """Store vertex data plus an index array of the given GL index type.

        Args:
            data: Vertex data, either a numpy array or a list of floats.
            size: Number of vertices represented by this data.
            indices: Index values referencing vertices in data.
            index_type: OpenGL index type (e.g. GL_UNSIGNED_INT).
            mode: OpenGL buffer usage hint (e.g. GL_STATIC_DRAW).

        Raises:
            TypeError: If index_type is not a supported GL index type.
        """
        super().__init__(data, size, mode)
        gl.GL_to_numpy_type = {
            gl.GL_UNSIGNED_INT: np.uint32,
            gl.GL_UNSIGNED_SHORT: np.uint16,
            gl.GL_UNSIGNED_BYTE: np.uint8,
        }
        numpy_dtype = gl.GL_to_numpy_type.get(index_type)
        if numpy_dtype is None:
            logger.error("SimpleIndexVAO: Unsupported index type")
            raise TypeError(f"Unsupported index type: {index_type}")

        self.indices = np.array(indices, dtype=numpy_dtype)
        self.index_type = index_type


class SimpleIndexVAO(AbstractVAO):
    """A VAO implementation that uses an index buffer for indexed drawing."""

    def __init__(self, mode: int = gl.GL_TRIANGLES) -> None:
        """Create the VAO and generate its vertex and index buffers."""
        super().__init__(mode)
        self.buffer = gl.glGenBuffers(1)
        self.idx_buffer = gl.glGenBuffers(1)
        self.index_type = gl.GL_UNSIGNED_INT

    def draw(self) -> None:
        """Draw the VAO's vertices using glDrawElements."""
        if self.bound and self.allocated:
            gl.glDrawElements(self.mode, self.indices_count, self.index_type, None)
        else:
            logger.error("SimpleIndexVAO not bound or not allocated")

    def set_data(self, data: IndexVertexData) -> None:
        """Upload vertex and index data to their respective buffers.

        Raises:
            TypeError: If data is not an IndexVertexData instance.
        """
        if not isinstance(data, IndexVertexData):
            logger.error("SimpleIndexVAO: Unsupported index type")
            raise TypeError("data must be of type IndexVertexData")

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.buffer)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, data.data.nbytes, data.data, data.mode)

        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.idx_buffer)
        gl.glBufferData(
            gl.GL_ELEMENT_ARRAY_BUFFER, data.indices.nbytes, data.indices, data.mode
        )

        self.allocated = True
        self.indices_count = len(data.indices)
        self.index_type = data.index_type

    def remove_vao(self) -> None:
        """Delete the VAO's vertex buffer, index buffer, and vertex array."""
        gl.glDeleteBuffers(1, [self.buffer])
        gl.glDeleteBuffers(1, [self.idx_buffer])
        gl.glDeleteVertexArrays(1, [self.id])

    def get_buffer_id(self, index: int = 0) -> int:
        """Return the OpenGL vertex buffer id (index is ignored)."""
        return self.buffer

    def map_buffer(self, index: int = 0, access_mode: int = gl.GL_READ_WRITE) -> Any:
        """Map the vertex buffer into client memory (index is ignored)."""
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.buffer)
        return gl.glMapBuffer(gl.GL_ARRAY_BUFFER, access_mode)
