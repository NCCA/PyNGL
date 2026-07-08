// src/ncca/ngl/qml/Mat2Widget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ncca.ngl.qml 1.0

Frame {
    id: root

    property string name: ""
    property bool readOnly: false
    property alias model: mat2Model
    signal valueChanged()

    Mat2Model {
        id: mat2Model
        onValueChanged: root.valueChanged()
    }

    ColumnLayout {
        anchors.fill: parent
        Label { text: root.name }
        MatrixGridWidget {
            size: 2
            model: mat2Model
            readOnly: root.readOnly
        }
    }
}
