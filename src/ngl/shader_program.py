import ctypes

import OpenGL.GL as gl

from .log import logger
from .mat2 import Mat2
from .mat3 import Mat3
from .mat4 import Mat4
from .shader import Shader
from .vec2 import Vec2
from .vec3 import Vec3
from .vec4 import Vec4
import numpy as np

class ShaderProgram:
    def __init__(self, name: str, exit_on_error: bool = True):
        self._name = name
        self._exit_on_error = exit_on_error
        self._id = gl.glCreateProgram()
        self._shaders = []
        self._uniforms = {}
        self._registered_uniform_blocks = {}

    def attach_shader(self, shader: Shader):
        gl.glAttachShader(self._id, shader._id)
        self._shaders.append(shader)

    def link(self) -> bool:
        gl.glLinkProgram(self._id)
        if gl.glGetProgramiv(self._id, gl.GL_LINK_STATUS) != gl.GL_TRUE:
            info = gl.glGetProgramInfoLog(self._id)
            logger.error(f"Error linking program {self._name}: {info}")
            if self._exit_on_error:
                exit()
            return False
        self.auto_register_uniforms()
        self.auto_register_uniform_blocks()
        return True

    def auto_register_uniforms(self):
        uniform_count = gl.glGetProgramiv(self._id, gl.GL_ACTIVE_UNIFORMS)
        for i in range(uniform_count):
            name, _, shader_type = gl.glGetActiveUniform(self._id, i, 256)
            # remove [0] if it exists in the name
            if name.endswith(b"[0]"):
                name = name[:-3]
            location = gl.glGetUniformLocation(self._id, name)
            self._uniforms[name.decode("utf-8")] = (location, shader_type)

    def auto_register_uniform_blocks(self):
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

            gl.glGetActiveUniformBlockName(self._id, i, 256, ctypes.byref(length), name_buffer)
            name_str = name_buffer.value.decode("utf-8") if name_buffer.value else f"UniformBlock_{i}"

            # Create uniform block data structure
            data = {
                "name": name_str,
                "loc": gl.glGetUniformBlockIndex(self._id, name_str.encode("utf-8")),
                "buffer": gl.glGenBuffers(1),
            }

            # Store the uniform block data
            self._registered_uniform_blocks[name_str] = data
            logger.info(f"Uniform Block {name_str} {data['loc']} {data['buffer']}")

    def use(self):
        gl.glUseProgram(self._id)

    def get_id(self) -> int:
        return self._id

    def get_uniform_location(self, name: str) -> int:
        if name in self._uniforms:
            return self._uniforms[name][0]
        else:
            logger.warning(f"Uniform '{name}' not found in shader '{self._name}'")
            return -1

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
            logger.error(f"Uniform block '{uniform_block_name}' not found in shader '{self._name}'")
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

    def set_uniform(self, name: str, *value):
        loc = self.get_uniform_location(name)
        if loc == -1:
            return
        if len(value) == 1:
            val = value[0]
            if isinstance(val, int):
                gl.glUniform1i(loc, val)
            elif isinstance(val, float):
                gl.glUniform1f(loc, val)
            elif isinstance(val, Mat2):
                gl.glUniformMatrix2fv(loc, 1, gl.GL_FALSE, (ctypes.c_float * 4)(*val.get_matrix()))
            elif isinstance(val, Mat3):
                gl.glUniformMatrix3fv(loc, 1, gl.GL_FALSE, (ctypes.c_float * 9)(*val.get_matrix()))
            elif isinstance(val, Mat4):
                gl.glUniformMatrix4fv(loc, 1, gl.GL_FALSE, (ctypes.c_float * 16)(*val.get_matrix()))
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
                        gl.glUniformMatrix2fv(loc, 1, gl.GL_FALSE, (ctypes.c_float * 4)(*val))
                    elif len(val) == 9:
                        gl.glUniformMatrix3fv(loc, 1, gl.GL_FALSE, (ctypes.c_float * 9)(*val))
                    elif len(val) == 16:
                        gl.glUniformMatrix4fv(loc, 1, gl.GL_FALSE, (ctypes.c_float * 16)(*val))
                except TypeError:
                    logger.warning(f"Warning: uniform '{name}' has unknown type: {type(val)}")

        elif len(value) == 2:
            gl.glUniform2f(loc, *value)
        elif len(value) == 3:
            gl.glUniform3f(loc, *value)
        elif len(value) == 4:
            gl.glUniform4f(loc, *value)

    def get_uniform_1f(self, name: str) -> float:
        loc = self.get_uniform_location(name)
        if loc != -1:
            result = (ctypes.c_float * 1)()
            gl.glGetUniformfv(self._id, loc, result)
            return result[0]
        return 0.0

    def get_uniform_2f(self, name: str) -> list[float]:
        loc = self.get_uniform_location(name)
        if loc != -1:
            result = (ctypes.c_float * 2)()
            gl.glGetUniformfv(self._id, loc, result)
            return list(result)
        return [0.0, 0.0]

    def get_uniform_3f(self, name: str) -> list[float]:
        loc = self.get_uniform_location(name)
        if loc != -1:
            result = (ctypes.c_float * 3)()
            gl.glGetUniformfv(self._id, loc, result)
            return list(result)
        return [0.0, 0.0, 0.0]

    def get_uniform_4f(self, name: str) -> list[float]:
        loc = self.get_uniform_location(name)
        if loc != -1:
            result = (ctypes.c_float * 4)()
            gl.glGetUniformfv(self._id, loc, result)
            return list(result)
        return [0.0, 0.0, 0.0, 0.0]

    def get_uniform_mat2(self, name: str) -> list[float]:
        loc = self.get_uniform_location(name)
        if loc != -1:
            result = (ctypes.c_float * 4)()
            gl.glGetUniformfv(self._id, loc, result)
            return list(result)
        return [0.0] * 4

    def get_uniform_mat3(self, name: str) -> list[float]:
        loc = self.get_uniform_location(name)
        if loc != -1:
            result = (ctypes.c_float * 9)()
            gl.glGetUniformfv(self._id, loc, result)
            return list(result)
        return [0.0] * 9

    def get_uniform_mat4(self, name: str) -> list[float]:
        loc = self.get_uniform_location(name)
        if loc != -1:
            result = (ctypes.c_float * 16)()
            gl.glGetUniformfv(self._id, loc, result)
            return list(result)
        return [0.0] * 16

    def get_uniform_mat4x3(self, name: str) -> list[float]:
        loc = self.get_uniform_location(name)
        if loc != -1:
            result = (ctypes.c_float * 12)()
            gl.glGetUniformfv(self._id, loc, result)
            return list(result)
        return [0.0] * 12

    def get_uniform_block_data(self, name: str):
        """Get uniform block data by name"""
        return self._registered_uniform_blocks.get(name, None)

    def get_registered_uniform_blocks(self) -> dict:
        """Get all registered uniform blocks"""
        return self._registered_uniform_blocks.copy()

    def get_uniform_block_location(self, name: str) -> int:
        """Get uniform block location by name"""
        if name in self._registered_uniform_blocks:
            return self._registered_uniform_blocks[name]["loc"]
        else:
            logger.warning(f"Uniform block '{name}' not found in shader '{self._name}'")
            return -1

    def get_uniform_block_buffer(self, name: str) -> int:
        """Get uniform block buffer by name"""
        if name in self._registered_uniform_blocks:
            return self._registered_uniform_blocks[name]["buffer"]
        else:
            logger.warning(f"Uniform block '{name}' not found in shader '{self._name}'")
            return 0

    def get_gl_type_string(self, gl_type: int) -> str:
        type_map = {
            gl.GL_FLOAT: "float",
            gl.GL_FLOAT_VEC2: "vec2",
            gl.GL_FLOAT_VEC3: "vec3",
            gl.GL_FLOAT_VEC4: "vec4",
            gl.GL_DOUBLE: "double",
            gl.GL_INT: "int",
            gl.GL_UNSIGNED_INT: "unsigned int",
            gl.GL_BOOL: "bool",
            gl.GL_FLOAT_MAT2: "mat2",
            gl.GL_FLOAT_MAT3: "mat3",
            gl.GL_FLOAT_MAT4: "mat4",
            gl.GL_SAMPLER_2D: "sampler2D",
            gl.GL_SAMPLER_CUBE: "samplerCube",
        }
        return type_map.get(gl_type, f"Unknown type {gl_type}")

    def print_registered_uniforms(self):
        logger.info(f"Registered uniforms for {self._name}:")
        for name, (location, type) in self._uniforms.items():
            type_str = self.get_gl_type_string(type)
            logger.info(f"  {name} (type: {type_str}, location: {location})")

    def print_registered_uniform_blocks(self):
        logger.info(f"Registered uniform blocks for {self._name}:")
        for name, data in self._registered_uniform_blocks.items():
            logger.info(f"  {name} (index: {data['loc']}, buffer: {data['buffer']})")

    def print_properties(self):
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
                logger.info(f"    {name} (index: {data['loc']}, buffer: {data['buffer']})")
