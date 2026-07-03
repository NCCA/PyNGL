import pytest
from PySide6.QtCore import Qt

from ncca.ngl import Mat4, Transform, Vec3
from ncca.ngl.widgets import TransformWidget


def test_transformwidget_initial_value(qt_app, qtbot):
    """Test default initialization values."""
    widget = TransformWidget()
    qtbot.addWidget(widget)

    # Default values: position=(0,0,0), rotation=(0,0,0), scale=(1,1,1)
    assert widget._position.get_value() == Vec3(0, 0, 0)
    assert widget._rotation.get_value() == Vec3(0, 0, 0)
    assert widget._scale.get_value() == Vec3(1, 1, 1)
    assert widget.name == ""


def test_transformwidget_constructor_with_name(qt_app, qtbot):
    """Test initialization with custom name parameter."""
    name = "TestTransform"

    widget = TransformWidget(name=name)
    qtbot.addWidget(widget)

    assert widget.name == name
    assert widget._toggle_button.text() == name


def test_set_name(qt_app, qtbot):
    """Test setting the widget name."""
    widget = TransformWidget()
    qtbot.addWidget(widget)

    new_name = "MyTransform"
    widget.set_name(new_name)

    assert widget.name == new_name
    assert widget._toggle_button.text() == new_name


def test_property_accessor_name(qt_app, qtbot):
    """Test Qt Property wrapper for name."""
    widget = TransformWidget()
    qtbot.addWidget(widget)

    # Test name property
    widget.name = "PropertyTransform"
    assert widget.name == "PropertyTransform"


def test_position_range(qt_app, qtbot):
    """Test that position has correct range set."""
    widget = TransformWidget()
    qtbot.addWidget(widget)

    assert widget._position.x_spinbox.minimum() == pytest.approx(-20)
    assert widget._position.x_spinbox.maximum() == pytest.approx(20)
    assert widget._position.y_spinbox.minimum() == pytest.approx(-20)
    assert widget._position.y_spinbox.maximum() == pytest.approx(20)
    assert widget._position.z_spinbox.minimum() == pytest.approx(-20)
    assert widget._position.z_spinbox.maximum() == pytest.approx(20)


def test_rotation_range(qt_app, qtbot):
    """Test that rotation has correct range set."""
    widget = TransformWidget()
    qtbot.addWidget(widget)

    assert widget._rotation.x_spinbox.minimum() == pytest.approx(-360)
    assert widget._rotation.x_spinbox.maximum() == pytest.approx(360)
    assert widget._rotation.y_spinbox.minimum() == pytest.approx(-360)
    assert widget._rotation.y_spinbox.maximum() == pytest.approx(360)
    assert widget._rotation.z_spinbox.minimum() == pytest.approx(-360)
    assert widget._rotation.z_spinbox.maximum() == pytest.approx(360)


def test_scale_range(qt_app, qtbot):
    """Test that scale has correct range set."""
    widget = TransformWidget()
    qtbot.addWidget(widget)

    assert widget._scale.x_spinbox.minimum() == pytest.approx(-20)
    assert widget._scale.x_spinbox.maximum() == pytest.approx(20)
    assert widget._scale.y_spinbox.minimum() == pytest.approx(-20)
    assert widget._scale.y_spinbox.maximum() == pytest.approx(20)
    assert widget._scale.z_spinbox.minimum() == pytest.approx(-20)
    assert widget._scale.z_spinbox.maximum() == pytest.approx(20)


def test_value_changed_signal_on_position_change(qt_app, qtbot):
    """Test that valueChanged signal emits when position changes."""
    widget = TransformWidget()
    qtbot.addWidget(widget)

    with qtbot.waitSignal(widget.valueChanged, timeout=1000) as signal:
        widget._position.set_value(Vec3(5, 5, 5))

    # Signal should emit a Mat4
    assert isinstance(signal.args[0], Mat4)


def test_value_changed_signal_on_rotation_change(qt_app, qtbot):
    """Test that valueChanged signal emits when rotation changes."""
    widget = TransformWidget()
    qtbot.addWidget(widget)

    with qtbot.waitSignal(widget.valueChanged, timeout=1000) as signal:
        widget._rotation.set_value(Vec3(45, 90, 180))

    # Signal should emit a Mat4
    assert isinstance(signal.args[0], Mat4)


def test_value_changed_signal_on_scale_change(qt_app, qtbot):
    """Test that valueChanged signal emits when scale changes."""
    widget = TransformWidget()
    qtbot.addWidget(widget)

    with qtbot.waitSignal(widget.valueChanged, timeout=1000) as signal:
        widget._scale.set_value(Vec3(2, 2, 2))

    # Signal should emit a Mat4
    assert isinstance(signal.args[0], Mat4)


def test_value_changed_signal_on_rotation_order_change(qt_app, qtbot):
    """Test that valueChanged signal emits when rotation order changes."""
    widget = TransformWidget()
    qtbot.addWidget(widget)

    with qtbot.waitSignal(widget.valueChanged, timeout=1000) as signal:
        widget._rot_order.setCurrentIndex(1)  # Change to "yzx"

    # Signal should emit a Mat4
    assert isinstance(signal.args[0], Mat4)


def test_rotation_order_combobox_items(qt_app, qtbot):
    """Test that the rotation order combobox has correct items."""
    widget = TransformWidget()
    qtbot.addWidget(widget)

    expected_orders = ["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"]

    assert widget._rot_order.count() == len(expected_orders)
    for i, order in enumerate(expected_orders):
        assert widget._rot_order.itemText(i) == order


def test_rotation_order_class_variable(qt_app, qtbot):
    """Test that _rotation_order class variable contains correct values."""
    expected_orders = ["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"]
    assert TransformWidget._rotation_order == expected_orders


def test_toggle_collapsed_expand(qt_app, qtbot):
    """Test expanding the collapsible section."""
    widget = TransformWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Initially should be expanded (button is checked)
    assert widget._toggle_button.isChecked()
    assert widget._content_widget.isVisible()
    assert widget._toggle_button.arrowType() == Qt.ArrowType.DownArrow


def test_toggle_collapsed_collapse(qt_app, qtbot):
    """Test collapsing the collapsible section."""
    widget = TransformWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    # Click to collapse
    widget._toggle_button.setChecked(False)
    widget.toggle_collapsed(False)

    assert not widget._content_widget.isVisible()
    assert widget._toggle_button.arrowType() == Qt.ArrowType.RightArrow


def test_toggle_collapsed_toggle_sequence(qt_app, qtbot):
    """Test toggling between collapsed and expanded states."""
    widget = TransformWidget()
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


def test_transform_matrix_calculation_identity(qt_app, qtbot):
    """Test that default transform produces identity-like matrix."""
    widget = TransformWidget()
    qtbot.addWidget(widget)

    # Create expected transform manually
    tx = Transform()
    tx.set_order("xyz")
    tx.set_position(0, 0, 0)
    tx.set_rotation(0, 0, 0)
    tx.set_scale(1, 1, 1)
    expected_matrix = tx.matrix()

    # Trigger matrix update by changing a value back to itself
    with qtbot.waitSignal(widget.valueChanged, timeout=1000) as signal:
        widget._position.set_value(Vec3(0, 0, 0))

    result_matrix = signal.args[0]

    # Compare matrices element by element
    for i in range(4):
        for j in range(4):
            assert result_matrix[i][j] == pytest.approx(expected_matrix[i][j])


def test_transform_matrix_with_translation(qt_app, qtbot):
    """Test transformation matrix with translation."""
    widget = TransformWidget()
    qtbot.addWidget(widget)

    position = Vec3(5, 10, 15)

    with qtbot.waitSignal(widget.valueChanged, timeout=1000) as signal:
        widget._position.set_value(position)

    result_matrix = signal.args[0]

    # Create expected transform
    tx = Transform()
    tx.set_order("xyz")
    tx.set_position(position.x, position.y, position.z)
    tx.set_rotation(0, 0, 0)
    tx.set_scale(1, 1, 1)
    expected_matrix = tx.matrix()

    # Compare matrices element by element
    for i in range(4):
        for j in range(4):
            assert result_matrix[i][j] == pytest.approx(expected_matrix[i][j])


def test_transform_matrix_with_rotation(qt_app, qtbot):
    """Test transformation matrix with rotation."""
    widget = TransformWidget()
    qtbot.addWidget(widget)

    rotation = Vec3(45, 90, 180)

    with qtbot.waitSignal(widget.valueChanged, timeout=1000) as signal:
        widget._rotation.set_value(rotation)

    result_matrix = signal.args[0]

    # Create expected transform
    tx = Transform()
    tx.set_order("xyz")
    tx.set_position(0, 0, 0)
    tx.set_rotation(rotation.x, rotation.y, rotation.z)
    tx.set_scale(1, 1, 1)
    expected_matrix = tx.matrix()

    # Compare matrices element by element
    for i in range(4):
        for j in range(4):
            assert result_matrix[i][j] == pytest.approx(expected_matrix[i][j])


def test_transform_matrix_with_scale(qt_app, qtbot):
    """Test transformation matrix with scale."""
    widget = TransformWidget()
    qtbot.addWidget(widget)

    scale = Vec3(2, 3, 4)

    with qtbot.waitSignal(widget.valueChanged, timeout=1000) as signal:
        widget._scale.set_value(scale)

    result_matrix = signal.args[0]

    # Create expected transform
    tx = Transform()
    tx.set_order("xyz")
    tx.set_position(0, 0, 0)
    tx.set_rotation(0, 0, 0)
    tx.set_scale(scale.x, scale.y, scale.z)
    expected_matrix = tx.matrix()

    # Compare matrices element by element
    for i in range(4):
        for j in range(4):
            assert result_matrix[i][j] == pytest.approx(expected_matrix[i][j])


def test_transform_matrix_with_different_rotation_order(qt_app, qtbot):
    """Test that different rotation orders produce different matrices."""
    widget = TransformWidget()
    qtbot.addWidget(widget)

    # Set non-zero rotation
    widget._rotation.set_value(Vec3(45, 45, 45))

    # Get matrix with xyz order
    widget._rot_order.setCurrentIndex(0)  # xyz
    with qtbot.waitSignal(widget.valueChanged, timeout=1000) as signal_xyz:
        widget._position.set_value(Vec3(0, 0, 0))  # Trigger update
    matrix_xyz = signal_xyz.args[0]

    # Get matrix with zyx order
    with qtbot.waitSignal(widget.valueChanged, timeout=1000) as signal_zyx:
        widget._rot_order.setCurrentIndex(5)  # zyx
    matrix_zyx = signal_zyx.args[0]

    # Matrices should be different for different rotation orders
    matrices_different = False
    for i in range(4):
        for j in range(4):
            if abs(matrix_xyz[i][j] - matrix_zyx[i][j]) > 1e-6:
                matrices_different = True
                break
        if matrices_different:
            break

    assert matrices_different, "Matrices should differ for different rotation orders"


def test_transform_matrix_full_transform(qt_app, qtbot):
    """Test transformation matrix with position, rotation, and scale."""
    widget = TransformWidget()
    qtbot.addWidget(widget)

    position = Vec3(1, 2, 3)
    rotation = Vec3(30, 45, 60)
    scale = Vec3(2, 2, 2)

    widget._position.set_value(position)
    widget._rotation.set_value(rotation)

    with qtbot.waitSignal(widget.valueChanged, timeout=1000) as signal:
        widget._scale.set_value(scale)

    result_matrix = signal.args[0]

    # Create expected transform
    tx = Transform()
    tx.set_order("xyz")
    tx.set_position(position.x, position.y, position.z)
    tx.set_rotation(rotation.x, rotation.y, rotation.z)
    tx.set_scale(scale.x, scale.y, scale.z)
    expected_matrix = tx.matrix()

    # Compare matrices element by element
    for i in range(4):
        for j in range(4):
            assert result_matrix[i][j] == pytest.approx(expected_matrix[i][j])


def test_multiple_value_changed_emissions(qt_app, qtbot):
    """Test that multiple changes emit multiple signals."""
    widget = TransformWidget()
    qtbot.addWidget(widget)

    emission_count = []
    widget.valueChanged.connect(lambda: emission_count.append(1))

    widget._position.set_value(Vec3(1, 1, 1))
    widget._rotation.set_value(Vec3(45, 45, 45))
    widget._scale.set_value(Vec3(2, 2, 2))
    widget._rot_order.setCurrentIndex(1)

    # Should have emitted 4 times
    assert len(emission_count) == 4


def test_widget_contains_vec3_widgets(qt_app, qtbot):
    """Test that the widget contains the expected Vec3Widget children."""
    widget = TransformWidget()
    qtbot.addWidget(widget)

    # Verify Vec3Widgets exist and have correct labels
    assert widget._position.get_name() == "Position"
    assert widget._rotation.get_name() == "Rotation"
    assert widget._scale.get_name() == "Scale"


def test_initial_rotation_order_is_xyz(qt_app, qtbot):
    """Test that the initial rotation order is xyz (index 0)."""
    widget = TransformWidget()
    qtbot.addWidget(widget)

    assert widget._rot_order.currentIndex() == 0
    assert widget._rot_order.currentText() == "xyz"
