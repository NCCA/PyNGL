from ncca.ngl import Vec2


def test_vec2_model_default_value_is_zero(qt_app):
    from ncca.ngl.qml.vec2_model import Vec2Model

    model = Vec2Model()

    assert model.get_value() == Vec2(0.0, 0.0)


def test_setting_x_property_updates_value(qt_app):
    from ncca.ngl.qml.vec2_model import Vec2Model

    model = Vec2Model()

    model.x = 3.5

    assert model.get_value() == Vec2(3.5, 0.0)


def test_setting_y_property_updates_value(qt_app):
    from ncca.ngl.qml.vec2_model import Vec2Model

    model = Vec2Model()

    model.y = -2.0

    assert model.get_value() == Vec2(0.0, -2.0)


def test_setting_a_property_emits_value_changed(qt_app, qtbot):
    from ncca.ngl.qml.vec2_model import Vec2Model

    model = Vec2Model()

    with qtbot.waitSignal(model.valueChanged, timeout=1000):
        model.x = 1.0


def test_set_value_replaces_whole_vector(qt_app):
    from ncca.ngl.qml.vec2_model import Vec2Model

    model = Vec2Model()

    model.set_value(Vec2(2.0, 4.0))

    assert model.x == 2.0
    assert model.y == 4.0
