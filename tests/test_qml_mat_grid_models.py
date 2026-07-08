import pytest

from ncca.ngl import Mat2, Mat3
from ncca.ngl.mat_base import MatrixError

WIDGET_CASES = [
    ("ncca.ngl.qml.mat2_model", "Mat2Model", Mat2, 2),
    ("ncca.ngl.qml.mat3_model", "Mat3Model", Mat3, 3),
]


def _load_model_cls(module_name, class_name):
    import importlib

    module = importlib.import_module(module_name)
    return getattr(module, class_name)


@pytest.mark.parametrize("module_name,class_name,mat_cls,size", WIDGET_CASES)
def test_default_value_is_identity(qt_app, module_name, class_name, mat_cls, size):
    model = _load_model_cls(module_name, class_name)()

    assert model.get_value() == mat_cls.identity()


@pytest.mark.parametrize("module_name,class_name,mat_cls,size", WIDGET_CASES)
def test_get_and_set_cell_round_trip(qt_app, module_name, class_name, mat_cls, size):
    model = _load_model_cls(module_name, class_name)()

    model.set_cell(0, 1, 3.5)

    assert model.get_cell(0, 1) == pytest.approx(3.5)


@pytest.mark.parametrize("module_name,class_name,mat_cls,size", WIDGET_CASES)
def test_set_cell_emits_value_changed(qt_app, qtbot, module_name, class_name, mat_cls, size):
    model = _load_model_cls(module_name, class_name)()

    with qtbot.waitSignal(model.valueChanged, timeout=1000):
        model.set_cell(0, 0, 9.0)


@pytest.mark.parametrize("module_name,class_name,mat_cls,size", WIDGET_CASES)
def test_zero_then_identity_round_trip(qt_app, module_name, class_name, mat_cls, size):
    model = _load_model_cls(module_name, class_name)()

    model.zero()
    assert model.get_value() == mat_cls.zero()

    model.identity()
    assert model.get_value() == mat_cls.identity()


@pytest.mark.parametrize("module_name,class_name,mat_cls,size", WIDGET_CASES)
def test_transpose_reflects_current_value(qt_app, module_name, class_name, mat_cls, size):
    model = _load_model_cls(module_name, class_name)()
    model.set_cell(0, 1, 7.0)

    model.transpose()

    assert model.get_cell(1, 0) == pytest.approx(7.0)


@pytest.mark.parametrize("module_name,class_name,mat_cls,size", WIDGET_CASES)
def test_inverse_of_singular_matrix_sets_status_message(
    qt_app, module_name, class_name, mat_cls, size
):
    model = _load_model_cls(module_name, class_name)()
    model.zero()

    model.inverse()

    assert model.statusMessage == "Matrix is singular"
    assert model.get_value() == mat_cls.zero()


@pytest.mark.parametrize("module_name,class_name,mat_cls,size", WIDGET_CASES)
def test_inverse_of_identity_is_identity_and_clears_status(
    qt_app, module_name, class_name, mat_cls, size
):
    model = _load_model_cls(module_name, class_name)()

    model.inverse()

    assert model.statusMessage == ""
    assert model.get_value() == mat_cls.identity()
