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

**Always run the whole test suite after making changes, not just the tests for the touched file.**

## Test architecture — read this before writing/running tests

`tests/conftest.py` defines three session fixtures that require a real graphics context: `opengl_context` (glfw), `webgpu_device` (wgpu), `qt_app` (PySide6). Any test that depends on one of these fixtures is **automatically deselected from a plain `uv run pytest` run** and only runs when its marker is explicitly requested (`-m opengl`, `-m webgpu`, `-m qt`). This is why CI and default local runs "pass" without ever touching a GPU/window — don't assume a green default run means graphics-dependent code paths were exercised. If you change code under an OpenGL/WebGPU/Qt fixture, explicitly run the matching `-m` suite.

## Architecture

### Core math/graphics library — `src/ncca/ngl/`

Flat module layout, one class family per file, all re-exported from `src/ncca/ngl/__init__.py`. Key groups:

- **Math primitives**: `vec2.py`/`vec3.py`/`vec4.py` (+ `vec*_array.py` list-like containers), `mat2.py`/`mat3.py`/`mat4.py`, `quaternion.py`, `plane.py`, `bbox.py`, `transform.py`, `util.py` (lookAt/perspective/ortho/frustum/clamp/lerp).
- **Mesh/geometry**: `base_mesh.py` (`BaseMesh`, `Face`) is the base for loadable/generatable geometry; `obj.py` (`Obj`) parses Wavefront OBJ on top of it; `prim_data.py` generates raw vertex data for primitive shapes (`Prims` enum + `PrimData`); `primitives.py` wraps that data into drawable VAOs via `VAOFactory`.
- **VAO abstraction**: `abstract_vao.py` defines the `AbstractVAO` interface + `VertexData`; `simple_vao.py`, `simple_index_vao.py`, `multi_buffer_vao.py` are concrete OpenGL implementations; `vao_factory.py` (`VAOFactory`) is a registry/factory so new VAO types can be added without touching call sites.
- **Shaders (OpenGL)**: `shader.py` (single compiled shader) → `shader_program.py` (linked program, uniform setters) → `shader_lib.py` (`ShaderLib`, a singleton registry of named shader programs — this is the conventional entry point application code uses, not `ShaderProgram` directly).
- **Cameras/input**: `first_person_camera.py`, `pyside_event_handling_mixin.py` (mouse/keyboard camera control mixin for PySide6 apps).
- **Other**: `image.py` (Pillow-backed), `texture.py`, `text.py` (freetype-py glyph atlas + geometry-shader quads), `random.py`, `log.py` (colored logger, `setup_logger`).

### `src/ncca/ngl/webgpu/`

Parallel rendering stack targeting `wgpu` instead of OpenGL. `base_webgpu_pipeline.py` is the common base; `*_pipeline.py` files (triangle, line, point, point_list, instanced_geometry, custom_shader) are concrete render pipelines; `pipeline_factory.py` mirrors the OpenGL `VAOFactory` pattern for pipelines; `pipeline_shaders.py`/`webgpu_constants.py` hold shader source and enum constants. Has its own `__main__.py` for standalone demo/dev runs.

### `src/ncca/ngl/widgets/`

PySide6 (Qt) widgets for editing/displaying NGL types in GUIs: `vec2widget.py`/`vec3widget.py`/`vec4widget.py`, `mat4widget.py`, `transformwidget.py`, `rgbcolourwidget.py`/`rgbacolourwidget.py`, `lookatwidget.py`. Has GLSL assets under `widgets/glsl/`.

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
