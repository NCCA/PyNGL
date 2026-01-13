import glfw
import OpenGL.GL as gl
import pytest


@pytest.fixture(scope="session")
def opengl_context():
    if not glfw.init():
        pytest.skip("Failed to initialize GLFW")
    # OSMesa requires this
    glfw.window_hint(glfw.CONTEXT_CREATION_API, glfw.OSMESA_CONTEXT_API)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)
    glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
    window = glfw.create_window(100, 100, "Test", None, None)

    if not window:
        glfw.terminate()
        pytest.skip("Failed to create GLFW window")

    glfw.make_context_current(window)
    yield

    glfw.terminate()
