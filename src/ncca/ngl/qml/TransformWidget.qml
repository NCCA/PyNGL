// src/ncca/ngl/qml/TransformWidget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ncca.ngl.qml 1.0

Frame {
    id: root

    property string name: ""
    property alias model: txModel
    signal valueChanged()

    TransformModel {
        id: txModel
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
                name: "Position"
                xValue: txModel.position.x
                yValue: txModel.position.y
                zValue: txModel.position.z
                xFrom: -20.0; xTo: 20.0
                yFrom: -20.0; yTo: 20.0
                zFrom: -20.0; zTo: 20.0
                onValueChanged: {
                    if (txModel.position.x !== xValue) txModel.position.x = xValue
                    if (txModel.position.y !== yValue) txModel.position.y = yValue
                    if (txModel.position.z !== zValue) txModel.position.z = zValue
                }
            }

            Vec3Widget {
                name: "Rotation"
                xValue: txModel.rotation.x
                yValue: txModel.rotation.y
                zValue: txModel.rotation.z
                xFrom: -360.0; xTo: 360.0
                yFrom: -360.0; yTo: 360.0
                zFrom: -360.0; zTo: 360.0
                onValueChanged: {
                    if (txModel.rotation.x !== xValue) txModel.rotation.x = xValue
                    if (txModel.rotation.y !== yValue) txModel.rotation.y = yValue
                    if (txModel.rotation.z !== zValue) txModel.rotation.z = zValue
                }
            }

            Vec3Widget {
                name: "Scale"
                xValue: txModel.scale.x
                yValue: txModel.scale.y
                zValue: txModel.scale.z
                xFrom: -20.0; xTo: 20.0
                yFrom: -20.0; yTo: 20.0
                zFrom: -20.0; zTo: 20.0
                onValueChanged: {
                    if (txModel.scale.x !== xValue) txModel.scale.x = xValue
                    if (txModel.scale.y !== yValue) txModel.scale.y = yValue
                    if (txModel.scale.z !== zValue) txModel.scale.z = zValue
                }
            }

            Label { text: "Rotation Order" }
            ComboBox {
                model: txModel.rotation_orders()
                onCurrentIndexChanged: txModel.rotationOrderIndex = currentIndex
            }
        }
    }
}
