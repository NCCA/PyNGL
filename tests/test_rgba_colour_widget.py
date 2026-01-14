import pytest
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QColorDialog

from ncca.ngl import Vec4
from ncca.ngl.widgets import RGBAColourWidget


def test_rgb_widget_initial_value(qtbot):
    w = RGBAColourWidget()
    qtbot.addWidget(w)

    # default constructor uses r=1.0,g=1.0,b=1.0 and empty name
    assert w.colour() == Vec4(1.0, 1.0, 1.0)
    # read the property (not call it as a method)
    assert w.name == ""
    # button stylesheet reflects white (#ffffff)
    assert "#ffffff" in w._color_button.styleSheet()


def test_rgba_widget_constructor_initial_value_and_name(qtbot):
    start_val = Vec4(0.5, 0.6, 0.7, 1.0)
    w = RGBAColourWidget(name="InitName", r=start_val.x, g=start_val.y, b=start_val.z, a=start_val.w)
    qtbot.addWidget(w)

    assert w.colour() == start_val
    # read the property (not call it as a method)
    assert w.name == "InitName"
    # spinboxes initialized to the provided values
    assert w.r_spinbox.value() == pytest.approx(start_val.x)
    assert w.g_spinbox.value() == pytest.approx(start_val.y)
    assert w.b_spinbox.value() == pytest.approx(start_val.z)
    assert w.a_spinbox.value() == pytest.approx(start_val.w)


def test_property_accessors(qtbot):
    w = RGBAColourWidget()
    qtbot.addWidget(w)

    # property-style assignment for value should work
    w.value = Vec4(0.1, 0.2, 0.3)
    assert w.colour() == Vec4(0.1, 0.2, 0.3)

    w.name = "PropName"
    # read the property (not call it as a method)
    assert w.name == "PropName"
    assert w._label.text() == "PropName"


def test_value_signals_for_each_component(qtbot):
    w = RGBAColourWidget()
    qtbot.addWidget(w)

    with qtbot.waitSignal(w.rValueChanged, timeout=1000) as sig_r:
        w.r_spinbox.setValue(0.25)
    assert sig_r.args == [pytest.approx(0.25)]

    with qtbot.waitSignal(w.gValueChanged, timeout=1000) as sig_g:
        w.g_spinbox.setValue(0.5)
    assert sig_g.args == [pytest.approx(0.5)]

    with qtbot.waitSignal(w.bValueChanged, timeout=1000) as sig_b:
        w.b_spinbox.setValue(0.75)
    assert sig_b.args == [pytest.approx(0.75)]

    with qtbot.waitSignal(w.aValueChanged, timeout=1000) as sig_a:
        w.a_spinbox.setValue(0.75)
    assert sig_a.args == [pytest.approx(0.75)]


def test_set_colour_blocks_channel_signals_but_emits_colour_changed(qtbot):
    w = RGBAColourWidget()
    qtbot.addWidget(w)

    rs = []
    gs = []
    bs = []
    w.rValueChanged.connect(rs.append)
    w.gValueChanged.connect(gs.append)
    w.bValueChanged.connect(bs.append)

    new_val = Vec4(0.1, 0.2, 0.3)
    with qtbot.waitSignal(w.colourChanged, timeout=1000) as sig:
        w.set_colour(new_val)

    # internal value updated
    assert w.colour() == new_val
    # per-channel signals should not have been emitted because set_colour blocks them
    assert rs == []
    assert gs == []
    assert bs == []
    # combined colourChanged emitted with Vec4
    emitted = sig.args[0]
    assert emitted.x == pytest.approx(new_val.x)
    assert emitted.y == pytest.approx(new_val.y)
    assert emitted.z == pytest.approx(new_val.z)


def test_spinbox_ranges_and_single_step_defaults(qtbot):
    w = RGBAColourWidget()
    qtbot.addWidget(w)

    # by implementation spinboxes are set to range 0.0..1.0 and single step 0.01
    assert w.r_spinbox.minimum() == pytest.approx(0.0)
    assert w.r_spinbox.maximum() == pytest.approx(1.0)
    assert w.g_spinbox.minimum() == pytest.approx(0.0)
    assert w.g_spinbox.maximum() == pytest.approx(1.0)
    assert w.b_spinbox.minimum() == pytest.approx(0.0)
    assert w.b_spinbox.maximum() == pytest.approx(1.0)

    assert w.r_spinbox.singleStep() == pytest.approx(0.01)
    assert w.g_spinbox.singleStep() == pytest.approx(0.01)
    assert w.b_spinbox.singleStep() == pytest.approx(0.01)


def test_update_button_color_updates_stylesheet(qtbot):
    w = RGBAColourWidget()
    qtbot.addWidget(w)

    # default white
    assert "#ffffff" in w._color_button.styleSheet()

    # change to black and verify stylesheet updates
    w.set_colour(Vec4(0.0, 0.0, 0.0))
    assert "#ff000000" in w._color_button.styleSheet()


def test_show_color_dialog_applies_selection_and_emits(monkeypatch, qtbot):
    w = RGBAColourWidget()
    qtbot.addWidget(w)

    # monkeypatch QColorDialog.getColor to return a specific valid colour
    def fake_get_color(current, parent, title, options=None):
        return QColor.fromRgbF(0.2, 0.3, 0.4, 0.8)

    monkeypatch.setattr(QColorDialog, "getColor", fake_get_color)

    with qtbot.waitSignal(w.colourChanged, timeout=1000) as sig:
        w._show_color_dialog()

    emitted = sig.args[0]
    # allow a small relative tolerance to accommodate QColor rounding
    assert emitted[0] == pytest.approx(0.2, rel=1e-4)
    assert emitted[1] == pytest.approx(0.3, rel=1e-4)
    assert emitted[2] == pytest.approx(0.4, rel=1e-4)
    assert emitted[3] == pytest.approx(0.8, rel=1e-4)

    # button stylesheet should have been updated to the chosen colour
    assert "#" in w._color_button.styleSheet()
