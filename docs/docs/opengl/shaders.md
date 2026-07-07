# Shaders and ShaderLib

`ShaderLib` is a singleton registry of named, linked shader programs, and
the conventional way application code deals with GLSL. The underlying
`Shader` (one compiled stage) and `ShaderProgram` (a linked program with
uniform setters) classes are available, but you rarely need them directly.

```python
from ncca.ngl.opengl import DefaultShader, ShaderLib
```

## The built-in shaders

Four shaders ship with the library and need no loading — just `use` them:

```python
ShaderLib.use(DefaultShader.DIFFUSE)
```

Each expects certain uniforms to be set — forget them and geometry
renders black or unlit:

| Shader | Uniforms |
|---|---|
| `DefaultShader.COLOUR` | `MVP` (Mat4), `Colour` (vec4) — flat colour |
| `DefaultShader.DIFFUSE` | `MVP`, `MV` (Mat4), `normalMatrix` (Mat3), `Colour` (vec4), `lightPos` (vec3, view space), `lightDiffuse` (vec4) |
| `DefaultShader.CHECKER` | `MVP`, `normalMatrix` (Mat3), `colour1` / `colour2` (vec4), `checkOn` (bool), `checkSize` (float, default 10), `lightPos` (vec3), `lightDiffuse` (vec4) |
| `DefaultShader.TEXT` | handled for you by the [`Text`](../Text.md) class |

The `normalMatrix` is the inverse-transpose of the model-view's upper
3×3:

```python
mv = self.view @ model
ShaderLib.set_uniform("normalMatrix", Mat3.from_mat4(mv).inverse().transposed())
```

## Setting uniforms

`set_uniform` dispatches on the value's type — pass a math object or the
raw components:

```python
ShaderLib.set_uniform("MVP", mvp_mat4)          # Mat4
ShaderLib.set_uniform("normalMatrix", n_mat3)   # Mat3
ShaderLib.set_uniform("Colour", 1.0, 0.0, 0.0, 1.0)   # vec4 as components
ShaderLib.set_uniform("lightPos", light_vec3)   # Vec3
ShaderLib.set_uniform("checkSize", 20.0)        # float
ShaderLib.set_uniform("tex", 0)                 # sampler = texture unit index
```

Uniforms go to the **currently used** program, so call
`ShaderLib.use(...)` first. When something renders wrong,
`ShaderLib.print_registered_uniforms(name)` dumps every uniform the
program declares — the quickest way to catch a typo'd name or a uniform
the compiler optimised away.

## Loading your own GLSL

One call compiles, links, and registers a program under a name of your
choice:

```python
ShaderLib.load_shader("PBR", "shaders/PBRVertex.glsl", "shaders/PBRFragment.glsl")
ShaderLib.use("PBR")
ShaderLib.set_uniform("albedo", 0.9, 0.4, 0.1)
```

`load_shader` also accepts an optional geometry-shader path. For
finer-grained control (loading source from strings, attaching stages by
hand, editing source before compilation) the lower-level calls
`create_shader_program`, `load_shader_source` /
`load_shader_source_from_string`, `compile_shader`,
`attach_shader_to_program`, and `link_program_object` mirror the C++ NGL
API — and `edit_shader` / `reset_edits` do textual substitution on the
source before compiling, which the demos use to set things like light
counts at run time.

## Uniform buffer objects

For blocks of uniforms (lights, per-frame camera data) use a UBO with a
numpy structured array whose layout matches the GLSL `uniform` block
(std140 — mind the padding, as with any std140 layout):

```python
import numpy as np

light_data = np.zeros(1, dtype=[("position", np.float32, 4),
                                ("colour", np.float32, 4)])
light_data["position"] = [0.0, 2.0, 2.0, 1.0]
light_data["colour"] = [1.0, 1.0, 1.0, 1.0]

ShaderLib.set_uniform_buffer("LightBlock", data=light_data.data,
                             size=light_data.data.nbytes)
```

`auto_register_uniform_blocks()` scans the current programs for uniform
blocks, and `get_uniform_block_data(...)` reads one back — useful in
tests. See `PyNGLDemos/SimplePyNGL` for a full PBR + UBO example.

## Odds and ends

- `ShaderLib.get_program_id(name)` returns the raw GL program id when
  you need to make PyOpenGL calls the wrapper doesn't cover.
- `ShaderLib.get_current_shader_name()` tells you what `use` last
  activated; `ShaderLib.use(None)` switches to program 0.
- `print_properties()` logs the active program's attributes and
  properties to the logger / `NGLDebug.log`.

Full API: [Shaders reference](../Shaders.md).
