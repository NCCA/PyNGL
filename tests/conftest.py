import glfw
import OpenGL.GL as gl
import pytest
import wgpu
import wgpu.utils


def pytest_addoption(parser):
    """Allow the coverage job to include graphics and Qt tests."""
    parser.addoption("--run-graphics", action="store_true", default=False)


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "opengl: mark test as using an OpenGL context")
    config.addinivalue_line("markers", "webgpu: mark test as using a WebGPU device")
    config.addinivalue_line("markers", "qt: mark test as using qt for ")


def pytest_collection_modifyitems(config, items):
    """Select graphics tests when requested by marker or --run-graphics.

    The default run leaves out tests using OpenGL, WebGPU or Qt fixtures.
    """
    # If the user is specifying a marker, just add our markers and let pytest handle it.
    if config.getoption("markexpr") or config.getoption("--run-graphics"):
        for item in items:
            fixtures = getattr(item, "fixturenames", [])
            if "opengl_context" in fixtures:
                item.add_marker(pytest.mark.opengl)
            elif "webgpu_device" in fixtures:
                item.add_marker(pytest.mark.webgpu)
            elif any(name in fixtures for name in ("qt_app", "qtbot", "qapp")):
                item.add_marker(pytest.mark.qt)
        return

    # If no marker is specified, manually partition the tests.
    remaining_items = []
    deselected_items = []
    for item in items:
        fixtures = getattr(item, "fixturenames", [])

        is_graphics = (
            "opengl_context" in fixtures
            or "webgpu_device" in fixtures
            or any(name in fixtures for name in ("qt_app", "qtbot", "qapp"))
        )

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
    """Provide a WebGPU device or skip when no adapter is available."""
    try:
        device = wgpu.utils.get_default_device()
    except (RuntimeError, wgpu.GPUError) as error:
        reason = str(error).splitlines()[0]
        pytest.skip(f"WebGPU is not available: {reason}")

    if device is None:
        pytest.skip("WebGPU is not available: no suitable device found")

    yield device
