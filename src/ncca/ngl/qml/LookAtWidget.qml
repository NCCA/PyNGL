// src/ncca/ngl/qml/LookAtWidget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ncca.ngl.qml 1.0

Frame {
    id: root

    property string name: ""
    property alias model: lookAtModel
    signal valueChanged()

    LookAtModel {
        id: lookAtModel
        onValueChanged: root.valueChanged()
    }

    ColumnLayout {
        anchors.fill: parent

        ToolButton {
            id: toggle
            text: root.name
            checkable: true
            checked: true
        }

        ColumnLayout {
            visible: toggle.checked

            Vec3Widget {
                name: "Eye"
                xValue: lookAtModel.eye.x
                yValue: lookAtModel.eye.y
                zValue: lookAtModel.eye.z
                xFrom: -20.0; xTo: 20.0
                yFrom: -20.0; yTo: 20.0
                zFrom: -20.0; zTo: 20.0
                onValueChanged: {
                    if (lookAtModel.eye.x !== xValue) lookAtModel.eye.x = xValue
                    if (lookAtModel.eye.y !== yValue) lookAtModel.eye.y = yValue
                    if (lookAtModel.eye.z !== zValue) lookAtModel.eye.z = zValue
                }
            }

            Vec3Widget {
                name: "Look"
                xValue: lookAtModel.look.x
                yValue: lookAtModel.look.y
                zValue: lookAtModel.look.z
                xFrom: -20.0; xTo: 20.0
                yFrom: -20.0; yTo: 20.0
                zFrom: -20.0; zTo: 20.0
                onValueChanged: {
                    if (lookAtModel.look.x !== xValue) lookAtModel.look.x = xValue
                    if (lookAtModel.look.y !== yValue) lookAtModel.look.y = yValue
                    if (lookAtModel.look.z !== zValue) lookAtModel.look.z = zValue
                }
            }

            Label { text: "World Up" }
            ComboBox {
                model: lookAtModel.up_names()
                onCurrentIndexChanged: lookAtModel.upIndex = currentIndex
            }
        }
    }
}
