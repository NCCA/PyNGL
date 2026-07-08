// src/ncca/ngl/qml/RGBAColourWidget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
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
            width: 20
            height: 20
            color: colourModel.hex
            border.color: "black"
        }
    }
}
