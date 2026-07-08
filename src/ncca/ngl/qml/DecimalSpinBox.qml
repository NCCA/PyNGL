// src/ncca/ngl/qml/DecimalSpinBox.qml
import QtQuick
import QtQuick.Controls

SpinBox {
    id: root

    property real realValue: 0.0
    property real from_: -5.0
    property real to_: 5.0
    property real stepSize_: 0.01
    property int decimals: 2
    property bool _updating: false

    from: Math.round(from_ * Math.pow(10, decimals))
    to: Math.round(to_ * Math.pow(10, decimals))
    stepSize: Math.max(1, Math.round(stepSize_ * Math.pow(10, decimals)))
    value: Math.round(realValue * Math.pow(10, decimals))
    editable: true

    onValueModified: {
        _updating = true
        realValue = value / Math.pow(10, decimals)
        _updating = false
    }

    onRealValueChanged: {
        if (!_updating) {
            value = Math.round(realValue * Math.pow(10, decimals))
        }
    }

    validator: DoubleValidator {
        bottom: Math.min(root.from_, root.to_)
        top: Math.max(root.from_, root.to_)
        decimals: root.decimals
        notation: DoubleValidator.StandardNotation
    }

    textFromValue: function (value, locale) {
        return Number(value / Math.pow(10, root.decimals)).toLocaleString(
            locale, "f", root.decimals)
    }

    valueFromText: function (text, locale) {
        return Math.round(
            Number.fromLocaleString(locale, text) * Math.pow(10, root.decimals))
    }
}
