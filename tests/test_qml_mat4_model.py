from ncca.ngl import Mat4


def test_method_names_lists_rotate_scale_translate(qt_app):
    from ncca.ngl.qml.mat4_model import Mat4Model

    model = Mat4Model()

    assert model.method_names() == [
        "rotate_x",
        "rotate_y",
        "rotate_z",
        "scale",
        "translate",
    ]


def test_apply_angle_method_matches_classmethod(qt_app):
    from ncca.ngl.qml.mat4_model import Mat4Model

    model = Mat4Model()

    model.apply_angle_method("rotate_x", 30.0)

    assert model.get_value() == Mat4.rotate_x(30.0)


def test_apply_xyz_method_translate_matches_classmethod(qt_app):
    from ncca.ngl.qml.mat4_model import Mat4Model

    model = Mat4Model()

    model.apply_xyz_method("translate", 1.0, 2.0, 3.0)

    assert model.get_value() == Mat4.translate(1.0, 2.0, 3.0)
