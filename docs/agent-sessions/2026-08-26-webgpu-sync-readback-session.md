# 2026-08-26 — Present the frame we just drew

## Goal

In PyNGLDemos, `ViewToWorldTransform/main_webgpu.py` shift-click places a cube in
world space, and the cube did not appear until the *next* click. The unprojection
maths was fine — the cube was in the right place all along, it just wasn't on
screen yet. The root cause sits here in the library, so the fix belongs here.

## Background

`WebGPUWidget._update_colour_buffer` read the frame back through a pipelined ring
of two buffers: copy the current frame into one buffer, map and read the *other*,
which holds the previous frame. Mapping a copy the GPU has had a whole frame to
finish returns almost immediately, so the CPU never stalls — but what reaches the
widget is always frame N-1.

That was documented on the class as "imperceptible at interactive rates", and it
is, so long as something is driving continuous repaints. About forty of the
forty-six WebGPU demos only repaint in response to an event, and were all quietly
a frame behind. It only became visible in `ViewToWorldTransform` because that demo
is precisely about one discrete click changing the picture, so there was no
following frame to hide the lag.

Confirmed with a headless probe that paints, counts non-background pixels, and
paints again (`non-background pixels` on the click's own paint):

```
pipelined (before)      cube pixels on the click's own paint =      0  NOT VISIBLE
synchronous (after)     cube pixels on the click's own paint =  10816  VISIBLE
```

## Changes

`src/ncca/ngl/webgpu/webgpu_widget.py`:

- New `pipelined_readback` attribute, defaulting to `False`. The one line that
  matters is the choice of `read_idx` in `_update_colour_buffer`: synchronously it
  is `write_idx`, the buffer the copy was just submitted into, so `map_sync` waits
  for the GPU and the widget shows the frame it just drew. Pipelined it is the
  other buffer, exactly as before.
- The ring invariant still holds both ways — a buffer is only mapped when nothing
  is copying into it. Pipelined the alternation guarantees it; synchronously the
  copy completes before the map returns and the unmap happens in the same call. No
  change to `_create_render_buffer`, and `NUM_READBACK_BUFFERS` stays at 2; the
  second buffer simply goes unused when pipelining is off.
- Class docstring, `_update_colour_buffer` docstring and the `render_text` caveat
  about text swimming during fast motion all rewritten — that caveat only applies
  on the pipelined path now.

I defaulted it off rather than on. Correctness by default seemed the better trade
given how few demos animate continuously, and the cost is small — measured on the
demo at several window sizes, the synchronous path is about 1.3ms per frame dearer,
under 9% of a 60fps budget even at 1080p:

```
window             sync   pipelined    delta  % of 16.7ms
800x600         1.74ms       0.46ms    1.28ms        7.7%
1024x720        1.87ms       0.52ms    1.35ms        8.1%
1920x1080       2.65ms       1.20ms    1.45ms        8.7%
2560x1440       1.89ms       1.13ms    0.76ms        4.5%
```

The delta is the GPU drain latency rather than bandwidth, so it stays roughly flat
as the window grows. Nothing in PyNGLDemos needed to opt back in: the timer-driven
demos render trivial scenes far above 60fps, and several of them can pause their
animation from the keyboard, which would put them right back to showing a stale
frame.

`tests/test_webgpu_widget.py`: four new tests over a fake device/ring, covering the
default, which buffer each mode maps, and the never-mapped-while-copying invariant
across ten frames in both modes. Checked they bite by forcing the old always-pipelined
behaviour — `test_synchronous_readback_maps_the_frame_it_just_copied` fails, as it
should.

## Commands

```bash
uv run pytest -q            # 628 passed
uv run pytest -m qt -q      # 289 passed
uv run pytest -m webgpu -q  # 123 passed
uv run ruff check --select I ; uv run ruff format --check ; uv run ruff check   # clean
```

Demo-side check against this branch with
`PYTHONPATH=/Users/jmacey/teaching/Code/PyNGL/.worktrees/webgpu-sync-readback/src`:
`ViewToWorldTransform`, `SimpleWebGPU`, `WebGPUShadows`, `Instancing`, `ShadedGrid`
and `Collisions/SphereSphere` all smoketest green, event-driven and timer-driven
alike. `SimpleWebGPU` and `WebGPUShadows` have to be run from their own folders —
they open their `.wgsl` by relative path, which is pre-existing and nothing to do
with this change.

One incidental improvement: the first painted frame used to show the zeroed
`frame_buffer` before the ring filled, a brief flash on startup and after every
resize. Synchronously there is nothing to fill, so it's gone.
