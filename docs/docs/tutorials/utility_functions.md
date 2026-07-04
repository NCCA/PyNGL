# Utility Functions — `clamp`, `lerp`, `calc_normal`

Three small free functions from `ncca.ngl` that turn up in almost every
graphics program. (The camera-related functions `look_at`, `perspective`,
`ortho`, and `frustum` live in the same module — they have
[their own tutorial](cameras_and_projection.md).)

## `clamp(value, low, high)` — keep a number in range

Returns `value`, limited to the range `[low, high]`:

```python
from ncca.ngl import clamp

clamp(5, 0, 1)      # 1  — too big, clamped down
clamp(-3, 0, 1)     # 0  — too small, clamped up
clamp(0.5, 0, 1)    # 0.5 — already in range, unchanged
```

Typical uses: keeping colour components in `[0, 1]`, limiting a camera's
pitch so it cannot flip over, keeping array indices valid.

```python
# don't let the camera pitch past straight up/down
pitch = clamp(pitch + mouse_dy, -89.0, 89.0)
```

> Vectors have their own component-wise version:
> [`v.clamped(low, high)`](vectors.md) — note the `-ed`, because it
> returns a new vector.

## `lerp(a, b, t)` — blend between two values

**L**inear int**erp**olation: returns the value a fraction `t` of the way
from `a` to `b`. `t = 0` gives `a`, `t = 1` gives `b`:

```python
from ncca.ngl import lerp, Vec3

lerp(0.0, 10.0, 0.5)     # 5.0
lerp(0.0, 10.0, 0.25)    # 2.5

# works for anything with +, - and scalar * — including vectors:
lerp(Vec3(0.0, 0.0, 0.0), Vec3(10.0, 0.0, 0.0), 0.5)   # [5.0, 0.0, 0.0]
```

The single most useful animation tool there is:

```python
# fade a light up over 2 seconds
brightness = lerp(0.0, 1.0, clamp(elapsed / 2.0, 0.0, 1.0))
```

Note how `lerp` and `clamp` combine: clamping `t` to `[0, 1]` makes the
animation stop cleanly at the end instead of overshooting.

## `calc_normal(p1, p2, p3)` — the normal of a triangle

Given the three corners of a triangle, returns its unit surface normal
(using the cross-product recipe from the [vectors tutorial](vectors.md)):

```python
from ncca.ngl import calc_normal, Vec3

n = calc_normal(Vec3(0.0, 0.0, 0.0),
                Vec3(1.0, 0.0, 0.0),
                Vec3(0.0, 1.0, 0.0))
print(n)     # [0.0, 0.0, -1.0]
```

The order of the points (the *winding*) decides which way the normal
points — swap two points and the normal flips. Use it whenever you build
your own geometry and need normals for lighting:

```python
for tri in triangles:
    n = calc_normal(tri[0], tri[1], tri[2])
    # store n for each of the three vertices (flat shading)
```

---

That completes the math tutorials. From here:

- Explore the **API Reference** section for the full documentation of
  every class and method.
- Revisit the [grammar guide](method_names.md) whenever a method name
  surprises you — the name always tells you what it does.
