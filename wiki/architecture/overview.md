---
sources:
  - src/ncca/ngl/__init__.py
  - src/ncca/ngl/opengl/__init__.py
  - src/ncca/ngl/webgpu/__init__.py
  - src/ncca/ngl/widgets/__init__.py
  - src/ncca/ngl/image.py
  - src/ncca/ngl/random.py
  - src/ncca/ngl/log.py
  - pyproject.toml
synced: cdaf11bb67c017e478348ac5591c0c90634629c7
---

# Architecture Overview

## Summary

PyNGL is organised as four package layers with a strict dependency rule: a
single API-agnostic core (`ncca.ngl`), and three API-coupled layers
(`ncca.ngl.opengl`, `ncca.ngl.webgpu`, `ncca.ngl.widgets`) that depend on the
core but never on each other. The installable module root is `src/` (see
`pyproject.toml:tool.uv.build-backend`), package name `ncca.ngl`, distribution
name `ncca-ngl`.

## How it works

**Core (`src/ncca/ngl/`, `src/ncca/ngl/__init__.py`).** Flat module layout,
one class family per file, everything re-exported via `__all__`. Contains
only code with no direct `import OpenGL.GL` / `wgpu` / `PySide6` dependency:
math primitives (`Vec2/3/4`, `Mat2/3/4`, `Quaternion`, `Plane`, `BBox`,
`Transform`, `util.py`), mesh/geometry data (`BezierCurve`, `PrimData`/`Prims`,
`Obj` — though `Obj` imports `BaseMesh`/`Face`/`Texture` from
`ncca.ngl.opengl`, the one sanctioned exception where core reaches into an
API-coupled layer for shared data structures), `FirstPersonCamera`, and the
"Other utilities" described below. This is the layer every other layer
imports from.

**OpenGL layer (`src/ncca/ngl/opengl/`, `opengl/__init__.py`).** Any module
that directly touches `OpenGL.GL` lives here, never in the top-level
package. It is a separate installed sub-package: import as
`from ncca.ngl.opengl import X`, not from `ncca.ngl` — the top-level
`__init__.py` does not re-export it. Layering inside this sub-package:
`abstract_vao.py` (`AbstractVAO`, `VertexData` interface) is implemented by
`simple_vao.py`, `simple_index_vao.py`, `multi_buffer_vao.py`, registered
through `vao_factory.py` (`VAOFactory`/`VAOType`); `base_mesh.py`
(`BaseMesh`, `Face`) is the geometry base, and `primitives.py`
(`Primitives`) wraps core's `PrimData` into drawable VAOs via
`VAOFactory`; `shader.py` → `shader_program.py` → `shader_lib.py`
(`ShaderLib`, `DefaultShader`) is the compile-link-registry chain,
`ShaderLib` being the conventional application entry point rather than
`ShaderProgram` directly; `texture.py`, `text.py` (freetype glyph atlas),
and `pyside_event_handling_mixin.py` (camera-control mixin for PySide6
apps) round out the layer.

**WebGPU layer (`src/ncca/ngl/webgpu/`, `webgpu/__init__.py`).** Parallel
rendering stack targeting `wgpu` instead of OpenGL, and deliberately mirrors
the OpenGL layer's shape: `base_webgpu_pipeline.py` is the common base
(compare `abstract_vao.py`); concrete `*_pipeline.py` files (triangle,
line, point, point_list, instanced_geometry, custom_shader) are the
implementations (compare `simple_vao.py` etc.); `pipeline_factory.py`
(`PipelineFactory`/`PipelineType`) is the registry (compare
`vao_factory.py`); `webgpu_widget.py` (`WebGPUWidget`) is the Qt-facing
entry point (compare `ShaderLib` as the conventional entry point); shader
source and constant tables live in `pipeline_shaders.py` /
`webgpu_constants.py` (`NGLToWebGPU`, compare `shaders/` glsl assets). Also
re-exported only from `ncca.ngl.webgpu`, never from top-level `ncca.ngl`.
Has its own `__main__.py` for standalone demo/dev runs.

**Widgets layer (`src/ncca/ngl/widgets/`, `widgets/__init__.py`).** PySide6
(Qt) widgets for editing/displaying core NGL types in GUIs: `Vec2Widget`,
`Vec3Widget`, `Vec4Widget`, `Mat2Widget`, `Mat3Widget`, `Mat4Widget`,
`TransformWidget`, `LookAtWidget`, `PerspectiveWidget`, `RGBColourWidget`,
`RGBAColourWidget`. Depends on core for the types it edits and on Qt for
the GUI; not re-exported from top-level `ncca.ngl`. Has its own `glsl/`
asset directory for any preview shaders.

**QML layer (`src/ncca/ngl/qml/`, `qml/__init__.py`).** The same editors
again, for Qt Quick instead of QtWidgets: a `@QmlElement`-registered
`QObject` model per type (`Vec3Model`, `Mat4Model`, `TransformModel`,
`LookAtModel`, `PerspectiveModel`, `RGBColourModel`, `RGBAColourModel`, …)
paired with a same-named `.qml` view, all declared in `qmldir` as the
file-based module `ncca.ngl.qml`. Also Qt-dependent and not re-exported
from top-level `ncca.ngl`. Exports `add_import_path(engine)`/`import_path()`
so an application's own `.qml` files can resolve the module. Has its own
`__main__.py` + `main.qml` demo.

**Other utilities (in core, `src/ncca/ngl/`).**

- `image.py` — `Image` (Pillow-backed) and `ImageModes` (`RGB`/`RGBA`/`GRAY`
  mapped to PIL mode strings). Stores pixels as a `numpy` array in `_data`;
  `load()`/`save()` go through `PIL.Image`, both catching exceptions and
  logging rather than raising, returning `bool` success instead.
- `random.py` — `Random`, a static/class-method-only port of the NGL C++
  `Random` singleton. Named float/int "generators" are held in class-level
  dicts (`_float_generators` seeded with `RandomFloat`,
  `RandomPositiveFloat`; `_int_generators` empty by default) and are
  pluggable via `add_float_generator`/`add_int_generator`. Convenience
  methods build `Vec2`/`Vec3`/`Vec4` random/normalized vectors and colours
  on top of these generators.
- `log.py` — module-level `logger` (name `"ngl"`), built by `setup_logger()`
  and exported from `ncca.ngl`. Attaches two handlers on first call (guarded
  by `if not logger.handlers`): a `FileHandler` writing `NGLDebug.log` and a
  `StreamHandler` to stdout using `ColoredFormatter` (ANSI colour by log
  level). Other modules should call `logging.getLogger(__name__)` for their
  own logger rather than importing this one directly, except where the
  shared `ngl` logger is intentionally reused.

## Key invariants

- No module under `src/ncca/ngl/` (the top level) may `import OpenGL.GL`,
  `wgpu`, or `PySide6` directly — that code belongs in `opengl/`, `webgpu/`,
  `widgets/`, or `qml/` respectively.
- `opengl/`, `webgpu/`, `widgets/`, and `qml/` symbols are **not** re-exported from
  `ncca.ngl.__init__`; callers must import from the sub-package
  (`from ncca.ngl.opengl import ShaderLib`, etc.).
- The OpenGL and WebGPU layers intentionally mirror each other's shape
  (abstract base → concrete implementations → factory → registry/entry
  point); when adding a feature to one, check whether the other needs the
  parallel addition.
- `Obj` (core) importing `BaseMesh`/`Face`/`Texture` from `ncca.ngl.opengl`
  is the one accepted core→opengl dependency; don't add others without
  reconsidering the layering.
- Build backend module name is `ncca.ngl` with `module-root = "src"`
  (`pyproject.toml`) — the installable package is `ncca-ngl` on PyPI-style
  metadata but imports as `ncca.ngl`.

## Connections

- [../modules/vao-stack.md](../modules/vao-stack.md) — VAO abstraction
  and factory detail.
- [../modules/shaders.md](../modules/shaders.md) — Shader/ShaderLib chain.
- [../modules/webgpu.md](../modules/webgpu.md) —
  WebGPU pipeline stack detail.
- [../modules/math.md](../modules/math.md) — Vec/Mat/
  Quaternion API consistency contract.
- [../modules/widgets.md](../modules/widgets.md) — Qt widget layer detail.
- [../modules/qml.md](../modules/qml.md) — the Qt Quick equivalent.
