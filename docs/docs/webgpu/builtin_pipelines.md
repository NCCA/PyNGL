# The Built-in Pipelines

`PipelineFactory` provides fourteen ready-made render pipelines so you can
draw points, lines, triangles, and instanced meshes without writing any
WGSL. This page follows the bundled demo application, which cycles through
every one of them:

```bash
uv run python -m ncca.ngl.webgpu
```

**Left** / **Right** switch pipelines, **Space** pauses the animation,
**A** toggles automatic switching, **Escape** quits. The demo's source is
[`src/ncca/ngl/webgpu/__main__.py`](https://github.com/NCCA/PyNGL/blob/main/src/ncca/ngl/webgpu/__main__.py)
— every snippet below is taken from it.

## The pipeline contract

Every built-in pipeline is used the same way. **Create it once** at start
up, then **each frame** set data, update uniforms, and render inside your
render pass:

```python
from ncca.ngl.webgpu import PipelineFactory, PipelineType

# once, in __init__ (after self.device exists)
pipeline = PipelineFactory.create_pipeline(
    self.device, PipelineType.MULTI_COLOURED_POINTS
)

# each frame, in paintWebGPU
pipeline.set_data(positions, colours)      # upload vertex data
pipeline.update_uniforms(mvp=mvp, ...)     # upload uniform values
pipeline.render(render_pass)               # record the draw call
```

- `set_data` accepts numpy `float32` arrays **or** pre-existing
  `wgpu.GPUBuffer` objects (useful when a compute shader writes the data).
  Buffers are created on first use and reused/grown on subsequent calls,
  so calling it every frame is fine.
- `update_uniforms` and `set_data` are keyword-based; each pipeline type
  documents which keywords it reads. Unknown keywords are ignored.
- `render(render_pass)` sets the pipeline, bind group, and vertex buffers
  and records the draw. Pass `num_points=` / `num_vertices=` /
  `num_instances=` to draw a subset.
- Call `pipeline.cleanup()` when you are finished with it.

Matrices go in as numpy arrays; the demo rebuilds them once per frame:

```python
rotation = Mat4.rotate_y(self.rotation)
self.mvp_matrix = (self.project @ self.view @ rotation).to_numpy().astype(np.float32)
self.view_matrix = (self.view @ rotation).to_numpy().astype(np.float32)
```

## Choosing a pipeline type

Each primitive family comes in two flavours: **multi-coloured** (a colour
per vertex/instance, passed to `set_data`) and **single-colour** (one
uniform colour for everything, passed to `update_uniforms`).

| `PipelineType` | Draws | `set_data` | `update_uniforms` | `render` kwarg |
|---|---|---|---|---|
| `MULTI_COLOURED_POINTS` | billboarded round points (world-size) | `positions`, `colours` | `mvp`, `view_matrix`, `point_size` | `num_points` |
| `SINGLE_COLOUR_POINTS` | as above, one colour | `positions` | `mvp`, `view_matrix`, `point_size`, `colour` | `num_points` |
| `POINT_LIST_MULTI_COLOURED` | 1-pixel raw points | `positions`, `colours` | `mvp` | `num_points` |
| `POINT_LIST_SINGLE_COLOUR` | as above, one colour | `positions` | `mvp`, `colour` | `num_points` |
| `MULTI_COLOURED_LINES` | line segments (pairs of vertices) | `positions`, `colors` | `mvp` | `num_vertices` |
| `SINGLE_COLOUR_LINES` | as above, one colour | `positions` | `mvp`, `colour` | `num_vertices` |
| `MULTI_COLOURED_TRIANGLES` | triangle list | `positions`, `colors` | `mvp` | `num_vertices` |
| `SINGLE_COLOUR_TRIANGLES` | as above, one colour | `positions` | `mvp`, `colour` | `num_vertices` |
| `TRIANGLE_LIST_MULTI_COLOURED` | triangle list (explicit topology) | `positions`, `colors` | `mvp` | `num_vertices` |
| `TRIANGLE_LIST_SINGLE_COLOUR` | as above, one colour | `positions` | `mvp`, `colour` | `num_vertices` |
| `TRIANGLE_STRIP_MULTI_COLOURED` | triangle strip | `positions`, `colors` | `mvp` | `num_vertices` |
| `TRIANGLE_STRIP_SINGLE_COLOUR` | as above, one colour | `positions` | `mvp`, `colour` | `num_vertices` |
| `MULTI_COLOURED_INSTANCED_GEOMETRY` | a mesh drawn once per instance | `positions`, `colours`, `geometry_data` | `mvp`, `view_matrix`, `instance_transform` | `num_instances` |
| `SINGLE_COLOUR_INSTANCED_GEOMETRY` | as above, one colour | `positions`, `geometry_data` | `mvp`, `view_matrix`, `colour`, `instance_transform` | `num_instances` |

Positions are `(N, 3)` (lines and triangles also accept `(N, 2)`);
colours are `(N, 3)` RGB in 0–1; the single-colour `colour` uniform is a
3-element `float32` array. All data must be `np.float32`.

## Points

Two different point renderers exist:

- The **`*_POINTS`** pipelines draw each point as a camera-facing quad,
  clipped to a circle in the fragment shader. `point_size` is in **world
  units**, and the pipeline needs the `view_matrix` for the billboarding.
- The **`POINT_LIST_*`** pipelines use raw `point_list` topology: always
  one pixel per point, only `mvp` (plus `colour` for the single-colour
  variant) — the cheapest way to fling a particle cloud at the screen.

From the demo — ten thousand random points:

```python
rng = np.random.default_rng()
positions = rng.uniform(-4.0, 4.0, size=(10000, 3)).astype(np.float32)
colours = rng.random((10000, 3)).astype(np.float32)

pipeline = PipelineFactory.create_pipeline(
    self.device, PipelineType.MULTI_COLOURED_POINTS
)

# per frame
pipeline.set_data(positions, colours)
pipeline.update_uniforms(
    mvp=self.mvp_matrix,
    view_matrix=self.view_matrix,
    point_size=0.05,          # world units
)
pipeline.render(render_pass)
```

The single-colour variant drops the `colours` array and takes the colour
as a uniform instead:

```python
pipeline.set_data(positions)
pipeline.update_uniforms(
    mvp=self.mvp_matrix,
    view_matrix=self.view_matrix,
    point_size=0.05,
    colour=np.array([1.0, 1.0, 0.0], dtype=np.float32),  # yellow
)
pipeline.render(render_pass)
```

## Lines

`line_list` topology: each consecutive **pair** of vertices is one
segment. The demo feeds it the same random point set (as 2D positions) to
draw a hairball:

```python
pipeline = PipelineFactory.create_pipeline(
    self.device, PipelineType.MULTI_COLOURED_LINES
)

pipeline.set_data(positions, colours)
pipeline.update_uniforms(mvp=self.mvp_matrix)
pipeline.render(render_pass)
```

For `SINGLE_COLOUR_LINES`, pass `colour=` to `update_uniforms` as with
points.

## Triangles — list and strip

`MULTI_COLOURED_TRIANGLES` / `SINGLE_COLOUR_TRIANGLES` draw a triangle
list (every three vertices make one triangle). The
`TRIANGLE_LIST_*` types are the same thing with the topology stated
explicitly, and `TRIANGLE_STRIP_*` switches to strip topology, where each
new vertex after the first two extends the previous triangle — the demo
uses a strip to build a twisting ribbon from a helix of alternating
upper/lower vertices.

```python
pipeline = PipelineFactory.create_pipeline(
    self.device, PipelineType.TRIANGLE_STRIP_MULTI_COLOURED
)

pipeline.set_data(strip_positions, strip_colours)
pipeline.update_uniforms(mvp=self.mvp_matrix)
pipeline.render(render_pass)
```

Under the hood these are one pipeline class parameterised by topology —
the triangle (and line) pipelines accept a `topology=` keyword through
`create_pipeline` if you need something the enum doesn't cover.

## Instanced geometry

The instanced pipelines draw a **mesh once per instance position** — the
demo renders a 15×15 grid of teapots this way. The mesh comes straight
from `PrimData` as interleaved `(M, 8)` data (position, normal, UV per
vertex):

```python
from ncca.ngl import PrimData

geometry = PrimData.primitive("teapot").reshape(-1, 8)

# one position (and optionally colour) per instance
instance_positions = ...  # (N, 3) float32
instance_colours = ...    # (N, 3) float32

pipeline = PipelineFactory.create_pipeline(
    self.device, PipelineType.MULTI_COLOURED_INSTANCED_GEOMETRY
)

pipeline.set_data(
    positions=instance_positions,
    colours=instance_colours,
    geometry_data=geometry,
)
pipeline.update_uniforms(
    mvp=self.mvp_matrix,
    view_matrix=self.view_matrix,
    instance_transform=np.eye(4, dtype=np.float32),
)
pipeline.render(render_pass, num_instances=len(instance_positions))
```

`instance_transform` is applied to the mesh in every instance — use it to
scale or orient the base geometry without touching the vertex data. The
single-colour variant omits `colours` from `set_data` and takes
`colour=` in `update_uniforms`.

## Putting it together: the demo's frame loop

The demo holds all fourteen pipelines in a list and renders whichever is
current — its `paintWebGPU` is a template for any multi-pipeline scene:

```python
def paintWebGPU(self):
    self.render_text(10, 20, pipeline_name, size=20, colour=QColor(255, 255, 255))
    encoder = self.device.create_command_encoder()
    render_pass = self._create_render_pass(encoder)
    self.update_uniform_buffers()          # rebuild mvp/view numpy matrices
    self.pipelines[self.current][1](render_pass)   # set_data / uniforms / render
    render_pass.end()
    self.device.queue.submit([encoder.finish()])
```

You can render several pipelines into the *same* render pass — just call
each pipeline's `render()` in turn before `render_pass.end()`.

## When the built-ins aren't enough

The built-in pipelines are deliberately simple: no lighting, no textures.
For anything beyond flat colour — Lambert/PBR shading, texture mapping,
per-vertex data of your own — write a WGSL shader and use
[a custom pipeline](custom_pipelines.md).
