# Understanding the Method Names — an English Grammar Guide

This guide explains **why the math methods in `ncca.ngl` are named the way they
are**. The names follow English grammar rules. If English is not your first
language — and especially if your language does **not** change a verb to show
past tense, or does **not** add a letter to show plural — these small word
endings can be confusing.

Read this once. After that, the names will tell you what each method does,
before you even read the documentation.

---

## The one rule to remember

> **A method ending in `-ed` gives you a NEW object and leaves the original
> unchanged. The plain verb `set` is the ONLY method that changes the object
> you call it on.**

Everything else in this guide explains that one sentence.

---

## Why: this library almost never changes your object

In this library, a `Vec3`, a `Mat4`, and a `Quaternion` behave like a number.

When you write `5 + 1`, the number `5` does **not** become `6`. You get a
**new** number, `6`, and `5` is still `5`.

Our math objects work the same way. When you "normalize" a vector, the original
vector does **not** change. You receive a **new** vector as the answer. This is
called an **immutable** style.

Because the answer is always a *new, finished* object, the method names use the
English grammar form that means *"a finished result"* — the **past participle**,
which ends in **`-ed`**.

---

## The grammar behind the names

English verbs have different forms. This library uses four kinds of names.

| Grammar form | English example | Meaning in the API | Does it change the object? |
|---|---|---|---|
| **Plain verb** (a command) | *"Set the table!"* | Do this action to the object **now** | ✅ **YES** |
| **Past participle** (`-ed`, used as an adjective) | *"the normaliz**ed** vector"* | Give me a **new** object that is the finished result | ❌ No |
| **Noun** (the name of a thing) | *"the length"*, *"the inverse"* | Give me this value / this new thing | ❌ No |
| **Preposition** (`to_` / `from_`) | *"convert **to** a list"* | Convert between types | ❌ No |

The rest of this section explains each row with real code.

---

### 1. Past tense vs. past participle — the `-ed` confusion

Many languages (for example Chinese, Japanese, Korean, Thai, Vietnamese, and
others) do **not** add an ending to a verb to show time. In English, the same
`-ed` spelling is used for two different grammar ideas:

- **Past tense** — an action that *happened*: *"Yesterday I normaliz**ed** the
  vector."*
- **Past participle** — an *adjective* describing a *finished result*: *"a
  normaliz**ed** vector"* (a vector that **has been** normalized).

**In this library, `-ed` always means the second one: a finished result.**

Compare the two forms of the verb:

| Base verb (the action) | Past participle (the result) | The library uses… |
|---|---|---|
| `normalize` — *to make unit length* | `normalized` — *made unit length* | **`normalized()`** |
| `reflect` — *to bounce off* | `reflected` — *bounced off* | **`reflected()`** |
| `transpose` — *to flip rows and columns* | `transposed` — *flipped* | **`transposed()`** |
| `clamp` — *to limit to a range* | `clamped` — *limited* | **`clamped()`** |

> 💡 **Everyday analogy (laundry):**
> `wash` is the action. `washed` is the result.
> `shirt.washed()` means *"give me a clean copy of this shirt"* — your original
> shirt in your hand does not suddenly become clean. You must **take** the clean
> shirt that is handed back to you.

That last point is the most common mistake, so here it is in code:

```python
from ncca.ngl import Vec3

v = Vec3(2.0, 0.0, 0.0)

v.normalized()      # ⚠️ WRONG use: the result is thrown away!
print(v)            # [2.0, 0.0, 0.0]  ← v did NOT change

u = v.normalized()  # ✅ RIGHT: keep the new vector that is returned
print(u)            # [1.0, 0.0, 0.0]  ← the answer (length 1)
print(v)            # [2.0, 0.0, 0.0]  ← original is still unchanged
```

If you want `v` itself to hold the answer, assign it back to `v`:

```python
v = v.normalized()  # replace v with its normalized version
```

---

### 2. The plain verb `set` — the one real command

`set` is a **command** (imperative mood). A command tells the object to change
**itself, right now**. It returns nothing. It is the only method here that
changes the object you call it on.

```python
from ncca.ngl import Vec3

v = Vec3(0.0, 0.0, 0.0)
v.set(1.0, 2.0, 3.0)   # v itself changes now
print(v)               # [1.0, 2.0, 3.0]
```

> 💡 Notice the grammar difference:
> `v.set(...)` → *"Vector, change yourself!"* (a command → it changes).
> `v.normalized()` → *"the normalized version of v"* (a description → new object).

---

### 3. Noun names — the method is named after the thing it returns

Some methods are named with a **noun**, not a verb. A noun name means: *"give me
this thing."* It returns a value or a new object and never changes the original.

```python
from ncca.ngl import Vec3, Mat4

v = Vec3(0.0, 3.0, 4.0)
print(v.length())       # 5.0        → "the length" (a number)
print(v.dot(v))         # 25.0       → "the dot product" (a number)

m = Mat4.rotate_x(45.0)
print(m.determinant())  # a number   → "the determinant"
inv = m.inverse()       # new Mat4   → "the inverse"
```

`length`, `dot`, `determinant`, `inverse`, `conjugate`, `cross` are all nouns —
the name **is** the answer you get back.

---

### 4. `to_` and `from_` — conversions

The prepositions `to` and `from` show a conversion between two types.

- **`to_something()`** — convert **this object into** something else.
- **`from_something(...)`** — build a **new object from** something else. This is
  written before the class name, because the class is doing the building.

```python
from ncca.ngl import Vec3
import numpy as np

v = Vec3(1.0, 2.0, 3.0)

a_list  = v.to_list()          # Vec3  → list:  [1.0, 2.0, 3.0]
a_tuple = v.to_tuple()         # Vec3  → tuple: (1.0, 2.0, 3.0)
an_array = v.to_numpy()        # Vec3  → numpy array

w = Vec3.from_list([4.0, 5.0, 6.0])          # list  → new Vec3
x = Vec3.from_numpy(np.array([7.0, 8.0, 9.0]))  # array → new Vec3
```

---

## Singular vs. plural — one thing or many things

Some languages do **not** change a word to show "one" versus "many". English
does. In this library, the singular/plural form of a name tells you whether it
deals with **one** item or **several**.

### One vector vs. a collection of vectors

```python
from ncca.ngl import Vec3, Vec3Array

point  = Vec3(1.0, 2.0, 3.0)   # Vec3      = ONE vector (singular)
points = Vec3Array()           # Vec3Array = MANY vectors (a collection)
```

The class name `Vec3` is singular: it is a single vector. The name `Vec3Array`
contains the idea of *many* — an array holds a plural collection.

### `append` (one) vs. `extend` (many)

Look carefully at the **parameter names**. The singular/plural ending is a clue.

```python
from ncca.ngl import Vec3, Vec3Array

points = Vec3Array()

points.append(Vec3(1.0, 2.0, 3.0))     # append ONE  → parameter is "value"  (singular)

points.extend([                        # extend with MANY → parameter is "values" (plural)
    Vec3(4.0, 5.0, 6.0),
    Vec3(7.0, 8.0, 9.0),
])
```

- `append(value)` — the word *value* is **singular**, so you give **one** vector.
- `extend(values)` — the word *values* is **plural**, so you give **many**
  vectors (a list).

If you give a *list* to `append`, or a *single* vector to `extend`, it will not
work — the grammar of the name told you which one to use.

---

## Full examples for the main classes

### `Vec3`

```python
from ncca.ngl import Vec3

v = Vec3(0.0, 3.0, 4.0)
n = Vec3(0.0, 1.0, 0.0)

# -ed  → new object, v unchanged
unit      = v.normalized()          # a unit-length copy
bounced   = v.reflected(n)          # reflected off normal n
limited   = v.clamped(0.0, 1.0)     # each component limited to [0, 1]

# noun → a value or new object
length    = v.length()              # 5.0
d         = v.dot(n)                # 3.0

# command → v itself changes
v.set(1.0, 1.0, 1.0)                # v is now (1, 1, 1)
```

### `Mat4`

```python
from ncca.ngl import Mat4

m = Mat4.rotate_x(45.0)             # "rotate_x" builds a rotation matrix

# -ed  → new matrix, m unchanged
flipped = m.transposed()            # rows and columns swapped (a new matrix)

# noun → a value or new object
det     = m.determinant()           # a single number
inv     = m.inverse()               # the inverse (a new matrix)

# You COMBINE matrices with @ (the multiply operator), which also returns a NEW matrix:
combined = Mat4.rotate_x(45.0) @ Mat4.rotate_y(90.0)
```

> Note: `m.transposed()` returns a new matrix. To change `m`, you must assign:
> `m = m.transposed()`.

### `Quaternion`

```python
from ncca.ngl import Quaternion, Vec3

q = Quaternion.from_axis_angle(Vec3(0.0, 1.0, 0.0), 90.0)  # build FROM axis+angle

# -ed  → new object, q unchanged
unit = q.normalized()               # a unit-length copy

# noun → a new object
conj = q.conjugate()                # the conjugate
inv  = q.inverse()                  # the inverse

# convert TO another type
m    = q.to_mat4()                  # Quaternion → Mat4
```

---

## Common mistakes and how to fix them

**Mistake 1 — Calling `-ed` methods but throwing the answer away.**

```python
v.normalized()          # ❌ does nothing useful — the new vector is lost
```
✅ **Fix:** keep the returned value.
```python
v = v.normalized()      # or: u = v.normalized()
```

**Mistake 2 — Expecting a `-ed` method to change the object.**

```python
m.transposed()
print(m)                # ❌ surprised that m is unchanged
```
✅ **Fix:** `-ed` never changes the object. Assign the result:
```python
m = m.transposed()
```

**Mistake 3 — Using the old-style plain verb.**

```python
v.normalize()           # ❌ AttributeError — this name does not exist
```
✅ **Fix:** use the `-ed` result form:
```python
v = v.normalized()
```

**Mistake 4 — Confusing `append` (one) and `extend` (many).**

```python
points.append([Vec3(1,2,3), Vec3(4,5,6)])   # ❌ a list is not one Vec3
```
✅ **Fix:** many items → use the plural `extend`:
```python
points.extend([Vec3(1,2,3), Vec3(4,5,6)])
```

---

## Quick reference cheat-sheet

| You see… | Grammar | It means… | Original changes? |
|---|---|---|---|
| `normalized()`, `reflected()`, `clamped()`, `transposed()` | past participle (`-ed`) | returns a **new** finished object | ❌ no |
| `inverse()`, `conjugate()`, `length()`, `dot()`, `determinant()`, `cross()` | noun | returns that **value / new object** | ❌ no |
| `to_list()`, `to_numpy()`, `to_mat4()` | preposition `to_` | convert **this** into another type | ❌ no |
| `from_list()`, `from_numpy()`, `from_axis_angle()` | preposition `from_` | build a **new** object from something | (makes new) |
| `set(...)` | plain verb (command) | change **this object now** | ✅ **yes** |
| `Vec3` | singular | **one** vector | — |
| `Vec3Array`, `extend(values)` | plural | **many** vectors | — |
| `append(value)` | singular parameter | **one** vector | — |

**If you remember nothing else:** words ending in **`-ed`** hand you a **new**
object — you must catch it in a variable. Only **`set`** changes the object in
your hand.
