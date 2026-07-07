# Qt Widgets for NGL Types

`ncca.ngl.widgets` provides ready-made PySide6 widgets for editing and
displaying NGL math types in a GUI — spin-box clusters for vectors,
colour pickers that speak `Vec3`/`Vec4`, and composite editors that emit
`Mat4` transforms. They are ordinary `QWidget`s (each is a `QFrame`), so
they drop into any Qt layout.

See them all at once with the bundled demo:

```bash
uv run python -m ncca.ngl.widgets
```

## The widgets

| Widget | Edits | Value signal |
|---|---|---|
| `Vec2Widget` | two spin boxes | `valueChanged(Vec2)` |
| `Vec3Widget` | three spin boxes | `valueChanged(Vec3)` |
| `Vec4Widget` | four spin boxes | `valueChanged(Vec4)` |
| `Mat2Widget` | 2x2 grid + reset buttons | `valueChanged(Mat2)` |
| `Mat3Widget` | 3x3 grid + reset buttons + method combo | `valueChanged(Mat3)` |
| `Mat4Widget` | 4x4 grid + reset buttons + method combo | `valueChanged(Mat4)` |
| `TransformWidget` | position / rotation / scale | `valueChanged(Mat4)` |
| `LookAtWidget` | eye / look / up | `valueChanged(Mat4)` (a `look_at` view matrix) |
| `RGBColourWidget` | RGB sliders + colour dialog | `colourChanged(Vec3)` |
| `RGBAColourWidget` | RGBA sliders + colour dialog | `colourChanged(Vec4)` |

The vector, transform, look-at and colour widgets share the constructor
shape `Widget(parent=None, name="", <initial value...>)` — `name` is the
label shown on the widget frame:

```python
from ncca.ngl import Vec3
from ncca.ngl.widgets import Vec3Widget

position = Vec3Widget(self, "Position", Vec3(0, 1, 0))
```

The matrix widgets (below) instead take `Widget(parent=None, name="",
read_only=False)` — no initial-value argument, since they always start
from an identity matrix; use `set_value()` to set a starting value.

## Signals

Beyond the whole-value signal, the vector widgets emit per-component
`float` signals (`xValueChanged`, `yValueChanged`, `zValueChanged`,
`wValueChanged`), and the colour widgets per-channel ones
(`rValueChanged`, `gValueChanged`, `bValueChanged`, `aValueChanged`).
Connect whichever granularity you need:

```python
position.valueChanged.connect(self.set_position)   # receives a Vec3
position.yValueChanged.connect(self.set_height)    # receives a float
```

Values are read and written with `get_value()` / `set_value(...)`
(`get_eye`/`set_eye`, `get_look`, `get_up` on `LookAtWidget`;
`set_colour` on the colour widgets).

## Ranges and steps

The vector widgets default to a small range, so set what your scene
needs — per component or all at once:

```python
position.set_range(-10.0, 10.0)     # all components
position.set_y_range(0.0, 5.0)      # just Y
position.set_single_step(0.1)
```

`set_range()`/`set_single_step()` work the same way on the matrix grid
widgets below, applied to every cell.

## Matrix grid widgets

`Mat2Widget`/`Mat3Widget`/`Mat4Widget` edit a matrix as a grid of spin
boxes, with **Identity**/**Zero**/**Transpose**/**Inverse** buttons that
reset or transform the current value (Inverse shows "Matrix is singular"
instead of raising if the matrix isn't invertible):

```python
from ncca.ngl.widgets import Mat4Widget

model_matrix = Mat4Widget(self, "Model")
model_matrix.valueChanged.connect(viewport.set_model)   # Mat4
```

`Mat3Widget` and `Mat4Widget` also have a method combo box
(`rotate_x`/`rotate_y`/`rotate_z`/`scale`, plus `translate` on
`Mat4Widget`) that sets the matrix from the corresponding classmethod.
Selecting a rotation shows a single angle (degrees) spin box; selecting
`scale`/`translate` shows an embedded `Vec3Widget` instead. Whichever
panel is visible updates the matrix live — there's no separate "Apply"
button.

### Read-only (view) mode

Pass `read_only=True` to get a plain display grid with no reset buttons
and no method combo — the cells can't be typed into, but `set_value()`
still updates what's shown. Use this to display a matrix that's produced
elsewhere (e.g. a `TransformWidget` output) without offering a second,
conflicting way to edit it:

```python
transform = TransformWidget(self, "Model")
transform_matrix = Mat4Widget(self, "Model Matrix", read_only=True)
transform.valueChanged.connect(transform_matrix.set_value)
```

## Driving a viewport

The typical use is a control panel beside an OpenGL (or WebGPU)
viewport: connect the widget signals to slots that store the value and
schedule a repaint.

```python
from ncca.ngl import Mat4, Vec3, Vec4
from ncca.ngl.widgets import LookAtWidget, RGBColourWidget, TransformWidget


class ControlPanel(QWidget):
    def __init__(self, viewport):
        super().__init__()
        layout = QVBoxLayout(self)

        camera = LookAtWidget(self, "Camera", eye=Vec3(2, 2, 2))
        camera.valueChanged.connect(viewport.set_view)        # Mat4

        transform = TransformWidget(self, "Model")
        transform.valueChanged.connect(viewport.set_model)    # Mat4

        colour = RGBColourWidget(self, "Colour", 0.8, 0.5, 0.2)
        colour.colourChanged.connect(viewport.set_colour)     # Vec3

        for w in (camera, transform, colour):
            layout.addWidget(w)
```

In the viewport slots, store the value and call `self.update()`; the next
`paintGL` picks it up. `TransformWidget` and `LookAtWidget` both hand you
a finished `Mat4` — the model matrix and the view matrix respectively —
so the paint code just multiplies:

```python
mvp = self.project @ self.view @ self.model
```

The demo dialog in
[`src/ncca/ngl/widgets/__main__.py`](https://github.com/NCCA/PyNGL/blob/main/src/ncca/ngl/widgets/__main__.py)
shows every widget wired to live value labels and is a good copy-paste
source.

Full API: [Widgets reference](../Widgets.md).
