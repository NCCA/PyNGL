# Geometry: Primitives, Meshes, and VAOs

Three ways to get geometry on screen, in increasing order of effort:
stock primitives, OBJ files, and custom vertex data through the VAO
factory.

## Stock primitives

`Primitives` is a static class holding named, ready-to-draw meshes. The
classic NGL teaching models are built in — load them once in
`initializeGL`, then drawing is one line:

```python
from ncca.ngl.opengl import Primitives

Primitives.load_default_primitives()   # once
Primitives.draw("teapot")              # per frame
```

The stock names (also available as the `Prims` enum from `ncca.ngl`):
`teapot`, `bunny`, `buddah`, `dragon`, `troll`, `cube`, `football`,
`icosahedron`, `octahedron`, `tetrahedron`, `dodecahedron`.

!!! note
    Drawing a stock name without calling `load_default_primitives()`
    first draws nothing — it is the most common first-app mistake.

## Parametric primitives

`Primitives.create(type, name, ...)` generates a shape at the resolution
you ask for and registers it under your own name:

```python
from ncca.ngl import Prims
from ncca.ngl.opengl import Primitives

Primitives.create(Prims.SPHERE, "ball", 0.3, 32)      # radius, precision
Primitives.create(Prims.TORUS, "donut", 1.0, 0.3, 40) # radius, tube_radius, precision
Primitives.draw("ball")
```

The available types and their arguments:

| `Prims` | Arguments |
|---|---|
| `SPHERE` | `radius, precision` |
| `TORUS` | `radius, tube_radius, precision` |
| `CYLINDER` / `CONE` / `CAPSULE` | `radius, height, slices, stacks` |
| `DISK` | `radius, slices` |
| `LINE_GRID` | `width, depth, steps` (drawn as `GL_LINES`) |
| `TRIANGLE_PLANE` | `width, depth, w_p, d_p, normal (Vec3)` |

Everything except `LINE_GRID` is interleaved position/normal/UV triangle
data, so the built-in shaders light and texture it correctly. The raw
vertex arrays behind these shapes come from `PrimData` in `ncca.ngl` —
useful on its own when you want the data without a VAO (the WebGPU stack
uses it this way).

## OBJ files

`Obj` parses Wavefront OBJ files into CPU-side mesh data. Upload it to an
OpenGL VAO with `OpenGLMesh`:

```python
from ncca.ngl import Obj
from ncca.ngl.opengl import OpenGLMesh

data = Obj.from_file("models/helix.obj")
mesh = OpenGLMesh(data)
mesh.upload()  # whilst an OpenGL context is current
mesh.draw()    # per frame, with your shader active
```

`Obj.from_file("file.obj")` returns the parsed data (vertices, normals, UVs,
and `Face` lists). `Obj` no longer has `create_vao()`, `draw()`, or
`obj_with_vao()`. Parse errors raise `ObjParse*Error` exceptions rather than
returning half-loaded meshes.

## Textures

```python
from ncca.ngl.opengl import Texture

tex = Texture("textures/crate.png")
tex_id = tex.set_texture_gl()          # creates the GL texture, returns its id
ShaderLib.set_uniform("tex", 0)        # sampler uniform = texture *unit* index
```

## Custom geometry: the VAO factory

For your own vertex data, `VAOFactory` creates a managed vertex array
object. Three implementations ship, chosen with `VAOType`:

| `VAOType` | Use for |
|---|---|
| `SIMPLE` | one interleaved buffer, `glDrawArrays` |
| `SIMPLE_INDEX` | interleaved buffer + index buffer, `glDrawElements` (use `IndexVertexData`) |
| `MULTI_BUFFER` | separate buffers per attribute (positions, normals, … each in their own VBO) |

A VAO is used as a context manager — `with` binds it, leaving the block
unbinds it. Build once:

```python
import numpy as np
import OpenGL.GL as gl

from ncca.ngl.opengl import VAOFactory, VAOType, VertexData

# x,y,z then u,v per vertex
verts = np.array([...], dtype=np.float32)

vao = VAOFactory.create_vao(VAOType.SIMPLE, gl.GL_TRIANGLES)
with vao:
    vao.set_data(VertexData(data=verts, size=len(verts) // 5))
    stride = 5 * verts.itemsize
    vao.set_vertex_attribute_pointer(0, 3, gl.GL_FLOAT, stride, 0)  # position
    vao.set_vertex_attribute_pointer(1, 2, gl.GL_FLOAT, stride, 3 * verts.itemsize)  # uv
```

Draw per frame:

```python
with vao:
    vao.draw()
```

`VertexData(data, size, mode=GL_STATIC_DRAW)` carries the array and the
**vertex count** (not float count); for indexed drawing,
`IndexVertexData` adds the index array and its GL type. The VAOs also
expose `get_buffer_id()` and `map_buffer()` when you need to poke the
underlying VBO — handy for dynamic/streaming data.

Like the WebGPU `PipelineFactory`, the factory is a registry:
`VAOFactory.register_vao_creator(...)` adds your own `AbstractVAO`
subclass without touching call sites —
`PyNGLDemos/VertexArrayObject` has a worked example.

## Text rendering

`Text` renders a TrueType font via a freetype glyph atlas and
geometry-shader quads, using the built-in `DefaultShader.TEXT`:

```python
from ncca.ngl import Vec3
from ncca.ngl.opengl import Text

text = Text()
text.add_font("arial", "fonts/Arial.ttf", 40)
text.set_screen_size(self.width(), self.height())   # and again on resize

# in paintGL
text.render_text("arial", 10, 20, "PyNGL!", colour=Vec3(1.0, 1.0, 0.0))
```

A `Text` object can hold several fonts/sizes at once — each `add_font`
builds a glyph atlas under the name you give it.

Full API: [Geometry](../Geometry.md), [VAO](../VAO.md),
[Image and Texture](../ImageAndTexture.md), and [Text](../Text.md)
references.
