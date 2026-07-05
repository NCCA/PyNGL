# OpenGL submodule refactor

## Goal

Move all directly OpenGL-coupled modules out of the flat `src/ncca/ngl/`
layout into a new `src/ncca/ngl/opengl/` sub-package, mirroring the existing
`src/ncca/ngl/webgpu/` structure. Math primitives, mesh/geometry data types,
cameras, and other API-agnostic modules stay at the top level.

## Scope decisions

- **In scope:** modules that directly `import OpenGL.GL`.
- **`obj.py` stays at top level for now**, even though it depends on
  `BaseMesh` (moving) and `Texture` (moving). It will need updated relative
  imports pointing into `opengl/`. A future refactor may split OBJ parsing
  from OpenGL rendering so the parser can be reused by the WebGPU stack —
  out of scope here, noted as a follow-up.
- **No backward-compatible re-export** of moved names from top-level
  `ncca.ngl`. This matches the existing `webgpu` precedent, where callers
  already do `from ncca.ngl.webgpu import X` rather than getting it from
  `ncca.ngl` directly. This is a breaking change for any external callers.
- Existing untracked working-tree files unrelated to this task
  (`docs/site/`, `examples/`, `glsl/`, `shaders/`,
  `src/ncca/ngl/webgpu/custom_shader_pipeline.py`,
  `src/ncca/ngl/webgpu/report`, `src/ncca/ngl/widgets/glsl/`, `.worktrees/`)
  are left untouched by this work.

## Files moving into `src/ncca/ngl/opengl/`

- `abstract_vao.py`
- `base_mesh.py`
- `multi_buffer_vao.py`
- `primitives.py`
- `pyside_event_handling_mixin.py`
- `shader.py`
- `shader_lib.py`
- `shader_program.py`
- `simple_index_vao.py`
- `simple_vao.py`
- `text.py`
- `texture.py`
- `vao_factory.py`
- `shaders/` (glsl asset directory) — `shader_lib.py` locates it via
  `Path(__file__).parent / "shaders"`, so it must move with the file to
  `src/ncca/ngl/opengl/shaders/`.

Everything else in `src/ncca/ngl/` (math types, `bbox.py`, `bezier_curve.py`,
`first_person_camera.py`, `image.py`, `log.py`, `obj.py`, `plane.py`,
`prim_data.py`, `random.py`, `transform.py`, `util.py`, `PrimData/`) stays
where it is.

## Import updates

- New `src/ncca/ngl/opengl/__init__.py`, following the `webgpu/__init__.py`
  pattern (version block, explicit imports, `__all__`), re-exporting:
  `ShaderLib`, `ShaderProgram`, `Shader`, `ShaderType`, `MatrixTranspose`,
  `DefaultShader`, `AbstractVAO`, `VertexData`, `SimpleVAO`, `SimpleIndexVAO`,
  `IndexVertexData`, `MultiBufferVAO`, `VAOFactory`, `VAOType`, `BaseMesh`,
  `Face`, `Primitives`, `PySideEventHandlingMixin`, `Text`, `Texture`.
- `src/ncca/ngl/__init__.py` removes these from its imports and `__all__`.
- Within moved files, relative imports pointing at modules that stay
  top-level gain an extra `.` level, e.g. `base_mesh.py`'s
  `from .bbox import BBox` → `from ..bbox import BBox`; `primitives.py`'s
  `from .prim_data import PrimData, Prims` → `from ..prim_data import ...`.
  Imports between two moved files stay single-dot relative imports.
- `obj.py` (staying top-level) updates:
  `from .base_mesh import BaseMesh, Face` → `from .opengl.base_mesh import BaseMesh, Face`;
  `from .texture import Texture` → `from .opengl.texture import Texture`.
- Test files updated to import from `ncca.ngl.opengl` instead of `ncca.ngl`
  for the moved symbols: `test_base_mesh.py`, `test_obj.py`,
  `test_pyside_event_handling_mixin.py`, `test_primitives.py`, `test_text.py`,
  `test_texture.py`, `test_shaderlib.py`, `test_vao.py`.
- No changes needed in `widgets/*.py` or `examples/custom_shader_example.py` —
  neither references the moved symbols.

## Verification

- `uv run pytest` (default, non-GPU suite)
- `uv run pytest -m opengl`
- `uv run pytest -m qt`
- `uv run ruff check src/` and `uv run ruff format src/`
- `tests/test_api_consistency.py` runs as part of the default suite
  (unaffected by this refactor, but confirms nothing else broke)

## Process notes

Per the user's global git workflow rules: work happens in a new git worktree
off a feature branch, tests and linters must pass before committing, and no
direct commits to `main`/`master`/`Version1.0`.
