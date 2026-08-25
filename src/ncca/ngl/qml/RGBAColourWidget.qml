// src/ncca/ngl/qml/RGBAColourWidget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import ncca.ngl.qml 1.0

Frame {
    id: root

    property string name: ""
    property alias model: colourModel
    signal colourChanged()

    RGBAColourModel {
        id: colourModel
        onColourChanged: root.colourChanged()
    }

    RowLayout {
        anchors.fill: parent
        Label { text: root.name }
        DecimalSpinBox {
            from_: 0.0
            to_: 1.0
            realValue: colourModel.r
            onRealValueChanged: {
                if (colourModel.r !== realValue) {
                    colourModel.r = realValue
                }
            }
        }
        DecimalSpinBox {
            from_: 0.0
            to_: 1.0
            realValue: colourModel.g
            onRealValueChanged: {
                if (colourModel.g !== realValue) {
                    colourModel.g = realValue
                }
            }
        }
        DecimalSpinBox {
            from_: 0.0
            to_: 1.0
            realValue: colourModel.b
            onRealValueChanged: {
                if (colourModel.b !== realValue) {
                    colourModel.b = realValue
                }
            }
        }
        DecimalSpinBox {
            from_: 0.0
            to_: 1.0
            realValue: colourModel.a
            onRealValueChanged: {
                if (colourModel.a !== realValue) {
                    colourModel.a = realValue
                }
            }
        }
        Rectangle {
            id: swatch
            width: 20
            height: 20
            color: colourModel.hex
            border.color: "black"

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    colourDialog.color = colourModel.hex
                    colourDialog.open()
                }
            }
        }
    }

    ColorDialog {
        id: colourDialog
        title: root.name.length > 0 ? root.name : "Select Colour"
        options: ColorDialog.ShowAlphaChannel
        onAccepted: {
            colourModel.r = colourDialog.color.r
            colourModel.g = colourDialog.color.g
            colourModel.b = colourDialog.color.b
            colourModel.a = colourDialog.color.a
        }
    }
}
