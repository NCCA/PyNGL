# OBJ backend decoupling session

## Goal

Split OBJ parsing from the OpenGL renderer and provide OpenGL and WebGPU mesh adapters.

## Files changed

- `src/ncca/ngl/mesh.py`, `src/ncca/ngl/obj.py`
- `src/ncca/ngl/opengl/mesh.py`, `src/ncca/ngl/opengl/base_mesh.py`
- `src/ncca/ngl/webgpu/mesh.py`
- OBJ, mesh and WebGPU mesh tests, package exports and geometry documentation

## Commands run

- `uv run pytest`
- `uv run ruff check ...`
- `uv build`
- `git diff --check`
