import abc
import ctypes

import numpy as np
import OpenGL.GL as gl

from .log import logger


class VertexData:
    def __init__(self, data, size, mode=gl.GL_STATIC_DRAW):
        if isinstance(data, np.ndarray):
            self.data = data
        else:
            self.data = np.array(data, dtype=np.float32)
        self.size = size
        self.mode = mode


class AbstractVAO(abc.ABC):
    def __init__(self, mode=gl.GL_TRIANGLES):
        self.id = gl.glGenVertexArrays(1)
        self.mode = mode
        self.bound = False
        self.allocated = False
        self.indices_count = 0

    def bind(self):
        gl.glBindVertexArray(self.id)
        self.bound = True

    def unbind(self):
        gl.glBindVertexArray(0)
        self.bound = False

    def __enter__(self):
        self.bind()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unbind()

    @abc.abstractmethod
    def draw(self):
        raise NotImplementedError

    @abc.abstractmethod
    def set_data(self, data):
        raise NotImplementedError

    @abc.abstractmethod
    def remove_vao(self):
        raise NotImplementedError

    def set_vertex_attribute_pointer(self, id, size, type, stride, offset, normalize=False):
        if not self.bound:
            logger.error("VAO not bound in set_vertex_attribute_pointer")
        gl.glVertexAttribPointer(id, size, type, normalize, stride, ctypes.c_void_p(offset))
        gl.glEnableVertexAttribArray(id)

    def set_num_indices(self, count):
        self.indices_count = count

    def num_indices(self):
        return self.indices_count

    def get_mode(self):
        return self.mode

    def set_mode(self, mode):
        self.mode = mode

    @abc.abstractmethod
    def get_buffer_id(self, index=0):
        raise NotImplementedError

    @abc.abstractmethod
    def map_buffer(self, index=0, access_mode=gl.GL_READ_WRITE):
        raise NotImplementedError

    def unmap_buffer(self):
        gl.glUnmapBuffer(gl.GL_ARRAY_BUFFER)

    def get_id(self):
        return self.id
