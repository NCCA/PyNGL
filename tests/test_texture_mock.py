# from unittest.mock import Mock, patch

# import pytest
# from ncca.ngl.texture import Texture
# from ncca.ngl.image import ImageModes
# import OpenGL.GL as gl

# @pytest.fixture
# def mock_image():
#     with patch("ncca.ngl.texture.Image") as mock:
#         yield mock

# @pytest.fixture
# def mock_gl():
#     with patch("ncca.ngl.texture.gl") as mock:
#         # constant values need to be integers for some checks
#         mock.GL_RGB = 6407
#         mock.GL_RGBA = 6408
#         mock.GL_RED = 6403
#         mock.GL_RGB8 = 32849
#         mock.GL_RGBA8 = 32856
#         mock.GL_R8 = 33321
#         mock.GL_TEXTURE0 = 33984
#         mock.GL_TEXTURE_2D = 3553
#         mock.GL_LINEAR = 9729
#         mock.GL_TEXTURE_MAG_FILTER = 10240
#         mock.GL_TEXTURE_MIN_FILTER = 10241
#         mock.GL_UNSIGNED_BYTE = 5121
#         yield mock

# def test_init(mock_image):
#     t = Texture("test.png")
#     mock_image.assert_called_with("test.png")
#     assert t._texture_id == 0
#     assert t._multi_texture_id == 0

# def test_properties_delegation(mock_image):
#     t = Texture()
#     img_instance = t._image
#     img_instance.width = 100
#     img_instance.height = 200

#     assert t.width == 100
#     assert t.height == 200

# def test_format_rgb(mock_image, mock_gl):
#     t = Texture()
#     t._image.mode.value = "RGB"
#     assert t.format == mock_gl.GL_RGB

# def test_format_rgba(mock_image, mock_gl):
#     t = Texture()
#     t._image.mode.value = "RGBA"
#     assert t.format == mock_gl.GL_RGBA

# def test_format_gray(mock_image, mock_gl):
#     t = Texture()
#     t._image.mode.value = "L"
#     assert t.format == mock_gl.GL_RED

# def test_format_unknown(mock_image):
#     t = Texture()
#     t._image.mode = None
#     assert t.format == 0

#     t._image.mode = Mock()
#     t._image.mode.value = "UNKNOWN"
#     assert t.format == 0

# def test_internal_format_rgb(mock_image, mock_gl):
#     t = Texture()
#     t._image.mode.value = "RGB"
#     assert t.internal_format == mock_gl.GL_RGB8

# def test_internal_format_rgba(mock_image, mock_gl):
#     t = Texture()
#     t._image.mode.value = "RGBA"
#     assert t.internal_format == mock_gl.GL_RGBA8

# def test_internal_format_gray(mock_image, mock_gl):
#     t = Texture()
#     t._image.mode.value = "L"
#     assert t.internal_format == mock_gl.GL_R8

# def test_internal_format_unknown(mock_image):
#     t = Texture()
#     t._image.mode = None
#     assert t.internal_format == 0

#     t._image.mode = Mock()
#     t._image.mode.value = "UNKNOWN"
#     assert t.internal_format == 0

# def test_load_image(mock_image):
#     t = Texture()
#     t._image.load.return_value = True
#     assert t.load_image("test.png") is True
#     t._image.load.assert_called_with("test.png")

# def test_get_pixels(mock_image):
#     t = Texture()
#     mock_bytes = b"pixeldata"
#     t._image.get_pixels.return_value.tobytes.return_value = mock_bytes
#     assert t.get_pixels() == mock_bytes

# def test_set_texture_gl_success(mock_image, mock_gl):
#     t = Texture()
#     # verify behavior when dimensions are valid
#     t._image.width = 10
#     t._image.height = 10
#     t._image.mode.value = "RGB"
#     mock_gl.glGenTextures.return_value = 123

#     tex_id = t.set_texture_gl()

#     assert tex_id == 123
#     assert t._texture_id == 123

#     mock_gl.glGenTextures.assert_called_once()
#     mock_gl.glActiveTexture.assert_called_with(mock_gl.GL_TEXTURE0)
#     mock_gl.glBindTexture.assert_called_with(mock_gl.GL_TEXTURE_2D, 123)
#     # Check if parameters are set
#     assert mock_gl.glTexParameteri.call_count == 2
#     mock_gl.glTexImage2D.assert_called_once()
#     mock_gl.glGenerateMipmap.assert_called_once()


# def test_set_texture_gl_fail_dimensions(mock_image, mock_gl):
#     t = Texture()
#     t._image.width = 0
#     t._image.height = 10

#     assert t.set_texture_gl() == 0
#     mock_gl.glGenTextures.assert_not_called()

# def test_set_multi_texture(mock_image, mock_gl):
#     t = Texture()
#     t._image.width = 10
#     t._image.height = 10
#     t.set_multi_texture(5)

#     t.set_texture_gl()

#     mock_gl.glActiveTexture.assert_called_with(mock_gl.GL_TEXTURE0 + 5)
