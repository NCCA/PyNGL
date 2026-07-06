# Agentic Knowledge Wiki — Design

**Date:** 2026-07-06
**Status:** Approved for planning

## Goal

Add a Karpathy-style knowledge wiki to PyNGL: a set of agent-written, agent-maintained
markdown pages describing how the codebase actually works — architecture narratives,
module deep-dives, design decisions, and gotchas. Written for both humans (students,
maintainers) and coding agents (loadable per-module context with explicit invariants).
It complements, and does not replace, the MkDocs API reference (which documents *what*
each symbol is; the wiki documents *how and why* the system fits together).

## Non-goals

- No MkDocs/site integration in this iteration (plain markdown in the repo; can be
  wired into the docs site later).
- No CI enforcement of wiki freshness in this iteration (`check_sync.py` supports it
  via exit code, but no workflow change is made).
- No automatic/scheduled updates — refresh is on-demand via a slash command.

## Layout

```
wiki/
  index.md                      # entry point: what this wiki is, page map, how to update
  architecture/
    overview.md                 # system map, package boundaries, OpenGL/WebGPU parallel structure
    api-conventions.md          # math-class contract, error conventions, colour spelling, style rules
    test-architecture.md        # conftest fixtures, marker deselection, coverage scripts
  modules/
    math.md                     # Vec/Mat/Quaternion/Transform/util + *_array containers
    geometry.md                 # prim_data, obj, bezier_curve, plane, bbox
    vao-stack.md                # abstract_vao → simple/index/multibuffer → vao_factory, primitives
    shaders.md                  # shader → shader_program → shader_lib, glsl assets, text/texture
    webgpu.md                   # base pipeline, pipeline factory, concrete pipelines, constants
    widgets.md                  # PySide6 widgets, event-handling mixin, camera
  decisions.md                  # decision log: why @ vs *, singleton ShaderLib, np.float32, etc.
  gotchas.md                    # GPU-test deselection, ANN401 --select trap, docs drift check, etc.
  howto/
    add-a-vao-type.md
    add-a-webgpu-pipeline.md
    add-a-primitive.md
  tools/
    check_sync.py               # staleness checker (stdlib only)
```

Plain markdown, cross-linked with relative links, readable on GitHub and greppable by
agents. No build step.

## Page format

Every page starts with YAML frontmatter mapping it to the code it describes:

```yaml
---
sources:
  - src/ncca/ngl/vec*.py
  - src/ncca/ngl/mat*.py
  - tests/test_api_consistency.py
synced: <full commit hash the page content was last verified against>
---
```

Body convention (enforced by the `/wiki` skill's writing rules):

1. **Summary** — one paragraph, what this part of the system is for.
2. **How it works** — the narrative: data flow, class relationships, lifecycle.
3. **Key invariants** — the facts an agent must not violate when editing this code
   (e.g. "`_data` is always `np.float32`", "only `set()` and element assignment mutate").
4. **Connections** — relative links to related wiki pages.

Style rules: point at code with `path:line`-style references rather than pasting
blocks (pasted code rots line-by-line); prefer stating invariants over narrating
implementation detail; keep pages short enough to load whole as agent context.

## Staleness tracking — `wiki/tools/check_sync.py`

A stdlib-only Python script (shebang `#!/usr/bin/env -S uv run --script` per project
convention; no new dependencies):

- Parses frontmatter (`sources`, `synced`) from every `wiki/**/*.md` (excluding
  `tools/`).
- For each page, runs `git diff --name-only <synced>..HEAD -- <sources>`; any output
  means the page is **STALE**, reported with the changed files.
- Reports pages with missing/malformed frontmatter or an unknown `synced` commit as
  **ERROR**.
- Coverage check: any file under `src/` matched by no page's `sources` globs is
  reported **UNTRACKED**.
- Output: human-readable report by default; `--json` for machine consumption by the
  skill.
- Exit code: 0 when everything is fresh, 1 when anything is stale/error (so it can
  become a CI gate later).
- Has a pytest test file (`tests/test_wiki_check_sync.py`) covering the frontmatter
  parsing and glob/diff logic (git interaction faked or run against a temp repo).

## The `/wiki` project skill

Lives at `.claude/skills/wiki/SKILL.md` with three modes:

- **`/wiki status`** — run `check_sync.py` and report stale pages and untracked
  source files.
- **`/wiki update`** — for each stale page: read `git diff <synced>..HEAD` limited to
  the page's sources plus the current source files, rewrite only the parts of the page
  the changes invalidate, and bump `synced` to HEAD. A handful of stale pages are
  handled inline; larger backlogs fan out one subagent per page.
- **`/wiki build [page]`** — full (re)generation of one page or the whole wiki, one
  subagent per page, each reading its sources fresh. Used for initial creation and
  rare rebuilds.

The skill embeds the page format and style rules above so every future agent writes
consistent pages, and instructs updaters to keep `sources` frontmatter current when
modules are added or renamed.

## Implementation order

1. `wiki/tools/check_sync.py` + its test (TDD).
2. The `/wiki` skill.
3. Initial `/wiki build` — generate all pages via subagents.
4. Review pass: spot-check each page's claims against the code before committing.

All work happens on a worktree branch (`agent/knowledge-wiki`), conventional commits,
full test suite + `ruff` before committing, per repository rules.

## Testing & verification

- `check_sync.py` is unit-tested; it is the only executable component.
- Wiki page accuracy is verified by the step-4 review pass (checking stated
  invariants and file references against the code), not by automated tests.
- `uv run pytest` must stay green; `ruff check src/` untouched (the wiki and its tool
  live outside `src/`, but the tool still gets type hints and Google-style docstrings).
