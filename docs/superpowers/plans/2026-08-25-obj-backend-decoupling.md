# OBJ parser and renderer split

`Obj` currently inherits from the OpenGL `BaseMesh`, so parsing a file also
imports the OpenGL back end and gives the parsed data a VAO, a texture id and a
`draw()` method. This plan makes `Obj` CPU-only and adds small OpenGL and
WebGPU objects which consume the same data.

## Goal

The dependency direction after the change is:

```text
OBJ file
   |
   v
Obj -> MeshData
          |
          +--> OpenGLMesh -> VAO
          |
          +--> WebGPUMesh -> GPUBuffer
```

`ncca.ngl.obj` and `ncca.ngl.mesh` must not import OpenGL, wgpu, Qt, textures
or renderer classes. The common CPU output is a flat contiguous `float32`
array containing eight floats per expanded triangle corner:

```text
x, y, z, nx, ny, nz, u, v
```

This is a breaking 2.0 API change. Do not retain `Obj.create_vao()`,
`Obj.draw()` or `Obj.obj_with_vao()` as lazy compatibility helpers.

## Scope

The work includes a backend-neutral mesh model, parser-only OBJ loading,
OpenGL and WebGPU mesh adapters, compatibility for `BaseMesh`, API
documentation and migration of the affected demos.

It does not include MTL files, automatic triangulation, indexed GPU meshes,
optional package dependency groups, `PipelineFactory` changes, a general
renderer interface or a new WebGPU OBJ viewer. `GameKeyControl` is the first
cross-backend proof.

## Decisions made before implementation

### Packed vertex data

`MeshData.triangle_vertex_data()` returns a one-dimensional,
C-contiguous `numpy.float32` array. This keeps the result compatible with
`PrimData`, `Obj2Numpy` and the existing WebGPU demos.

```python
data = mesh.triangle_vertex_data()
vertex_count = data.size // 8
```

Consumers may use `data.reshape(-1, 8)` locally where rows are useful.

### Face validation

For each triangle:

- `face.vertex` contains exactly three valid indices;
- `face.normal` is empty or contains three valid indices;
- `face.uv` is empty or contains three valid indices;
- missing normals are packed as `0.0, 0.0, 0.0`;
- missing UVs are packed as `0.0, 0.0`;
- partial optional lists and all out-of-range indices are errors.

`MeshValidationError(RuntimeError)` is used for structural mesh errors. An
empty mesh produces `np.empty(0, dtype=np.float32)` but cannot be uploaded to
either GPU back end.

### UV convention

The CPU packing method defaults to `flip_v=False`. `OpenGLMesh` requests
`flip_v=True` to preserve current behaviour. `WebGPUMesh` defaults to
`False`; a demo can request a flip when its texture-upload convention needs
one.

### Resource ownership

- `OpenGLMesh` owns and deletes its VAO.
- Texture ids passed to `OpenGLMesh` are borrowed and never deleted by it.
- `WebGPUMesh` owns and deletes its GPU vertex buffer.
- Render pipelines borrow a `WebGPUMesh` buffer and must not destroy it.
- Both cleanup methods are idempotent.
- OpenGL upload and cleanup require a current OpenGL context.

## Repository workflow

PyNGL and PyNGLDemos are separate repositories. Complete and validate the
library first, then migrate the demos against that library version. Do not
modify either `main` branch. Check that the current branch is clean, create an
`agent/` worktree and use conventional commits.

Suggested library worktree:

```bash
git worktree add .worktrees/obj-backend-split -b agent/obj-backend-split
```

Suggested demos worktree:

```bash
git worktree add .worktrees/obj-backend-demos -b agent/obj-backend-demos
```

Use a test-first loop for each task: add the failing test, implement the
smallest change, then refactor.

## Part 1: PyNGL library

### 1. Add the backend-neutral mesh module

Add:

```text
src/ncca/ngl/mesh.py
tests/test_mesh.py
```

Move `Face` out of `ncca.ngl.opengl.base_mesh` and define it as:

```python
@dataclass(slots=True)
class Face:
    vertex: list[int] = field(default_factory=list)
    uv: list[int] = field(default_factory=list)
    normal: list[int] = field(default_factory=list)
```

This must preserve the existing `Face()` followed by list mutation API.

Add:

```python
class MeshValidationError(RuntimeError):
    """Raised when mesh data cannot be converted into renderable triangles."""
```

Add `MeshData` with these public fields:

```python
vertex: list[Vec3]
normals: list[Vec3]
uv: list[Vec2 | Vec3]
faces: list[Face]
colour: list[Vec3]
bbox: BBox | None
min_x: float
max_x: float
min_y: float
max_y: float
min_z: float
max_z: float
```

`colour` is always present. It is either empty or contains a value for every
vertex.

Add these methods:

```python
def is_triangular(self) -> bool: ...
def validate(self) -> None: ...
def calc_dimensions(self) -> None: ...
def triangle_vertex_data(self, *, flip_v: bool = False) -> np.ndarray: ...
```

`validate()` checks the colour invariant, face list lengths and all index
ranges. `triangle_vertex_data()` calls validation, requires triangles and
returns the standard flat P/N/UV format. `calc_dimensions()` resets an empty
mesh to zero extents and `bbox=None`; otherwise it updates extents and builds
the `BBox` with `BBox.from_extents()`.

Tests must cover empty construction, mutable faces, triangular and
non-triangular data, exact component ordering, flat float32 output, missing
normal and UV data, V flipping, invalid indices, partial attributes, invalid
colours, empty data and bounds.

Commit:

```text
feat(mesh): add backend-neutral mesh data
```

### 2. Make `Obj` parser-only

Modify:

```text
src/ncca/ngl/obj.py
src/ncca/ngl/__init__.py
tests/test_obj.py
```

Make `Obj` inherit from `MeshData`. Remove its OpenGL imports and remove
`obj_with_vao()` along with all inherited VAO, texture and drawing behaviour.

Keep the existing load, save and add methods. `load()` retains its current
append behaviour in this change. `from_file()` must create `cls()`, not
`Obj()`.

Whilst touching the parser make only these local correctness fixes:

- resolve negative indices from current list lengths, not private counters;
- reject OBJ index zero with `ObjParseFaceError`;
- turn missing or malformed vertex, normal and UV components into the
  appropriate `ObjParse*Error`;
- reject mixed corner formats in one face.

Run `calc_dimensions()` after a successful load. Do not add MTL support or
triangulation.

An OBJ with mixed coloured and uncoloured vertices may parse, but `validate()`
and `save()` must reject its incomplete colour data.

Move `Face`, `MeshData` and `MeshValidationError` into the top-level package
exports. Update tests to import `Face` from `ncca.ngl`. Correct
`TriangleVertNormal.obj` so it contains the normals referenced by its faces,
or turn it into a validation-failure fixture. Move save/reload output to
`tmp_path` and correct the existing truthy-list assertions.

Add parser tests for subclass `from_file()`, index zero, too-negative indices,
positive out-of-range indices at validation time, missing components, mixed
corner formats, append behaviour, programmatic negative indices and incomplete
colours.

Add an import-isolation test in a subprocess, as pytest collection imports
OpenGL itself:

```python
import ncca.ngl
import sys

assert "OpenGL.GL" not in sys.modules
```

Commit:

```text
refactor(obj): remove OpenGL backend coupling
```

### 3. Add `OpenGLMesh`

Add:

```text
src/ncca/ngl/opengl/mesh.py
tests/test_opengl_mesh.py
```

Export `OpenGLMesh` from `ncca.ngl.opengl`.

```python
class OpenGLMesh:
    def __init__(self, mesh: MeshData, *, texture_id: int = 0) -> None: ...

    @property
    def vao(self) -> AbstractVAO | None: ...

    def upload(self, *, force: bool = False) -> None: ...
    def draw(self) -> None: ...
    def cleanup(self) -> None: ...
```

`upload()` runs in a current GL context. It is idempotent unless
`force=True`. When forced, it deletes the previous VAO first. It requests
`mesh.triangle_vertex_data(flip_v=True)`, rejects empty data, creates a
`VAOType.SIMPLE` triangle VAO and sets the established layout:

```text
location 0: float3, offset 0
location 1: float3, offset 12
location 2: float2, offset 24
stride: 32 bytes
```

The draw count is `data.size // 8`. Call `mesh.calc_dimensions()` during
upload. `draw()` raises a clear error before upload; it binds a non-zero
borrowed texture id before drawing. `cleanup()` removes only the VAO.

Use `opengl_context` tests for upload, attributes, vertex counts, drawing,
pre-upload errors, repeated and forced upload, borrowed texture binding,
cleanup and empty mesh rejection.

Commit:

```text
feat(opengl): add mesh rendering adapter
```

### 4. Retain `BaseMesh` as a compatibility layer

Modify:

```text
src/ncca/ngl/opengl/base_mesh.py
tests/test_base_mesh.py
```

Make `BaseMesh` inherit `MeshData` and delegate GPU work to an internal
`OpenGLMesh(self)`. Preserve `vao`, `texture_id`, `texture`,
`create_vao()`, `draw()`, `_should_skip_vao_creation()` and
`_validate_triangular_mesh()`.

Keep the old `reset_vao` behaviour only here:

- with an existing VAO, `reset_vao=True` does nothing;
- with an existing VAO, `reset_vao=False` replaces it.

`BaseMesh.draw()` remains a no-op before upload for source compatibility.
Both `ncca.ngl.opengl.Face` and
`ncca.ngl.opengl.base_mesh.Face` must alias the new core `Face`.

Move pure geometry tests into `test_mesh.py`; leave compatibility and GL
delegation tests in `test_base_mesh.py`.

Commit:

```text
refactor(opengl): delegate BaseMesh rendering
```

### 5. Add `WebGPUMesh`

Add:

```text
src/ncca/ngl/webgpu/mesh.py
tests/test_webgpu_mesh.py
```

Export from `ncca.ngl.webgpu`:

```python
STANDARD_MESH_VERTEX_STRIDE = 32
STANDARD_MESH_TOPOLOGY = wgpu.PrimitiveTopology.triangle_list

def standard_mesh_vertex_layout() -> dict[str, object]: ...
```

The helper returns a fresh dictionary for one interleaved vertex buffer with
locations 0, 1 and 2 matching the OpenGL P/N/UV layout.

Add:

```python
class WebGPUMesh:
    def __init__(
        self,
        device: wgpu.GPUDevice,
        mesh: MeshData,
        *,
        flip_v: bool = False,
    ) -> None: ...

    @property
    def buffer(self) -> wgpu.GPUBuffer | None: ...

    @property
    def vertex_count(self) -> int: ...

    def upload(self, *, force: bool = False) -> None: ...
    def draw(
        self,
        render_pass: wgpu.GPURenderPassEncoder,
        *,
        slot: int = 0,
        instance_count: int = 1,
        first_instance: int = 0,
    ) -> None: ...
    def cleanup(self) -> None: ...
```

This is a static resource. `upload()` uses `wgpu.BufferUsage.VERTEX`, returns
unchanged unless forced, and destroys/recreates the old buffer when forced.
It rejects empty data. `draw()` checks that upload happened, binds the buffer
and issues the draw itself. Pipeline and bind-group setup remain external.
`cleanup()` destroys the buffer and is idempotent.

Do not change `PipelineFactory`; its existing triangle and custom pipelines
do not automatically support this interleaved P/N/UV layout.

Use fake devices and encoders for command tests, then add one real
`webgpu_device` buffer smoke test. Cover layout, usage, bytes, vertex count,
UV policy, repeat upload, forced replacement, draw ordering, custom slots,
instance settings, invalid draw and cleanup.

Commit:

```text
feat(webgpu): add mesh buffer adapter
```

### 6. Version and documentation

Modify:

```text
pyproject.toml
docs/docs/Geometry.md
docs/docs/opengl/geometry.md
docs/docs/webgpu/index.md
docs/mkdocs.yml
README.md, if it refers to the old OBJ API
```

Set the package version to `2.0.0`. Document parser-only OBJ usage, the
OpenGL adapter, the WebGPU layout helper and the 2.0 migration from
`obj_with_vao()`, `create_vao()` and `draw()`.

Correct documentation which claims `Obj("file.obj")` loads a file; use
`Obj.from_file()`.

Commit:

```text
docs: document backend-neutral OBJ meshes
```

## Part 2: PyNGLDemos

Update the committed dependency to `ncca-ngl>=2.0.0`. For local validation,
use the existing commented editable source entry temporarily, but do not
commit an absolute worktree path.

### 7. Migrate `GameKeyControl`

Modify:

```text
GameKeyControl/main.py
GameKeyControl/main_webgpu.py
GameKeyControl/README.md
```

Delete `GameKeyControl/ship_mesh.py` once nothing references it.

The OpenGL entry point parses the ship with `Obj.from_file()`, constructs an
`OpenGLMesh`, uploads it during `initializeGL()` and draws the adapter each
frame. Release the VAO whilst the context is current.

The WebGPU entry point constructs `WebGPUMesh`, uploads it during scene setup
and uses `standard_mesh_vertex_layout()` in its existing custom pipeline.
Replace the manual vertex-buffer bind and draw call with `self.ship.draw()`.
Release the buffer when the widget closes. Keep the shader, depth state, MSAA,
projection, input, recording and playback behaviour unchanged.

### 8. Migrate OpenGL OBJ demos

- `ObjViewer`: construct `Obj`, create its `Texture` separately, pass the
  borrowed texture id to `OpenGLMesh`, and track both resources when replacing
  a model.
- `MuJoCoNGL`: cache `OpenGLMesh` objects, not `Obj` objects. Collision-shape
  loading remains CPU-only.
- `MathNodeEditor`: retain CPU `Obj` data for the graph but maintain a
  separate `OpenGLMesh` for the preview. Clean up and rebuild it when the
  graph mesh changes.
- `ColourObj`: replace the `ColourObj(Obj)` inheritance with a demo-local
  renderer composed around `Obj`. It may keep its specialised eleven-float
  layout and shader. Do not add arbitrary layouts to PyNGL for this one demo.

### 9. Migrate CPU packing users

- `Obj2Numpy`: use `obj.triangle_vertex_data(flip_v=True)` and keep the flat
  output shape.
- `HDRIBaker`: use the shared packed data, retaining only its fit-to-view
  operation.
- `NormalMapping`: retain its tangent/binormal code; it is already a CPU
  consumer once renderer methods disappear.
- `MorphObj`, collision shapes and the Math Node Editor graph remain CPU-only
  users. Update imports only where required.

Search active demo code and documentation before completing the migration:

```bash
rg -n "obj_with_vao|Obj\\.create_vao|self\\._obj\\.draw" .
```

Commit:

```text
refactor(demos): use backend mesh adapters
```

## Verification

Run in PyNGL:

```bash
uv run pytest
uv run pytest -m opengl
uv run pytest -m webgpu
uv run ruff format src/ tests/
uv run ruff format --check src/ tests/
uv run ruff check src/ tests/
uv run pre-commit run --all-files
uv build
uv run --with mkdocs --with "mkdocstrings[python]" \
    mkdocs build --strict -f docs/mkdocs.yml
git diff --check
```

Also run:

```bash
PYTHONPATH=src uv run python -c \
'import sys; import ncca.ngl; assert "OpenGL.GL" not in sys.modules'
```

Run the PyNGLDemos test suite against the local library worktree. Smoke test
both `GameKeyControl` back ends, `ObjViewer`, `MuJoCoNGL`, `ColourObj`,
the Math Node Editor preview and HDRIBaker OBJ loading.

## Completion criteria

The work is complete when `Obj` imports without importing OpenGL; it holds no
GPU state or drawing methods; both back ends consume the same packed CPU data;
the standard layout is documented; `BaseMesh` remains source-compatible; all
active demos use the new API; both GameKeyControl versions draw the same ship;
and the CPU, OpenGL, WebGPU, documentation, lint and build checks pass.

After each repository change, export the agent session and save the required
`docs/agent-sessions/<date>-session.md` summary with the goal, files changed
and commands run.

