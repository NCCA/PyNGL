# OpenGL in PyNGL

The `ncca.ngl.opengl` package is PyNGL's OpenGL rendering stack — the
Python equivalent of the C++ NGL library used in NCCA teaching. It targets
**OpenGL 4.1 core profile** (the maximum available on macOS) through
PyOpenGL, and is windowing-toolkit agnostic: the examples here use PySide6
(`QOpenGLWindow`), but glfw and SDL3 work the same way once a context
exists.

Unlike the maths classes, the OpenGL modules are **not** re-exported from
`ncca.ngl` — import them from the sub-package:

```python
from ncca.ngl.opengl import ShaderLib, Primitives, VAOFactory
```

What the package gives you:

- **`ShaderLib`** — a singleton registry of named shader programs, with
  four ready-made shaders (`DefaultShader.COLOUR`, `DIFFUSE`, `CHECKER`,
  `TEXT`), GLSL loading/compiling/linking, and `set_uniform` /
  `set_uniform_buffer` for typed uniform upload. This is the conventional
  entry point — application code rarely touches `Shader` or
  `ShaderProgram` directly.
- **`Primitives`** — stock meshes (teapot, bunny, dragon, cube, …) and
  parametric shapes (sphere, torus, cone, …) as one-line drawables.
- **VAO abstraction** — `VAOFactory` creates `SimpleVAO`,
  `SimpleIndexVAO`, or `MultiBufferVAO` wrappers around vertex array
  objects, so custom geometry needs no raw `glGenVertexArrays` code.
- **`Obj` / `BaseMesh`** — Wavefront OBJ loading straight to a drawable
  VAO (`Obj` itself lives in `ncca.ngl` but builds on this package).
- **`Texture`** and **`Text`** — image textures (Pillow-backed) and
  font rendering (freetype glyph atlas + geometry-shader quads).
- **`PySideEventHandlingMixin`** — drop-in mouse rotate/pan/zoom camera
  controls for PySide6 windows.

## The pages in this section

1. **[Getting Started with OpenGL](getting_started.md)** — the
   `QOpenGLWindow` lifecycle, the surface-format setup you must not skip,
   and a complete spinning-teapot application.
2. **[Shaders and ShaderLib](shaders.md)** — using the built-in shaders
   (and their required uniforms), loading your own GLSL, and uniform
   buffer objects.
3. **[Geometry: Primitives, Meshes, and VAOs](geometry.md)** — stock and
   parametric primitives, OBJ files, textures, and building custom
   geometry with the VAO factory.
4. **API Reference** — [VAO](../VAO.md), [Shaders](../Shaders.md),
   [Geometry](../Geometry.md), [Image and Texture](../ImageAndTexture.md),
   and [Text](../Text.md).

## Complete examples

The [PyNGLDemos](https://github.com/NCCA/PyNGLDemos) repository has a
runnable demo per topic: `BlankPySide6NGL` (the starting template, with
and without the event mixin), `SimplePyNGL` (full manual event handling,
PBR, UBOs), `VAOPrimitives`, `VertexArrayObject` (custom VAOs),
`ObjViewer`, `SimpleTexture`, `ShadingModels`, `Lights`, `FBODemos`, and
`FontRendering`.
