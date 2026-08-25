# src/ncca/ngl/qml/__main__.py
"""Demo Qt Quick app showcasing all of the NGL QML widgets."""

import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

import ncca.ngl.qml  # noqa: F401  (import registers every QML type)


def main() -> int:
    """Launch the QML widgets demo application.

    Returns:
        The process exit code (-1 if the QML file failed to load).
    """
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    package_dir = Path(__file__).parent
    engine.addImportPath(str(package_dir))
    engine.load(QUrl.fromLocalFile(str(package_dir / "main.qml")))
    if not engine.rootObjects():
        return -1
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
