# Custom Pipelines

The [built-in pipelines](builtin_pipelines.md) only do flat colour. As
soon as you want lighting, textures, or your own per-vertex attributes you
need your own [WGSL](https://www.w3.org/TR/WGSL/) shader. There are two
routes, in increasing order of control:

1. **`CustomShaderPipeline`** — supply WGSL source and vertex formats;
   the library handles buffers, uniforms, and pipeline creation.
2. **Subclass `BaseWebGPUPipeline`** — full control over vertex layouts,
   uniform structures, and rendering, with the buffer-management
   boilerplate inherited.

Neither class is re-exported from `ncca.ngl.webgpu`, so import them from
their modules:

```python
from ncca.ngl.webgpu.custom_shader_pipeline import CustomShaderPipeline
from ncca.ngl.webgpu.base_webgpu_pipeline import BaseWebGPUPipeline
```

## Route 1: `CustomShaderPipeline`

Give it WGSL source with `vertex_main` and `fragment_main` entry points
and a list of vertex formats. Each format becomes its own vertex buffer,
bound at successive `@location`s:

```python
import numpy as np
import wgpu

from ncca.ngl.webgpu.custom_shader_pipeline import CustomShaderPipeline

SHADER = """
struct Uniforms {
    MVP : mat4x4<f32>,
    colour : vec4<f32>,
};
@group(0) @binding(0) var<uniform> uniforms : Uniforms;

struct VertexOut {
    @builtin(position) position : vec4<f32>,
    @location(0) colour : vec3<f32>,
};

@vertex
fn vertex_main(
    @location(0) position : vec3<f32>,
    @location(1) colour : vec3<f32>,
) -> VertexOut {
    var out : VertexOut;
    out.position = uniforms.MVP * vec4<f32>(position, 1.0);
    out.colour = colour;
    return out;
}

@fragment
fn fragment_main(in : VertexOut) -> @location(0) vec4<f32> {
    return vec4<f32>(in.colour, 1.0) * uniforms.colour;
}
"""

pipeline = CustomShaderPipeline(
    device=self.device,
    shader_source=SHADER,
    vertex_formats=["Vec3", "Vec3"],   # position at @location(0), colour at @location(1)
    primitive_topology=wgpu.PrimitiveTopology.triangle_list,
)

# per frame — same contract as the built-ins
pipeline.set_data(positions=positions, colours=colours)
pipeline.update_uniforms(mvp=mvp, colour=np.array([1, 1, 1, 1], dtype=np.float32))
pipeline.render(render_pass)
```

Details worth knowing:

- The uniform buffer at `@group(0) @binding(0)` is a `mat4x4` MVP plus a
  `vec4` colour — match that struct in your WGSL. `update_uniforms`
  accepts `mvp=` and `colour=` (RGB is padded to RGBA for you).
- `set_data` uploads `positions=` and `colours=` to bindings 0 and 1, and
  any extra keyword arrays (e.g. `velocities=...`) to the bindings after
  them, in order. Alternatively pass a single `interleaved_data=` array
  when `vertex_formats` has one entry.
- Constructor keywords let you change topology, texture/depth formats, and
  MSAA count; the defaults match what `WebGPUWidget` sets up
  (`rgba8unorm`, `depth24plus`, 4 samples).

## Route 2: subclass `BaseWebGPUPipeline`

For full control — your own uniform structure, interleaved layouts,
instancing — subclass `BaseWebGPUPipeline` and implement its abstract
methods. This is exactly how the built-in pipelines are written, so
[`point_pipeline.py`, `triangle_pipeline.py`, and friends](https://github.com/NCCA/PyNGL/tree/main/src/ncca/ngl/webgpu)
are working reference implementations.

You must implement:

| Method | Returns |
|---|---|
| `get_dtype()` | numpy structured dtype mirroring your WGSL uniform struct |
| `_get_shader_code()` | the WGSL source (entry points `vertex_main` / `fragment_main`) |
| `_get_vertex_buffer_layouts()` | list of wgpu vertex-buffer layout dicts |
| `_get_primitive_topology()` | a `wgpu.PrimitiveTopology` |
| `_set_default_uniforms()` | nothing — fill `self.uniform_data` with defaults |
| `_get_pipeline_label()` | debug label string |
| `set_data(**kwargs)` | nothing — upload vertex data |
| `update_uniforms(**kwargs)` | nothing — write `self.uniform_data` fields and upload |
| `render(render_pass, **kwargs)` | nothing — bind and draw |

The base class then builds the render pipeline, uniform buffer, and bind
group for you, and provides `_create_or_update_buffer(...)` /
`_process_vertex_data(...)` so per-frame uploads reuse buffers instead of
reallocating.

A sketch of the shape:

```python
class MyPipeline(BaseWebGPUPipeline):
    def get_dtype(self):
        return np.dtype([
            ("MVP", np.float32, (4, 4)),
            ("colour", np.float32, 4),
        ])

    def _get_shader_code(self):
        return MY_WGSL_SOURCE

    def _get_vertex_buffer_layouts(self):
        return [{
            "array_stride": NGLToWebGPU.stride_from_type("Vec3"),
            "step_mode": "vertex",
            "attributes": [{
                "format": NGLToWebGPU.vertex_format("Vec3"),
                "offset": 0,
                "shader_location": 0,
            }],
        }]

    def _get_primitive_topology(self):
        return wgpu.PrimitiveTopology.triangle_list

    def _set_default_uniforms(self):
        self.uniform_data["MVP"] = np.eye(4, dtype=np.float32)
        self.uniform_data["colour"] = np.array([1, 1, 1, 1], dtype=np.float32)

    def _get_pipeline_label(self):
        return "MyPipeline"

    def set_data(self, positions=None, **kwargs):
        self.vertex_buffer, _ = self._create_or_update_buffer(
            getattr(self, "vertex_buffer", None), positions,
            wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST, "my_vertices",
        )
        self.num_vertices = len(positions)

    def update_uniforms(self, mvp=None, colour=None, **kwargs):
        if mvp is not None:
            self.uniform_data["MVP"] = mvp
        if colour is not None:
            self.uniform_data["colour"] = colour
        self.device.queue.write_buffer(self.uniform_buffer, 0, self.uniform_data.tobytes())

    def render(self, render_pass, **kwargs):
        render_pass.set_pipeline(self.pipeline)
        render_pass.set_bind_group(0, self.bind_group, [], 0, 999999)
        render_pass.set_vertex_buffer(0, self.vertex_buffer)
        render_pass.draw(self.num_vertices)
```

Instantiate it directly (`MyPipeline(self.device)`), or register it with
the factory to swap it in wherever a built-in type is requested:

```python
from ncca.ngl.webgpu import PipelineFactory, PipelineType

PipelineFactory.register_pipeline(PipelineType.MULTI_COLOURED_TRIANGLES, MyPipeline)
```

## Uniform layout: mind the padding

WGSL uniform structs follow WebGPU's alignment rules, and your numpy
dtype must match **byte for byte**:

- A `vec3<f32>` field is aligned to 16 bytes — follow it with a
  4-byte padding field in the dtype (the built-ins use e.g.
  `("Colour", "float32", 3), ("padding", "float32")`).
- A `mat3x3<f32>` is stored as three *padded* columns — 12 floats, not 9
  (`NGLToWebGPU.stride_from_type("mat3")` returns 48 bytes). The demos
  simply use `mat4x4` for normal matrices to sidestep this.
- The whole struct is padded to a 16-byte multiple.

If your rendering is subtly wrong — colours shifted, matrices sheared —
mismatched uniform padding is the first thing to check.

## Vertex format helpers

`NGLToWebGPU` (exported from `ncca.ngl.webgpu`) maps NGL type names to
the WebGPU values used in vertex layouts:

```python
NGLToWebGPU.stride_from_type("vec3")   # 12  (bytes)
NGLToWebGPU.vertex_format("vec3")      # "float32x3"
```

## Complete examples

The [PyNGLDemos](https://github.com/NCCA/PyNGLDemos) repository contains
full custom-pipeline programs: `SimpleWebGPU` (a PBR-shaded teapot with a
checkerboard floor — its `TeapotPipeline.py` is the canonical custom
pipeline class), `TextureWebGPU`, `WebGPUShadows`, and compute-shader
examples under `WebGPUCompute`.
