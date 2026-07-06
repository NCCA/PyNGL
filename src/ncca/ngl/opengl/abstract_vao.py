"""Abstract base class and data container for Vertex Array Object (VAO) implementations."""

import abc
import ctypes
from typing import Any

import numpy as np
import OpenGL.GL as gl

from ..log import logger


class VertexData:
    """A simple data structure to hold vertex data for a VAO."""

    def __init__(
        self, data: np.ndarray | list[float], size: int, mode: int = gl.GL_STATIC_DRAW
    ) -> None:
        """Store vertex data as a float32 numpy array along with its size and draw mode.

        Args:
            data: Vertex data, either a numpy array or a list of floats.
            size: Number of vertices represented by this data.
            mode: OpenGL buffer usage hint (e.g. GL_STATIC_DRAW).
        """
        if isinstance(data, np.ndarray):
            self.data = data
        else:
            self.data = np.array(data, dtype=np.float32)
        self.size = size
        self.mode = mode


class AbstractVAO(abc.ABC):
    """Abstract base class for Vertex Array Objects (VAOs).

    Defines the interface for different VAO implementations, including
    methods for binding, drawing, setting data, and managing the VAO's
    lifecycle.
    """

    def __init__(self, mode: int = gl.GL_TRIANGLES) -> None:
        """Generate a new OpenGL VAO id and initialize default state.

        Args:
            mode: OpenGL primitive drawing mode (e.g. GL_TRIANGLES).
        """
        self.id = gl.glGenVertexArrays(1)
        self.mode = mode
        self.bound = False
        self.allocated = False
        self.indices_count = 0

    def bind(self) -> None:
        """Bind this VAO as the current OpenGL vertex array."""
        gl.glBindVertexArray(self.id)
        self.bound = True

    def unbind(self) -> None:
        """Unbind the current OpenGL vertex array."""
        gl.glBindVertexArray(0)
        self.bound = False

    def __enter__(self) -> "AbstractVAO":
        """Bind the VAO on entering a `with` block."""
        self.bind()
        return self

    def __exit__(self, exc_type: type, exc_val: BaseException, exc_tb: Any) -> None:
        """Unbind the VAO on exiting a `with` block."""
        self.unbind()

    @abc.abstractmethod
    def draw(self) -> None:
        """Draw the contents of this VAO."""
        raise NotImplementedError

    @abc.abstractmethod
    def set_data(self, data: VertexData) -> None:
        """Upload vertex data to the VAO's buffer(s)."""
        raise NotImplementedError

    @abc.abstractmethod
    def remove_vao(self) -> None:
        """Delete the VAO and its associated buffers."""
        raise NotImplementedError

    def set_vertex_attribute_pointer(
        self,
        id: int,
        size: int,
        type: int,
        stride: int,
        offset: int,
        normalize: bool = False,
    ) -> None:
        """Configure and enable a vertex attribute pointer for the bound buffer.

        Args:
            id: Attribute location index.
            size: Number of components per vertex attribute.
            type: OpenGL data type of each component (e.g. GL_FLOAT).
            stride: Byte offset between consecutive vertex attributes.
            offset: Byte offset of the first component in the buffer.
            normalize: Whether integer data should be normalized.
        """
        if not self.bound:
            logger.error("VAO not bound in set_vertex_attribute_pointer")
        gl.glVertexAttribPointer(
            id, size, type, normalize, stride, ctypes.c_void_p(offset)
        )
        gl.glEnableVertexAttribArray(id)

    def set_num_indices(self, count: int) -> None:
        """Set the number of indices/vertices to draw."""
        self.indices_count = count

    def num_indices(self) -> int:
        """Return the number of indices/vertices to draw."""
        return self.indices_count

    def get_mode(self) -> int:
        """Return the OpenGL primitive drawing mode."""
        return self.mode

    def set_mode(self, mode: int) -> None:
        """Set the OpenGL primitive drawing mode."""
        self.mode = mode

    @abc.abstractmethod
    def get_buffer_id(self, index: int = 0) -> int:
        """Return the OpenGL buffer id at the given index."""
        raise NotImplementedError

    @abc.abstractmethod
    def map_buffer(self, index: int = 0, access_mode: int = gl.GL_READ_WRITE) -> Any:
        """Map the buffer at the given index into client memory."""
        raise NotImplementedError

    def unmap_buffer(self) -> None:
        """Unmap the currently mapped GL_ARRAY_BUFFER."""
        gl.glUnmapBuffer(gl.GL_ARRAY_BUFFER)

    def get_id(self) -> int:
        """Return the OpenGL VAO id."""
        return self.id
