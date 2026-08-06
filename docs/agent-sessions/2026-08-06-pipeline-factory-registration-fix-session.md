# 2026-08-06 — Fix duplicate/clobbered registrations in PipelineFactory

## Goal

A code review of `src/ncca/ngl/webgpu/pipeline_factory.py` flagged that
`_PipelineFactory.__init__` registered triangle topology pipelines twice —
once as wrapper classes, once as lambdas overwriting those same
registrations — and that the lambdas didn't match the registry's declared
type or `create_pipeline`'s `**kwargs` contract. Verified the finding against
the source and fixed it.

## Background

For each of `TRIANGLE_LIST_MULTI_COLOURED`, `TRIANGLE_LIST_SINGLE_COLOUR`,
`TRIANGLE_STRIP_MULTI_COLOURED`, `TRIANGLE_STRIP_SINGLE_COLOUR`, the factory
built a private wrapper class (`TriangleListMultiColour`, etc.), registered
it, then immediately re-registered the same `PipelineType` with a
`lambda device: TrianglePipelineXColour(device, topology=...)` — making the
wrapper classes dead code. `SINGLE_COLOUR_TRIANGLES` was also registered
twice with the same class (harmless but redundant).

The registry was typed `Dict[PipelineType, Type[BasePipeline]]`, but those
four lambdas are callables, not classes — a real type/API mismatch.
`create_pipeline(device, pipeline_type, **kwargs)` calls
`pipeline_class(device, **kwargs)`; because the lambdas only accepted
`device`, any kwarg (e.g. `colour`, `data_type`, `msaa_sample_count`) raised
`TypeError` for those four pipeline types specifically, while working fine
for every other registered type. Confirmed by checking
`TrianglePipelineMultiColour`/`TrianglePipelineSingleColour.__init__` in
`triangle_pipeline.py`, which do accept those kwargs.

## Changes

`src/ncca/ngl/webgpu/pipeline_factory.py`:

- Removed the four dead wrapper classes and the duplicate
  `SINGLE_COLOUR_TRIANGLES` registration.
- Replaced the four triangle-topology lambdas with `lambda device, **kwargs:
  ...(device, topology=..., **kwargs)` so pipeline-specific kwargs reach the
  underlying class.
- Added a `PipelineFactoryFn = Callable[..., BaseWebGPUPipeline]` alias and
  retyped the registry (`Dict[PipelineType, PipelineFactoryFn]`) and
  `register_pipeline`'s parameter to match what's actually stored — a class
  or a factory callable — instead of the previously-inaccurate
  `Type[BasePipeline]`.
- Every `PipelineType` member is now registered exactly once.

`tests/test_webgpu_pipelines.py` (additions):

- `test_topology_pinned_triangle_pipelines_forward_kwargs` — parametrized
  over the four topology-pinned types, asserts `data_type` and
  `msaa_sample_count` kwargs reach the created pipeline.
- `test_topology_pinned_single_colour_triangle_forwards_colour_kwarg` —
  regression test for the exact bug: `colour=...` used to raise `TypeError`
  through `TRIANGLE_LIST_SINGLE_COLOUR`.
- `test_all_pipeline_types_registered_exactly_once` — asserts the registry's
  key set equals `set(PipelineType)`, guarding against a future registration
  silently overwriting another.

## Commands

```bash
uv run pytest                 # 621 passed, 494 deselected (default, non-GPU)
uv run pytest -m webgpu       # 123 passed, 992 deselected
uv run ruff check src/ncca/ngl/webgpu/pipeline_factory.py tests/test_webgpu_pipelines.py
uv run ruff format src/ncca/ngl/webgpu/pipeline_factory.py tests/test_webgpu_pipelines.py
```

No public API surface changed (`PipelineFactory`, `PipelineType`,
`register_pipeline`, `create_pipeline` all keep their names and behaviour for
existing callers), so no docs/nav updates were needed.

Work done on branch `agent/pipeline-factory-fix` in worktree
`.worktrees/pipeline-factory-fix/`, off `Version1.0` (commit `46a62f7`).
