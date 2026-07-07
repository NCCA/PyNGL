---
sources:
  - tests/test_api_consistency.py
  - CLAUDE.md
synced: 9c2b6deffde456bb528df654ca6ce5e810d8f3a8
---

# API Conventions

## Summary

PyNGL's math classes (`Vec2`/`Vec3`/`Vec4`, `Mat2`/`Mat3`/`Mat4`, `Quaternion`)
all implement one shared contract, so that any function written against one
class's shape works the same way against the others. This page documents that
contract, the conformance suite that enforces it, and the project-wide coding
conventions (naming, docstrings, spelling) that apply beyond the math classes.

## How it works

Every math class stores its components as a numpy `np.float32` array in
`self._data`. Construction is by component with a sensible zero/identity
default (`cls()` must always succeed), plus two classmethod round-trips:
`from_numpy` and `from_list`, which are the inverse of `to_numpy`/`to_list`.
`to_numpy()` returns a defensive copy — mutating the returned array must never
affect the original object. `to_tuple()` returns a plain `tuple[float, ...]`.
Every instance is hashable and supports `==`; `hash(a) == hash(a.copy())` and
a copied instance is a distinct object with its own `_data` buffer
(`a.copy() is not a` and the underlying arrays differ).

Operations that read as producing a "new state" — `normalized()`,
`transposed()`, `inverse()`, `clamped()`, `conjugate()` on `Quaternion` — are
pure: they return a new object and leave `self` untouched. The only ways to
mutate an existing instance are `set()` and element assignment
(`a[0] = ...`). `-a` and `a / scalar` likewise return new objects; dividing by
zero raises `ZeroDivisionError` rather than producing `inf`/`nan`. `repr()` is
eval-able: `eval(repr(a)) == a` must hold for every class.

Operator semantics are split deliberately: `@` is reserved for
linear-algebra products (vector/matrix multiplication), while `*` is
scalar-only — with one named exception, `Quaternion * Vec3`, which rotates
the vector and is kept because it matches the C++ NGL API it ports.

`tests/test_api_consistency.py` is the enforcement mechanism: it builds one
distinctive, invertible sample instance per class (`SAMPLES`, keyed by class)
and runs every contract check above as a `pytest.mark.parametrize`d test
across all six classes at once (constructor, float32 storage, copy identity,
numpy/list round-trips, `to_tuple`, hashing, `repr` round-trip, `len`/`iter`,
purity of `normalized`/`transposed`/`inverse`/`conjugate`, `-a`, `/`,
`__getitem__`). Adding a seventh math class means adding it to `SAMPLES` and
it is automatically covered by every existing test in the file — there is no
per-class test to hand-write.

Beyond the math classes, the whole `src/` tree follows shared conventions:
module-specific errors are plain `Exception` subclasses named `<Module>Error`
(e.g. `MatrixError`, `ObjParseVertexError`) and are raised, never returned as
sentinel values; numeric data prefers numpy `np.float32` arrays over Python
lists, and data-heavy classes use `__slots__`; every function/class touched
must carry complete type hints and a Google-style docstring
(Args/Returns/Raises) — Ruff's `ANN`/`D` rules enforce this on new/edited
code via a non-blocking CI job while an inherited backlog is cleared
module-by-module; standalone executable scripts use the shebang
`#!/usr/bin/env -S uv run --script`; and "colour" (not "color") is the
correct spelling throughout identifiers, docs, and variables.

## Key invariants

- `_data` is always a numpy array of dtype `np.float32` — never `float64` or
  a Python list.
- `normalized()`, `transposed()`, `inverse()`, `clamped()`, `conjugate()`
  return new objects; they must never mutate `self`. Only `set()` and
  `__setitem__` mutate in place.
- Every class needs `from_list`, `from_numpy`, `copy`, `to_numpy`, `to_list`,
  `to_tuple`, `__eq__`, `__hash__`, and an eval-able `__repr__` — omitting any
  one breaks `tests/test_api_consistency.py` for every class, not just the
  one you touched.
- `to_numpy()` must return a copy, not a view — callers must not be able to
  mutate internal state through it.
- `@` = linear-algebra product; `*` = scalar multiply only, except
  `Quaternion * Vec3` (vector rotation) — do not add further exceptions
  without updating this page and the test suite.
- Dividing by zero must raise `ZeroDivisionError`, not silently produce
  `inf`/`nan`.
- New math classes must be added to `SAMPLES` in
  `tests/test_api_consistency.py`, not given bespoke duplicate tests.
- Custom exceptions are named `<Module>Error` and raised — never sentinel
  return values (`None`, `-1`, etc.) for error conditions.
- New/edited functions and classes require full type hints and a
  Google-style docstring; don't add to the pre-existing lint backlog.
- Spell it "colour", not "color", in all new identifiers, docs, and prose.
- Executable scripts start with `#!/usr/bin/env -S uv run --script`.

## Connections

- [Wiki index](../index.md)
