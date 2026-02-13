import pytest

from ncca.ngl import Vec3
from ncca.ngl.widgets import Vec3Widget


def test_vec3_widget_initial_value(qt_app, qtbot):
    # Create the window
    v3 = Vec3Widget()
    qtbot.addWidget(v3)

    assert v3.get_value() == Vec3(0, 0, 0)
    assert v3.get_name() == ""


def test_vec3_widget_constructor_initial_value_and_name(qt_app, qtbot):
    # Pass name and value via keywords (constructor signature is parent, name, value)
    start_value = Vec3(0.5, -0.5, 1.0)
    v3 = Vec3Widget(name="InitName", value=start_value)
    qtbot.addWidget(v3)

    # internal value and label text
    assert v3.get_value() == start_value
    assert v3.get_name() == "InitName"
    # spinboxes initialized to the provided values
    assert v3.get_value() == start_value


def test_vec3_widget_set_value(qt_app, qtbot):
    # Create the window
    v3 = Vec3Widget()
    qtbot.addWidget(v3)
    v3.set_value(Vec3(1, 2, 3))
    assert v3.get_value() == Vec3(1, 2, 3)


def test_property_accessors(qt_app, qtbot):
    v3 = Vec3Widget()
    qtbot.addWidget(v3)

    # property-style assignment should work (Qt Property wrapper)
    v3.value = Vec3(7, 8, 9)
    assert v3.get_value() == Vec3(7, 8, 9)

    v3.name = "PropName"
    assert v3.get_name() == "PropName"
    assert v3._label.text() == "PropName"


def test_value_signals_for_each_component(qt_app, qtbot):
    # Verify per-axis signals emit when spinboxes change (already in your tests,
    # but keep a concise check here)
    v3 = Vec3Widget()
    qtbot.addWidget(v3)

    with qtbot.waitSignal(v3.xValueChanged, timeout=1000) as sig_x:
        v3.x_spinbox.setValue(1.23)
    assert sig_x.args == [pytest.approx(1.23)]

    with qtbot.waitSignal(v3.yValueChanged, timeout=1000) as sig_y:
        v3.y_spinbox.setValue(-2.34)
    assert sig_y.args == [pytest.approx(-2.34)]

    with qtbot.waitSignal(v3.zValueChanged, timeout=1000) as sig_z:
        v3.z_spinbox.setValue(3.45)
    assert sig_z.args == [pytest.approx(3.45)]


def test_set_value_blocks_axis_signals_but_emits_value_changed(qt_app, qtbot):
    v3 = Vec3Widget()
    qtbot.addWidget(v3)

    # lists to collect any axis signal emissions
    xs = []
    ys = []
    zs = []
    v3.xValueChanged.connect(xs.append)
    v3.yValueChanged.connect(ys.append)
    v3.zValueChanged.connect(zs.append)

    new_val = Vec3(1.0, 2.0, 3.0)
    # set_value uses QSignalBlocker on the spinboxes, so individual axis signals
    # should NOT be emitted, but the combined valueChanged should be.
    with qtbot.waitSignal(v3.valueChanged, timeout=1000) as sig:
        v3.set_value(new_val)

    assert v3.get_value() == new_val
    # axis signal lists must remain empty
    assert xs == []
    assert ys == []
    assert zs == []
    # the valueChanged signal should have been emitted with the Vec3
    assert sig.args == [new_val]


def test_set_range_and_individual_ranges(qt_app, qtbot):
    v3 = Vec3Widget()
    qtbot.addWidget(v3)

    # set individual ranges
    v3.set_x_range(-1.0, 1.0)
    assert v3.x_spinbox.minimum() == pytest.approx(-1.0)
    assert v3.x_spinbox.maximum() == pytest.approx(1.0)

    v3.set_y_range(-2.0, 2.0)
    assert v3.y_spinbox.minimum() == pytest.approx(-2.0)
    assert v3.y_spinbox.maximum() == pytest.approx(2.0)

    v3.set_z_range(-3.0, 3.0)
    assert v3.z_spinbox.minimum() == pytest.approx(-3.0)
    assert v3.z_spinbox.maximum() == pytest.approx(3.0)

    # set_range should override all three
    v3.set_range(-5.0, 5.0)
    assert v3.x_spinbox.minimum() == pytest.approx(-5.0)
    assert v3.x_spinbox.maximum() == pytest.approx(5.0)
    assert v3.y_spinbox.minimum() == pytest.approx(-5.0)
    assert v3.y_spinbox.maximum() == pytest.approx(5.0)
    assert v3.z_spinbox.minimum() == pytest.approx(-5.0)
    assert v3.z_spinbox.maximum() == pytest.approx(5.0)


def test_set_single_step_applies_to_all(qt_app, qtbot):
    v3 = Vec3Widget()
    qtbot.addWidget(v3)

    v3.set_single_step(0.5)
    assert v3.x_spinbox.singleStep() == pytest.approx(0.5)
    assert v3.y_spinbox.singleStep() == pytest.approx(0.5)
    assert v3.z_spinbox.singleStep() == pytest.approx(0.5)
