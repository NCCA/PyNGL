---
sources:
  - src/ncca/ngl/opengl/abstract_vao.py
  - src/ncca/ngl/opengl/simple_vao.py
  - src/ncca/ngl/opengl/simple_index_vao.py
  - src/ncca/ngl/opengl/multi_buffer_vao.py
  - src/ncca/ngl/opengl/vao_factory.py
  - src/ncca/ngl/opengl/primitives.py
  - src/ncca/ngl/opengl/base_mesh.py
  - src/ncca/ngl/opengl/__main__.py
  - src/ncca/ngl/opengl/pipeline_demo_shaders/**
synced: 4891d49afd4ef2329ac7b95298f1677fd2b3a5ef
---

# The VAO Stack

## Summary

This is PyNGL's OpenGL vertex-buffer layer: a small abstraction over Vertex
Array Objects so that geometry code (primitives, loaded meshes) doesn't
call `OpenGL.GL` buffer functions directly. `abstract_vao.py` defines the
contract, three concrete classes implement different buffer layouts, and
`vao_factory.py` provides a registry so callers ask for a VAO by type name
without importing the concrete class. `primitives.py` and `base_mesh.py`
are the two consumers that turn raw vertex data into drawable VAOs.

## How it works

`AbstractVAO` (`src/ncca/ngl/opengl/abstract_vao.py:34`) owns the id,
draw mode, and `bound`/`allocated`/`indices_count` state common to every
implementation; it also supplies `set_vertex_attribute_pointer`,
`bind`/`unbind`, and context-manager `__enter__`/`__exit__` so a VAO can be
used in a `with` block. Subclasses must implement `draw`, `set_data`,
`remove_vao`, `get_buffer_id`, and `map_buffer`. `VertexData`
(`abstract_vao.py:13`) is a thin wrapper: converts input to an
`np.float32` array, stores `size` and a GL usage-hint `mode`.

Three concrete implementations:

- `SimpleVAO` (`simple_vao.py`) — one buffer, `glDrawArrays`. Used for
  non-indexed triangle/line data, e.g. `_primitive` in `primitives.py` and
  `BaseMesh.create_vao`.
- `SimpleIndexVAO` (`simple_index_vao.py`) — a vertex buffer plus an index
  buffer, `glDrawElements`. Takes `IndexVertexData`, which extends
  `VertexData` with an `indices` array and a GL index type (uint8/16/32
  mapped to numpy dtypes). Used where indexed geometry is needed.
- `MultiBufferVAO` (`multi_buffer_vao.py`) — a list of buffers (`vbo_ids`),
  each set independently via `set_data(data, index)`; buffers are created
  lazily/appended as needed. Buffer 0 is assumed to define
  `indices_count`. Used when attributes (position, colour, normal, ...)
  live in separate VBOs rather than one interleaved buffer.

`VAOFactory` (`vao_factory.py:15`) is a static registry:
`_creators` maps a `VAOType` enum value (or any hashable key) to a
constructor callable. `register_vao_creator(name, creator_func)` adds an
entry; `create_vao(name, mode)` looks it up and instantiates it, raising
`ValueError` if unregistered. The module pre-registers `SIMPLE`,
`MULTI_BUFFER`, `SIMPLE_INDEX` at import time. A new VAO type is added by
writing a class that implements `AbstractVAO` and calling
`VAOFactory.register_vao_creator` with a new `VAOType` member — no call
site that already does `VAOFactory.create_vao(VAOType.X, mode)` needs to
change.

`Primitives` (`primitives.py:54`) is a static/class-level registry
(`_primitives: dict[str, _primitive]`) of named drawable shapes.
`_primitive.__init__` asks `VAOFactory` for a `SIMPLE` VAO, binds it via
`with self.vao:`, uploads a `VertexData` built from a `PrimData`/`Prims`
numpy array, and configures attribute pointers 0 (position), 1 (normal),
2 (uv) — unless `floats_per_vertex == 3`, meaning line-only data (e.g.
`Prims.LINE_GRID`, drawn `GL_LINES`), which skips normal/uv pointers.
`Primitives.create` maps a `Prims` enum member to a `PrimData` generator
method and the right `(draw_mode, floats_per_vertex)` pair before
building the `_primitive`. `load_default_primitives` builds every `Prims`
member once (guarded by `_loaded`), swallowing per-primitive exceptions.
`Primitives.draw(name)` looks the primitive up by string or `Prims`
value, re-binds its VAO in a `with` block, and calls `draw()`.

`BaseMesh` (`base_mesh.py:25`) is the base class for loadable/generated
mesh geometry (subclassed by `Obj`, for instance). It stores raw
`vertex`/`normals`/`uv` lists and `faces` (list of `Face`, each holding
parallel index lists for vertex/uv/normal). `create_vao` only supports
triangular meshes (`is_triangular` checks every face has 3 vertices;
`_validate_triangular_mesh` raises `RuntimeError` otherwise); it flattens
faces into interleaved `(x,y,z,nx,ny,nz,u,v)` `VertData` records (V is
flipped for OpenGL), concatenates them into one float32 array, requests a
`SIMPLE` VAO from `VAOFactory`, uploads it, and sets three attribute
pointers matching that 8-float layout. `_should_skip_vao_creation` makes
a second `create_vao()` call a no-op unless `reset_vao=True`. After
building the VAO, `calc_dimensions` computes min/max extents and
`BBox.from_extents` builds `self.bbox`. `draw()` binds the mesh's texture
(if `texture_id` is set) then draws the VAO inside a `with` block.

`src/ncca/ngl/opengl/__main__.py` is a runnable pipeline-tour demo
(`uv run python -m ncca.ngl.opengl`, mirroring the WebGPU one): it cycles
through small scenes exercising `SimpleVAO`, `SimpleIndexVAO`,
`MultiBufferVAO`, and the `Primitives` registry, using the per-vertex
colour GLSL pair in `src/ncca/ngl/opengl/pipeline_demo_shaders/`.

## Key invariants

- Every VAO must be bound (`with vao:` or `bind()`) before `set_data`,
  `set_vertex_attribute_pointer`, or `draw` — `draw()` on an unbound or
  unallocated VAO logs an error and does nothing rather than raising.
- `set_data` must be called with the matching data type: `SimpleVAO`/
  `MultiBufferVAO` require `VertexData`; `SimpleIndexVAO` requires
  `IndexVertexData`. Passing the wrong type raises `TypeError`.
- `MultiBufferVAO` assumes buffer index 0 determines `indices_count` —
  always upload the primary attribute buffer first (or explicitly at
  index 0).
- New VAO types integrate by implementing `AbstractVAO`'s five abstract
  methods and registering via `VAOFactory.register_vao_creator`; never
  hardcode a concrete VAO class at a call site that should stay
  type-agnostic.
- `BaseMesh.create_vao` refuses non-triangular meshes (`RuntimeError`);
  quad/n-gon faces must be triangulated before VAO creation.
- `Primitives`/`_primitive` state is class-level (shared across all
  callers) — there is one global namespace of primitive names, and
  `load_default_primitives` only populates it once per process.

## Connections

- [geometry.md](geometry.md) — `PrimData`/`Prims` (the generators `Primitives.create` wraps) and `Obj`, the main `BaseMesh` subclass loading real files.
- [shaders.md](shaders.md) — attribute locations set here (0/1/2) must match shader `layout` bindings.
- [../howto/add-a-vao-type.md](../howto/add-a-vao-type.md) — step-by-step guide to adding a new VAO implementation.
