import OpenGL.GL as gl

from .abstract_vao import AbstractVAO, VertexData
from .log import logger


class SimpleVAO(AbstractVAO):
    def __init__(self, mode=gl.GL_TRIANGLES):
        super().__init__(mode)
        self.buffer = gl.glGenBuffers(1)

    def draw(self):
        if self.bound and self.allocated:
            gl.glDrawArrays(self.mode, 0, self.indices_count)
        else:
            logger.error("SimpleVAO not bound or not allocated")

    def set_data(self, data):
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

    def num_indices(self):
        return self.indices_count

    def remove_vao(self):
        gl.glDeleteBuffers(1, [self.buffer])
        gl.glDeleteVertexArrays(1, [self.id])

    def get_buffer_id(self, index=0):
        return self.buffer

    def map_buffer(self, index=0, access_mode=gl.GL_READ_WRITE):
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.buffer)
        return gl.glMapBuffer(gl.GL_ARRAY_BUFFER, access_mode)
