---
sources:
  - src/ncca/ngl/qml/**
synced: cdaf11bb67c017e478348ac5591c0c90634629c7
---

# QML Models and Views

## Summary

`src/ncca/ngl/qml/` is the Qt Quick counterpart to `src/ncca/ngl/widgets/`:
the same set of editors for NGL math types (`Vec2/3/4`, `Mat2/3/4`,
`Transform`, look-at, perspective, RGB/RGBA colour), but split the QML way
into a Python `QObject` holding the value and a `.qml` file drawing it.
Every model is registered as a QML type with `@QmlElement`, and every view
is declared in `qmldir`, so a Qt Quick application writes
`import ncca.ngl.qml 1.0` and then `Vec3Widget { ... }` rather than
constructing anything in Python.

## How it works

### The model half

Each `*_model.py` defines one `QObject` subclass decorated with
`@QmlElement`, which registers it under the `QML_IMPORT_NAME` /
`QML_IMPORT_MAJOR_VERSION` module-level constants both files declare
(`"ncca.ngl.qml"` and `1`). Registration happens as a side effect of
importing the module, which is why `__main__.py` carries a bare
`import ncca.ngl.qml  # noqa: F401` with a comment saying so.

The models follow one shape:

- The NGL value lives in `self._value`; QML never sees it directly.
- Components are exposed as Qt `Property` objects backed by `get_*`/`set_*`
  pairs, with `notify=` pointing at a single aggregate signal
  (`valueChanged`, or `colourChanged` for the two colour models — the same
  naming split the PySide6 widgets use).
- Anything QML needs to *call* rather than read is a `@Slot`, since a plain
  Python method is invisible to QML.
- The composite models (`TransformModel`, `LookAtModel`) hold child
  `Vec3Model` instances and expose them as `Property(QObject, ..., constant=True)`
  — constant because the child object identity never changes, only its
  contents. Their own `_update_matrix` rebuilds a `Mat4` from the children
  and they publish it through a `matrix` property plus a `matrix_text()`
  slot for display.
- `PerspectiveModel` is the same pattern over `fov`/`aspect`/`near`/`far`
  plus a `modeIndex` into `mode_names()`, calling `perspective()` to
  produce its `matrix`.

`MatGridModel` (`mat_grid_model.py`) is the shared base for the three
matrix models and is deliberately *not* `@QmlElement`-registered — it has
no usable `mat_cls`/`size` of its own. Subclasses set those two class
attributes and nothing else (`Mat2Model` is 18 lines). It exposes cells
through `get_cell`/`set_cell` slots rather than N² properties, plus
`identity`/`zero`/`transpose`/`inverse` slots. `inverse` catches
`MatrixError` on a singular matrix, leaves the value alone, and publishes
"Matrix is singular" through a separate `statusMessage` property —
matching `_MatGridWidget`'s behaviour on the PySide6 side.
`Mat3Model`/`Mat4Model` add the method-combo slots (`method_names`,
`method_kind`, `apply_angle_method`, `apply_xyz_method`) over a private
`_METHODS` dict mapping a name to an `("angle" | "xyz", classmethod)` pair.

### The view half

Each model has a same-named view (`Vec3Model` → `Vec3Widget.qml`), and
`qmldir` declares every one of them plus the two shared components,
`DecimalSpinBox.qml` and `MatrixGridWidget.qml`. A view instantiates its
own model inline (`Vec3Model { id: vecModel }`), re-exposes the pieces a
parent might want as `property alias`es, and re-emits the model's signal as
its own — so from the outside a `Vec3Widget` looks like a self-contained
QML component with `xValue`/`yValue`/`zValue` and a `valueChanged` signal,
with the Python object an implementation detail. `model` is aliased too,
for anything that needs the `QObject` itself.

The spin boxes are `DecimalSpinBox`, a wrapper over QML's integer-only
`SpinBox` exposing `realValue`/`from_`/`to_`. The guarded write in each
view (`if (vecModel.x !== realValue)`) is what stops the property binding
and the change handler bouncing off each other.

### Import paths

`ncca.ngl.qml` is a file-based QML module: `qmldir` declares
`module ncca.ngl.qml`, so for an external `.qml` file to resolve
`import ncca.ngl.qml 1.0` the engine's import path has to be the directory
*containing* the `ncca/` package. That is what `add_import_path(engine)`
adds, deriving it as `Path(__file__).parents[3]` — computed from the module
file rather than `ncca.__file__` because `ncca` is a PEP 420 namespace
package and so has no `__file__` at all. `import_path()` returns the same
path without touching an engine.

`__main__.py` adds the package directory instead, which works only because
`main.qml` sits alongside the components and Qt resolves same-directory
neighbours implicitly. Don't copy that line into an application whose
`.qml` files live elsewhere; call `add_import_path` instead.

## Key invariants

- A model is only visible to QML once its module has been imported —
  `@QmlElement` registers on import, so `import ncca.ngl.qml` must happen
  before `engine.load()`.
- `QML_IMPORT_NAME` and `QML_IMPORT_MAJOR_VERSION` must be present and
  identical (`"ncca.ngl.qml"`, `1`) in every module defining a
  `@QmlElement` type; `@QmlElement` reads them from the defining module's
  globals, so a missing or mismatched pair registers the type under the
  wrong module or not at all.
- A new model needs its view added to `qmldir` as well. The type is
  reachable from Python once registered, but a `.qml` component that is not
  declared in `qmldir` is not part of the module.
- Only `@Slot`-decorated methods are callable from QML. Adding a plain
  Python method to a model and calling it from a view fails silently at
  runtime as "not a function", not at import.
- `MatGridModel` must stay unregistered — it has no `mat_cls`/`size`, so an
  instance built by QML would fail in `__init__`.
- The colour models name their aggregate signal `colourChanged`, not
  `valueChanged`, same as `RGBColourWidget`/`RGBAColourWidget`.
- `add_import_path` derives its directory from `Path(__file__).parents[3]`,
  so the four-level layout `qml -> ngl -> ncca -> containing dir` is load
  bearing; moving the package without updating that index breaks external
  QML imports.

## Connections

- [widgets.md](widgets.md) — the PySide6 widgets these mirror, and the
  source of the shared conventions (aggregate signals, `colourChanged`,
  the singular-matrix status message).
- [math.md](math.md) — the `Vec3`/`Mat4`/`Transform`/`look_at`/`perspective`
  types the models wrap.
- [../architecture/overview.md](../architecture/overview.md) — where this
  package sits in the module layout.
