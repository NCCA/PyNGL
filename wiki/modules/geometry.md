---
sources:
  - src/ncca/ngl/prim_data.py
  - src/ncca/ngl/obj.py
  - src/ncca/ngl/bezier_curve.py
  - src/ncca/ngl/plane.py
  - src/ncca/ngl/bbox.py
  - src/ncca/ngl/base_mesh.pyi
  - src/ncca/ngl/PrimData/**
synced: 4891d49afd4ef2329ac7b95298f1677fd2b3a5ef
---

# Geometry and Mesh Data

## Summary

This is the API-agnostic geometry layer: it produces or represents vertex
data and shapes without ever touching OpenGL/WebGPU. `prim_data.py`
generates raw numpy vertex buffers for built-in primitive shapes (spheres,
cones, tori, etc.), `obj.py` parses/writes Wavefront OBJ files into an
indexed mesh, `bezier_curve.py` evaluates B-spline/Bezier curves, and
`plane.py`/`bbox.py` are small analytic shape helpers (signed-distance
plane, axis-aligned box). Only `obj.py` reaches outside this module,
importing mesh/texture types from the OpenGL sub-package.

## How it works

`prim_data.py:Prims` is an enum of primitive names; `PrimData` is a
collection of `@staticmethod` generators (`sphere`, `torus`, `cone`,
`cylinder`, `capsule`, `disk`, `line_grid`, `triangle_plane`), each
returning a flat `np.float32` array of interleaved vertex data —
`x,y,z,nx,ny,nz,u,v` (8 floats/vertex) for surface primitives, `x,y,z`
(3 floats/vertex) only for `line_grid`. Data is unindexed triangle-list
form (each triangle's 3 verts written out in full, no shared-index
buffer). `PrimData.primitive(name)` is a separate path: it loads
pre-baked complex meshes (bunny, dragon, teapot, buddha, troll, ...) from
`PrimData/Primitives.npz` by key, raising `ValueError` for an unknown
name. The `src/ncca/ngl/PrimData/` directory holds those baked assets:
the individual `.npy` mesh files, the packed `Primitives.npz`, and
`pack_arrays.py`, the small script that rebuilds the `.npz` from the
`.npy` files. `src/ncca/ngl/base_mesh.pyi` is a top-level type stub for
the `Face`/`BaseMesh` types that `obj.py` uses from `ncca.ngl.opengl`. `_circle_table` is a shared helper producing cos/sin lookup tables
used by the circular-cross-section generators (cone, cylinder, capsule).
`ncca.ngl.opengl.primitives.Primitives` (a different, OpenGL-coupled
class) is the consumer: `Primitives.create()` calls the matching
`PrimData` static method, wraps the returned array in a `_primitive`
holding a `VAOFactory`-built VAO, and stores it by name in a class-level
dict for later `draw()`. `floats_per_vertex` (3 or 8) there must match
what the specific `PrimData` generator emitted.

`obj.py:Obj` subclasses `ncca.ngl.opengl.base_mesh.BaseMesh` and imports
`Face` and `Texture` from `ncca.ngl.opengl` — this is the one geometry
module with an OpenGL dependency baked into its class hierarchy, despite
living in the "API-agnostic" top-level package. `Obj.load()` reads an OBJ
file line by line, dispatching `v`/`vn`/`vt`/`f` tokens to
`_parse_vertex`/`_parse_normal`/`_parse_uv`/`_parse_face`. Vertices,
normals and UVs are stored as `Vec3` lists (UV `z` defaults to 0 for
2-component `vt` lines; an optional non-standard 4th/5th/6th token on `v`
lines is treated as per-vertex colour). `_parse_face` sniffs the token
format (`v`, `v/vt`, `v//vn`, `v/vt/vn`) from the first face token and
dispatches to one of four private parsers, each building a `Face` from
`base_mesh.py`. OBJ indices are 1-based and may be negative (relative to
the count so far); all four face parsers convert to 0-based absolute
indices using the running `_current_vertex_offset` /
`_current_normal_offset` / `_current_uv_offset` counters, which only
`_parse_vertex`/`_parse_normal`/`_parse_uv` increment. `BaseMesh.create_vao()`
(in `opengl/base_mesh.py`) is what actually de-indexes faces back into a
flat interleaved `x,y,z,nx,ny,nz,u,v` buffer for the GPU, flipping V
(`1 - v`) for OpenGL's texture-origin convention, and requires the mesh
be all-triangle (`is_triangular()`) or it raises `RuntimeError`.
`Obj.save()` writes vertices/UVs/normals/faces back out in the same `f
v/vt/vn` style, re-adding 1 to indices.

`bezier_curve.py:BezierCurve` stores control points (`Vec3` list) and a
knot vector; `create_knots()` auto-generates a clamped, degree-matched
knot vector (`0.0` for the first half, `1.0` for the second) whenever
points are added and no explicit knots were supplied. `get_point_on_curve`
evaluates the curve at parameter `u` via recursive Cox-de Boor
(`cox_de_boor`), skipping basis-function contributions below `0.001` as
an optimisation, not a correctness rule.

`plane.py:Plane` stores a unit `normal`, a `point` on the plane, and the
implicit-form constant `d` (`normal . p + d = 0`); `set_points`,
`set_normal_point`, and `set_floats` are three equivalent ways to define
the same plane, and `distance(p)` returns the signed distance.

`bbox.py:BBox` stores centre/width/height/depth plus derived min/max
extents, 8 corner `Vec3` vertices, and 6 face-normal `Vec3`s. It has two
equivalent construction/recompute paths — `recalculate_from_center_dims()`
(driven by the `center`/`width`/`height`/`depth` property setters) and
`recalculate_from_extents()` (driven by `set_extents()` /
`BBox.from_extents()`) — both funnel into `_update_verts_and_normals()`
so the two representations never drift apart. `base_mesh.py:BaseMesh.create_vao()`
constructs a mesh's `bbox` via `BBox.from_extents()` after computing
`min_x`..`max_z` in `calc_dimensions()`.

## Key invariants

- `PrimData` generators always return `np.float32` arrays; surface
  generators interleave 8 floats/vertex (`x,y,z,nx,ny,nz,u,v`) in
  triangle-list order — changing the field count or order breaks every
  `Primitives._primitive` vertex-attribute-pointer offset that assumes it.
- `PrimData.primitive()` reads keys straight from `PrimData/Primitives.npz`;
  `Prims` enum values must stay in sync with the `.npz` key names.
- OBJ face-token format detection in `Obj._parse_face` inspects only the
  *first* face token per line — an OBJ line mixing formats across
  vertices is not supported and must not be assumed to work.
- The three offset counters (`_current_vertex_offset`, `_current_normal_offset`,
  `_current_uv_offset`) exist solely to resolve OBJ's negative
  (relative) indices; they must be incremented exactly once per
  `v`/`vn`/`vt` line and never touched by face parsing.
- All OBJ parse errors raise the matching `ObjParse*Error` (`Vertex`,
  `Normal`, `UV`, `Face`) rather than propagating the underlying
  `ValueError` — preserve this when editing parsers.
- `Obj` is the only top-level `ncca.ngl` geometry module allowed to
  import from `ncca.ngl.opengl` (`BaseMesh`, `Face`, `Texture`); do not
  add similar imports to `prim_data.py`, `bezier_curve.py`, `plane.py`,
  or `bbox.py` without revisiting the "API-agnostic top-level package"
  architecture rule in CLAUDE.md.
- `BaseMesh.create_vao()` only supports triangular meshes; it raises
  `RuntimeError` otherwise, and flips UV `v` (`1 - v`) for OpenGL — any
  new consumer of `Obj` data must account for that flip already being
  baked into the VAO, not the parsed `Obj.uv` list.
- `BBox`'s two recompute paths (`recalculate_from_center_dims` /
  `recalculate_from_extents`) must always leave both the
  centre/dimensions fields and the min/max extents fields consistent —
  never update one without the other.
- `Plane.normal` is always normalized by every setter (`set_points`,
  `set_normal_point`, `set_floats`); `d` is always recomputed alongside it.
- `BezierCurve.create_knots()` regenerates the whole knot vector on every
  `add_point()` call unless knots were explicitly supplied at
  construction — mixing manual `add_knot()` calls with further
  `add_point()` calls will silently discard the manual knots.

## Connections

- [vao-stack.md](vao-stack.md) — `VAOFactory`/`AbstractVAO` that `Primitives`
  and `BaseMesh.create_vao()` build on, and `BaseMesh`/`Face` themselves.
- [math.md](math.md) — `Vec3` used throughout as the point/vector type.
- [../howto/add-a-primitive.md](../howto/add-a-primitive.md) — step-by-step
  guide to adding a new primitive shape.
