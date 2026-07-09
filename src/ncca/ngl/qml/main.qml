// src/ncca/ngl/qml/main.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import ncca.ngl.qml 1.0

ApplicationWindow {
    id: window

    title: "PyNGL ncca.ngl.qml widgets demo"
    visible: true
    width: Math.min(1000, Screen.desktopAvailableWidth - 80)
    height: Math.min(800, Screen.desktopAvailableHeight - 80)

    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth

        GridLayout {
            columns: 2
            columnSpacing: 12
            rowSpacing: 12

            Vec2Widget {
                id: vec2Widget
                name: "Vec2 Widget"
                xValue: 1.0
                yValue: 2.0
            }
            Label {
                text: "[" + vec2Widget.xValue.toFixed(2) + ", " + vec2Widget.yValue.toFixed(2) + "]"
            }

            Vec3Widget {
                id: vec3Widget
                name: "Vec3 Widget"
                xValue: 1.0
                yValue: 2.0
                zValue: 3.0
            }
            Label {
                text: "[" + vec3Widget.xValue.toFixed(2) + ", " + vec3Widget.yValue.toFixed(2)
                    + ", " + vec3Widget.zValue.toFixed(2) + "]"
            }

            Vec4Widget {
                id: vec4Widget
                name: "Vec4 Widget"
                xValue: 1.0
                yValue: 2.0
                zValue: 3.0
                wValue: 1.0
            }
            Label {
                text: "[" + vec4Widget.xValue.toFixed(2) + ", " + vec4Widget.yValue.toFixed(2)
                    + ", " + vec4Widget.zValue.toFixed(2) + ", " + vec4Widget.wValue.toFixed(2) + "]"
            }

            Mat2Widget { id: mat2Widget; name: "Mat2 Widget" }
            Item {}

            Mat3Widget { id: mat3Widget; name: "Mat3 Widget" }
            Item {}

            Mat4Widget { id: mat4Widget; name: "Mat4 Widget" }
            Item {}

            TransformWidget { id: transformWidget; name: "Transform Widget" }
            Label {
                id: transformMatrixLabel
                font.family: "monospace"
                text: transformWidget.model.matrix_text()
                Connections {
                    target: transformWidget.model
                    function onValueChanged() {
                        transformMatrixLabel.text = transformWidget.model.matrix_text()
                    }
                }
            }

            LookAtWidget { id: lookAtWidget; name: "Look At" }
            Label {
                id: lookAtMatrixLabel
                font.family: "monospace"
                text: lookAtWidget.model.matrix_text()
                Connections {
                    target: lookAtWidget.model
                    function onValueChanged() {
                        lookAtMatrixLabel.text = lookAtWidget.model.matrix_text()
                    }
                }
            }

            PerspectiveWidget { id: perspectiveWidget; name: "Perspective Widget"; showMode: true }
            Label {
                id: perspectiveMatrixLabel
                font.family: "monospace"
                text: perspectiveWidget.model.matrix_text()
                Connections {
                    target: perspectiveWidget.model
                    function onValueChanged() {
                        perspectiveMatrixLabel.text = perspectiveWidget.model.matrix_text()
                    }
                }
            }

            RGBColourWidget { id: rgbWidget; name: "RGB Colour Widget" }
            Item {}

            RGBAColourWidget { id: rgbaWidget; name: "RGBA Colour Widget" }
            Item {}
        }
    }
}
