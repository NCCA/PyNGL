---
sources:
  - tests/conftest.py
  - CLAUDE.md
  - .github/workflows/**
synced: 9c2b6deffde456bb528df654ca6ce5e810d8f3a8
---

# Gotchas

## Summary

Traps in this repo's tooling and CI that look fine on the surface but
silently do the wrong thing — collected here so agents don't rediscover
them the hard way.

## How it works

- **A green `uv run pytest` proves nothing about GPU code paths.**
  `tests/conftest.py:pytest_collection_modifyitems` deselects any test
  whose fixtures include `opengl_context`, `webgpu_device`, or `qt_app`
  when no `-m` marker is given on the command line. If you touch code
  under one of those fixtures, you must explicitly run
  `uv run pytest -m opengl` / `-m webgpu` / `-m qt` — the default run
  passing tells you nothing about those paths.

- **Never run `uv run ruff check --select ANN,D src/` directly.**
  `pyproject.toml` configures ruff's `ANN`/`D` rules with an `ignore`
  list (e.g. `ANN401` is deliberately allowed at math/shader-uniform
  bridge points). Passing an explicit `--select` on the CLI overrides
  the config's `ignore`, so it wrongly re-flags those allowed cases.
  Use the plain `uv run ruff check src/` — it already picks up the
  configured rules.

- **mkdocstrings renders live but never discovers new symbols.** Editing
  a docstring updates the deployed site automatically at build time, but
  adding, renaming, or removing a public class/function does nothing
  until the matching `::: ncca.ngl...` directive is added to the
  relevant `docs/docs/*.md` page and any new page is added to `nav:` in
  `docs/mkdocs.yml`. Forgetting this step means the symbol silently has
  no docs page, with no error to flag it locally.

- **The docs strict-build gate exists but doesn't block anything yet.**
  `.github/workflows/docs.yml` runs a `docs-strict` job
  (`uv run mkdocs build --strict -f docs/mkdocs.yml`) that would catch
  broken references, bad `:::` targets, missing/orphaned nav entries,
  and docstring/signature mismatches — but it has `continue-on-error:
  true` because of a backlog of ~37 pre-existing griffe warnings, so a
  failing strict build does not fail CI or block `gh-deploy`. Run the
  strict build locally before committing docs/API changes; don't rely
  on CI to catch drift.

- **`lint-annotations-docstrings` in `.github/workflows/uv.yml` is also
  non-blocking** (`continue-on-error: true`), for the same reason: a
  pre-existing backlog of missing type hints/docstrings in `src/`. New
  or touched code must still have complete type hints and Google-style
  docstrings — CI won't stop a regression, review must.

- **Import OpenGL-coupled modules from `ncca.ngl.opengl`, not
  `ncca.ngl`.** The top-level `src/ncca/ngl/` package holds only
  API-agnostic modules and never imports `OpenGL.GL` directly; anything
  that does (VAOs, `shader*.py`, `texture.py`, `text.py`,
  `primitives.py`, `base_mesh.py`) lives in the `opengl/` sub-package
  and is deliberately **not** re-exported from `ncca.ngl.__init__`.
  `from ncca.ngl import Texture` (etc.) will fail or shadow the wrong
  symbol — use `from ncca.ngl.opengl import Texture`.

- **The default CI matrix (`uv.yml build` job) ignores a long list of
  GPU/Qt/webgpu test files by name** (`test_shaderlib.py`,
  `test_texture.py`, `test_vao.py`, `test_webgpu_pipelines.py`, the
  `*_widget.py` tests, etc.) on top of the marker-based deselection in
  `conftest.py`. This is belt-and-braces for cross-platform runners
  (ubuntu/macos/windows) without a real display — it's not just a local
  quirk, so don't assume CI exercises these files anywhere.

- **`sonar-scan.yml` runs coverage via `run_coverage_nogpu.py` under a
  headless GL stack** (`QT_QPA_PLATFORM=offscreen`,
  `GLFW_CONTEXT_API=osmesa`) rather than the real drivers used
  elsewhere — coverage numbers reported to SonarCloud reflect this
  CPU-only path, not a genuine GPU run.

## Key invariants

- Passing `uv run pytest` with no `-m` flag never touches
  `opengl_context`, `webgpu_device`, or `qt_app` fixtures.
- `ruff check src/` (no explicit `--select`) is the only correct local
  equivalent of the CI annotation/docstring check.
- A new public symbol needs a docs `:::` directive and nav entry, or it
  is invisible on the deployed site even though the build "succeeds".
- `docs-strict` and `lint-annotations-docstrings` failing does not fail
  the workflow run — check their logs explicitly, don't trust the green
  check mark alone.

## Connections

- [Test architecture](architecture/test-architecture.md) — full detail
  on the GPU fixtures and marker deselection mechanism.
- [System overview](architecture/overview.md) — the `ncca.ngl` vs
  `ncca.ngl.opengl` package boundary.
- [Decision log](decisions.md) — why these conventions exist.
