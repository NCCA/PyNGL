import pytest

from ncca.ngl import Mat3


def test_method_names_lists_rotate_and_scale(qt_app):
    from ncca.ngl.qml.mat3_model import Mat3Model

    model = Mat3Model()

    assert model.method_names() == ["rotate_x", "rotate_y", "rotate_z", "scale"]


def test_method_kind_angle_vs_xyz(qt_app):
    from ncca.ngl.qml.mat3_model import Mat3Model

    model = Mat3Model()

    assert model.method_kind("rotate_x") == "angle"
    assert model.method_kind("scale") == "xyz"


def test_apply_angle_method_matches_classmethod(qt_app):
    from ncca.ngl.qml.mat3_model import Mat3Model

    model = Mat3Model()

    model.apply_angle_method("rotate_y", 45.0)

    assert model.get_value() == Mat3.rotate_y(45.0)


def test_apply_xyz_method_matches_classmethod(qt_app):
    from ncca.ngl.qml.mat3_model import Mat3Model

    model = Mat3Model()

    model.apply_xyz_method("scale", 2.0, 3.0, 4.0)

    assert model.get_value() == Mat3.scale(2.0, 3.0, 4.0)
