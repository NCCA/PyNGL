// src/ncca/ngl/qml/Mat3Widget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ncca.ngl.qml 1.0

Frame {
    id: root

    property string name: ""
    property bool readOnly: false
    property alias model: mat3Model
    signal valueChanged()

    Mat3Model {
        id: mat3Model
        onValueChanged: root.valueChanged()
    }

    ColumnLayout {
        anchors.fill: parent
        Label { text: root.name }
        MatrixGridWidget {
            size: 3
            model: mat3Model
            readOnly: root.readOnly
        }

        RowLayout {
            visible: !root.readOnly

            ComboBox {
                id: methodCombo
                model: mat3Model.method_names()
            }

            DecimalSpinBox {
                id: angleSpin
                visible: methodCombo.currentText !== "" && mat3Model.method_kind(methodCombo.currentText) === "angle"
                from_: -360.0
                to_: 360.0
                stepSize_: 0.5
                decimals: 1
                onRealValueChanged: {
                    if (visible) {
                        mat3Model.apply_angle_method(methodCombo.currentText, realValue)
                    }
                }
            }

            Vec3Widget {
                id: xyzWidget
                visible: methodCombo.currentText !== "" && mat3Model.method_kind(methodCombo.currentText) === "xyz"
                name: "xyz"
                xValue: 1.0
                yValue: 1.0
                zValue: 1.0
                onValueChanged: {
                    if (visible) {
                        mat3Model.apply_xyz_method(methodCombo.currentText, xValue, yValue, zValue)
                    }
                }
            }
        }
    }
}
