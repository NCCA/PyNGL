# 2026-08-25 -- Packaging cleanup before the main migration

## Goal

Two loose ends found while assessing whether `Version1.0` is ready to migrate
to `main`: the wheel shipped ~14MB of data nothing loads, and a type stub
survived a module move and had been quietly wrong ever since.

## The wheel

`src/ncca/ngl/PrimData/` holds eleven baked meshes twice over -- as individual
`.npy` files and as the packed `Primitives.npz` that `pack_arrays.py` builds
from them. `prim_data.py:621` loads the `.npz` and nothing else; nothing in the
repo reads a loose `.npy` except `pack_arrays.py` itself. Both sets were going
into the wheel.

Added `wheel-exclude = ["PrimData/*.npy"]` to `[tool.uv.build-backend]`. The
files stay in the repo and in the sdist -- they are the sources the `.npz` is
rebuilt from, and an sdist should carry sources.

Wheel: **29MB -> 14MB**. The sdist stays at 29MB, as intended.

## The stub

`src/ncca/ngl/base_mesh.pyi` was a type stub for `Face`/`BaseMesh`, left behind
when the real module moved to `opengl/base_mesh.py`. Two problems:

- There is no `base_mesh.py` at that path any more, so the stub describes a
  module that does not exist.
- It declares `Face.vert` and `BaseMesh.verts`; the real classes use `vertex`
  for both. So where a type checker did pick it up, it was wrong.

Nothing consumes it -- there is no mypy or pyright config in the repo, and
`obj.py` imports the real classes from `.opengl.base_mesh`. Deleted.

## Files changed

- `pyproject.toml` -- `wheel-exclude` for `PrimData/*.npy`, with a comment
  explaining why the files are kept but not shipped
- `src/ncca/ngl/base_mesh.pyi` -- deleted
- `wiki/modules/geometry.md` -- dropped the stub from `sources` and from the
  prose; recorded that only the `.npz` ships, plus a new invariant that adding
  a baked mesh means re-running `pack_arrays.py`, not just dropping in a
  `.npy` (which works from a source checkout and then fails for anyone who
  pip-installed)

## Commands run

```bash
uv build                                     # wheel 14M, sdist 29M
uv lock --check                              # in sync
uv run ruff check src/                       # All checks passed
uv run ruff format --check src/              # 81 files already formatted
uv run pytest -q                             # 621 passed
uv run pytest -m opengl -q                   # 93 passed
uv run pytest -m webgpu -q                   # 123 passed
uv run pytest -m qt -q                       # 285 passed
uv run --with mkdocs ... mkdocs build --strict -f docs/mkdocs.yml   # clean
uv run wiki/tools/check_sync.py              # exit 0
```

The exclusion was verified against an installed wheel, not just the archive
listing: built it, `uv pip install`ed it into a throwaway venv, and loaded all
eleven baked primitives (`teapot`, `bunny`, `dragon`, `buddah`, `troll`,
`cube`, `football`, `icosahedron`, `octahedron`, `tetrahedron`, `dodecahedron`)
with zero `.npy` files on disk. The GLSL and QML assets still ship.

## Note

This does not touch the two remaining pre-migration items: `uv.yml` and
`sonar-scan.yml` still only trigger on `main`, so the 160 commits on
`Version1.0` have never been through the ubuntu/macos/windows matrix -- worth
merging via a PR so the matrix runs before it lands rather than after. There
are also still 15 ruff errors outside `src/` (11 in `tests/`), which the
`lint-annotations-docstrings` job does not check.
