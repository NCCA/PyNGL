---
sources:
  - CLAUDE.md
  - tests/test_api_consistency.py
synced: b3ac1a4e16eb594b40036f776028ae25de168432
---

# Decision log

## Summary

PyNGL is a Python port of the C++ NGL teaching library (NCCA, Bournemouth
University), not a green-field design. Many of its conventions exist to keep
the Python API recognisable to students and staff who already know NGL, to
make the code teachable, and to keep a foothold in both the OpenGL and WebGPU
worlds without one leaking into the other. This page records the deliberate
choices behind the shape of the API — the "why", not the "what" (see
[API conventions](architecture/api-conventions.md) for the "what").

## How it works

Each entry is a standalone decision; read any one without the others.

- **`@` for linear algebra, `*` for scalars.** Matrix/vector multiplication
  uses Python's `@` (`__matmul__`) operator so it reads unambiguously as a
  linear-algebra product; `*` is reserved for scalar scaling. The one
  exception is `Quaternion * Vec3`, which rotates the vector — kept per spec
  (i.e. matching NGL's existing C++ API) even though it breaks the
  scalar-only rule, because changing it would diverge from the ported
  library's established usage.
- **Immutable-style math ops.** `normalized()`, `transposed()`, `inverse()`,
  `clamped()` and friends return new objects and leave the receiver
  unchanged; only `set()` and element assignment mutate in place. This
  removes a whole class of aliasing bugs (a shared `Vec3` silently changing
  under a caller) that are easy for students to trip over.
  `tests/test_api_consistency.py::test_vectors_normalized_is_pure` and
  `test_matrices_transposed_is_pure` enforce this by asserting the receiver
  is unchanged after the call.
- **`np.float32` storage in `_data`.** All math classes store components as
  numpy `float32`, not Python `float` or `float64`, because that is the
  precision GPUs expect — data handed to OpenGL/WebGPU buffers needs no
  conversion. `test_storage_is_float32` checks every class's `_data.dtype`.
- **`__slots__` on data-heavy classes.** Numeric-heavy classes use
  `__slots__` to keep memory overhead down and access fast, consistent with
  preferring numpy arrays over Python lists for numeric data. Worth spelling
  carefully: a bare `slots = (...)` is a legal, inert class attribute, so
  the saving is silently lost with nothing to warn you.
- **`ShaderLib` as a singleton registry, not `ShaderProgram` directly.**
  `shader.py` (one compiled shader) links into `shader_program.py` (one
  linked program with uniform setters), but application code is meant to go
  through `shader_lib.py`'s `ShaderLib` — a singleton registry of named
  programs. This mirrors NGL's C++ `ShaderLib` and gives call sites a single
  well-known place to look up "the current shader" instead of passing
  `ShaderProgram` instances around.
- **OpenGL isolated in `ncca.ngl.opengl`, not re-exported.** Anything that
  directly imports `OpenGL.GL` lives in the `opengl/` sub-package and is
  deliberately excluded from `ncca.ngl`'s top-level re-exports, so the
  top-level package stays API-agnostic (importable without a GL context).
  `src/ncca/ngl/webgpu/` mirrors the same shape (`base_webgpu_pipeline.py` →
  concrete pipelines → `pipeline_factory.py`) so the two rendering backends
  stay structurally parallel and swappable rather than entangled.
- **Plain `<Module>Error` exceptions, not sentinel returns.** Errors
  (`MatrixError`, `ObjParseVertexError`, etc.) are raised as named
  `Exception` subclasses rather than encoded as `None`/`False`/magic return
  values, so failures are explicit and cannot be silently ignored by
  forgetting to check a return value.
- **British "colour" spelling.** Identifiers, docs and variables use
  "colour", matching NGL's original British-English convention rather than
  the US spelling common in most Python code.
- **`ANN401`/`Any` allowed at math/shader-uniform bridge points.** Ruff's
  type-hint rules are enforced everywhere except this one carve-out, because
  uniform-setting code genuinely bridges typed Python values to
  loosely-typed GPU uniform calls; forcing a precise type there would be
  false precision. An explicit CLI `--select ANN,D` overrides the
  config's ignore list and wrongly re-flags this case, so lint must be run
  via the plain `ruff check src/` command from `pyproject.toml`.
- **GPU tests are opt-in by marker, not default.** `opengl_context`,
  `webgpu_device` and `qt_app` fixtures are session-scoped and require a
  real graphics context; tests depending on them are auto-deselected from a
  plain `uv run pytest` run and only execute under `-m opengl`/`-m
  webgpu`/`-m qt`. This keeps CI and default local runs fast and
  headless-safe, at the cost that a green default run never proves
  graphics-dependent code paths actually ran (see
  [Test architecture](architecture/test-architecture.md)).

## Key invariants

- `Quaternion * Vec3` is the only sanctioned exception to "`*` is scalar
  only" — do not add further exceptions without matching NGL's C++ spec.
- Never re-export an `opengl/`, `webgpu/`, `widgets/`, or `qml/` module
  from top-level `ncca.ngl.__init__`.
- Never run `ruff check --select ANN,D src/` directly; it defeats the
  `ANN401` carve-out in `pyproject.toml`.
- New math methods that transform a vector/matrix/quaternion must return a
  new instance, not mutate `self`, unless named `set()`.

## Connections

- [API conventions](architecture/api-conventions.md) — the concrete contract
  these decisions produce
- [System overview](architecture/overview.md) — where `opengl/` and
  `webgpu/` sit in the package layout
- [Test architecture](architecture/test-architecture.md) — the GPU marker
  system in full
- [Math](modules/math.md) — the classes these decisions govern
- [Shaders](modules/shaders.md) — `ShaderLib` in context
