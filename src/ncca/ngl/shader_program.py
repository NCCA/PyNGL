import ctypes
from typing import Any, Dict, List, Optional, Union

import numpy as np
import OpenGL.GL as gl

from .log import logger
from .mat2 import Mat2
from .mat3 import Mat3
from .mat4 import Mat4
from .shader import Shader
from .vec2 import Vec2
from .vec3 import Vec3
from .vec4 import Vec4


class ShaderProgram:
    """
    A wrapper class for OpenGL shader programs.

    This class provides functionality to create, link, and manage OpenGL shader programs,
    including automatic uniform and uniform block registration, and convenience methods
    for setting uniform values.

    Attributes:
        _name: The name of the shader program
        _exit_on_error: Whether to exit the application on errors
        _id: The OpenGL shader program ID
        _shaders: List of attached shaders
        _uniforms: Dictionary of registered uniforms
        _registered_uniform_blocks: Dictionary of registered uniform blocks
    """

    def __init__(self, name: str, exit_on_error: bool = True) -> None:
        """
        Initialize a new shader program.

        Args:
            name: Name of the shader program for identification
            exit_on_error: Whether to exit the application when errors occur
        """
        self._name: str = name
        self._exit_on_error: bool = exit_on_error
        self._id: int = gl.glCreateProgram()
        self._shaders: list[Shader] = []
        self._uniforms: dict[str, tuple[int, int, int, bool]] = {}
        self._registered_uniform_blocks: dict[str, dict] = {}

    def attach_shader(self, shader: Shader) -> None:
        """
        Attach a shader to this program.

        Args:
            shader: The Shader object to attach
        """
        gl.glAttachShader(self._id, shader._id)
        self._shaders.append(shader)

    def link(self) -> bool:
        """
        Link the attached shaders to create the final shader program.

        Returns:
            bool: True if linking succeeded, False otherwise.
        """
        gl.glLinkProgram(self._id)
        if gl.glGetProgramiv(self._id, gl.GL_LINK_STATUS) != gl.GL_TRUE:
            info = gl.glGetProgramInfoLog(self._id)
            logger.error(f"Error linking program {self._name}: {info}")
            if self._exit_on_error:
                exit()
            return False
        # Automatically register uniforms and uniform blocks after linking
        self.auto_register_uniforms()
        self.auto_register_uniform_blocks()
        return True

    def auto_register_uniforms(self) -> None:
        """
        Automatically register all active uniforms in the shader program.

        This method queries OpenGL for all active uniforms and stores their
        information including location, type, size, and array status.
        For array uniforms, it also registers individual array elements.
        """
        uniform_count = gl.glGetProgramiv(self._id, gl.GL_ACTIVE_UNIFORMS)
        for i in range(uniform_count):
            name, size, shader_type = gl.glGetActiveUniform(self._id, i, 256)

            # Convert name to string
            name_str = name.decode("utf-8") if isinstance(name, bytes) else name

            # Handle array uniforms - OpenGL returns name with [0] for arrays
            is_array = size > 1
            base_name = name_str
            if name_str.endswith("[0]"):
                base_name = name_str[:-3]

            location = gl.glGetUniformLocation(self._id, name)

            # Store uniform info: (location, shader_type, size, is_array)
            self._uniforms[base_name] = (location, shader_type, size, is_array)

            # For arrays, also register individual elements
            if is_array:
                for element_idx in range(size):
                    element_name = f"{base_name}[{element_idx}]"
                    element_location = gl.glGetUniformLocation(
                        self._id, element_name.encode("utf-8")
                    )
                    if element_location != -1:
                        # Store individual array element: (location, shader_type, 1, False)
                        self._uniforms[element_name] = (
                            element_location,
                            shader_type,
                            1,
                            False,
                        )

            # Log array uniforms differently
            if is_array:
                logger.info(
                    f"Registered array uniform: {base_name}[{size}] (type: {self.get_gl_type_string(shader_type)}, location: {location})"
                )
                logger.info(
                    f"  Also registered individual elements: {base_name}[0] to {base_name}[{size - 1}]"
                )
            else:
                logger.info(
                    f"Registered uniform: {base_name} (type: {self.get_gl_type_string(shader_type)}, location: {location})"
                )

    def auto_register_uniform_blocks(self) -> None:
        """
        Automatically register uniform blocks for this shader program.
        This is the Python equivalent of the C++ ShaderProgram::autoRegisterUniformBlocks method.
        """
        # Clear existing uniform blocks
        self._registered_uniform_blocks.clear()

        # Get number of active uniform blocks
        n_uniforms = gl.glGetProgramiv(self._id, gl.GL_ACTIVE_UNIFORM_BLOCKS)
        logger.info(f"FOUND UNIFORM BLOCKS {n_uniforms}")

        for i in range(n_uniforms):
            # Get uniform block name using ctypes buffer
            name_buffer = (ctypes.c_char * 256)()
            length = ctypes.c_int()

            gl.glGetActiveUniformBlockName(
                self._id, i, 256, ctypes.byref(length), name_buffer
            )
            name_str = (
                name_buffer.value.decode("utf-8")
                if name_buffer.value
                else f"UniformBlock_{i}"
            )

            # Create uniform block data structure
            data = {
                "name": name_str,
                "loc": gl.glGetUniformBlockIndex(self._id, name_str.encode("utf-8")),
                "buffer": gl.glGenBuffers(1),
            }

            # Store the uniform block data
            self._registered_uniform_blocks[name_str] = data
            logger.info(f"Uniform Block {name_str} {data['loc']} {data['buffer']}")

    def use(self) -> None:
        """
        Set this shader program as the current active program.
        """
        gl.glUseProgram(self._id)

    def get_id(self) -> int:
        """
        Get the OpenGL shader program ID.

        Returns:
            int: The OpenGL program ID
        """
        return self._id

    def get_uniform_location(self, name: str) -> int:
        """
        Get the location of a uniform variable.

        Args:
            name: The name of the uniform variable

        Returns:
            int: The uniform location, or -1 if not found
        """
        if name in self._uniforms:
            return self._uniforms[name][0]
        else:
            logger.warning(f"Uniform '{name}' not found in shader '{self._name}'")
            return -1

    def get_uniform_info(self, name: str) -> tuple[int, int, int, bool]:
        """
        Get complete uniform info: (location, shader_type, size, is_array).

        Args:
            name: The name of the uniform variable

        Returns:
            tuple: (location, shader_type, size, is_array)
        """
        return self._uniforms.get(name, (-1, 0, 0, False))

    def is_uniform_array(self, name: str) -> bool:
        """
        Check if a uniform is an array.

        Args:
            name: The name of the uniform variable

        Returns:
            bool: True if the uniform is an array, False otherwise
        """
        if name in self._uniforms:
            return self._uniforms[name][3]
        return False

    def get_uniform_array_size(self, name: str) -> int:
        """
        Get the size of a uniform array, returns 1 for non-arrays.

        Args:
            name: The name of the uniform variable

        Returns:
            int: The array size, or 0 if uniform not found
        """
        if name in self._uniforms:
            return self._uniforms[name][2]
        return 0

    def set_uniform_buffer(self, uniform_block_name: str, size: int, data) -> bool:
        """
        Set uniform buffer data for the specified uniform block.
        This is the Python equivalent of the C++ ShaderProgram::setUniformBuffer method.

        Args:
            uniform_block_name: Name of the uniform block
            size: Size of the data in bytes
            data: Data to upload (can be ctypes array, bytes, or buffer-like object)

        Returns:
            bool: True if successful, False otherwise
        """
        if uniform_block_name not in self._registered_uniform_blocks:
            logger.error(
                f"Uniform block '{uniform_block_name}' not found in shader '{self._name}'"
            )
            return False

        block = self._registered_uniform_blocks[uniform_block_name]

        try:
            # Bind the uniform buffer
            gl.glBindBuffer(gl.GL_UNIFORM_BUFFER, block["buffer"])

            # Upload the data
            data = np.frombuffer(data, dtype=np.float32)
            gl.glBufferData(gl.GL_UNIFORM_BUFFER, size, data, gl.GL_DYNAMIC_DRAW)

            # Bind the buffer to the uniform block binding point
            gl.glBindBufferBase(gl.GL_UNIFORM_BUFFER, block["loc"], block["buffer"])

            # Unbind the buffer
            gl.glBindBuffer(gl.GL_UNIFORM_BUFFER, 0)

            return True

        except Exception as e:
            logger.error(f"Failed to set uniform buffer '{uniform_block_name}': {e}")
            return False

    def set_uniform(self, name: str, *value: Any) -> None:
        """
        Set a uniform variable value.

        This method automatically detects the type of the value and calls the
        appropriate OpenGL uniform function. Supports scalars, vectors, matrices,
        and custom vector/matrix types.

        Args:
            name: The name of the uniform variable
            *value: The value(s) to set
        """
        loc = self.get_uniform_location(name)
        if loc == -1:
            logger.warning(f"Uniform location not found for '{name}'")
            return

        # Get uniform info for better type handling
        uniform_info = self.get_uniform_info(name)
        _, uniform_type, array_size, is_array = uniform_info

        if len(value) == 1:
            val = value[0]
            if isinstance(val, int):
                gl.glUniform1i(loc, val)
            elif isinstance(val, float):
                gl.glUniform1f(loc, val)
            elif isinstance(val, Mat2):
                gl.glUniformMatrix2fv(
                    loc, 1, gl.GL_FALSE, (ctypes.c_float * 4)(*val.get_matrix())
                )
            elif isinstance(val, Mat3):
                gl.glUniformMatrix3fv(
                    loc, 1, gl.GL_FALSE, (ctypes.c_float * 9)(*val.get_matrix())
                )
            elif isinstance(val, Mat4):
                gl.glUniformMatrix4fv(
                    loc, 1, gl.GL_FALSE, (ctypes.c_float * 16)(*val.get_matrix())
                )
            elif isinstance(val, Vec2):
                gl.glUniform2f(loc, *val)
            elif isinstance(val, Vec3):
                gl.glUniform3f(loc, *val)
            elif isinstance(val, Vec4):
                gl.glUniform4f(loc, *val)
            else:
                try:
                    val = list(value[0])
                    if len(val) == 4:
                        gl.glUniformMatrix2fv(
                            loc, 1, gl.GL_FALSE, (ctypes.c_float * 4)(*val)
                        )
                    elif len(val) == 9:
                        gl.glUniformMatrix3fv(
                            loc, 1, gl.GL_FALSE, (ctypes.c_float * 9)(*val)
                        )
                    elif len(val) == 16:
                        gl.glUniformMatrix4fv(
                            loc, 1, gl.GL_FALSE, (ctypes.c_float * 16)(*val)
                        )
                except TypeError:
                    logger.warning(
                        f"Warning: uniform '{name}' has unknown type: {type(val)}"
                    )

        elif len(value) == 2:
            if isinstance(value[0], int):
                gl.glUniform2i(loc, *value)
            else:
                gl.glUniform2f(loc, *value)
        elif len(value) == 3:
            if isinstance(value[0], int):
                gl.glUniform3i(loc, *value)
            else:
                gl.glUniform3f(loc, *value)
        elif len(value) == 4:
            if isinstance(value[0], int):
                gl.glUniform4i(loc, *value)
            else:
                gl.glUniform4f(loc, *value)

    def set_uniform_1fv(self, name: str, values: List[float]) -> None:
        """
        Set a float array uniform.

        Args:
            name: The name of the uniform variable
            values: List of float values
        """
        """Set a float array uniform"""
        loc = self.get_uniform_location(name)
        if loc != -1:
            gl.glUniform1fv(loc, len(values), (ctypes.c_float * len(values))(*values))

    def set_uniform_2fv(self, name: str, values: List[List[float]]) -> None:
        """
        Set a vec2 array uniform.

        Args:
            name: The name of the uniform variable
            values: List of vec2 values (each as a list of 2 floats)
        """
        """Set a vec2 array uniform"""
        loc = self.get_uniform_location(name)
        if loc != -1:
            flat_values = [item for vec in values for item in vec]
            gl.glUniform2fv(
                loc, len(values), (ctypes.c_float * len(flat_values))(*flat_values)
            )

    def set_uniform_3fv(self, name: str, values: List[List[float]]) -> None:
        """
        Set a vec3 array uniform.

        Args:
            name: The name of the uniform variable
            values: List of vec3 values (each as a list of 3 floats)
        """
        """Set a vec3 array uniform"""
        loc = self.get_uniform_location(name)
        if loc != -1:
            flat_values = [item for vec in values for item in vec]
            gl.glUniform3fv(
                loc, len(values), (ctypes.c_float * len(flat_values))(*flat_values)
            )

    def set_uniform_4fv(self, name: str, values: List[List[float]]) -> None:
        """
        Set a vec4 array uniform.

        Args:
            name: The name of the uniform variable
            values: List of vec4 values (each as a list of 4 floats)
        """
        """Set a vec4 array uniform"""
        loc = self.get_uniform_location(name)
        if loc != -1:
            flat_values = [item for vec in values for item in vec]
            gl.glUniform4fv(
                loc, len(values), (ctypes.c_float * len(flat_values))(*flat_values)
            )

    def set_uniform_1iv(self, name: str, values: List[int]) -> None:
        """
        Set an int array uniform.

        Args:
            name: The name of the uniform variable
            values: List of integer values
        """
        """Set an int array uniform"""
        loc = self.get_uniform_location(name)
        if loc != -1:
            gl.glUniform1iv(loc, len(values), (ctypes.c_int * len(values))(*values))

    def set_uniform_matrix2fv(
        self,
        name: str,
        matrices: List[Union[Mat2, List[float]]],
        transpose: bool = False,
    ) -> None:
        """
        Set a mat2 array uniform.

        Args:
            name: The name of the uniform variable
            matrices: List of 2x2 matrices (Mat2 objects or lists of 4 floats)
            transpose: Whether to transpose the matrices
        """
        """Set a mat2 array uniform"""
        loc = self.get_uniform_location(name)
        if loc != -1:
            flat_values = []
            for matrix in matrices:
                if hasattr(matrix, "get_matrix"):
                    flat_values.extend(matrix.get_matrix())
                else:
                    flat_values.extend(matrix)
            gl.glUniformMatrix2fv(
                loc,
                len(matrices),
                gl.GL_TRUE if transpose else gl.GL_FALSE,
                (ctypes.c_float * len(flat_values))(*flat_values),
            )

    def set_uniform_matrix3fv(
        self,
        name: str,
        matrices: List[Union[Mat3, List[float]]],
        transpose: bool = False,
    ) -> None:
        """
        Set a mat3 array uniform.

        Args:
            name: The name of the uniform variable
            matrices: List of 3x3 matrices (Mat3 objects or lists of 9 floats)
            transpose: Whether to transpose the matrices
        """
        """Set a mat3 array uniform"""
        loc = self.get_uniform_location(name)
        if loc != -1:
            flat_values = []
            for matrix in matrices:
                if hasattr(matrix, "get_matrix"):
                    flat_values.extend(matrix.get_matrix())
                else:
                    flat_values.extend(matrix)
            gl.glUniformMatrix3fv(
                loc,
                len(matrices),
                gl.GL_TRUE if transpose else gl.GL_FALSE,
                (ctypes.c_float * len(flat_values))(*flat_values),
            )

    def set_uniform_matrix4fv(
        self,
        name: str,
        matrices: List[Union[Mat4, List[float]]],
        transpose: bool = False,
    ) -> None:
        """
        Set a mat4 array uniform.

        Args:
            name: The name of the uniform variable
            matrices: List of 4x4 matrices (Mat4 objects or lists of 16 floats)
            transpose: Whether to transpose the matrices
        """
        """Set a mat4 array uniform"""
        loc = self.get_uniform_location(name)
        if loc != -1:
            flat_values = []
            for matrix in matrices:
                if hasattr(matrix, "get_matrix"):
                    flat_values.extend(matrix.get_matrix())
                else:
                    flat_values.extend(matrix)
            gl.glUniformMatrix4fv(
                loc,
                len(matrices),
                gl.GL_TRUE if transpose else gl.GL_FALSE,
                (ctypes.c_float * len(flat_values))(*flat_values),
            )

    def get_uniform_1f(self, name: str) -> float:
        """
        Get a single float uniform value.

        Args:
            name: The name of the uniform variable

        Returns:
            The float value, or 0.0 if not found
        """
        loc = self.get_uniform_location(name)
        if loc != -1:
            result = (ctypes.c_float * 1)()
            gl.glGetUniformfv(self._id, loc, result)
            return result[0]
        return 0.0

    def get_uniform_2f(self, name: str) -> List[float]:
        """
        Get a vec2 uniform value.

        Args:
            name: The name of the uniform variable

        Returns:
            A list of 2 floats, or [0.0, 0.0] if not found
        """
        loc = self.get_uniform_location(name)
        if loc != -1:
            result = (ctypes.c_float * 2)()
            gl.glGetUniformfv(self._id, loc, result)
            return list(result)
        return [0.0, 0.0]

    def get_uniform_3f(self, name: str) -> List[float]:
        """
        Get a vec3 uniform value.

        Args:
            name: The name of the uniform variable

        Returns:
            A list of 3 floats, or [0.0, 0.0, 0.0] if not found
        """
        loc = self.get_uniform_location(name)
        if loc != -1:
            result = (ctypes.c_float * 3)()
            gl.glGetUniformfv(self._id, loc, result)
            return list(result)
        return [0.0, 0.0, 0.0]

    def get_uniform_4f(self, name: str) -> List[float]:
        """
        Get a vec4 uniform value.

        Args:
            name: The name of the uniform variable

        Returns:
            A list of 4 floats, or [0.0, 0.0, 0.0, 0.0] if not found
        """
        loc = self.get_uniform_location(name)
        if loc != -1:
            result = (ctypes.c_float * 4)()
            gl.glGetUniformfv(self._id, loc, result)
            return list(result)
        return [0.0, 0.0, 0.0, 0.0]

    def get_uniform_mat2(self, name: str) -> List[float]:
        """
        Get a mat2 uniform value.

        Args:
            name: The name of the uniform variable

        Returns:
            A list of 4 floats representing the 2x2 matrix, or zeros if not found
        """
        loc = self.get_uniform_location(name)
        if loc != -1:
            result = (ctypes.c_float * 4)()
            gl.glGetUniformfv(self._id, loc, result)
            return list(result)
        return [0.0] * 4

    def get_uniform_mat3(self, name: str) -> List[float]:
        """
        Get a mat3 uniform value.

        Args:
            name: The name of the uniform variable

        Returns:
            A list of 9 floats representing the 3x3 matrix, or zeros if not found
        """
        loc = self.get_uniform_location(name)
        if loc != -1:
            result = (ctypes.c_float * 9)()
            gl.glGetUniformfv(self._id, loc, result)
            return list(result)
        return [0.0] * 9

    def get_uniform_mat4(self, name: str) -> List[float]:
        """
        Get a mat4 uniform value.

        Args:
            name: The name of the uniform variable

        Returns:
            A list of 16 floats representing the 4x4 matrix, or zeros if not found
        """
        loc = self.get_uniform_location(name)
        if loc != -1:
            result = (ctypes.c_float * 16)()
            gl.glGetUniformfv(self._id, loc, result)
            return list(result)
        return [0.0] * 16

    def get_uniform_mat4x3(self, name: str) -> List[float]:
        """
        Get a mat4x3 uniform value.

        Args:
            name: The name of the uniform variable

        Returns:
            A list of 12 floats representing the 4x3 matrix, or zeros if not found
        """
        loc = self.get_uniform_location(name)
        if loc != -1:
            result = (ctypes.c_float * 12)()
            gl.glGetUniformfv(self._id, loc, result)
            return list(result)
        return [0.0] * 12

    def get_uniform_block_data(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get uniform block data by name.

        Args:
            name: The name of the uniform block

        Returns:
            Dictionary containing uniform block data, or None if not found
        """
        """Get uniform block data by name"""
        return self._registered_uniform_blocks.get(name, None)

    def get_registered_uniform_blocks(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all registered uniform blocks.

        Returns:
            A copy of the registered uniform blocks dictionary
        """
        """Get all registered uniform blocks"""
        return self._registered_uniform_blocks.copy()

    def get_uniform_block_location(self, name: str) -> int:
        """
        Get uniform block location by name.

        Args:
            name: The name of the uniform block

        Returns:
            The uniform block index/location, or -1 if not found
        """
        """Get uniform block location by name"""
        if name in self._registered_uniform_blocks:
            return self._registered_uniform_blocks[name]["loc"]
        else:
            logger.warning(f"Uniform block '{name}' not found in shader '{self._name}'")
            return -1

    def get_uniform_block_buffer(self, name: str) -> int:
        """
        Get uniform block buffer by name.

        Args:
            name: The name of the uniform block

        Returns:
            The OpenGL buffer ID, or 0 if not found
        """
        """Get uniform block buffer by name"""
        if name in self._registered_uniform_blocks:
            return self._registered_uniform_blocks[name]["buffer"]
        else:
            logger.warning(f"Uniform block '{name}' not found in shader '{self._name}'")
            return 0

    def get_gl_type_string(self, gl_type: int) -> str:
        """
        Convert OpenGL type constant to human-readable string.

        Args:
            gl_type: OpenGL type constant (e.g., GL_FLOAT, GL_FLOAT_VEC3)

        Returns:
            str: Human-readable type string
        """
        type_map = {
            # Scalars
            gl.GL_FLOAT: "float",
            gl.GL_DOUBLE: "double",
            gl.GL_INT: "int",
            gl.GL_UNSIGNED_INT: "uint",
            gl.GL_BOOL: "bool",
            # Float vectors
            gl.GL_FLOAT_VEC2: "vec2",
            gl.GL_FLOAT_VEC3: "vec3",
            gl.GL_FLOAT_VEC4: "vec4",
            # Double vectors
            gl.GL_DOUBLE_VEC2: "dvec2",
            gl.GL_DOUBLE_VEC3: "dvec3",
            gl.GL_DOUBLE_VEC4: "dvec4",
            # Integer vectors
            gl.GL_INT_VEC2: "ivec2",
            gl.GL_INT_VEC3: "ivec3",
            gl.GL_INT_VEC4: "ivec4",
            # Unsigned int vectors
            gl.GL_UNSIGNED_INT_VEC2: "uvec2",
            gl.GL_UNSIGNED_INT_VEC3: "uvec3",
            gl.GL_UNSIGNED_INT_VEC4: "uvec4",
            # Bool vectors
            gl.GL_BOOL_VEC2: "bvec2",
            gl.GL_BOOL_VEC3: "bvec3",
            gl.GL_BOOL_VEC4: "bvec4",
            # Float matrices
            gl.GL_FLOAT_MAT2: "mat2",
            gl.GL_FLOAT_MAT3: "mat3",
            gl.GL_FLOAT_MAT4: "mat4",
            gl.GL_FLOAT_MAT2x3: "mat2x3",
            gl.GL_FLOAT_MAT2x4: "mat2x4",
            gl.GL_FLOAT_MAT3x2: "mat3x2",
            gl.GL_FLOAT_MAT3x4: "mat3x4",
            gl.GL_FLOAT_MAT4x2: "mat4x2",
            gl.GL_FLOAT_MAT4x3: "mat4x3",
            # Double matrices
            gl.GL_DOUBLE_MAT2: "dmat2",
            gl.GL_DOUBLE_MAT3: "dmat3",
            gl.GL_DOUBLE_MAT4: "dmat4",
            gl.GL_DOUBLE_MAT2x3: "dmat2x3",
            gl.GL_DOUBLE_MAT2x4: "dmat2x4",
            gl.GL_DOUBLE_MAT3x2: "dmat3x2",
            gl.GL_DOUBLE_MAT3x4: "dmat3x4",
            gl.GL_DOUBLE_MAT4x2: "dmat4x2",
            gl.GL_DOUBLE_MAT4x3: "dmat4x3",
            # Samplers (float)
            gl.GL_SAMPLER_1D: "sampler1D",
            gl.GL_SAMPLER_2D: "sampler2D",
            gl.GL_SAMPLER_3D: "sampler3D",
            gl.GL_SAMPLER_CUBE: "samplerCube",
            gl.GL_SAMPLER_1D_SHADOW: "sampler1DShadow",
            gl.GL_SAMPLER_2D_SHADOW: "sampler2DShadow",
            gl.GL_SAMPLER_1D_ARRAY: "sampler1DArray",
            gl.GL_SAMPLER_2D_ARRAY: "sampler2DArray",
            gl.GL_SAMPLER_1D_ARRAY_SHADOW: "sampler1DArrayShadow",
            gl.GL_SAMPLER_2D_ARRAY_SHADOW: "sampler2DArrayShadow",
            gl.GL_SAMPLER_CUBE_SHADOW: "samplerCubeShadow",
            gl.GL_SAMPLER_BUFFER: "samplerBuffer",
            gl.GL_SAMPLER_2D_RECT: "sampler2DRect",
            gl.GL_SAMPLER_2D_RECT_SHADOW: "sampler2DRectShadow",
            # Samplers (int)
            gl.GL_INT_SAMPLER_1D: "isampler1D",
            gl.GL_INT_SAMPLER_2D: "isampler2D",
            gl.GL_INT_SAMPLER_3D: "isampler3D",
            gl.GL_INT_SAMPLER_CUBE: "isamplerCube",
            gl.GL_INT_SAMPLER_1D_ARRAY: "isampler1DArray",
            gl.GL_INT_SAMPLER_2D_ARRAY: "isampler2DArray",
            gl.GL_INT_SAMPLER_BUFFER: "isamplerBuffer",
            gl.GL_INT_SAMPLER_2D_RECT: "isampler2DRect",
            # Samplers (unsigned int)
            gl.GL_UNSIGNED_INT_SAMPLER_1D: "usampler1D",
            gl.GL_UNSIGNED_INT_SAMPLER_2D: "usampler2D",
            gl.GL_UNSIGNED_INT_SAMPLER_3D: "usampler3D",
            gl.GL_UNSIGNED_INT_SAMPLER_CUBE: "usamplerCube",
            gl.GL_UNSIGNED_INT_SAMPLER_1D_ARRAY: "usampler1DArray",
            gl.GL_UNSIGNED_INT_SAMPLER_2D_ARRAY: "usampler2DArray",
            gl.GL_UNSIGNED_INT_SAMPLER_BUFFER: "usamplerBuffer",
            gl.GL_UNSIGNED_INT_SAMPLER_2D_RECT: "usampler2DRect",
            # Images (float)
            gl.GL_IMAGE_1D: "image1D",
            gl.GL_IMAGE_2D: "image2D",
            gl.GL_IMAGE_3D: "image3D",
            gl.GL_IMAGE_2D_RECT: "image2DRect",
            gl.GL_IMAGE_CUBE: "imageCube",
            gl.GL_IMAGE_BUFFER: "imageBuffer",
            gl.GL_IMAGE_1D_ARRAY: "image1DArray",
            gl.GL_IMAGE_2D_ARRAY: "image2DArray",
            gl.GL_IMAGE_CUBE_MAP_ARRAY: "imageCubeArray",
            gl.GL_IMAGE_2D_MULTISAMPLE: "image2DMS",
            gl.GL_IMAGE_2D_MULTISAMPLE_ARRAY: "image2DMSArray",
            # Images (int)
            gl.GL_INT_IMAGE_1D: "iimage1D",
            gl.GL_INT_IMAGE_2D: "iimage2D",
            gl.GL_INT_IMAGE_3D: "iimage3D",
            gl.GL_INT_IMAGE_2D_RECT: "iimage2DRect",
            gl.GL_INT_IMAGE_CUBE: "iimageCube",
            gl.GL_INT_IMAGE_BUFFER: "iimageBuffer",
            gl.GL_INT_IMAGE_1D_ARRAY: "iimage1DArray",
            gl.GL_INT_IMAGE_2D_ARRAY: "iimage2DArray",
            gl.GL_INT_IMAGE_CUBE_MAP_ARRAY: "iimageCubeArray",
            gl.GL_INT_IMAGE_2D_MULTISAMPLE: "iimage2DMS",
            gl.GL_INT_IMAGE_2D_MULTISAMPLE_ARRAY: "iimage2DMSArray",
            # Images (unsigned int)
            gl.GL_UNSIGNED_INT_IMAGE_1D: "uimage1D",
            gl.GL_UNSIGNED_INT_IMAGE_2D: "uimage2D",
            gl.GL_UNSIGNED_INT_IMAGE_3D: "uimage3D",
            gl.GL_UNSIGNED_INT_IMAGE_2D_RECT: "uimage2DRect",
            gl.GL_UNSIGNED_INT_IMAGE_CUBE: "uimageCube",
            gl.GL_UNSIGNED_INT_IMAGE_BUFFER: "uimageBuffer",
            gl.GL_UNSIGNED_INT_IMAGE_1D_ARRAY: "uimage1DArray",
            gl.GL_UNSIGNED_INT_IMAGE_2D_ARRAY: "uimage2DArray",
            gl.GL_UNSIGNED_INT_IMAGE_CUBE_MAP_ARRAY: "uimageCubeArray",
            gl.GL_UNSIGNED_INT_IMAGE_2D_MULTISAMPLE: "uimage2DMS",
            gl.GL_UNSIGNED_INT_IMAGE_2D_MULTISAMPLE_ARRAY: "uimage2DMSArray",
        }
        return type_map.get(gl_type, f"Unknown type {gl_type}")

    def print_registered_uniforms(self) -> None:
        """
        Print information about all registered uniforms to the log.
        """
        logger.info(f"Registered uniforms for {self._name}:")
        base_uniforms = {}
        array_elements = {}

        # Separate base uniforms from array elements
        for name, (location, uniform_type, size, is_array) in self._uniforms.items():
            if "[" in name and "]" in name:
                # This is an array element
                base_name = name.split("[")[0]
                if base_name not in array_elements:
                    array_elements[base_name] = []
                array_elements[base_name].append(
                    (name, location, uniform_type, size, is_array)
                )
            else:
                base_uniforms[name] = (location, uniform_type, size, is_array)

        # Print base uniforms
        for name, (location, uniform_type, size, is_array) in base_uniforms.items():
            type_str = self.get_gl_type_string(uniform_type)
            if is_array:
                logger.info(
                    f"  {name}[{size}] (type: {type_str}, location: {location})"
                )
            else:
                logger.info(f"  {name} (type: {type_str}, location: {location})")

        # Print array elements grouped by base name
        for base_name, elements in array_elements.items():
            logger.info(f"  Array elements for {base_name}:")
            for element_name, location, uniform_type, size, is_array in elements:
                type_str = self.get_gl_type_string(uniform_type)
                logger.info(
                    f"    {element_name} (type: {type_str}, location: {location})"
                )

    def print_registered_uniform_blocks(self) -> None:
        """
        Print information about all registered uniform blocks to the log.
        """
        logger.info(f"Registered uniform blocks for {self._name}:")
        for name, data in self._registered_uniform_blocks.items():
            logger.info(f"  {name} (index: {data['loc']}, buffer: {data['buffer']})")

    def print_properties(self) -> None:
        """
        Print detailed properties and status information about this shader program.
        """
        logger.info(f"Properties for shader program {self._name}:")
        logger.info(f"  ID: {self._id}")

        link_status = gl.glGetProgramiv(self._id, gl.GL_LINK_STATUS)
        logger.info(f"  Link status: {link_status}")

        validate_status = gl.glGetProgramiv(self._id, gl.GL_VALIDATE_STATUS)
        logger.info(f"  Validate status: {validate_status}")

        attached_shaders = gl.glGetProgramiv(self._id, gl.GL_ATTACHED_SHADERS)
        logger.info(f"  Attached shaders: {attached_shaders}")

        active_attributes = gl.glGetProgramiv(self._id, gl.GL_ACTIVE_ATTRIBUTES)
        logger.info(f"  Active attributes: {active_attributes}")

        active_uniforms = gl.glGetProgramiv(self._id, gl.GL_ACTIVE_UNIFORMS)
        logger.info(f"  Active uniforms: {active_uniforms}")

        active_uniform_blocks = gl.glGetProgramiv(self._id, gl.GL_ACTIVE_UNIFORM_BLOCKS)
        logger.info(f"  Active uniform blocks: {active_uniform_blocks}")

        if self._registered_uniform_blocks:
            logger.info("  Registered uniform blocks:")
            for name, data in self._registered_uniform_blocks.items():
                logger.info(
                    f"    {name} (index: {data['loc']}, buffer: {data['buffer']})"
                )
