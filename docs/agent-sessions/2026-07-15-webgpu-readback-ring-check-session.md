# 2026-07-15 — Fail loudly on a missing WebGPU read-back ring

## Goal

While migrating the PyNGLDemos WebGPU demos onto this library's `WebGPUWidget`,
a whole class of demo turned up grey with no obvious cause. The root cause sits
here in the library, so the fix belongs here: make the failure visible instead
of hiding it.

## Background

`WebGPUWidget._update_colour_buffer` reads back the rendered frame through a
pipelined ring of buffers (`readback_buffers`, `_readback_index`,
`_readback_pending`), which only `_create_render_buffer` creates. A subclass
that overrides `_create_render_buffer` — to add its own render targets — and
forgets to build the ring (or to call `super()`) hit an `AttributeError` on the
ring attributes inside the method's `try/except`. That was swallowed every frame
and the window just filled grey (128), with only a one-line `print` to stdout.

## Changes

`src/ncca/ngl/webgpu/webgpu_widget.py`:

- Guard the ring before the copy-back and raise a `RuntimeError` naming the fix
  (call `super()._create_render_buffer()`), so the mistake fails on the first
  frame with an actionable message rather than going quietly grey.
- Replace the bare `print` in the fallback path with `logging.exception`, so a
  genuine (usually transient) copy-back failure is logged with a traceback and
  is actually visible, while still falling back to a grey frame rather than
  tearing down the event loop.

`tests/test_webgpu_widget.py` (new): a headless subclass that never builds the
ring, covering both paths — missing ring raises `RuntimeError`, and a copy-back
failure once the ring exists is logged and grey-filled.

## Commands

```bash
uv run pytest -q            # 620 passed (default selection)
uv run pytest -m qt -q      # 278 passed (Qt widget tests)
uv run ruff check --select I ; uv run ruff format   # enforced gate, clean
```

The change adds no new pydocstyle/annotation warnings over the file's
pre-existing ones. Verified against the demos (OIT, SimpleCompute, Blending):
they run with no ring error and no read-back failures; the guard does not
misfire on healthy demos.
