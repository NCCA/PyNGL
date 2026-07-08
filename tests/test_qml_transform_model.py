"""Tests for TransformModel, the QML-exposed position/rotation/scale transform."""

from ncca.ngl import Transform


def test_default_matrix_matches_default_transform(qt_app):
    from ncca.ngl.qml.transform_model import TransformModel

    model = TransformModel()

    assert model.get_matrix() == Transform().matrix()


def test_setting_position_updates_matrix(qt_app):
    from ncca.ngl.qml.transform_model import TransformModel

    model = TransformModel()

    model.position.x = 1.0
    model.position.y = 2.0
    model.position.z = 3.0

    expected = Transform()
    expected.set_position(1.0, 2.0, 3.0)
    assert model.get_matrix() == expected.matrix()


def test_setting_scale_updates_matrix(qt_app):
    from ncca.ngl.qml.transform_model import TransformModel

    model = TransformModel()

    model.scale.x = 2.0
    model.scale.y = 2.0
    model.scale.z = 2.0

    expected = Transform()
    expected.set_scale(2.0, 2.0, 2.0)
    assert model.get_matrix() == expected.matrix()


def test_scale_defaults_to_one(qt_app):
    from ncca.ngl.qml.transform_model import TransformModel

    model = TransformModel()

    assert (model.scale.x, model.scale.y, model.scale.z) == (1.0, 1.0, 1.0)


def test_changing_rotation_order_updates_matrix(qt_app):
    from ncca.ngl.qml.transform_model import TransformModel

    model = TransformModel()
    model.rotation.x = 10.0
    model.rotation.y = 20.0
    model.rotation.z = 30.0

    model.rotationOrderIndex = model.rotation_orders().index("zyx")

    expected = Transform()
    expected.set_order("zyx")
    expected.set_rotation(10.0, 20.0, 30.0)
    assert model.get_matrix() == expected.matrix()


def test_setting_position_emits_value_changed(qt_app, qtbot):
    from ncca.ngl.qml.transform_model import TransformModel

    model = TransformModel()

    with qtbot.waitSignal(model.valueChanged, timeout=1000):
        model.position.x = 5.0
