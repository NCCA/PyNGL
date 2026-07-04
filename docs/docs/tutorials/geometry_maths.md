# Geometry classes `BBox`, `Plane`, `BezierCurve`

Three small geometric classes that build on [vectors](vectors.md):
bounding boxes for collision and culling, planes for tests like "which side
am I on?", and Bézier curves for smooth paths.

---

## `BBox` :- axis-aligned bounding boxes

A **bounding box** is the simplest useful approximation of an object: the
smallest axis-aligned box the object fits inside. We can use this for what is know as "broad phase" collision detection where we first test the cheap box before (or instead of) the expensive mesh.

It can be used to quickly test whether a ray (e.g. from a mouse click) intersects with the mesh, without needing to test every vertex.


### Creating a BBox

There are two ways to create a `BBox` depending on how you have the data:

```python
from ncca.ngl import BBox, Vec3

# from a center point and dimensions
box = BBox(center=Vec3(0.0, 0.0, 0.0), width=2.0, height=2.0, depth=2.0)

# FROM min/max extents (note the from_ classmethod naming)
box = BBox.from_extents(-1.0, 1.0,    # min_x, max_x
                        -1.0, 1.0,    # min_y, max_y
                        -1.0, 1.0)    # min_z, max_z
```

### Properties

```python
box.center     # Vec3  property, no parentheses
box.width      # 2.0
box.height     # 2.0
box.depth      # 2.0

box.min_x, box.max_x    # extents on each axis
box.min_y, box.max_y
box.min_z, box.max_z

box.get_vertex_array()   # the 8 corner Vec3s  handy for drawing the box
box.get_normal_array()   # the 6 face normals
```

### Mutation 

`center`, `width`, `height`, and `depth` are settable properties, and
`set_extents(...)` replaces the extents; the corner vertices and normals
are recalculated for you:

```python
box.center = Vec3(5.0, 0.0, 0.0)      # move the box
box.width  = 4.0                       # widen it
box.set_extents(0.0, 1.0, 0.0, 1.0, 0.0, 1.0)
```

### Worked example — point-in-box and overlap tests

```python
def contains(box: BBox, p: Vec3) -> bool:
    return (box.min_x <= p.x <= box.max_x and
            box.min_y <= p.y <= box.max_y and
            box.min_z <= p.z <= box.max_z)

def overlaps(a: BBox, b: BBox) -> bool:
    return (a.min_x <= b.max_x and a.max_x >= b.min_x and
            a.min_y <= b.max_y and a.max_y >= b.min_y and
            a.min_z <= b.max_z and a.max_z >= b.min_z)
```

These two tests are the backbone of simple collision detection.

---

## `Plane` :- an infinite flat surface

A **plane** divides space in two. Graphics uses planes everywhere: the six
faces of a camera's viewing volume (frustum culling), mirrors, floors,
clipping.

### Creating a Plane

```python
from ncca.ngl import Plane, Vec3

# from three points ON the plane (their winding decides the normal direction)
p = Plane(Vec3(0.0, 0.0, 0.0), Vec3(1.0, 0.0, 0.0), Vec3(0.0, 0.0, -1.0))

# or from a normal and one point
p = Plane()
p.set_normal_point(Vec3(0.0, 1.0, 0.0), Vec3(0.0, 0.0, 0.0))   # the ground plane

# or from the four floats of the plane equation ax + by + cz + d = 0
p = Plane()
p.set_floats(0.0, 1.0, 0.0, 0.0)
```

```python
p.normal    # Vec3 — the plane's unit normal (property)
p.point     # Vec3 — a point on the plane
p.d         # float — the d of the plane equation
```

###  The signed distance from a plane

`distance(point)` returns how far a point is from the plane, **with a
sign**: positive on the side the normal points to, negative on the other
side, zero on the plane itself.

```python
ground = Plane()
ground.set_normal_point(Vec3(0.0, 1.0, 0.0), Vec3(0.0, 0.0, 0.0))

ground.distance(Vec3(0.0, 5.0, 0.0))    #  5.0 — above the ground
ground.distance(Vec3(0.0, -2.0, 0.0))   # -2.0 — below it!
```

### Worked example :- is a sphere visible?

Frustum culling in one line per plane: a sphere is completely outside a
plane if its center is further than its radius behind it.

```python
def sphere_outside(plane: Plane, center: Vec3, radius: float) -> bool:
    return plane.distance(center) < -radius
```

Run that against the six planes of the camera frustum and you can skip
drawing everything the camera cannot see.

---

## `BezierCurve` :- smooth curves through control points

A **Bézier curve** turns a handful of *control points* into a smooth path
 for camera moves, animation paths, or modelling curved shapes. The curve
starts at the first control point, ends at the last, and is *pulled
towards* (but does not touch) the ones in between.

### Building and evaluating a curve

```python
from ncca.ngl import BezierCurve, Vec3

curve = BezierCurve()
curve.add_point(Vec3(0.0, 0.0, 0.0))     # add_point accepts a Vec3...
curve.add_point(1.0, 2.0, 0.0)           # ...or three floats
curve.add_point(3.0, 2.0, 0.0)
curve.add_point(4.0, 0.0, 0.0)
curve.create_knots()                     # call once after adding all points

mid = curve.get_point_on_curve(0.5)      # Vec3 at the halfway parameter
print(mid)                               # [2.0, 1.5, 0.0]
```

`get_point_on_curve(u)` takes a parameter `u` from `0.0` (start) to `1.0`
(end) and returns the `Vec3` on the curve at that parameter.

### Worked example :- flying a camera along a path

```python
from ncca.ngl import BezierCurve, Vec3, look_at

path = BezierCurve()
for p in [Vec3(10.0, 2.0, 10.0), Vec3(10.0, 8.0, -10.0),
          Vec3(-10.0, 8.0, -10.0), Vec3(-10.0, 2.0, 10.0)]:
    path.add_point(p)
path.create_knots()

frames = 300
for frame in range(frames + 1):
    u = frame / frames
    eye = path.get_point_on_curve(u)
    view = look_at(eye, Vec3(0.0, 0.0, 0.0), Vec3(0.0, 1.0, 0.0))
    # render the scene with this view matrix...
```

The camera glides smoothly around the scene, always looking at the origin.

## Common mistakes

**Mistake 1 — forgetting `create_knots()`.** The curve cannot be evaluated
until the knot vector exists. Add all your points, call `create_knots()`
once, then evaluate.

**Mistake 2 :- treating `distance()` as always positive.** It is a *signed*
distance :- that sign is the useful part. Use `abs()` if you only want the
magnitude.

**Mistake 3 :- expecting the curve to pass through the middle control
points.** Bézier curves only touch their first and last points; the middle
ones shape the curve.

**Next:** [Utility Functions](utility_functions.md) :- the small helpers
you will use everywhere.
