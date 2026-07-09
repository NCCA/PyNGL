import pytest
from PySide6.QtCore import Qt

from ncca.ngl import Mat4, PerspMode, perspective
from ncca.ngl.widgets import PerspectiveWidget


def test_perspectivewidget_initial_value(qt_app, qtbot):
    """Test default initialization values."""
    widget = PerspectiveWidget()
    qtbot.addWidget(widget)

    assert widget.get_fov() == pytest.approx(45.0)
    assert widget.get_aspect() == pytest.approx(1.333)
    assert widget.get_near() == pytest.approx(0.1)
    assert widget.get_far() == pytest.approx(100.0)
    assert widget.get_mode() == PerspMode.OpenGL
    assert widget.get_name() == ""


def test_perspectivewidget_constructor_with_parameters(qt_app, qtbot):
    """Test initialization with custom parameters."""
    name = "MainCamera"
    widget = PerspectiveWidget(name=name, fov=60.0, aspect=1.777, near=1.0, far=500.0)
    qtbot.addWidget(widget)

    assert widget.get_fov() == pytest.approx(60.0)
    assert widget.get_aspect() == pytest.approx(1.777)
    assert widget.get_near() == pytest.approx(1.0)
    assert widget.get_far() == pytest.approx(500.0)
    assert widget.get_name() == name
    assert widget._toggle_button.text() == name


def test_set_fov_aspect_near_far(qt_app, qtbot):
    """Test setting each field individually."""
    widget = PerspectiveWidget()
    qtbot.addWidget(widget)

    widget.set_fov(90.0)
    assert widget.get_fov() == pytest.approx(90.0)

    widget.set_aspect(2.0)
    assert widget.get_aspect() == pytest.approx(2.0)

    widget.set_near(0.5)
    assert widget.get_near() == pytest.approx(0.5)

    widget.set_far(200.0)
    assert widget.get_far() == pytest.approx(200.0)


def test_set_name(qt_app, qtbot):
    """Test setting the widget name."""
    widget = PerspectiveWidget()
    qtbot.addWidget(widget)

    widget.set_name("Cam1")
    assert widget.get_name() == "Cam1"
    assert widget._toggle_button.text() == "Cam1"


def test_property_accessors(qt_app, qtbot):
    """Test Qt Property wrappers."""
    widget = PerspectiveWidget()
    qtbot.addWidget(widget)

    widget.fov = 50.0
    assert widget.get_fov() == pytest.approx(50.0)

    widget.aspect = 1.5
    assert widget.get_aspect() == pytest.approx(1.5)

    widget.near = 0.2
    assert widget.get_near() == pytest.approx(0.2)

    widget.far = 300.0
    assert widget.get_far() == pytest.approx(300.0)

    widget.name = "PropCam"
    assert widget.get_name() == "PropCam"


def test_value_changed_signal_on_fov_change(qt_app, qtbot):
    """Test that valueChanged signal emits a Mat4 when fov changes."""
    widget = PerspectiveWidget()
    qtbot.addWidget(widget)

    with qtbot.waitSignal(widget.valueChanged, timeout=1000) as signal:
        widget.set_fov(60.0)

    assert isinstance(signal.args[0], Mat4)


def test_matrix_calculation(qt_app, qtbot):
    """Test that the perspective matrix matches ncca.ngl.perspective() directly."""
    widget = PerspectiveWidget(fov=50.0, aspect=1.5, near=0.5, far=200.0)
    qtbot.addWidget(widget)

    expected = perspective(50.0, 1.5, 0.5, 200.0, PerspMode.OpenGL)
    actual = widget.matrix()

    for i in range(4):
        for j in range(4):
            assert actual[i][j] == pytest.approx(expected[i][j])


def test_matrix_updates_on_parameter_change(qt_app, qtbot):
    """Test that the matrix updates when a parameter changes."""
    widget = PerspectiveWidget()
    qtbot.addWidget(widget)

    initial = widget.matrix()
    widget.set_fov(90.0)
    updated = widget.matrix()

    assert initial != updated


def test_toggle_collapsed_expand_and_collapse(qt_app, qtbot):
    """Test expanding/collapsing the collapsible section."""
    widget = PerspectiveWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    assert widget._toggle_button.isChecked()
    assert widget._content_widget.isVisible()
    assert widget._toggle_button.arrowType() == Qt.ArrowType.DownArrow

    widget._toggle_button.setChecked(False)
    widget.toggle_collapsed(False)
    assert not widget._content_widget.isVisible()
    assert widget._toggle_button.arrowType() == Qt.ArrowType.RightArrow

    widget.toggle_collapsed(True)
    assert widget._content_widget.isVisible()


def test_show_mode_false_hides_combobox(qt_app, qtbot):
    """Test that the mode combo box is absent when show_mode=False."""
    widget = PerspectiveWidget(show_mode=False)
    qtbot.addWidget(widget)

    assert not hasattr(widget, "_mode_combo")
    assert widget.get_mode() == PerspMode.OpenGL


def test_show_mode_true_shows_combobox(qt_app, qtbot):
    """Test that the mode combo box is present with correct items when show_mode=True."""
    widget = PerspectiveWidget(show_mode=True)
    qtbot.addWidget(widget)

    assert widget._mode_combo.count() == 3
    assert widget._mode_combo.itemText(0) == "OpenGL"
    assert widget._mode_combo.itemText(1) == "Vulkan"
    assert widget._mode_combo.itemText(2) == "WebGPU"


def test_mode_switch_changes_matrix(qt_app, qtbot):
    """Test that changing mode produces a different matrix (WebGPU vs OpenGL)."""
    widget = PerspectiveWidget(show_mode=True, fov=50.0, aspect=1.5, near=0.5, far=200.0)
    qtbot.addWidget(widget)

    opengl_matrix = widget.matrix()
    widget._mode_combo.setCurrentIndex(2)  # WebGPU
    webgpu_matrix = widget.matrix()

    assert opengl_matrix != webgpu_matrix
    assert widget.get_mode() == PerspMode.WebGPU


def test_set_mode_programmatically_without_show_mode(qt_app, qtbot):
    """Test that mode can still be set programmatically when show_mode=False."""
    widget = PerspectiveWidget(show_mode=False, fov=50.0, aspect=1.5, near=0.5, far=200.0)
    qtbot.addWidget(widget)

    widget.set_mode(PerspMode.Vulkan)
    assert widget.get_mode() == PerspMode.Vulkan
