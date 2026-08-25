# tests/test_qml_views.py
from pathlib import Path

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine

import ncca.ngl.qml  # noqa: F401  (import registers every QML type)

QML_DIR = Path(__file__).parent.parent / "src" / "ncca" / "ngl" / "qml"

STANDALONE_VIEWS = [
    "Vec2Widget.qml",
    "Vec3Widget.qml",
    "Vec4Widget.qml",
    "Mat2Widget.qml",
    "Mat3Widget.qml",
    "Mat4Widget.qml",
    "TransformWidget.qml",
    "LookAtWidget.qml",
    "RGBColourWidget.qml",
    "RGBAColourWidget.qml",
]


@pytest.mark.parametrize("qml_file", STANDALONE_VIEWS)
def test_widget_view_loads_without_errors(qt_app, qtbot, qml_file):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(QML_DIR))

    errors = []
    engine.warnings.connect(lambda msgs: errors.extend(msgs))
    engine.load(QUrl.fromLocalFile(str(QML_DIR / qml_file)))

    assert engine.rootObjects(), f"{qml_file} failed to load: {errors}"
    assert not errors, f"{qml_file} produced warnings: {errors}"


def test_main_qml_loads_without_errors(qt_app, qtbot):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(QML_DIR))

    errors = []
    engine.warnings.connect(lambda msgs: errors.extend(msgs))
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "main.qml")))

    assert engine.rootObjects(), f"main.qml failed to load: {errors}"
    assert not errors, f"main.qml produced warnings: {errors}"
