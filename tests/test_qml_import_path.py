# tests/test_qml_import_path.py
from PySide6.QtQml import QQmlApplicationEngine

from ncca.ngl.qml import add_import_path, import_path


def test_import_path_contains_qmldir():
    """The derived root must actually contain the module's qmldir.

    This pins the parents[3] depth in import_path(): if the walk is off by a
    level the qmldir won't be found there and `import ncca.ngl.qml 1.0` would
    silently fail to resolve in client apps.
    """
    assert (import_path() / "ncca" / "ngl" / "qml" / "qmldir").is_file()


def test_add_import_path_registers_on_engine(qt_app, qtbot):
    """add_import_path should add the module root to the engine's import paths."""
    engine = QQmlApplicationEngine()
    add_import_path(engine)
    assert str(import_path()) in engine.importPathList()
