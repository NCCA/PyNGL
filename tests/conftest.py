import gc

import glfw
import OpenGL.GL as gl
import pytest
import wgpu
import wgpu.utils


def pytest_collection_modifyitems(config, items):
    """
    Ensure WebGPU tests run before OpenGL tests to avoid context conflicts
    This is fine on mac as both are Metal backends.
    """

    opengl_tests = []
    webgpu_tests = []
    other_tests = []

    for item in items:
        fixtures = getattr(item, "fixturenames", [])
        if "opengl_context" in fixtures or any("opengl" in f for f in fixtures):
            opengl_tests.append(item)
        elif "webgpu_device" in fixtures or any("webgpu" in f for f in fixtures):
            webgpu_tests.append(item)
        else:
            other_tests.append(item)

    # Reorder:  Other -> WebGPU -> OpenGL this avoids context conflicts on Linux
    # WebGPU cleans nicely OpenGL not so much!
    items[:] = other_tests + webgpu_tests + opengl_tests

    print(f"\nTest execution order: {len(opengl_tests)} OpenGL, {len(other_tests)} Other, {len(webgpu_tests)} WebGPU")


@pytest.fixture(scope="session")
def opengl_context():
    if not glfw.init():
        pytest.skip("Failed to initialize GLFW")

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


@pytest.fixture(scope="session")
def webgpu_device():
    # Get the default WebGPU device
    device = wgpu.utils.get_default_device()
    if device is None:
        raise RuntimeError("Could not get a WebGPU device.")
    yield device
    del device
    gc.collect()
