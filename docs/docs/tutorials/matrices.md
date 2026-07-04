# Matrices :- `Mat2`, `Mat3`, `Mat4`

A **matrix** is a grid of numbers that *transforms* vectors — it can rotate,
scale, and (for `Mat4`) translate them. Matrices are how everything in a 3D
scene gets positioned, oriented, and finally projected onto your screen.

| Class | Size | Typical uses |
|---|---|---|
| `Mat2` | 2×2 | 2D rotation/scale |
| `Mat3` | 3×3 | 3D rotation/scale, normal matrices |
| `Mat4` | 4×4 | full 3D transforms **including translation**, cameras, projection |

All three share the same core API `Mat4` is the one you will use most.

> **Before you start:** read [Vectors](vectors.md) first, and remember the
> [naming rule](method_names.md): `transposed()` returns a **new** matrix,
> `inverse()` and `determinant()` are nouns naming what they return, and no
> method changes the matrix you call it on.

---

## Creating matrices

Matrices are usually built with **named classmethods**, not by typing 16
numbers:

```python
from ncca.ngl import Mat3, Mat4

i = Mat4()                      # identity 
i = Mat4.identity()             # the same, spelled explicitly
z = Mat4.zero()                 # all zeros (rarely what you want!)

r = Mat4.rotate_x(45.0)         # rotate 45 DEGREES about the x axis
r = Mat4.rotate_y(90.0)         # ... about y
r = Mat4.rotate_z(30.0)         # ... about z
s = Mat4.scale(2.0, 2.0, 2.0)   # uniform scale ×2
t = Mat4.translate(1.0, 2.0, 3.0)   # move by (1, 2, 3) — Mat4 only!
```

> **Angles are in degrees** everywhere in PyNGL.

And of course `from_list` / `from_numpy` / `to_numpy` conversions exist,
just like vectors:

```python
m = Mat4.from_list([1.0, 0.0, 0.0, 0.0,
                    0.0, 1.0, 0.0, 0.0,
                    0.0, 0.0, 1.0, 0.0,
                    0.0, 0.0, 0.0, 1.0])
m.to_numpy()     # np.float32 4×4 array ready for glUniformMatrix4fv 
```

You can also convert between sizes: `Mat3.from_mat4(m)` keeps the top-left
3×3 (the rotation/scale part, dropping translation) and `Mat4.from_mat3(m)`
embeds a 3×3 into a 4×4.

### The identity matrix

`Mat4()` is the *identity*: transforming a vector by it changes nothing,
just like multiplying a number by 1. It is the natural starting point when
you build up a transform.

---

## PyNGL uses row-vector convention

This is the single most important thing to learn on this page. In PyNGL
(matching the C++ NGL and libraries like DirectX):

- Vectors are **rows**, and you transform a point by writing the point
  **first**: `new_point = point @ matrix`.
- The translation lives in the **bottom row** of a `Mat4`.

```python
from ncca.ngl import Mat4, Vec4

print(Mat4.translate(1.0, 2.0, 3.0))
# [[1.0, 0.0, 0.0, 0.0]
#  [0.0, 1.0, 0.0, 0.0]
#  [0.0, 0.0, 1.0, 0.0]
#  [1.0, 2.0, 3.0, 1.0]]   <- translation in the bottom row

p = Vec4(0.0, 0.0, 0.0)          # a point at the origin (w defaults to 1)
p2 = p @ Mat4.translate(1.0, 2.0, 3.0)
print(p2)                        # [1.0, 2.0, 3.0, 1.0]
```

If you have used GLM or written OpenGL maths by hand you may know the
*column-vector* convention (`matrix @ point`, translation in the last
column). PyNGL's matrices are the transpose of that layout. Don't mix the
two conventions in your head — in PyNGL, **the point goes on the left**.

### Points vs directions — why `w` matters

```python
from ncca.ngl import Mat4, Vec4

m = Mat4.translate(5.0, 0.0, 0.0)

point     = Vec4(1.0, 0.0, 0.0, 1.0)   # w = 1 -> a position
direction = Vec4(1.0, 0.0, 0.0, 0.0)   # w = 0 -> a direction

point @ m       # [6.0, 0.0, 0.0, 1.0]   moved
direction @ m   # [1.0, 0.0, 0.0, 0.0]   NOT moved (directions can't move)
```

`Vec3 @ Mat3` works the same way for pure rotation/scale:

```python
from ncca.ngl import Mat3, Vec3

up      = Vec3(0.0, 1.0, 0.0)
rotated = up @ Mat3.rotate_x(90.0)   # [0.0, 0.0, 1.0]  y axis rotated onto z
```

---

## Combining transforms with `@`

Real transforms are built by *combining* simple ones. `@` multiplies two
matrices into one matrix that does both:

```python
model = Mat4.translate(0.0, 5.0, 0.0) @ Mat4.rotate_z(90.0) @ Mat4.scale(2.0, 2.0, 2.0)
```

**Read the combination right to left**: the matrix *nearest the end* is
applied to the object **first**. The line above means:

1. **scale** the object ×2, *then*
2. **rotate** it 90° about z, *then*
3. **translate** it up by 5.

This *scale → rotate → translate* order is the standard way to place an
object in a scene, and it is exactly what the
[`Transform` class](transforms.md) does for you.

### Order matters!

Matrix multiplication is **not** commutative — `a @ b` and `b @ a` are
different transforms:

```python
from ncca.ngl import Mat4, Vec4

t = Mat4.translate(1.0, 0.0, 0.0)
r = Mat4.rotate_z(90.0)
p = Vec4(0.0, 0.0, 0.0)      # the origin, w = 1

p @ (t @ r)   # [1.0, 0.0, 0.0, 1.0] — rotate first (spins in place), then move
p @ (r @ t)   # [0.0, 1.0, 0.0, 1.0] — move first, then rotate about the origin
```

Think about a real object: "spin on the spot, then walk forward" ends
somewhere completely different from "walk forward, then orbit the origin".

> **Tip — build the matrix first, then apply it.** Always combine your
> matrices into one and then transform points with it
> (`p @ (t @ r)`), rather than chaining points through matrices one at a
> time. One combined matrix is also far cheaper when you have thousands of
> vertices.

---

## Inverse, transpose, determinant

```python
m = Mat4.rotate_x(45.0) @ Mat4.translate(0.0, 2.0, 0.0)

inv  = m.inverse()       # the transform that UNDOES m (a new Mat4)
flip = m.transposed()    # rows and columns swapped (a new Mat4)
det  = m.determinant()   # a single float
```

- **`inverse()`** :- if `m` moves an object into place, `m.inverse()` moves
  it back: `(p @ m) @ m.inverse() == p`. Cameras are the classic use: the
  *view matrix* is the inverse of the camera's own transform.
- **`transposed()`** :- swaps rows and columns. For a **pure rotation**
  matrix the transpose *is* the inverse, which is much cheaper to compute.
- **`determinant()`** :- a single number describing how the matrix changes
  volume. `1.0` means volume is preserved (pure rotation); `0.0` means the
  matrix is *singular* :- it flattens space and **has no inverse**.

```python
Mat4.rotate_z(90.0).determinant()    # 1.0 — rotations preserve volume
Mat4.scale(2.0, 2.0, 2.0).determinant()  # 8.0 — doubles each axis -> 8x volume
Mat4.scale(1.0, 1.0, 0.0).determinant()  # 0.0 — flattens z -> NOT invertible
```

Calling `inverse()` on a singular matrix raises `MatrixError`.

### The normal matrix

If a model matrix contains **non-uniform scale**, you
cannot transform surface *normals* with it as they come out skewed. The fix
is to use the *inverse transpose* of the 3×3 part:

```python
from ncca.ngl import Mat3, Mat4

model = Mat4.rotate_y(30.0) @ Mat4.scale(1.0, 2.0, 1.0)
normal_matrix = Mat3.from_mat4(model).inverse().transposed()
# transform normals with:  n @ normal_matrix, then renormalize
```

---

## Element access

Matrices support two-level indexing (row, then column) and iteration:

```python
m = Mat4.translate(1.0, 2.0, 3.0)

m[3]        # the bottom row as an array: [1.0, 2.0, 3.0, 1.0]
m[3][0]     # 1.0 — the x translation

m[3][0] = 5.0   # element assignment mutates the matrix (like set)
```

As with vectors, element assignment is the only mutation. As every named method returns a new matrix.

---

## Worked example :- a planet with a moon

Hierarchical transforms: the moon's position depends on the planet's.

```python
from ncca.ngl import Mat4, Vec4

def planet_and_moon(t: float) -> tuple[Vec4, Vec4]:
    # the planet spins about the origin and sits 10 units out
    planet = Mat4.translate(10.0, 0.0, 0.0) @ Mat4.rotate_y(t * 10.0)

    # the moon orbits the PLANET: its own small orbit, then the planet's transform
    moon = planet @ Mat4.translate(2.0, 0.0, 0.0) @ Mat4.rotate_y(t * 50.0)

    origin = Vec4(0.0, 0.0, 0.0)      # w = 1
    return origin @ planet, origin @ moon
```

Reading `moon` right to left: rotate in a fast small orbit, push out 2
units, *then* apply everything the planet does. Parent transforms always go
on the **left** of the child's own transform.

---

## Common mistakes

**Mistake 1 writing the point on the wrong side.**

```python
m @ p       #  wrong side — this is column-vector convention
p @ m       # Correct PyNGL is row-vector: point first
```

**Mistake 2  expecting `transposed()` to change the matrix.**

```python
m.transposed()          #  result thrown away
m = m.transposed()      # Correct
```

**Mistake 3  combining transforms in the wrong order.**

If your object orbits the origin when you wanted it to spin in place, your
rotation and translation are swapped. Remember: **right to left**, and
*scale → rotate → translate* reads `translate @ rotate @ scale`.

**Mistake 4  using `*` for matrix multiplication.**

```python
a * b        # wrong :- MatrixError  * is scalar-only
a @ b        # matrix product
a * 2.0      # scale every element by 2
```

**Mistake 5  translating a `Vec3`.**

Translation needs the fourth (`w`) component, so it needs `Vec4` and
`Mat4`. `Vec3 @ Mat3` can only rotate and scale.

---

## Quick reference

| Operation | Code | Returns |
|---|---|---|
| identity / zero | `Mat4()`, `Mat4.identity()`, `Mat4.zero()` | new matrix |
| build transforms | `Mat4.rotate_x/y/z(deg)`, `Mat4.scale(x,y,z)`, `Mat4.translate(x,y,z)` | new matrix |
| combine | `a @ b` (right one applies first) | new matrix |
| transform a point | `Vec4(...) @ m`, `Vec3(...) @ mat3` | new vector |
| undo | `m.inverse()` | new matrix |
| flip rows/cols | `m.transposed()` | new matrix |
| volume change | `m.determinant()` | `float` |
| resize | `Mat3.from_mat4(m)`, `Mat4.from_mat3(m)` | new matrix |
| elements | `m[row][col]` (read/write) | `float` |
| convert | `to_list/tuple/numpy`, `from_list/numpy`, `copy()` | conversions |

**Next:** [Quaternions](quaternions.md) — a better way to represent
rotation.
