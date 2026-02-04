import glfw
import OpenGL.GL as gl
import pytest
import wgpu
import wgpu.utils


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "opengl: mark test as using an OpenGL context")
    config.addinivalue_line("markers", "webgpu: mark test as using a WebGPU device")
    config.addinivalue_line("markers", "qt: mark test as using qt for ")


def pytest_collection_modifyitems(config, items):
    """
    If `-m` is specified on the command line, this function only adds the
    'opengl' and 'webgpu' markers, allowing pytest to handle filtering.

    If no `-m` is specified, this function manually deselects all tests
    marked 'opengl' or 'webgpu' for the default test run.
    """
    # If the user is specifying a marker, just add our markers and let pytest handle it.
    if config.getoption("markexpr"):
        for item in items:
            fixtures = getattr(item, "fixturenames", [])
            if "opengl_context" in fixtures:
                item.add_marker(pytest.mark.opengl)
            elif "webgpu_device" in fixtures:
                item.add_marker(pytest.mark.webgpu)
            elif "qt_app" in fixtures:
                item.add_marker(pytest.mark.qt)
        return

    # If no marker is specified, manually partition the tests.
    remaining_items = []
    deselected_items = []
    for item in items:
        fixtures = getattr(item, "fixturenames", [])

        is_graphics = "opengl_context" in fixtures or "webgpu_device" in fixtures or "qt_app" in fixtures

        if is_graphics:
            deselected_items.append(item)
        else:
            remaining_items.append(item)

    # Modify the collection in-place and report the deselected items.
    if deselected_items:
        items[:] = remaining_items
        config.hook.pytest_deselected(items=deselected_items)


@pytest.fixture(scope="session")
def qt_app(): ...


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
