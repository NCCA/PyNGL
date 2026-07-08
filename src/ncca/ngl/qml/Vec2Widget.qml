// src/ncca/ngl/qml/Vec2Widget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ncca.ngl.qml 1.0

Frame {
    id: root

    property string name: ""
    property alias xValue: vecModel.x
    property alias yValue: vecModel.y
    property alias xFrom: xSpin.from_
    property alias xTo: xSpin.to_
    property alias yFrom: ySpin.from_
    property alias yTo: ySpin.to_
    property alias model: vecModel
    signal valueChanged()

    Vec2Model {
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
    }
}
