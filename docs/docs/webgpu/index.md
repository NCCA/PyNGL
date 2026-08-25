# WebGPU in PyNGL

Alongside the OpenGL stack, PyNGL ships a parallel renderer built on
[WebGPU](https://gpuweb.github.io/gpuweb/) via the
[`wgpu`](https://wgpu-py.readthedocs.io/) Python package. WebGPU is the
modern successor to OpenGL: instead of a hidden global state machine you
describe your rendering up front as explicit **pipeline** objects (shaders,
vertex layouts, and render state bundled together), then record draw calls
into a command encoder each frame. Shaders are written in
[WGSL](https://www.w3.org/TR/WGSL/) rather than GLSL.

Everything lives in the `ncca.ngl.webgpu` package, which exports four
things:

- **`WebGPUWidget`** — a PySide6 `QWidget` base class that hosts the
  renderer. It renders *offscreen* with `wgpu` into a colour buffer that
  the widget blits to the screen with `QPainter`, so there is no OpenGL
  context, canvas, or swapchain to manage. Subclass it and implement
  `paintWebGPU()` and `resizeWebGPU(w, h)`.
- **`PipelineFactory`** — a registry that creates ready-made render
  pipelines (points, lines, triangles, triangle strips, and instanced
  geometry), mirroring the OpenGL `VAOFactory` pattern. You can register
  your own pipeline classes without touching library code.
- **`PipelineType`** — the enum of built-in pipeline types the factory
  knows about.
- **`NGLToWebGPU`** — helpers that translate NGL type names into WebGPU
  vertex formats and strides (e.g. `"vec3"` → `"float32x3"`).

All the maths and geometry classes are shared with the OpenGL stack —
`Vec3`, `Mat4`, `look_at`, `perspective`, and `PrimData` work unchanged.

OBJ files are parser-only. Load one with `Obj.from_file()`, then pass it to
`WebGPUMesh`. `standard_mesh_vertex_layout()` describes its interleaved
position, normal and UV buffer (32 bytes per vertex) for a custom pipeline.

!!! warning "One thing to remember"
    WebGPU's clip-space depth runs from 0 to 1, whereas OpenGL's runs from
    −1 to 1. Always build projection matrices with
    `perspective(..., PerspMode.WebGPU)` — with the default (OpenGL) mode
    your geometry will clip or z-fight.

## The pages in this section

1. **[Getting Started with WebGPU](getting_started.md)** — the
   `WebGPUWidget` lifecycle and a minimal working application.
2. **[The Built-in Pipelines](builtin_pipelines.md)** — a tour of all
   fourteen `PipelineType`s and the `set_data` / `update_uniforms` /
   `render` contract, following the bundled demo app.
3. **[Custom Pipelines](custom_pipelines.md)** — writing your own WGSL
   shaders with `CustomShaderPipeline`, or subclassing
   `BaseWebGPUPipeline` and registering it with the factory.
4. **[WebGPU API Reference](../WebGPU.md)** — full auto-generated
   documentation for every class in the package.

## Try it right now

The package ships a demo application that cycles through every built-in
pipeline. If you have the library installed you can run it immediately:

```bash
uv run python -m ncca.ngl.webgpu
```

Use the **Left** / **Right** arrow keys to switch pipelines manually,
**Space** to pause the animation, **A** to toggle automatic switching, and
**Escape** to quit. Its source
([`src/ncca/ngl/webgpu/__main__.py`](https://github.com/NCCA/PyNGL/blob/main/src/ncca/ngl/webgpu/__main__.py))
is the reference example for the built-in pipelines and is walked through
in [The Built-in Pipelines](builtin_pipelines.md).

For larger complete programs — lit meshes, textures, shadows, compute —
see the WebGPU examples in
[PyNGLDemos](https://github.com/NCCA/PyNGLDemos).
