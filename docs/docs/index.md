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

A minimal application looks like this:

```python
import wgpu
from wgpu.utils import get_default_device

from ncca.ngl import Mat4, PerspMode, Vec3, look_at, perspective
from ncca.ngl.webgpu import PipelineFactory, PipelineType, WebGPUWidget


class Scene(WebGPUWidget):
    def __init__(self):
        super().__init__()
        self.device = get_default_device()
        self._create_render_buffer()
        self.project = perspective(45.0, 1.0, 0.1, 100.0, PerspMode.WebGPU)
        self.view = look_at(Vec3(0, 2, 4), Vec3(0, 0, 0), Vec3(0, 1, 0))
        self.pipeline = PipelineFactory.create_pipeline(
            self.device, PipelineType.MULTI_COLOURED_TRIANGLES
        )

    def paintWebGPU(self):
        encoder = self.device.create_command_encoder()
        render_pass = encoder.begin_render_pass(
            color_attachments=[{
                "view": self.multisample_texture_view,
                "resolve_target": self.colour_buffer_texture_view,
                "load_op": wgpu.LoadOp.clear,
                "store_op": wgpu.StoreOp.store,
                "clear_value": (0.3, 0.3, 0.3, 1.0),
            }]
        )
        self.pipeline.update_uniforms(mvp=self.project @ self.view)
        self.pipeline.render(render_pass)
        render_pass.end()
        self.device.queue.submit([encoder.finish()])
        self._update_colour_buffer()  # copy the GPU image into the widget

    def resizeWebGPU(self, w, h):
        self.project = perspective(
            45.0, w / max(h, 1), 0.1, 100.0, PerspMode.WebGPU
        )
```

For lit meshes or custom effects you write your own WGSL shader and
pipeline class (subclass `BaseWebGPUPipeline`, or a plain class) — see the
WebGPU examples in
[PyNGLDemos](https://github.com/NCCA/PyNGLDemos) for complete working
programs, from a minimal triangle to textured and shadowed scenes.
