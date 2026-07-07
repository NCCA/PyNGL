# Getting Started with OpenGL

This page builds a complete PySide6 + OpenGL application: a shaded teapot
you can rotate, pan, and zoom with the mouse. It assumes you have already
[installed PyNGL](../getting_started.md) along with `PyOpenGL` and
`PySide6`.

## Before anything else: the surface format

Qt gives you a **legacy OpenGL 2.1 context** unless you ask for better,
and the library's shaders won't compile in one. Request a 4.1 core
profile *before any window is created*:

```python
from PySide6.QtGui import QSurfaceFormat

fmt = QSurfaceFormat()
fmt.setSamples(4)                          # 4x MSAA
fmt.setMajorVersion(4)
fmt.setMinorVersion(1)                     # 4.1 is the macOS maximum
fmt.setProfile(QSurfaceFormat.CoreProfile)
fmt.setDepthBufferSize(24)
QSurfaceFormat.setDefaultFormat(fmt)
```

## The window lifecycle

Subclass `QOpenGLWindow` and override three methods:

| Method | Called | Your job |
|---|---|---|
| `initializeGL()` | once, when the context exists | set GL state, load shaders, create geometry |
| `paintGL()` | every repaint | clear, set uniforms, draw |
| `resizeGL(w, h)` | on resize | rebuild the projection matrix |

Adding `PySideEventHandlingMixin` (listed **first** in the bases) gives
you standard NCCA mouse controls for free — left-drag rotates, right-drag
pans, wheel zooms. The mixin maintains `self.spin_x_face`,
`self.spin_y_face`, and `self.model_position`, which you fold into a
transform each frame.

## A complete application

```python
#!/usr/bin/env -S uv run --script
import sys

import OpenGL.GL as gl
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtOpenGL import QOpenGLWindow
from PySide6.QtWidgets import QApplication

from ncca.ngl import Mat3, Mat4, Vec3, look_at, perspective
from ncca.ngl.opengl import (
    DefaultShader,
    Primitives,
    PySideEventHandlingMixin,
    ShaderLib,
)


class MainWindow(PySideEventHandlingMixin, QOpenGLWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("PyNGL Teapot")
        self.setup_event_handling(
            rotation_sensitivity=0.5,
            translation_sensitivity=0.01,
            zoom_sensitivity=0.1,
            initial_position=Vec3(0, 0, 0),
        )
        self.view = Mat4()
        self.project = Mat4()
        self.window_width = 1024
        self.window_height = 720

    def initializeGL(self) -> None:
        self.makeCurrent()
        gl.glClearColor(0.4, 0.4, 0.4, 1.0)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_MULTISAMPLE)
        self.view = look_at(Vec3(0, 1, 4), Vec3(0, 0, 0), Vec3(0, 1, 0))
        # stock meshes must be loaded once before they can be drawn
        Primitives.load_default_primitives()
        # built-in diffuse shader; set its static uniforms once
        ShaderLib.use(DefaultShader.DIFFUSE)
        ShaderLib.set_uniform("Colour", 0.8, 0.5, 0.2, 1.0)
        ShaderLib.set_uniform("lightPos", 0.0, 2.0, 2.0)
        ShaderLib.set_uniform("lightDiffuse", 1.0, 1.0, 1.0, 1.0)

    def paintGL(self) -> None:
        self.makeCurrent()
        gl.glViewport(0, 0, self.window_width, self.window_height)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # fold the mixin's mouse state into a global transform
        rot_x = Mat4.rotate_x(self.spin_x_face)
        rot_y = Mat4.rotate_y(self.spin_y_face)
        mouse_global_tx = rot_y @ rot_x
        mouse_global_tx[3, 0] = self.model_position.x  # translation lives in row 3
        mouse_global_tx[3, 1] = self.model_position.y
        mouse_global_tx[3, 2] = self.model_position.z

        mv = self.view @ mouse_global_tx
        ShaderLib.use(DefaultShader.DIFFUSE)
        ShaderLib.set_uniform("MVP", self.project @ mv)
        ShaderLib.set_uniform("MV", mv)
        ShaderLib.set_uniform(
            "normalMatrix", Mat3.from_mat4(mv).inverse().transposed()
        )
        Primitives.draw("teapot")

    def resizeGL(self, w: int, h: int) -> None:
        # account for high-DPI displays
        self.window_width = int(w * self.devicePixelRatio())
        self.window_height = int(h * self.devicePixelRatio())
        self.project = perspective(45.0, float(w) / h, 0.01, 350.0)


if __name__ == "__main__":
    fmt = QSurfaceFormat()
    fmt.setSamples(4)
    fmt.setMajorVersion(4)
    fmt.setMinorVersion(1)
    fmt.setProfile(QSurfaceFormat.CoreProfile)
    fmt.setDepthBufferSize(24)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1024, 720)
    window.show()
    sys.exit(app.exec())
```

This is essentially `BlankPySide6NGL/using_mixin.py` from
[PyNGLDemos](https://github.com/NCCA/PyNGLDemos) plus a teapot — copy
that template when starting a new project.

## Things that bite

- **Forgetting the `QSurfaceFormat` setup** — shaders fail to compile in
  the legacy 2.1 context you get by default.
- **Requesting OpenGL newer than 4.1 on macOS** — 4.1 is the ceiling.
- **Drawing `"teapot"` (or any stock mesh) without
  `Primitives.load_default_primitives()`** — nothing appears.
- **Forgetting `self.makeCurrent()`** at the top of `initializeGL` and
  `paintGL` — GL calls hit the wrong (or no) context.
- **Using `*` for matrix multiplication** — in PyNGL `*` is scalar-only;
  the linear-algebra product is `@`.
- **Silent exceptions** — Qt swallows exceptions raised inside event
  handlers like `paintGL`, so a typo can freeze the app with no
  traceback. The demos ship a `DebugApplication(QApplication)` subclass
  that overrides `notify()` to print tracebacks; copy it while
  developing.
- The library logs to `NGLDebug.log` (and `from ncca.ngl import logger`
  gets you the same colored logger for your own messages).

## Next steps

- [Shaders and ShaderLib](shaders.md) — what the built-in shaders expect,
  and how to load your own GLSL.
- [Geometry: Primitives, Meshes, and VAOs](geometry.md) — beyond the
  teapot: parametric shapes, OBJ files, and custom vertex data.
