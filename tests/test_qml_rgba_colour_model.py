import pytest

from ncca.ngl import Vec4


def test_default_colour_is_opaque_white(qt_app):
    from ncca.ngl.qml.rgba_colour_model import RGBAColourModel

    model = RGBAColourModel()

    assert model.get_value() == Vec4(1.0, 1.0, 1.0, 1.0)
    assert model.hex == "#ffffffff"


def test_setting_a_updates_value_and_hex(qt_app):
    from ncca.ngl.qml.rgba_colour_model import RGBAColourModel

    model = RGBAColourModel()

    model.a = 0.0

    assert model.get_value() == Vec4(1.0, 1.0, 1.0, 0.0)
    assert model.hex == "#00ffffff"


def test_setting_a_emits_colour_changed(qt_app, qtbot):
    from ncca.ngl.qml.rgba_colour_model import RGBAColourModel

    model = RGBAColourModel()

    with qtbot.waitSignal(model.colourChanged, timeout=1000):
        model.a = 0.5


def test_set_value_replaces_whole_colour(qt_app):
    from ncca.ngl.qml.rgba_colour_model import RGBAColourModel

    model = RGBAColourModel()

    model.set_value(Vec4(0.2, 0.4, 0.6, 0.8))

    assert (model.r, model.g, model.b, model.a) == pytest.approx((0.2, 0.4, 0.6, 0.8))
