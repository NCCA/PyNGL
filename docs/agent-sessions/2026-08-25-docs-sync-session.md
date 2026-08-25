# 2026-08-25 -- Documentation sync

## Goal

Bring every documentation surface back in line with the code: the MkDocs API
reference, the README, `CLAUDE.md`'s architecture section, and the `wiki/`
knowledge base.

The `--strict` MkDocs build was already clean, which is exactly why the drift
had gone unnoticed -- `--strict` catches broken `:::` targets, but it never
notices a public symbol that no page mentions at all.

## What was actually wrong

**Undocumented public API.** Diffing the `__all__` of all five packages against
every `::: ncca.ngl...` directive in `docs/docs/` found 21 exported symbols with
no reference page: the whole of `util.py` (`look_at`, `perspective`, `PerspMode`,
`ortho`, `frustum`, `clamp`, `lerp`, `calc_normal`, `renderman_look_at`,
`prim_data_to_ri_points_polygons`), the exception classes (`MatrixError`,
`TransformRotationOrder`, the four `ObjParse*Error`s), `ImageModes`, `logger`,
and the QML import-path helpers.

**A broken README example.** It imported `lookAt`, which has never existed under
that name -- the function is `look_at`. Anyone copying the first code block in
the README got an `ImportError`.

**`CLAUDE.md` architecture drift.** No mention of `PerspectiveWidget`,
`PerspectiveModel`, `webgpu_widget.py`, or the QML import path rule.

**Wiki staleness.** `check_sync.py` reported 9 stale pages, and the entire
`src/ncca/ngl/qml/` package was covered by no page at all (29 untracked files).

**25 ruff errors in `src/`.** Found while verifying, not part of the original
brief. `webgpu_widget.py` lost its module docstring and picked up non-Google
docstring formatting in the readback-ring rewrite. This matters here because
both `CLAUDE.md` and `wiki/gotchas.md` state that `src/` passes clean and that
`lint-annotations-docstrings` is a blocking CI job -- so the documentation was
wrong until the code was fixed. Fixed rather than documented around.

## Files changed

- `docs/docs/Math.md` -- utility functions and exceptions sections
- `docs/docs/Geometry.md` -- `prim_data_to_ri_points_polygons`, `ObjParse*Error`
- `docs/docs/ImageAndTexture.md` -- `ImageModes`
- `docs/docs/Misc.md` -- logging section (`logger` in prose, `setup_logger` rendered)
- `docs/docs/QmlWidgets.md` -- `add_import_path` / `import_path`
- `README.md` -- `lookAt` -> `look_at`; example verified by running it
- `CLAUDE.md` -- `WebGPUWidget`, `perspectivewidget.py`, `perspective_model.py`,
  the file-based QML module and its import path
- `src/ncca/ngl/webgpu/webgpu_widget.py` -- module docstring, Google-style
  docstring formatting, `QResizeEvent`/`QPaintEvent` annotations on the two Qt
  event handlers. No behaviour change.
- `wiki/modules/qml.md` -- **new page** covering the QML models and views
- `wiki/modules/widgets.md` -- `PerspectiveWidget`, the mixin's `close_target`
  and `handle_key_shortcuts`, the scrolling demo dialog
- `wiki/modules/webgpu.md` -- the readback ring, the 256-byte row alignment,
  and the factory-callable registry that replaced the topology wrapper classes
- `wiki/modules/vao-stack.md` -- the `slots` -> `__slots__` fix on `Face`
- `wiki/howto/add-a-webgpu-pipeline.md` -- register a `**kwargs`-forwarding
  callable, not a wrapper subclass
- `wiki/architecture/overview.md` -- the QML layer, package-boundary invariants
- `wiki/architecture/api-conventions.md`, `wiki/decisions.md` -- the inert
  `slots = (...)` trap
- `wiki/gotchas.md` -- sub-package import rule extended to widgets and qml
- `wiki/index.md` -- QML page added to the page map

## Commands run

```bash
uv run --with mkdocs --with "mkdocstrings[python]" \
  mkdocs build --strict -f docs/mkdocs.yml   # clean
uv run wiki/tools/check_sync.py              # exit 0, all 16 pages fresh
uv run ruff check src/                       # All checks passed
uv run ruff format --check src/              # 82 files already formatted
uv run pytest -q                             # 621 passed
uv run pytest -m opengl -q                   # 93 passed
uv run pytest -m webgpu -q                   # 123 passed
uv run pytest -m qt -q                       # 285 passed
```

The README example and both QML import-path mechanisms were run rather than
read: `add_import_path()` and `__main__.py`'s `addImportPath(package_dir)` both
load `main.qml`, but only because `main.qml` sits alongside the components and
Qt resolves same-directory neighbours implicitly. The wiki page says so, so
nobody copies that line into an app whose `.qml` files live elsewhere.

## Note

The API-coverage diff now reports only `ncca.ngl.logger` and
`ncca.ngl.webgpu.PipelineFactory` as "undocumented". Both are module-level
singleton instances, deliberately covered in prose with their classes rendered
underneath -- pointing mkdocstrings at an instance renders an attribute, not
the API.
