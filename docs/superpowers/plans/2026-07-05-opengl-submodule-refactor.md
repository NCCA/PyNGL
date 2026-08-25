# OpenGL Submodule Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the 13 directly OpenGL-coupled modules (plus their glsl shader assets) out of the flat `src/ncca/ngl/` layout into a new `src/ncca/ngl/opengl/` sub-package, mirroring the existing `src/ncca/ngl/webgpu/` structure, with no backward-compatible re-export from the top-level package.

**Architecture:** Pure structural move — no behavior changes. All 13 files move together (they're mutually interdependent), internal relative imports are patched to keep working, a new `opengl/__init__.py` re-exports the public API (webgpu-style), and every external reference (top-level `__init__.py`, `obj.py`, 8 test files) is updated to the new location.

**Tech Stack:** Python 3.11+, PyOpenGL, uv/pytest, ruff.

## Global Constraints

- No backward-compatible re-export of moved names from top-level `ncca.ngl` — this is an intentional breaking change matching the `webgpu` precedent.
- `obj.py` stays at top level (not moved), even though it imports `BaseMesh`/`Texture` from the new `opengl/` location.
- Do not touch: `docs/site/`, `examples/`, `glsl/`, `shaders/` (top-level), `src/ncca/ngl/webgpu/custom_shader_pipeline.py`, `src/ncca/ngl/webgpu/report`, `src/ncca/ngl/widgets/glsl/`, `.worktrees/` — pre-existing untracked work outside this task's scope.
- Work happens in a git worktree on a feature branch (never commit directly to `main`/`master`/`Version1.0`); tests and linters must pass before each commit; use conventional commit messages.
- Full verification command set (must all pass before the final commit of Task 3):
  - `uv run pytest`
  - `uv run pytest -m opengl`
  - `uv run pytest -m qt`
  - `uv run ruff check src/`
  - `uv run ruff format --check src/`

---

## Task 1: Move OpenGL-coupled modules into `ngl/opengl/`

**Files:**
- Create: `src/ncca/ngl/opengl/__init__.py`
- Move: `src/ncca/ngl/abstract_vao.py` → `src/ncca/ngl/opengl/abstract_vao.py`
- Move: `src/ncca/ngl/base_mesh.py` → `src/ncca/ngl/opengl/base_mesh.py`
- Move: `src/ncca/ngl/multi_buffer_vao.py` → `src/ncca/ngl/opengl/multi_buffer_vao.py`
- Move: `src/ncca/ngl/primitives.py` → `src/ncca/ngl/opengl/primitives.py`
- Move: `src/ncca/ngl/pyside_event_handling_mixin.py` → `src/ncca/ngl/opengl/pyside_event_handling_mixin.py`
- Move: `src/ncca/ngl/shader.py` → `src/ncca/ngl/opengl/shader.py`
- Move: `src/ncca/ngl/shader_lib.py` → `src/ncca/ngl/opengl/shader_lib.py`
- Move: `src/ncca/ngl/shader_program.py` → `src/ncca/ngl/opengl/shader_program.py`
- Move: `src/ncca/ngl/simple_index_vao.py` → `src/ncca/ngl/opengl/simple_index_vao.py`
- Move: `src/ncca/ngl/simple_vao.py` → `src/ncca/ngl/opengl/simple_vao.py`
- Move: `src/ncca/ngl/text.py` → `src/ncca/ngl/opengl/text.py`
- Move: `src/ncca/ngl/texture.py` → `src/ncca/ngl/opengl/texture.py`
- Move: `src/ncca/ngl/vao_factory.py` → `src/ncca/ngl/opengl/vao_factory.py`
- Move: `src/ncca/ngl/shaders/` (9 `.glsl` files) → `src/ncca/ngl/opengl/shaders/`

**Interfaces:**
- Consumes: nothing from other tasks (first task).
- Produces: `ncca.ngl.opengl` package importable in isolation, exporting `ShaderLib`, `ShaderProgram`, `Shader`, `ShaderType`, `MatrixTranspose`, `DefaultShader`, `AbstractVAO`, `VertexData`, `SimpleVAO`, `SimpleIndexVAO`, `IndexVertexData`, `MultiBufferVAO`, `VAOFactory`, `VAOType`, `BaseMesh`, `Face`, `Primitives`, `PySideEventHandlingMixin`, `Text`, `Texture`. Task 2 and Task 3 rely on these names existing at `ncca.ngl.opengl`.

- [ ] **Step 1: Move the 13 files and the shaders asset directory with `git mv`**

```bash
mkdir -p src/ncca/ngl/opengl
git mv src/ncca/ngl/abstract_vao.py src/ncca/ngl/opengl/abstract_vao.py
git mv src/ncca/ngl/base_mesh.py src/ncca/ngl/opengl/base_mesh.py
git mv src/ncca/ngl/multi_buffer_vao.py src/ncca/ngl/opengl/multi_buffer_vao.py
git mv src/ncca/ngl/primitives.py src/ncca/ngl/opengl/primitives.py
git mv src/ncca/ngl/pyside_event_handling_mixin.py src/ncca/ngl/opengl/pyside_event_handling_mixin.py
git mv src/ncca/ngl/shader.py src/ncca/ngl/opengl/shader.py
git mv src/ncca/ngl/shader_lib.py src/ncca/ngl/opengl/shader_lib.py
git mv src/ncca/ngl/shader_program.py src/ncca/ngl/opengl/shader_program.py
git mv src/ncca/ngl/simple_index_vao.py src/ncca/ngl/opengl/simple_index_vao.py
git mv src/ncca/ngl/simple_vao.py src/ncca/ngl/opengl/simple_vao.py
git mv src/ncca/ngl/text.py src/ncca/ngl/opengl/text.py
git mv src/ncca/ngl/texture.py src/ncca/ngl/opengl/texture.py
git mv src/ncca/ngl/vao_factory.py src/ncca/ngl/opengl/vao_factory.py
git mv src/ncca/ngl/shaders src/ncca/ngl/opengl/shaders
```

- [ ] **Step 2: Fix relative imports in moved files that reference modules staying at top level**

`src/ncca/ngl/opengl/abstract_vao.py` — change:
```python
from .log import logger
```
to:
```python
from ..log import logger
```

`src/ncca/ngl/opengl/base_mesh.py` — change:
```python
from . import vao_factory
from .abstract_vao import VertexData
from .bbox import BBox
from .log import logger
```
to:
```python
from . import vao_factory
from .abstract_vao import VertexData
from ..bbox import BBox
from ..log import logger
```

`src/ncca/ngl/opengl/multi_buffer_vao.py` — change:
```python
from .abstract_vao import AbstractVAO, VertexData
from .log import logger
```
to:
```python
from .abstract_vao import AbstractVAO, VertexData
from ..log import logger
```

`src/ncca/ngl/opengl/primitives.py` — change:
```python
from .log import logger
from .prim_data import PrimData, Prims
from .simple_vao import VertexData
from .vao_factory import VAOFactory, VAOType  # noqa
from .vec3 import Vec3
```
to:
```python
from ..log import logger
from ..prim_data import PrimData, Prims
from .simple_vao import VertexData
from .vao_factory import VAOFactory, VAOType  # noqa
from ..vec3 import Vec3
```

`src/ncca/ngl/opengl/pyside_event_handling_mixin.py` — change:
```python
from .vec3 import Vec3
```
to:
```python
from ..vec3 import Vec3
```

`src/ncca/ngl/opengl/shader.py` — change:
```python
from .log import logger
```
to:
```python
from ..log import logger
```

`src/ncca/ngl/opengl/shader_lib.py` — change:
```python
from .log import logger
from .shader import Shader, ShaderType
from .shader_program import ShaderProgram
```
to:
```python
from ..log import logger
from .shader import Shader, ShaderType
from .shader_program import ShaderProgram
```

`src/ncca/ngl/opengl/shader_program.py` — change:
```python
from .log import logger
from .mat2 import Mat2
from .mat3 import Mat3
from .mat4 import Mat4
from .shader import Shader
from .vec2 import Vec2
from .vec3 import Vec3
from .vec4 import Vec4
```
to:
```python
from ..log import logger
from ..mat2 import Mat2
from ..mat3 import Mat3
from ..mat4 import Mat4
from .shader import Shader
from ..vec2 import Vec2
from ..vec3 import Vec3
from ..vec4 import Vec4
```

`src/ncca/ngl/opengl/simple_index_vao.py` — change:
```python
from .abstract_vao import AbstractVAO, VertexData
from .log import logger
```
to:
```python
from .abstract_vao import AbstractVAO, VertexData
from ..log import logger
```

`src/ncca/ngl/opengl/simple_vao.py` — change:
```python
from .abstract_vao import AbstractVAO, VertexData
from .log import logger
```
to:
```python
from .abstract_vao import AbstractVAO, VertexData
from ..log import logger
```

`src/ncca/ngl/opengl/text.py` — change:
```python
from .log import logger
from .shader_lib import DefaultShader, ShaderLib
from .simple_vao import VertexData
from .vao_factory import VAOFactory, VAOType
from .vec3 import Vec3
```
to:
```python
from ..log import logger
from .shader_lib import DefaultShader, ShaderLib
from .simple_vao import VertexData
from .vao_factory import VAOFactory, VAOType
from ..vec3 import Vec3
```

`src/ncca/ngl/opengl/texture.py` — change:
```python
from .image import Image
```
to:
```python
from ..image import Image
```

`src/ncca/ngl/opengl/vao_factory.py` — no change needed (only imports other moved files plus `.log`):
```python
from .multi_buffer_vao import MultiBufferVAO
from .simple_index_vao import SimpleIndexVAO
from .simple_vao import SimpleVAO
from .log import logger
```
to:
```python
from .multi_buffer_vao import MultiBufferVAO
from .simple_index_vao import SimpleIndexVAO
from .simple_vao import SimpleVAO
from ..log import logger
```

- [ ] **Step 3: Check for any other relative imports in the moved files referencing top-level modules**

Run: `grep -n "^from \.[a-z]" src/ncca/ngl/opengl/*.py`
Expected: every `from .X import ...` line refers only to another file inside `src/ncca/ngl/opengl/` (i.e. one of: `abstract_vao`, `base_mesh`, `multi_buffer_vao`, `primitives`, `pyside_event_handling_mixin`, `shader`, `shader_lib`, `shader_program`, `simple_index_vao`, `simple_vao`, `text`, `texture`, `vao_factory`). Any other target means Step 2 missed a line — fix it the same way (add a second `.`).

- [ ] **Step 4: Create `src/ncca/ngl/opengl/__init__.py`**

```python
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ncca-ngl")  # pragma: no cover
except PackageNotFoundError:
    __version__ = "0.0.0"  # pragma: no cover

__author__ = "Jon Macey jmacey@bournemouth.ac.uk"
__license__ = "MIT"

from .abstract_vao import AbstractVAO, VertexData
from .base_mesh import BaseMesh, Face
from .multi_buffer_vao import MultiBufferVAO
from .primitives import Primitives
from .pyside_event_handling_mixin import PySideEventHandlingMixin
from .shader import MatrixTranspose, Shader, ShaderType
from .shader_lib import DefaultShader, ShaderLib
from .shader_program import ShaderProgram
from .simple_index_vao import IndexVertexData, SimpleIndexVAO
from .simple_vao import SimpleVAO
from .text import Text
from .texture import Texture
from .vao_factory import VAOFactory, VAOType

__all__ = [
    "AbstractVAO",
    "VertexData",
    "BaseMesh",
    "Face",
    "MultiBufferVAO",
    "Primitives",
    "PySideEventHandlingMixin",
    "MatrixTranspose",
    "Shader",
    "ShaderType",
    "DefaultShader",
    "ShaderLib",
    "ShaderProgram",
    "IndexVertexData",
    "SimpleIndexVAO",
    "SimpleVAO",
    "Text",
    "Texture",
    "VAOFactory",
    "VAOType",
]
```

- [ ] **Step 5: Smoke-test the new sub-package imports in isolation**

Run: `uv run python -c "from ncca.ngl.opengl import ShaderLib, ShaderProgram, Shader, ShaderType, MatrixTranspose, DefaultShader, AbstractVAO, VertexData, SimpleVAO, SimpleIndexVAO, IndexVertexData, MultiBufferVAO, VAOFactory, VAOType, BaseMesh, Face, Primitives, PySideEventHandlingMixin, Text, Texture; print('ok')"`
Expected: `ok` (this only exercises `ncca.ngl.opengl`, not the still-broken top-level `ncca.ngl`, so an `ImportError` here means Step 2/3 missed a reference — fix before continuing).

- [ ] **Step 6: Commit**

```bash
git add src/ncca/ngl/opengl
git add -u src/ncca/ngl
git commit -m "refactor: move OpenGL-coupled modules into ncca.ngl.opengl"
```

---

## Task 2: Update top-level package and `obj.py` for the new location

**Files:**
- Modify: `src/ncca/ngl/__init__.py`
- Modify: `src/ncca/ngl/obj.py`

**Interfaces:**
- Consumes: `ncca.ngl.opengl.BaseMesh`, `ncca.ngl.opengl.Face`, `ncca.ngl.opengl.Texture` (from Task 1).
- Produces: `ncca.ngl` importable again as a whole package (no `ImportError`), with the 19 moved names no longer present in `ncca.ngl.__all__`.

- [ ] **Step 1: Remove the moved imports and `__all__` entries from `src/ncca/ngl/__init__.py`**

Remove these import lines:
```python
from .base_mesh import BaseMesh, Face
```
```python
from .multi_buffer_vao import MultiBufferVAO
```
```python
from .primitives import Primitives
```
```python
from .pyside_event_handling_mixin import PySideEventHandlingMixin
```
```python
from .shader import MatrixTranspose, Shader, ShaderType
from .shader_lib import DefaultShader, ShaderLib
from .shader_program import ShaderProgram
```
```python
from .simple_index_vao import IndexVertexData, SimpleIndexVAO
from .simple_vao import SimpleVAO
```
```python
from .text import Text
from .texture import Texture
```
```python
from .vao_factory import VAOFactory, VAOType
```

Note: `AbstractVAO`/`VertexData` were imported via `from .abstract_vao import AbstractVAO, VertexData` — remove that line too.

Remove these entries from `__all__`:
```python
    "AbstractVAO",
    "VertexData",
    "BaseMesh",
    "Face",
```
```python
    "MultiBufferVAO",
```
```python
    "Primitives",
    "PySideEventHandlingMixin",
```
```python
    "MatrixTranspose",
    "Shader",
    "ShaderType",
    "DefaultShader",
    "ShaderLib",
    "ShaderProgram",
    "IndexVertexData",
    "SimpleIndexVAO",
    "SimpleVAO",
```
```python
    "Text",
    "Texture",
```
```python
    "VAOFactory",
    "VAOType",
```

Keep everything else in `__init__.py` unchanged (math types; `Obj` and its exception classes; `Prims`/`PrimData`; `Transform`; `util` functions; `BBox`; `BezierCurve`; `FirstPersonCamera`; `Image`/`ImageModes`; `logger`; `MatrixError`; `Plane`; `Quaternion`; `Random`).

- [ ] **Step 2: Update `src/ncca/ngl/obj.py` imports**

Change:
```python
from .base_mesh import BaseMesh, Face
from .texture import Texture
```
to:
```python
from .opengl.base_mesh import BaseMesh, Face
from .opengl.texture import Texture
```

- [ ] **Step 3: Smoke-test the top-level package imports**

Run: `uv run python -c "import ncca.ngl; from ncca.ngl import Obj, Vec3, Mat4; print('ok')"`
Expected: `ok`, no `ImportError`.

- [ ] **Step 4: Commit**

```bash
git add src/ncca/ngl/__init__.py src/ncca/ngl/obj.py
git commit -m "refactor: point top-level ncca.ngl and obj.py at ncca.ngl.opengl"
```

---

## Task 3: Update test imports and run full verification

**Files:**
- Modify: `tests/test_base_mesh.py`
- Modify: `tests/test_obj.py`
- Modify: `tests/test_pyside_event_handling_mixin.py`
- Modify: `tests/test_primitives.py`
- Modify: `tests/test_text.py`
- Modify: `tests/test_texture.py`
- Modify: `tests/test_shaderlib.py`
- Modify: `tests/test_vao.py`

**Interfaces:**
- Consumes: `ncca.ngl.opengl` public API from Task 1, updated `ncca.ngl`/`obj.py` from Task 2.
- Produces: fully green test suite — nothing downstream depends on this task.

- [ ] **Step 1: Inspect current imports in each test file**

Run: `grep -n "^from ncca.ngl import\|^from ncca\.ngl\." tests/test_base_mesh.py tests/test_obj.py tests/test_pyside_event_handling_mixin.py tests/test_primitives.py tests/test_text.py tests/test_texture.py tests/test_shaderlib.py tests/test_vao.py`

Use the output to identify exactly which names each file imports from `ncca.ngl` that now live in `ncca.ngl.opengl` (per the Task 1 `__all__` list: `ShaderLib`, `ShaderProgram`, `Shader`, `ShaderType`, `MatrixTranspose`, `DefaultShader`, `AbstractVAO`, `VertexData`, `SimpleVAO`, `SimpleIndexVAO`, `IndexVertexData`, `MultiBufferVAO`, `VAOFactory`, `VAOType`, `BaseMesh`, `Face`, `Primitives`, `PySideEventHandlingMixin`, `Text`, `Texture`).

- [ ] **Step 2: Split each file's import into two lines — one for `ncca.ngl`, one for `ncca.ngl.opengl`**

`tests/test_base_mesh.py` — change:
```python
from ncca.ngl import BaseMesh, Face, Image, ImageModes, ShaderLib, Texture, Vec2, Vec3
```
to:
```python
from ncca.ngl import Image, ImageModes, Vec2, Vec3
from ncca.ngl.opengl import BaseMesh, Face, ShaderLib, Texture
```

`tests/test_obj.py` — change:
```python
from ncca.ngl import (
    Face,
    Obj,
    ObjParseFaceError,
    ObjParseNormalError,
    ObjParseUVError,
    ObjParseVertexError,
    Vec3,
)
```
to:
```python
from ncca.ngl import (
    Obj,
    ObjParseFaceError,
    ObjParseNormalError,
    ObjParseUVError,
    ObjParseVertexError,
    Vec3,
)
from ncca.ngl.opengl import Face
```

`tests/test_pyside_event_handling_mixin.py` — change:
```python
from ncca.ngl import PySideEventHandlingMixin, Vec3
```
to:
```python
from ncca.ngl import Vec3
from ncca.ngl.opengl import PySideEventHandlingMixin
```

`tests/test_primitives.py` — change:
```python
from ncca.ngl import PrimData, Primitives, Prims, Vec3
```
to:
```python
from ncca.ngl import PrimData, Prims, Vec3
from ncca.ngl.opengl import Primitives
```

`tests/test_text.py` — change:
```python
from ncca.ngl import Text
```
to:
```python
from ncca.ngl.opengl import Text
```

`tests/test_texture.py` — change:
```python
from ncca.ngl import Image, ImageModes, Texture
```
to:
```python
from ncca.ngl import Image, ImageModes
from ncca.ngl.opengl import Texture
```

`tests/test_shaderlib.py` — change:
```python
from ncca.ngl import (
    Mat2,
    Mat3,
    Mat4,
    Shader,
    ShaderLib,
    ShaderProgram,
    ShaderType,
    Vec2,
    Vec3,
    Vec4,
)
```
to:
```python
from ncca.ngl import (
    Mat2,
    Mat3,
    Mat4,
    Vec2,
    Vec3,
    Vec4,
)
from ncca.ngl.opengl import Shader, ShaderLib, ShaderProgram, ShaderType
```

`tests/test_vao.py` — change:
```python
from ncca.ngl import (
    DefaultShader,
    IndexVertexData,
    ShaderLib,
    VAOFactory,
    VAOType,
    VertexData,
)
```
to:
```python
from ncca.ngl.opengl import (
    DefaultShader,
    IndexVertexData,
    ShaderLib,
    VAOFactory,
    VAOType,
    VertexData,
)
```

- [ ] **Step 3: Run the default test suite**

Run: `uv run pytest`
Expected: all tests pass (no collection errors, no `ImportError`).

- [ ] **Step 4: Run the OpenGL-marked test suite**

Run: `uv run pytest -m opengl`
Expected: all tests pass.

- [ ] **Step 5: Run the Qt-marked test suite**

Run: `uv run pytest -m qt`
Expected: all tests pass.

- [ ] **Step 6: Run linters**

Run: `uv run ruff check src/` and `uv run ruff format --check src/`
Expected: no errors. If `ruff format --check` reports files needing formatting, run `uv run ruff format src/` and re-check.

- [ ] **Step 7: Commit**

```bash
git add tests/test_base_mesh.py tests/test_obj.py tests/test_pyside_event_handling_mixin.py tests/test_primitives.py tests/test_text.py tests/test_texture.py tests/test_shaderlib.py tests/test_vao.py
git commit -m "test: update imports for ncca.ngl.opengl module move"
```

---

## Follow-up (not part of this plan)

`obj.py` still depends on `BaseMesh`/`Texture` from `ncca.ngl.opengl`. A future refactor may split OBJ parsing from OpenGL rendering so the parser can be reused by the WebGPU stack.
