import pytest

from ncca.ngl import Vec2
from ncca.ngl.widgets import Vec2Widget


def test_vec2_widget_initial_value(qt_app, qtbot):
    # Create the window
    v2 = Vec2Widget()
    qtbot.addWidget(v2)

    assert v2.get_value() == Vec2(0, 0)
    assert v2.get_name() == ""


def test_vec2_widget_constructor_initial_value_and_name(qt_app, qtbot):
    # Pass name and value via keywords (constructor signature is parent, name, value)
    start_value = Vec2(0.5, -0.5)
    v2 = Vec2Widget(name="InitName", value=start_value)
    qtbot.addWidget(v2)

    # internal value and label text
    assert v2.get_value() == start_value
    assert v2.get_name() == "InitName"
    # spinboxes initialized to the provided values
    assert v2.get_value() == start_value


def test_vec2_widget_set_value(qt_app, qtbot):
    # Create the window
    v2 = Vec2Widget()
    qtbot.addWidget(v2)
    v2.set_value(Vec2(1, 2))
    assert v2.get_value() == Vec2(1, 2)


def test_property_accessors(qt_app, qtbot):
    v2 = Vec2Widget()
    qtbot.addWidget(v2)

    # property-style assignment should work (Qt Property wrapper)
    v2.value = Vec2(7, 8)
    assert v2.get_value() == Vec2(7, 8)

    v2.name = "PropName"
    assert v2.get_name() == "PropName"
    assert v2._label.text() == "PropName"


def test_value_signals_for_each_component(qt_app, qtbot):
    # Verify per-axis signals emit when spinboxes change (already in your tests,
    # but keep a concise check here)
    v2 = Vec2Widget()
    qtbot.addWidget(v2)

    with qtbot.waitSignal(v2.xValueChanged, timeout=1000) as sig_x:
        v2.x_spinbox.setValue(1.23)
    assert sig_x.args == [pytest.approx(1.23)]

    with qtbot.waitSignal(v2.yValueChanged, timeout=1000) as sig_y:
        v2.y_spinbox.setValue(-2.34)
    assert sig_y.args == [pytest.approx(-2.34)]


def test_set_value_blocks_axis_signals_but_emits_valuechanged(qt_app, qtbot):
    v2 = Vec2Widget()
    qtbot.addWidget(v2)

    # lists to collect any axis signal emissions
    xs = []
    ys = []
    v2.xValueChanged.connect(xs.append)
    v2.yValueChanged.connect(ys.append)

    new_val = Vec2(1.0, 2.0)
    # set_value uses QSignalBlocker on the spinboxes, so individual axis signals
    # should NOT be emitted, but the combined valueChanged should be.
    with qtbot.waitSignal(v2.valueChanged, timeout=1000) as sig:
        v2.set_value(new_val)

    assert v2.get_value() == new_val
    # axis signal lists must remain empty
    assert xs == []
    assert ys == []
    # the valueChanged signal should have been emitted with the Vec2
    assert sig.args == [new_val]


def test_set_range_and_individual_ranges(qt_app, qtbot):
    v2 = Vec2Widget()
    qtbot.addWidget(v2)

    # set individual ranges
    v2.set_x_range(-1.0, 1.0)
    assert v2.x_spinbox.minimum() == pytest.approx(-1.0)
    assert v2.x_spinbox.maximum() == pytest.approx(1.0)

    v2.set_y_range(-2.0, 2.0)
    assert v2.y_spinbox.minimum() == pytest.approx(-2.0)
    assert v2.y_spinbox.maximum() == pytest.approx(2.0)

    # set_range should override all three
    v2.set_range(-5.0, 5.0)
    assert v2.x_spinbox.minimum() == pytest.approx(-5.0)
    assert v2.x_spinbox.maximum() == pytest.approx(5.0)
    assert v2.y_spinbox.minimum() == pytest.approx(-5.0)
    assert v2.y_spinbox.maximum() == pytest.approx(5.0)


def test_set_single_step_applies_to_all(qt_app, qtbot):
    v2 = Vec2Widget()
    qtbot.addWidget(v2)

    v2.set_single_step(0.5)
    assert v2.x_spinbox.singleStep() == pytest.approx(0.5)
    assert v2.y_spinbox.singleStep() == pytest.approx(0.5)
