# Cameras and Projection — `look_at`, `perspective`, `ortho`

To draw a 3D scene you need three matrices, traditionally called
**M V P** — *Model*, *View*, *Projection*:

| Matrix | Question it answers | How you build it in PyNGL |
|---|---|---|
| **Model** | Where is the object in the world? | [`Transform`](transforms.md) or `Mat4.translate/rotate/scale` |
| **View** | Where is the camera, and which way is it looking? | `look_at(eye, look, up)` |
| **Projection** | How does 3D become a 2D image (perspective)? | `perspective(fov, aspect, near, far)` or `ortho(...)` |

This tutorial covers the *View* and *Projection* halves, which live as
plain functions in `ncca.ngl`.

---

## `look_at` — the view matrix

`look_at(eye, look, up)` builds a `Mat4` that moves the whole world so
that the camera sits at the origin looking down −z. You describe the
camera in plain terms:

- **`eye`**  :- where the camera *is*;
- **`look`**  :- the point the camera looks *at*;
- **`up`** :- which way is "up" for the camera (almost always the world y
  axis).

```python
from ncca.ngl import Vec3, look_at

view = look_at(
    Vec3(0.0, 2.0, 10.0),   # eye: 2 up, 10 back
    Vec3(0.0, 0.0, 0.0),    # look: at the origin
    Vec3(0.0, 1.0, 0.0),    # up: world y
)
```

> **Why does the *world* move and not the camera?** A camera is a trick:
> there is no camera object on the GPU. Instead, the view matrix is the
> *inverse* of the camera's own transform — moving the camera 10 units back
> is the same picture as moving the whole world 10 units forward.

### Orbiting the scene

A classic turntable camera — the eye circles the origin:

```python
import math
from ncca.ngl import Vec3, look_at

def turntable(angle_deg: float, radius: float, height: float):
    a = math.radians(angle_deg)
    eye = Vec3(radius * math.cos(a), height, radius * math.sin(a))
    return look_at(eye, Vec3(0.0, 0.0, 0.0), Vec3(0.0, 1.0, 0.0))
```

---

## `perspective` — the projection matrix

`perspective(fov, aspect, near, far)` builds the matrix that gives your
image *depth* — distant objects appear smaller, like a real camera lens.

```python
from ncca.ngl import perspective

projection = perspective(
    45.0,           # fov: vertical field of view in DEGREES
    1024 / 720,     # aspect: viewport width / height
    0.1,            # near: closest visible distance
    100.0,          # far: furthest visible distance
)
```

- **`fov`** :- a small angle is a telephoto lens (zoomed in); a large angle
  is a wide-angle lens (more scene, more distortion). 45° is a sensible
  default.
- **`aspect`** :- must match your window, or the image stretches.
  Recalculate it in your resize handler.
- **`near` / `far`** :- the visible depth range. Keep `near` as *large* as
  you can get away with: depth buffer precision is concentrated near the
  near plane, and `near=0.001, far=10000` is a recipe for z-fighting.
  `near` must be greater than 0.

### Projection Modes

OpenGL clips z to `[-1, 1]`, but WebGPU and Vulkan clip to `[0, 1]`.
`perspective` (and `ortho`) take a `mode` argument so the same call works
everywhere:

```python
from ncca.ngl import perspective, PerspMode

proj_gl  = perspective(45.0, aspect, 0.1, 100.0)                        # OpenGL (default)
proj_web = perspective(45.0, aspect, 0.1, 100.0, PerspMode.WebGPU)     # WebGPU / Vulkan
```

---

## `ortho` projection.

An **orthographic** projection has no foreshortening, so objects are the
same size at any distance. It is what you want for 2D/UI rendering,
CAD-style views, and shadow maps for directional lights.

```python
from ncca.ngl import ortho

# a 2D screen-space projection for a 1024x720 window
projection = ortho(0.0, 1024.0, 0.0, 720.0, -1.0, 1.0)
#                  left  right  bottom top   near  far
```

You describe a box (left/right/bottom/top/near/far); everything inside the
box ends up on screen. There is also `frustum(left, right, bottom, top,
near, far)` — a lower-level perspective projection where you give the box
edges yourself instead of a field-of-view angle.

---

## The MVP Matrix

Remember PyNGL's [row-vector convention](matrices.md): points go on the
left, and combined matrices read **right to left**. A vertex must be
transformed by model first, then view, then projection:

```python
from ncca.ngl import Mat4, Transform, Vec3, look_at, perspective

# Model — where the teapot is
tx = Transform()
tx.set_position(0.0, 0.0, 0.0)
tx.set_rotation(0.0, 45.0, 0.0)

# View — where the camera is
view = look_at(Vec3(0.0, 2.0, 10.0), Vec3(0.0, 0.0, 0.0), Vec3(0.0, 1.0, 0.0))

# Projection — the lens
projection = perspective(45.0, 1024 / 720, 0.1, 100.0)

# combined: model is applied FIRST (rightmost)
mvp = projection @ view @ tx.matrix()

shader.set_uniform("MVP", mvp)     # one matrix, uploaded once per object
```

In the vertex shader the GPU then computes `position @ MVP` (or the
equivalent for your shading language conventions) for every vertex.

## `FirstPersonCamera`

For interactive apps, PyNGL also provides a ready made
`FirstPersonCamera` class (movement + mouse look) that maintains its
own view and projection matrices, see the *Camera* page in the API Reference. There are a number of PyNGL Demos that use this class. 

## Common mistakes

**Mistake 1** :- `eye` and `look` the same point. The camera cannot look at
itself; you get a degenerate matrix. Keep them apart.

**Mistake 2** :- `up` parallel to the view direction. Looking straight down
with `up = (0, 1, 0)` makes the cross products collapse. Use a different
`up` (e.g. `(0, 0, -1)`) when looking along y.

**Mistake 3** :- a `near` plane of 0. Division by zero inside the
projection. Use a small positive value like `0.1`.

**Mistake 4** :- multiplying MVP in the wrong order. It is
`projection @ view @ model` — if your scene is visible but transforms
behave strangely, check this first.

**Next:** [Vector Arrays](vector_arrays.md) — packing many vectors for the
GPU.
