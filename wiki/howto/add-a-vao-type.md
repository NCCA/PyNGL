---
sources:
  - src/ncca/ngl/opengl/vao_factory.py
  - src/ncca/ngl/opengl/abstract_vao.py
  - src/ncca/ngl/opengl/simple_vao.py
synced: 9c2b6deffde456bb528df654ca6ce5e810d8f3a8
---

# Add a VAO Type

## Summary

This page walks through adding a new concrete Vertex Array Object (VAO)
implementation to `src/ncca/ngl/opengl/` and wiring it into the
`VAOFactory` registry so existing call sites (`Primitives`, `Obj`,
application code) can request it without any change on their side.

## How it works

1. **Subclass `AbstractVAO`** (`abstract_vao.py`). The base `__init__`
   already generates the OpenGL vertex array id and initialises `mode`,
   `bound`, `allocated`, `indices_count` — call `super().__init__(mode)`
   from your subclass's constructor and create whatever buffer objects
   your storage scheme needs there.
2. **Implement the abstract methods.** `AbstractVAO` declares five
   `@abc.abstractmethod` members that a subclass must provide or it
   cannot be instantiated: a no-argument `draw` that issues the actual
   GL draw call; `set_data`, taking a `VertexData` instance, that
   uploads vertex bytes to a buffer; a no-argument `remove_vao` that
   deletes the VAO's buffer(s) and vertex array; `get_buffer_id`, taking
   an optional buffer `index`, that returns the GL buffer id at that
   index; and `map_buffer`, taking an optional `index` and
   `access_mode`, that maps a buffer into client memory. Concrete
   multi-buffer implementations (see `multi_buffer_vao.py`,
   `simple_index_vao.py`) use the `index` argument to select among
   several buffers; single-buffer types ignore it, as `simple_vao.py`
   does.
3. **Reuse the concrete helpers already on `AbstractVAO`** rather than
   reimplementing them: `bind`/`unbind` (also exposed via the
   `with vao:` context manager), `set_vertex_attribute_pointer` for
   configuring attribute layout, `set_num_indices`/`num_indices`,
   `get_mode`/`set_mode`, `unmap_buffer`, and `get_id`. Only override
   `num_indices` if your storage needs a different count source, as
   `SimpleVAO` does (its override is functionally identical to the
   base — kept for clarity of intent).
4. **Guard state before mutating GL state.** `SimpleVAO.set_data` is the
   pattern to copy: check `isinstance(data, VertexData)` and raise
   `TypeError` if not, check `self.bound` and raise `RuntimeError` if
   not bound, only then call `glBufferData`, and set
   `self.allocated = True` plus `self.indices_count` from `data.size`.
   `draw` should itself check `self.bound and self.allocated` and log
   an error (not raise) if the VAO is used out of order.
5. **Add an enum member to `VAOType`** in `vao_factory.py` naming your
   new type (a short string value, e.g. `"myVAO"`).
6. **Register the creator** with
   `VAOFactory.register_vao_creator(VAOType.MY_TYPE, MyVAO)` at import
   time, alongside the existing pre-registration calls at the bottom of
   `vao_factory.py`. `VAOFactory._creators` is a plain dict keyed by the
   enum member; `create_vao(name, mode)` looks up the creator and calls
   it with `mode`, raising `ValueError` (after logging a warning) for an
   unknown name. Because call sites go through `VAOFactory.create_vao`
   with a `VAOType` value, not a class import, adding a new type never
   requires touching `Primitives`, `Obj`, or any other consumer.
7. **Export the new class** from `src/ncca/ngl/opengl/__init__.py` so it
   is importable as `from ncca.ngl.opengl import MyVAO`, matching
   `SimpleVAO`, `SimpleIndexVAO`, `MultiBufferVAO`.

## Key invariants

- All five abstract methods (`draw`, `set_data`, `remove_vao`,
  `get_buffer_id`, `map_buffer`) must be implemented — an incomplete
  subclass cannot be instantiated (`abc.ABC` enforcement).
- `draw` must only draw when both `bound` and `allocated` are true;
  violating this silently draws stale or empty data on real drivers.
- `set_data` must validate its argument is a `VertexData` and that the
  VAO is bound before touching any GL buffer call.
- New types are registered by `VAOType` enum member, not by string
  literal or class reference, at the bottom of `vao_factory.py` —
  keeping this indirection is what lets call sites stay untouched.
- VAO code needs a live GL context: tests live in `tests/test_vao.py`
  and depend on the `opengl_context` fixture, so they are skipped by a
  plain `uv run pytest` and must be run explicitly with
  `uv run pytest -m opengl`. Add your new type's coverage there,
  following `test_simple_vao`/`test_multi_buffer_vao` as templates.

## Connections

- [The VAO Stack](../modules/vao-stack.md)
- [Test Architecture](../architecture/test-architecture.md)
- [API Conventions](../architecture/api-conventions.md)
