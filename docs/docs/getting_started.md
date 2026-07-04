# Getting Started

## Installation

PyNGL is managed with [uv](https://docs.astral.sh/uv/). Clone the repository
and let `uv` set everything up:

```bash
git clone https://github.com/NCCA/PyNGL
cd PyNGL
uv sync
```

Everything is run through `uv run`, so you never need to activate a virtual
environment yourself:

```bash
uv run python          # a Python shell with ncca.ngl available
uv run pytest          # run the (non-GPU) test suite
```

## Your first PyNGL code

The whole library lives in one module, `ncca.ngl`. Every class is imported
from the same place:

```python
from ncca.ngl import Vec3, Mat4, Quaternion

# vectors behave like mathematical values
a = Vec3(1.0, 0.0, 0.0)
b = Vec3(0.0, 1.0, 0.0)

print(a + b)          # [1.0, 1.0, 0.0]
print(a.dot(b))       # 0.0
print(a.cross(b))     # [0.0, 0.0, 1.0]

# matrices are built with named class methods
m = Mat4.rotate_y(45.0)          # angles are in degrees
q = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), 45.0)
```

## Three things to know before you write more code

**1. Methods ending in `-ed` return a new object.** `v.normalized()` does
*not* change `v` — it hands you a new vector. You must keep the result:

```python
v = Vec3(2.0, 0.0, 0.0)
v = v.normalized()     # assign the result back if you want v to change
```

This is the most important convention in the library. Read
[Understanding the Method Names](tutorials/method_names.md) for the full
story.

**2. `@` multiplies, `*` scales.** Matrix–matrix and matrix–vector products
use Python's `@` operator. `*` is only for scaling by a number:

```python
m = Mat4.rotate_x(45.0) @ Mat4.rotate_y(90.0)   # combine two rotations
v2 = v * 3.0                                    # scale a vector
```

**3. Angles are in degrees.** Everywhere in PyNGL — `Mat4.rotate_x(90.0)`,
`Quaternion.from_axis_angle(axis, 90.0)`, `Transform.set_rotation(...)` —
angles are degrees, not radians.

## Where next?

Work through the [tutorials](tutorials/index.md) in order — they build from
vectors up to full camera and transformation pipelines, with runnable
examples throughout.
