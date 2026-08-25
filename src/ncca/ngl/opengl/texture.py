"""OpenGL texture creation from image files."""

from __future__ import annotations

import OpenGL.GL as gl

from ..image import Image


class Texture:
    """A texture class to load and create OpenGL textures."""

    def __init__(self, filename: str | None = None) -> None:
        """Create a texture, optionally loading an image file immediately."""
        self._image = Image(filename)
        self._texture_id = 0
        self._multi_texture_id = 0

    @property
    def width(self) -> int:
        """The texture image width in pixels."""
        return self._image.width

    @property
    def height(self) -> int:
        """The texture image height in pixels."""
        return self._image.height

    @property
    def format(self) -> int:
        """The OpenGL pixel format for the image mode, or 0 if unknown."""
        if self._image.mode:
            if self._image.mode.value == "RGB":
                return gl.GL_RGB
            elif self._image.mode.value == "RGBA":
                return gl.GL_RGBA
            elif self._image.mode.value == "L":
                return gl.GL_RED
        return 0

    @property
    def internal_format(self) -> int:
        """The OpenGL internal format for the image mode, or 0 if unknown."""
        if self._image.mode:
            if self._image.mode.value == "RGB":
                return gl.GL_RGB8
            elif self._image.mode.value == "RGBA":
                return gl.GL_RGBA8
            elif self._image.mode.value == "L":
                return gl.GL_R8
        return 0

    def load_image(self, filename: str) -> bool:
        """Load an image file; returns True on success."""
        return self._image.load(filename)

    def get_pixels(self) -> bytes:
        """Return the raw pixel data as bytes."""
        return self._image.get_pixels().tobytes()

    def set_texture_gl(self) -> int:
        """Generate a texture ID and set the texture parameters.

        Returns 0 (the OpenGL "not active" default) if the image is invalid.
        """
        if self._image.width > 0 and self._image.height > 0:
            self._texture_id = gl.glGenTextures(1)
            gl.glActiveTexture(gl.GL_TEXTURE0 + self._multi_texture_id)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self._texture_id)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexImage2D(
                gl.GL_TEXTURE_2D,
                0,
                self.internal_format,
                self.width,
                self.height,
                0,
                self.format,
                gl.GL_UNSIGNED_BYTE,
                self.get_pixels(),
            )
            gl.glGenerateMipmap(gl.GL_TEXTURE_2D)
        return self._texture_id

    def set_multi_texture(self, id: int) -> None:
        """Set the texture unit offset used when binding."""
        self._multi_texture_id = id
