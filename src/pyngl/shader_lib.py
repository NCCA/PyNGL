from __future__ import annotations

import enum
from pathlib import Path

import OpenGL.GL as gl

from .log import logger
from .shader import Shader, ShaderType
from .shader_program import ShaderProgram


class DefaultShader(enum.Enum):
    """
    Enum representing the default shaders available in the library.
    """

    COLOUR = "nglColourShader"
    TEXT = "nglTextShader"
    DIFFUSE = "nglDiffuseShader"
    CHECKER = "nglCheckerShader"


class _ShaderLib:
    """
    Shader library for managing OpenGL shader programs and shaders.
    Provides methods to load, compile, link, and use shaders, as well as manage uniforms and uniform blocks.
    """

    def __init__(self):
        """
        Initialize the shader library with empty registries for shader programs, shaders, and uniform blocks.
        """
        self._shader_programs: dict[str, ShaderProgram] = {}
        self._shaders: dict[str, Shader] = {}
        self._current_shader: str | None = None
        self._default_shaders_loaded: bool = False
        self._registered_uniform_blocks: dict[str, dict] = {}

    def load_shader(
        self,
        name: str,
        vert: str,
        frag: str,
        geo: str = None,
        exit_on_error: bool = True,
    ) -> bool:
        """
        Load, compile, and link a shader program from vertex, fragment, and optionally geometry shader sources.

        Args:
            name: Name of the shader program.
            vert: Path to the vertex shader source file.
            frag: Path to the fragment shader source file.
            geo: Optional path to the geometry shader source file.
            exit_on_error: Whether to exit on shader compilation/linking error.

        Returns:
            bool: True if the shader program was successfully created, False otherwise.
        """
        program = ShaderProgram(name, exit_on_error)

        # Load and compile vertex shader
        vert_shader = Shader(f"{name}Vertex", ShaderType.VERTEX.value, exit_on_error)
        vert_shader.load(vert)
        if not vert_shader.compile():
            logger.error(f"Failed to compile vertex shader for {name}")
            return False

        # Load and compile fragment shader
        frag_shader = Shader(
            f"{name}Fragment", ShaderType.FRAGMENT.value, exit_on_error
        )
        frag_shader.load(frag)
        if not frag_shader.compile():
            logger.error(f"Failed to compile fragment shader for {name}")
            return False

        # Attach compiled shaders to the program
        program.attach_shader(vert_shader)
        program.attach_shader(frag_shader)

        # Optionally load and compile geometry shader
        if geo:
            geo_shader = Shader(
                f"{name}Geometry", ShaderType.GEOMETRY.value, exit_on_error
            )
            geo_shader.load(geo)
            if not geo_shader.compile():
                logger.error(f"Failed to compile geometry shader for {name}")
                return False
            program.attach_shader(geo_shader)

        # Link the shader program
        if not program.link():
            logger.error(f"Failed to link shader program for {name}")
            return False

        self._shader_programs[name] = program
        logger.info(f"Shader program '{name}' created")
        return True

    def use(self, name: str | None) -> None:
        """
        Activate the specified shader program by name, or deactivate shaders if name is None.

        Args:
            name: Name of the shader program to use, or None to clear the current shader.
        """
        # Handle None to clear current shader
        if name is None:
            gl.glUseProgram(0)
            self._current_shader = None
            return

        # Lazy load default shaders on request
        if not self._default_shaders_loaded and name not in self._shader_programs:
            logger.warning("Default shaders not loaded loading now")
            self._load_default_shaders()

        if name in self._shader_programs:
            self._shader_programs[name].use()
            self._current_shader = name
        else:
            logger.error(f"Shader '{name}' not found")
            gl.glUseProgram(0)
            self._current_shader = None

    def get_current_shader_name(self) -> str | None:
        """
        Get the name of the currently active shader program.

        Returns:
            str | None: Name of the current shader, or None if no shader is active.
        """
        return self._current_shader

    def get_program_id(self, name: str) -> int | None:
        """
        Get the OpenGL program ID for a shader program by name.

        Args:
            name: Name of the shader program.

        Returns:
            int | None: OpenGL program ID, or None if not found.
        """
        if name in self._shader_programs:
            return self._shader_programs[name].get_id()
        return None

    def create_shader_program(self, name: str, exit_on_error: bool = True) -> None:
        """
        Create a new ShaderProgram and register it by name.

        Args:
            name: Name of the shader program.
            exit_on_error: Whether to exit on error.
        """
        self._shader_programs[name] = ShaderProgram(name, exit_on_error)

    def attach_shader(
        self, name: str, type: ShaderType, exit_on_error: bool = True
    ) -> None:
        """
        Create and register a Shader object by name and type.

        Args:
            name: Name of the shader.
            type: ShaderType (VERTEX, FRAGMENT, GEOMETRY).
            exit_on_error: Whether to exit on error.
        """
        self._shaders[name] = Shader(name, type.value, exit_on_error)

    def load_shader_source(self, name: str, source_file: str) -> None:
        """
        Load shader source code from a file into a registered Shader.

        Args:
            name: Name of the shader.
            source_file: Path to the shader source file.
        """
        if name in self._shaders:
            self._shaders[name].load(source_file)
        else:
            logger.error(f"Error: shader {name} not found")

    def load_shader_source_from_string(self, name: str, source_string: str) -> None:
        """
        Load shader source code from a string into a registered Shader.

        Args:
            name: Name of the shader.
            source_string: Shader source code as a string.
        """
        if name in self._shaders:
            self._shaders[name].load_shader_source_from_string(source_string)
        else:
            logger.error(f"Error: shader {name} not found")

    def compile_shader(self, name: str) -> bool:
        """
        Compile a registered Shader by name.

        Args:
            name: Name of the shader.

        Returns:
            bool: True if compilation succeeded, False otherwise.
        """
        if name in self._shaders:
            return self._shaders[name].compile()
        else:
            logger.error(f"Error: shader {name} not found")
            return False

    def attach_shader_to_program(self, program_name: str, shader_name: str) -> None:
        """
        Attach a registered Shader to a registered ShaderProgram.

        Args:
            program_name: Name of the shader program.
            shader_name: Name of the shader.
        """
        if program_name in self._shader_programs and shader_name in self._shaders:
            self._shader_programs[program_name].attach_shader(
                self._shaders[shader_name]
            )
        else:
            logger.error(
                f"Error: program {program_name} or shader {shader_name} not found"
            )

    def link_program_object(self, name: str) -> bool:
        """
        Link a registered ShaderProgram by name.

        Args:
            name: Name of the shader program.

        Returns:
            bool: True if linking succeeded, False otherwise.
        """
        if name in self._shader_programs:
            return self._shader_programs[name].link()
        else:
            logger.error(f"Error: program {name} not found")
            return False

    def set_uniform(self, name: str, *value) -> None:
        """
        Set a uniform variable in the currently active shader program.

        Args:
            name: Name of the uniform variable.
            *value: Values to set for the uniform.
        """
        if self._current_shader:
            self._shader_programs[self._current_shader].set_uniform(name, *value)

    def set_uniform_buffer(self, uniform_block_name: str, size: int, data) -> bool:
        """
        Set uniform buffer data for the specified uniform block in the current shader.

        Args:
            uniform_block_name: Name of the uniform block.
            size: Size of the data in bytes.
            data: Data to upload (can be ctypes array, bytes, or buffer-like object).

        Returns:
            bool: True if successful, False otherwise.
        """
        if self._current_shader:
            return self._shader_programs[self._current_shader].set_uniform_buffer(
                uniform_block_name, size, data
            )
        else:
            logger.error("No current shader active")
            return False

    def get_uniform_1f(self, name: str) -> float:
        """
        Get the value of a float uniform variable from the current shader.

        Args:
            name: Name of the uniform variable.

        Returns:
            float: Value of the uniform, or 0.0 if not found.
        """
        if self._current_shader:
            return self._shader_programs[self._current_shader].get_uniform_1f(name)
        return 0.0

    def get_uniform_2f(self, name: str) -> list[float]:
        """
        Get the value of a vec2 uniform variable from the current shader.

        Args:
            name: Name of the uniform variable.

        Returns:
            list[float]: List of 2 float values, or [0.0, 0.0] if not found.
        """
        if self._current_shader:
            return self._shader_programs[self._current_shader].get_uniform_2f(name)
        return [0.0, 0.0]

    def get_uniform_3f(self, name: str) -> list[float]:
        """
        Get the value of a vec3 uniform variable from the current shader.

        Args:
            name: Name of the uniform variable.

        Returns:
            list[float]: List of 3 float values, or [0.0, 0.0, 0.0] if not found.
        """
        if self._current_shader:
            return self._shader_programs[self._current_shader].get_uniform_3f(name)
        return [0.0, 0.0, 0.0]

    def get_uniform_4f(self, name: str) -> list[float]:
        """
        Get the value of a vec4 uniform variable from the current shader.

        Args:
            name: Name of the uniform variable.

        Returns:
            list[float]: List of 4 float values, or [0.0, 0.0, 0.0, 0.0] if not found.
        """
        if self._current_shader:
            return self._shader_programs[self._current_shader].get_uniform_4f(name)
        return [0.0, 0.0, 0.0, 0.0]

    def get_uniform_mat2(self, name: str) -> list[float]:
        """
        Get the value of a mat2 uniform variable from the current shader.

        Args:
            name: Name of the uniform variable.

        Returns:
            list[float]: List of 4 float values, or [0.0]*4 if not found.
        """
        if self._current_shader:
            return self._shader_programs[self._current_shader].get_uniform_mat2(name)
        return [0.0] * 4

    def get_uniform_mat3(self, name: str) -> list[float]:
        """
        Get the value of a mat3 uniform variable from the current shader.

        Args:
            name: Name of the uniform variable.

        Returns:
            list[float]: List of 9 float values, or [0.0]*9 if not found.
        """
        if self._current_shader:
            return self._shader_programs[self._current_shader].get_uniform_mat3(name)
        return [0.0] * 9

    def get_uniform_mat4(self, name: str) -> list[float]:
        """
        Get the value of a mat4 uniform variable from the current shader.

        Args:
            name: Name of the uniform variable.

        Returns:
            list[float]: List of 16 float values, or [0.0]*16 if not found.
        """
        if self._current_shader:
            return self._shader_programs[self._current_shader].get_uniform_mat4(name)
        return [0.0] * 16

    def edit_shader(self, shader_name: str, to_find: str, replace_with: str) -> bool:
        """
        Edit the source code of a registered shader by replacing a substring.

        Args:
            shader_name: Name of the shader.
            to_find: Substring to find.
            replace_with: Substring to replace with.

        Returns:
            bool: True if edit succeeded, False otherwise.
        """
        if shader_name in self._shaders:
            return self._shaders[shader_name].edit_shader(to_find, replace_with)
        return False

    def reset_edits(self, shader_name: str) -> None:
        """
        Reset any edits made to a registered shader's source code.

        Args:
            shader_name: Name of the shader.
        """
        if shader_name in self._shaders:
            self._shaders[shader_name].reset_edits()

    def _load_default_shaders(self) -> None:
        """
        Load the default shaders from the 'shaders' directory and register them.
        """
        shader_folder = Path(__file__).parent / "shaders"

        # Define which default shaders to load and their corresponding files
        to_load = {
            DefaultShader.COLOUR: {
                "vertex": shader_folder / "colour_vertex.glsl",
                "fragment": shader_folder / "colour_fragment.glsl",
            },
            DefaultShader.DIFFUSE: {
                "vertex": shader_folder / "diffuse_vertex.glsl",
                "fragment": shader_folder / "diffuse_fragment.glsl",
            },
            DefaultShader.CHECKER: {
                "vertex": shader_folder / "checker_vertex.glsl",
                "fragment": shader_folder / "checker_fragment.glsl",
            },
        }

        # Load each default shader program
        for shader_name, shader_data in to_load.items():
            if self.load_shader(
                shader_name, shader_data["vertex"], shader_data["fragment"]
            ):
                logger.info(f"{shader_name} shader loaded successfully")

        # Text shader has geometry shader as well
        if self.load_shader(
            DefaultShader.TEXT,
            vert=shader_folder / "text_vertex.glsl",
            frag=shader_folder / "text_fragment.glsl",
            geo=shader_folder / "text_geometry.glsl",
        ):
            logger.info("DefaultShader.TEXT  shader loaded successfully")

        self._default_shaders_loaded = True

    def print_registered_uniforms(self, shader_name: str = None) -> None:
        """
        Print the registered uniforms for a shader program.

        Args:
            shader_name: Name of the shader program. If None, uses the current shader.
        """
        if shader_name is None:
            shader_name = self._current_shader

        if shader_name in self._shader_programs:
            self._shader_programs[shader_name].print_registered_uniforms()
        else:
            logger.error(f"Shader '{shader_name}' not found")

    def print_properties(self) -> None:
        """
        Print properties of the currently active shader program.
        """
        if self._current_shader in self._shader_programs:
            logger.info(
                "_______________________________________________________________________________________________________________________"
            )
            logger.info(
                f"Printing Properties for ShaderProgram {self._current_shader} "
            )
            logger.info(
                "_______________________________________________________________________________________________________________________"
            )
            self._shader_programs[self._current_shader].print_properties()
            logger.info(
                "_______________________________________________________________________________________________________________________"
            )
        else:
            logger.warning(
                f"Warning no currently active shader to print properties for {self._current_shader} "
            )

    def auto_register_uniform_blocks(self, shader_name: str = None) -> None:
        """
        Auto-register uniform blocks for the specified shader program.
        If no shader_name is provided, uses the current shader.

        Args:
            shader_name: Name of the shader program. If None, uses the current shader.
        """
        if shader_name is None:
            shader_name = self._current_shader

        if shader_name not in self._shader_programs:
            logger.error(f"Shader program '{shader_name}' not found")
            return

        # Delegate to the ShaderProgram's auto_register_uniform_blocks method
        program = self._shader_programs[shader_name]
        program.auto_register_uniform_blocks()

        # Copy the uniform blocks to our registry
        if shader_name not in self._registered_uniform_blocks:
            self._registered_uniform_blocks[shader_name] = {}

        self._registered_uniform_blocks[shader_name] = (
            program.get_registered_uniform_blocks()
        )

    def get_uniform_block_data(self, shader_name: str = None, block_name: str = None):
        """
        Get uniform block data for the specified shader and block name.
        If shader_name is None, uses current shader.
        If block_name is None, returns all blocks for the shader.

        Args:
            shader_name: Name of the shader program. If None, uses the current shader.
            block_name: Name of the uniform block. If None, returns all blocks.

        Returns:
            dict or None: Uniform block data, or None if not found.
        """
        if shader_name is None:
            shader_name = self._current_shader

        if shader_name not in self._registered_uniform_blocks:
            return None

        if block_name is None:
            return self._registered_uniform_blocks[shader_name]
        else:
            return self._registered_uniform_blocks[shader_name].get(block_name)


# Singleton instance of the shader library for use throughout the application.
ShaderLib = _ShaderLib()
