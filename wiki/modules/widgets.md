---
sources:
  - src/ncca/ngl/widgets/**
  - src/ncca/ngl/opengl/pyside_event_handling_mixin.py
  - src/ncca/ngl/first_person_camera.py
synced: 33b278187fbf30621d08376f7256c7bd5bb5f926
---

# Widgets and Camera Controls

## Summary

This page covers PyNGL's PySide6 (Qt) GUI layer and the two camera-control
helpers apps built with it typically pair it with. `src/ncca/ngl/widgets/`
holds `QFrame`-based editor widgets for the core math value types (`Vec2/3/4`,
`Mat2/3/4`, colours, `Transform`, look-at matrices) plus their GLSL demo
assets.
`PySideEventHandlingMixin` (`src/ncca/ngl/opengl/pyside_event_handling_mixin.py`)
gives a Qt/OpenGL window mouse-orbit and keyboard shortcuts "for free".
`FirstPersonCamera` (`src/ncca/ngl/first_person_camera.py`) is an
API-agnostic fly camera with no Qt or OpenGL dependency at all — the three
pieces live in different packages precisely because they depend on
different things.

## How it works

### Widgets package (`src/ncca/ngl/widgets/`)

Every widget is a `QFrame` subclass exported from
`src/ncca/ngl/widgets/__init__.py`. They follow one shared pattern:

- **`Vec2Widget` / `Vec3Widget` / `Vec4Widget`** (`vec2widget.py`,
  `vec3widget.py`, `vec4widget.py`) each wrap N `QDoubleSpinBox`es (one per
  component) behind a `QLabel` name. Each spinbox's `valueChanged` is wired
  to a private `_on_value_changed` slot that updates the backing `Vec*`
  in place, emits a per-component signal (`xValueChanged`, `yValueChanged`,
  ...), then emits the aggregate `valueChanged(Vec*)` signal. `set_value`
  does the reverse: it wraps all spinbox updates in `QSignalBlocker`s so
  programmatic changes don't re-trigger `_on_value_changed` per component,
  then emits `valueChanged` once itself. A Qt `Property` named `value`
  exposes `get_value`/`set_value` for use in Qt Designer / property
  animations.
- **`RGBColourWidget` / `RGBAColourWidget`** (`rgbcolourwidget.py`,
  `rgbacolourwidget.py`) are the same spinbox pattern applied to a `Vec3`/
  `Vec4` used as a colour, plus a `QPushButton` swatch that opens a
  `QColorDialog` (`_show_color_dialog`) and a `_update_button_color` helper
  that keeps the swatch's stylesheet background in sync. Their aggregate
  signal is named `colourChanged`, not `valueChanged` — deliberately
  distinct from the vector widgets even though the backing type is the same
  `Vec3`/`Vec4`.
- **`TransformWidget`** (`transformwidget.py`) composes three `Vec3Widget`s
  (Position/Rotation/Scale, each with its own numeric range) and a rotation
  order `QComboBox` inside a collapsible `QToolButton` section
  (`toggle_collapsed`). Any child change calls `_update_matrix`, which
  builds a `Transform`, calls `set_order`/`set_position`/`set_rotation`/
  `set_scale`, and emits `valueChanged(Mat4)` — the widget's public output
  is a `Mat4`, not a `Transform`.
- **`LookAtWidget`** (`lookatwidget.py`) composes two `Vec3Widget`s
  (Eye/Look) and a world-up `QComboBox` (y-up/x-up/z-up, indexing the
  class-level `world_up` list). `_update_matrix` calls `ncca.ngl.look_at`
  and emits `valueChanged(Mat4)` — a view matrix.
- **`Mat2Widget` / `Mat3Widget` / `Mat4Widget`** (`mat2widget.py`,
  `mat3widget.py`, `mat4widget.py`) each edit an NxN matrix as a grid of
  `QDoubleSpinBox`es, plus Identity/Zero/Transpose/Inverse reset buttons.
  All the mechanical grid/button/name/range logic lives once in the
  private, unexported `_MatGridWidget` base (`mat_grid_widget.py`); the
  three concrete classes just call `super().__init__(mat_cls, size, ...)`
  and declare their own typed `valueChanged = Signal(Mat2|Mat3|Mat4)`
  (Qt signals must be redeclared per-subclass — the base class emits via
  `self.valueChanged` but never declares it itself). Editing a cell updates
  the backing matrix element and re-emits `valueChanged`; the Identity/Zero
  buttons call `mat_cls.identity()`/`.zero()`; Transpose/Inverse operate on
  the *current* value (`self._value.transposed()`/`.inverse()`). Inverse
  catches `MatrixError` on a singular matrix, leaves the value unchanged,
  and writes "Matrix is singular" to a `_status_label` instead of raising.
  `Mat3Widget`/`Mat4Widget` additionally call `_add_method_combo(methods)`
  with a `dict[str, tuple[str, Callable]]` mapping a display label to a
  `("angle" | "xyz", classmethod)` pair (`rotate_x/y/z` + `scale` for
  Mat3; adds `translate` for Mat4). The combo box drives a `QStackedWidget`
  that swaps between a single angle `QDoubleSpinBox` (degrees) and an
  embedded `Vec3Widget`; changing the combo selection or the visible
  panel's value recomputes the matrix via the stored classmethod and calls
  `set_value` — there is no separate "Apply" button, matching
  `TransformWidget`'s live-update pattern. `Mat2Widget` has no combo box
  since `Mat2` has no `rotate_*`/`scale` classmethods.
- **`widgets/glsl/`** holds four demo shaders for whatever OpenGL view a
  widget-based inspector renders into: `phong.vert`/`phong.frag` (ambient+
  diffuse+specular, uniforms `model`, `MVP`, `normal_matrix`, `light_pos`,
  `view_pos`, `light_color`, `object_color`) and `picking.vert`/
  `picking.frag` (flat `face_id` colour per object for mouse-picking).
  Plain asset files, not auto-loaded — a consuming app passes them to
  `ShaderLib` itself.
- **`widgets/__main__.py`** is a standalone demo (`SimpleDialog`) wiring up
  one instance of every widget in a `QGridLayout`, useful as a live
  reference for how to construct and connect each widget.

### `PySideEventHandlingMixin`

Lives under `opengl/` (not `widgets/`) because it directly calls
`OpenGL.GL.glPolygonMode` — it is a mixin for a `QOpenGLWindow` subclass,
not a plain Qt widget. `setup_event_handling()` must be called from
`__init__` (it is not itself an `__init__`) to set up state: `rotate`/
`translate` booleans, `spin_x_face`/`spin_y_face` accumulators, last-mouse-
position trackers, `model_position` (`Vec3`), and sensitivity constants.
It then supplies `keyPressEvent` (Escape closes, W/S toggle wireframe/fill
via `glPolygonMode`, Space calls `reset_camera()`), `mousePressEvent`/
`mouseMoveEvent`/`mouseReleaseEvent` (left button accumulates
`spin_x_face`/`spin_y_face` from mouse delta for orbit rotation; right
button adjusts `model_position.x`/`.y` for panning), and `wheelEvent`
(adjusts `model_position.z` for zoom). Unhandled keys fall through to
`super().keyPressEvent(event)` so a subclass can still add its own
shortcuts.

### `FirstPersonCamera`

Lives in the top-level `src/ncca/ngl/` package (re-exported from
`ncca.ngl`), alongside the other API-agnostic math/camera code — it has no
Qt or `OpenGL.GL` import, so it works equally with the OpenGL or WebGPU
stacks, or headless. Constructed from `eye`, `look`, `up`, `fov`, and a
`PerspMode` (default `PerspMode.OpenGL`, from `util.py`, which selects the
clip-space convention `perspective()` targets). It stores `yaw`/`pitch`
angles (not the `look` point) as the source of truth for direction;
`_update_camera_vectors` derives `front`/`right`/`up` from `yaw`/`pitch`
via trig, then rebuilds `self._view` with `look_at`. Callers drive it via
`process_mouse_movement(diffx, diffy)` (scales by `sensitivity`, updates
yaw/pitch, clamps pitch to ±89° to avoid gimbal flip), `move(x, y, delta)`
(translates `eye` along `front`/`right` scaled by `speed`), and
`process_mouse_scroll(y_offset)` (adjusts `zoom` clamped to [1, 45] and
rebuilds `_projection`). `projection` and `view` are read-only properties;
`get_vp()` returns `projection @ view`.

## Key invariants

- Widget aggregate change signals only fire once per logical change:
  `_on_value_changed` fires the aggregate signal after updating one
  component; `set_value`/`set_colour` blocks all child spinbox signals
  with `QSignalBlocker` first, then fires the aggregate signal itself —
  never rely on child per-component signals firing during a programmatic
  `set_value` call.
- `RGBColourWidget`/`RGBAColourWidget` name their aggregate signal
  `colourChanged`, not `valueChanged`, even though the underlying value is
  a plain `Vec3`/`Vec4` — don't assume the vector-widget signal name
  applies to colour widgets.
- `TransformWidget` and `LookAtWidget` emit `Mat4`, not the `Transform`
  object or component vectors — consumers connect to `valueChanged` and
  receive a ready-to-use matrix.
- `PySideEventHandlingMixin.setup_event_handling()` must be called
  explicitly from the host window's `__init__`; the mixin defines no
  `__init__` of its own, so state attributes (`rotate`, `model_position`,
  etc.) do not exist until it runs.
- Package placement is deliberate: `opengl/pyside_event_handling_mixin.py`
  imports `OpenGL.GL`, so it lives under `opengl/`, not `widgets/`;
  `first_person_camera.py` imports neither Qt nor `OpenGL.GL`, so it lives
  in the top-level API-agnostic package and is re-exported from
  `ncca.ngl`.
- `FirstPersonCamera` pitch is always clamped to [-89, 89] degrees in
  `process_mouse_movement` when `_constrain_pitch` is true (the default) —
  disabling it allows the up vector to flip.
- `_MatGridWidget` (base for `Mat2Widget`/`Mat3Widget`/`Mat4Widget`) never
  declares `valueChanged` itself — each concrete subclass must redeclare
  `valueChanged = Signal(Mat2|Mat3|Mat4)` or `self.valueChanged.emit(...)`
  in the base class's `set_value`/`_on_cell_changed`/method-combo handlers
  will raise `AttributeError`.
- `_MatGridWidget.set_value` wraps every cell spinbox in `QSignalBlocker`
  via a `contextlib.ExitStack` (the count varies with `SIZE`) before
  updating them, then emits `valueChanged` once itself — same
  never-rely-on-child-signals-during-set_value rule as the vector widgets,
  just generalised to N*N children instead of a fixed 2/3/4.
- The Mat3/Mat4 method combo's angle and xyz parameter panels are shared
  across every method of that kind — switching from `scale` to `translate`
  on `Mat4Widget` keeps whatever xyz values were already entered; the
  panels do not reset when the combo selection changes.

## Connections

- [Math](math.md) — `Vec2/3/4`, `Mat4`, `Transform`, and `look_at`/
  `perspective`/`PerspMode` (from `util.py`) that the widgets and camera
  build on.
- [Shaders](shaders.md) — `ShaderLib`/`ShaderProgram`, the consumer for the
  `widgets/glsl/` demo shaders and the uniforms `FirstPersonCamera`'s
  `view`/`projection` feed.
- [Architecture overview](../architecture/overview.md) — the OpenGL vs.
  top-level package split that explains why the mixin and the camera live
  in different modules.
