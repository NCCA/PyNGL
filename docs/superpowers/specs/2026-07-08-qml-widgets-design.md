# QML widgets module — design

## Goal

Add a QML equivalent of `src/ncca/ngl/widgets/` (the PySide6/QtWidgets editors for
NGL math types) as a new sibling package `src/ncca/ngl/qml/`, with feature parity
across all 10 existing widgets, plus a demo app equivalent to
`widgets/__main__.py`'s `SimpleDialog`.

## Scope

Full parity with `src/ncca/ngl/widgets/__init__.py`'s `__all__`:
Vec2Widget, Vec3Widget, Vec4Widget, Mat2Widget, Mat3Widget, Mat4Widget,
TransformWidget, LookAtWidget, RGBColourWidget, RGBAColourWidget.

Out of scope: a colour-picker popup (QML version is spinbox + live swatch
only — see "Colour widgets" below).

## Package layout

```
src/ncca/ngl/qml/
    __init__.py            # imports all model modules (triggers QmlElement
                            # registration), re-exports model classes, __version__
    __main__.py             # demo entry point (QGuiApplication + QQmlApplicationEngine)
    vec2_model.py            # Vec2Model(QObject)
    vec3_model.py            # Vec3Model(QObject)
    vec4_model.py            # Vec4Model(QObject)
    mat_grid_model.py         # _MatGridModel base (mirrors widgets/mat_grid_widget.py)
    mat2_model.py             # Mat2Model(_MatGridModel)
    mat3_model.py             # Mat3Model(_MatGridModel) + rotate/scale method table
    mat4_model.py             # Mat4Model(_MatGridModel) + rotate/scale/translate method table
    transform_model.py        # TransformModel(QObject)
    lookat_model.py           # LookAtModel(QObject)
    rgb_colour_model.py       # RGBColourModel(QObject)
    rgba_colour_model.py      # RGBAColourModel(QObject)
    Vec2Widget.qml
    Vec3Widget.qml
    Vec4Widget.qml
    DecimalSpinBox.qml        # shared reusable float spinbox control
    MatrixGridWidget.qml      # generic NxN grid view, driven by `size` + `model` properties
    Mat2Widget.qml            # MatrixGridWidget{size:2} + Mat2Model{}
    Mat3Widget.qml            # + rotate/scale method combo
    Mat4Widget.qml            # + rotate/scale/translate method combo
    TransformWidget.qml
    LookAtWidget.qml
    RGBColourWidget.qml
    RGBAColourWidget.qml
    main.qml                  # demo window: one of each widget + live value labels
```

Same convention as `widgets/`: one class/concern per file, flat directory,
shared base extracted where duplication would otherwise occur (mat grids).
Each `.qml` file's basename is its QML type name (standard QML convention).

## Model layer (Python)

Each model is a `QObject` subclass registered as a QML type via PySide6's
`@QmlElement` decorator (requires module-level `QML_IMPORT_NAME =
"ncca.ngl.qml"` and `QML_IMPORT_MAJOR_VERSION = 1` in each file that uses the
decorator — this is a PySide6 requirement, not avoidable duplication). It
holds the actual `ncca.ngl` object and exposes it through `Property`/`Signal`,
e.g.:

```python
QML_IMPORT_NAME = "ncca.ngl.qml"
QML_IMPORT_MAJOR_VERSION = 1

@QmlElement
class Vec3Model(QObject):
    valueChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = Vec3(0.0, 0.0, 0.0)

    def get_x(self) -> float: return float(self._value.x)
    def set_x(self, v: float) -> None:
        self._value.x = v
        self.valueChanged.emit()
    x = Property(float, get_x, set_x, notify=valueChanged)
    # y, z follow the same pattern

    @Slot(result=Vec3)
    def get_value(self) -> Vec3: return self._value

    @Slot(Vec3)
    def set_value(self, v: Vec3) -> None:
        self._value = v
        self.valueChanged.emit()
```

- `_MatGridModel` (base): exposes `get_cell(row, col)`/`set_cell(row, col,
  value)` as `Slot`s, `valueChanged`, and `identity()`/`zero()`/`transpose()`/
  `inverse()` slots. Direct analogue of `_MatGridWidget`'s button handlers,
  minus QtWidgets-specific code (no `QDoubleSpinBox`/`QPushButton`
  construction — that's the QML view's job).
- `Mat2Model`/`Mat3Model`/`Mat4Model` set `mat_cls`/`size` on the base and
  (Mat3/Mat4 only) the method table (`rotate_x`/`rotate_y`/`rotate_z`/`scale`
  [/`translate` for Mat4]) — mirrors `mat2widget.py`/`mat3widget.py`/
  `mat4widget.py` exactly.
- `TransformModel`/`LookAtModel` hold child `Vec3Model`s (position/rotation/
  scale, or eye/look) as properties and recompute the output `Mat4` the same
  way `TransformWidget._update_matrix`/`LookAtWidget._update_matrix` do,
  exposed as a read-only `matrix` property + `valueChanged` signal.
- `RGBColourModel`/`RGBAColourModel` expose `r/g/b[/a]` floats and a computed
  `hex` string property for the QML swatch `Rectangle.color` binding.

### Colour widgets — picker popup

**Amended after initial implementation:** the swatch `Rectangle` is clickable
and opens a `Qt.labs.platform.ColorDialog` (with `ShowAlphaChannel` on the
RGBA widget), writing the picked colour back into `r`/`g`/`b`[`/a`]. This
supersedes the original decision below to skip a picker, once cross-platform
`ColorDialog` support was confirmed adequate for this project's use.

~~The QML colour widgets are spinbox-driven only (r/g/b[/a] `DecimalSpinBox`es
+ a live swatch `Rectangle`), with no `ColorDialog` popup. `Qt.labs.platform`'s
`ColorDialog` has patchier cross-platform support in QML than `QColorDialog`
does in QtWidgets, and the spinboxes already give full editing capability.~~

## View layer (QML) & registration mechanics

- Each `.qml` file is self-contained: it instantiates its own model
  internally (mirrors the Python widgets owning their own `_value`), e.g.
  `Vec3Widget.qml` contains `Vec3Model { id: model }`, exposes `property alias
  value: model.value`, forwards `valueChanged`, and exposes `name`/range
  properties as plain QML properties bound to the child spinboxes' `from`/
  `to`.
- `DecimalSpinBox.qml` wraps `QtQuick.Controls SpinBox` with `property real
  value`, `property real from/to/stepSize`, `property int decimals: 2`, using
  the standard QML float-spinbox pattern: an internal scaled integer
  `SpinBox` (`value = realValue * 10^decimals`) with `textFromValue`/
  `valueFromText` overridden for display/parsing.
- `MatrixGridWidget.qml` takes `property int size` and `property var model`
  (a `_MatGridModel`-derived instance created by the caller), builds a
  `size*size` grid of `DecimalSpinBox`es via nested `Repeater`s bound through
  `model.get_cell(row,col)`/`model.set_cell(row,col,value)`, refreshing all
  cells on the model's `valueChanged`. `Mat2Widget.qml`/`Mat3Widget.qml`/
  `Mat4Widget.qml` each declare their own concrete model instance and pass it
  + `size` into `MatrixGridWidget`, plus (Mat3/Mat4) the rotate/scale method
  combo box — mirrors the Python subclass split.
- Registration: `@QmlElement` calls `qmlRegisterType` at class-definition
  time, so importing the `ncca.ngl.qml` package (which imports every model
  module in `__init__.py`) makes every model instantiable from any `.qml`
  file via `import ncca.ngl.qml 1.0`. No `qmldir` file is needed since these
  are Python-backed types, not a file-based QML module.

## Demo app

`ncca/ngl/qml/__main__.py` mirrors `widgets/__main__.py`: imports the `qml`
package (triggers registration), creates a `QGuiApplication` +
`QQmlApplicationEngine`, adds the package directory to the engine's import
path, and loads `main.qml`. `main.qml` is an `ApplicationWindow` with a
`GridLayout` laying out one of each of the 10 widgets plus `Label`s bound to
their live values (direct QML analogue of `SimpleDialog`), sized to fit the
screen the same way `SimpleDialog._resize_to_fit_screen` does (via
`Screen.desktopAvailableWidth`/`Height` minus a margin, falling back to a
fixed size if unavailable).

## Testing

`tests/test_qml_*.py` (one per model or grouped by family) instantiate the
model `QObject`s directly — no `QQmlApplicationEngine`/`.qml` loading
required, since constructing the `QObject`s only needs a `QCoreApplication`
(the existing `qt_app` fixture covers this). Assert:

- property get/set round-trips
- `valueChanged` emission on every mutation path
- matrix computation for `TransformModel`/`LookAtModel`
- `_MatGridModel` `identity`/`zero`/`transpose`/`inverse` behaviour (including
  the singular-matrix case for `inverse`)

These tests require the `qt` marker (real `QObject`/signal machinery) and
won't run in the default non-GPU `uv run pytest` suite, same as existing
Qt-dependent tests — run via `uv run pytest -m qt`.

## Documentation sync

Per this repo's `CLAUDE.md` doc-sync rule for public API changes:

1. Add `docs/docs/QmlWidgets.md` with `::: ncca.ngl.qml...` directives for
   each model class.
2. Add the new page to `nav:` in `docs/mkdocs.yml`.
3. Ensure every model class has a complete Google-style docstring.
4. Update the README feature list and this repo's `CLAUDE.md` Architecture
   section to describe the new `qml/` module, alongside the existing
   `widgets/` description.
5. Verify with `uv run --with mkdocs --with "mkdocstrings[python]" mkdocs
   build --strict -f docs/mkdocs.yml` before committing.

## Non-goals

- No changes to the existing `widgets/` (QtWidgets) module — this is a
  purely additive parallel implementation.
- No colour-picker dialog (see above).
- No new project dependency — `pyside6` already provides `QtQml`/`QtQuick`/
  `QtQuickControls2`.
