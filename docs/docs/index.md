# PyNGL — NCCA Python Graphics Library

PyNGL is a Python port of [NGL](https://github.com/NCCA/NGL), the graphics
library used for teaching 3D computer graphics at the NCCA (Bournemouth
University). It gives you:

- **Math classes** for 3D graphics — `Vec2/3/4`, `Mat2/3/4`, `Quaternion`,
  `Transform`, and helpers such as `look_at` and `perspective`.
- **OpenGL support** — VAO abstractions, shader management (`ShaderLib`),
  primitives, textures, and text rendering.
- **WebGPU support** — a parallel rendering stack built on `wgpu`.
- **Qt widgets** — PySide6 widgets for editing NGL types in GUIs.

## Where to start

1. **[Getting Started](getting_started.md)** — install the library and run
   your first lines of PyNGL code.
2. **[Understanding the Method Names](tutorials/method_names.md)** — *read
   this first!* It explains the one rule that makes the whole math API
   predictable.
3. **[Tutorials](tutorials/index.md)** — in-depth, example-driven guides to
   every math class.
4. **API Reference** — full auto-generated documentation for every class
   (see the *API Reference* section in the navigation).

## The one rule of the math API

> A method ending in **`-ed`** (`normalized()`, `transposed()`, `clamped()`)
> returns a **new** object and leaves the original unchanged. The plain verb
> **`set()`** is the only method that changes the object you call it on.

```python
from ncca.ngl import Vec3

v = Vec3(2.0, 0.0, 0.0)
u = v.normalized()   # u is a NEW unit vector; v is unchanged
print(u)             # [1.0, 0.0, 0.0]
print(v)             # [2.0, 0.0, 0.0]
```

If that surprises you, read the
[grammar guide](tutorials/method_names.md) — it explains why.
