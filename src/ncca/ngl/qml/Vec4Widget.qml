// src/ncca/ngl/qml/Vec4Widget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ncca.ngl.qml 1.0

Frame {
    id: root

    property string name: ""
    property alias xValue: vecModel.x
    property alias yValue: vecModel.y
    property alias zValue: vecModel.z
    property alias wValue: vecModel.w
    property alias xFrom: xSpin.from_
    property alias xTo: xSpin.to_
    property alias yFrom: ySpin.from_
    property alias yTo: ySpin.to_
    property alias zFrom: zSpin.from_
    property alias zTo: zSpin.to_
    property alias wFrom: wSpin.from_
    property alias wTo: wSpin.to_
    property alias model: vecModel
    signal valueChanged()

    Vec4Model {
        id: vecModel
        onValueChanged: root.valueChanged()
    }

    RowLayout {
        anchors.fill: parent
        Label { text: root.name }
        DecimalSpinBox {
            id: xSpin
            realValue: vecModel.x
            onRealValueChanged: vecModel.x = realValue
        }
        DecimalSpinBox {
            id: ySpin
            realValue: vecModel.y
            onRealValueChanged: vecModel.y = realValue
        }
        DecimalSpinBox {
            id: zSpin
            realValue: vecModel.z
            onRealValueChanged: vecModel.z = realValue
        }
        DecimalSpinBox {
            id: wSpin
            realValue: vecModel.w
            onRealValueChanged: vecModel.w = realValue
        }
    }
}
