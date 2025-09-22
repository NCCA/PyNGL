import numpy as np
import OpenGL.GL as gl

from .abstract_vao import AbstractVAO, VertexData
from .log import logger


class MultiBufferVAO(AbstractVAO):
    def __init__(self, mode=gl.GL_TRIANGLES):
        super().__init__(mode)
        self.vbo_ids = []

    def draw(self):
        if self.bound and self.allocated:
            gl.glDrawArrays(self.mode, 0, self.indices_count)
        else:
            logger.error("MultiBufferVAO is not bound or not allocated")

    def set_data(self, data, index=None):
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

    def remove_vao(self):
        gl.glDeleteBuffers(len(self.vbo_ids), self.vbo_ids)
        gl.glDeleteVertexArrays(1, [self.id])

    def get_buffer_id(self, index=0):
        return self.vbo_ids[index]

    def map_buffer(self, index=0, access_mode=gl.GL_READ_WRITE):
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo_ids[index])
        return gl.glMapBuffer(gl.GL_ARRAY_BUFFER, access_mode)
