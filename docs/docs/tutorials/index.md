# Tutorials

These tutorials teach the PyNGL math classes from the ground up, with
runnable examples. They are written for students meeting 3D graphics maths
for the first time, but they also serve as a practical reference.

**Read them in this order** — each one builds on the previous:

| # | Tutorial | What you will learn |
|---|---|---|
| 1 | [Understanding the Method Names](method_names.md) | The grammar rules behind the API — why `normalized()` ends in `-ed`, and the one method that mutates |
| 2 | [Vectors](vectors.md) | `Vec2`, `Vec3`, `Vec4` — directions, positions, dot and cross products, normals, reflection |
| 3 | [Matrices](matrices.md) | `Mat2`, `Mat3`, `Mat4` — rotation, scale, translation, combining transforms with `@` |
| 4 | [Quaternions](quaternions.md) | `Quaternion` — rotation without gimbal lock, `slerp` for smooth animation |
| 5 | [The Transform Class](transforms.md) | `Transform` — position + rotation + scale bundled into one model matrix |
| 6 | [Cameras and Projection](cameras_and_projection.md) | `look_at`, `perspective`, `ortho` — building the view and projection matrices |
| 7 | [Vector Arrays](vector_arrays.md) | `Vec2Array`, `Vec3Array`, `Vec4Array` — collections of vectors ready for the GPU |
| 8 | [Geometry Maths](geometry_maths.md) | `BBox`, `Plane`, `BezierCurve` — bounding boxes, planes, and curves |
| 9 | [Utility Functions](utility_functions.md) | `clamp`, `lerp`, `calc_normal` — small helpers you will use everywhere |

Every code block in these tutorials is runnable. Try them in a Python
shell as you read:

```bash
uv run python
```

```python
>>> from ncca.ngl import Vec3
>>> Vec3(1.0, 2.0, 3.0) + Vec3(4.0, 5.0, 6.0)
Vec3(5.0, 7.0, 9.0)
```
