# Getting Started with WebGPU

This page walks through the `WebGPUWidget` lifecycle and builds a minimal
application from scratch. It assumes you have already
[installed PyNGL](../getting_started.md) along with the `wgpu` and
`PySide6` packages.

## How the widget works

`WebGPUWidget` is an abstract PySide6 `QWidget`. Unlike an OpenGL widget
there is no window-system surface: the widget renders **offscreen**.

Each frame goes through these steps:

1. Qt delivers a paint event and the widget calls your `paintWebGPU()`
   override.
2. Your code records a render pass into a command encoder and submits it.
   The pass draws into a multisampled texture that resolves into
   `self.colour_buffer_texture` (RGBA8, with a `depth24plus` depth
   buffer).
3. The widget copies that texture back into a numpy array
   (`self.frame_buffer`) and draws it onto the widget with `QPainter`,
   along with any text queued with `render_text()`.

The two abstract methods you must implement:

| Method | Called when | Your job |
|---|---|---|
| `paintWebGPU()` | every paint event | record and submit the frame's render pass |
| `resizeWebGPU(w, h)` | the window resizes (`w`/`h` are in device pixels) | update your projection matrix and any size-dependent state |

The widget handles high-DPI scaling (`self.ratio`), recreates the render
textures on resize, and tracks the current pixel size in
`self.texture_size`.

## A minimal application

```python
import sys

import wgpu
from PySide6.QtWidgets import QApplication
from wgpu.utils import get_default_device

from ncca.ngl import PerspMode, Vec3, look_at, perspective
from ncca.ngl.webgpu import WebGPUWidget


class Scene(WebGPUWidget):
    def __init__(self):
        super().__init__(background_colour=(0.4, 0.4, 0.4, 1.0))
        # 1. Get a device — everything is created from this.
        self.device = get_default_device()
        # 2. Create the colour / MSAA / depth textures.
        self._create_render_buffer()
        # 3. Set up cameras. Note PerspMode.WebGPU!
        self.view = look_at(Vec3(0, 2, 4), Vec3(0, 0, 0), Vec3(0, 1, 0))
        self.project = perspective(45.0, 1.0, 0.1, 100.0, PerspMode.WebGPU)
        # 4. Repaint at ~60 FPS.
        self.start_update_timer(16)

    def paintWebGPU(self):
        encoder = self.device.create_command_encoder()
        # The widget builds a render pass with the clear colour,
        # MSAA resolve, and depth attachment already configured.
        render_pass = self._create_render_pass(encoder)
        # ... set pipelines and draw here (see the next page) ...
        render_pass.end()
        self.device.queue.submit([encoder.finish()])
        self.render_text(10, 20, "Hello WebGPU")

    def resizeWebGPU(self, w, h):
        self.project = perspective(
            45.0, w / max(h, 1), 0.1, 100.0, PerspMode.WebGPU
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Scene()
    win.resize(1024, 720)
    win.show()
    sys.exit(app.exec())
```

Run it and you get a grey window — a cleared render target presented
through Qt, ready for the pipelines on the
[next page](builtin_pipelines.md).

Some points worth noting:

- **`self.device` must exist before the first resize/paint.** Create it
  first thing in `__init__`; the widget's resize handling calls
  `_create_render_buffer()`, which needs it.
- **You don't submit the copy-to-screen yourself.** After `paintWebGPU()`
  returns, the widget reads the colour texture back and paints it — your
  only job is to fill the texture.
- **`_create_render_pass(encoder)`** is a convenience that begins a render
  pass targeting the widget's multisample texture, resolving into the
  colour buffer, clearing to `self.background_colour`, with the depth
  buffer attached. You can also call `encoder.begin_render_pass(...)`
  yourself with `self.multisample_texture_view`,
  `self.colour_buffer_texture_view`, and `self.depth_buffer_view` if you
  need different load/store behaviour.
- **Animation** is just Qt: `start_update_timer(16)` (or a `QTimer` /
  `startTimer` of your own) schedules repaints; change your scene state
  each tick.
- **Text overlays** — `render_text(x, y, text, size=10, font="Arial",
  colour=Qt.black)` queues text that is drawn over the frame with
  `QPainter`. A negative `y` positions relative to the bottom of the
  window, and sizes scale with the window height.

## Projection: the WebGPU depth range

This deserves repeating because it is the most common porting mistake.
WebGPU clip space is *z from 0 to 1*; OpenGL's is *z from −1 to 1*. The
`perspective` (and `ortho`/`frustum`) helpers take a `PerspMode` argument
for exactly this reason:

```python
from ncca.ngl import PerspMode, perspective

project = perspective(45.0, aspect, 0.1, 100.0, PerspMode.WebGPU)
```

If you use the default (OpenGL) mode with the WebGPU renderer, half your
depth range falls outside the clip volume — geometry disappears or
z-fights.

## Uploading matrices

The math classes are numpy-backed, and `wgpu` wants raw `float32` data.
The pattern used throughout the demos is to build the matrix with `@` and
convert at the point of upload:

```python
mvp = (self.project @ self.view @ model).to_numpy().astype(np.float32)
pipeline.update_uniforms(mvp=mvp)
```

Everything you hand to a pipeline — vertex positions, colours, uniform
matrices — must be `np.float32`. Data in `float64` (numpy's default!) has
twice the byte size the GPU-side layout expects.

## Next steps

With the widget skeleton in place, the quickest way to get something on
screen is one of the fourteen built-in pipelines — continue to
[The Built-in Pipelines](builtin_pipelines.md).
