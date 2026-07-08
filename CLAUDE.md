# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

PyNGL is a Python port of [NGL](https://github.com/NCCA/NGL), a graphics library used for teaching 3D graphics at NCCA (Bournemouth University). It supports OpenGL (via PyOpenGL/glfw), WebGPU (via `wgpu`), and Qt-based widgets (PySide6). Package managed with `uv`; the installable module is `ncca.ngl` (source root `src/`).

## Commands

Use `uv run` for everything — this project does not assume an activated venv.

```bash
# Run default test suite (non-GPU tests only, see conftest.py below)
uv run pytest

# Run a single test file / method
uv run pytest tests/test_vec3.py
uv run pytest tests/test_vec3.py::TestVec3::test_addition
uv run pytest -k "test_addition"

# Run tests requiring a real context, by marker
uv run pytest -m opengl
uv run pytest -m webgpu
uv run pytest -m qt

# Coverage
uv run pytest --cov=src --cov-report=term-missing
uv run python run_coverage_nogpu.py      # CPU-only coverage
uv run python coverage_nogpu.py          # simplified CPU-only coverage

# Lint / format
uv run ruff format src/
uv run ruff check src/
uv run ruff check --select I --fix src/  # fix import order only
uv run pre-commit run --all-files
```

A `Taskfile.yml` (go-task) wraps some of these: `task test-all`, `task lint`, `task coverage`, `task sync`.

## Documentation sync — do this whenever you touch the public API

The docs site (https://ncca.github.io/PyNGL/) is built with MkDocs + mkdocstrings from `docs/` and deployed by `.github/workflows/docs.yml`. mkdocstrings renders each class/function's docstring **live from `src/` at build time**, so editing a docstring updates the site automatically — but it does **not** discover new symbols. When you add, rename, or remove a public class or function you MUST also:

1. Update the matching `::: ncca.ngl...` directive in the relevant `docs/docs/*.md` page (Math, Geometry, VAO, Shaders, Camera, ImageAndTexture, Text, Misc). A new symbol that isn't listed there never appears in the docs.
2. Add any new page to `nav:` in `docs/mkdocs.yml`.
3. Ensure the symbol has a complete Google-style docstring — it *is* the rendered API reference — and update any tutorial examples in `docs/docs/tutorials/` that use it.
4. Update the README feature list and this file's **Architecture** section if the module layout changed.

Verify before committing (this is the drift check `gh-deploy` skips):

```bash
uv run --with mkdocs --with "mkdocstrings[python]" mkdocs build --strict -f docs/mkdocs.yml
```

`--strict` fails on broken references, bad `:::` targets, missing/orphaned nav entries, and docstring/signature mismatches (griffe warnings). The strict build passes clean and runs as a **blocking** `docs-strict` job in `docs.yml` — keep it at zero warnings.

### Type hints and docstring linting

Ruff enforces type-hint presence (`ANN` rules) and docstring presence/format (`D` rules, Google convention) on `src/` — see `[tool.ruff.lint]` in `pyproject.toml` (`ANN401`/`Any` is deliberately allowed at math/shader-uniform bridge points). Check before committing with the normal lint command — it already picks up these rules from config:

```bash
uv run ruff check src/
```

**Do not** run `ruff check --select ANN,D src/` — an explicit CLI `--select` overrides the config's `ignore` list, which wrongly re-flags the allowed `ANN401` cases.

`src/` passes clean and the check runs as a **blocking** `lint-annotations-docstrings` CI job (see `uv.yml`). Any new or touched function/class must have complete type hints and a Google-style docstring.

**Always run the whole test suite after making changes, not just the tests for the touched file.**

## Test architecture — read this before writing/running tests

`tests/conftest.py` defines three session fixtures that require a real graphics context: `opengl_context` (glfw), `webgpu_device` (wgpu), `qt_app` (PySide6). Any test that depends on one of these fixtures is **automatically deselected from a plain `uv run pytest` run** and only runs when its marker is explicitly requested (`-m opengl`, `-m webgpu`, `-m qt`). This is why CI and default local runs "pass" without ever touching a GPU/window — don't assume a green default run means graphics-dependent code paths were exercised. If you change code under an OpenGL/WebGPU/Qt fixture, explicitly run the matching `-m` suite.

## Architecture

### Core math/graphics library — `src/ncca/ngl/`

Flat module layout, one class family per file, all re-exported from `src/ncca/ngl/__init__.py`. This top-level package holds only API-agnostic modules (no direct `OpenGL.GL` imports); OpenGL-coupled modules live in the `src/ncca/ngl/opengl/` sub-package (see below) and are **not** re-exported from `ncca.ngl` — import them from `ncca.ngl.opengl` directly. Key groups:

- **Math primitives**: `vec2.py`/`vec3.py`/`vec4.py` (+ `vec*_array.py` list-like containers), `mat2.py`/`mat3.py`/`mat4.py`, `quaternion.py`, `plane.py`, `bbox.py`, `transform.py`, `util.py` (lookAt/perspective/ortho/frustum/clamp/lerp).
- **Mesh/geometry data**: `bezier_curve.py`, `prim_data.py` generates raw vertex data for primitive shapes (`Prims` enum + `PrimData`); `obj.py` (`Obj`) parses Wavefront OBJ files, importing `BaseMesh`/`Face` and `Texture` from `ncca.ngl.opengl`.
- **Cameras**: `first_person_camera.py`.
- **Other**: `image.py` (Pillow-backed), `random.py`, `log.py` (colored logger, `setup_logger`).

### `src/ncca/ngl/opengl/`

OpenGL-coupled modules (anything that directly `import OpenGL.GL`), mirroring the `webgpu/` sub-package structure. Re-exported from `src/ncca/ngl/opengl/__init__.py`; import as `from ncca.ngl.opengl import X`, not from `ncca.ngl`.

- **Mesh/geometry**: `base_mesh.py` (`BaseMesh`, `Face`) is the base for loadable/generatable geometry; `primitives.py` (`Primitives`) wraps `PrimData` (from top-level `ncca.ngl`) into drawable VAOs via `VAOFactory`.
- **VAO abstraction**: `abstract_vao.py` defines the `AbstractVAO` interface + `VertexData`; `simple_vao.py`, `simple_index_vao.py`, `multi_buffer_vao.py` are concrete implementations; `vao_factory.py` (`VAOFactory`) is a registry/factory so new VAO types can be added without touching call sites.
- **Shaders**: `shader.py` (single compiled shader) → `shader_program.py` (linked program, uniform setters) → `shader_lib.py` (`ShaderLib`, a singleton registry of named shader programs — this is the conventional entry point application code uses, not `ShaderProgram` directly).
- **Input**: `pyside_event_handling_mixin.py` (mouse/keyboard camera control mixin for PySide6 apps).
- **Other**: `texture.py`, `text.py` (freetype-py glyph atlas + geometry-shader quads), `shaders/` (glsl assets used by `shader_lib.py`).

### `src/ncca/ngl/webgpu/`

Parallel rendering stack targeting `wgpu` instead of OpenGL. `base_webgpu_pipeline.py` is the common base; `*_pipeline.py` files (triangle, line, point, point_list, instanced_geometry, custom_shader) are concrete render pipelines; `pipeline_factory.py` mirrors the OpenGL `VAOFactory` pattern for pipelines; `pipeline_shaders.py`/`webgpu_constants.py` hold shader source and enum constants. Has its own `__main__.py` for standalone demo/dev runs.

### `src/ncca/ngl/widgets/`

PySide6 (Qt) widgets for editing/displaying NGL types in GUIs: `vec2widget.py`/`vec3widget.py`/`vec4widget.py`, `mat2widget.py`/`mat3widget.py`/`mat4widget.py` (editable NxN grids sharing the private `_MatGridWidget` base in `mat_grid_widget.py`; Mat3Widget/Mat4Widget add a method combo box for `rotate_x`/`rotate_y`/`rotate_z`/`scale`/`translate`), `transformwidget.py`, `rgbcolourwidget.py`/`rgbacolourwidget.py`, `lookatwidget.py`. Has GLSL assets under `widgets/glsl/`.

### `src/ncca/ngl/qml/`

Qt Quick (QML) equivalents of the `widgets/` PySide6 widgets: `vec2_model.py`/`vec3_model.py`/`vec4_model.py`,
`mat_grid_model.py` (shared base) + `mat2_model.py`/`mat3_model.py`/`mat4_model.py`, `transform_model.py`,
`lookat_model.py`, `rgb_colour_model.py`/`rgba_colour_model.py` — each a `QObject` registered as a QML type via
`@QmlElement`, paired with a same-named `.qml` view file (`Vec3Widget.qml`, `Mat4Widget.qml`, etc.) plus shared
`DecimalSpinBox.qml`/`MatrixGridWidget.qml` components. Has its own `__main__.py` + `main.qml` demo, run via
`python -m ncca.ngl.qml`.

### API consistency conventions

- All math classes (`Vec2/3/4`, `Mat2/3/4`, `Quaternion`) follow one contract:
  numpy `np.float32` storage in `_data`; immutable-style operations returning
  new objects (`normalized()`, `transposed()`, `inverse()`, `clamped()` — only
  `set()` and element assignment mutate); constructors take components with a
  sensible default; `from_list`/`from_numpy` classmethods;
  `copy()`/`to_numpy()`/`to_list()`/`to_tuple()`; `__eq__`/`__hash__`; eval-able
  `__repr__`. `@` is the linear-algebra product; `*` is scalar only, except
  `Quaternion * Vec3`, which rotates the vector (kept per spec).
  `tests/test_api_consistency.py` enforces this — run it when touching math code.
- Prefer numpy arrays (`np.float32`) over Python lists for numeric data; use `__slots__` on data-heavy classes.
- Module-specific errors are plain `Exception` subclasses named `<Module>Error` (e.g. `MatrixError`, `ObjParseVertexError`), raised rather than returning sentinel values.
- **"Colour"** (not "color") is the correct spelling in this codebase's identifiers, docs, and variables.
- Docstrings are Google-style with Args/Returns/Raises; type hints are required on all function signatures and class attributes.
- Executable scripts use the shebang `#!/usr/bin/env -S uv run --script`.
