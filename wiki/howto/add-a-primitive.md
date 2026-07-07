---
sources:
  - src/ncca/ngl/prim_data.py
  - src/ncca/ngl/opengl/primitives.py
synced: 9c2b6deffde456bb528df654ca6ce5e810d8f3a8
---

# Add a Primitive

## Summary

A task guide for adding a new built-in generated shape (like `sphere` or
`cylinder`) to PyNGL. Two files must change together: `prim_data.py`,
which is the API-agnostic generator producing raw vertex numpy data, and
`opengl/primitives.py`, which wraps that data in a VAO and makes it
drawable via `Primitives.create`/`Primitives.draw`.

## How it works

1. **Add the enum member.** `prim_data.py:Prims` is the canonical name
   list for built-in primitives. Add a new member whose `.value` is the
   lower-case name you'll register elsewhere (e.g. `PYRAMID = "pyramid"`).

2. **Write the generator.** Add a `@staticmethod` to `PrimData` following
   the existing shapes (`sphere`, `cone`, `cylinder`, `torus`, `disk`,
   `capsule`). Build vertex data in a Python list, then convert once at
   the end with `np.array(data, dtype=np.float32)` — every other
   generator does this. Validate inputs the same way the others do
   (`RAD_POS`/`NON_NEG` `ValueError`s for bad radius/height, clamping low
   precision/slice counts up rather than raising).

3. **Match the data-format contract.** This is the invariant the whole
   pipeline depends on: surface shapes interleave 8 floats per vertex —
   `x,y,z,nx,ny,nz,u,v` — as unindexed triangle-list data (three full
   vertices per triangle, no shared-index buffer). Line-only shapes (like
   `line_grid`) use 3 floats per vertex (`x,y,z`) with no normal/uv. Pick
   one of these two layouts; there is no third option currently supported
   by `Primitives`.

4. **Reuse `_circle_table`** if the shape has a circular cross-section
   (cone, cylinder, capsule all do) — it returns a `(n+1, 2)` cos/sin
   lookup table with the first sample duplicated at the end, avoiding
   repeated trig calls per vertex.

5. **Register the generator with `Primitives.create`.** In
   `opengl/primitives.py:Primitives.create`, add your `Prims` member to
   the `prim_methods` dict, mapping it to your new `PrimData` static
   method. If your shape is line-only (3 floats/vertex), also add an
   entry to `prim_layouts` mapping it to `(gl.GL_LINES, 3)` — everything
   absent from `prim_layouts` defaults to `(gl.GL_TRIANGLES, 8)`, which is
   correct for the common surface-shape case and needs no change.

6. **`_primitive.__init__` does the wiring**: it asks `VAOFactory` for a
   `SIMPLE` VAO, uploads your array as `VertexData`, and sets attribute
   pointers 0 (position, always 3 floats), and — only when
   `floats_per_vertex == 8` — pointer 1 (normal) and pointer 2 (uv). The
   vertex stride passed to `set_vertex_attribute_pointer` is
   `floats_per_vertex * 4` bytes; this is derived from the value you put
   in `prim_layouts`, so an inconsistent entry there silently corrupts
   every attribute offset rather than raising.

7. **Baked/complex meshes are a separate path.** If instead you're adding
   a pre-baked mesh (like `bunny` or `teapot`), you don't write a
   generator — you add data to `PrimData/Primitives.npz` under a key
   matching your `Prims.value`, and `PrimData.primitive(name)` will load
   it; `Primitives.load_default_primitives()` iterates all `Prims`
   members through this path and silently skips any whose key is
   missing from the `.npz`.

## Testing

`prim_data.py` has no OpenGL import, so a new generator is exercised by
the default CPU test suite (`uv run pytest`) — assert on the returned
array's shape, dtype (`np.float32`), and that it's a multiple of
`floats_per_vertex`. Anything that constructs the VAO and actually draws
— `Primitives.create`/`Primitives.draw`, attribute pointer wiring —
requires a real OpenGL context and is deselected by default; run it with
`uv run pytest -m opengl`.

## Key invariants

- Every `PrimData` generator returns a flat `np.float32` array; surface
  shapes are 8 floats/vertex (`x,y,z,nx,ny,nz,u,v`), line shapes are 3
  (`x,y,z`) — there is no other layout `Primitives` understands.
- Data is unindexed triangle-list form: each triangle contributes 3 full
  vertices, not indices into a shared vertex pool.
- `prim_layouts` in `Primitives.create` and the generator's actual output
  must agree on `floats_per_vertex`; this value directly drives the byte
  stride and offsets used to configure attribute pointers 0/1/2.
- A `Prims` enum member added for a pre-baked mesh must have a `.value`
  matching a key already present in `PrimData/Primitives.npz`, or
  `PrimData.primitive()` raises `ValueError` (silently skipped by
  `load_default_primitives`, but not by direct calls).

## Connections

- [../modules/geometry.md](../modules/geometry.md) — full narrative of
  `prim_data.py` alongside the rest of the geometry layer.
- [../modules/vao-stack.md](../modules/vao-stack.md) — how `Primitives`
  fits into the wider VAO abstraction (`VAOFactory`, `SimpleVAO`).
