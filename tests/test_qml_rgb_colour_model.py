"""Tests for RGBColourModel QML model."""

import pytest

from ncca.ngl import Vec3


def test_default_colour_is_white(qt_app):
    """Test that default colour is white."""
    from ncca.ngl.qml.rgb_colour_model import RGBColourModel

    model = RGBColourModel()

    assert model.get_value() == Vec3(1.0, 1.0, 1.0)
    assert model.hex == "#ffffff"


def test_setting_r_updates_value_and_hex(qt_app):
    """Test that setting RGB values updates hex."""
    from ncca.ngl.qml.rgb_colour_model import RGBColourModel

    model = RGBColourModel()

    model.r = 0.0
    model.g = 0.0
    model.b = 0.0

    assert model.get_value() == Vec3(0.0, 0.0, 0.0)
    assert model.hex == "#000000"


def test_setting_g_emits_colour_changed(qt_app, qtbot):
    """Test that setting g channel emits colourChanged signal."""
    from ncca.ngl.qml.rgb_colour_model import RGBColourModel

    model = RGBColourModel()

    with qtbot.waitSignal(model.colourChanged, timeout=1000):
        model.g = 0.5


def test_set_value_replaces_whole_colour(qt_app):
    """Test that set_value replaces the entire colour."""
    from ncca.ngl.qml.rgb_colour_model import RGBColourModel

    model = RGBColourModel()

    model.set_value(Vec3(0.2, 0.4, 0.6))

    assert (model.r, model.g, model.b) == pytest.approx((0.2, 0.4, 0.6))
