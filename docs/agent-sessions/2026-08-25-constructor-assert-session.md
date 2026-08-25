# 2026-08-25 -- Self-comparing assertion in the API conformance suite

## Goal

Sonar flagged `test_component_constructor` in `tests/test_api_consistency.py`:
the assertion compared an expression against itself, so it could never fail for
the reason the test name suggests.

## What was wrong

```python
def test_component_constructor(cls):
    assert make(cls) == make(cls)
```

`make(cls)` builds `cls(*SAMPLES[cls])`, so both sides are the same call. The
test only proves that `__eq__` is reflexive -- and every class here stores
`np.float32` in `_data` and compares elementwise, so that holds whatever the
constructor did with the arguments. Swap two components inside any constructor
and this still passes. Reflexivity is already covered by
`test_copy_is_equal_and_independent` and `test_hashable`.

## The fix

Compare against the sample values the object was built from:

```python
def test_component_constructor(cls):
    assert make(cls).to_tuple() == SAMPLES[cls]
```

`to_tuple()` returns the flat components in constructor order for all seven
classes -- vectors, the row-major matrices, and `Quaternion` (s, x, y, z) --
so one assertion covers the whole parametrised set. The sample values
(0.125 .. 4.0) are all exactly representable in `float32`, so the equality is
exact and not a tolerance question.

## Files changed

- `tests/test_api_consistency.py`

## Commands run

```bash
uv run pytest tests/test_api_consistency.py -q   # 105 passed
uv run pytest -q                                 # 628 passed, 500 deselected
uv run ruff format --check tests/test_api_consistency.py
uv run ruff check tests/test_api_consistency.py
```
