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
uv run src/ncca/ngl/webgpu # run webgpu pipline demos
uv run src/ncca/ngl/widgets # run Qt widgets demos
```

## Your first PyNGL code

The math and geometry-data classes all live in one module, `ncca.ngl`, and
are imported from the same place:

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

## Core Principles of PyNGL

**1. Methods ending in `-ed` return a new object.** `v.normalized()` does
*not* change `v` it returns you a new vector. You must assign the result to a variable :

```python
v = Vec3(2.0, 0.0, 0.0)
v = v.normalized()     # assign the result back if you want v to change
```

This is the most important convention in the library. Read
[Understanding the Method Names](tutorials/method_names.md) for more details. 

**2. `@` multiplies, `*` scales.** Matrix -> matrix and matrix -> vector products
use Python's `@` operator `*` is only for scaling by a number.

```python
m = Mat4.rotate_x(45.0) @ Mat4.rotate_y(90.0)   # combine two rotations
v2 = v * 3.0                                    # scale a vector
```

**3. Angles are in degrees.**  in PyNGL so all rotation type methods such as  `Mat4.rotate_x(90.0)`,
`Quaternion.from_axis_angle(axis, 90.0)`, `Transform.set_rotation(...)` pass the values in degrees.

## OpenGL and WebGPU classes live in their own sub-modules

Anything that talks directly to OpenGL — `ShaderLib`, the VAO classes,
`Primitives`, `BaseMesh`, `Texture`, `Text`, `PySideEventHandlingMixin` — is
imported from `ncca.ngl.opengl`, not `ncca.ngl`:

```python
from ncca.ngl.opengl import ShaderLib, Primitives
```

The WebGPU stack is similarly namespaced under `ncca.ngl.webgpu`. See the
*API Reference* section for the full class-by-class breakdown.

## Where next?

Work through the [tutorials](tutorials/index.md) in order — they build from
vectors up to full camera and transformation pipelines, with runnable
examples throughout.
