"""Tests for Vec3Model QML widget."""

from ncca.ngl import Vec3


def test_vec3_model_default_value_is_zero(qt_app):
    """Test that Vec3Model initializes with zero vector."""
    from ncca.ngl.qml.vec3_model import Vec3Model

    model = Vec3Model()

    assert model.get_value() == Vec3(0.0, 0.0, 0.0)


def test_setting_xyz_properties_updates_value(qt_app):
    """Test that setting x, y, z properties updates the value."""
    from ncca.ngl.qml.vec3_model import Vec3Model

    model = Vec3Model()

    model.x = 1.0
    model.y = 2.0
    model.z = 3.0

    assert model.get_value() == Vec3(1.0, 2.0, 3.0)


def test_setting_z_property_emits_value_changed(qt_app, qtbot):
    """Test that setting z property emits valueChanged signal."""
    from ncca.ngl.qml.vec3_model import Vec3Model

    model = Vec3Model()

    with qtbot.waitSignal(model.valueChanged, timeout=1000):
        model.z = 5.0


def test_set_value_replaces_whole_vector(qt_app):
    """Test that set_value replaces the entire vector."""
    from ncca.ngl.qml.vec3_model import Vec3Model

    model = Vec3Model()

    model.set_value(Vec3(2.0, 4.0, 6.0))

    assert (model.x, model.y, model.z) == (2.0, 4.0, 6.0)
