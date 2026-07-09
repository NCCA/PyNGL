// src/ncca/ngl/qml/PerspectiveWidget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ncca.ngl.qml 1.0

Frame {
    id: root

    property string name: ""
    property alias model: perspectiveModel
    property bool showMode: false
    signal valueChanged()

    PerspectiveModel {
        id: perspectiveModel
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

            RowLayout {
                Label { text: "Fov" }
                DecimalSpinBox {
                    id: fovSpin
                    realValue: perspectiveModel.fov
                    from_: 1.0; to_: 179.0; stepSize_: 1.0; decimals: 1
                    onRealValueChanged: {
                        if (perspectiveModel.fov !== realValue) {
                            perspectiveModel.fov = realValue
                        }
                    }
                }
            }

            RowLayout {
                Label { text: "Aspect" }
                DecimalSpinBox {
                    id: aspectSpin
                    realValue: perspectiveModel.aspect
                    from_: 0.1; to_: 4.0; stepSize_: 0.01; decimals: 3
                    onRealValueChanged: {
                        if (perspectiveModel.aspect !== realValue) {
                            perspectiveModel.aspect = realValue
                        }
                    }
                }
            }

            RowLayout {
                Label { text: "Near" }
                DecimalSpinBox {
                    id: nearSpin
                    realValue: perspectiveModel.near
                    from_: 0.01; to_: 10.0; stepSize_: 0.01; decimals: 2
                    onRealValueChanged: {
                        if (perspectiveModel.near !== realValue) {
                            perspectiveModel.near = realValue
                        }
                    }
                }
            }

            RowLayout {
                Label { text: "Far" }
                DecimalSpinBox {
                    id: farSpin
                    realValue: perspectiveModel.far
                    from_: 1.0; to_: 1000.0; stepSize_: 1.0; decimals: 1
                    onRealValueChanged: {
                        if (perspectiveModel.far !== realValue) {
                            perspectiveModel.far = realValue
                        }
                    }
                }
            }

            RowLayout {
                visible: root.showMode
                Label { text: "Mode" }
                ComboBox {
                    model: perspectiveModel.mode_names()
                    currentIndex: perspectiveModel.modeIndex
                    onCurrentIndexChanged: perspectiveModel.modeIndex = currentIndex
                }
            }
        }
    }
}
