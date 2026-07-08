// src/ncca/ngl/qml/MatrixGridWidget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: root

    property int size: 3
    property var model
    property bool readOnly: false
    property real cellMin: -20.0
    property real cellMax: 20.0

    GridLayout {
        columns: root.size

        Repeater {
            model: root.size * root.size

            delegate: DecimalSpinBox {
                id: cellSpin
                readonly property int row: Math.floor(index / root.size)
                readonly property int col: index % root.size

                from_: root.cellMin
                to_: root.cellMax
                enabled: !root.readOnly
                realValue: root.model.get_cell(row, col)
                onRealValueChanged: {
                    if (!root.readOnly && root.model.get_cell(row, col) !== realValue) {
                        root.model.set_cell(row, col, realValue)
                    }
                }

                Connections {
                    target: root.model
                    function onValueChanged() {
                        cellSpin.realValue = root.model.get_cell(cellSpin.row, cellSpin.col)
                    }
                }
            }
        }
    }

    RowLayout {
        visible: !root.readOnly
        Button { text: "Identity"; onClicked: root.model.identity() }
        Button { text: "Zero"; onClicked: root.model.zero() }
        Button { text: "Transpose"; onClicked: root.model.transpose() }
        Button { text: "Inverse"; onClicked: root.model.inverse() }
    }

    Label {
        visible: !root.readOnly && root.model.statusMessage.length > 0
        text: root.model ? root.model.statusMessage : ""
    }
}
