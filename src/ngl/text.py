"""
This is a python implementation of the C++ Text class from NGL
"""

import freetype
import numpy as np
import OpenGL.GL as gl

# from ngl import DefaultShader, ShaderLib, VAOFactory, VAOType, VertexData
from .shader_lib import DefaultShader, ShaderLib
from .simple_vao import VertexData
from .vao_factory import VAOFactory, VAOType
from .vec4 import Vec4

# ------------------------------
# Font atlas builder
# ------------------------------
class FontAtlas:
    def __init__(self, font_path, font_size=48, debug=False):
        self.face = freetype.Face(font_path)
        self.face.set_pixel_sizes(0, font_size)
        self.font_size = font_size
        self.glyphs = {}
        self.texture = 0
        self.build_atlas()
    def __str__(self) :
        return f"{self.texture} {self.font_size}"

    def build_atlas(self, debug=False):
        padding = 2
        atlas_w = 1024
        x, y, row_h = 0, 0, 0
        bitmaps_data = []

        for charcode in range(ord(" "), ord("~")):
            self.face.load_char(chr(charcode), freetype.FT_LOAD_RENDER)
            bmp = self.face.glyph.bitmap
            w, h = bmp.width, bmp.rows

            if x + w + padding > atlas_w:
                x = 0
                y += row_h + padding
                row_h = 0

            # Copy bitmap data as the buffer is overwritten for each glyph
            if w > 0 and h > 0:
                buffer_copy = np.array(bmp.buffer, dtype=np.ubyte).reshape(h, w)
                bitmaps_data.append((buffer_copy, x, y))

            self.glyphs[chr(charcode)] = {
                "size": (w, h),
                "bearing": (self.face.glyph.bitmap_left, self.face.glyph.bitmap_top),
                "advance": self.face.glyph.advance.x >> 6,
                "uv": (x, y, x + w, y + h),
            }
            x += w + padding
            row_h = max(row_h, h)

        atlas_h = y + row_h + padding
        self.atlas_w, self.atlas_h = atlas_w, atlas_h
        atlas = np.zeros((atlas_h, atlas_w), dtype=np.ubyte)

        for arr, dest_x, dest_y in bitmaps_data:
            h, w = arr.shape
            atlas[dest_y : dest_y + h, dest_x : dest_x + w] = arr

        self.atlas = atlas
        if debug:
            # Save the full atlas for debugging
            from PIL import Image

            img = Image.fromarray(self.atlas, mode="L")
            img.save("debug_atlas.png")
            print("Saved debug_atlas.png, size:", self.atlas.shape)

    def generate_texture(self):
        tex = gl.glGenTextures(1)
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)

        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
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

        #  swizzle RED -> ALPHA, force RGB = 1 for mac
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_SWIZZLE_R, gl.GL_ONE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_SWIZZLE_G, gl.GL_ONE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_SWIZZLE_B, gl.GL_ONE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_SWIZZLE_A, gl.GL_RED)

        self.texture = tex


class _Text:
    def __init__(self):
        self._fonts = {}
        self._static_text = []

    def add_font(self, name: str, font_file: str, size: int) -> None:
        """
        add a font  to the text class,
        Parameters :
            name  : the name to use when using the font
            font_file : the path / name of the font to load
            size : the size of the fon
        """
        font = FontAtlas(font_file, size)
        print(font)
        font.generate_texture()
        print(font)
        print(f"adding {name} to atlas")
        self._fonts[name] = font

    def set_screen_size(self, w: int, h: int) -> None:
        ShaderLib.use(DefaultShader.TEXT)
        ShaderLib.set_uniform("u_texture", 0)
        ShaderLib.set_uniform("u_screenSize", w, h)
        ShaderLib.set_uniform("u_fontSize", 1.0)
        ShaderLib.set_uniform("u_textColor", 1.0, 1.0, 1.0, 1.0)

    def render_dynamic_text(self, font: str, x: int, y: int, text: str, colour):
        render_data = self._build_instances(font, text, x, y)
        if not render_data:
            return
        buffer_data = np.array(render_data, dtype=np.float32)
        vao = VAOFactory.create_vao(VAOType.SIMPLE, gl.GL_POINTS)
        atlas = self._fonts[font]
        with vao:
            data = VertexData(data=buffer_data, size=buffer_data.nbytes)
            stride = 8 * Vec4.sizeof()  # 8 floats * 4 bytes
            vao.set_data(data)
            vao.set_vertex_attribute_pointer(0, 2, gl.GL_FLOAT, stride, 0)
            vao.set_vertex_attribute_pointer(1, 4, gl.GL_FLOAT, stride, 2 * Vec4.sizeof())
            vao.set_vertex_attribute_pointer(2, 2, gl.GL_FLOAT, stride, 6 * Vec4.sizeof())

            gl.glActiveTexture(gl.GL_TEXTURE0)
            print(f"{atlas.texture=}")
            gl.glBindTexture(gl.GL_TEXTURE_2D, atlas.texture)
            ShaderLib.use(DefaultShader.TEXT)
            ShaderLib.set_uniform("u_textColor", colour.x, colour.y, colour.z, 1.0)
            vao.set_num_indices(len(render_data))
            vao.draw()
        vao.remove_vao()

    def _build_instances(self, font: str, text: str, start_x, start_y):
        """
        build point / uv combos for each character from the atlas. This will feed
        into the geometry shader to render the textured quads
        """
        inst = []
        atlas = self._fonts.get(font)
        if atlas:
            x, y = start_x, start_y  # y is baseline

            for ch in text:
                if ch not in atlas.glyphs:
                    continue
                g = atlas.glyphs[ch]
                w, h = g["size"]
                adv = g["advance"]
                bearing_x, bearing_y = g["bearing"]

                # UV coordinates from atlas
                u0_px, v0_px, u1_px, v1_px = g["uv"]

                # Normalize UVs
                u0 = u0_px / atlas.atlas_w
                v0 = v0_px / atlas.atlas_h
                u1 = u1_px / atlas.atlas_w
                v1 = v1_px / atlas.atlas_h

                # Calculate quad position using bearing
                pos_x = x + bearing_x
                pos_y = y - bearing_y

                # Pass UVs straight through, without any flipping yet.
                inst.extend([pos_x, pos_y, u0, v0, u1, v1, w, h])
                x += adv
        return inst


# class Character(object):
#     """simple class to hold character data for rendering"""

#     def __init__(self, texture_id, sizex, sizey, bearingx, bearingy, advance):
#         self.texture_id = texture_id
#         self.sizex = sizex
#         self.sizey = sizey
#         self.bearingx = bearingx
#         self.bearingy = bearingy
#         self.advance = advance


# class Text(object):
#     def __init__(self, font_name: str, size: int):
#         """
#         ctor, requires a font name and size
#         """
#         self.characters = {}
#         face = freetype.Face(font_name)
#         if not face:
#             logger.error(f"Font '{font_name}' not found")
#             raise ValueError(f"Font '{font_name}' not found")
#         face.set_pixel_sizes(0, size)
#         # disable byte-alignment restriction
#         gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
#         start_char = " "
#         end_char = "~"

#         for code in range(ord(start_char), ord(end_char) + 1):
#             c = chr(code)
#             face.load_char(c, freetype.FT_LOAD_RENDER)
#             # # now we create the OpenGL texture ID and bind to make it active
#             # texture_id = gl.glGenTextures(1)
#             # gl.glActiveTexture(gl.GL_TEXTURE0)

#             # gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
#             # # set texture options
#             # gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
#             # gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
#             # gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
#             # gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)

#             # # fmt: off
#             # gl.glTexImage2D(
#             #     gl.GL_TEXTURE_2D,0,gl.GL_R8,
#             #     face.glyph.bitmap.width,face.glyph.bitmap.rows, 0,
#             #     gl.GL_RED, gl.GL_UNSIGNED_BYTE,bytes(face.glyph.bitmap.buffer))
#             # fmt: on
#             # generate and bind texture
#             texture_id = gl.glGenTextures(1)
#             gl.glActiveTexture(gl.GL_TEXTURE0)
#             gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)

#             # upload glyph bitmap as single channel texture
#             gl.glTexImage2D(
#                 gl.GL_TEXTURE_2D,
#                 0,
#                 gl.GL_RED,  # internal format (driver accepts it on macOS, though not spec-legal)
#                 face.glyph.bitmap.width,
#                 face.glyph.bitmap.rows,
#                 0,
#                 gl.GL_RED,  # external format (matches buffer)
#                 gl.GL_UNSIGNED_BYTE,
#                 face.glyph.bitmap.buffer,  # FreeType buffer is already bytes-like
#             )

#             # set texture options
#             gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
#             gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
#             gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
#             gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
#             char = Character(
#                 texture_id,
#                 face.glyph.bitmap.width,
#                 face.glyph.bitmap.rows,
#                 face.glyph.bitmap_left,
#                 face.glyph.bitmap_top,
#                 face.glyph.advance.x,
#             )
#             self.characters[c] = char

#         gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 4)
#         self.set_colour(0.0, 0.0, 0.0)
#         self.vao = VAOFactory.create_vao(VAOType.SIMPLE, gl.GL_TRIANGLES)
#         ShaderLib.use(DefaultShader.TEXT)
#         ShaderLib.set_uniform("text", 0)

#     def __del__(self):
#         for _, font in self.characters.items():
#             gl.glDeleteTextures(1, font.texture_id)

#     def render_text(self, x: float, y: float, text: str):
#         """
#         renders the text string at screen coordinates x,y
#         """
#         ShaderLib.use(DefaultShader.TEXT)

#         gl.glActiveTexture(gl.GL_TEXTURE0)
#         gl.glEnable(gl.GL_BLEND)
#         gl.glDisable(gl.GL_DEPTH_TEST)
#         gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
#         gl.glEnable(gl.GL_CULL_FACE)
#         scale = 1.0
#         try:
#             with self.vao:
#                 for char in text:
#                     fc = self.characters[char]
#                     xpos = x + fc.bearingx * scale
#                     ypos = y - (fc.sizey - fc.bearingy) * scale
#                     w = fc.sizex * scale
#                     h = fc.sizey * scale
#                     # fmt: off
#                     vertices = np.array(
#                     [
#                         xpos, ypos + h, 0.0, 0.0,
#                         xpos, ypos, 0.0, 1.0,
#                         xpos + w, ypos, 1.0, 1.0,
#                         xpos, ypos + h, 0.0, 0.0,
#                         xpos + w, ypos, 1.0, 1.0,
#                         xpos + w, ypos + h, 1.0, 0.0,
#                     ], dtype=np.float32)
#                     # fmt: on
#                     gl.glActiveTexture(gl.GL_TEXTURE0)
#                     gl.glBindTexture(gl.GL_TEXTURE_2D, fc.texture_id)
#                     data = VertexData(
#                         data=vertices,
#                         size=len(vertices) // 4,
#                         mode=gl.GL_DYNAMIC_DRAW,
#                     )
#                     self.vao.set_data(data)
#                     self.vao.set_vertex_attribute_pointer(0, 4, gl.GL_FLOAT, 0, 0)
#                     self.vao.set_num_indices(6)
#                     self.vao.draw()
#                     x += (fc.advance >> 6) * scale
#         except Exception as e:
#             print(f"Error rendering text: {e}")
#         gl.glDisable(gl.GL_BLEND)
#         gl.glEnable(gl.GL_DEPTH_TEST)
#         gl.glDisable(gl.GL_CULL_FACE)

#     def set_screen_size(self, w: int, h: int):
#         """
#         sets the screen size for the projection matrix
#         """
#         ShaderLib.use(DefaultShader.TEXT)
#         ortho_proj = ortho(0, w, 0, h, 0.1, 100.0)
#         print(f"{ortho_proj=}")
#         ShaderLib.set_uniform("projection", ortho_proj)

#     def set_colour(self, r, g, b):
#         """
#         sets the colour of the text
#         """
#         ShaderLib.use(DefaultShader.TEXT)
#         ShaderLib.set_uniform("textColour", r, g, b)

#     def set_colour_vec3(self, c: Vec3):
#         """
#         sets the colour of the text from a Vec3
#         """
#         ShaderLib.use(DefaultShader.TEXT)
#         ShaderLib.set_uniform("textColour", c.x, c.y, c.z)


Text = _Text()
