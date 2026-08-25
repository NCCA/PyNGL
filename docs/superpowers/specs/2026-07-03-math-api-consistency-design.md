# Math API Consistency — Design

**Date:** 2026-07-03
**Status:** Approved
**Scope:** `Vec2/3/4`, `Mat2/3/4`, `Quaternion`, plus direct dependents (`Vec2/3/4Array`, `Transform`, `util.py`); mechanical call-site fixes elsewhere.

## Goal

Give every math type in `ncca.ngl` one uniform, Python-first API. Today the
vectors share a solid `VectorBase`, but the matrices have no shared base and
diverge badly (`Mat2` lacks `transpose`, `inverse`, `determinant`, arithmetic,
indexing; `Mat3`/`Mat4` duplicate near-identical code), `Quaternion` is its own
island, and mutation semantics are mixed (`transpose()` mutates,
`get_transpose()` copies, `normalize()` returns a value, `clamp()` mutates
silently).

## Decisions (agreed with maintainer)

1. **Breaking changes are fine.** No deprecation shims; old names are removed
   and all in-repo callers are fixed in the same change series.
2. **Immutable-style API.** Every operation returns a new object. The only
   mutation is `set(*args)` and component/element assignment
   (`v.x = 2`, `m[1][2] = 0.5`).
3. **Numpy-backed everywhere.** Each class stores a single private
   `np.float32` ndarray.
4. **Architecture:** keep `VectorBase` (rewritten), add a parallel
   `MatrixBase`; `Quaternion` stays standalone but conforms to the same
   contract, enforced by a conformance test suite.

## 1. The common contract (all seven classes)

- **Storage:** private `_data` ndarray, dtype `np.float32`; shape `(n,)` for
  vectors and quaternion, `(n, n)` for matrices. `__slots__ = ("_data",)`.
- **Construction:** `Cls()` gives the sensible default (zero vector, identity
  matrix, identity quaternion); `Cls(a, b, …)` takes components. Classmethods
  `from_list(lst)` and `from_numpy(arr)` on every class. Matrix factory
  classmethods stay: `identity()`, `zero()`, `scale(…)`, `rotate_x/y/z(…)`,
  `translate(…)` (Mat4 only), `from_mat4`/`from_mat3` conversions.
- **Export:** `to_numpy()` (returns a copy), `to_list()`, `to_tuple()`,
  `copy()`. `get_matrix()` and `get_array()` are **deleted** — `to_numpy()` is
  the one way out.
- **Immutability naming:** past-participle methods return new objects:
  `normalized()`, `transposed()`, `reflected(n)`, `clamped(low, high)`.
  Nouns that already read as products return new objects too: `inverse()`,
  `conjugate()`, `determinant()`. The mutating forms (`normalize()`,
  `transpose()`, in-place `clamp()`, `null()`) are **deleted**.
- **Dunders on every class:** `__eq__` (float tolerance, as now), `__ne__`,
  `__hash__`, `__repr__` (eval-able, e.g. `Vec3(1.0, 2.0, 3.0)`), `__str__`
  (pretty), `__getitem__`, `__iter__`, `__len__`, `__neg__`,
  `__add__`/`__sub__`, scalar `__mul__`/`__rmul__`/`__truediv__`.
  `__matmul__` carries the linear-algebra products: mat @ mat, mat @ vec,
  vec @ mat, quat @ quat. Explicit `__iadd__`/`__isub__` are dropped —
  Python's default `a += b` → `a = a + b` gives correct immutable behaviour.
- **Typing/docs:** full type hints, Google-style docstrings, module errors as
  `<Module>Error` `Exception` subclasses.

## 2. `VectorBase` (rewrite in place, same role)

`Vec2/3/4` inherit. Numpy-backed; `x/y/z/w` properties index into `_data`.

- Keeps: `dot`, `length`, `length_squared`, `inner`, `outer`,
  `cross` (Vec2 → float, Vec3/Vec4 → vector), `sizeof`, `set`.
- Renames: `normalize()` → `normalized()`, `reflect()` → `reflected()`,
  `clamp()` → `clamped()` (returns new).
- Deletes: `null()` (use `v.set(0, 0, 0)` or a fresh `Vec3()`).
- Adds: `lerp(rhs, t)` returning a new vector.

## 3. New `MatrixBase` (`mat_base.py`)

`Mat2/3/4` inherit. Subclasses define only their size and their own factories
(`rotate_*`, `scale`, `translate`, `from_mat4`/`from_mat3`).

Shared in the base: all arithmetic dunders, `transposed()`, `inverse()`,
`determinant()`, `identity()`, `zero()`, `from_list()`, `from_numpy()`,
row indexing (`__getitem__`/`__setitem__`), `__eq__`/`__ne__`/`__hash__`,
`__repr__`/`__str__`, `copy()`, exports.

This closes every `Mat2` gap automatically. `Mat2Error`, `Mat2NotSquare`,
`Mat3Error`, `Mat3NotSquare`, `Mat4Error`, `Mat4NotSquare` collapse into a
single `MatrixError` raised from the base.

## 4. `Quaternion`

Standalone class (not a `VectorBase`) conforming to the contract:

- Numpy-backed `(4,)` `_data`; `s/x/y/z` properties.
- Gains: `copy()`, `to_tuple()`, `from_numpy()`, `__eq__`/`__ne__`/`__hash__`,
  `set()`, eval-able `__repr__`.
- `from_mat4` / `from_axis_angle` become `@classmethod` (matching matrix
  factories).
- `normalize()` → `normalized()`; `conjugate()` already returns new — keeps
  its name.
- Adds: `inverse()`, `slerp(rhs, t)` (instance method, matching `Vec.lerp`),
  `to_mat4()`.
- Quaternion product moves to `__matmul__`; scalar multiply stays on `*`;
  `q * vec3` rotation stays as is.

## 5. Direct dependents

- **`Transform`:** `get_matrix()` → `matrix()` (still computed lazily).
  Setters remain — it is a stateful builder, explicitly exempt from the
  immutable rule. Internals updated to the new `Mat4` API.
- **`Vec2/3/4Array`:** `get_array()` deleted (`to_numpy()` stays); gains
  `to_tuple()`. No `__hash__` — mutable container, intentionally excluded
  (documented in the class docstring). Internal storage is one contiguous
  `(n, size)` float32 array.
- **`util.py`:** `look_at`, `perspective`, `ortho`, `frustum`, `calc_normal`,
  `lerp` updated to the new API and fully type-hinted; `lerp` is generic over
  anything supporting `+` and scalar `*`.
- **`Plane`, `BBox`, shader/widget/prim/mesh code:** mechanical call-site
  fixes only; no convention changes.

## 6. Enforcement & testing

New `tests/test_api_consistency.py`, parametrised over all seven classes,
asserting the shared contract:

- constructor forms (default + component args),
- `copy`/`to_numpy`/`to_list`/`to_tuple`/`from_list`/`from_numpy` round-trips,
- hashability and `eval(repr(x)) == x`,
- immutability (e.g. `v.normalized()` leaves `v` untouched),
- internal dtype is `np.float32`.

Existing per-class tests are updated to the new names. Definition of done:
full default suite, `-m opengl`, and `-m qt` suites pass; `ruff format` and
`ruff check` clean.

## 7. Migration

Single breaking change series, no shims. `CLAUDE.md`'s "API consistency
conventions" section is updated to state this contract so future code follows
it.
