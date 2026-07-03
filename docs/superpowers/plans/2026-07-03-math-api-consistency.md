# Math API Consistency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every math type in `ncca.ngl` (Vec2/3/4, Mat2/3/4, Quaternion) one uniform, immutable-style, numpy-float32-backed API, per the approved spec at `docs/superpowers/specs/2026-07-03-math-api-consistency-design.md`.

**Architecture:** Rewrite `VectorBase` in place (float32, immutable naming); add a new `MatrixBase` in `mat_base.py` that `Mat2/3/4` inherit; make `Quaternion` conform to the same contract standalone. A parametrised conformance test suite locks the contract in.

**Tech Stack:** Python 3.11+, numpy, pytest, ruff, `uv` for everything.

## Global Constraints

- Work in the worktree: `/Volumes/teaching/Code/PyNGL/.worktrees/math-api` (branch `agent/math-api-consistency`). All paths below are relative to it.
- Run everything with `uv run` (e.g. `uv run pytest`, `uv run ruff check src/`).
- All math storage is `np.float32`; the private attribute is `_data`; `__slots__ = ("_data",)`.
- Immutable-style: operations return new objects. Only `set(*args)` and component/element assignment mutate.
- No deprecation shims — old names are deleted and all in-repo callers fixed in the same task.
- Conventional commit messages, ending with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- Before each commit: `uv run ruff format src/ tests/ && uv run ruff check src/ tests/` must be clean, and `uv run pytest` must pass.
- "Colour" spelling; Google-style docstrings; type hints on all signatures.
- Deliberate spec deviation to preserve graphics semantics: `Vec4()` defaults to `(0, 0, 0, 1)` (homogeneous point convention), not all-zero. Matrix `@` keeps existing row-vector semantics: `(a @ b)._data == b._data @ a._data` for mat@mat, and `m @ v` computes `m._data @ v`.

---

### Task 1: VectorBase rewrite + Vec2/3/4 + vector call sites

**Files:**
- Modify: `src/ncca/ngl/vector_base.py`
- Modify: `src/ncca/ngl/vec2.py`, `src/ncca/ngl/vec3.py`, `src/ncca/ngl/vec4.py`
- Modify: `src/ncca/ngl/util.py` (normalize call sites only), `src/ncca/ngl/plane.py`, `src/ncca/ngl/random.py`, `src/ncca/ngl/first_person_camera.py`
- Test: `tests/test_vec2.py`, `tests/test_vec3.py`, `tests/test_vec4.py`, plus any test using renamed vector methods

**Interfaces:**
- Produces (later tasks rely on these exact names): `normalized() -> Self`, `reflected(n) -> Self`, `clamped(low, high) -> Self`, `lerp(rhs, t) -> Self`, `from_list(lst) -> Self` (classmethod), `from_numpy(arr) -> Self` (classmethod), `__len__`, eval-able `__repr__` (`Vec3(1.0, 2.0, 3.0)`), `_data` is `np.float32` shape `(DIMENSION,)`.
- Deletes: `normalize()`, `reflect()`, `clamp()` (method), `null()`, `__iadd__`, `__isub__`.

- [ ] **Step 1: Update vector tests to the new API**

Apply this mechanical mapping in `tests/test_vec2.py`, `tests/test_vec3.py`, `tests/test_vec4.py` (grep each file for the old names):

| Old | New |
|---|---|
| `v.normalize()` (statement) | `v = v.normalized()` |
| `x = v.normalize()` | `x = v.normalized()` |
| `v.reflect(n)` | `v.reflected(n)` |
| `v.clamp(lo, hi)` (statement) | `v = v.clamped(lo, hi)` |
| `v.null()` | `v.set(0.0, 0.0, 0.0)` (per-dimension arg count) |
| tests of `__iadd__`/`__isub__` identity (`a is b`) | delete the identity assertion; `a += b` still works via `__add__`, keep value assertions |
| `repr(v) == "Vec4 [...]"` style assertions | `repr(v) == "Vec4(1.0, 2.0, 3.0, 4.0)"` |
| `str(v)` int-formatting assertions (`"[1,2,3]"`) | `str(v) == "[1.0, 2.0, 3.0]"` |

Add these new tests to each of the three files (shown for Vec3; adjust arity for Vec2/Vec4):

```python
def test_normalized_returns_new():
    v = Vec3(3.0, 0.0, 0.0)
    n = v.normalized()
    assert n == Vec3(1.0, 0.0, 0.0)
    assert v == Vec3(3.0, 0.0, 0.0)  # original untouched

def test_clamped_returns_new():
    v = Vec3(-2.0, 0.5, 9.0)
    c = v.clamped(0.0, 1.0)
    assert c == Vec3(0.0, 0.5, 1.0)
    assert v == Vec3(-2.0, 0.5, 9.0)

def test_lerp():
    a = Vec3(0.0, 0.0, 0.0)
    b = Vec3(2.0, 4.0, 6.0)
    assert a.lerp(b, 0.5) == Vec3(1.0, 2.0, 3.0)

def test_from_numpy_round_trip():
    import numpy as np
    v = Vec3.from_numpy(np.array([1.0, 2.0, 3.0]))
    assert v == Vec3(1.0, 2.0, 3.0)
    assert v.to_numpy().dtype == np.float32

def test_eval_repr_round_trip():
    v = Vec3(1.5, 2.5, 3.5)
    assert eval(repr(v)) == v

def test_dtype_is_float32():
    import numpy as np
    assert Vec3(1.0, 2.0, 3.0)._data.dtype == np.float32
```

- [ ] **Step 2: Run vector tests to verify they fail**

Run: `uv run pytest tests/test_vec2.py tests/test_vec3.py tests/test_vec4.py -x -q`
Expected: FAIL (`AttributeError: ... has no attribute 'normalized'` etc.)

- [ ] **Step 3: Rewrite `vector_base.py`**

Precise edits to `src/ncca/ngl/vector_base.py`:

1. Change every `dtype=np.float64` to `dtype=np.float32` (two places, `_init_from_kwargs` and `_init_from_args`).
2. Remove `from .util import clamp, hash_combine` → keep only `hash_combine`; `clamp` no longer used.
3. Add `__slots__ = ("_data",)` to the class body (subclasses already declare it too — harmless).
4. Delete methods: `__iadd__`, `__isub__`, `normalize`, `null`, `clamp`.
5. Delete the abstract `__repr__` and `__str__` declarations; add concrete implementations.
6. Rename abstract `reflect` → `reflected` (docstring: "Return a new vector reflected about the normal").
7. Add the following methods:

```python
    def __len__(self) -> int:
        """Return the number of components."""
        return self.DIMENSION

    def normalized(self) -> Self:
        """Return a new vector normalized to unit length.

        Returns:
            A new unit-length vector.

        Raises:
            ZeroDivisionError: If the length of the vector is zero.
        """
        vector_length = self.length()
        if math.isclose(vector_length, 0.0):
            raise ZeroDivisionError(
                f"{self.__class__.__name__}.normalized: length is zero"
            )
        result = self.__class__()
        result._data = self._data / np.float32(vector_length)
        return result

    def clamped(self, low: float, high: float) -> Self:
        """Return a new vector with each component clamped to [low, high].

        Args:
            low: The low end of the range.
            high: The high end of the range.

        Returns:
            A new clamped vector.
        """
        result = self.__class__()
        result._data = np.clip(self._data, low, high).astype(np.float32)
        return result

    def lerp(self, rhs: Self, t: float) -> Self:
        """Return the linear interpolation between this vector and rhs at t.

        Args:
            rhs: The target vector.
            t: Interpolation parameter (0.0 returns self, 1.0 returns rhs).

        Returns:
            A new interpolated vector.
        """
        if not isinstance(rhs, self.__class__):
            raise ValueError(f"Can only lerp with {self.__class__.__name__}")
        result = self.__class__()
        result._data = self._data + (rhs._data - self._data) * np.float32(t)
        return result

    @classmethod
    def from_list(cls, lst: list[float]) -> Self:
        """Create a vector from a list of components.

        Args:
            lst: A list of exactly DIMENSION floats.

        Returns:
            A new vector.

        Raises:
            ValueError: If the list has the wrong length.
        """
        if len(lst) != cls.DIMENSION:
            raise ValueError(
                f"{cls.__name__}.from_list requires {cls.DIMENSION} values"
            )
        return cls(*lst)

    @classmethod
    def from_numpy(cls, arr: np.ndarray) -> Self:
        """Create a vector from a numpy array.

        Args:
            arr: An array of shape (DIMENSION,).

        Returns:
            A new vector.

        Raises:
            ValueError: If the array has the wrong shape.
        """
        arr = np.asarray(arr, dtype=np.float32)
        if arr.shape != (cls.DIMENSION,):
            raise ValueError(
                f"{cls.__name__}.from_numpy requires shape ({cls.DIMENSION},)"
            )
        result = cls()
        result._data = arr.copy()
        return result

    def __repr__(self) -> str:
        """Eval-able representation, e.g. Vec3(1.0, 2.0, 3.0)."""
        args = ", ".join(repr(float(v)) for v in self._data)
        return f"{self.__class__.__name__}({args})"

    def __str__(self) -> str:
        """Pretty representation, e.g. [1.0, 2.0, 3.0]."""
        return "[" + ", ".join(str(float(v)) for v in self._data) + "]"
```

8. In `to_tuple`, return plain floats: `return tuple(float(v) for v in self._data)`.
9. In `__getitem__`, return `float(self._data[index])`.

- [ ] **Step 4: Update `vec2.py`, `vec3.py`, `vec4.py`**

In all three files:
- Rename `def reflect(` → `def reflected(` (keep bodies; they already return new objects).
- Delete the per-class `__repr__` and `__str__` methods (the base now provides them).
- Leave `outer()` and `__matmul__` untouched in all three files this task — they reference the matrix `.m` attribute, which still exists until Task 2 updates them.

- [ ] **Step 5: Fix vector call sites in `util.py`, `plane.py`, `random.py`, `first_person_camera.py`**

Exact replacements (all are mutating `normalize()` statements):

`src/ncca/ngl/util.py`:
- line ~30-32 (`look_at`): `n.normalize()` → `n = n.normalized()`, `v.normalize()` → `v = v.normalized()`, `u.normalize()` → `u = u.normalized()`
- line ~156 (`calc_normal`): `normal.normalize()` → `normal = normal.normalized()` (and `return normal` stays)
- lines ~185-194 (`renderman_look_at`): same pattern for `n`, `v`, `u`.

`src/ncca/ngl/plane.py` (3 sites): `self._normal.normalize()` → `self._normal = self._normal.normalized()`

`src/ncca/ngl/random.py` (3 sites in `get_random_normalized_vec{2,3,4}`): `v.normalize()` → `v = v.normalized()` (keep the following `return v`).

`src/ncca/ngl/first_person_camera.py` (3 sites): `self.front.normalize()` → `self.front = self.front.normalized()`, `self.right.normalize()` → `self.right = self.right.normalized()`.

- [ ] **Step 6: Run the full default suite**

Run: `uv run pytest -q`
Expected: PASS. If other test files (e.g. `tests/test_util.py`, `tests/test_plane.py`, `tests/test_random.py`) use the old vector names, apply the Step 1 mapping there too.

- [ ] **Step 7: Lint and commit**

```bash
uv run ruff format src/ tests/ && uv run ruff check src/ tests/
git add -A src tests
git commit -m "refactor(math)!: immutable float32 vector API (normalized/reflected/clamped/lerp)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: MatrixBase + Mat2/3/4 rewrite + matrix call sites

**Files:**
- Create: `src/ncca/ngl/mat_base.py`
- Rewrite: `src/ncca/ngl/mat2.py`, `src/ncca/ngl/mat3.py`, `src/ncca/ngl/mat4.py`
- Modify: `src/ncca/ngl/__init__.py`, `src/ncca/ngl/util.py`, `src/ncca/ngl/vec2.py`, `src/ncca/ngl/vec3.py`, `src/ncca/ngl/vec4.py`, `src/ncca/ngl/transform.py` (internal fix only), `src/ncca/ngl/shader_program.py`, `src/ncca/ngl/quaternion.py` (one line)
- Test: `tests/test_mat2.py`, `tests/test_mat3.py`, `tests/test_mat4.py`

**Interfaces:**
- Consumes: Task 1's `VectorBase` (unchanged here).
- Produces: `MatrixError` exception; `MatrixBase` with `_data` float32 `(SIZE, SIZE)`; `transposed()`, `inverse()`, `determinant() -> float`, `identity()`, `zero()`, `from_list()`, `from_numpy()`, `copy()`, `to_numpy()`, `to_list()` (flat row-major), `to_tuple()`, `__matmul__` (mat@mat preserves old semantics `rhs._data @ self._data`; mat@vec computes `self._data @ v`), scalar `__mul__`/`__rmul__`, `__add__`/`__sub__`, `__getitem__` returning a numpy row **view** (so `m[3][0] = x` writes through), `__setitem__`, `__eq__`/`__ne__`/`__hash__`, eval-able `__repr__` (`Mat3(1.0, 0.0, ...)` — constructor accepts SIZE*SIZE flat row-major args), `__len__` (= SIZE), `__iter__` (flat floats).
- Deletes: `get_matrix()`, `transpose()` (mutating), `get_transpose()`, public `.m` attribute, `Mat2Error`, `Mat2NotSquare`, `Mat3Error`, `Mat3NotSquare`, `Mat4Error`, `Mat4NotSquare`, matrix `__iadd__`/`__isub__`.

- [ ] **Step 1: Update matrix tests to the new API**

Mapping for `tests/test_mat2.py`, `tests/test_mat3.py`, `tests/test_mat4.py`:

| Old | New |
|---|---|
| `m.get_matrix()` | `m.to_list()` |
| `m.transpose()` (statement) | `m = m.transposed()` |
| `m.get_transpose()` | `m.transposed()` |
| `m.m` (direct array access) | `m.to_numpy()` for reads; `m[i][j] = x` for element writes |
| `Mat3Error` / `Mat3NotSquare` (and 2/4 variants) | `MatrixError` (import from `ncca.ngl`) |
| `m[0] == [1.0, 0.0, 0.0]` (row-as-list) | `m[0].tolist() == [1.0, 0.0, 0.0]` |
| `a is b` assertions on `__iadd__` | delete; keep value assertions |

Add per file (shown for Mat3; adjust size for Mat2/Mat4):

```python
def test_ctor_components():
    m = Mat3(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)
    assert m.to_list() == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]

def test_transposed_returns_new():
    m = Mat3(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)
    t = m.transposed()
    assert t.to_list() == [1.0, 4.0, 7.0, 2.0, 5.0, 8.0, 3.0, 6.0, 9.0]
    assert m.to_list()[1] == 2.0  # original untouched

def test_eval_repr_round_trip():
    m = Mat3.rotate_x(45.0)
    assert eval(repr(m)) == m

def test_hashable():
    m = Mat3.identity()
    assert hash(m) == hash(m.copy())

def test_element_write_through():
    m = Mat3.identity()
    m[1][2] = 0.5
    assert m.to_numpy()[1][2] == np.float32(0.5)

def test_from_numpy():
    m = Mat3.from_numpy(np.arange(9, dtype=np.float32).reshape(3, 3))
    assert m.to_list() == [float(i) for i in range(9)]

def test_mat2_has_full_api():  # test_mat2.py only
    m = Mat2(1.0, 2.0, 3.0, 4.0)
    assert m.determinant() == pytest.approx(-2.0)
    assert m.inverse() @ m == Mat2.identity()
    assert (m + m).to_list() == [2.0, 4.0, 6.0, 8.0]
    assert (m - m) == Mat2.zero()
    assert m.transposed().to_list() == [1.0, 3.0, 2.0, 4.0]
```

- [ ] **Step 2: Run matrix tests to verify they fail**

Run: `uv run pytest tests/test_mat2.py tests/test_mat3.py tests/test_mat4.py -x -q`
Expected: FAIL (`TypeError: Mat3() takes no arguments` / missing names).

- [ ] **Step 3: Create `src/ncca/ngl/mat_base.py`**

Full file:

```python
"""Shared base class for square matrix types (Mat2, Mat3, Mat4).

All matrices are numpy float32 backed and follow the immutable-style API:
operations return new matrices; the only mutation is element assignment
via ``m[row][col] = value`` or ``m[row] = [...]``.
"""

import ctypes
from typing import Any, ClassVar, Self

import numpy as np


class MatrixError(Exception):
    """Raised for invalid matrix construction or operations."""


class MatrixBase:
    """Base class providing the common square-matrix API.

    Attributes:
        SIZE: The row/column count (2, 3 or 4), set by subclasses.
    """

    SIZE: ClassVar[int]
    __slots__ = ("_data",)

    def __init__(self, *args: float) -> None:
        """Construct an identity matrix, or from SIZE*SIZE row-major values.

        Args:
            *args: Either nothing (identity) or SIZE*SIZE floats row-major.

        Raises:
            MatrixError: If the wrong number of components is given.
        """
        n = self.SIZE
        if not args:
            self._data = np.eye(n, dtype=np.float32)
        elif len(args) == n * n:
            self._data = np.array(args, dtype=np.float32).reshape(n, n)
        else:
            raise MatrixError(
                f"{self.__class__.__name__} requires 0 or {n * n} components"
            )

    # -- factories ---------------------------------------------------------
    @classmethod
    def identity(cls) -> Self:
        """Return a new identity matrix."""
        return cls()

    @classmethod
    def zero(cls) -> Self:
        """Return a new all-zero matrix."""
        result = cls()
        result._data = np.zeros((cls.SIZE, cls.SIZE), dtype=np.float32)
        return result

    @classmethod
    def from_list(cls, lst: list) -> Self:
        """Create a matrix from a nested or flat row-major list.

        Args:
            lst: Either SIZE lists of SIZE floats, or a flat list of
                SIZE*SIZE floats.

        Raises:
            MatrixError: If the shape is wrong.
        """
        n = cls.SIZE
        result = cls()
        if (
            isinstance(lst, list)
            and len(lst) == n
            and all(isinstance(row, list) and len(row) == n for row in lst)
        ):
            result._data = np.array(lst, dtype=np.float32)
            return result
        if isinstance(lst, list) and len(lst) == n * n:
            result._data = np.array(lst, dtype=np.float32).reshape(n, n)
            return result
        raise MatrixError(f"{cls.__name__}.from_list requires {n}x{n} values")

    @classmethod
    def from_numpy(cls, arr: np.ndarray) -> Self:
        """Create a matrix from a numpy array of shape (n, n) or (n*n,).

        Raises:
            MatrixError: If the shape is wrong.
        """
        n = cls.SIZE
        arr = np.asarray(arr, dtype=np.float32)
        if arr.shape == (n * n,):
            arr = arr.reshape(n, n)
        if arr.shape != (n, n):
            raise MatrixError(f"{cls.__name__}.from_numpy requires shape ({n},{n})")
        result = cls()
        result._data = arr.copy()
        return result

    # -- exports -----------------------------------------------------------
    def to_numpy(self) -> np.ndarray:
        """Return a float32 copy of the matrix as a (n, n) numpy array."""
        return self._data.copy()

    def to_list(self) -> list[float]:
        """Return the matrix as a flat row-major list of floats."""
        return self._data.flatten("C").tolist()

    def to_tuple(self) -> tuple[float, ...]:
        """Return the matrix as a flat row-major tuple of floats."""
        return tuple(float(v) for v in self._data.flatten("C"))

    def copy(self) -> Self:
        """Return a new matrix with the same values."""
        result = self.__class__()
        result._data = self._data.copy()
        return result

    @classmethod
    def sizeof(cls) -> int:
        """Return the size of the matrix in bytes (for OpenGL compatibility)."""
        return cls.SIZE * cls.SIZE * ctypes.sizeof(ctypes.c_float)

    # -- linear algebra ----------------------------------------------------
    def transposed(self) -> Self:
        """Return a new matrix that is the transpose of this one."""
        result = self.__class__()
        result._data = self._data.T.copy()
        return result

    def determinant(self) -> float:
        """Return the determinant of the matrix."""
        return float(np.linalg.det(self._data))

    def inverse(self) -> Self:
        """Return a new matrix that is the inverse of this one.

        Raises:
            MatrixError: If the matrix is singular.
        """
        try:
            result = self.__class__()
            result._data = np.linalg.inv(self._data).astype(np.float32)
            return result
        except np.linalg.LinAlgError as e:
            raise MatrixError("matrix is not invertible") from e

    # -- operators ----------------------------------------------------------
    def _vec_type(self) -> type:
        """Return the vector type this matrix transforms (set by subclass)."""
        raise NotImplementedError  # pragma: no cover

    def __matmul__(self, rhs: Any) -> Any:
        """Matrix @ matrix (row-vector convention) or matrix @ vector.

        Raises:
            MatrixError: If rhs is not a compatible matrix or vector.
        """
        if isinstance(rhs, self.__class__):
            result = self.__class__()
            result._data = rhs._data @ self._data
            return result
        vec_type = self._vec_type()
        if isinstance(rhs, vec_type):
            res = self._data @ np.asarray(list(rhs), dtype=np.float32)
            return vec_type(*res)
        raise MatrixError(
            f"can only multiply {self.__class__.__name__} by "
            f"{self.__class__.__name__} or {vec_type.__name__}"
        )

    def __mul__(self, rhs: float | int) -> Self:
        """Multiply every element by a scalar, returning a new matrix.

        Raises:
            MatrixError: If rhs is not a scalar.
        """
        if isinstance(rhs, (int, float)):
            result = self.__class__()
            result._data = self._data * np.float32(rhs)
            return result
        raise MatrixError("matrices only scale by scalars; use @ for products")

    def __rmul__(self, rhs: float | int) -> Self:
        """Scalar * matrix."""
        return self * rhs

    def __add__(self, rhs: Self) -> Self:
        """Piecewise addition, returning a new matrix."""
        if not isinstance(rhs, self.__class__):
            raise MatrixError(f"can only add {self.__class__.__name__}")
        result = self.__class__()
        result._data = self._data + rhs._data
        return result

    def __sub__(self, rhs: Self) -> Self:
        """Piecewise subtraction, returning a new matrix."""
        if not isinstance(rhs, self.__class__):
            raise MatrixError(f"can only subtract {self.__class__.__name__}")
        result = self.__class__()
        result._data = self._data - rhs._data
        return result

    def __getitem__(self, idx: int) -> np.ndarray:
        """Return row idx as a numpy view (element writes go through)."""
        return self._data[idx]

    def __setitem__(self, idx: int, item: Any) -> None:
        """Assign row idx from an iterable of floats."""
        self._data[idx] = np.asarray(item, dtype=np.float32)

    def __len__(self) -> int:
        """Return the row count."""
        return self.SIZE

    def __iter__(self):
        """Yield the elements flat, row-major, as floats."""
        for v in self._data.flatten("C"):
            yield float(v)

    def __eq__(self, rhs: Any) -> bool:
        """Tolerant value equality."""
        if not isinstance(rhs, self.__class__):
            return NotImplemented
        return bool(np.allclose(self._data, rhs._data, rtol=1e-5, atol=1e-6))

    def __ne__(self, rhs: Any) -> bool:
        """Tolerant value inequality."""
        result = self.__eq__(rhs)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self) -> int:
        """Hash combining all elements (32-bit float semantics)."""
        # local import to avoid the util -> mat4 -> mat_base import cycle
        from .util import hash_combine

        seed = 0
        for v in self._data.flatten("C"):
            seed = hash_combine(seed, hash(float(np.float32(v))))
        return seed

    def __repr__(self) -> str:
        """Eval-able representation, e.g. Mat2(1.0, 0.0, 0.0, 1.0)."""
        args = ", ".join(repr(float(v)) for v in self._data.flatten("C"))
        return f"{self.__class__.__name__}({args})"

    def __str__(self) -> str:
        """Pretty row-per-line representation."""
        rows = [str(self._data[i].tolist()) for i in range(self.SIZE)]
        return "[" + "\n ".join(rows) + "]"
```

- [ ] **Step 4: Rewrite `mat2.py`, `mat3.py`, `mat4.py` as thin subclasses**

`src/ncca/ngl/mat2.py` — full new content:

```python
"""Mat2: 2x2 float32 matrix built on MatrixBase."""

from .mat_base import MatrixBase, MatrixError  # noqa: F401  (re-export)


class Mat2(MatrixBase):
    """A 2x2 matrix for 2D transforms."""

    SIZE = 2

    def _vec_type(self) -> type:
        from .vec2 import Vec2

        return Vec2
```

`src/ncca/ngl/mat3.py` — full new content (keep the existing rotation-value layout exactly — the `a.m[...]` assignments become `a._data[...]`):

```python
"""Mat3: 3x3 float32 matrix built on MatrixBase."""

import math

from .mat_base import MatrixBase, MatrixError  # noqa: F401  (re-export)


class Mat3(MatrixBase):
    """A 3x3 matrix for basic affine transforms."""

    SIZE = 3

    def _vec_type(self) -> type:
        from .vec3 import Vec3

        return Vec3

    @classmethod
    def scale(cls, x: float, y: float, z: float) -> "Mat3":
        """Return a scale matrix with the diagonal set to (x, y, z)."""
        a = cls()
        a._data[0, 0] = x
        a._data[1, 1] = y
        a._data[2, 2] = z
        return a

    @classmethod
    def rotate_x(cls, angle: float) -> "Mat3":
        """Return a rotation matrix around the X axis by angle degrees."""
        a = cls()
        beta = math.radians(angle)
        sr = math.sin(beta)
        cr = math.cos(beta)
        a._data[1, 1] = cr
        a._data[1, 2] = sr
        a._data[2, 1] = -sr
        a._data[2, 2] = cr
        return a

    @classmethod
    def rotate_y(cls, angle: float) -> "Mat3":
        """Return a rotation matrix around the Y axis by angle degrees."""
        a = cls()
        beta = math.radians(angle)
        sr = math.sin(beta)
        cr = math.cos(beta)
        a._data[0, 0] = cr
        a._data[0, 2] = -sr
        a._data[2, 0] = sr
        a._data[2, 2] = cr
        return a

    @classmethod
    def rotate_z(cls, angle: float) -> "Mat3":
        """Return a rotation matrix around the Z axis by angle degrees."""
        a = cls()
        beta = math.radians(angle)
        sr = math.sin(beta)
        cr = math.cos(beta)
        a._data[0, 0] = cr
        a._data[0, 1] = sr
        a._data[1, 0] = -sr
        a._data[1, 1] = cr
        return a

    @classmethod
    def from_mat4(cls, mat4) -> "Mat3":
        """Return the upper-left 3x3 of a Mat4."""
        result = cls()
        result._data = mat4._data[:3, :3].copy()
        return result
```

`src/ncca/ngl/mat4.py` — same structure; `SIZE = 4`, `_vec_type` returns `Vec4`, and factories `scale`, `translate`, `rotate_x`, `rotate_y`, `rotate_z`, `from_mat3` — copy the numeric element layout verbatim from the current file (`self.m[...]`/`a.m[...]` → `a._data[...]`). `translate` keeps its current row placement (`a._data[3, 0] = x` etc. — check the existing body at `src/ncca/ngl/mat4.py:129` and preserve it exactly). Add:

```python
    @classmethod
    def from_mat3(cls, mat3) -> "Mat4":
        """Return a Mat4 with the given Mat3 as its upper-left block."""
        result = cls()
        result._data[:3, :3] = mat3._data
        return result
```

- [ ] **Step 5: Fix matrix call sites**

- `src/ncca/ngl/__init__.py`: replace exports of `Mat2Error`, `Mat2NotSquare`, `Mat3Error`, `Mat3NotSquare`, `Mat4Error`, `Mat4NotSquare` with a single `MatrixError` (import from `.mat_base`); keep `Mat2/3/4` exports. Update `__all__` accordingly.
- `src/ncca/ngl/util.py`: every `result.m[i][j] = v` → `result[i][j] = v`; `m.m[i][j] = v` → `m[i][j] = v` (in `look_at`, `perspective`, `ortho`, `frustum`, `renderman_look_at`).
- `src/ncca/ngl/vec2.py`/`vec3.py`/`vec4.py` `outer()`: `result.m = np.outer(...).astype(np.float64)` → `result._data = np.outer(self._data, rhs._data).astype(np.float32)`.
- `src/ncca/ngl/vec4.py` `__matmul__`: `Vec4(*self._data @ rhs.m)` → `Vec4(*(self._data @ rhs._data))`. Same pattern in `vec2.py`/`vec3.py` if they reference `rhs.m`.
- `src/ncca/ngl/transform.py` `get_matrix()`: `self.matrix.m[3][0]` → `self.matrix[3][0]` (four lines; full rename to `matrix()` happens in Task 4).
- `src/ncca/ngl/shader_program.py`: `matrix.get_matrix()` → `matrix.to_list()` (line ~328) and the three `hasattr(matrix, "get_matrix")` guards → `hasattr(matrix, "to_list")` with `flat_values.extend(matrix.to_list())`.
- `src/ncca/ngl/quaternion.py` `from_mat4`: `matrix = mat.get_matrix()` → `matrix = mat.to_list()`.

- [ ] **Step 6: Run the full default suite**

Run: `uv run pytest -q`
Expected: PASS. Fix any straggler call sites the suite finds using the same mappings.

- [ ] **Step 7: Lint and commit**

```bash
uv run ruff format src/ tests/ && uv run ruff check src/ tests/
git add -A src tests
git commit -m "refactor(math)!: shared MatrixBase for Mat2/3/4, immutable float32 API

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Quaternion conformance

**Files:**
- Rewrite: `src/ncca/ngl/quaternion.py`
- Test: `tests/test_quaternion.py`

**Interfaces:**
- Consumes: `Mat4` from Task 2 (`to_list()`, `_data`), `Vec3`.
- Produces: `Quaternion(s, x, y, z)` float32-backed; classmethods `from_mat4`, `from_axis_angle`, `from_list`, `from_numpy`; methods `normalized()`, `conjugate()`, `inverse()`, `dot()`, `length()`, `length_squared()`, `slerp(rhs, t)`, `to_mat4()`, `set()`, `copy()`, `to_numpy()`, `to_list()`, `to_tuple()`; `__matmul__` = quaternion product; `__mul__` = scalar or Vec3 rotation only; `__eq__`/`__ne__`/`__hash__`/`__len__`; eval-able `__repr__` → `Quaternion(1.0, 0.0, 0.0, 0.0)`.
- Deletes: mutating `normalize()`, `__iadd__`/`__isub__`, quat*quat via `__mul__` (raises `TypeError` pointing at `@`).

- [ ] **Step 1: Update `tests/test_quaternion.py`**

Mapping: `q.normalize()` (statement) → `q = q.normalized()`; `q1 * q2` (both Quaternions) → `q1 @ q2`; repr assertions → `Quaternion(s, x, y, z)` form. Add:

```python
def test_matmul_product():
    a = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), 90.0)
    b = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), -90.0)
    assert a @ b == Quaternion(1.0, 0.0, 0.0, 0.0)

def test_mul_quaternion_raises():
    with pytest.raises(TypeError):
        Quaternion() * Quaternion()

def test_inverse():
    q = Quaternion.from_axis_angle(Vec3(1.0, 0.0, 0.0), 30.0)
    assert q @ q.inverse() == Quaternion(1.0, 0.0, 0.0, 0.0)

def test_slerp_endpoints():
    a = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), 0.0)
    b = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), 90.0)
    assert a.slerp(b, 0.0) == a
    assert a.slerp(b, 1.0) == b

def test_to_mat4_round_trip():
    q = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), 45.0)
    assert Quaternion.from_mat4(q.to_mat4()) == q

def test_contract():
    q = Quaternion(1.0, 0.5, 0.25, 0.125)
    assert eval(repr(q)) == q
    assert hash(q) == hash(q.copy())
    assert q.to_tuple() == (1.0, 0.5, 0.25, 0.125)
    assert Quaternion.from_list(q.to_list()) == q
    assert Quaternion.from_numpy(q.to_numpy()) == q
    assert q._data.dtype == np.float32
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_quaternion.py -x -q`
Expected: FAIL.

- [ ] **Step 3: Rewrite `quaternion.py`**

Keep the existing `from_mat4` math (with `mat.to_list()`) and `from_axis_angle` math, converted to `@classmethod`. Keep the existing `__mul__` Vec3-rotation math. Storage `dtype=np.float32`. Keep the property generation loop for `s, x, y, z`. New/changed methods:

```python
    def __matmul__(self, rhs: "Quaternion") -> "Quaternion":
        """Quaternion product (Hamilton), returning a new quaternion."""
        if not isinstance(rhs, Quaternion):
            raise TypeError("@ requires a Quaternion")
        s1, x1, y1, z1 = self._data
        s2, x2, y2, z2 = rhs._data
        return Quaternion(
            s1 * s2 - x1 * x2 - y1 * y2 - z1 * z2,
            s1 * x2 + x1 * s2 + y1 * z2 - z1 * y2,
            s1 * y2 - x1 * z2 + y1 * s2 + z1 * x2,
            s1 * z2 + x1 * y2 - y1 * x2 + z1 * s2,
        )

    def __mul__(self, rhs):
        """Scalar scale or Vec3 rotation. Quaternion product uses @."""
        if isinstance(rhs, Quaternion):
            raise TypeError("use q1 @ q2 for the quaternion product")
        if isinstance(rhs, (int, float)):
            result = Quaternion()
            result._data = self._data * np.float32(rhs)
            return result
        if isinstance(rhs, Vec3):
            ...  # keep the existing rotation math verbatim
        raise TypeError(f"cannot multiply Quaternion by {type(rhs)}")

    def __rmul__(self, rhs: float) -> "Quaternion":
        if isinstance(rhs, (int, float)):
            return self * rhs
        raise TypeError(f"cannot multiply {type(rhs)} by Quaternion")

    def normalized(self) -> "Quaternion":
        """Return a new unit-length quaternion.

        Raises:
            ZeroDivisionError: If the quaternion has zero length.
        """
        length = self.length()
        if math.isclose(length, 0.0):
            raise ZeroDivisionError("Quaternion.normalized: length is zero")
        result = Quaternion()
        result._data = self._data / np.float32(length)
        return result

    def length_squared(self) -> float:
        """Return the squared magnitude."""
        return float(np.dot(self._data, self._data))

    def inverse(self) -> "Quaternion":
        """Return the multiplicative inverse (conjugate / |q|^2)."""
        lsq = self.length_squared()
        if math.isclose(lsq, 0.0):
            raise ZeroDivisionError("Quaternion.inverse: zero quaternion")
        result = self.conjugate()
        result._data = result._data / np.float32(lsq)
        return result

    def slerp(self, rhs: "Quaternion", t: float) -> "Quaternion":
        """Spherical linear interpolation from self to rhs at t in [0, 1]."""
        dot = float(np.dot(self._data, rhs._data))
        rhs_data = rhs._data.copy()
        if dot < 0.0:
            dot = -dot
            rhs_data = -rhs_data
        if dot > 0.9995:
            data = self._data + np.float32(t) * (rhs_data - self._data)
            data = data / np.linalg.norm(data)
        else:
            theta0 = math.acos(max(-1.0, min(1.0, dot)))
            theta = theta0 * t
            s0 = math.cos(theta) - dot * math.sin(theta) / math.sin(theta0)
            s1 = math.sin(theta) / math.sin(theta0)
            data = np.float32(s0) * self._data + np.float32(s1) * rhs_data
        result = Quaternion()
        result._data = data.astype(np.float32)
        return result

    def to_mat4(self) -> Mat4:
        """Return the equivalent rotation matrix (row-vector convention)."""
        s, x, y, z = (float(v) for v in self._data)
        m = Mat4()
        m._data[0, 0] = 1.0 - 2.0 * (y * y + z * z)
        m._data[0, 1] = 2.0 * (x * y + s * z)
        m._data[0, 2] = 2.0 * (x * z - s * y)
        m._data[1, 0] = 2.0 * (x * y - s * z)
        m._data[1, 1] = 1.0 - 2.0 * (x * x + z * z)
        m._data[1, 2] = 2.0 * (y * z + s * x)
        m._data[2, 0] = 2.0 * (x * z + s * y)
        m._data[2, 1] = 2.0 * (y * z - s * x)
        m._data[2, 2] = 1.0 - 2.0 * (x * x + y * y)
        return m

    def set(self, s: float, x: float, y: float, z: float) -> None:
        """Set all four components."""
        self._data[:] = (float(s), float(x), float(y), float(z))

    def copy(self) -> "Quaternion":
        """Return a new quaternion with the same values."""
        return Quaternion(*self._data)

    def to_tuple(self) -> tuple[float, float, float, float]:
        """Return (s, x, y, z) as plain floats."""
        return tuple(float(v) for v in self._data)

    @classmethod
    def from_list(cls, lst: list[float]) -> "Quaternion":
        """Create from [s, x, y, z]."""
        if len(lst) != 4:
            raise ValueError("Quaternion.from_list requires 4 values")
        return cls(*lst)

    @classmethod
    def from_numpy(cls, arr: np.ndarray) -> "Quaternion":
        """Create from an array [s, x, y, z]."""
        arr = np.asarray(arr, dtype=np.float32)
        if arr.shape != (4,):
            raise ValueError("Quaternion.from_numpy requires shape (4,)")
        return cls(*arr)

    def __eq__(self, rhs: object) -> bool:
        if not isinstance(rhs, Quaternion):
            return NotImplemented
        return bool(np.allclose(self._data, rhs._data, rtol=1e-5, atol=1e-6))

    def __ne__(self, rhs: object) -> bool:
        result = self.__eq__(rhs)
        return result if result is NotImplemented else not result

    def __hash__(self) -> int:
        from .util import hash_combine

        seed = 0
        for v in self._data:
            seed = hash_combine(seed, hash(float(np.float32(v))))
        return seed

    def __len__(self) -> int:
        return 4

    def __repr__(self) -> str:
        args = ", ".join(repr(float(v)) for v in self._data)
        return f"Quaternion({args})"

    def __str__(self) -> str:
        s, x, y, z = (float(v) for v in self._data)
        return f"Quaternion({s}, [{x}, {y}, {z}])"
```

Delete `normalize`, `__iadd__`, `__isub__`. Keep `__add__`, `__sub__`, `dot`, `length`, `conjugate`, `to_numpy`, `to_list` (bodies unchanged apart from float32).

- [ ] **Step 4: Run tests, lint, commit**

Run: `uv run pytest -q` → PASS, then:

```bash
uv run ruff format src/ tests/ && uv run ruff check src/ tests/
git add -A src tests
git commit -m "refactor(math)!: Quaternion conforms to shared math contract

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Transform + widget

**Files:**
- Modify: `src/ncca/ngl/transform.py`, `src/ncca/ngl/widgets/transformwidget.py`
- Test: `tests/test_transform.py`, `tests/test_transform_widget.py`

**Interfaces:**
- Produces: `Transform.matrix() -> Mat4` (replaces `get_matrix()`); internal cached attribute renamed `self.matrix` → `self._matrix` (needed because the method now takes the `matrix` name). Setters unchanged — `Transform` is a stateful builder, exempt from the immutable rule.

- [ ] **Step 1: Update tests**

In `tests/test_transform.py` and `tests/test_transform_widget.py`: `tx.get_matrix()` → `tx.matrix()`; any direct `tx.matrix` attribute reads → `tx.matrix()`.

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_transform.py -x -q` → FAIL.

- [ ] **Step 3: Implement**

In `src/ncca/ngl/transform.py`: in `__init__`, `self.matrix = Mat4()` → `self._matrix = Mat4()`; rename `def get_matrix(self):` → `def matrix(self) -> Mat4:` and inside it replace `self.matrix` with `self._matrix` (5 references, including the `[3][0]`-style writes from Task 2 and the return).

In `src/ncca/ngl/widgets/transformwidget.py` (~lines 93-94): `tx.get_matrix()` → `tx.matrix()` (both the `print` and the `valueChanged.emit`).

- [ ] **Step 4: Run tests, lint, commit**

`uv run pytest -q` → PASS.

```bash
uv run ruff format src/ tests/ && uv run ruff check src/ tests/
git add -A src tests
git commit -m "refactor(transform)!: get_matrix() becomes matrix()

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: Vec2/3/4Array cleanup

**Files:**
- Modify: `src/ncca/ngl/vec2_array.py`, `src/ncca/ngl/vec3_array.py`, `src/ncca/ngl/vec4_array.py`
- Test: `tests/test_vec2_array.py`, `tests/test_vec3_array.py`, `tests/test_vec4_array.py`

**Interfaces:**
- Deletes: `get_array()`.
- Produces: `to_tuple()`; internal `_data` becomes `np.float32` (was float64); `to_numpy()` unchanged signature (flat float32). No `__hash__` — mutable container, intentionally excluded.

- [ ] **Step 1: Update tests**

Mapping in the three `tests/test_vec*_array.py` files: `a.get_array()` → `a.to_numpy().reshape(-1, N)` where N is 2/3/4 (or drop the reshape if the test only checks values). Add per file (Vec3 shown):

```python
def test_to_tuple():
    a = Vec3Array([Vec3(1.0, 2.0, 3.0), Vec3(4.0, 5.0, 6.0)])
    assert a.to_tuple() == (1.0, 2.0, 3.0, 4.0, 5.0, 6.0)

def test_dtype_float32():
    a = Vec3Array(2)
    assert a._data.dtype == np.float32
```

- [ ] **Step 2: Run to verify failure** — `uv run pytest tests/test_vec3_array.py -x -q` → FAIL.

- [ ] **Step 3: Implement in each of the three array files**

- Change every `dtype=np.float64` → `dtype=np.float32` (three places per file: empty init, int init, iterable init; also `append`/`extend` row construction).
- `to_numpy()` body becomes `return self._data.flatten().copy()` (already float32 now).
- Delete `get_array()`.
- Add, with the class's own docstring noting: "Mutable container — intentionally not hashable."

```python
    def to_tuple(self) -> tuple[float, ...]:
        """Return all components as one flat tuple of floats."""
        return tuple(float(v) for v in self._data.flatten())
```

- [ ] **Step 4: Run tests, lint, commit**

`uv run pytest -q` → PASS.

```bash
uv run ruff format src/ tests/ && uv run ruff check src/ tests/
git add -A src tests
git commit -m "refactor(math)!: float32 Vec*Array, drop get_array, add to_tuple

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: util.py polish + conformance suite + CLAUDE.md

**Files:**
- Modify: `src/ncca/ngl/util.py`, `CLAUDE.md`
- Create: `tests/test_api_consistency.py`

**Interfaces:**
- Consumes: everything produced by Tasks 1-5.
- Produces: `lerp(a, b, t)` generic over anything supporting `+` and scalar `*`; full type hints on `look_at`, `perspective`, `ortho`, `frustum`, `calc_normal`, `lerp`.

- [ ] **Step 1: Write `tests/test_api_consistency.py`**

Full file:

```python
"""Conformance suite: every math class implements the shared API contract."""

import numpy as np
import pytest

from ncca.ngl import Mat2, Mat3, Mat4, Quaternion, Vec2, Vec3, Vec4

# Sample constructor args producing a distinctive, invertible value per class.
SAMPLES = {
    Vec2: (1.0, 2.0),
    Vec3: (1.0, 2.0, 3.0),
    Vec4: (1.0, 2.0, 3.0, 4.0),
    Mat2: (2.0, 0.0, 0.0, 3.0),
    Mat3: (2.0, 0.0, 0.0, 0.0, 3.0, 0.0, 0.0, 0.0, 4.0),
    Mat4: (
        2.0, 0.0, 0.0, 0.0,
        0.0, 3.0, 0.0, 0.0,
        0.0, 0.0, 4.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ),
    Quaternion: (1.0, 0.5, 0.25, 0.125),
}

ALL_CLASSES = list(SAMPLES)


def make(cls):
    return cls(*SAMPLES[cls])


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_default_constructor(cls):
    assert cls() is not None


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_component_constructor(cls):
    assert make(cls) == make(cls)


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_storage_is_float32(cls):
    assert make(cls)._data.dtype == np.float32


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_copy_is_equal_and_independent(cls):
    a = make(cls)
    b = a.copy()
    assert a == b
    assert a is not b
    assert a._data is not b._data


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_to_numpy_is_a_copy(cls):
    a = make(cls)
    arr = a.to_numpy()
    arr[...] = 99.0
    assert a == make(cls)


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_numpy_round_trip(cls):
    a = make(cls)
    assert cls.from_numpy(a.to_numpy()) == a


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_list_round_trip(cls):
    a = make(cls)
    assert cls.from_list(a.to_list()) == a


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_to_tuple(cls):
    a = make(cls)
    t = a.to_tuple()
    assert isinstance(t, tuple)
    assert all(isinstance(v, float) for v in t)


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_hashable(cls):
    a = make(cls)
    assert hash(a) == hash(a.copy())
    assert a in {a.copy()}


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_eval_repr_round_trip(cls):
    a = make(cls)
    assert eval(repr(a)) == a  # noqa: S307


@pytest.mark.parametrize("cls", ALL_CLASSES)
def test_len_and_iter(cls):
    a = make(cls)
    assert len(a) > 0
    assert all(isinstance(float(v), float) for v in a)


@pytest.mark.parametrize("cls", [Vec2, Vec3, Vec4])
def test_vectors_normalized_is_pure(cls):
    a = make(cls)
    before = a.copy()
    a.normalized()
    assert a == before


@pytest.mark.parametrize("cls", [Mat2, Mat3, Mat4])
def test_matrices_transposed_is_pure(cls):
    a = make(cls)
    before = a.copy()
    a.transposed()
    a.inverse()
    assert a == before


def test_quaternion_normalized_is_pure():
    q = make(Quaternion)
    before = q.copy()
    q.normalized()
    q.conjugate()
    q.inverse()
    assert q == before
```

- [ ] **Step 2: Run it**

Run: `uv run pytest tests/test_api_consistency.py -q`
Expected: PASS (Tasks 1-5 implemented everything). Any failure here is a contract gap — fix the class, not the test.

- [ ] **Step 3: Type-hint and genericise `util.py`**

Add signatures (bodies already updated in Tasks 1-2):
`def look_at(eye: Vec3, look: Vec3, up: Vec3) -> Mat4:`; `def perspective(fov: float, aspect: float, near: float, far: float, mode: PerspMode = PerspMode.OpenGL) -> Mat4:` (match existing parameter list); `def ortho(left: float, right: float, bottom: float, top: float, near: float, far: float, mode: PerspMode = PerspMode.OpenGL) -> Mat4:`; `def frustum(left: float, right: float, bottom: float, top: float, near: float, far: float) -> Mat4:`; `def calc_normal(p1: Vec3, p2: Vec3, p3: Vec3) -> Vec3:`; and

```python
T = TypeVar("T")


def lerp(a: T, b: T, t: float) -> T:
    """Linearly interpolate between a and b at parameter t.

    Works for floats and any type supporting + and scalar * (Vec2/3/4,
    Quaternion, matrices).
    """
    return a + (b - a) * t
```

(Confirm the existing body is equivalent; keep it if so, just add hints.)

- [ ] **Step 4: Update `CLAUDE.md` conventions**

Replace the "API consistency conventions" bullet list's first bullet with:

```markdown
- All math classes (`Vec2/3/4`, `Mat2/3/4`, `Quaternion`) follow one contract:
  numpy `np.float32` storage in `_data`; immutable-style operations returning
  new objects (`normalized()`, `transposed()`, `inverse()`, `clamped()` — only
  `set()` and element assignment mutate); constructors take components with a
  sensible default; `from_list`/`from_numpy` classmethods;
  `copy()`/`to_numpy()`/`to_list()`/`to_tuple()`; `__eq__`/`__hash__`; eval-able
  `__repr__`. `@` is the linear-algebra product; `*` is scalar only.
  `tests/test_api_consistency.py` enforces this — run it when touching math code.
```

- [ ] **Step 5: Lint and commit**

```bash
uv run ruff format src/ tests/ && uv run ruff check src/ tests/
uv run pytest -q
git add -A src tests CLAUDE.md
git commit -m "test(math): add API conformance suite; type-hint util; document contract

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: Full verification sweep

**Files:** none new — fixes only if suites fail.

- [ ] **Step 1: Grep for stragglers**

```bash
grep -rn "get_matrix\|get_transpose\|get_array\|\.null()\|Mat[234]Error\|Mat[234]NotSquare" src/ tests/ examples/ --include="*.py"
```

Expected: no hits in `src/` or `tests/` (hits in `examples/` are out of scope for the library but fix any that are trivial renames). Also check the webgpu stack: `grep -rn "get_matrix\|\.m\b" src/ncca/ngl/webgpu/ src/ncca/ngl/widgets/` and apply the Task 2 mappings to any hits.

- [ ] **Step 2: Run every suite**

```bash
uv run pytest -q                      # default (non-GPU)
uv run pytest -m opengl -q            # real GL context
uv run pytest -m qt -q                # PySide6
uv run pytest -m webgpu -q            # wgpu
uv run pytest --cov=src --cov-report=term-missing -q
uv run pre-commit run --all-files
```

Expected: all PASS. The GPU/Qt suites matter here — shader_program and widgets changed.

- [ ] **Step 3: Final commit (if fixes were needed) and stop**

```bash
git add -A && git commit -m "fix(math): call-site stragglers found by full suite sweep

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

Do not merge to `main` — finishing the branch is a separate decision for the maintainer (superpowers:finishing-a-development-branch).
