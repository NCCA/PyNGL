import numpy as np
import OpenGL.GL as gl

from .abstract_vao import AbstractVAO, VertexData
from .log import logger


class IndexVertexData(VertexData):
    def __init__(self, data, size, indices, index_type, mode=gl.GL_STATIC_DRAW):
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
    def __init__(self, mode=gl.GL_TRIANGLES):
        super().__init__(mode)
        self.buffer = gl.glGenBuffers(1)
        self.idx_buffer = gl.glGenBuffers(1)
        self.index_type = gl.GL_UNSIGNED_INT

    def draw(self):
        if self.bound and self.allocated:
            gl.glDrawElements(self.mode, self.indices_count, self.index_type, None)
        else:
            logger.error("SimpleIndexVAO not bound or not allocated")

    def set_data(self, data):
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

    def remove_vao(self):
        gl.glDeleteBuffers(1, [self.buffer])
        gl.glDeleteBuffers(1, [self.idx_buffer])
        gl.glDeleteVertexArrays(1, [self.id])

    def get_buffer_id(self, index=0):
        return self.buffer

    def map_buffer(self, index=0, access_mode=gl.GL_READ_WRITE):
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.buffer)
        return gl.glMapBuffer(gl.GL_ARRAY_BUFFER, access_mode)
