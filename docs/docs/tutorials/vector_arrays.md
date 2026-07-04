# Vector Arrays — `Vec2Array`, `Vec3Array`, `Vec4Array`

Graphics APIs don't want one vector — they want *thousands*, packed
tightly together in memory. A Python `list` of `Vec3` objects is scattered
all over memory and must be converted before the GPU can use it.

`Vec2Array`, `Vec3Array`, and `Vec4Array` solve this: they look like a
Python list of vectors, but internally store everything in **one
contiguous `np.float32` numpy array** — exactly the layout OpenGL and
WebGPU expect for a vertex buffer.

> **Singular vs plural** ([grammar guide](method_names.md)): `Vec3` is
> **one** vector; `Vec3Array` holds **many**. The method names carry the
> same clue: `append(value)` takes one, `extend(values)` takes many.

## Creating an array

```python
from ncca.ngl import Vec3, Vec3Array

points = Vec3Array()                      # empty
points = Vec3Array(100)                   # 100 zero vectors, ready to fill in
points = Vec3Array([Vec3(1.0, 2.0, 3.0),  # from an iterable of Vec3
                    Vec3(4.0, 5.0, 6.0)])
```

Only real `Vec3` objects are accepted — passing anything else raises
`TypeError`. (This is stricter than a plain list, and it is what guarantees
the data can be packed.)

## `append` one, `extend` many

```python
points = Vec3Array()

points.append(Vec3(1.0, 2.0, 3.0))       # ONE vector — parameter "value" is singular

points.extend([                           # MANY vectors — parameter "values" is plural
    Vec3(4.0, 5.0, 6.0),
    Vec3(7.0, 8.0, 9.0),
])
```

## It behaves like a list

```python
len(points)          # 3
points[0]            # Vec3(1.0, 2.0, 3.0)
points[1] = Vec3(0.0, 0.0, 0.0)     # replace an element
points[0:2]          # a new Vec3Array with the first two elements

for p in points:     # iterate as Vec3 objects
    print(p.length())
```

> **A copy, not a view:** `points[0]` gives you a *new* `Vec3` built from
> the stored data. Changing that `Vec3`'s components does **not** write
> back into the array — assign it back with `points[i] = p` if you want
> the array to change.

## Sending it to the GPU

This is the whole point of the class:

```python
data = points.to_numpy()   # flat np.float32 array: [x0, y0, z0, x1, y1, z1, ...]
nbytes = points.sizeof()   # total size in BYTES — what glBufferData wants
```

A typical OpenGL upload:

```python
import OpenGL.GL as gl

gl.glBufferData(gl.GL_ARRAY_BUFFER, points.sizeof(), points.to_numpy(), gl.GL_STATIC_DRAW)
```

`to_list()` and `to_tuple()` also exist when you need plain Python values.

## Worked example — building a triangle mesh

```python
from ncca.ngl import Vec3, Vec3Array, calc_normal

verts   = Vec3Array()
normals = Vec3Array()

def add_triangle(p1: Vec3, p2: Vec3, p3: Vec3) -> None:
    n = calc_normal(p1, p2, p3)
    verts.extend([p1, p2, p3])
    normals.extend([n, n, n])      # flat shading: same normal at each corner

add_triangle(Vec3(0.0, 0.0, 0.0), Vec3(1.0, 0.0, 0.0), Vec3(0.0, 1.0, 0.0))
add_triangle(Vec3(1.0, 0.0, 0.0), Vec3(1.0, 1.0, 0.0), Vec3(0.0, 1.0, 0.0))

# verts.to_numpy() / normals.to_numpy() now go straight into a VAO
```

## Common mistakes

**Mistake 1 — `append` with a list.**

```python
points.append([Vec3(1, 2, 3), Vec3(4, 5, 6)])   # ❌ a list is not one Vec3
points.extend([Vec3(1, 2, 3), Vec3(4, 5, 6)])   # ✅ many -> extend
```

**Mistake 2 — expecting `points[0].x = 5` to change the array.**

```python
p = points[0]
p.x = 5.0            # ❌ changes the copy only
points[0] = p        # ✅ write it back
```

**Mistake 3 — growing a huge array one `append` at a time.** Each `append`
reallocates. If you know the size, create it up front (`Vec3Array(n)`) and
assign by index, or collect into a list and `extend` once.

**Next:** [Geometry Maths](geometry_maths.md) — bounding boxes, planes,
and curves.
