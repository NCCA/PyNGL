# Getting Started

## Installation

PyNGL is managed with [uv](https://docs.astral.sh/uv/). Clone the repository
and let `uv` set everything up:

```bash
git clone https://github.com/NCCA/PyNGL
cd PyNGL
uv sync
```

Everything is run through `uv run`, so you never need to activate a virtual
environment yourself:

```bash
uv run python          # a Python shell with ncca.ngl available
uv run pytest          # run the (non-GPU) test suite
uv run src/ncca/ngl/webgpu # run webgpu pipline demos
uv run src/ncca/ngl/widgets # run Qt widgets demos
```

## Your first PyNGL code

The math and geometry-data classes all live in one module, `ncca.ngl`, and
are imported from the same place:

```python
from ncca.ngl import Vec3, Mat4, Quaternion

# vectors behave like mathematical values
a = Vec3(1.0, 0.0, 0.0)
b = Vec3(0.0, 1.0, 0.0)

print(a + b)          # [1.0, 1.0, 0.0]
print(a.dot(b))       # 0.0
print(a.cross(b))     # [0.0, 0.0, 1.0]

# matrices are built with named class methods
m = Mat4.rotate_y(45.0)          # angles are in degrees
q = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), 45.0)
```

## Core Principles of PyNGL

**1. Methods ending in `-ed` return a new object.** `v.normalized()` does
*not* change `v` it returns you a new vector. You must assign the result to a variable :

```python
v = Vec3(2.0, 0.0, 0.0)
v = v.normalized()     # assign the result back if you want v to change
```

This is the most important convention in the library. Read
[Understanding the Method Names](tutorials/method_names.md) for more details. 

**2. `@` multiplies, `*` scales.** Matrix -> matrix and matrix -> vector products
use Python's `@` operator `*` is only for scaling by a number.

```python
m = Mat4.rotate_x(45.0) @ Mat4.rotate_y(90.0)   # combine two rotations
v2 = v * 3.0                                    # scale a vector
```

**3. Angles are in degrees.**  in PyNGL so all rotation type methods such as  `Mat4.rotate_x(90.0)`,
`Quaternion.from_axis_angle(axis, 90.0)`, `Transform.set_rotation(...)` pass the values in degrees.

## OpenGL and WebGPU classes live in their own sub-modules

Anything that talks directly to OpenGL — `ShaderLib`, the VAO classes,
`Primitives`, `BaseMesh`, `Texture`, `Text`, `PySideEventHandlingMixin` — is
imported from `ncca.ngl.opengl`, not `ncca.ngl`:

```python
from ncca.ngl.opengl import ShaderLib, Primitives
```

The WebGPU stack is similarly namespaced under `ncca.ngl.webgpu`. See the
*API Reference* section for the full class-by-class breakdown.

## Where next?

Work through the [tutorials](tutorials/index.md) in order — they build from
vectors up to full camera and transformation pipelines, with runnable
examples throughout.

## Running the analysis tests

The SonarCloud job collects the complete test suite, including Qt, OpenGL and
WebGPU tests. Run it locally with:

```bash
uv run python run_coverage_nogpu.py
```

The script keeps its historical filename. It now needs graphics support;
Linux CI uses Mesa software rendering under Xvfb. To run the full suite without
coverage, use `uv run pytest --run-graphics`. The default test run continues to
leave out tests requiring graphics or Qt fixtures.

Coverage reports are regenerated for each run. Test failures, report failures
and coverage below 80% stop the analysis job.

The Linux analysis job explicitly selects WebGPU's Vulkan backend and Mesa's
Lavapipe driver using `WGPU_BACKEND_TYPE` and `VK_DRIVER_FILES`. It checks
Vulkan and WebGPU device creation before collecting tests, and prints the
selected adapter. `LIBGL_ALWAYS_SOFTWARE` controls the OpenGL side separately.
A native driver abort stops the process before Python can catch an exception;
the separate device check makes that failure easier to locate in the CI log.

## Commit checks

Install the Git hook once after cloning:

```bash
uv run pre-commit install
```

Each commit runs `uv run --locked ruff check src/`, using the same Ruff rules
and locked version as CI. This includes public docstrings and type annotations
from `pyproject.toml`. The check covers the whole source tree even when the
commit only changes configuration or documentation. Python files in the commit
are also formatted; stage any formatting changes before committing again.

To run the source check manually:

```bash
uv run pre-commit run ruff-check --all-files
```

The hook must be installed in each clone. Installing the Python package alone
does not install Git hooks. CI remains the check for full tests and builds.
