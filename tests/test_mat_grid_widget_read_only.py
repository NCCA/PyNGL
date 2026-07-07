"""Behavior tests for the read-only (view-only) mode of matrix grid widgets."""

import pytest

from ncca.ngl import Mat2, Mat3, Mat4
from ncca.ngl.widgets import Mat2Widget, Mat3Widget, Mat4Widget

WIDGET_CASES = [
    (Mat2Widget, Mat2),
    (Mat3Widget, Mat3),
    (Mat4Widget, Mat4),
]


@pytest.mark.parametrize("widget_cls,mat_cls", WIDGET_CASES)
def test_read_only_has_no_reset_buttons(qt_app, qtbot, widget_cls, mat_cls):
    widget = widget_cls(read_only=True)
    qtbot.addWidget(widget)

    assert not hasattr(widget, "_identity_button")
    assert not hasattr(widget, "_zero_button")
    assert not hasattr(widget, "_transpose_button")
    assert not hasattr(widget, "_inverse_button")


@pytest.mark.parametrize("widget_cls,mat_cls", WIDGET_CASES)
def test_read_only_has_no_method_combo(qt_app, qtbot, widget_cls, mat_cls):
    widget = widget_cls(read_only=True)
    qtbot.addWidget(widget)

    assert not hasattr(widget, "_method_combo")


@pytest.mark.parametrize("widget_cls,mat_cls", WIDGET_CASES)
def test_read_only_cells_cannot_be_typed_into(qt_app, qtbot, widget_cls, mat_cls):
    widget = widget_cls(read_only=True)
    qtbot.addWidget(widget)

    for row in widget._cells:
        for spinbox in row:
            assert spinbox.isReadOnly()


@pytest.mark.parametrize("widget_cls,mat_cls", WIDGET_CASES)
def test_read_only_set_value_still_updates_display(qt_app, qtbot, widget_cls, mat_cls):
    widget = widget_cls(read_only=True)
    qtbot.addWidget(widget)

    new_value = mat_cls.identity() * 2.0
    with qtbot.waitSignal(widget.valueChanged, timeout=1000):
        widget.set_value(new_value)

    assert widget.get_value() == new_value
    assert widget._cells[0][0].value() == pytest.approx(2.0, abs=1e-2)


@pytest.mark.parametrize("widget_cls,mat_cls", WIDGET_CASES)
def test_editable_widget_still_has_buttons_by_default(
    qt_app, qtbot, widget_cls, mat_cls
):
    widget = widget_cls()
    qtbot.addWidget(widget)

    assert widget._identity_button is not None
    for row in widget._cells:
        for spinbox in row:
            assert not spinbox.isReadOnly()
