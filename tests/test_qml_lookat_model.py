from ncca.ngl import Vec3, look_at


def test_default_eye_and_matrix(qt_app):
    from ncca.ngl.qml.lookat_model import LookAtModel

    model = LookAtModel()

    assert (model.eye.x, model.eye.y, model.eye.z) == (2.0, 2.0, 2.0)
    assert model.get_matrix() == look_at(Vec3(2, 2, 2), Vec3(0, 0, 0), Vec3(0, 1, 0))


def test_changing_eye_updates_matrix(qt_app):
    from ncca.ngl.qml.lookat_model import LookAtModel

    model = LookAtModel()

    model.eye.x = 5.0
    model.eye.y = 0.0
    model.eye.z = 0.0

    assert model.get_matrix() == look_at(Vec3(5, 0, 0), Vec3(0, 0, 0), Vec3(0, 1, 0))


def test_changing_up_index_updates_matrix(qt_app):
    from ncca.ngl.qml.lookat_model import LookAtModel

    model = LookAtModel()

    model.upIndex = model.up_names().index("x-up")

    assert model.get_matrix() == look_at(Vec3(2, 2, 2), Vec3(0, 0, 0), Vec3(1, 0, 0))


def test_changing_eye_emits_value_changed(qt_app, qtbot):
    from ncca.ngl.qml.lookat_model import LookAtModel

    model = LookAtModel()

    with qtbot.waitSignal(model.valueChanged, timeout=1000):
        model.eye.x = 1.0
