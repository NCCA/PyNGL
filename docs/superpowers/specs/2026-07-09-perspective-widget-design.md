# Perspective Widget Design

**Date:** 2026-07-09
**Status:** Approved

## Goal

Add a `PerspectiveWidget` (PySide6) and matching `PerspectiveModel`/`PerspectiveWidget.qml`
(Qt Quick), following the exact structural pattern of the existing `LookAtWidget` /
`LookAtModel` pair, so users can edit fov/aspect/near/far interactively and get a live
`Mat4` computed via `ncca.ngl.perspective()`.

## Scope

In scope: one new Qt widget, one new QML model + view, docs updates, tests, demo wiring
in `main.qml`.

Out of scope: ortho/frustum widgets (separate future work if wanted), 3D preview/visualization
of the frustum.

## Qt widget — `src/ncca/ngl/widgets/perspectivewidget.py`

`PerspectiveWidget(QFrame)`, structurally identical to `LookAtWidget`:

- `valueChanged = Signal(Mat4)`
- Foldable: `QToolButton` header (name label, checkable, arrow icon) + collapsible
  `QWidget` content area, exactly per `LookAtWidget._toggle_button` /
  `_content_widget` / `toggle_collapsed`.
- Four labelled `QDoubleSpinBox` rows, one per parameter, with defaults and ranges:
  | field  | default | range        | step |
  |--------|---------|--------------|------|
  | fov    | 45.0    | 1.0 – 179.0  | 1.0  |
  | aspect | 1.333   | 0.1 – 4.0    | 0.01 |
  | near   | 0.1     | 0.01 – 10.0  | 0.01 |
  | far    | 100.0   | 1.0 – 1000.0 | 1.0  |
- Constructor signature:
  ```python
  def __init__(
      self,
      parent: QWidget | None = None,
      name: str = "",
      fov: float = 45.0,
      aspect: float = 1.333,
      near: float = 0.1,
      far: float = 100.0,
      show_mode: bool = False,
  ) -> None:
  ```
- `show_mode=False` (default): no combo box is created; `self._mode` is fixed to
  `PerspMode.OpenGL` and cannot be changed except by directly setting `.mode` (still
  exposed as a `Property` for programmatic use).
- `show_mode=True`: a `QComboBox` with items `["OpenGL", "Vulkan", "WebGPU"]` is added
  to the content layout below the four spinboxes, wired to `_update_matrix` the same
  way `LookAtWidget._up` is.
- `_update_matrix()` calls `ncca.ngl.perspective(fov, aspect, near, far, mode)` and
  emits `valueChanged`.
- Getters/setters: `get_fov/set_fov`, `get_aspect/set_aspect`, `get_near/set_near`,
  `get_far/set_far`, `get_mode/set_mode` (mode setter accepts a `PerspMode` or int
  index; only meaningful when `show_mode=True`, but always settable programmatically),
  `get_name/set_name` — mirroring `LookAtWidget`'s getter/setter + `Property` style.
- `matrix()` accessor returns the current `Mat4` (mirrors `LookAtWidget.view()`).
- Exported from `src/ncca/ngl/widgets/__init__.py` (`__all__` + import).

## QML model — `src/ncca/ngl/qml/perspective_model.py`

`PerspectiveModel(QObject)`, `@QmlElement`, mirrors `LookAtModel`:

- Four flat `float` properties — `fov`, `aspect`, `near`, `far` — each a plain
  `Property(float, getter, setter, notify=valueChanged)` (not child sub-models,
  since these are independent scalars, unlike `LookAtModel`'s `Vec3Model` children).
  Defaults match the Qt widget table above.
- `modeIndex: Property(int, ..., notify=valueChanged)`, default `0` (OpenGL).
- `@Slot(result=list) mode_names()` → `["OpenGL", "Vulkan", "WebGPU"]`, mirrors
  `LookAtModel.up_names()`.
- `valueChanged = Signal()`; `_update_matrix()` recomputes `self._matrix` via
  `ncca.ngl.perspective(...)` on any property change and emits it.
- `matrix: Property(Mat4, get_matrix, notify=valueChanged)`.
- `@Slot(result=str) matrix_text()` — same 2-decimal-place formatted grid as
  `LookAtModel.matrix_text()`.

## QML view — `src/ncca/ngl/qml/PerspectiveWidget.qml`

- `Frame` root with `property string name`, `property alias model: perspectiveModel`,
  `signal valueChanged()`, and `property bool showMode: false`.
- Toggle button header (`checkable`, `checked: true`) — same as `LookAtWidget.qml`.
- Four `DecimalSpinBox` rows bound to `perspectiveModel.fov/aspect/near/far`, each with
  its own `from_`/`to_` matching the Qt ranges table, using the same `_ready` guard
  pattern as `Vec3Widget.qml` to avoid binding loops.
- A `ComboBox` bound to `perspectiveModel.modeIndex`, wrapped in
  `visible: root.showMode` (and `Layout`/`ColumnLayout` collapse-friendly, i.e. it
  takes no space when hidden).

## Registration / wiring

- `src/ncca/ngl/qml/qmldir`: add `PerspectiveWidget 1.0 PerspectiveWidget.qml`.
- `src/ncca/ngl/qml/__init__.py`: import and `__all__`-export `PerspectiveModel`.
- `src/ncca/ngl/qml/main.qml`: add a `PerspectiveWidget { id: perspectiveWidget; name: "Perspective Widget" }`
  entry to the demo `GridLayout`, with a `Label` showing `matrix_text()` via a
  `Connections`/`onValueChanged` block, following the `TransformWidget`/`LookAtWidget`
  entries already there.

## Docs

- `docs/docs/Widgets.md`: add a `## PerspectiveWidget` section with
  `::: ncca.ngl.widgets.PerspectiveWidget`, positioned after `LookAtWidget`.
- `docs/docs/QmlWidgets.md`: add a `## PerspectiveModel` section with
  `::: ncca.ngl.qml.PerspectiveModel`, positioned after `LookAtModel`.
- No new nav page needed — both existing pages are already in `mkdocs.yml` nav.
- Verify with `uv run --with mkdocs --with "mkdocstrings[python]" mkdocs build --strict -f docs/mkdocs.yml`.

## Tests

- `tests/test_perspective_widget.py` (marked via the `qt_app`/`qtbot` fixtures, same
  as `test_lookat_widget.py`): initial values, constructor overrides, per-field
  setters, `Property` accessors, `valueChanged` signal emission per field, matrix
  correctness against `ncca.ngl.perspective()` directly, fold/collapse behaviour,
  `show_mode=True` combo box presence/items and `show_mode=False` absence, mode
  switching changes the matrix.
- `tests/test_qml_perspective_model.py` (same style as `test_qml_lookat_model.py`):
  default fov/aspect/near/far and resulting matrix, changing each field updates the
  matrix, changing `modeIndex` updates the matrix, `valueChanged` emission,
  `mode_names()` contents.

## Error handling

No new error paths — parameter validation is left to the spinbox ranges (as with all
sibling widgets); `perspective()` itself is a pure function with no exceptions in its
current implementation.
