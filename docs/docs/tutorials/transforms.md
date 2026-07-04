# The Transform Class — position, rotation, and scale in one object

In the [matrices tutorial](matrices.md) you learned to place an object with
*scale -> rotate -> translate*, written as:

```python
model = Mat4.translate(...) @ rotation @ Mat4.scale(...)
```

Every object in a scene needs exactly this, so PyNGL bundles it into one
class: **`Transform`**. You give it a position, a rotation, and a scale,
and it builds the model matrix for you, in the right order, every time.

## Basic use

```python
from ncca.ngl import Transform

tx = Transform()
tx.set_position(0.0, 5.0, 0.0)     # where the object is
tx.set_rotation(0.0, 45.0, 0.0)    # Euler angles in DEGREES (x, y, z)
tx.set_scale(2.0, 2.0, 2.0)        # how big it is

model = tx.matrix()                # the combined Mat4  send this to your shader
```

Each setter also accepts a `Vec3` (or a list/tuple) instead of three
floats:

```python
from ncca.ngl import Vec3

tx.set_position(Vec3(0.0, 5.0, 0.0))
tx.set_scale([2.0, 2.0, 2.0])
```

> **Note the naming** ([grammar guide](method_names.md)): `set_position`,
> `set_rotation`, and `set_scale` start with the command verb **`set`** —
> so, unlike the math classes, a `Transform` **is** mutable. It is a
> *builder* for matrices, not a mathematical value. `matrix()` is a noun:
> it returns a new `Mat4` and changes nothing.

## A typical render loop

```python
tx = Transform()
tx.set_scale(0.5, 0.5, 0.5)

angle = 0.0
while running:                       # your draw loop
    angle += 1.0
    tx.set_rotation(0.0, angle, 0.0)     # spin about y
    shader.set_uniform("model", tx.matrix())
    draw_the_object()
```

`Transform` caches its matrix internally and only rebuilds it when one of
the setters has been called, so calling `matrix()` every frame is cheap.

## Rotation order

Euler rotations are applied one axis at a time, and the *order* changes the
result. By default `Transform` uses `"xyz"` (x first, then y, then z). You
can choose another order:

```python
tx.set_order("zyx")      # one of: xyz, yzx, zxy, xzy, yxz, zyx
```

An invalid string raises `TransformRotationOrder`. If you find yourself
fighting rotation orders (or hitting gimbal lock), that is your cue to use
[quaternions](quaternions.md) instead.

## Resetting

```python
tx.reset()    # position (0,0,0), rotation (0,0,0), scale (1,1,1), order "xyz"
```

## Reading the current values

The components are plain attributes — each is a `Vec3`:

```python
tx.position    # Vec3
tx.rotation    # Vec3 of Euler angles in degrees
tx.scale       # Vec3
```

## Common mistakes

**Mistake 1 :- rebuilding the ordering by hand.** If you already use
`Transform`, don't multiply extra scale/rotate matrices around
`tx.matrix()` unless you really mean to add a second transform (e.g. a
parent, as in the planet-and-moon example in the
[matrices tutorial](matrices.md)).

**Mistake 2 :- radians.** `set_rotation` takes **degrees**, like everything
in PyNGL.

**Mistake 3 :- forgetting `matrix()` is a method.** Write `tx.matrix()`,
with parentheses.

**Next:** [Cameras and Projection](cameras_and_projection.md) — the view
and projection matrices that turn your scene into pixels.
