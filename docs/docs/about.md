# About PyNGL

PyNGL is a Python port of [NGL](https://github.com/NCCA/NGL), the C++
graphics library developed by Jon Macey for teaching 3D computer graphics at
the National Centre for Computer Animation (NCCA), Bournemouth University.

## What it is for

PyNGL is a *teaching* library. It is designed so that the code you write
looks like the maths you learn in lectures: vectors, matrices, and
quaternions behave like mathematical values, and the rendering classes hide
just enough boilerplate to let you focus on the graphics concepts.

## Design principles

- **Immutable-style maths** — operations such as `normalized()` and
  `transposed()` return new objects; only `set()` mutates. See the
  [grammar guide](tutorials/method_names.md) for why the names are chosen
  this way.
- **numpy under the hood** — all math classes store their data as
  `np.float32` numpy arrays, so they can be passed straight to OpenGL and
  WebGPU.
- **Same API across backends** — the OpenGL, WebGPU, and Qt widget layers
  all share the same math classes.

## Relationship to the C++ NGL

The class names and behaviour deliberately mirror the C++ library, so
knowledge transfers in both directions. The main differences are Pythonic:
`snake_case` method names, `@` for matrix multiplication, and
`from_*`/`to_*` conversion methods.

## Further resources

- [NGL (C++) on GitHub](https://github.com/NCCA/NGL)
- [NCCA Coding Standard](https://nccastaff.bournemouth.ac.uk/jmacey/NCCACodingStandard/)
