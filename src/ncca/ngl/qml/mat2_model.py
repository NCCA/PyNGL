"""QML-exposed model for editing a Mat2 as a 2x2 grid."""

from PySide6.QtQml import QmlElement

from ncca.ngl import Mat2

from .mat_grid_model import MatGridModel

QML_IMPORT_NAME = "ncca.ngl.qml"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class Mat2Model(MatGridModel):
    """Grid model for a Mat2. No rotate/scale method combo (mirrors Mat2Widget)."""

    mat_cls = Mat2
    size = 2
