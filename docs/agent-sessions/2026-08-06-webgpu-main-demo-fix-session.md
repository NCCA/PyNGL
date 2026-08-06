# 2026-08-06 — Port the WebGPU `__main__.py` demo to the double-buffered widget API

## Goal

`uv run -m ncca.ngl.webgpu` crashed immediately with `TypeError:
WebGPUWidget.__init__() got an unexpected keyword argument
'background_colour'`, surfaced while smoke-testing the unrelated
`PipelineFactory` registration fix in a sibling worktree. Not caused by that
fix — root-caused and repaired separately.

## Background

`src/ncca/ngl/webgpu/webgpu_widget.py` was rewritten for double buffering in
`45f5c91` (2026-07-15): `WebGPUWidget.__init__()` now takes no arguments and
has no `background_colour` concept, render targets are created via
`_create_render_buffer()`, and every `paintWebGPU()` implementation must
call `_update_colour_buffer()` at the end to drive the read-back ring
(enforced loudly since `b866e4d`). `src/ncca/ngl/webgpu/__main__.py` — the
standalone pipeline-tour demo — predates that rewrite and was never ported:
its `WebGPUScene.__init__` still passed `background_colour=...` to
`super().__init__()`, and its `paintWebGPU` called
`self._create_render_pass(command_encoder)`, a method that doesn't exist
anywhere in the codebase. Past the constructor crash it would have hit that
`AttributeError` on the first paint, and even past that would never have
called `_update_colour_buffer()`, so the window would have stayed blank.

## Changes

`src/ncca/ngl/webgpu/__main__.py`:

- `WebGPUScene.__init__` no longer takes/forwards `background_colour`;
  `main()` no longer passes it.
- Dropped the dead `self.pipeline_backgrounds = {}` (assigned, never read)
  and the redundant `_create_render_buffer` override that only delegated to
  `super()`.
- `paintWebGPU` now builds the render pass directly with
  `command_encoder.begin_render_pass(...)` against
  `self.multisample_texture_view` (colour, MSAA) /
  `self.colour_buffer_texture_view` (resolve target) /
  `self.depth_buffer_view` (depth, matching the pipelines' `depth24plus`
  attachment) instead of the missing `_create_render_pass` helper. Each
  pipeline's stored background colour is passed straight through as
  `clear_value` rather than round-tripped through a `self.background_colour`
  attribute that no longer exists on the base class.
- Added the required `self._update_colour_buffer()` call at the end of the
  try block so the frame is actually read back and presented.

## Commands

```bash
uv run pytest                 # 620 passed, 489 deselected (default, non-GPU)
uv run pytest -m webgpu       # 118 passed, 991 deselected
uv run pytest -m qt           # 278 passed, 831 deselected
uv run ruff check src/ncca/ngl/webgpu/__main__.py     # clean
uv run ruff format --check src/ncca/ngl/webgpu/__main__.py  # clean
```

Manually smoke-tested by driving `WebGPUScene` headed for 16s (matches the
`BlankWebGPU` demo's smoketest pattern): device init, all 14 `PipelineType`
values auto-cycled via the 1s pipeline timer (points, lines, triangles,
triangle list/strip, point list, instanced geometry — multi- and
single-colour variants of each), and a mid-run `resize()`. No exceptions, no
read-back-ring errors, clean exit code 0 throughout.

No public API changed (`WebGPUScene` is local to this `__main__.py`, not
re-exported), so no docs/nav updates were needed.

Work done on branch `agent/webgpu-main-demo-fix` in worktree
`.worktrees/webgpu-main-demo-fix/`, off `Version1.0` (commit `46a62f7`) —
independent of the sibling `agent/pipeline-factory-fix` branch.
