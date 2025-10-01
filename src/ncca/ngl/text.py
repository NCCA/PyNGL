"""
A module for rendering text in OpenGL using pre-rendered font atlases.

This implementation uses the 'freetype-py' library to rasterize characters
from a given font file into a single texture atlas. This atlas is then
used by a set of shaders (vertex, geometry, and fragment) to render
text efficiently.

The process is as follows:
1.  FontAtlas class:
    -   Loads a font file.
    -   Renders glyphs for a range of characters (ASCII ' ' to '~').
    -   Packs these glyphs into a single large texture atlas in memory.
    -   Calculates and stores metadata for each glyph (size, bearing,
        advance, and UV coordinates within the atlas).
    -   Generates a single OpenGL texture for the atlas.

2.  _Text class (exported as Text):
    -   Manages multiple fonts by creating and storing FontAtlas objects.
    -   Provides a `render_dynamic_text` method to draw text strings.
    -   `_build_instances`: For a given string, this method generates a
        list of vertex attributes for each character. Each character is
        represented as a single point with attributes for position, UVs,
        and size.
    -   `render_dynamic_text`: This method sends the generated instance
        data to the GPU and draws it using GL_POINTS.

3.  Shaders:
    -   Vertex Shader: A simple pass-through shader that sends point
        data to the geometry shader.
    -   Geometry Shader: Receives points and generates a textured quad
        for each character on the fly.
    -   Fragment Shader: Samples the font atlas texture to color the
        quad, effectively drawing the character.
"""

from typing import Any, Dict, List

import freetype
import numpy as np
import OpenGL.GL as gl

from .log import logger
from .shader_lib import DefaultShader, ShaderLib
from .simple_vao import VertexData
from .vao_factory import VAOFactory, VAOType
from .vec3 import Vec3


class FontAtlas:
    """
    Manages the creation of a font texture atlas for efficient text rendering.

    This class uses FreeType to render glyphs for a specified font and packs them
    into a single texture. It also stores metadata for each glyph.
    """

    def __init__(self, font_path: str, font_size: int = 48, debug: bool = False):
        """
        Initializes the FontAtlas.

        Args:
            font_path: The file path to the font (e.g., a .ttf file).
            font_size: The font size in pixels to be used for rendering the atlas.
            debug: If True, saves the generated atlas as a PNG for debugging.
        """
        try:
            self.face = freetype.Face(font_path)
            self.face.set_pixel_sizes(0, font_size)
            self.font_size: int = font_size
            self.glyphs: Dict[str, Dict[str, Any]] = {}
            self.texture: int = 0
            self.atlas_w: int = 0
            self.atlas_h: int = 0
            self.atlas: np.ndarray | None = None
            self.build_atlas(debug)

        except freetype.FT_Exception as e:
            logger.error(f"{font_path} could not be loaded {e}")

    def __str__(self) -> str:
        """Returns a string representation of the FontAtlas."""
        return f"TextureID: {self.texture}, FontSize: {self.font_size}"

    def build_atlas(self, debug: bool = False) -> None:
        """
        Renders characters and packs them into a texture atlas.

        This method iterates through ASCII characters 32-126, renders each one
        using FreeType, and arranges them in a single large numpy array which
        will later be used to create an OpenGL texture.

        Args:
            debug: If True, saves the generated atlas as 'debug_atlas.png'.
        """
        padding = 2  # Padding between glyphs in the atlas
        atlas_w = 1024  # Fixed width for the atlas texture
        x, y, row_h = 0, 0, 0
        bitmaps_data = []

        # Iterate through printable ASCII characters
        for charcode in range(ord(" "), ord("~")):
            self.face.load_char(chr(charcode), freetype.FT_LOAD_RENDER)
            bmp = self.face.glyph.bitmap
            w, h = bmp.width, bmp.rows

            # Move to the next row if the current glyph doesn't fit
            if x + w + padding > atlas_w:
                x = 0
                y += row_h + padding
                row_h = 0

            # Copy bitmap data as the buffer is overwritten for each glyph
            if w > 0 and h > 0:
                buffer_copy = np.array(bmp.buffer, dtype=np.ubyte).reshape(h, w)
                bitmaps_data.append((buffer_copy, x, y))

            # Store glyph metadata
            self.glyphs[chr(charcode)] = {
                "size": (w, h),
                "bearing": (self.face.glyph.bitmap_left, self.face.glyph.bitmap_top),
                "advance": self.face.glyph.advance.x >> 6,  # Advance is in 1/64 pixels
                "uv": (x, y, x + w, y + h),  # UVs in pixel coordinates
            }
            x += w + padding
            row_h = max(row_h, h)

        atlas_h = y + row_h + padding
        self.atlas_w, self.atlas_h = atlas_w, atlas_h
        atlas = np.zeros((atlas_h, atlas_w), dtype=np.ubyte)

        # Blit all the individual glyph bitmaps onto the atlas
        for arr, dest_x, dest_y in bitmaps_data:
            h, w = arr.shape
            atlas[dest_y : dest_y + h, dest_x : dest_x + w] = arr

        self.atlas = atlas
        if debug:
            from PIL import Image

            img = Image.fromarray(self.atlas, mode="L")
            img.save("debug_atlas.png")
            print(f"Saved debug_atlas.png, size: {self.atlas.shape}")

    def generate_texture(self) -> None:
        """Generates and configures the OpenGL texture for the font atlas."""
        if self.atlas is None:
            return
        tex = gl.glGenTextures(1)
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)

        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        # Create a single-channel RED texture from our numpy atlas
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D,
            0,
            gl.GL_RED,
            self.atlas_w,
            self.atlas_h,
            0,
            gl.GL_RED,
            gl.GL_UNSIGNED_BYTE,
            self.atlas,
        )

        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

        # Use texture swizzling to use the RED channel as ALPHA.
        # This allows us to color the font using a uniform in the shader,
        # while using the glyph's intensity for transparency.
        # We set the texture's RGB channels to 1.0, and the A channel to the
        # value from the RED channel of the source.
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_SWIZZLE_R, gl.GL_ONE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_SWIZZLE_G, gl.GL_ONE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_SWIZZLE_B, gl.GL_ONE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_SWIZZLE_A, gl.GL_RED)

        self.texture = tex


class _Text:
    """
    Main class for managing and rendering text.

    This class acts as a controller, loading fonts and providing methods
    to render text strings to the screen. It is designed to be used as a
    singleton instance.
    """

    def __init__(self) -> None:
        """Initializes the Text renderer."""
        self._fonts: Dict[str, FontAtlas] = {}
        self._static_text: List[Any] = []  # Reserved for future use

    def add_font(self, name: str, font_file: str, size: int) -> None:
        """
        Loads a font and makes it available for rendering.

        Args:
            name: A unique name to identify this font (e.g., "main_font").
            font_file: The path to the font file.
            size: The font size in pixels.
        """
        if not hasattr(self, "vao"):
            self.vao = VAOFactory.create_vao(VAOType.SIMPLE, gl.GL_POINTS)
        font = FontAtlas(font_file, size)
        font.generate_texture()
        print(f"Font '{name}' added with texture ID: {font.texture}")
        self._fonts[name] = font

    def set_screen_size(self, w: int, h: int) -> None:
        """
        Sets the screen dimensions for the text shader.

        This should be called whenever the window is resized.

        Args:
            w: The width of the screen in pixels.
            h: The height of the screen in pixels.
        """
        ShaderLib.use(DefaultShader.TEXT)
        ShaderLib.set_uniform("textureID", 0)
        ShaderLib.set_uniform("screenSize", float(w), float(h))
        ShaderLib.set_uniform("fontSize", 1.0)
        ShaderLib.set_uniform("textColour", 1.0, 1.0, 1.0, 1.0)

    def render_text(
        self, font: str, x: int, y: int, text: str, colour: Vec3 = Vec3(1.0, 1.0, 1.0)
    ) -> None:
        """
        Renders a string of text to the screen.

        Args:
            font: The name of the font to use (previously added with add_font).
            x: The x-coordinate of the starting position (baseline).
            y: The y-coordinate of the starting position (baseline).
            text: The string of text to render.
            colour: The color of the text as a Vec4.
        """
        render_data = self._build_instances(font, text, x, y)
        if not render_data:
            return

        buffer_data = np.array(render_data, dtype=np.float32)
        atlas = self._fonts[font]

        # Enable blending for transparency
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        # Ensure text is rendered filled and restore state afterwards.
        polygon_mode = gl.glGetIntegerv(gl.GL_POLYGON_MODE)[0]
        if polygon_mode != gl.GL_FILL:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

        # Disable depth testing to ensure text is always drawn on top
        depth_test_enabled = gl.glIsEnabled(gl.GL_DEPTH_TEST)
        if depth_test_enabled:
            gl.glDisable(gl.GL_DEPTH_TEST)

        with self.vao as vao:
            data = VertexData(data=buffer_data, size=buffer_data.nbytes)
            stride = 32  # 8 floats * 4 bytes
            vao.set_data(data)
            # Vertex Attributes:
            # 0: vec2 a_position (screen position of the glyph)
            # 1: vec4 a_uvRect (u0, v0, u1, v1)
            # 2: vec2 a_size (width, height of the glyph quad)
            vao.set_vertex_attribute_pointer(0, 2, gl.GL_FLOAT, stride, 0)
            vao.set_vertex_attribute_pointer(1, 4, gl.GL_FLOAT, stride, 8)
            vao.set_vertex_attribute_pointer(2, 2, gl.GL_FLOAT, stride, 24)

            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, atlas.texture)
            ShaderLib.use(DefaultShader.TEXT)
            ShaderLib.set_uniform(
                "textColour", float(colour.x), float(colour.y), float(colour.z), 1.0
            )
            # We are drawing one point per character
            vao.set_num_indices(len(render_data) // 8)
            vao.draw()

        # Restore OpenGL state
        gl.glDisable(gl.GL_BLEND)
        if depth_test_enabled:
            gl.glEnable(gl.GL_DEPTH_TEST)
        if polygon_mode != gl.GL_FILL:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, polygon_mode)

    def _build_instances(
        self, font: str, text: str, start_x: int, start_y: int
    ) -> List[float]:
        """
        Generates vertex attribute data for each character in a string.

        This data is sent to the GPU as a single buffer. The geometry shader
        then uses this data to construct a quad for each character.

        Args:
            font: The name of the font to use.
            text: The string to process.
            start_x: The initial x-coordinate for the text baseline.
            start_y: The initial y-coordinate for the text baseline.

        Returns:
            A list of floats representing the packed vertex data for all characters.
        """
        inst = []
        atlas = self._fonts.get(font)
        if atlas:
            x, y = float(start_x), float(start_y)  # Use floats for positioning

            for ch in text:
                if ch not in atlas.glyphs:
                    continue
                g = atlas.glyphs[ch]
                w, h = g["size"]
                adv = g["advance"]
                bearing_x, bearing_y = g["bearing"]

                # UV coordinates from atlas (in pixels)
                u0_px, v0_px, u1_px, v1_px = g["uv"]

                # Normalize UVs to the range [0, 1]
                u0 = u0_px / atlas.atlas_w
                v0 = v0_px / atlas.atlas_h
                u1 = u1_px / atlas.atlas_w
                v1 = v1_px / atlas.atlas_h

                # Calculate the screen position for the top-left corner of the quad.
                # FreeType's origin is at the baseline, with +y going up.
                # Screen coordinates usually have +y going down, so we adjust.
                pos_x = x + bearing_x
                pos_y = y - bearing_y

                # Each character is defined by 8 floats:
                # pos_x, pos_y, u0, v0, u1, v1, w, h
                inst.extend([pos_x, pos_y, u0, v0, u1, v1, float(w), float(h)])
                # Advance the cursor for the next character
                x += adv
        return inst


# Create a singleton instance of the Text class for global use.
Text = _Text()
