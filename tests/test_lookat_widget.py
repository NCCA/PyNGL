import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QFrame, QVBoxLayout
from ncca.ngl import Mat4, Vec3, look_at
from ncca.ngl.widgets import LookAtWidget


def test_lookatwidget_initial_value(qtbot):
    """Test default initialization values."""
    widget = LookAtWidget()
    qtbot.addWidget(widget)

    # Default values: eye=(2,2,2), look=(0,0,0), up=y-up
    assert widget.get_eye() == Vec3(2, 2, 2)
    assert widget.get_look() == Vec3(0, 0, 0)
    assert widget.get_up() == Vec3(0, 1, 0)
    assert widget.get_name() == ""


def test_lookatwidget_constructor_with_parameters(qtbot):
    """Test initialization with custom parameters."""
    eye = Vec3(5, 5, 5)
    look = Vec3(1, 1, 1)
    name = "TestCamera"

    widget = LookAtWidget(name=name, eye=eye, look=look)
    qtbot.addWidget(widget)

    assert widget.get_eye() == eye
    assert widget.get_look() == look
    assert widget.get_name() == name
    assert widget._toggle_button.text() == name


def test_set_eye(qtbot):
    """Test setting the eye position."""
    widget = LookAtWidget()
    qtbot.addWidget(widget)

    new_eye = Vec3(10, 10, 10)
    widget.set_eye(new_eye)

    assert widget.get_eye() == new_eye


def test_set_look(qtbot):
    """Test setting the look-at position."""
    widget = LookAtWidget()
    qtbot.addWidget(widget)

    new_look = Vec3(5, 5, 5)
    widget.set_look(new_look)

    assert widget.get_look() == new_look


def test_set_up(qtbot):
    """Test setting the up vector via index."""
    widget = LookAtWidget()
    qtbot.addWidget(widget)

    # Test y-up (index 0)
    widget.set_up(0)
    assert widget.get_up() == Vec3(0, 1, 0)

    # Test x-up (index 1)
    widget.set_up(1)
    assert widget.get_up() == Vec3(1, 0, 0)

    # Test z-up (index 2)
    widget.set_up(2)
    assert widget.get_up() == Vec3(0, 0, 1)


def test_set_name(qtbot):
    """Test setting the widget name."""
    widget = LookAtWidget()
    qtbot.addWidget(widget)

    new_name = "MainCamera"
    widget.set_name(new_name)

    assert widget.get_name() == new_name
    assert widget._toggle_button.text() == new_name


def test_property_accessors(qtbot):
    """Test Qt Property wrappers."""
    widget = LookAtWidget()
    qtbot.addWidget(widget)

    # Test eye property
    widget.eye = Vec3(3, 3, 3)
    assert widget.get_eye() == Vec3(3, 3, 3)

    # Test look property
    widget.look = Vec3(1, 2, 3)
    assert widget.get_look() == Vec3(1, 2, 3)

    # Test name property
    widget.name = "PropertyCamera"
    assert widget.get_name() == "PropertyCamera"


def test_value_changed_signal_on_eye_change(qtbot):
    """Test that valueChanged signal emits when eye position changes."""
    widget = LookAtWidget()
    qtbot.addWidget(widget)

    with qtbot.waitSignal(widget.valueChanged, timeout=1000) as signal:
        widget._eye.set_value(Vec3(5, 5, 5))

    # Signal should emit a Mat4
    assert isinstance(signal.args[0], Mat4)


def test_value_changed_signal_on_look_change(qtbot):
    """Test that valueChanged signal emits when look position changes."""
    widget = LookAtWidget()
    qtbot.addWidget(widget)

    with qtbot.waitSignal(widget.valueChanged, timeout=1000) as signal:
        widget._look.set_value(Vec3(1, 1, 1))

    # Signal should emit a Mat4
    assert isinstance(signal.args[0], Mat4)


def test_value_changed_signal_on_up_change(qtbot):
    """Test that valueChanged signal emits when up vector changes."""
    widget = LookAtWidget()
    qtbot.addWidget(widget)

    with qtbot.waitSignal(widget.valueChanged, timeout=1000) as signal:
        widget._up.setCurrentIndex(1)  # Change to x-up

    # Signal should emit a Mat4
    assert isinstance(signal.args[0], Mat4)


def test_view_matrix_calculation(qtbot):
    """Test that the view matrix is calculated correctly."""
    eye = Vec3(0, 0, 5)
    look = Vec3(0, 0, 0)

    widget = LookAtWidget(eye=eye, look=look)
    qtbot.addWidget(widget)

    # Get the view matrix from widget
    view_matrix = widget.view()

    # Calculate expected matrix manually
    expected_matrix = look_at(eye, look, Vec3(0, 1, 0))

    # Compare matrices
    # Compare matrices element by element
    for i in range(4):
        for j in range(4):
            assert view_matrix[i][j] == pytest.approx(expected_matrix[i][j])


def test_view_matrix_updates_on_parameter_change(qtbot):
    """Test that view matrix updates when parameters change."""
    widget = LookAtWidget()
    qtbot.addWidget(widget)

    initial_view = widget.view()

    # Change eye position
    widget.set_eye(Vec3(10, 10, 10))

    updated_view = widget.view()

    # Matrices should be different
    assert initial_view != updated_view


def test_toggle_collapsed_expand(qtbot):
    """Test expanding the collapsible section."""
    widget = LookAtWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Initially should be expanded (button is checked)
    assert widget._toggle_button.isChecked()
    assert widget._content_widget.isVisible()
    assert widget._toggle_button.arrowType() == Qt.ArrowType.DownArrow


def test_toggle_collapsed_collapse(qtbot):
    """Test collapsing the collapsible section."""
    widget = LookAtWidget()
    qtbot.addWidget(widget)

    # Click to collapse
    widget._toggle_button.setChecked(False)
    widget.toggle_collapsed(False)

    assert not widget._content_widget.isVisible()
    assert widget._toggle_button.arrowType() == Qt.ArrowType.RightArrow


def test_toggle_collapsed_toggle_sequence(qtbot):
    """Test toggling between collapsed and expanded states."""
    widget = LookAtWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Start expanded
    assert widget._content_widget.isVisible()

    # Collapse
    widget.toggle_collapsed(False)
    assert not widget._content_widget.isVisible()

    # Expand again
    widget.toggle_collapsed(True)
    assert widget._content_widget.isVisible()


def test_world_up_vectors(qtbot):
    """Test that world_up class variable contains correct vectors."""
    widget = LookAtWidget()
    qtbot.addWidget(widget)

    assert LookAtWidget.world_up[0] == Vec3(0, 1, 0)  # y-up
    assert LookAtWidget.world_up[1] == Vec3(1, 0, 0)  # x-up
    assert LookAtWidget.world_up[2] == Vec3(0, 0, 1)  # z-up


def test_combobox_items(qtbot):
    """Test that the up vector combobox has correct items."""
    widget = LookAtWidget()
    qtbot.addWidget(widget)

    assert widget._up.count() == 3
    assert widget._up.itemText(0) == "y-up"
    assert widget._up.itemText(1) == "x-up"
    assert widget._up.itemText(2) == "z-up"


def test_matrix_recalculation_with_different_up_vectors(qtbot):
    """Test that changing up vector produces different view matrices."""
    widget = LookAtWidget(eye=Vec3(5, 5, 5), look=Vec3(0, 0, 0))
    qtbot.addWidget(widget)

    # Get matrix with y-up
    widget.set_up(0)
    matrix_y_up = widget.view()

    # Get matrix with x-up
    widget.set_up(1)
    matrix_x_up = widget.view()

    # Get matrix with z-up
    widget.set_up(2)
    matrix_z_up = widget.view()

    # All three should be different
    assert matrix_y_up != matrix_x_up
    assert matrix_y_up != matrix_z_up
    assert matrix_x_up != matrix_z_up


def test_multiple_value_changed_emissions(qtbot):
    """Test that multiple changes emit multiple signals."""
    widget = LookAtWidget()
    qtbot.addWidget(widget)

    emission_count = []
    widget.valueChanged.connect(lambda: emission_count.append(1))

    widget.set_eye(Vec3(1, 1, 1))
    widget.set_look(Vec3(2, 2, 2))
    widget.set_up(1)

    # Should have emitted 3 times
    assert len(emission_count) == 3
