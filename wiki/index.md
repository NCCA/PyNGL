---
sources:
  - CLAUDE.md
synced: 9c2b6deffde456bb528df654ca6ce5e810d8f3a8
---

# PyNGL Knowledge Wiki

## Summary

This is an agent-maintained knowledge base about how PyNGL works — architecture
narratives, module deep-dives, design decisions, and gotchas — written for both
humans and coding agents. It complements the MkDocs API reference
(https://ncca.github.io/PyNGL/): the reference documents *what* each symbol is;
this wiki documents *how and why* the system fits together.

## Page map

- **Architecture**
  - [System overview](architecture/overview.md) — package boundaries, the
    OpenGL/WebGPU parallel structure, and top-level utilities
  - [API conventions](architecture/api-conventions.md) — the math-class
    contract, error conventions, naming and style rules
  - [Test architecture](architecture/test-architecture.md) — GPU fixtures,
    marker deselection, coverage scripts
- **Modules**
  - [Math](modules/math.md) — Vec/Mat/Quaternion/Transform/util and the
    `*_array` containers
  - [Geometry](modules/geometry.md) — prim_data, obj, bezier_curve, plane, bbox
  - [VAO stack](modules/vao-stack.md) — abstract_vao, concrete VAOs,
    vao_factory, primitives, base_mesh
  - [Shaders](modules/shaders.md) — shader → shader_program → shader_lib,
    text, texture, GLSL assets
  - [WebGPU](modules/webgpu.md) — pipeline base, factory, concrete pipelines
  - [Widgets](modules/widgets.md) — PySide6 widgets, event-handling mixin,
    first-person camera
- **Decisions and gotchas**
  - [Decision log](decisions.md) — why the API is shaped the way it is
  - [Gotchas](gotchas.md) — traps that bite agents and contributors
- **How-tos**
  - [Add a VAO type](howto/add-a-vao-type.md)
  - [Add a WebGPU pipeline](howto/add-a-webgpu-pipeline.md)
  - [Add a primitive](howto/add-a-primitive.md)

## How it works

Every page's frontmatter records the source files it describes (`sources`
globs) and the commit its content was last verified against (`synced`).
`wiki/tools/check_sync.py` reports pages whose sources changed since their
synced commit (STALE), broken metadata (ERROR), and `src/` files no page
covers (UNTRACKED).

## Key invariants

- Every file under `src/` is matched by some page's `sources`; the checker
  exits 0 only when all pages are fresh.
- Pages follow the format in `.claude/skills/wiki/SKILL.md` (Summary /
  How it works / Key invariants / Connections, ~150 lines max).

## Connections

To maintain this wiki, run `/wiki status`, `/wiki update`, or `/wiki build` —
see `.claude/skills/wiki/SKILL.md`.
