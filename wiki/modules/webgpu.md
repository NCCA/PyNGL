---
sources:
  - src/ncca/ngl/webgpu/**
synced: cdaf11bb67c017e478348ac5591c0c90634629c7
---

# The WebGPU Pipeline Stack

## Summary

`src/ncca/ngl/webgpu/` is a parallel rendering stack targeting `wgpu` instead
of `OpenGL.GL`, structured to mirror the OpenGL VAO stack's pattern: a common
abstract base (`BaseWebGPUPipeline`) owning buffer/pipeline plumbing,
concrete pipeline classes per primitive type (points, lines, triangles,
point-lists, instanced geometry, user-supplied shaders), and a factory
(`PipelineFactory`) registering them by enum so call sites never import a
concrete pipeline class directly. A Qt widget (`WebGPUWidget`) hosts the
device/surface inside a `QWidget`, and `__main__.py` is a standalone demo
touring every registered pipeline.

## How it works

`BaseWebGPUPipeline` (`base_webgpu_pipeline.py:15`) is constructed with a
`device`, colour/depth texture formats, `msaa_sample_count` (default 4), a
`data_type` string (e.g. `"Vec3"`) and optional explicit `stride` (0 means
infer the stride from `data_type` via `NGLToWebGPU.stride_from_type`). Its
`__init__` allocates `uniform_data` from `get_dtype()`, calls
`_set_default_uniforms()`, then `_create_pipeline()`, which compiles the
WGSL from `_get_shader_code()`, builds the `GPURenderPipeline` (layout
`"auto"`, `depth_write_enabled=True`, `depth_compare=less`), creates the
uniform buffer, and derives the bind group (binding 0) from the pipeline's
own bind-group layout. Subclasses must implement six abstract methods:
`get_dtype`, `_get_shader_code`, `_get_vertex_buffer_layouts`,
`_get_primitive_topology`, `_set_default_uniforms`, `_get_pipeline_label`,
plus the public `set_data`/`update_uniforms`/`render`. Helpers
`_create_or_update_buffer` and `_process_vertex_data` centralise
create-vs-write-buffer logic (a buffer is recreated only if missing or too
small) and numpy-to-vec4 padding for colour attributes.
`BasePointPipeline` extends the base with shared quad-billboard machinery
(`_get_default_vertex_layouts`, `_render_points`) used by the two point
pipelines below.

Concrete pipelines, each with single- and multi-colour variants (multi
takes a per-vertex/per-instance colour buffer; single stores one colour in
the uniform struct):

- `triangle_pipeline.py` — `TrianglePipelineMultiColour`/
  `TrianglePipelineSingleColour`, topology configurable (`triangle_list` or
  `triangle_strip`) via the `topology` constructor arg.
- `line_pipeline.py` — `LinePipelineMultiColour`/`LinePipelineSingleColour`,
  topology `line_list`/`line_strip`.
- `point_pipeline.py` — `PointPipelineMultiColour`/`PointPipelineSingleColour`,
  billboarded quads via `BasePointPipeline` (`triangle_strip`, `step_mode`
  `"instance"`, 4 vertices drawn per instance).
- `point_list_pipeline.py` — `PointListPipelineMultiColour`/
  `PointListPipelineSingleColour`, native `point_list` topology (no
  billboarding), one vertex per point.
- `instanced_geometry_pipeline.py` — `InstancedGeometryPipelineMultiColour`/
  `InstancedGeometryPipelineSingleColour`, renders arbitrary geometry
  (interleaved `x,y,z,nx,ny,nz,u,v`, the same 8-float layout `PrimData`
  produces) once per instance; `set_data` requires `geometry_data` and
  raises `ValueError` (`GEOM_ERROR`) if omitted.
- `custom_shader_pipeline.py` — `CustomShaderPipeline` takes arbitrary WGSL
  source (string or `from_file(device, path)`), a list of `vertex_formats`
  to derive buffer layouts/stride, and a default MVP+colour uniform struct;
  for escape-hatch/demo shaders that don't fit the other pipelines.

`pipeline_shaders.py` holds all WGSL as composed string fragments
(`UNIFORMS_*`, `VERTEX_IN_*`, `LIGHTING_CALCULATION`, `CIRCLE_DISCARD`,
etc.) assembled by a `generate_shader` helper into the exported constants
(`POINT_SHADER_MULTI_COLOURED`, `TRIANGLE_SHADER_SINGLE_COLOUR`, ...) that
each pipeline's `_get_shader_code` returns. `webgpu_constants.py`
(`NGLToWebGPU`) maps NGL type names (`"vec2"/"vec3"/"vec4"/"mat2/3/4"`,
case-insensitive) to byte strides and WGPU `VertexFormat` strings —
the single source of truth both pipelines and demo code use to compute
buffer strides.

`PipelineFactory` (`pipeline_factory.py`, a module-level singleton instance
of `_PipelineFactory`) registers one entry per `PipelineType` enum member at
construction time. An entry is a `PipelineFactoryFn` —
`Callable[..., BaseWebGPUPipeline]` — which in practice is either a pipeline
class or a lambda that binds a fixed keyword. The four topology-pinned
triangle types use the lambda form
(`lambda device, **kwargs: TrianglePipelineMultiColour(device,
topology=..., **kwargs)`) rather than the wrapper subclasses they used to,
because a subclass with a `(self, device)` `__init__` swallowed every other
keyword `create_pipeline` was given — `colour` and `data_type` never reached
the pipeline. The `**kwargs` forwarding in the lambda is the whole point of
it; drop it and those keywords silently vanish again.
`create_pipeline(device, pipeline_type, **kwargs)` looks up the registry and
calls the entry as `factory(device, **kwargs)`, raising `ValueError` for an
unregistered type; `register_pipeline` lets callers add custom types
without touching this module.

`WebGPUWidget` (`webgpu_widget.py`) is an abstract `QWidget` (combined
metaclass `QWidgetABCMeta` so it can be both `ABC` and `QWidget`).
Subclasses implement `resizeWebGPU`/`paintWebGPU`; the widget owns a numpy
`frame_buffer`, an update `QTimer`, and `_create_render_buffer` which
allocates the resolve-target colour texture, an MSAA texture
(`msaa_sample_count`, default 4), a depth texture
(`wgpu.TextureFormat.depth24plus`), and a *ring* of `NUM_READBACK_BUFFERS`
(2) row-aligned readback buffers for copying the rendered texture back to
CPU memory for `QPainter` to blit via `_present_image`.

The ring is what makes the read-back cheap. `_update_colour_buffer` copies
the current frame into `readback_buffers[write_idx]` and submits without
waiting, then maps the *other* buffer — last frame's — and strides the
padded rows into `frame_buffer`. Because the GPU has had a whole frame to
finish that copy, `map_sync` returns almost immediately instead of stalling
on the copy just submitted. `_readback_pending` tracks which slots hold a
frame, so the first frame after startup or a resize simply has nothing to
read and shows the previous contents once. `_readback_index` then flips to
the buffer just drained, which is what guarantees a buffer is never mapped
while it is the copy target.

Row alignment is spec, not a per-GPU quirk: `copy_texture_to_buffer`
requires `bytes_per_row` to be a multiple of `COPY_BYTES_PER_ROW_ALIGNMENT`
(256), so `_calculate_aligned_row_size` rounds up and the read side rebuilds
the image with `np.lib.stride_tricks.as_strided` to skip the padding.

`_create_render_pass` wires the MSAA texture as the
render target with `resolve_target` set to the plain colour texture, clear
colour from `self.background_colour`, and a depth-stencil attachment
cleared to `1.0`.

`__main__.py` (`ncca.ngl.webgpu.__main__`) is a standalone demo (`uv run
--script`) that builds a `WebGPUWidget` subclass, initialises a device via
`wgpu.utils.get_default_device()`, and cycles through every
`PipelineFactory`-registered `PipelineType`, giving each one a distinct
background colour for visual identification while animating an MVP matrix.

## Key invariants

- Every concrete pipeline must implement all nine `BaseWebGPUPipeline`
  abstract methods; the class is otherwise uninstantiable (`ABC`).
- `uniform_data`'s dtype (`get_dtype()`) must exactly match the WGSL
  uniform struct's field order/sizes/alignment — vec3 uniforms are always
  followed by explicit `padding` fields to satisfy WGPU's 16-byte
  uniform-struct alignment rules (see `Colour`/`padding` pairs across
  triangle/line/point-list single-colour pipelines).
  Getting this out of sync produces silently wrong GPU-side values, not an
  exception.
  `Colour` fields are 3 floats + 1 float padding; `MVP`/`ViewMatrix`/
  `instance_transform` are always `float32, (4, 4)`.
- Vertex buffer slot indices in `_get_vertex_buffer_layouts` must match the
  `set_vertex_buffer(slot, ...)` calls in `render` and the WGSL
  `@location(n)` bindings — e.g. instanced geometry always uses slots
  0=position, 1=colour, 2=instance_id, 3=interleaved geometry
  (locations 3/4/5).
- `render()` on any pipeline is a safe no-op (returns early) if required
  buffers are `None` — it never raises for "not yet configured".
- `msaa_sample_count` (default 4) and `depth_format`
  (`depth24plus`)/`texture_format` (`rgba8unorm`) are fixed at pipeline
  construction; changing them requires rebuilding the pipeline, not
  patching an attribute.
- `PipelineFactory` is a process-wide singleton (`PipelineFactory =
  _PipelineFactory()`) — registering a `PipelineType` twice silently
  overwrites the earlier registration (`SINGLE_COLOUR_TRIANGLES` is still
  registered twice in `pipeline_factory.py`, the later winning).
- Anything registered with `register_pipeline` is called as
  `factory(device, **kwargs)`. A callable that does not accept and forward
  `**kwargs` will silently drop every keyword `create_pipeline` was given
  rather than raising — this is exactly how the old topology wrapper
  subclasses lost `colour`.
- `_update_colour_buffer` raises `RuntimeError` rather than degrading if
  `readback_buffers` is missing: a subclass overriding
  `_create_render_buffer` must call `super()._create_render_buffer()` or
  otherwise build the ring. The deliberate loudness is because the
  surrounding `try/except` would otherwise swallow the `AttributeError`
  every frame, leaving a grey window and no clue why.
- New pipeline types integrate via `PipelineFactory.register_pipeline`,
  never by hardcoding a concrete pipeline class at a call site that should
  stay type-agnostic (same convention as `VAOFactory` in the OpenGL stack).
- `NGLToWebGPU` type-name lookups are case-insensitive but only recognise
  `vec2/vec3/vec4/mat2/mat3/mat4` — anything else raises `KeyError`.

## Connections

- [vao-stack.md](vao-stack.md) — the OpenGL equivalent; `PipelineFactory`
  deliberately mirrors `VAOFactory`'s registry pattern.
- [shaders.md](shaders.md) — the OpenGL shader/uniform layer this stack
  parallels for the `wgpu` backend.
- [../architecture/overview.md](../architecture/overview.md) — where this
  package sits in the overall module layout.
