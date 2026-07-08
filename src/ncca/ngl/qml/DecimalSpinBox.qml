// src/ncca/ngl/qml/DecimalSpinBox.qml
import QtQuick
import QtQuick.Controls

Item {
    id: root

    property real realValue: 0.0
    property real from_: -5.0
    property real to_: 5.0
    property real stepSize_: 0.01
    property int decimals: 2

    property real currentStep: stepSize_
    property bool _dragging: false
    property bool _editing: false
    property real _dragStartX: 0
    property real _dragStartValue: 0
    readonly property int _pixelsPerStep: 4
    readonly property int _dragThreshold: 3

    implicitWidth: 70
    implicitHeight: 24

    SystemPalette { id: palette }

    function _clamp(value) {
        var lo = Math.min(from_, to_)
        var hi = Math.max(from_, to_)
        return Math.max(lo, Math.min(hi, value))
    }

    function _formatValue(value) {
        return value.toFixed(decimals)
    }

    Rectangle {
        id: background
        anchors.fill: parent
        radius: 3
        border.width: 1
        border.color: root._dragging
            ? palette.highlight
            : (mouseArea.containsMouse ? palette.dark : palette.mid)
        color: root._dragging ? Qt.lighter(palette.base, 1.1) : palette.base
    }

    Text {
        id: valueText
        anchors.centerIn: parent
        visible: !root._editing
        color: palette.text
        text: root._formatValue(root.realValue)
    }

    TextInput {
        id: valueInput
        anchors.centerIn: parent
        visible: root._editing
        focus: root._editing
        color: palette.text
        validator: DoubleValidator {
            bottom: Math.min(root.from_, root.to_)
            top: Math.max(root.from_, root.to_)
            notation: DoubleValidator.StandardNotation
        }

        function commit() {
            var parsed = Number.fromLocaleString(Qt.locale(), text)
            if (!isNaN(parsed)) {
                root.realValue = root._clamp(parsed)
            }
            root._editing = false
        }

        function cancel() {
            root._editing = false
        }

        Keys.onReturnPressed: commit()
        Keys.onEnterPressed: commit()
        Keys.onEscapePressed: cancel()
        onActiveFocusChanged: if (!activeFocus && root._editing) commit()

        onVisibleChanged: {
            if (visible) {
                text = String(root.realValue)
                selectAll()
                forceActiveFocus()
            }
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.MiddleButton
        cursorShape: Qt.SizeHorCursor

        onPressed: (mouse) => {
            if (mouse.button === Qt.LeftButton) {
                root._dragStartX = mouse.x
                root._dragStartValue = root.realValue
                root._dragging = false
            } else if (mouse.button === Qt.MiddleButton) {
                ladder.startAt(mouse.x, mouse.y)
            }
        }

        onPositionChanged: (mouse) => {
            if (pressedButtons & Qt.LeftButton) {
                var dx = mouse.x - root._dragStartX
                if (!root._dragging && Math.abs(dx) > root._dragThreshold) {
                    root._dragging = true
                }
                if (root._dragging) {
                    var steps = Math.round(dx / root._pixelsPerStep)
                    root.realValue = root._clamp(root._dragStartValue + steps * root.currentStep)
                }
            } else if (ladder.visible) {
                ladder.updateHighlight(mouse.y)
            }
        }

        onReleased: (mouse) => {
            if (mouse.button === Qt.LeftButton) {
                if (!root._dragging) {
                    root._editing = true
                }
                root._dragging = false
            } else if (mouse.button === Qt.MiddleButton) {
                ladder.finish()
            }
        }
    }

    Popup {
        id: ladder
        modal: false
        focus: false
        closePolicy: Popup.NoAutoClose
        padding: 2

        property var steps: [100, 10, 1, 0.1, 0.01, 0.001, 0.0001]
        property int highlightedIndex: -1
        property int rowHeightPx: 22

        function startAt(localX, localY) {
            highlightedIndex = steps.indexOf(root.currentStep)
            if (highlightedIndex < 0) highlightedIndex = 2
            x = localX - width / 2
            y = localY - (highlightedIndex + 0.5) * rowHeightPx
            open()
        }

        function updateHighlight(localY) {
            var relativeY = localY - y
            var idx = Math.floor(relativeY / rowHeightPx)
            highlightedIndex = Math.max(0, Math.min(steps.length - 1, idx))
        }

        function finish() {
            if (highlightedIndex >= 0) {
                root.currentStep = steps[highlightedIndex]
            }
            close()
        }

        contentItem: Column {
            Repeater {
                model: ladder.steps
                delegate: Rectangle {
                    width: 60
                    height: ladder.rowHeightPx
                    color: index === ladder.highlightedIndex ? "orange" : "transparent"
                    Text {
                        anchors.centerIn: parent
                        text: modelData < 1 ? modelData.toString() : modelData.toFixed(0)
                    }
                }
            }
        }
    }
}
