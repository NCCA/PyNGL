from ncca.ngl import PerspMode, perspective


def test_default_values_and_matrix(qt_app):
    from ncca.ngl.qml.perspective_model import PerspectiveModel

    model = PerspectiveModel()

    assert model.fov == 45.0
    assert model.aspect == 1.333
    assert model.near == 0.1
    assert model.far == 100.0
    assert model.modeIndex == 0
    assert model.get_matrix() == perspective(45.0, 1.333, 0.1, 100.0, PerspMode.OpenGL)


def test_changing_fov_updates_matrix(qt_app):
    from ncca.ngl.qml.perspective_model import PerspectiveModel

    model = PerspectiveModel()
    model.fov = 60.0

    assert model.get_matrix() == perspective(60.0, 1.333, 0.1, 100.0, PerspMode.OpenGL)


def test_changing_aspect_near_far_updates_matrix(qt_app):
    from ncca.ngl.qml.perspective_model import PerspectiveModel

    model = PerspectiveModel()
    model.aspect = 1.777
    model.near = 1.0
    model.far = 500.0

    assert model.get_matrix() == perspective(45.0, 1.777, 1.0, 500.0, PerspMode.OpenGL)


def test_changing_mode_index_updates_matrix(qt_app):
    from ncca.ngl.qml.perspective_model import PerspectiveModel

    model = PerspectiveModel()
    model.modeIndex = model.mode_names().index("WebGPU")

    assert model.get_matrix() == perspective(45.0, 1.333, 0.1, 100.0, PerspMode.WebGPU)


def test_mode_names(qt_app):
    from ncca.ngl.qml.perspective_model import PerspectiveModel

    model = PerspectiveModel()

    assert model.mode_names() == ["OpenGL", "Vulkan", "WebGPU"]


def test_changing_fov_emits_value_changed(qt_app, qtbot):
    from ncca.ngl.qml.perspective_model import PerspectiveModel

    model = PerspectiveModel()

    with qtbot.waitSignal(model.valueChanged, timeout=1000):
        model.fov = 70.0


def test_matrix_text_format(qt_app):
    from ncca.ngl.qml.perspective_model import PerspectiveModel

    model = PerspectiveModel()
    text = model.matrix_text()

    rows = text.split("\n")
    assert len(rows) == 4
    for row in rows:
        assert len(row.split()) == 4
