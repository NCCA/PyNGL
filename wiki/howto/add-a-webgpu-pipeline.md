---
sources:
  - src/ncca/ngl/webgpu/pipeline_factory.py
  - src/ncca/ngl/webgpu/base_webgpu_pipeline.py
  - src/ncca/ngl/webgpu/line_pipeline.py
synced: 9c2b6deffde456bb528df654ca6ce5e810d8f3a8
---

# How to Add a WebGPU Pipeline

## Summary

A "pipeline" in the WebGPU stack is a `wgpu.GPURenderPipeline` plus the
buffer/uniform plumbing needed to feed it, wrapped in a subclass of
`BaseWebGPUPipeline`. Adding a new one means implementing a small, fixed
contract of abstract methods, following the existing line pipelines as the
template, and registering the class with `PipelineFactory` so callers never
import the concrete class directly.

## How it works

1. **Subclass `BaseWebGPUPipeline`** (`base_webgpu_pipeline.py:15`), or one of
   its shared bases if applicable (`BasePointPipeline` for billboarded
   quads). The base `__init__` takes `device`, `texture_format`,
   `depth_format`, `msaa_sample_count`, `data_type`, `stride`, and drives
   construction itself: it allocates `uniform_data` from `get_dtype()`,
   calls `_set_default_uniforms()`, then `_create_pipeline()`. Do not
   duplicate that sequence in a subclass — only extend `__init__` to store
   pipeline-specific attributes (buffers, colours) *before* calling
   `super().__init__(...)`, exactly as `line_pipeline.py:19` and
   `line_pipeline.py:65` do.

2. **Implement the nine abstract methods.** `BaseWebGPUPipeline` is an
   `ABC` and is uninstantiable until all of these exist:
   `get_dtype`, `_get_shader_code`, `_get_vertex_buffer_layouts`,
   `_get_primitive_topology`, `_set_default_uniforms`, `_get_pipeline_label`,
   and the public `set_data`, `update_uniforms`, `render`. `line_pipeline.py`
   defines a small `BaseLinePipeline` layer that implements
   `_get_primitive_topology` once (returning a configurable `self._topology`)
   for both its multi- and single-colour subclasses — follow that pattern
   when several variants of a new primitive type share topology logic.

3. **Study `LinePipelineMultiColour`/`LinePipelineSingleColour`
   (`line_pipeline.py:55`, `line_pipeline.py:236`) as the reference pair.**
   They show the standard multi-/single-colour split used by every
   primitive family in this stack: multi-colour carries a second per-vertex
   colour vertex buffer (slot 1, `step_mode: vertex`) and an uninitialised
   `Colour` field in the uniform struct; single-colour has no colour vertex
   buffer and instead stores one `Colour` (+ explicit `padding`) in
   `get_dtype()`'s uniform struct, set via `update_uniforms`/`set_color`.
   Both implement `_set_default_uniforms` as a no-op (`pass`) because the
   MVP/colour fields are written on first `update_uniforms` call, not at
   construction.

4. **Put WGSL shader source in `pipeline_shaders.py`**, not inline in the
   pipeline module. Compose it from the existing `UNIFORMS_*`/`VERTEX_IN_*`
   string fragments where possible and export it as a module-level constant
   (see `LINE_SHADER_MULTI_COLOURED`/`LINE_SHADER_SINGLE_COLOUR`, imported
   into `line_pipeline.py:12`); `_get_shader_code` should just `return` that
   constant.

5. **Use `NGLToWebGPU`** (`webgpu_constants.py`) for stride/format lookups
   in `_get_vertex_buffer_layouts` — never hardcode byte strides. It only
   recognises `vec2/vec3/vec4/mat2/mat3/mat4` (case-insensitive).

6. **Register with `PipelineFactory`.** Add a `PipelineType` enum member in
   `pipeline_factory.py` and call
   `self.register_pipeline(PipelineType.YOUR_TYPE, YourPipelineClass)` in
   `_PipelineFactory.__init__` (`pipeline_factory.py:56` onward shows every
   existing registration). If the new pipeline needs a fixed-configuration
   variant (e.g. one topology baked in), define a small wrapper subclass or
   a `lambda device: YourPipelineClass(device, ...)` and register that,
   mirroring the `TriangleListMultiColour`/`TriangleListSingleColour`
   wrapper classes (`pipeline_factory.py:76-102`). Never have call-site code
   import the concrete pipeline class directly — go through
   `PipelineFactory.create_pipeline(device, pipeline_type, **kwargs)`.

7. **Test it.** Pipeline construction calls real `wgpu` device APIs
   (`create_shader_module`, `create_render_pipeline`, `create_buffer_with_data`),
   so unit tests need the `webgpu` marker and the session's real
   `webgpu_device` fixture (`tests/conftest.py`) — run with
   `uv run pytest -m webgpu`. A plain `uv run pytest` silently skips these
   tests, so a green default run proves nothing about a new pipeline.

## Key invariants

- All nine abstract methods must be implemented or the class cannot be
  instantiated (`ABC`); there is no partial-implementation fallback.
- `get_dtype()`'s field order/sizes/alignment must exactly match the WGSL
  uniform struct — mismatches produce silently wrong GPU-side values, not an
  exception. `Colour` fields need an explicit `padding` float to satisfy
  WGPU's 16-byte alignment; `MVP` is always `float32, (4, 4)`.
- Vertex buffer slot numbers in `_get_vertex_buffer_layouts` must match both
  the `set_vertex_buffer(slot, ...)` calls in `render` and the WGSL
  `@location(n)` bindings.
- `render()` must be a safe no-op (return early) when required buffers are
  still `None` — never raise for "not yet configured".
- New pipeline types integrate exclusively through
  `PipelineFactory.register_pipeline`; hardcoding a concrete class at a
  call site defeats the registry pattern the whole stack relies on.
- `PipelineFactory` is a process-wide singleton — registering the same
  `PipelineType` twice silently overwrites the earlier registration.

## Connections

- [../modules/webgpu.md](../modules/webgpu.md) — full description of the
  pipeline stack this guide is extending.
- [../modules/vao-stack.md](../modules/vao-stack.md) — the OpenGL
  `VAOFactory` registry pattern that `PipelineFactory` deliberately mirrors.
