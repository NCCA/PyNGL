"""Behavior tests for the Mat3Widget/Mat4Widget method combo box."""

import pytest

from ncca.ngl import Mat3, Mat4, Vec3
from ncca.ngl.widgets import Mat3Widget, Mat4Widget

WIDGET_CASES = [
    (Mat3Widget, Mat3, ["rotate_x", "rotate_y", "rotate_z", "scale"]),
    (Mat4Widget, Mat4, ["rotate_x", "rotate_y", "rotate_z", "scale", "translate"]),
]


@pytest.mark.parametrize("widget_cls,mat_cls,expected_items", WIDGET_CASES)
def test_combo_contains_expected_methods(
    qt_app, qtbot, widget_cls, mat_cls, expected_items
):
    widget = widget_cls()
    qtbot.addWidget(widget)

    items = [
        widget._method_combo.itemText(i) for i in range(widget._method_combo.count())
    ]
    assert items == expected_items


@pytest.mark.parametrize("widget_cls,mat_cls,expected_items", WIDGET_CASES)
def test_rotate_x_selected_shows_angle_panel(
    qt_app, qtbot, widget_cls, mat_cls, expected_items
):
    widget = widget_cls()
    qtbot.addWidget(widget)

    assert widget._param_stack.currentWidget() is widget._angle_spinbox


@pytest.mark.parametrize("widget_cls,mat_cls,expected_items", WIDGET_CASES)
def test_selecting_scale_shows_xyz_panel(
    qt_app, qtbot, widget_cls, mat_cls, expected_items
):
    widget = widget_cls()
    qtbot.addWidget(widget)

    widget._method_combo.setCurrentText("scale")

    assert widget._param_stack.currentWidget() is widget._xyz_widget


@pytest.mark.parametrize("widget_cls,mat_cls,expected_items", WIDGET_CASES)
def test_changing_angle_recomputes_rotate_x(
    qt_app, qtbot, widget_cls, mat_cls, expected_items
):
    widget = widget_cls()
    qtbot.addWidget(widget)

    with qtbot.waitSignal(widget.valueChanged, timeout=1000):
        widget._angle_spinbox.setValue(45.0)

    assert widget.get_value() == mat_cls.rotate_x(45.0)


@pytest.mark.parametrize("widget_cls,mat_cls,expected_items", WIDGET_CASES)
def test_changing_xyz_recomputes_scale(
    qt_app, qtbot, widget_cls, mat_cls, expected_items
):
    widget = widget_cls()
    qtbot.addWidget(widget)
    widget._method_combo.setCurrentText("scale")

    with qtbot.waitSignal(widget.valueChanged, timeout=1000):
        widget._xyz_widget.set_value(Vec3(2.0, 3.0, 4.0))

    assert widget.get_value() == mat_cls.scale(2.0, 3.0, 4.0)


def test_mat4widget_changing_xyz_recomputes_translate(qt_app, qtbot):
    widget = Mat4Widget()
    qtbot.addWidget(widget)
    widget._method_combo.setCurrentText("translate")

    with qtbot.waitSignal(widget.valueChanged, timeout=1000):
        widget._xyz_widget.set_value(Vec3(5.0, 6.0, 7.0))

    assert widget.get_value() == Mat4.translate(5.0, 6.0, 7.0)
