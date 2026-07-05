from __future__ import annotations

from enum import Enum

import OpenGL.GL as gl

from ..log import logger


class ShaderType(Enum):
    """
    Enum representing the different types of OpenGL shaders.
    """

    VERTEX = gl.GL_VERTEX_SHADER
    FRAGMENT = gl.GL_FRAGMENT_SHADER
    GEOMETRY = gl.GL_GEOMETRY_SHADER
    TESSCONTROL = gl.GL_TESS_CONTROL_SHADER
    TESSEVAL = gl.GL_TESS_EVALUATION_SHADER
    COMPUTE = gl.GL_COMPUTE_SHADER
    NONE = -1


class MatrixTranspose(Enum):
    """
    Enum for matrix transpose options (currently both set to GL_TRUE).
    """

    TransposeOn = gl.GL_TRUE
    TransposeOff = gl.GL_TRUE


class Shader:
    """
    Class representing an OpenGL shader object.
    Handles loading, compiling, and editing shader source code.
    """

    def __init__(self, name: str, type: int, exit_on_error: bool = True):
        """
        Initialize a Shader object.

        Args:
            name: Name of the shader (for logging/debugging).
            type: OpenGL shader type (e.g., gl.GL_VERTEX_SHADER).
            exit_on_error: Whether to exit the program on compilation error.
        """
        self._name: str = name
        self._type: int = type
        self._exit_on_error: bool = exit_on_error
        self._id: int = gl.glCreateShader(type)
        self._source: str = ""

    def load(self, source_file: str) -> None:
        """
        Load shader source code from a file and set it for this shader.

        Args:
            source_file: Path to the shader source file.
        """
        with open(source_file, "r") as f:
            self._source = f.read()
        gl.glShaderSource(self._id, self._source)

    def compile(self) -> bool:
        """
        Compile the shader source code.

        Returns:
            bool: True if compilation succeeded, False otherwise.
        """
        gl.glCompileShader(self._id)
        if gl.glGetShaderiv(self._id, gl.GL_COMPILE_STATUS) != gl.GL_TRUE:
            info = gl.glGetShaderInfoLog(self._id)
            logger.error(f"Error compiling shader {self._name=}: {info=}")
            if self._exit_on_error:
                exit()
            return False
        return True

    def edit_shader(self, to_find: str, replace_with: str) -> bool:
        """
        Edit the shader source code by replacing a substring and update the shader.

        Args:
            to_find: Substring to find in the shader source.
            replace_with: Substring to replace with.

        Returns:
            bool: True if the edit was successful, False otherwise.
        """
        if self._source:
            self._source = self._source.replace(to_find, replace_with)
            gl.glShaderSource(self._id, self._source)
            return True
        return False

    def reset_edits(self) -> None:
        """
        Reset the shader source code to the current stored source.
        """
        if self._source:
            gl.glShaderSource(self._id, self._source)

    def load_shader_source_from_string(self, shader_source: str) -> None:
        """
        Load shader source code from a string and set it for this shader.

        Args:
            shader_source: Shader source code as a string.
        """
        self._source = shader_source
        gl.glShaderSource(self._id, self._source)
