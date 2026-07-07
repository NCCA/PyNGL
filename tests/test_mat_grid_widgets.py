"""Shared behavior tests for Mat2Widget/Mat3Widget/Mat4Widget.

Parametrized across every matrix size so the common grid/button/name/range
behavior implemented once in _MatGridWidget is verified identically for each
concrete widget.
"""

import pytest
from PySide6.QtWidgets import QFrame

from ncca.ngl import Mat2, Mat3, Mat4
from ncca.ngl.widgets import Mat2Widget, Mat3Widget, Mat4Widget

WIDGET_CASES = [
    (Mat2Widget, Mat2, 2),
    (Mat3Widget, Mat3, 3),
    (Mat4Widget, Mat4, 4),
]


def _flat_values(size: int) -> list[list[float]]:
    return [[float(row * size + col + 1) for col in range(size)] for row in range(size)]


@pytest.mark.parametrize("widget_cls,mat_cls,size", WIDGET_CASES)
def test_widget_is_a_qframe(qt_app, qtbot, widget_cls, mat_cls, size):
    widget = widget_cls()
    qtbot.addWidget(widget)

    assert isinstance(widget, QFrame)


@pytest.mark.parametrize("widget_cls,mat_cls,size", WIDGET_CASES)
def test_grid_has_size_by_size_cells(qt_app, qtbot, widget_cls, mat_cls, size):
    widget = widget_cls()
    qtbot.addWidget(widget)

    assert len(widget._cells) == size
    assert all(len(row) == size for row in widget._cells)


@pytest.mark.parametrize("widget_cls,mat_cls,size", WIDGET_CASES)
def test_default_value_is_identity(qt_app, qtbot, widget_cls, mat_cls, size):
    widget = widget_cls()
    qtbot.addWidget(widget)

    assert widget.get_value() == mat_cls.identity()


@pytest.mark.parametrize("widget_cls,mat_cls,size", WIDGET_CASES)
def test_editing_a_cell_updates_value(qt_app, qtbot, widget_cls, mat_cls, size):
    widget = widget_cls()
    qtbot.addWidget(widget)

    widget._cells[0][1].setValue(3.5)

    assert widget.get_value()[0][1] == pytest.approx(3.5)


@pytest.mark.parametrize("widget_cls,mat_cls,size", WIDGET_CASES)
def test_editing_a_cell_emits_value_changed(qt_app, qtbot, widget_cls, mat_cls, size):
    widget = widget_cls()
    qtbot.addWidget(widget)

    with qtbot.waitSignal(widget.valueChanged, timeout=1000) as signal:
        widget._cells[1][0].setValue(2.0)

    assert isinstance(signal.args[0], mat_cls)
    assert signal.args[0][1][0] == pytest.approx(2.0)


@pytest.mark.parametrize("widget_cls,mat_cls,size", WIDGET_CASES)
def test_set_value_updates_cells_and_emits(qt_app, qtbot, widget_cls, mat_cls, size):
    widget = widget_cls()
    qtbot.addWidget(widget)

    flat = _flat_values(size)
    new_value = mat_cls.from_list(flat)
    with qtbot.waitSignal(widget.valueChanged, timeout=1000) as signal:
        widget.set_value(new_value)

    assert widget.get_value() == new_value
    assert widget._cells[0][0].value() == pytest.approx(flat[0][0])
    assert widget._cells[size - 1][size - 1].value() == pytest.approx(flat[-1][-1])
    assert signal.args[0] == new_value


@pytest.mark.parametrize("widget_cls,mat_cls,size", WIDGET_CASES)
def test_identity_button_resets_value(qt_app, qtbot, widget_cls, mat_cls, size):
    widget = widget_cls()
    qtbot.addWidget(widget)
    widget.set_value(mat_cls.from_list(_flat_values(size)))

    widget._identity_button.click()

    assert widget.get_value() == mat_cls.identity()


@pytest.mark.parametrize("widget_cls,mat_cls,size", WIDGET_CASES)
def test_zero_button_resets_value(qt_app, qtbot, widget_cls, mat_cls, size):
    widget = widget_cls()
    qtbot.addWidget(widget)

    widget._zero_button.click()

    assert widget.get_value() == mat_cls.zero()


@pytest.mark.parametrize("widget_cls,mat_cls,size", WIDGET_CASES)
def test_transpose_button_transposes_current_value(
    qt_app, qtbot, widget_cls, mat_cls, size
):
    widget = widget_cls()
    qtbot.addWidget(widget)
    value = mat_cls.from_list(_flat_values(size))
    widget.set_value(value)

    widget._transpose_button.click()

    assert widget.get_value() == value.transposed()


@pytest.mark.parametrize("widget_cls,mat_cls,size", WIDGET_CASES)
def test_inverse_button_inverts_current_value(qt_app, qtbot, widget_cls, mat_cls, size):
    widget = widget_cls()
    qtbot.addWidget(widget)
    widget.set_value(mat_cls.identity() * 2.0)

    widget._inverse_button.click()

    assert widget.get_value() == mat_cls.identity() * 0.5


@pytest.mark.parametrize("widget_cls,mat_cls,size", WIDGET_CASES)
def test_inverse_button_on_singular_matrix_shows_status(
    qt_app, qtbot, widget_cls, mat_cls, size
):
    widget = widget_cls()
    qtbot.addWidget(widget)
    singular = mat_cls.zero()
    widget.set_value(singular)

    widget._inverse_button.click()

    assert widget.get_value() == singular
    assert "singular" in widget._status_label.text().lower()


@pytest.mark.parametrize("widget_cls,mat_cls,size", WIDGET_CASES)
def test_name_property(qt_app, qtbot, widget_cls, mat_cls, size):
    widget = widget_cls(name="MyMatrix")
    qtbot.addWidget(widget)

    assert widget.get_name() == "MyMatrix"
    assert widget.name == "MyMatrix"

    widget.set_name("Other")
    assert widget.name == "Other"


@pytest.mark.parametrize("widget_cls,mat_cls,size", WIDGET_CASES)
def test_name_label_shows_name(qt_app, qtbot, widget_cls, mat_cls, size):
    widget = widget_cls(name="MyMatrix")
    qtbot.addWidget(widget)

    assert widget._name_label.text() == "MyMatrix"

    widget.set_name("Other")
    assert widget._name_label.text() == "Other"


@pytest.mark.parametrize("widget_cls,mat_cls,size", WIDGET_CASES)
def test_set_range_applies_to_all_cells(qt_app, qtbot, widget_cls, mat_cls, size):
    widget = widget_cls()
    qtbot.addWidget(widget)

    widget.set_range(-1.0, 1.0)

    for row in widget._cells:
        for spinbox in row:
            assert spinbox.minimum() == pytest.approx(-1.0)
            assert spinbox.maximum() == pytest.approx(1.0)


@pytest.mark.parametrize("widget_cls,mat_cls,size", WIDGET_CASES)
def test_set_single_step_applies_to_all_cells(qt_app, qtbot, widget_cls, mat_cls, size):
    widget = widget_cls()
    qtbot.addWidget(widget)

    widget.set_single_step(0.5)

    for row in widget._cells:
        for spinbox in row:
            assert spinbox.singleStep() == pytest.approx(0.5)
