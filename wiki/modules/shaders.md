---
sources:
  - src/ncca/ngl/opengl/shader*.py
  - src/ncca/ngl/opengl/text.py
  - src/ncca/ngl/opengl/texture.py
  - src/ncca/ngl/opengl/shaders/**
synced: 4891d49afd4ef2329ac7b95298f1677fd2b3a5ef
---

# Shaders

## Summary

The OpenGL shader stack is three layers deep: `path:src/ncca/ngl/opengl/shader.py:Shader`
compiles a single GLSL stage, `path:src/ncca/ngl/opengl/shader_program.py:ShaderProgram`
links stages into a usable program and exposes a uniform-setting API, and
`path:src/ncca/ngl/opengl/shader_lib.py:ShaderLib` is a module-level singleton
registry of named programs — this is the entry point application code should
use. `path:src/ncca/ngl/opengl/texture.py:Texture` loads image data into an
OpenGL texture, and `path:src/ncca/ngl/opengl/text.py` builds a freetype glyph
atlas rendered through the built-in text shader.

## How it works

**Shader** (`shader.py:Shader`) wraps one `glCreateShader` object: `load()`
reads GLSL source from a file, `compile()` compiles and logs the info log on
failure, `edit_shader()`/`reset_edits()` do string substitution on the stored
source for runtime shader hot-editing, and `load_shader_source_from_string()`
loads source directly. `ShaderType` enumerates the GL stage constants
(VERTEX/FRAGMENT/GEOMETRY/TESSCONTROL/TESSEVAL/COMPUTE).

**ShaderProgram** (`shader_program.py:ShaderProgram`) owns `glCreateProgram`,
collects attached `Shader`s via `attach_shader()`, and `link()`s them. On
successful link it calls `auto_register_uniforms()` and
`auto_register_uniform_blocks()`, which query the linked program for every
active uniform/uniform block and cache `(location, gl_type, size, is_array)`
tuples keyed by name (array uniforms also get per-element keys like
`lights[0]`). `set_uniform(name, *value)` is the single dispatch point:
it inspects the Python type of the value(s) — `int`/`float`, `Mat2/3/4`,
`Vec2/3/4`, a bare tuple of 2-4 scalars, or a flat list matching a matrix size
— and calls the matching `glUniform*`/`glUniformMatrix*` call; unrecognised
types log a warning and are silently skipped. Dedicated `set_uniform_1fv` /
`_2fv`/`_3fv`/`_4fv`/`_1iv`/`_matrix{2,3,4}fv` methods exist for explicit
array uploads, and `get_uniform_*` methods read values back via
`glGetUniformfv`. `set_uniform_buffer()` uploads raw bytes to a registered
uniform block's UBO.

**ShaderLib** (`shader_lib.py:_ShaderLib`, exported as the singleton instance
`ShaderLib`) is the conventional application-facing API — application code
should call `ShaderLib.load_shader/use/set_uniform`, not construct a
`ShaderProgram` directly. `load_shader(name, vert, frag, geo=None)` creates,
compiles, attaches and links vertex/fragment/(optional geometry) shaders in
one call and stores the resulting `ShaderProgram` in `_shader_programs[name]`.
`use(name)` activates a program (or `glUseProgram(0)`/clears state if `name`
is `None`); if the requested name isn't loaded and the default shaders
haven't been loaded yet, `use()` lazily calls `_load_default_shaders()`
first. `set_uniform`, `set_uniform_buffer`, and all `get_uniform_*` methods
implicitly target whichever program is `_current_shader` — there is no
explicit "which program" argument, so calling them with no shader active is
a no-op/zero-return.

`_load_default_shaders()` loads four built-ins from
`path:src/ncca/ngl/opengl/shaders/` and registers them under the
`DefaultShader` enum *members themselves* (`DefaultShader.COLOUR` etc.), not
their `.value` strings — `to_load.items()` iterates `DefaultShader` keys and
passes them straight through as the `name` argument to `load_shader`, so
`ShaderLib.use(DefaultShader.COLOUR)` is the correct call, not
`ShaderLib.use("nglColourShader")` (the `.value` string exists only for
display/identification, it is not the registry key). The four built-ins:

- `DefaultShader.COLOUR` — `colour_vertex.glsl` / `colour_fragment.glsl`, flat colour.
- `DefaultShader.DIFFUSE` — `diffuse_vertex.glsl` / `diffuse_fragment.glsl`, per-vertex diffuse lighting.
- `DefaultShader.CHECKER` — `checker_vertex.glsl` / `checker_fragment.glsl`, procedural checker pattern.
- `DefaultShader.TEXT` — `text_vertex.glsl` / `text_geometry.glsl` / `text_fragment.glsl`, the only built-in with a geometry stage.

**Texture** (`texture.py:Texture`) wraps `path:src/ncca/ngl/image.py:Image`
(Pillow-backed): construction loads the file via `Image`, `width`/`height`
and the `format`/`internal_format` properties map the image's Pillow mode
(RGB/RGBA/L) to `GL_RGB8`/`GL_RGBA8`/`GL_R8` (and matching upload format),
and `set_texture_gl()` generates the GL texture, uploads pixels with
`glTexImage2D`, and builds mipmaps — returning texture id `0` if the image
failed to load (width/height <= 0). `set_multi_texture(id)` sets which
`GL_TEXTURE0 + id` unit the texture binds to on `set_texture_gl()`.

**Text** (`text.py`) has two classes: `FontAtlas` uses `freetype-py` to
rasterise printable ASCII (32–126) from a `.ttf`/similar font file into one
packed greyscale texture atlas (`build_atlas()`), records each glyph's size,
bearing, advance and pixel-space UV rect, then `generate_texture()` uploads
it as a single-channel `GL_RED` texture with a swizzle mask that maps the
red channel to alpha — so the fragment shader can tint glyphs with an
arbitrary uniform colour while sampling one channel for coverage. `_Text`
(singleton instance `Text`) manages named fonts (`add_font`), and
`render_text()` builds one `GL_POINTS` vertex per character (position, UV
rect, size — via `_build_instances`) into a `SimpleVAO`
(`path:src/ncca/ngl/opengl/simple_vao.py`) and draws it using
`DefaultShader.TEXT`; the geometry shader expands each point into a textured
quad on the GPU. `set_screen_size()` must be called on resize to update the
shader's `screenSize` uniform (also sets defaults for `textureID`,
`fontSize`, `textColour`).

## Key invariants

- `ShaderLib` is a module-level singleton (`_ShaderLib()` instantiated once
  at import time as `ShaderLib`) — do not instantiate `_ShaderLib` yourself;
  import and use the shared instance.
- Application code uses `ShaderLib`, never `ShaderProgram` directly — the
  latter has no registry/lookup-by-name of its own.
- Default shaders are registered under `DefaultShader` **enum members**, not
  their string `.value`s; `ShaderLib.use()`/`load_shader()` calls for
  built-ins must pass the enum member.
- `set_uniform`/`get_uniform_*`/`set_uniform_buffer` on `ShaderLib` always
  act on `_current_shader` (whatever `use()` last activated); there is no
  active shader if `use(None)` was called or nothing has been used yet.
- `auto_register_uniforms`/`auto_register_uniform_blocks` run automatically
  inside `ShaderProgram.link()` — uniforms are only queryable after a
  successful link, and only uniforms the linker considers "active" (i.e.
  actually used in the shader source) get registered.
- `set_uniform`'s single-value dispatch only recognises `int`, `float`,
  `Mat2/3/4`, `Vec2/3/4`, or list-likes whose length matches a known matrix
  size (4/9/16); anything else logs a warning and sets nothing.
- `Texture.set_texture_gl()` returns id `0` (OpenGL's "no texture") if the
  backing `Image` failed to load — callers must check for `0`, not assume
  success.
- `FontAtlas` only rasterises ASCII 32–126; characters outside that range
  are silently skipped by `_build_instances`.
- The text shader's alpha comes from a swizzled `GL_RED` channel — glyph
  colour is entirely uniform-driven (`textColour`), not baked into the atlas.

## Connections

- [vao-stack.md](vao-stack.md) — `SimpleVAO`/`VAOFactory` used by `Text` to draw glyph quads.
- [math.md](math.md) — `Vec2/3/4`, `Mat2/3/4` types accepted directly by `set_uniform`.
- [webgpu.md](webgpu.md) — the parallel WebGPU pipeline stack (no shared code with this stack).
