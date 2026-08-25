"""Tests for Vec4Model QML widget."""

from ncca.ngl import Vec4


def test_vec4_model_default_value_is_zero(qt_app):
    """Test that Vec4Model initializes with zero vector."""
    from ncca.ngl.qml.vec4_model import Vec4Model

    model = Vec4Model()

    assert model.get_value() == Vec4(0.0, 0.0, 0.0, 0.0)


def test_setting_xyzw_properties_updates_value(qt_app):
    """Test that setting x, y, z, w properties updates the value."""
    from ncca.ngl.qml.vec4_model import Vec4Model

    model = Vec4Model()

    model.x = 1.0
    model.y = 2.0
    model.z = 3.0
    model.w = 4.0

    assert model.get_value() == Vec4(1.0, 2.0, 3.0, 4.0)


def test_setting_w_property_emits_value_changed(qt_app, qtbot):
    """Test that setting w property emits valueChanged signal."""
    from ncca.ngl.qml.vec4_model import Vec4Model

    model = Vec4Model()

    with qtbot.waitSignal(model.valueChanged, timeout=1000):
        model.w = 1.0


def test_set_value_replaces_whole_vector(qt_app):
    """Test that set_value replaces the entire vector."""
    from ncca.ngl.qml.vec4_model import Vec4Model

    model = Vec4Model()

    model.set_value(Vec4(2.0, 4.0, 6.0, 8.0))

    assert (model.x, model.y, model.z, model.w) == (2.0, 4.0, 6.0, 8.0)
