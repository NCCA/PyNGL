# PyNGL — NCCA Python Graphics Library

PyNGL is a Python port of [NGL](https://github.com/NCCA/NGL), the graphics
library used for teaching 3D computer graphics at the NCCA (Bournemouth
University). It gives you:

- **Math classes** for 3D graphics — `Vec2/3/4`, `Mat2/3/4`, `Quaternion`,
  `Transform`, and helpers such as `look_at` and `perspective`.
- **OpenGL support** (`ncca.ngl.opengl`) — VAO abstractions, shader
  management (`ShaderLib`), primitives, textures, and text rendering.
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

## The WebGPU API

Alongside the OpenGL stack, PyNGL ships a parallel renderer built on
[WebGPU](https://gpuweb.github.io/gpuweb/) via the
[`wgpu`](https://wgpu-py.readthedocs.io/) Python package. WebGPU is the
modern successor to OpenGL: instead of a hidden global state machine you
describe your rendering up front as explicit **pipeline** objects (shaders,
vertex layouts, and render state bundled together), then record draw calls
into a command encoder each frame. Shaders are written in
[WGSL](https://www.w3.org/TR/WGSL/) rather than GLSL.

PyNGL wraps this in `ncca.ngl.webgpu`, which exports four things:

- **`WebGPUWidget`** — a PySide6 `QWidget` base class. It renders
  *offscreen* with `wgpu` into a colour buffer that the widget blits to the
  screen, so there is no OpenGL context or swapchain to manage. Subclass it
  and implement `paintWebGPU()` (record and submit your render pass) and
  `resizeWebGPU(w, h)`.
- **`PipelineFactory`** and **`PipelineType`** — a registry of ready-made
  render pipelines (single- or multi-coloured points, lines, triangles,
  triangle strips, and instanced geometry) mirroring the OpenGL
  `VAOFactory` pattern. You can register your own pipeline classes without
  touching library code.
- **`NGLToWebGPU`** — helpers that translate NGL type names into WebGPU
  vertex formats and strides (e.g. `"vec3"` → `"float32x3"`).

All the maths and geometry classes are shared with the OpenGL stack —
`Vec3`, `Mat4`, `look_at`, `perspective`, and `PrimData` work unchanged.
The one difference to remember: WebGPU's clip-space depth runs from 0 to 1
(OpenGL's runs from −1 to 1), so build projection matrices with
`perspective(..., PerspMode.WebGPU)`.

The [WebGPU section](webgpu/index.md) covers the stack in depth:

1. **[Getting Started with WebGPU](webgpu/getting_started.md)** — the
   `WebGPUWidget` lifecycle and a minimal working application.
2. **[The Built-in Pipelines](webgpu/builtin_pipelines.md)** — drawing
   points, lines, triangles, and instanced meshes without writing any
   WGSL, following the bundled `python -m ncca.ngl.webgpu` demo.
3. **[Custom Pipelines](webgpu/custom_pipelines.md)** — your own WGSL
   shaders via `CustomShaderPipeline` or a `BaseWebGPUPipeline` subclass.
4. **[WebGPU API Reference](WebGPU.md)** — every class in the package.
