---
sources:
  - tests/conftest.py
  - run_coverage_nogpu.py
  - pyproject.toml
synced: b3ac1a4e16eb594b40036f776028ae25de168432
---

# Test Architecture

## Summary

PyNGL's test suite is deliberately split into CPU-only tests and
graphics-context tests, so that a plain CI/local run never needs a real
GPU, window, or Qt event loop. `tests/conftest.py` implements this split
via three session-scoped fixtures and a collection hook; the coverage
scripts and `pyproject.toml` pytest config reinforce the same boundary.

## How it works

`tests/conftest.py` defines three session fixtures that stand up a real
graphics context: `opengl_context` (creates a hidden GLFW 4.1 core-profile
window and makes it current, skipping the test via `pytest.skip` if GLFW
init or window creation fails), `webgpu_device` (fetches the default
`wgpu` device via `wgpu.utils.get_default_device()`, raising if `None`),
and `qt_app` (an empty stub fixture — its presence in a test's
fixturenames is what matters, not its body).

`pytest_configure` registers three matching markers: `opengl`, `webgpu`,
`qt`. `pytest_collection_modifyitems` is the actual gate: it inspects
each collected test's `fixturenames`. If the user passed `-m` on the
command line, it just tags matching items with the corresponding marker
and lets pytest's own `-m` filtering do the work. If no `-m` was given
(the default `uv run pytest` case), it manually partitions items —
anything depending on `opengl_context`, `webgpu_device`, or `qt_app` is
pulled out of `items` and reported to pytest as deselected, never
executed or even attempted.

`run_coverage_nogpu.py` mirrors this split explicitly at the file level:
it hardcodes three lists (`cpu_only_tests`, `gpu_tests`, `qt_tests`) and
only runs `coverage run ... -m pytest -p no:pytest-qt` over the CPU-only
list, then emits `coverage report`, `coverage xml`, and `coverage html`.
GPU and Qt test files are printed as counts but never invoked — the
script's whole point is a fast, deterministic, hardware-independent
coverage number (e.g. for SonarCloud).

`pyproject.toml`'s `[tool.pytest.ini_options]` just sets `pythonpath`
(`src`, `tests`); it carries no marker-related config — the deselection
behaviour lives entirely in the `conftest.py` hook, not in ini options.
`[tool.coverage.run]`/`[tool.coverage.report]` set the coverage source
to `src/ncca/ngl`, omit tests/`__init__.py`/`__main__.py`, and exclude
boilerplate lines (`__repr__`, `NotImplementedError`, `TYPE_CHECKING`
guards) from the report.

## Key invariants

- A plain `uv run pytest` **silently skips** every test whose
  fixturenames include `opengl_context`, `webgpu_device`, or `qt_app` —
  green output does not mean those code paths ran.
- To exercise graphics-context code you must pass the marker explicitly:
  `uv run pytest -m opengl`, `-m webgpu`, or `-m qt`. Passing `-m` also
  changes the deselection logic itself (tag-and-filter instead of
  manual partition), so marker behaviour is consistent either way.
- If you add a new test that depends on one of the three fixtures, it is
  picked up automatically by name — no manual marker needed for the
  default-run deselection to apply — but you must still remember to run
  the matching `-m` suite yourself when validating changes.
- If you change code reached only through `opengl_context`,
  `webgpu_device`, or `qt_app` fixtures (VAOs, `ShaderLib`, `Texture`,
  `Primitives`, WebGPU pipelines, Qt widgets), the default test run
  passing is **not evidence** the change works; run the relevant `-m`
  suite before trusting it.
- `run_coverage_nogpu.py`'s three test lists are maintained by hand and
  can drift from the actual fixture-based deselection in `conftest.py`;
  when adding a new GPU/Qt test file, add it to `gpu_tests` or
  `qt_tests` there too, or it will silently be counted as CPU-only.
- `pytest-qt` is explicitly disabled (`-p no:pytest-qt`) in the
  CPU-only coverage run in `run_coverage_nogpu.py`, since its own
  fixtures would otherwise try to start a Qt event loop.

## Connections

- [overview.md](overview.md) — where the OpenGL, WebGPU, and Qt widget
  sub-packages exercised by these fixtures sit in the module layout.
- [api-conventions.md](api-conventions.md) — conventions enforced by the
  CPU-only test suite (e.g. `tests/test_api_consistency.py`).
