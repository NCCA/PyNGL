from PySide6.QtWidgets import QFrame

from ncca.ngl.widgets.mat4widget import Mat4ViewWidget


def test_mat4viewwidget_is_a_qframe(qt_app, qtbot):
    w = Mat4ViewWidget()
    qtbot.addWidget(w)

    assert isinstance(w, QFrame)
