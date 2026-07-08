# Qt Quick (QML) Widgets for NGL Types

`ncca.ngl.qml` provides Qt Quick equivalents of the `ncca.ngl.widgets`
PySide6 widgets — the same editors for NGL math types, built as QML
components instead of `QWidget`s. Each widget pairs a Python model
(a `QObject` holding the actual `ncca.ngl` value) with a `.qml` view file
that binds to it declaratively.

See them all at once with the bundled demo:

```bash
uv run python -m ncca.ngl.qml
```

## The widgets

| QML type | Edits | Value signal |
|---|---|---|
| `Vec2Widget` | two spin boxes | `valueChanged()` |
| `Vec3Widget` | three spin boxes | `valueChanged()` |
| `Vec4Widget` | four spin boxes | `valueChanged()` |
| `Mat2Widget` | 2x2 grid + reset buttons | `valueChanged()` |
| `Mat3Widget` | 3x3 grid + reset buttons + method combo | `valueChanged()` |
| `Mat4Widget` | 4x4 grid + reset buttons + method combo | `valueChanged()` |
| `TransformWidget` | position / rotation / scale | `valueChanged()` |
| `LookAtWidget` | eye / look / up | `valueChanged()` (a `look_at` view matrix) |
| `RGBColourWidget` | RGB spin boxes + swatch + colour picker | `colourChanged()` |
| `RGBAColourWidget` | RGBA spin boxes + swatch + colour picker | `colourChanged()` |

Unlike the PySide6 widgets (which emit the actual `Vec3`/`Mat4` object),
the QML signals are plain no-argument notifications — QML/JS can't hold a
numpy-backed `ncca.ngl` object directly, so read the value back through the
widget's aliased properties (`xValue`/`yValue`/`zValue`/...) or its
`model.get_value()` slot.

## Editing a number: the scrub field

Every numeric field in these widgets (vector components, matrix cells,
colour channels) is a `DecimalSpinBox` — a Houdini-style drag/scrub control,
not a conventional spin box with up/down arrows:

- **Left-click and drag** left/right to scrub the value smoothly, using the
  field's current increment (`stepSize_` by default, or whatever the ladder
  below last selected).
- **Left-click without dragging** puts the field into text-edit mode so you
  can type an exact value — `Enter` commits, `Escape` cancels back to the
  previous value.
- **Middle-click (or right-click, i.e. a trackpad's two-finger click) and
  hold** opens a ladder popup to the left of the field, listing magnitudes
  `100 / 10 / 1 / .1 / .01 / .001 / .0001`. While the button is held, moving
  the mouse **vertically** picks which magnitude is active, and moving it
  **horizontally** scrubs the value live at that magnitude — release to
  commit that magnitude as the field's new drag increment. This lets you
  jump to large or very fine changes without repeatedly re-dragging at the
  default increment.

The colour widgets' swatch is also clickable: it opens a native colour
picker (`Qt.labs.platform.ColorDialog`, with alpha support on
`RGBAColourWidget`) that writes the picked colour back into the model.

## Using a widget in your own `.qml` file

Every widget registers itself under the `ncca.ngl.qml` import, so importing
the package from Python (which happens automatically if you import
anything from `ncca.ngl.qml`) makes the types available to any `.qml` file
on the engine's import path:

```qml
import QtQuick
import QtQuick.Layouts
import ncca.ngl.qml 1.0

ColumnLayout {
    Vec3Widget {
        id: position
        name: "Position"
        xValue: 0.0; yValue: 1.0; zValue: 0.0
        onValueChanged: console.log(position.xValue, position.yValue, position.zValue)
    }
}
```

```python
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

import ncca.ngl.qml  # registers every widget type

app = QGuiApplication(sys.argv)
engine = QQmlApplicationEngine()
engine.addImportPath(str(Path("src/ncca/ngl/qml")))  # ships alongside your .qml files
engine.load(QUrl.fromLocalFile("my_panel.qml"))
sys.exit(app.exec())
```

## Ranges

The vector and matrix-cell spin boxes default to a small range, matching
the PySide6 widgets. Override per axis/cell via the exposed properties:

```qml
Vec3Widget {
    name: "Position"
    xFrom: -10.0; xTo: 10.0
    yFrom: 0.0; yTo: 5.0
}
```

`MatrixGridWidget` (used internally by `Mat2Widget`/`Mat3Widget`/`Mat4Widget`)
exposes `cellMin`/`cellMax` the same way.

## Matrix grid widgets

`Mat2Widget`/`Mat3Widget`/`Mat4Widget` edit a matrix as a grid of spin
boxes, with **Identity**/**Zero**/**Transpose**/**Inverse** buttons —
`Inverse` sets `model.statusMessage` to `"Matrix is singular"` instead of
raising if the matrix isn't invertible, which the view surfaces as a label.

`Mat3Widget`/`Mat4Widget` also expose a method combo box
(`rotate_x`/`rotate_y`/`rotate_z`/`scale`, plus `translate` on `Mat4Widget`)
that sets the matrix from the matching classmethod — a single angle spin
box for rotations, an embedded `Vec3Widget` for `scale`/`translate`.

### Read-only (view) mode

Set `readOnly: true` for a plain display grid with no reset buttons and no
method combo — cells can't be typed into, but the bound model still
updates what's shown:

```qml
Mat4Widget { id: modelMatrix; name: "Model" }
Mat4Widget {
    id: modelMatrixView
    name: "Model Matrix"
    readOnly: true
    Connections {
        target: modelMatrix.model
        function onValueChanged() {
            for (var r = 0; r < 4; r++)
                for (var c = 0; c < 4; c++)
                    modelMatrixView.model.set_cell(r, c, modelMatrix.model.get_cell(r, c))
        }
    }
}
```

## Driving a viewport

`TransformWidget`/`LookAtWidget` compute a `Mat4` you can read via
`widget.model.get_matrix()` (a `Slot`) or display live via
`widget.model.matrix_text()`, exactly as shown in the bundled demo's
`main.qml`:

```qml
TransformWidget { id: transformWidget; name: "Model" }
Label {
    text: transformWidget.model.matrix_text()
    Connections {
        target: transformWidget.model
        function onValueChanged() { text = transformWidget.model.matrix_text() }
    }
}
```

The demo app in
[`src/ncca/ngl/qml/main.qml`](https://github.com/NCCA/PyNGL/blob/main/src/ncca/ngl/qml/main.qml)
and
[`src/ncca/ngl/qml/__main__.py`](https://github.com/NCCA/PyNGL/blob/main/src/ncca/ngl/qml/__main__.py)
shows every widget wired up and is a good copy-paste source.

Full API: [QML Widgets reference](../QmlWidgets.md).
