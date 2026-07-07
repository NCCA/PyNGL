---
sources:
  - src/ncca/ngl/vec*.py
  - src/ncca/ngl/mat*.py
  - src/ncca/ngl/quaternion.py
  - src/ncca/ngl/transform.py
  - src/ncca/ngl/util.py
synced: 9c2b6deffde456bb528df654ca6ce5e810d8f3a8
---

# Math

## Summary

The math family (`src/ncca/ngl/vec2.py`/`vec3.py`/`vec4.py`, their `*_array.py`
containers, `mat2.py`/`mat3.py`/`mat4.py`, `quaternion.py`, `transform.py`, and
`util.py`) is the numeric foundation everything else in PyNGL builds on:
positions, directions, colours, transforms, cameras and projection all pass
through these types. It is deliberately dependency-light (numpy only) and
follows one shared contract so that agents can predict behaviour for any
class in the family without reading every file.

## How it works

`vec2.py`/`vec3.py`/`vec4.py` are thin subclasses of the generic
`vector_base.py:VectorBase` (a `Generic[T]` ABC): the base implements
`__add__`/`__sub__`/`__mul__` (scalar only)/`__truediv__`/`dot`/`length`/
`normalized`/`clamped`/`lerp`/`from_list`/`from_numpy`/`copy`/`to_list`/
`to_numpy`/`to_tuple`/`__eq__`/`__hash__`/`__repr__` once for all dimensions;
each concrete `VecN` only supplies `DIMENSION`, `COMPONENT_NAMES`,
`DEFAULT_VALUES`, and the dimension-specific `cross`, `reflected`, `outer`
and `__matmul__`. `Vec2.cross` returns a scalar (perpendicular dot product);
`Vec3.cross` returns a `Vec3`; `Vec4.cross` cross-products only the first
three components and zeroes `w`. `outer()` builds the next-size-up matrix
(`Vec2.outer` -> `Mat2`, `Vec3.outer` -> `Mat3`). `VecN.__matmul__` multiplies
the vector by the same-size matrix (`vec3.py:Vec3.__matmul__` does
`rhs._data.T @ self._data`). Component access (`.x`, `.y`, ...) is generated
by `vector_base.py:_create_properties`, and `__setattr__` on `VectorBase`
rejects any attribute name outside `COMPONENT_NAMES`/`_data`.

`vec2_array.py`/`vec3_array.py`/`vec4_array.py` are separate, non-inheriting
container classes (`Vec3Array` etc.) that hold many `VecN` values as one
contiguous `(N, DIM)` numpy array rather than a Python list of objects —
built for bulk GPU upload (`to_numpy()` returns a flattened float32 copy;
`sizeof()` reports total bytes). They behave like a mutable
`list[VecN]`: `__getitem__`/`__setitem__`/`__len__`/`__iter__`/`append`/
`extend`, materialising/copying individual `VecN` objects on read and
writing back into the shared array on write. Unlike the `VecN` types they
are intentionally unhashable (mutable container semantics), and slicing
returns a new array copy rather than a view.

`mat2.py`/`mat3.py`/`mat4.py` subclass `mat_base.py:MatrixBase`, which stores
a `(SIZE, SIZE)` numpy array and implements the shared matrix API:
`identity`/`zero`/`from_list`/`from_numpy`, `transposed`/`determinant`/
`inverse` (raises `MatrixError` if singular), scalar `__mul__`/`__truediv__`,
`__add__`/`__sub__`, and `__matmul__`. Matrix `@` is row-vector convention:
`M1 @ M2` computes `M2._data @ M1._data` internally (apply `M1` first, then
`M2`, matching how `transform.py` composes rotations); `M @ v` (where `v` is
the matrix's `_vec_type()`, e.g. `Vec4` for `Mat4`) returns a new vector.
Row access/mutation is via `m[i]` (returns/accepts the numpy row directly —
this is the one exception to "operations return new objects", alongside
`set()`). `Mat4` adds `scale`/`translate`/`rotate_x`/`rotate_y`/`rotate_z`
classmethods (degrees in) and `from_mat3` (embeds a `Mat3` as the
upper-left 3x3 block, leaving row/col 3 as identity).

`quaternion.py:Quaternion` does not inherit `VectorBase` (it has 4 named
components `s, x, y, z` but different operator semantics) and stores
`_data = [s, x, y, z]`. `@` is the Hamilton product (`Quaternion @
Quaternion`); `*` is overloaded — `Quaternion * float` scales, but
`Quaternion * Vec3` rotates the vector (`qvq*`) and returns a `Vec3`, not a
`Quaternion`. `Quaternion.from_mat4()` extracts a quaternion from a
`Mat4`'s rotation part (branches on the trace, standard robust conversion);
`to_mat4()` is the inverse, building a `Mat4` from `s, x, y, z`. `slerp`
handles the antipodal and near-parallel (linear-interpolation fallback)
cases explicitly.

`transform.py:Transform` composes `position`/`rotation`/`scale` (each a
`Vec3`; rotation in degrees) into a single `Mat4` via `matrix()`, which is
lazily recomputed only when `need_recalc` is set (by any `set_position`/
`set_rotation`/`set_scale`/`set_order`). The rotation order is a string key
(`"xyz"`, `"zyx"`, ...) into `Transform.rot_order`, mapped to an `eval()`'d
expression of `rx`/`ry`/`rz` matrix `@` composition, then combined with the
scale matrix and stamped with the translation into row 3. `set_order`
raises `TransformRotationOrder` for an unrecognised key.

`util.py` holds free functions rather than a class: `clamp` (raises
`ValueError` if `low >= high`), `look_at`/`renderman_look_at` (build camera
view `Mat4`s from eye/look/up `Vec3`s, the latter for RenderMan's Y-down
convention), `perspective`/`ortho`/`frustum` (build projection `Mat4`s,
each takes a `PerspMode` enum — `OpenGL`, `WebGPU`, `Vulkan` — to pick the
right clip-space Z convention), `lerp` (generic — works on anything
supporting `+` and scalar `*`, so floats, `VecN`, `Quaternion` and matrices
all work through the same function), `calc_normal` (triangle normal via
cross product), and `hash_combine` (the shared seed-combining routine used
by every math class's `__hash__`).

## Key invariants

- Every class's numeric storage is `_data`, always `np.float32`.
- Mutation is limited to `set()` and element/row assignment
  (`v.x = ...`, `m[i][j] = ...`, `m[i] = [...]`); every other operation
  (`normalized`, `transposed`, `inverse`, `clamped`, arithmetic operators)
  returns a new object.
- `@` is always the linear-algebra product (vector-matrix, matrix-matrix,
  quaternion Hamilton product); `*` is scalar-only **except**
  `Quaternion * Vec3`, which rotates the vector — this exception is
  deliberate and tested, not a bug.
- `VectorBase.__setattr__` rejects setting any attribute not in
  `COMPONENT_NAMES` — do not add new instance attributes to `VecN`
  subclasses without updating `COMPONENT_NAMES`/`__slots__`.
- `Vec*Array` containers are intentionally unhashable and mutable; do not
  add `__hash__` to them.
- `Mat4` row/column layout and the `M1 @ M2 -> M2 @ M1` data-reversal in
  `mat_base.py:MatrixBase.__matmul__` implement the row-vector convention
  consistently — `transform.py`'s rotation-order composition and
  `util.py`'s `look_at`/`perspective`/`ortho`/`frustum` all depend on it.
- `tests/test_api_consistency.py` enforces the shared contract
  (constructors, `from_list`/`from_numpy`, `copy`/`to_*`, `__eq__`/`__hash__`,
  `__repr__`) across `Vec2/3/4`, `Mat2/3/4` and `Quaternion` — run it when
  touching any file in this family.

## Connections

- [geometry.md](geometry.md) — `prim_data.py`/`obj.py` consume `Vec3`/`Vec3Array` for vertex data.
- [shaders.md](shaders.md) / [webgpu.md](webgpu.md) — shader/pipeline uniform setters take `Mat4`/`Vec3`/`Vec4` directly.
- [widgets.md](widgets.md) — `first_person_camera.py` builds view/projection matrices via `util.py`; the Qt widgets edit `Vec2/3/4`/`Mat4`/`Transform` values.
- [../architecture/api-conventions.md](../architecture/api-conventions.md) — the shared math-class contract this page documents in detail.
