# Vectors :- `Vec2`, `Vec3`, `Vec4`

A **vector** is the most important object in 3D graphics. In PyNGL a vector
is a small, fixed-size collection of `float` values:

| Class | Components | Typical uses |
|---|---|---|
| `Vec2` | `x, y` | texture coordinates, 2D positions, screen positions |
| `Vec3` | `x, y, z` | 3D positions, directions, normals, colours (r, g, b) |
| `Vec4` | `x, y, z, w` | homogeneous positions, colours with alpha (r, g, b, a) |

All three share the same API, so once you know `Vec3` you know them all.
This tutorial uses `Vec3` for most examples.

> **Before you start:** make sure you have read
> [Understanding the Method Names](method_names.md). The single most
> important fact is that methods ending in `-ed` return a **new** vector —
> they never change the vector you call them on.

---

## Creating vectors

```python
from ncca.ngl import Vec2, Vec3, Vec4

a = Vec3(1.0, 2.0, 3.0)     # positional components
b = Vec3(y=1.0)             # keywords work too -> (0.0, 1.0, 0.0)
c = Vec3()                  # default -> (0.0, 0.0, 0.0)
d = Vec4()                  # default -> (0.0, 0.0, 0.0, 1.0)  note w = 1!
```

> **Why does `Vec4` default `w` to 1.0?** A `Vec4` usually represents a
> *position* in homogeneous coordinates, and positions have `w = 1` so that
> matrix translation affects them. Directions use `w = 0`. This matters in
> the [matrices tutorial](matrices.md).

You can also build vectors *from* other types with the `from_` classmethods,
and convert *to* other types with the `to_` methods:

```python
import numpy as np

v = Vec3.from_list([1.0, 2.0, 3.0])
w = Vec3.from_numpy(np.array([4.0, 5.0, 6.0]))

v.to_list()    # [1.0, 2.0, 3.0]
v.to_tuple()   # (1.0, 2.0, 3.0)
v.to_numpy()   # np.float32 array ready to send to OpenGL / WebGPU
```

### Reading and writing components

```python
v = Vec3(1.0, 2.0, 3.0)

v.x            # 1.0 — by name
v[0]           # 1.0 — by index
x, y, z = v    # vectors unpack like tuples

v.x = 10.0     # component assignment mutates (like set)
v.set(1.0, 2.0, 3.0)   # set() replaces ALL components at once
```

Remember: `set()` and component assignment are the **only** ways to change
an existing vector. Everything else returns a new one.

---

## Arithmetic  
Vectors support the arithmetic you would expect, and every operation
returns a **new** vector:

```python
a = Vec3(1.0, 2.0, 3.0)
b = Vec3(4.0, 5.0, 6.0)

a + b          # [5.0, 7.0, 9.0]   component-wise add
a - b          # [-3.0, -3.0, -3.0]
-a             # [-1.0, -2.0, -3.0] negation (the opposite direction)
a * 2.0        # [2.0, 4.0, 6.0]   scale by a number
2.0 * a        # same order does not matter for scalars
a / 2.0        # [0.5, 1.0, 1.5]

a == Vec3(1.0, 2.0, 3.0)   # True  compares component values
```

> **Note:** `*` only works with a *number* (a scalar). You cannot write
> `a * b` for two vectors — that would be ambiguous (dot product? cross
> product? component-wise?). PyNGL makes you say which one you mean:
> `a.dot(b)` or `a.cross(b)`.

### A worked example — moving a point

A very common pattern in animation: move a position along a direction.

```python
position  = Vec3(0.0, 0.0, 0.0)
velocity  = Vec3(1.0, 2.0, 0.0)
dt        = 0.1                       # time step in seconds

position = position + velocity * dt   # new position each frame
print(position)                       # [0.1, 0.2, 0.0]
```

---

## Length and normalization

The **length** (or *magnitude*) of a vector is how long the arrow is:

```python
v = Vec3(0.0, 3.0, 4.0)
v.length()          # 5.0        (the 3-4-5 triangle!)
v.length_squared()  # 25.0
```

> **Why `length_squared()`?** Computing a length needs a square root, which
> is relatively slow. If you only want to *compare* distances ("which enemy
> is closest?"), compare the squared lengths instead — the comparison gives
> the same answer and skips the square root.

A **normalized** vector (also called a *unit vector*) has length 1. Unit
vectors represent pure *direction* with no magnitude, and almost every
lighting and reflection formula requires them:

```python
v = Vec3(0.0, 3.0, 4.0)

u = v.normalized()   # NEW vector [0.0, 0.6, 0.8] with length 1.0
print(v)             # [0.0, 3.0, 4.0] — v is unchanged!
```

### A worked example — the direction from A to B

"Which way do I walk from `start` to `target`, and how far is it?"

```python
start  = Vec3(1.0, 0.0, 1.0)
target = Vec3(4.0, 0.0, 5.0)

offset    = target - start        # the arrow from start to target
distance  = offset.length()       # 5.0
direction = offset.normalized()   # [0.6, 0.0, 0.8]  unit direction

# walk 2 units towards the target:
new_position = start + direction * 2.0
```

This *subtract, measure, normalize* pattern appears constantly in graphics
and games — learn it well.

---

## The dot product 

`a.dot(b)` returns a single number that measures the alignment of two
vectors. For **unit** vectors it is the cosine of the angle between them:

| `a.dot(b)` (unit vectors) | Meaning |
|---|---|
| `1.0` | same direction (0°) |
| `0.0` | perpendicular (90°) |
| `-1.0` | opposite directions (180°) |

```python
a = Vec3(1.0, 0.0, 0.0)
b = Vec3(0.0, 1.0, 0.0)

a.dot(b)    # 0.0   perpendicular
a.dot(a)    # 1.0   a vector always fully agrees with itself
a.dot(-a)   # -1.0  opposite
```

### A worked example :- simple diffuse lighting

The heart of the classic *Lambert* lighting model is one dot product: a
surface is bright when its normal points at the light.

```python
normal          = Vec3(0.0, 1.0, 0.0)                # surface faces up
to_light        = Vec3(1.0, 1.0, 0.0).normalized()   # direction to the light

brightness = max(0.0, normal.dot(to_light))
print(brightness)    # 0.707...  light at 45 degrees gives ~71% brightness
```

The `max(0.0, ...)` clamps away negative values  a surface facing *away*
from the light is dark, not "negatively lit".

### A worked example :- is it in front of me?

```python
forward   = Vec3(0.0, 0.0, -1.0)      # camera looks down -z
to_object = (obj_pos - cam_pos).normalized()

if forward.dot(to_object) > 0.0:
    print("the object is in front of the camera")
```

---

## The cross product :- "give me a perpendicular vector"

`a.cross(b)` returns a **new vector perpendicular to both** `a` and `b`.
Its direction follows the right-hand rule, and its length equals the area
of the parallelogram the two vectors span.

```python
x = Vec3(1.0, 0.0, 0.0)
y = Vec3(0.0, 1.0, 0.0)

x.cross(y)   # [0.0, 0.0, 1.0]   the z axis
y.cross(x)   # [0.0, 0.0, -1.0]  order matters! (anti-commutative)
```

> **`Vec2` is special:** in 2D there is no third axis to point along, so
> `Vec2.cross()` returns a single *number* (the signed area) instead of a
> vector. Positive means `b` is anticlockwise from `a`.

### A worked example :- the normal of a triangle

Given three corners of a triangle, the cross product of two edges gives the surface normal (used in lighting calculations).

```python
p1 = Vec3(0.0, 0.0, 0.0)
p2 = Vec3(1.0, 0.0, 0.0)
p3 = Vec3(0.0, 1.0, 0.0)

edge1  = p2 - p1
edge2  = p3 - p1
normal = edge1.cross(edge2).normalized()
```

PyNGL wraps this exact pattern in a helper —
[`calc_normal(p1, p2, p3)`](utility_functions.md) — but you should
understand what it does inside.

---

## Reflection :- bouncing off a surface

`v.reflected(n)` returns the vector `v` bounced off a surface whose unit
normal is `n`. Think of a ball hitting the floor, or light hitting a mirror:

```python
incoming = Vec3(1.0, -1.0, 0.0)      # travelling right and DOWN
floor_n  = Vec3(0.0, 1.0, 0.0)       # the floor's normal points UP

bounced = incoming.reflected(floor_n)
print(bounced)                        # [1.0, 1.0, 0.0] — right and UP
```

The formula inside is `v - 2 * v.dot(n) * n`. The normal `n` **must be unit
length** or the result will be wrong — normalize it first if in doubt.

### A worked example — a bouncing ball

```python
position = Vec3(0.0, 5.0, 0.0)
velocity = Vec3(2.0, 0.0, 0.0)
gravity  = Vec3(0.0, -9.8, 0.0)
floor_n  = Vec3(0.0, 1.0, 0.0)
dt = 1.0 / 60.0

for frame in range(600):
    velocity = velocity + gravity * dt
    position = position + velocity * dt
    if position.y < 0.0:                          # hit the floor
        position.y = 0.0
        velocity = velocity.reflected(floor_n) * 0.8   # bounce, lose 20% energy
```

---

## Clamping and interpolation

`clamped(low, high)` limits every component to a range — useful for
colours, which must stay in `[0, 1]`:

```python
colour = Vec3(1.4, -0.2, 0.5)
safe   = colour.clamped(0.0, 1.0)   # [1.0, 0.0, 0.5]
```

`lerp(other, t)` (**l**inear int**erp**olation) blends from this vector to
another. `t = 0` gives the start, `t = 1` gives the end, `t = 0.5` gives
the midpoint:

```python
start = Vec3(0.0, 0.0, 0.0)
end   = Vec3(10.0, 0.0, 0.0)

start.lerp(end, 0.25)   # [2.5, 0.0, 0.0] — a quarter of the way there
```

### A worked example — mixing between two colours

```python
red  = Vec3(1.0, 0.0, 0.0)
blue = Vec3(0.0, 0.0, 1.0)

for frame in range(101):
    t = frame / 100.0
    colour = red.lerp(blue, t)   # smoothly red -> purple -> blue
```

---

## `Vec4` and the `w` component

`Vec4` adds a fourth component, `w`. In graphics it has two main jobs:

**1. Homogeneous coordinates.** A `Mat4` can only translate a point if the
point has `w = 1`:

```python
point     = Vec4(2.0, 3.0, 4.0)        # w defaults to 1.0 -> a POSITION
direction = Vec4(0.0, 1.0, 0.0, 0.0)   # w = 0.0           -> a DIRECTION
```

When multiplied by a `Mat4`, the position is affected by translation but the direction is not — which is exactly right: you can move a *point*, but "up" is still "up" no matter where you stand.

**2. RGBA colours.** `Vec4(r, g, b, a)` and here the default `w = 1.0` also makes sense: fully opaque.

---

## Common mistakes

**Mistake 1 :- forgetting to keep the result of an `-ed` method.**

```python
v.normalized()          #  result thrown away, v unchanged
v = v.normalized()      # 
```

**Mistake 2 :- normalizing the zero vector.**

```python
Vec3(0.0, 0.0, 0.0).normalized()   # ❌ length is 0  you cannot divide by it
```

Guard with `if v.length_squared() > 0.0:` when the input might be zero.

**Mistake 3 :- using `*` between two vectors.**

```python
a * b        #  ValueError — * is scalar-only
a.dot(b)     #  if you wanted the dot product
a.cross(b)   #  if you wanted the cross product
```

**Mistake 4 :- comparing distances with `length()` in a loop.**

```python
if (a - b).length() < (a - c).length():          # works, but slow (2 sqrts)
if (a - b).length_squared() < (a - c).length_squared():   #  same answer, faster
```

**Mistake 5 :- reflecting off an unnormalized normal.**

```python
v.reflected(Vec3(0.0, 2.0, 0.0))                 #  normal has length 2 wrong answer
v.reflected(Vec3(0.0, 2.0, 0.0).normalized())    # 
```

---

## Quick reference

| Operation | Code | Returns |
|---|---|---|
| add / subtract | `a + b`, `a - b` | new vector |
| scale | `a * 2.0`, `a / 2.0` | new vector |
| negate | `-a` | new vector |
| length | `a.length()`, `a.length_squared()` | `float` |
| unit vector | `a.normalized()` | new vector |
| alignment | `a.dot(b)` | `float` |
| perpendicular | `a.cross(b)` | new vector (`float` for `Vec2`) |
| bounce | `a.reflected(n)` | new vector |
| limit range | `a.clamped(low, high)` | new vector |
| blend | `a.lerp(b, t)` | new vector |
| copy | `a.copy()` | new vector |
| mutate | `a.set(x, y, z)`, `a.x = 1.0` | — (changes `a`) |
| convert | `to_list/tuple/numpy`, `from_list/numpy` | conversions |

**Next:** [Matrices](matrices.md) — transforming vectors with rotation,
scale, and translation.
