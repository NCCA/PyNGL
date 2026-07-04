# Quaternions — smooth rotation without gimbal lock

A **quaternion** is a four-number object `(s, x, y, z)` that represents a
3D rotation. Compared to rotation matrices and Euler angles, quaternions:

- **interpolate beautifully** — `slerp` gives perfectly smooth rotation
  between two orientations, which is why animation systems store rotations
  as quaternions;
- **never suffer gimbal lock** — the "stuck axis" problem that Euler angles
  (separate x/y/z rotations) run into;
- are **compact** — 4 floats instead of a matrix's 9 or 16.

You don't need to understand the four numbers themselves (they come from
the mathematics of complex numbers extended to 4D). You only need the
recipes on this page.

> **Naming reminder** ([grammar guide](method_names.md)): `normalized()`
> returns a **new** quaternion; `conjugate()` and `inverse()` are nouns
> naming the new object they return; only `set()` mutates.

---

## Creating quaternions

Never type the four numbers by hand — build quaternions **from** something
meaningful:

```python
from ncca.ngl import Quaternion, Vec3

# the identity quaternion: "no rotation"
q = Quaternion()                 # (s=1, x=0, y=0, z=0)

# THE way to make a rotation: an axis and an angle (in degrees)
q = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), 90.0)   # 90° about y

# from an existing rotation matrix
from ncca.ngl import Mat4
q = Quaternion.from_mat4(Mat4.rotate_y(90.0))
```

And convert back to a matrix when the GPU needs one:

```python
m = q.to_mat4()      # Quaternion -> Mat4, ready to combine with @ and upload
```

`from_list` / `from_numpy` / `to_list` / `to_numpy` / `to_tuple` / `copy`
work exactly as they do on vectors. Components are accessible as `q.s`,
`q.x`, `q.y`, `q.z` or by index.

---

## Rotating a vector

This is the one deliberate exception to PyNGL's "`*` is scalar-only" rule:
**`Quaternion * Vec3` rotates the vector** and returns a new `Vec3`.

```python
from ncca.ngl import Quaternion, Vec3

q = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), 90.0)

v = Vec3(1.0, 0.0, 0.0)
rotated = q * v
print(rotated)       # [0.0, 0.0, -1.0] — x axis swung 90° about y onto -z
```

(Right-hand rule: point your right thumb along +y; your fingers curl from
+x towards −z.)

---

## Combining rotations with `@`

Just like matrices, quaternions combine with `@`, and the combination reads
**right to left** — the right-hand rotation is applied first:

```python
yaw   = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), 45.0)
pitch = Quaternion.from_axis_angle(Vec3(1.0, 0.0, 0.0), 30.0)

look = yaw @ pitch     # pitch first, then yaw
```

> **Why `@` and not `*`?** The quaternion product *is* a linear-algebra
> product, so it uses the same operator as matrix multiplication. Writing
> `q1 * q2` raises a `TypeError` telling you to use `@` — the library keeps
> `*` for "scale by a number" and the one special `Quaternion * Vec3` case.

After combining many rotations, floating-point error slowly makes the
quaternion drift away from unit length. Re-normalize occasionally:

```python
q = q.normalized()     # a new, exactly-unit-length quaternion
```

---

## `slerp` — the reason quaternions exist

**S**pherical **l**inear int**erp**olation blends smoothly from one
orientation to another at constant angular speed. This is *the* tool for
animating rotation:

```python
from ncca.ngl import Quaternion, Vec3

start = Quaternion()                                             # no rotation
end   = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), 90.0)   # 90° about y

halfway = start.slerp(end, 0.5)      # exactly 45° about y
```

### Worked example — turning a character to face a new direction

```python
frames = 60
start  = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), 0.0)
end    = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), 180.0)

for frame in range(frames + 1):
    t = frame / frames                    # 0.0 -> 1.0
    q = start.slerp(end, t)
    model = q.to_mat4()                   # use as the model's rotation
```

Why not just `lerp` the Euler angles? For a single-axis turn it happens to
work, but between two arbitrary 3D orientations, interpolating angles gives
wobbling, speed changes, and can hit gimbal lock. `slerp` takes the
shortest arc at constant speed, always.

---

## Conjugate and inverse — undoing a rotation

```python
q = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), 90.0)

back = q.inverse()       # the rotation that undoes q
conj = q.conjugate()     # flips the axis: (s, -x, -y, -z)
```

For a **unit** quaternion (which every rotation should be), the conjugate
*is* the inverse — same idea as "for a pure rotation matrix, the transpose
is the inverse", and just as cheap.

```python
v = Vec3(1.0, 0.0, 0.0)
w = q.inverse() * (q * v)     # rotate, then un-rotate
print(w)                      # [1.0, 0.0, 0.0] (within float precision)
```

---

## Other operations

Quaternions also support `+`, `-`, unary `-`, scalar `*` and `/`, `dot`,
`length` / `length_squared`, `==`, and iteration — the same value-like
behaviour as vectors. You will rarely need the arithmetic ones directly
(slerp uses them internally), but `dot` has a handy meaning:

```python
q1.dot(q2)    # close to 1.0 (or -1.0) -> the two orientations are similar
```

---

## Common mistakes

**Mistake 1 — using `*` for the quaternion product.**

```python
q1 * q2      # ❌ TypeError — the message tells you what to do
q1 @ q2      # ✅
```

**Mistake 2 — forgetting angles are degrees.**

```python
Quaternion.from_axis_angle(axis, math.pi / 2)   # ❌ that's 1.57 DEGREES
Quaternion.from_axis_angle(axis, 90.0)          # ✅
```

**Mistake 3 — a non-unit axis.** `from_axis_angle` expects a direction —
keep the axis normalized:

```python
Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), 90.0)          # ✅ unit axis
Quaternion.from_axis_angle(Vec3(1.0, 1.0, 0.0).normalized(), 90.0)  # ✅
```

**Mistake 4 — expecting `normalized()` to mutate.** As everywhere in
PyNGL: assign the result — `q = q.normalized()`.

---

## Quick reference

| Operation | Code | Returns |
|---|---|---|
| no rotation | `Quaternion()` | identity quaternion |
| axis + angle | `Quaternion.from_axis_angle(axis, deg)` | new quaternion |
| from / to matrix | `Quaternion.from_mat4(m)`, `q.to_mat4()` | conversions |
| rotate a vector | `q * v` | new `Vec3` |
| combine | `q1 @ q2` (right one first) | new quaternion |
| blend | `q1.slerp(q2, t)` | new quaternion |
| undo | `q.inverse()`, `q.conjugate()` | new quaternion |
| unit length | `q.normalized()` | new quaternion |
| similarity | `q1.dot(q2)` | `float` |
| mutate | `q.set(s, x, y, z)` | — (changes `q`) |

**Next:** [The Transform Class](transforms.md) — position, rotation, and
scale bundled into one object.
