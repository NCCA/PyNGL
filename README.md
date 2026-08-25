# PyNGL

PyNGL is the full Python version of [NGL](https://github.com/NCCA/NGL), the NCCA graphics library used for teaching 3D computer graphics at the [NCCA Bournemouth University](https://nccastaff.bournemouth.ac.uk/jmacey/). It provides a consistent set of 3D math primitives, geometry loaders, and rendering back-ends for **OpenGL**, **WebGPU**, and **Qt (PySide6)**.

**Full documentation, tutorials and API reference:** <https://ncca.github.io/PyNGL/>

[![UV Tests](https://github.com/NCCA/PyNGL/actions/workflows/uv.yml/badge.svg)](https://github.com/NCCA/PyNGL/actions/workflows/uv.yml)[![Sonar Scanner](https://github.com/NCCA/PyNGL/actions/workflows/sonar-scan.yml/badge.svg)](https://github.com/NCCA/PyNGL/actions/workflows/sonar-scan.yml)

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=NCCA_PyNGL&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=NCCA_PyNGL)[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=NCCA_PyNGL&metric=bugs)](https://sonarcloud.io/summary/new_code?id=NCCA_PyNGL)[![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=NCCA_PyNGL&metric=code_smells)](https://sonarcloud.io/summary/new_code?id=NCCA_PyNGL)[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=NCCA_PyNGL&metric=coverage)](https://sonarcloud.io/summary/new_code?id=NCCA_PyNGL)[![Duplicated Lines (%)](https://sonarcloud.io/api/project_badges/measure?project=NCCA_PyNGL&metric=duplicated_lines_density)](https://sonarcloud.io/summary/new_code?id=NCCA_PyNGL)

## Features

- **3D math** — `Vec2/3/4`, `Mat2/3/4`, `Quaternion`, `Transform`, `Plane`, `BBox`, and the `Vec*Array` containers, all backed by NumPy `float32` with a consistent, well-tested API.
- **Geometry** — Wavefront OBJ loading (`Obj`), procedural primitives (`PrimData` / `Primitives`), and Bézier curves.
- **OpenGL rendering** — shader management (`ShaderLib`), VAO abstractions, textures, and freetype-based text.
- **WebGPU rendering** — a parallel pipeline stack targeting `wgpu`.
- **Qt Widgets & QML** — ready-made PySide6 widgets (`ncca.ngl.widgets`) and Qt Quick components (`ncca.ngl.qml`) for editing/displaying NGL math types in a GUI, plus camera event handling.

## Installation

PyNGL is published on PyPI as [`ncca-ngl`](https://pypi.org/project/ncca-ngl/) and the project uses [`uv`](https://docs.astral.sh/uv/).

Add it to a project:

```bash
uv add ncca-ngl
```

Or install into the current environment:

```bash
uv pip install ncca-ngl
```

The importable module is `ncca.ngl`:

```python
from ncca.ngl import Vec3, look_at, perspective

eye = Vec3(0, 2, 5)
view = look_at(eye, Vec3(0, 0, 0), Vec3(0, 1, 0))
proj = perspective(45.0, 16.0 / 9.0, 0.1, 100.0)
```

> **Note:** the OpenGL, WebGPU and Qt back-ends require a real graphics context and are imported from their sub-packages, e.g. `from ncca.ngl.opengl import ShaderLib` and `from ncca.ngl.webgpu import ...`.

## Development

Clone the repository and sync the environment (including dev dependencies):

```bash
git clone https://github.com/NCCA/PyNGL.git
cd PyNGL
uv sync
```

### Testing

```bash
uv run pytest                                   # default (non-GPU) test suite
uv run pytest --cov=src --cov-report=term-missing  # with coverage
```

Tests that need a real graphics context are deselected by default and only run when their marker is requested:

```bash
uv run pytest -m opengl
uv run pytest -m webgpu
uv run pytest -m qt
./test_all.sh
```

### Linting & formatting

```bash
uv run ruff format src/
uv run ruff check src/
```

## Documentation

A full class listing and documentations can be found here :- 

- **Docs site:** <https://ncca.github.io/PyNGL/>
- **Getting started / tutorials:** <https://ncca.github.io/PyNGL/tutorials/> (Getting Started and Tutorials sections)

The site covers the math API design rules, vectors/matrices/quaternions, transforms, cameras and projections, geometry, and the full module-by-module API reference.

### Knowledge wiki

Alongside the API reference, [`wiki/`](wiki/index.md) is an agent-maintained
knowledge base about *how PyNGL works* — architecture narratives, module
deep-dives, design decisions, and gotchas — written for both people and
coding agents. Start at [`wiki/index.md`](wiki/index.md).

Every page records which source files it describes and the commit it was
last verified against. To check the wiki is in sync with the code:

```bash
uv run wiki/tools/check_sync.py
```

Exit code 0 means every page is fresh; stale pages are listed with the
source files that changed. If you use Claude Code, `/wiki status`,
`/wiki update`, and `/wiki build` maintain the wiki for you (see
`.claude/skills/wiki/SKILL.md`).

## License

See [LICENSE.txt](LICENSE.txt) or just use the [Beerware License](https://scancode-licensedb.aboutcode.org/beerware.html)
