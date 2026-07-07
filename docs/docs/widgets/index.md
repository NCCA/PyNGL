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
| `TransformWidget` | position / rotation / scale | `valueChanged(Mat4)` |
| `LookAtWidget` | eye / look / up | `valueChanged(Mat4)` (a `look_at` view matrix) |
| `RGBColourWidget` | RGB sliders + colour dialog | `colourChanged(Vec3)` |
| `RGBAColourWidget` | RGBA sliders + colour dialog | `colourChanged(Vec4)` |

All widgets share the constructor shape
`Widget(parent=None, name="", <initial value...>)` — `name` is the label
shown on the widget frame:

```python
from ncca.ngl import Vec3
from ncca.ngl.widgets import Vec3Widget

position = Vec3Widget(self, "Position", Vec3(0, 1, 0))
```

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
