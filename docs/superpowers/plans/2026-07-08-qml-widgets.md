# QML Widgets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `src/ncca/ngl/qml/`, a Qt Quick (QML) equivalent of `src/ncca/ngl/widgets/`, with feature parity across all 10 widgets, a demo app, tests, and docs.

**Architecture:** Each widget pairs a Python `QObject` "model" (holds the `ncca.ngl` value, exposes it via `Property`/`Signal`/`Slot`, registered as a QML type with `@QmlElement`) with a `.qml` view file that is pure declarative UI bound to the model. Mat2/Mat3/Mat4 share one generic `MatrixGridWidget.qml` parametrized by `size`. Follows `docs/superpowers/specs/2026-07-08-qml-widgets-design.md`.

**Tech Stack:** PySide6 (`QtCore`, `QtQml`, `QtQuick.Controls`, `QtQuick.Layouts`) — already a project dependency, no new packages needed. `pytest` + `pytest-qt` for model tests.

## Global Constraints

- Package root: `src/ncca/ngl/qml/`, flat layout, one model class per file, `.qml` views alongside them (per approved spec).
- Model classes registered via `@QmlElement` with `QML_IMPORT_NAME = "ncca.ngl.qml"` and `QML_IMPORT_MAJOR_VERSION = 1` (module-level constants, required in every file using the decorator).
- QML-callable Python methods keep their exact snake_case names in `.qml` bindings — PySide6 does **not** camelCase-convert `Slot`/`Property` names.
- Vector widget default range: `-5.0..5.0`, step `0.01` (matches `widgets/vec3widget.py`).
- Matrix cell default range: `-20.0..20.0`, step `0.01`; angle spin range `-360.0..360.0`, step `0.5` (matches `widgets/mat_grid_widget.py`).
- Colour channel range: `0.0..1.0`, step `0.01` (matches `widgets/rgbcolourwidget.py`).
- No colour-picker popup — swatch (`Rectangle.color`) driven by a `hex` string property only (per approved spec).
- Vec2/3/4Widget's top-level component aliases for the vector components are named `xValue`/`yValue`/`zValue`/`wValue` (NOT bare `x`/`y`/`z`/`w`) — `Frame` derives from `Item`, which declares `x`/`y`/`z` as Qt `FINAL` properties, so `property alias x: vecModel.x` on a `Frame`-rooted component is rejected by the QML engine at load time ("Cannot override FINAL property"). Discovered and fixed during Task 11's implementation; every task that binds to a `Vec2Widget`/`Vec3Widget`/`Vec4Widget` instance's component values (Mat3/Mat4's embedded `xyzWidget`, Transform/LookAtWidget's Position/Rotation/Scale/Eye/Look sub-widgets, `main.qml`, the tutorial doc) uses `xValue`/`yValue`/`zValue`/`wValue`. The underlying `Vec2Model`/`Vec3Model`/`Vec4Model` Python properties are unaffected and remain plain `x`/`y`/`z`/`w` (they're not QtQuick `Item`s, so no collision there).
- Model-layer tests use the existing `qt_app`/`qtbot` fixtures from `tests/conftest.py`, marked `qt` (auto-deselected from the default `uv run pytest` run, run via `uv run pytest -m qt`).
- Every new public class needs a complete Google-style docstring and type hints (`ruff check src/` enforces `ANN`/`D` rules — this is a blocking CI job).
- Doc-sync: any new public class/module needs a `::: ncca.ngl.qml...` entry in a new `docs/docs/QmlWidgets.md`, a nav entry in `docs/mkdocs.yml`, and `uv run --with mkdocs --with "mkdocstrings[python]" mkdocs build --strict -f docs/mkdocs.yml` must pass with zero warnings before the final commit.

---

### Task 1: Package scaffold + Vec2Model

**Files:**
- Create: `src/ncca/ngl/qml/__init__.py`
- Create: `src/ncca/ngl/qml/vec2_model.py`
- Test: `tests/test_qml_vec2_model.py`

**Interfaces:**
- Consumes: `ncca.ngl.Vec2` (existing).
- Produces: `Vec2Model` — `QObject` with `Property(float) x`, `Property(float) y` (both `notify=valueChanged`), `Signal() valueChanged`, `Slot(result=Vec2) get_value()`, `Slot(Vec2) set_value(value)`. Later vector models (`Vec3Model`, `Vec4Model`) follow this exact shape with more components.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_qml_vec2_model.py
from ncca.ngl import Vec2


def test_vec2_model_default_value_is_zero(qt_app):
    from ncca.ngl.qml.vec2_model import Vec2Model

    model = Vec2Model()

    assert model.get_value() == Vec2(0.0, 0.0)


def test_setting_x_property_updates_value(qt_app):
    from ncca.ngl.qml.vec2_model import Vec2Model

    model = Vec2Model()

    model.x = 3.5

    assert model.get_value() == Vec2(3.5, 0.0)


def test_setting_y_property_updates_value(qt_app):
    from ncca.ngl.qml.vec2_model import Vec2Model

    model = Vec2Model()

    model.y = -2.0

    assert model.get_value() == Vec2(0.0, -2.0)


def test_setting_a_property_emits_value_changed(qt_app, qtbot):
    from ncca.ngl.qml.vec2_model import Vec2Model

    model = Vec2Model()

    with qtbot.waitSignal(model.valueChanged, timeout=1000):
        model.x = 1.0


def test_set_value_replaces_whole_vector(qt_app):
    from ncca.ngl.qml.vec2_model import Vec2Model

    model = Vec2Model()

    model.set_value(Vec2(2.0, 4.0))

    assert model.x == 2.0
    assert model.y == 4.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_qml_vec2_model.py -m qt -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'ncca.ngl.qml'`

- [ ] **Step 3: Write the package scaffold**

```python
# src/ncca/ngl/qml/__init__.py
"""QML widgets exposing NGL math types to Qt Quick applications."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ncca-ngl")  # pragma: no cover
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

__author__ = "Jon Macey jmacey@bournemouth.ac.uk"
__license__ = "MIT"

from .vec2_model import Vec2Model

__all__ = [
    "Vec2Model",
]
```

- [ ] **Step 4: Write minimal implementation**

```python
# src/ncca/ngl/qml/vec2_model.py
"""QML-exposed model for editing a Vec2."""

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtQml import QmlElement

from ncca.ngl import Vec2

QML_IMPORT_NAME = "ncca.ngl.qml"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class Vec2Model(QObject):
    """Holds a Vec2 and exposes its components as QML properties."""

    valueChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the model with a zero Vec2.

        Args:
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._value = Vec2(0.0, 0.0)

    def get_x(self) -> float:
        """Return the x component.

        Returns:
            The current x value.
        """
        return float(self._value.x)

    def set_x(self, value: float) -> None:
        """Set the x component and emit valueChanged.

        Args:
            value: The new x value.
        """
        self._value.x = value
        self.valueChanged.emit()

    def get_y(self) -> float:
        """Return the y component.

        Returns:
            The current y value.
        """
        return float(self._value.y)

    def set_y(self, value: float) -> None:
        """Set the y component and emit valueChanged.

        Args:
            value: The new y value.
        """
        self._value.y = value
        self.valueChanged.emit()

    x = Property(float, get_x, set_x, notify=valueChanged)
    y = Property(float, get_y, set_y, notify=valueChanged)

    @Slot(result=Vec2)
    def get_value(self) -> Vec2:
        """Return the current Vec2 value.

        Returns:
            The current value.
        """
        return self._value

    @Slot(Vec2)
    def set_value(self, value: Vec2) -> None:
        """Replace the current value and emit valueChanged.

        Args:
            value: The new Vec2 value.
        """
        self._value = value
        self.valueChanged.emit()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_qml_vec2_model.py -m qt -v`
Expected: PASS (5 tests)

- [ ] **Step 6: Commit**

```bash
git add src/ncca/ngl/qml/__init__.py src/ncca/ngl/qml/vec2_model.py tests/test_qml_vec2_model.py
git commit -m "feat(qml): add Vec2Model"
```

---

### Task 2: Vec3Model

**Files:**
- Create: `src/ncca/ngl/qml/vec3_model.py`
- Modify: `src/ncca/ngl/qml/__init__.py` (add `Vec3Model` import + `__all__` entry)
- Test: `tests/test_qml_vec3_model.py`

**Interfaces:**
- Consumes: `ncca.ngl.Vec3`.
- Produces: `Vec3Model` — same shape as `Vec2Model` plus a `z` property. Used directly by `TransformModel`/`LookAtModel` (Task 7/8) as child position/rotation/scale and eye/look models.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_qml_vec3_model.py
from ncca.ngl import Vec3


def test_vec3_model_default_value_is_zero(qt_app):
    from ncca.ngl.qml.vec3_model import Vec3Model

    model = Vec3Model()

    assert model.get_value() == Vec3(0.0, 0.0, 0.0)


def test_setting_xyz_properties_updates_value(qt_app):
    from ncca.ngl.qml.vec3_model import Vec3Model

    model = Vec3Model()

    model.x = 1.0
    model.y = 2.0
    model.z = 3.0

    assert model.get_value() == Vec3(1.0, 2.0, 3.0)


def test_setting_z_property_emits_value_changed(qt_app, qtbot):
    from ncca.ngl.qml.vec3_model import Vec3Model

    model = Vec3Model()

    with qtbot.waitSignal(model.valueChanged, timeout=1000):
        model.z = 5.0


def test_set_value_replaces_whole_vector(qt_app):
    from ncca.ngl.qml.vec3_model import Vec3Model

    model = Vec3Model()

    model.set_value(Vec3(2.0, 4.0, 6.0))

    assert (model.x, model.y, model.z) == (2.0, 4.0, 6.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_qml_vec3_model.py -m qt -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'ncca.ngl.qml.vec3_model'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/ncca/ngl/qml/vec3_model.py
"""QML-exposed model for editing a Vec3."""

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtQml import QmlElement

from ncca.ngl import Vec3

QML_IMPORT_NAME = "ncca.ngl.qml"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class Vec3Model(QObject):
    """Holds a Vec3 and exposes its components as QML properties."""

    valueChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the model with a zero Vec3.

        Args:
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._value = Vec3(0.0, 0.0, 0.0)

    def get_x(self) -> float:
        """Return the x component.

        Returns:
            The current x value.
        """
        return float(self._value.x)

    def set_x(self, value: float) -> None:
        """Set the x component and emit valueChanged.

        Args:
            value: The new x value.
        """
        self._value.x = value
        self.valueChanged.emit()

    def get_y(self) -> float:
        """Return the y component.

        Returns:
            The current y value.
        """
        return float(self._value.y)

    def set_y(self, value: float) -> None:
        """Set the y component and emit valueChanged.

        Args:
            value: The new y value.
        """
        self._value.y = value
        self.valueChanged.emit()

    def get_z(self) -> float:
        """Return the z component.

        Returns:
            The current z value.
        """
        return float(self._value.z)

    def set_z(self, value: float) -> None:
        """Set the z component and emit valueChanged.

        Args:
            value: The new z value.
        """
        self._value.z = value
        self.valueChanged.emit()

    x = Property(float, get_x, set_x, notify=valueChanged)
    y = Property(float, get_y, set_y, notify=valueChanged)
    z = Property(float, get_z, set_z, notify=valueChanged)

    @Slot(result=Vec3)
    def get_value(self) -> Vec3:
        """Return the current Vec3 value.

        Returns:
            The current value.
        """
        return self._value

    @Slot(Vec3)
    def set_value(self, value: Vec3) -> None:
        """Replace the current value and emit valueChanged.

        Args:
            value: The new Vec3 value.
        """
        self._value = value
        self.valueChanged.emit()
```

- [ ] **Step 4: Register in `__init__.py`**

```python
# src/ncca/ngl/qml/__init__.py  (edit)
from .vec2_model import Vec2Model
from .vec3_model import Vec3Model

__all__ = [
    "Vec2Model",
    "Vec3Model",
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_qml_vec3_model.py -m qt -v`
Expected: PASS (4 tests)

- [ ] **Step 6: Commit**

```bash
git add src/ncca/ngl/qml/vec3_model.py src/ncca/ngl/qml/__init__.py tests/test_qml_vec3_model.py
git commit -m "feat(qml): add Vec3Model"
```

---

### Task 3: Vec4Model

**Files:**
- Create: `src/ncca/ngl/qml/vec4_model.py`
- Modify: `src/ncca/ngl/qml/__init__.py`
- Test: `tests/test_qml_vec4_model.py`

**Interfaces:**
- Consumes: `ncca.ngl.Vec4`.
- Produces: `Vec4Model` — same shape as `Vec3Model` plus a `w` property.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_qml_vec4_model.py
from ncca.ngl import Vec4


def test_vec4_model_default_value_is_zero(qt_app):
    from ncca.ngl.qml.vec4_model import Vec4Model

    model = Vec4Model()

    assert model.get_value() == Vec4(0.0, 0.0, 0.0, 0.0)


def test_setting_xyzw_properties_updates_value(qt_app):
    from ncca.ngl.qml.vec4_model import Vec4Model

    model = Vec4Model()

    model.x = 1.0
    model.y = 2.0
    model.z = 3.0
    model.w = 4.0

    assert model.get_value() == Vec4(1.0, 2.0, 3.0, 4.0)


def test_setting_w_property_emits_value_changed(qt_app, qtbot):
    from ncca.ngl.qml.vec4_model import Vec4Model

    model = Vec4Model()

    with qtbot.waitSignal(model.valueChanged, timeout=1000):
        model.w = 1.0


def test_set_value_replaces_whole_vector(qt_app):
    from ncca.ngl.qml.vec4_model import Vec4Model

    model = Vec4Model()

    model.set_value(Vec4(2.0, 4.0, 6.0, 8.0))

    assert (model.x, model.y, model.z, model.w) == (2.0, 4.0, 6.0, 8.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_qml_vec4_model.py -m qt -v`
Expected: FAIL/ERROR — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/ncca/ngl/qml/vec4_model.py
"""QML-exposed model for editing a Vec4."""

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtQml import QmlElement

from ncca.ngl import Vec4

QML_IMPORT_NAME = "ncca.ngl.qml"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class Vec4Model(QObject):
    """Holds a Vec4 and exposes its components as QML properties."""

    valueChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the model with a zero Vec4.

        Args:
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._value = Vec4(0.0, 0.0, 0.0, 0.0)

    def get_x(self) -> float:
        """Return the x component.

        Returns:
            The current x value.
        """
        return float(self._value.x)

    def set_x(self, value: float) -> None:
        """Set the x component and emit valueChanged.

        Args:
            value: The new x value.
        """
        self._value.x = value
        self.valueChanged.emit()

    def get_y(self) -> float:
        """Return the y component.

        Returns:
            The current y value.
        """
        return float(self._value.y)

    def set_y(self, value: float) -> None:
        """Set the y component and emit valueChanged.

        Args:
            value: The new y value.
        """
        self._value.y = value
        self.valueChanged.emit()

    def get_z(self) -> float:
        """Return the z component.

        Returns:
            The current z value.
        """
        return float(self._value.z)

    def set_z(self, value: float) -> None:
        """Set the z component and emit valueChanged.

        Args:
            value: The new z value.
        """
        self._value.z = value
        self.valueChanged.emit()

    def get_w(self) -> float:
        """Return the w component.

        Returns:
            The current w value.
        """
        return float(self._value.w)

    def set_w(self, value: float) -> None:
        """Set the w component and emit valueChanged.

        Args:
            value: The new w value.
        """
        self._value.w = value
        self.valueChanged.emit()

    x = Property(float, get_x, set_x, notify=valueChanged)
    y = Property(float, get_y, set_y, notify=valueChanged)
    z = Property(float, get_z, set_z, notify=valueChanged)
    w = Property(float, get_w, set_w, notify=valueChanged)

    @Slot(result=Vec4)
    def get_value(self) -> Vec4:
        """Return the current Vec4 value.

        Returns:
            The current value.
        """
        return self._value

    @Slot(Vec4)
    def set_value(self, value: Vec4) -> None:
        """Replace the current value and emit valueChanged.

        Args:
            value: The new Vec4 value.
        """
        self._value = value
        self.valueChanged.emit()
```

- [ ] **Step 4: Register in `__init__.py`**

```python
# src/ncca/ngl/qml/__init__.py  (edit)
from .vec2_model import Vec2Model
from .vec3_model import Vec3Model
from .vec4_model import Vec4Model

__all__ = [
    "Vec2Model",
    "Vec3Model",
    "Vec4Model",
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_qml_vec4_model.py -m qt -v`
Expected: PASS (4 tests)

- [ ] **Step 6: Commit**

```bash
git add src/ncca/ngl/qml/vec4_model.py src/ncca/ngl/qml/__init__.py tests/test_qml_vec4_model.py
git commit -m "feat(qml): add Vec4Model"
```

---

### Task 4: `_MatGridModel` base + Mat2Model

**Files:**
- Create: `src/ncca/ngl/qml/mat_grid_model.py`
- Create: `src/ncca/ngl/qml/mat2_model.py`
- Modify: `src/ncca/ngl/qml/__init__.py`
- Test: `tests/test_qml_mat_grid_models.py`

**Interfaces:**
- Consumes: `ncca.ngl.mat_base.MatrixBase`, `MatrixError`; `ncca.ngl.Mat2`.
- Produces: `MatGridModel` (not itself a `QmlElement` — an internal base, mirrors `_MatGridWidget`) with `Slot(int,int,result=float) get_cell(row,col)`, `Slot(int,int,float) set_cell(row,col,value)`, `get_value()/set_value()` (plain Python methods, used by tests and by `TransformModel`-style composition — not `Slot`s since callers are Python, not QML), `Slot() identity()`, `Slot() zero()`, `Slot() transpose()`, `Slot() inverse()`, `Property(str) statusMessage`, `Signal() valueChanged`, `Signal() statusMessageChanged`. Subclasses set class attributes `mat_cls` and `size`. `Mat2Model(MatGridModel)` sets `mat_cls = Mat2`, `size = 2`, no method combo. Task 5/6 (`Mat3Model`/`Mat4Model`) subclass this and add `method_names()`/`method_kind()`/`apply_angle_method()`/`apply_xyz_method()`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_qml_mat_grid_models.py
import pytest

from ncca.ngl import Mat2
from ncca.ngl.mat_base import MatrixError

WIDGET_CASES = [
    ("ncca.ngl.qml.mat2_model", "Mat2Model", Mat2, 2),
]


def _load_model_cls(module_name, class_name):
    import importlib

    module = importlib.import_module(module_name)
    return getattr(module, class_name)


@pytest.mark.parametrize("module_name,class_name,mat_cls,size", WIDGET_CASES)
def test_default_value_is_identity(qt_app, module_name, class_name, mat_cls, size):
    model = _load_model_cls(module_name, class_name)()

    assert model.get_value() == mat_cls.identity()


@pytest.mark.parametrize("module_name,class_name,mat_cls,size", WIDGET_CASES)
def test_get_and_set_cell_round_trip(qt_app, module_name, class_name, mat_cls, size):
    model = _load_model_cls(module_name, class_name)()

    model.set_cell(0, 1, 3.5)

    assert model.get_cell(0, 1) == pytest.approx(3.5)


@pytest.mark.parametrize("module_name,class_name,mat_cls,size", WIDGET_CASES)
def test_set_cell_emits_value_changed(qt_app, qtbot, module_name, class_name, mat_cls, size):
    model = _load_model_cls(module_name, class_name)()

    with qtbot.waitSignal(model.valueChanged, timeout=1000):
        model.set_cell(0, 0, 9.0)


@pytest.mark.parametrize("module_name,class_name,mat_cls,size", WIDGET_CASES)
def test_zero_then_identity_round_trip(qt_app, module_name, class_name, mat_cls, size):
    model = _load_model_cls(module_name, class_name)()

    model.zero()
    assert model.get_value() == mat_cls.zero()

    model.identity()
    assert model.get_value() == mat_cls.identity()


@pytest.mark.parametrize("module_name,class_name,mat_cls,size", WIDGET_CASES)
def test_transpose_reflects_current_value(qt_app, module_name, class_name, mat_cls, size):
    model = _load_model_cls(module_name, class_name)()
    model.set_cell(0, 1, 7.0)

    model.transpose()

    assert model.get_cell(1, 0) == pytest.approx(7.0)


@pytest.mark.parametrize("module_name,class_name,mat_cls,size", WIDGET_CASES)
def test_inverse_of_singular_matrix_sets_status_message(
    qt_app, module_name, class_name, mat_cls, size
):
    model = _load_model_cls(module_name, class_name)()
    model.zero()

    model.inverse()

    assert model.statusMessage == "Matrix is singular"
    assert model.get_value() == mat_cls.zero()


@pytest.mark.parametrize("module_name,class_name,mat_cls,size", WIDGET_CASES)
def test_inverse_of_identity_is_identity_and_clears_status(
    qt_app, module_name, class_name, mat_cls, size
):
    model = _load_model_cls(module_name, class_name)()

    model.inverse()

    assert model.statusMessage == ""
    assert model.get_value() == mat_cls.identity()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_qml_mat_grid_models.py -m qt -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'ncca.ngl.qml.mat2_model'`

- [ ] **Step 3: Write the base model**

```python
# src/ncca/ngl/qml/mat_grid_model.py
"""Shared base model for editable NxN matrix grids (Mat2/Mat3/Mat4)."""

from PySide6.QtCore import Property, QObject, Signal, Slot

from ncca.ngl.mat_base import MatrixBase, MatrixError


class MatGridModel(QObject):
    """Base QObject exposing an NxN MatrixBase value to QML.

    Not registered as a QML type directly; Mat2Model/Mat3Model/Mat4Model
    subclass it, setting the `mat_cls` and `size` class attributes.
    """

    valueChanged = Signal()
    statusMessageChanged = Signal()

    mat_cls: type[MatrixBase]
    size: int

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the model with an identity matrix.

        Args:
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._value = self.mat_cls.identity()
        self._status_message = ""

    @Slot(int, int, result=float)
    def get_cell(self, row: int, col: int) -> float:
        """Return the value at (row, col).

        Args:
            row: The row index.
            col: The column index.

        Returns:
            The cell's current value.
        """
        return float(self._value[row][col])

    @Slot(int, int, float)
    def set_cell(self, row: int, col: int, value: float) -> None:
        """Set the value at (row, col) and emit valueChanged.

        Args:
            row: The row index.
            col: The column index.
            value: The new cell value.
        """
        self._value[row][col] = value
        self.valueChanged.emit()

    def get_value(self) -> MatrixBase:
        """Return the current matrix value.

        Returns:
            The current matrix.
        """
        return self._value

    def set_value(self, value: MatrixBase) -> None:
        """Replace the current matrix value and emit valueChanged.

        Args:
            value: The new matrix value.
        """
        self._value = value
        self.valueChanged.emit()

    @Slot()
    def identity(self) -> None:
        """Reset the matrix to identity."""
        self.set_value(self.mat_cls.identity())

    @Slot()
    def zero(self) -> None:
        """Reset the matrix to all zeros."""
        self.set_value(self.mat_cls.zero())

    @Slot()
    def transpose(self) -> None:
        """Replace the matrix with its transpose."""
        self.set_value(self._value.transposed())

    @Slot()
    def inverse(self) -> None:
        """Replace the matrix with its inverse, or set a status message if singular."""
        try:
            inverted = self._value.inverse()
        except MatrixError:
            self._status_message = "Matrix is singular"
            self.statusMessageChanged.emit()
            return
        self._status_message = ""
        self.statusMessageChanged.emit()
        self.set_value(inverted)

    def get_status_message(self) -> str:
        """Return the current status message.

        Returns:
            The status message, or an empty string if none.
        """
        return self._status_message

    statusMessage = Property(str, get_status_message, notify=statusMessageChanged)
```

- [ ] **Step 4: Write Mat2Model**

```python
# src/ncca/ngl/qml/mat2_model.py
"""QML-exposed model for editing a Mat2 as a 2x2 grid."""

from PySide6.QtQml import QmlElement

from ncca.ngl import Mat2

from .mat_grid_model import MatGridModel

QML_IMPORT_NAME = "ncca.ngl.qml"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class Mat2Model(MatGridModel):
    """Grid model for a Mat2. No rotate/scale method combo (mirrors Mat2Widget)."""

    mat_cls = Mat2
    size = 2
```

- [ ] **Step 5: Register in `__init__.py`**

```python
# src/ncca/ngl/qml/__init__.py  (edit)
from .mat2_model import Mat2Model
from .vec2_model import Vec2Model
from .vec3_model import Vec3Model
from .vec4_model import Vec4Model

__all__ = [
    "Vec2Model",
    "Vec3Model",
    "Vec4Model",
    "Mat2Model",
]
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_qml_mat_grid_models.py -m qt -v`
Expected: PASS (7 tests)

- [ ] **Step 7: Commit**

```bash
git add src/ncca/ngl/qml/mat_grid_model.py src/ncca/ngl/qml/mat2_model.py src/ncca/ngl/qml/__init__.py tests/test_qml_mat_grid_models.py
git commit -m "feat(qml): add MatGridModel base and Mat2Model"
```

---

### Task 5: Mat3Model (rotate/scale method combo)

**Files:**
- Create: `src/ncca/ngl/qml/mat3_model.py`
- Modify: `src/ncca/ngl/qml/__init__.py`
- Modify: `tests/test_qml_mat_grid_models.py` (add Mat3 to `WIDGET_CASES`)
- Test: `tests/test_qml_mat3_model.py` (method-combo behaviour, not covered by the shared parametrized suite)

**Interfaces:**
- Consumes: `ncca.ngl.Mat3`.
- Produces: `Mat3Model(MatGridModel)` adding `Slot(result=list) method_names()`, `Slot(str,result=str) method_kind(name)` (returns `"angle"` or `"xyz"`), `Slot(str,float) apply_angle_method(name, degrees)`, `Slot(str,float,float,float) apply_xyz_method(name, x, y, z)`. Same shape reused verbatim by `Mat4Model` (Task 6) with a longer method table.

- [ ] **Step 1: Extend the shared parametrized test with Mat3**

```python
# tests/test_qml_mat_grid_models.py  (edit WIDGET_CASES)
from ncca.ngl import Mat2, Mat3

WIDGET_CASES = [
    ("ncca.ngl.qml.mat2_model", "Mat2Model", Mat2, 2),
    ("ncca.ngl.qml.mat3_model", "Mat3Model", Mat3, 3),
]
```

- [ ] **Step 2: Write the method-combo test**

```python
# tests/test_qml_mat3_model.py
import pytest

from ncca.ngl import Mat3


def test_method_names_lists_rotate_and_scale(qt_app):
    from ncca.ngl.qml.mat3_model import Mat3Model

    model = Mat3Model()

    assert model.method_names() == ["rotate_x", "rotate_y", "rotate_z", "scale"]


def test_method_kind_angle_vs_xyz(qt_app):
    from ncca.ngl.qml.mat3_model import Mat3Model

    model = Mat3Model()

    assert model.method_kind("rotate_x") == "angle"
    assert model.method_kind("scale") == "xyz"


def test_apply_angle_method_matches_classmethod(qt_app):
    from ncca.ngl.qml.mat3_model import Mat3Model

    model = Mat3Model()

    model.apply_angle_method("rotate_y", 45.0)

    assert model.get_value() == Mat3.rotate_y(45.0)


def test_apply_xyz_method_matches_classmethod(qt_app):
    from ncca.ngl.qml.mat3_model import Mat3Model

    model = Mat3Model()

    model.apply_xyz_method("scale", 2.0, 3.0, 4.0)

    assert model.get_value() == Mat3.scale(2.0, 3.0, 4.0)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_qml_mat3_model.py tests/test_qml_mat_grid_models.py -m qt -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'ncca.ngl.qml.mat3_model'`

- [ ] **Step 4: Write minimal implementation**

```python
# src/ncca/ngl/qml/mat3_model.py
"""QML-exposed model for editing a Mat3 as a 3x3 grid with a method combo."""

from PySide6.QtCore import Slot
from PySide6.QtQml import QmlElement

from ncca.ngl import Mat3

from .mat_grid_model import MatGridModel

QML_IMPORT_NAME = "ncca.ngl.qml"
QML_IMPORT_MAJOR_VERSION = 1

_METHODS = {
    "rotate_x": ("angle", Mat3.rotate_x),
    "rotate_y": ("angle", Mat3.rotate_y),
    "rotate_z": ("angle", Mat3.rotate_z),
    "scale": ("xyz", Mat3.scale),
}


@QmlElement
class Mat3Model(MatGridModel):
    """Grid model for a Mat3, with a rotate/scale method combo."""

    mat_cls = Mat3
    size = 3

    @Slot(result=list)
    def method_names(self) -> list:
        """Return the ordered list of available method names for the combo box.

        Returns:
            The method display names, in combo-box order.
        """
        return list(_METHODS)

    @Slot(str, result=str)
    def method_kind(self, name: str) -> str:
        """Return the parameter kind for a method name.

        Args:
            name: One of the names returned by `method_names()`.

        Returns:
            `"angle"` for a single-degrees method, `"xyz"` for a 3-component one.
        """
        return _METHODS[name][0]

    @Slot(str, float)
    def apply_angle_method(self, name: str, degrees: float) -> None:
        """Apply an angle-based method (rotate_x/y/z) by degrees.

        Args:
            name: The method name (must have kind `"angle"`).
            degrees: The rotation angle in degrees.
        """
        _, factory = _METHODS[name]
        self.set_value(factory(degrees))

    @Slot(str, float, float, float)
    def apply_xyz_method(self, name: str, x: float, y: float, z: float) -> None:
        """Apply an xyz-based method (scale) with the given components.

        Args:
            name: The method name (must have kind `"xyz"`).
            x: The x component.
            y: The y component.
            z: The z component.
        """
        _, factory = _METHODS[name]
        self.set_value(factory(x, y, z))
```

- [ ] **Step 5: Register in `__init__.py`**

```python
# src/ncca/ngl/qml/__init__.py  (edit)
from .mat2_model import Mat2Model
from .mat3_model import Mat3Model
from .vec2_model import Vec2Model
from .vec3_model import Vec3Model
from .vec4_model import Vec4Model

__all__ = [
    "Vec2Model",
    "Vec3Model",
    "Vec4Model",
    "Mat2Model",
    "Mat3Model",
]
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_qml_mat3_model.py tests/test_qml_mat_grid_models.py -m qt -v`
Expected: PASS (4 + 14 tests)

- [ ] **Step 7: Commit**

```bash
git add src/ncca/ngl/qml/mat3_model.py src/ncca/ngl/qml/__init__.py tests/test_qml_mat3_model.py tests/test_qml_mat_grid_models.py
git commit -m "feat(qml): add Mat3Model with rotate/scale method combo"
```

---

### Task 6: Mat4Model (rotate/scale/translate method combo)

**Files:**
- Create: `src/ncca/ngl/qml/mat4_model.py`
- Modify: `src/ncca/ngl/qml/__init__.py`
- Modify: `tests/test_qml_mat_grid_models.py` (add Mat4 to `WIDGET_CASES`)
- Test: `tests/test_qml_mat4_model.py`

**Interfaces:**
- Consumes: `ncca.ngl.Mat4`.
- Produces: `Mat4Model(MatGridModel)` — identical shape to `Mat3Model`, method table adds `"translate"`.

- [ ] **Step 1: Extend the shared parametrized test with Mat4**

```python
# tests/test_qml_mat_grid_models.py  (edit WIDGET_CASES)
from ncca.ngl import Mat2, Mat3, Mat4

WIDGET_CASES = [
    ("ncca.ngl.qml.mat2_model", "Mat2Model", Mat2, 2),
    ("ncca.ngl.qml.mat3_model", "Mat3Model", Mat3, 3),
    ("ncca.ngl.qml.mat4_model", "Mat4Model", Mat4, 4),
]
```

- [ ] **Step 2: Write the method-combo test**

```python
# tests/test_qml_mat4_model.py
from ncca.ngl import Mat4


def test_method_names_lists_rotate_scale_translate(qt_app):
    from ncca.ngl.qml.mat4_model import Mat4Model

    model = Mat4Model()

    assert model.method_names() == [
        "rotate_x",
        "rotate_y",
        "rotate_z",
        "scale",
        "translate",
    ]


def test_apply_angle_method_matches_classmethod(qt_app):
    from ncca.ngl.qml.mat4_model import Mat4Model

    model = Mat4Model()

    model.apply_angle_method("rotate_x", 30.0)

    assert model.get_value() == Mat4.rotate_x(30.0)


def test_apply_xyz_method_translate_matches_classmethod(qt_app):
    from ncca.ngl.qml.mat4_model import Mat4Model

    model = Mat4Model()

    model.apply_xyz_method("translate", 1.0, 2.0, 3.0)

    assert model.get_value() == Mat4.translate(1.0, 2.0, 3.0)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_qml_mat4_model.py tests/test_qml_mat_grid_models.py -m qt -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'ncca.ngl.qml.mat4_model'`

- [ ] **Step 4: Write minimal implementation**

```python
# src/ncca/ngl/qml/mat4_model.py
"""QML-exposed model for editing a Mat4 as a 4x4 grid with a method combo."""

from PySide6.QtCore import Slot
from PySide6.QtQml import QmlElement

from ncca.ngl import Mat4

from .mat_grid_model import MatGridModel

QML_IMPORT_NAME = "ncca.ngl.qml"
QML_IMPORT_MAJOR_VERSION = 1

_METHODS = {
    "rotate_x": ("angle", Mat4.rotate_x),
    "rotate_y": ("angle", Mat4.rotate_y),
    "rotate_z": ("angle", Mat4.rotate_z),
    "scale": ("xyz", Mat4.scale),
    "translate": ("xyz", Mat4.translate),
}


@QmlElement
class Mat4Model(MatGridModel):
    """Grid model for a Mat4, with a rotate/scale/translate method combo."""

    mat_cls = Mat4
    size = 4

    @Slot(result=list)
    def method_names(self) -> list:
        """Return the ordered list of available method names for the combo box.

        Returns:
            The method display names, in combo-box order.
        """
        return list(_METHODS)

    @Slot(str, result=str)
    def method_kind(self, name: str) -> str:
        """Return the parameter kind for a method name.

        Args:
            name: One of the names returned by `method_names()`.

        Returns:
            `"angle"` for a single-degrees method, `"xyz"` for a 3-component one.
        """
        return _METHODS[name][0]

    @Slot(str, float)
    def apply_angle_method(self, name: str, degrees: float) -> None:
        """Apply an angle-based method (rotate_x/y/z) by degrees.

        Args:
            name: The method name (must have kind `"angle"`).
            degrees: The rotation angle in degrees.
        """
        _, factory = _METHODS[name]
        self.set_value(factory(degrees))

    @Slot(str, float, float, float)
    def apply_xyz_method(self, name: str, x: float, y: float, z: float) -> None:
        """Apply an xyz-based method (scale/translate) with the given components.

        Args:
            name: The method name (must have kind `"xyz"`).
            x: The x component.
            y: The y component.
            z: The z component.
        """
        _, factory = _METHODS[name]
        self.set_value(factory(x, y, z))
```

- [ ] **Step 5: Register in `__init__.py`**

```python
# src/ncca/ngl/qml/__init__.py  (edit)
from .mat2_model import Mat2Model
from .mat3_model import Mat3Model
from .mat4_model import Mat4Model
from .vec2_model import Vec2Model
from .vec3_model import Vec3Model
from .vec4_model import Vec4Model

__all__ = [
    "Vec2Model",
    "Vec3Model",
    "Vec4Model",
    "Mat2Model",
    "Mat3Model",
    "Mat4Model",
]
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_qml_mat4_model.py tests/test_qml_mat_grid_models.py -m qt -v`
Expected: PASS (3 + 21 tests)

- [ ] **Step 7: Commit**

```bash
git add src/ncca/ngl/qml/mat4_model.py src/ncca/ngl/qml/__init__.py tests/test_qml_mat4_model.py tests/test_qml_mat_grid_models.py
git commit -m "feat(qml): add Mat4Model with rotate/scale/translate method combo"
```

---

### Task 7: TransformModel

**Files:**
- Create: `src/ncca/ngl/qml/transform_model.py`
- Modify: `src/ncca/ngl/qml/__init__.py`
- Test: `tests/test_qml_transform_model.py`

**Interfaces:**
- Consumes: `ncca.ngl.Mat4`, `ncca.ngl.Transform`; `Vec3Model` (Task 2).
- Produces: `TransformModel` — `Property(QObject) position/rotation/scale` (constant, each a child `Vec3Model`), `Property(int) rotationOrderIndex`, `Slot(result=list) rotation_orders()`, `Property(Mat4) matrix` (notify=`valueChanged`), `Slot(result=str) matrix_text()` (for demo display), `Signal() valueChanged`. Recomputes `matrix` whenever `position`/`rotation`/`scale`/`rotationOrderIndex` change, via `ncca.ngl.Transform`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_qml_transform_model.py
from ncca.ngl import Transform, Vec3


def test_default_matrix_matches_default_transform(qt_app):
    from ncca.ngl.qml.transform_model import TransformModel

    model = TransformModel()

    assert model.get_matrix() == Transform().matrix()


def test_setting_position_updates_matrix(qt_app):
    from ncca.ngl.qml.transform_model import TransformModel

    model = TransformModel()

    model.position.x = 1.0
    model.position.y = 2.0
    model.position.z = 3.0

    expected = Transform()
    expected.set_position(1.0, 2.0, 3.0)
    assert model.get_matrix() == expected.matrix()


def test_setting_scale_updates_matrix(qt_app):
    from ncca.ngl.qml.transform_model import TransformModel

    model = TransformModel()

    model.scale.x = 2.0
    model.scale.y = 2.0
    model.scale.z = 2.0

    expected = Transform()
    expected.set_scale(2.0, 2.0, 2.0)
    assert model.get_matrix() == expected.matrix()


def test_scale_defaults_to_one(qt_app):
    from ncca.ngl.qml.transform_model import TransformModel

    model = TransformModel()

    assert (model.scale.x, model.scale.y, model.scale.z) == (1.0, 1.0, 1.0)


def test_changing_rotation_order_updates_matrix(qt_app):
    from ncca.ngl.qml.transform_model import TransformModel

    model = TransformModel()
    model.rotation.x = 10.0
    model.rotation.y = 20.0
    model.rotation.z = 30.0

    model.rotationOrderIndex = model.rotation_orders().index("zyx")

    expected = Transform()
    expected.set_order("zyx")
    expected.set_rotation(10.0, 20.0, 30.0)
    assert model.get_matrix() == expected.matrix()


def test_setting_position_emits_value_changed(qt_app, qtbot):
    from ncca.ngl.qml.transform_model import TransformModel

    model = TransformModel()

    with qtbot.waitSignal(model.valueChanged, timeout=1000):
        model.position.x = 5.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_qml_transform_model.py -m qt -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'ncca.ngl.qml.transform_model'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/ncca/ngl/qml/transform_model.py
"""QML-exposed model combining position/rotation/scale into a Transform matrix."""

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtQml import QmlElement

from ncca.ngl import Mat4, Transform

from .vec3_model import Vec3Model

QML_IMPORT_NAME = "ncca.ngl.qml"
QML_IMPORT_MAJOR_VERSION = 1

ROTATION_ORDERS = ["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"]


@QmlElement
class TransformModel(QObject):
    """Combines position/rotation/scale Vec3Models into a Mat4 transform."""

    valueChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize child position/rotation/scale models and compute the matrix.

        Args:
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._position = Vec3Model(self)
        self._rotation = Vec3Model(self)
        self._scale = Vec3Model(self)
        self._scale.x = 1.0
        self._scale.y = 1.0
        self._scale.z = 1.0
        self._rotation_order_index = 0
        self._matrix = Mat4()
        self._position.valueChanged.connect(self._update_matrix)
        self._rotation.valueChanged.connect(self._update_matrix)
        self._scale.valueChanged.connect(self._update_matrix)
        self._update_matrix()

    def get_position(self) -> Vec3Model:
        """Return the position child model.

        Returns:
            The position Vec3Model.
        """
        return self._position

    def get_rotation(self) -> Vec3Model:
        """Return the rotation child model.

        Returns:
            The rotation Vec3Model.
        """
        return self._rotation

    def get_scale(self) -> Vec3Model:
        """Return the scale child model.

        Returns:
            The scale Vec3Model.
        """
        return self._scale

    position = Property(QObject, get_position, constant=True)
    rotation = Property(QObject, get_rotation, constant=True)
    scale = Property(QObject, get_scale, constant=True)

    def get_rotation_order_index(self) -> int:
        """Return the index into ROTATION_ORDERS currently in use.

        Returns:
            The current rotation order index.
        """
        return self._rotation_order_index

    def set_rotation_order_index(self, index: int) -> None:
        """Set the rotation order by index and recompute the matrix.

        Args:
            index: An index into ROTATION_ORDERS.
        """
        self._rotation_order_index = index
        self._update_matrix()

    rotationOrderIndex = Property(
        int, get_rotation_order_index, set_rotation_order_index, notify=valueChanged
    )

    @Slot(result=list)
    def rotation_orders(self) -> list:
        """Return the ordered list of valid rotation order strings.

        Returns:
            The rotation order names, in combo-box order.
        """
        return list(ROTATION_ORDERS)

    def _update_matrix(self) -> None:
        """Recompute the transform matrix from the current child values."""
        position = self._position.get_value()
        rotation = self._rotation.get_value()
        scale = self._scale.get_value()

        tx = Transform()
        tx.set_order(ROTATION_ORDERS[self._rotation_order_index])
        tx.set_position(position.x, position.y, position.z)
        tx.set_rotation(rotation.x, rotation.y, rotation.z)
        tx.set_scale(scale.x, scale.y, scale.z)
        self._matrix = tx.matrix()
        self.valueChanged.emit()

    @Slot(result=Mat4)
    def get_matrix(self) -> Mat4:
        """Return the current transform matrix.

        Returns:
            The current Mat4.
        """
        return self._matrix

    matrix = Property(Mat4, get_matrix, notify=valueChanged)

    @Slot(result=str)
    def matrix_text(self) -> str:
        """Return the current matrix formatted as a readable multi-line string.

        Returns:
            The matrix formatted with 2 decimal places per cell.
        """
        rows = [
            " ".join(f"{self._matrix[r][c]:6.2f}" for c in range(4)) for r in range(4)
        ]
        return "\n".join(rows)
```

- [ ] **Step 4: Register in `__init__.py`**

```python
# src/ncca/ngl/qml/__init__.py  (edit)
from .mat2_model import Mat2Model
from .mat3_model import Mat3Model
from .mat4_model import Mat4Model
from .transform_model import TransformModel
from .vec2_model import Vec2Model
from .vec3_model import Vec3Model
from .vec4_model import Vec4Model

__all__ = [
    "Vec2Model",
    "Vec3Model",
    "Vec4Model",
    "Mat2Model",
    "Mat3Model",
    "Mat4Model",
    "TransformModel",
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_qml_transform_model.py -m qt -v`
Expected: PASS (6 tests)

- [ ] **Step 6: Commit**

```bash
git add src/ncca/ngl/qml/transform_model.py src/ncca/ngl/qml/__init__.py tests/test_qml_transform_model.py
git commit -m "feat(qml): add TransformModel"
```

---

### Task 8: LookAtModel

**Files:**
- Create: `src/ncca/ngl/qml/lookat_model.py`
- Modify: `src/ncca/ngl/qml/__init__.py`
- Test: `tests/test_qml_lookat_model.py`

**Interfaces:**
- Consumes: `ncca.ngl.Mat4`, `ncca.ngl.Vec3`, `ncca.ngl.look_at`; `Vec3Model`.
- Produces: `LookAtModel` — `Property(QObject) eye/look` (constant, child `Vec3Model`s, `eye` defaults to `(2,2,2)`), `Property(int) upIndex`, `Slot(result=list) up_names()`, `Property(Mat4) matrix` (notify=`valueChanged`), `Slot(result=str) matrix_text()`, `Signal() valueChanged`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_qml_lookat_model.py
from ncca.ngl import Vec3, look_at


def test_default_eye_and_matrix(qt_app):
    from ncca.ngl.qml.lookat_model import LookAtModel

    model = LookAtModel()

    assert (model.eye.x, model.eye.y, model.eye.z) == (2.0, 2.0, 2.0)
    assert model.get_matrix() == look_at(Vec3(2, 2, 2), Vec3(0, 0, 0), Vec3(0, 1, 0))


def test_changing_eye_updates_matrix(qt_app):
    from ncca.ngl.qml.lookat_model import LookAtModel

    model = LookAtModel()

    model.eye.x = 5.0
    model.eye.y = 0.0
    model.eye.z = 0.0

    assert model.get_matrix() == look_at(Vec3(5, 0, 0), Vec3(0, 0, 0), Vec3(0, 1, 0))


def test_changing_up_index_updates_matrix(qt_app):
    from ncca.ngl.qml.lookat_model import LookAtModel

    model = LookAtModel()

    model.upIndex = model.up_names().index("x-up")

    assert model.get_matrix() == look_at(Vec3(2, 2, 2), Vec3(0, 0, 0), Vec3(1, 0, 0))


def test_changing_eye_emits_value_changed(qt_app, qtbot):
    from ncca.ngl.qml.lookat_model import LookAtModel

    model = LookAtModel()

    with qtbot.waitSignal(model.valueChanged, timeout=1000):
        model.eye.x = 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_qml_lookat_model.py -m qt -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'ncca.ngl.qml.lookat_model'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/ncca/ngl/qml/lookat_model.py
"""QML-exposed model combining eye/look/up into a look_at view matrix."""

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtQml import QmlElement

from ncca.ngl import Mat4, Vec3, look_at

from .vec3_model import Vec3Model

QML_IMPORT_NAME = "ncca.ngl.qml"
QML_IMPORT_MAJOR_VERSION = 1

WORLD_UP = [Vec3(0, 1, 0), Vec3(1, 0, 0), Vec3(0, 0, 1)]
WORLD_UP_NAMES = ["y-up", "x-up", "z-up"]


@QmlElement
class LookAtModel(QObject):
    """Combines eye/look Vec3Models and a world-up choice into a view Mat4."""

    valueChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize eye/look child models and compute the initial view matrix.

        Args:
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._eye = Vec3Model(self)
        self._eye.x = 2.0
        self._eye.y = 2.0
        self._eye.z = 2.0
        self._look = Vec3Model(self)
        self._up_index = 0
        self._matrix = Mat4()
        self._eye.valueChanged.connect(self._update_matrix)
        self._look.valueChanged.connect(self._update_matrix)
        self._update_matrix()

    def get_eye(self) -> Vec3Model:
        """Return the eye child model.

        Returns:
            The eye Vec3Model.
        """
        return self._eye

    def get_look(self) -> Vec3Model:
        """Return the look-at child model.

        Returns:
            The look Vec3Model.
        """
        return self._look

    eye = Property(QObject, get_eye, constant=True)
    look = Property(QObject, get_look, constant=True)

    def get_up_index(self) -> int:
        """Return the index into WORLD_UP currently in use.

        Returns:
            The current world-up index.
        """
        return self._up_index

    def set_up_index(self, index: int) -> None:
        """Set the world-up vector by index and recompute the matrix.

        Args:
            index: An index into WORLD_UP.
        """
        self._up_index = index
        self._update_matrix()

    upIndex = Property(int, get_up_index, set_up_index, notify=valueChanged)

    @Slot(result=list)
    def up_names(self) -> list:
        """Return the ordered list of world-up display names.

        Returns:
            The world-up names, in combo-box order.
        """
        return list(WORLD_UP_NAMES)

    def _update_matrix(self) -> None:
        """Recompute the view matrix from the current eye/look/up values."""
        eye = self._eye.get_value()
        look = self._look.get_value()
        up = WORLD_UP[self._up_index]
        self._matrix = look_at(eye, look, up)
        self.valueChanged.emit()

    @Slot(result=Mat4)
    def get_matrix(self) -> Mat4:
        """Return the current view matrix.

        Returns:
            The current Mat4.
        """
        return self._matrix

    matrix = Property(Mat4, get_matrix, notify=valueChanged)

    @Slot(result=str)
    def matrix_text(self) -> str:
        """Return the current matrix formatted as a readable multi-line string.

        Returns:
            The matrix formatted with 2 decimal places per cell.
        """
        rows = [
            " ".join(f"{self._matrix[r][c]:6.2f}" for c in range(4)) for r in range(4)
        ]
        return "\n".join(rows)
```

- [ ] **Step 4: Register in `__init__.py`**

```python
# src/ncca/ngl/qml/__init__.py  (edit)
from .lookat_model import LookAtModel
from .mat2_model import Mat2Model
from .mat3_model import Mat3Model
from .mat4_model import Mat4Model
from .transform_model import TransformModel
from .vec2_model import Vec2Model
from .vec3_model import Vec3Model
from .vec4_model import Vec4Model

__all__ = [
    "Vec2Model",
    "Vec3Model",
    "Vec4Model",
    "Mat2Model",
    "Mat3Model",
    "Mat4Model",
    "TransformModel",
    "LookAtModel",
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_qml_lookat_model.py -m qt -v`
Expected: PASS (4 tests)

- [ ] **Step 6: Commit**

```bash
git add src/ncca/ngl/qml/lookat_model.py src/ncca/ngl/qml/__init__.py tests/test_qml_lookat_model.py
git commit -m "feat(qml): add LookAtModel"
```

---

### Task 9: RGBColourModel

**Files:**
- Create: `src/ncca/ngl/qml/rgb_colour_model.py`
- Modify: `src/ncca/ngl/qml/__init__.py`
- Test: `tests/test_qml_rgb_colour_model.py`

**Interfaces:**
- Consumes: `ncca.ngl.Vec3`; `PySide6.QtGui.QColor`.
- Produces: `RGBColourModel` — `Property(float) r/g/b` (notify=`colourChanged`), `Property(str) hex` (notify=`colourChanged`, `#RRGGBB`), `Slot(result=Vec3) get_value()`, `Slot(Vec3) set_value(value)`, `Signal() colourChanged`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_qml_rgb_colour_model.py
from ncca.ngl import Vec3


def test_default_colour_is_white(qt_app):
    from ncca.ngl.qml.rgb_colour_model import RGBColourModel

    model = RGBColourModel()

    assert model.get_value() == Vec3(1.0, 1.0, 1.0)
    assert model.hex == "#ffffff"


def test_setting_r_updates_value_and_hex(qt_app):
    from ncca.ngl.qml.rgb_colour_model import RGBColourModel

    model = RGBColourModel()

    model.r = 0.0
    model.g = 0.0
    model.b = 0.0

    assert model.get_value() == Vec3(0.0, 0.0, 0.0)
    assert model.hex == "#000000"


def test_setting_g_emits_colour_changed(qt_app, qtbot):
    from ncca.ngl.qml.rgb_colour_model import RGBColourModel

    model = RGBColourModel()

    with qtbot.waitSignal(model.colourChanged, timeout=1000):
        model.g = 0.5


def test_set_value_replaces_whole_colour(qt_app):
    from ncca.ngl.qml.rgb_colour_model import RGBColourModel

    model = RGBColourModel()

    model.set_value(Vec3(0.2, 0.4, 0.6))

    assert (model.r, model.g, model.b) == (0.2, 0.4, 0.6)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_qml_rgb_colour_model.py -m qt -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'ncca.ngl.qml.rgb_colour_model'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/ncca/ngl/qml/rgb_colour_model.py
"""QML-exposed model for an RGB colour (Vec3) with a hex swatch string."""

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtQml import QmlElement

from ncca.ngl import Vec3

QML_IMPORT_NAME = "ncca.ngl.qml"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class RGBColourModel(QObject):
    """Holds an RGB Vec3 colour and exposes r/g/b plus a hex swatch colour."""

    colourChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the model with white (1, 1, 1).

        Args:
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._colour = Vec3(1.0, 1.0, 1.0)

    def get_r(self) -> float:
        """Return the red channel.

        Returns:
            The current red value.
        """
        return float(self._colour.x)

    def set_r(self, value: float) -> None:
        """Set the red channel and emit colourChanged.

        Args:
            value: The new red value.
        """
        self._colour.x = value
        self.colourChanged.emit()

    def get_g(self) -> float:
        """Return the green channel.

        Returns:
            The current green value.
        """
        return float(self._colour.y)

    def set_g(self, value: float) -> None:
        """Set the green channel and emit colourChanged.

        Args:
            value: The new green value.
        """
        self._colour.y = value
        self.colourChanged.emit()

    def get_b(self) -> float:
        """Return the blue channel.

        Returns:
            The current blue value.
        """
        return float(self._colour.z)

    def set_b(self, value: float) -> None:
        """Set the blue channel and emit colourChanged.

        Args:
            value: The new blue value.
        """
        self._colour.z = value
        self.colourChanged.emit()

    r = Property(float, get_r, set_r, notify=colourChanged)
    g = Property(float, get_g, set_g, notify=colourChanged)
    b = Property(float, get_b, set_b, notify=colourChanged)

    def get_hex(self) -> str:
        """Return the colour as a `#RRGGBB` hex string.

        Returns:
            The hex colour string.
        """
        return QColor.fromRgbF(self._colour.x, self._colour.y, self._colour.z).name()

    hex = Property(str, get_hex, notify=colourChanged)

    @Slot(result=Vec3)
    def get_value(self) -> Vec3:
        """Return the current colour as a Vec3.

        Returns:
            The current colour.
        """
        return self._colour

    @Slot(Vec3)
    def set_value(self, value: Vec3) -> None:
        """Replace the current colour and emit colourChanged.

        Args:
            value: The new colour value.
        """
        self._colour = value
        self.colourChanged.emit()
```

- [ ] **Step 4: Register in `__init__.py`**

```python
# src/ncca/ngl/qml/__init__.py  (edit)
from .lookat_model import LookAtModel
from .mat2_model import Mat2Model
from .mat3_model import Mat3Model
from .mat4_model import Mat4Model
from .rgb_colour_model import RGBColourModel
from .transform_model import TransformModel
from .vec2_model import Vec2Model
from .vec3_model import Vec3Model
from .vec4_model import Vec4Model

__all__ = [
    "Vec2Model",
    "Vec3Model",
    "Vec4Model",
    "Mat2Model",
    "Mat3Model",
    "Mat4Model",
    "TransformModel",
    "LookAtModel",
    "RGBColourModel",
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_qml_rgb_colour_model.py -m qt -v`
Expected: PASS (4 tests)

- [ ] **Step 6: Commit**

```bash
git add src/ncca/ngl/qml/rgb_colour_model.py src/ncca/ngl/qml/__init__.py tests/test_qml_rgb_colour_model.py
git commit -m "feat(qml): add RGBColourModel"
```

---

### Task 10: RGBAColourModel

**Files:**
- Create: `src/ncca/ngl/qml/rgba_colour_model.py`
- Modify: `src/ncca/ngl/qml/__init__.py`
- Test: `tests/test_qml_rgba_colour_model.py`

**Interfaces:**
- Consumes: `ncca.ngl.Vec4`; `PySide6.QtGui.QColor`.
- Produces: `RGBAColourModel` — same shape as `RGBColourModel` plus `a` property and `hex` in `#AARRGGBB` form (`QColor.NameFormat.HexArgb`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_qml_rgba_colour_model.py
from ncca.ngl import Vec4


def test_default_colour_is_opaque_white(qt_app):
    from ncca.ngl.qml.rgba_colour_model import RGBAColourModel

    model = RGBAColourModel()

    assert model.get_value() == Vec4(1.0, 1.0, 1.0, 1.0)
    assert model.hex == "#ffffffff"


def test_setting_a_updates_value_and_hex(qt_app):
    from ncca.ngl.qml.rgba_colour_model import RGBAColourModel

    model = RGBAColourModel()

    model.a = 0.0

    assert model.get_value() == Vec4(1.0, 1.0, 1.0, 0.0)
    assert model.hex == "#00ffffff"


def test_setting_a_emits_colour_changed(qt_app, qtbot):
    from ncca.ngl.qml.rgba_colour_model import RGBAColourModel

    model = RGBAColourModel()

    with qtbot.waitSignal(model.colourChanged, timeout=1000):
        model.a = 0.5


def test_set_value_replaces_whole_colour(qt_app):
    from ncca.ngl.qml.rgba_colour_model import RGBAColourModel

    model = RGBAColourModel()

    model.set_value(Vec4(0.2, 0.4, 0.6, 0.8))

    assert (model.r, model.g, model.b, model.a) == (0.2, 0.4, 0.6, 0.8)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_qml_rgba_colour_model.py -m qt -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'ncca.ngl.qml.rgba_colour_model'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/ncca/ngl/qml/rgba_colour_model.py
"""QML-exposed model for an RGBA colour (Vec4) with a hex swatch string."""

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtQml import QmlElement

from ncca.ngl import Vec4

QML_IMPORT_NAME = "ncca.ngl.qml"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
class RGBAColourModel(QObject):
    """Holds an RGBA Vec4 colour and exposes r/g/b/a plus a hex swatch colour."""

    colourChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the model with opaque white (1, 1, 1, 1).

        Args:
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._colour = Vec4(1.0, 1.0, 1.0, 1.0)

    def get_r(self) -> float:
        """Return the red channel.

        Returns:
            The current red value.
        """
        return float(self._colour.x)

    def set_r(self, value: float) -> None:
        """Set the red channel and emit colourChanged.

        Args:
            value: The new red value.
        """
        self._colour.x = value
        self.colourChanged.emit()

    def get_g(self) -> float:
        """Return the green channel.

        Returns:
            The current green value.
        """
        return float(self._colour.y)

    def set_g(self, value: float) -> None:
        """Set the green channel and emit colourChanged.

        Args:
            value: The new green value.
        """
        self._colour.y = value
        self.colourChanged.emit()

    def get_b(self) -> float:
        """Return the blue channel.

        Returns:
            The current blue value.
        """
        return float(self._colour.z)

    def set_b(self, value: float) -> None:
        """Set the blue channel and emit colourChanged.

        Args:
            value: The new blue value.
        """
        self._colour.z = value
        self.colourChanged.emit()

    def get_a(self) -> float:
        """Return the alpha channel.

        Returns:
            The current alpha value.
        """
        return float(self._colour.w)

    def set_a(self, value: float) -> None:
        """Set the alpha channel and emit colourChanged.

        Args:
            value: The new alpha value.
        """
        self._colour.w = value
        self.colourChanged.emit()

    r = Property(float, get_r, set_r, notify=colourChanged)
    g = Property(float, get_g, set_g, notify=colourChanged)
    b = Property(float, get_b, set_b, notify=colourChanged)
    a = Property(float, get_a, set_a, notify=colourChanged)

    def get_hex(self) -> str:
        """Return the colour as a `#AARRGGBB` hex string.

        Returns:
            The hex colour string, including alpha.
        """
        colour = QColor.fromRgbF(
            self._colour.x, self._colour.y, self._colour.z, self._colour.w
        )
        return colour.name(QColor.NameFormat.HexArgb)

    hex = Property(str, get_hex, notify=colourChanged)

    @Slot(result=Vec4)
    def get_value(self) -> Vec4:
        """Return the current colour as a Vec4.

        Returns:
            The current colour.
        """
        return self._colour

    @Slot(Vec4)
    def set_value(self, value: Vec4) -> None:
        """Replace the current colour and emit colourChanged.

        Args:
            value: The new colour value.
        """
        self._colour = value
        self.colourChanged.emit()
```

- [ ] **Step 4: Register in `__init__.py`**

```python
# src/ncca/ngl/qml/__init__.py  (edit)
from .lookat_model import LookAtModel
from .mat2_model import Mat2Model
from .mat3_model import Mat3Model
from .mat4_model import Mat4Model
from .rgb_colour_model import RGBColourModel
from .rgba_colour_model import RGBAColourModel
from .transform_model import TransformModel
from .vec2_model import Vec2Model
from .vec3_model import Vec3Model
from .vec4_model import Vec4Model

__all__ = [
    "Vec2Model",
    "Vec3Model",
    "Vec4Model",
    "Mat2Model",
    "Mat3Model",
    "Mat4Model",
    "TransformModel",
    "LookAtModel",
    "RGBColourModel",
    "RGBAColourModel",
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_qml_rgba_colour_model.py -m qt -v`
Expected: PASS (4 tests)

- [ ] **Step 6: Commit**

```bash
git add src/ncca/ngl/qml/rgba_colour_model.py src/ncca/ngl/qml/__init__.py tests/test_qml_rgba_colour_model.py
git commit -m "feat(qml): add RGBAColourModel"
```

---

### Task 11: DecimalSpinBox.qml + Vec2/Vec3/Vec4 widget views

**Files:**
- Create: `src/ncca/ngl/qml/DecimalSpinBox.qml`
- Create: `src/ncca/ngl/qml/Vec2Widget.qml`
- Create: `src/ncca/ngl/qml/Vec3Widget.qml`
- Create: `src/ncca/ngl/qml/Vec4Widget.qml`

**Interfaces:**
- Consumes: `Vec2Model`/`Vec3Model`/`Vec4Model` (Tasks 1–3), imported via `import ncca.ngl.qml 1.0`.
- Produces: `DecimalSpinBox` — reusable float spinbox with `property real realValue`, `property real from_`, `property real to_`, `property real stepSize_`, `property int decimals`. `Vec2Widget`/`Vec3Widget`/`Vec4Widget` — `Frame` with `property string name`, `property alias x/y/z/[w]` (bound straight to the child model's properties), `property alias model` (the underlying model instance, for whole-value access), `signal valueChanged()`.

This task has no pytest coverage (no automated QML-engine test is written until Task 16); verify it manually per Step 4 below.

- [ ] **Step 1: Write DecimalSpinBox.qml**

```qml
// src/ncca/ngl/qml/DecimalSpinBox.qml
import QtQuick
import QtQuick.Controls

SpinBox {
    id: root

    property real realValue: 0.0
    property real from_: -5.0
    property real to_: 5.0
    property real stepSize_: 0.01
    property int decimals: 2
    property bool _updating: false

    from: Math.round(from_ * Math.pow(10, decimals))
    to: Math.round(to_ * Math.pow(10, decimals))
    stepSize: Math.max(1, Math.round(stepSize_ * Math.pow(10, decimals)))
    value: Math.round(realValue * Math.pow(10, decimals))
    editable: true

    onValueModified: {
        _updating = true
        realValue = value / Math.pow(10, decimals)
        _updating = false
    }

    onRealValueChanged: {
        if (!_updating) {
            value = Math.round(realValue * Math.pow(10, decimals))
        }
    }

    validator: DoubleValidator {
        bottom: Math.min(root.from_, root.to_)
        top: Math.max(root.from_, root.to_)
        decimals: root.decimals
        notation: DoubleValidator.StandardNotation
    }

    textFromValue: function (value, locale) {
        return Number(value / Math.pow(10, root.decimals)).toLocaleString(
            locale, "f", root.decimals)
    }

    valueFromText: function (text, locale) {
        return Math.round(
            Number.fromLocaleString(locale, text) * Math.pow(10, root.decimals))
    }
}
```

- [ ] **Step 2: Write Vec2Widget.qml, Vec3Widget.qml, Vec4Widget.qml**

```qml
// src/ncca/ngl/qml/Vec2Widget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ncca.ngl.qml 1.0

Frame {
    id: root

    property string name: ""
    property alias xValue: vecModel.x
    property alias yValue: vecModel.y
    property alias xFrom: xSpin.from_
    property alias xTo: xSpin.to_
    property alias yFrom: ySpin.from_
    property alias yTo: ySpin.to_
    property alias model: vecModel
    signal valueChanged()

    Vec2Model {
        id: vecModel
        onValueChanged: root.valueChanged()
    }

    RowLayout {
        anchors.fill: parent
        Label { text: root.name }
        DecimalSpinBox {
            id: xSpin
            realValue: vecModel.x
            onRealValueChanged: vecModel.x = realValue
        }
        DecimalSpinBox {
            id: ySpin
            realValue: vecModel.y
            onRealValueChanged: vecModel.y = realValue
        }
    }
}
```

```qml
// src/ncca/ngl/qml/Vec3Widget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ncca.ngl.qml 1.0

Frame {
    id: root

    property string name: ""
    property alias xValue: vecModel.x
    property alias yValue: vecModel.y
    property alias zValue: vecModel.z
    property alias xFrom: xSpin.from_
    property alias xTo: xSpin.to_
    property alias yFrom: ySpin.from_
    property alias yTo: ySpin.to_
    property alias zFrom: zSpin.from_
    property alias zTo: zSpin.to_
    property alias model: vecModel
    signal valueChanged()

    Vec3Model {
        id: vecModel
        onValueChanged: root.valueChanged()
    }

    RowLayout {
        anchors.fill: parent
        Label { text: root.name }
        DecimalSpinBox {
            id: xSpin
            realValue: vecModel.x
            onRealValueChanged: vecModel.x = realValue
        }
        DecimalSpinBox {
            id: ySpin
            realValue: vecModel.y
            onRealValueChanged: vecModel.y = realValue
        }
        DecimalSpinBox {
            id: zSpin
            realValue: vecModel.z
            onRealValueChanged: vecModel.z = realValue
        }
    }
}
```

```qml
// src/ncca/ngl/qml/Vec4Widget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ncca.ngl.qml 1.0

Frame {
    id: root

    property string name: ""
    property alias xValue: vecModel.x
    property alias yValue: vecModel.y
    property alias zValue: vecModel.z
    property alias wValue: vecModel.w
    property alias xFrom: xSpin.from_
    property alias xTo: xSpin.to_
    property alias yFrom: ySpin.from_
    property alias yTo: ySpin.to_
    property alias zFrom: zSpin.from_
    property alias zTo: zSpin.to_
    property alias wFrom: wSpin.from_
    property alias wTo: wSpin.to_
    property alias model: vecModel
    signal valueChanged()

    Vec4Model {
        id: vecModel
        onValueChanged: root.valueChanged()
    }

    RowLayout {
        anchors.fill: parent
        Label { text: root.name }
        DecimalSpinBox {
            id: xSpin
            realValue: vecModel.x
            onRealValueChanged: vecModel.x = realValue
        }
        DecimalSpinBox {
            id: ySpin
            realValue: vecModel.y
            onRealValueChanged: vecModel.y = realValue
        }
        DecimalSpinBox {
            id: zSpin
            realValue: vecModel.z
            onRealValueChanged: vecModel.z = realValue
        }
        DecimalSpinBox {
            id: wSpin
            realValue: vecModel.w
            onRealValueChanged: vecModel.w = realValue
        }
    }
}
```

- [ ] **Step 3: Manually smoke-test the three views**

Run (repeat for `Vec2Widget.qml`, `Vec3Widget.qml`, `Vec4Widget.qml`):

```bash
QT_QPA_PLATFORM=offscreen uv run pyside6-qml src/ncca/ngl/qml/Vec3Widget.qml -I src/ncca/ngl/qml
```

Expected: window loads with no `qrc:` / `QQmlApplicationEngine` error output on stderr (a bare `Vec3Widget.qml` has no root `ApplicationWindow`, so `pyside6-qml` will show it as a plain top-level item — the check here is "no red QML errors printed", not a visual review).

- [ ] **Step 4: Commit**

```bash
git add src/ncca/ngl/qml/DecimalSpinBox.qml src/ncca/ngl/qml/Vec2Widget.qml src/ncca/ngl/qml/Vec3Widget.qml src/ncca/ngl/qml/Vec4Widget.qml
git commit -m "feat(qml): add DecimalSpinBox and Vec2/Vec3/Vec4 widget views"
```

---

### Task 12: MatrixGridWidget.qml + Mat2/Mat3/Mat4 widget views

**Files:**
- Create: `src/ncca/ngl/qml/MatrixGridWidget.qml`
- Create: `src/ncca/ngl/qml/Mat2Widget.qml`
- Create: `src/ncca/ngl/qml/Mat3Widget.qml`
- Create: `src/ncca/ngl/qml/Mat4Widget.qml`

**Interfaces:**
- Consumes: `Mat2Model`/`Mat3Model`/`Mat4Model` (Tasks 4–6), `DecimalSpinBox` (Task 11).
- Produces: `MatrixGridWidget` — generic grid, `property int size`, `property var model`, `property bool readOnly`, `property real cellMin: -20.0`, `property real cellMax: 20.0`. `Mat2Widget`/`Mat3Widget`/`Mat4Widget` — `Frame` with `property string name`, `property bool readOnly: false`, `property alias model`, `signal valueChanged()`; Mat3/Mat4 add the rotate/scale(/translate) method combo.

- [ ] **Step 1: Write MatrixGridWidget.qml**

```qml
// src/ncca/ngl/qml/MatrixGridWidget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: root

    property int size: 3
    property var model
    property bool readOnly: false
    property real cellMin: -20.0
    property real cellMax: 20.0

    GridLayout {
        columns: root.size

        Repeater {
            model: root.size * root.size

            delegate: DecimalSpinBox {
                id: cellSpin
                readonly property int row: Math.floor(index / root.size)
                readonly property int col: index % root.size

                from_: root.cellMin
                to_: root.cellMax
                enabled: !root.readOnly
                realValue: root.model.get_cell(row, col)
                onRealValueChanged: {
                    if (!root.readOnly) {
                        root.model.set_cell(row, col, realValue)
                    }
                }

                Connections {
                    target: root.model
                    function onValueChanged() {
                        cellSpin.realValue = root.model.get_cell(cellSpin.row, cellSpin.col)
                    }
                }
            }
        }
    }

    RowLayout {
        visible: !root.readOnly
        Button { text: "Identity"; onClicked: root.model.identity() }
        Button { text: "Zero"; onClicked: root.model.zero() }
        Button { text: "Transpose"; onClicked: root.model.transpose() }
        Button { text: "Inverse"; onClicked: root.model.inverse() }
    }

    Label {
        visible: !root.readOnly && root.model.statusMessage.length > 0
        text: root.model ? root.model.statusMessage : ""
    }
}
```

- [ ] **Step 2: Write Mat2Widget.qml**

```qml
// src/ncca/ngl/qml/Mat2Widget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ncca.ngl.qml 1.0

Frame {
    id: root

    property string name: ""
    property bool readOnly: false
    property alias model: mat2Model
    signal valueChanged()

    Mat2Model {
        id: mat2Model
        onValueChanged: root.valueChanged()
    }

    ColumnLayout {
        anchors.fill: parent
        Label { text: root.name }
        MatrixGridWidget {
            size: 2
            model: mat2Model
            readOnly: root.readOnly
        }
    }
}
```

- [ ] **Step 3: Write Mat3Widget.qml**

```qml
// src/ncca/ngl/qml/Mat3Widget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ncca.ngl.qml 1.0

Frame {
    id: root

    property string name: ""
    property bool readOnly: false
    property alias model: mat3Model
    signal valueChanged()

    Mat3Model {
        id: mat3Model
        onValueChanged: root.valueChanged()
    }

    ColumnLayout {
        anchors.fill: parent
        Label { text: root.name }
        MatrixGridWidget {
            size: 3
            model: mat3Model
            readOnly: root.readOnly
        }

        RowLayout {
            visible: !root.readOnly

            ComboBox {
                id: methodCombo
                model: mat3Model.method_names()
            }

            DecimalSpinBox {
                id: angleSpin
                visible: mat3Model.method_kind(methodCombo.currentText) === "angle"
                from_: -360.0
                to_: 360.0
                stepSize_: 0.5
                decimals: 1
                onRealValueChanged: {
                    if (visible) {
                        mat3Model.apply_angle_method(methodCombo.currentText, realValue)
                    }
                }
            }

            Vec3Widget {
                id: xyzWidget
                visible: mat3Model.method_kind(methodCombo.currentText) === "xyz"
                name: "xyz"
                xValue: 1.0
                yValue: 1.0
                zValue: 1.0
                onValueChanged: {
                    if (visible) {
                        mat3Model.apply_xyz_method(methodCombo.currentText, xValue, yValue, zValue)
                    }
                }
            }
        }
    }
}
```

- [ ] **Step 4: Write Mat4Widget.qml**

```qml
// src/ncca/ngl/qml/Mat4Widget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ncca.ngl.qml 1.0

Frame {
    id: root

    property string name: ""
    property bool readOnly: false
    property alias model: mat4Model
    signal valueChanged()

    Mat4Model {
        id: mat4Model
        onValueChanged: root.valueChanged()
    }

    ColumnLayout {
        anchors.fill: parent
        Label { text: root.name }
        MatrixGridWidget {
            size: 4
            model: mat4Model
            readOnly: root.readOnly
        }

        RowLayout {
            visible: !root.readOnly

            ComboBox {
                id: methodCombo
                model: mat4Model.method_names()
            }

            DecimalSpinBox {
                id: angleSpin
                visible: mat4Model.method_kind(methodCombo.currentText) === "angle"
                from_: -360.0
                to_: 360.0
                stepSize_: 0.5
                decimals: 1
                onRealValueChanged: {
                    if (visible) {
                        mat4Model.apply_angle_method(methodCombo.currentText, realValue)
                    }
                }
            }

            Vec3Widget {
                id: xyzWidget
                visible: mat4Model.method_kind(methodCombo.currentText) === "xyz"
                name: "xyz"
                xValue: 1.0
                yValue: 1.0
                zValue: 1.0
                onValueChanged: {
                    if (visible) {
                        mat4Model.apply_xyz_method(methodCombo.currentText, xValue, yValue, zValue)
                    }
                }
            }
        }
    }
}
```

- [ ] **Step 5: Manually smoke-test the four views**

Run (repeat for `Mat2Widget.qml`, `Mat3Widget.qml`, `Mat4Widget.qml`):

```bash
QT_QPA_PLATFORM=offscreen uv run pyside6-qml src/ncca/ngl/qml/Mat4Widget.qml -I src/ncca/ngl/qml
```

Expected: no red QML error output on stderr.

- [ ] **Step 6: Commit**

```bash
git add src/ncca/ngl/qml/MatrixGridWidget.qml src/ncca/ngl/qml/Mat2Widget.qml src/ncca/ngl/qml/Mat3Widget.qml src/ncca/ngl/qml/Mat4Widget.qml
git commit -m "feat(qml): add MatrixGridWidget and Mat2/Mat3/Mat4 widget views"
```

---

### Task 13: TransformWidget.qml + LookAtWidget.qml

**Files:**
- Create: `src/ncca/ngl/qml/TransformWidget.qml`
- Create: `src/ncca/ngl/qml/LookAtWidget.qml`

**Interfaces:**
- Consumes: `TransformModel` (Task 7), `LookAtModel` (Task 8), `Vec3Widget` (Task 11).
- Produces: `TransformWidget`/`LookAtWidget` — foldable `Frame`s with `property string name`, `property alias model`, `signal valueChanged()`.

- [ ] **Step 1: Write TransformWidget.qml**

```qml
// src/ncca/ngl/qml/TransformWidget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ncca.ngl.qml 1.0

Frame {
    id: root

    property string name: ""
    property alias model: txModel
    signal valueChanged()

    TransformModel {
        id: txModel
        onValueChanged: root.valueChanged()
    }

    ColumnLayout {
        anchors.fill: parent

        ToolButton {
            id: toggle
            text: root.name
            checkable: true
            checked: true
        }

        ColumnLayout {
            visible: toggle.checked

            Vec3Widget {
                name: "Position"
                xValue: txModel.position.x
                yValue: txModel.position.y
                zValue: txModel.position.z
                xFrom: -20.0; xTo: 20.0
                yFrom: -20.0; yTo: 20.0
                zFrom: -20.0; zTo: 20.0
                onValueChanged: {
                    txModel.position.x = xValue
                    txModel.position.y = yValue
                    txModel.position.z = zValue
                }
            }

            Vec3Widget {
                name: "Rotation"
                xValue: txModel.rotation.x
                yValue: txModel.rotation.y
                zValue: txModel.rotation.z
                xFrom: -360.0; xTo: 360.0
                yFrom: -360.0; yTo: 360.0
                zFrom: -360.0; zTo: 360.0
                onValueChanged: {
                    txModel.rotation.x = xValue
                    txModel.rotation.y = yValue
                    txModel.rotation.z = zValue
                }
            }

            Vec3Widget {
                name: "Scale"
                xValue: txModel.scale.x
                yValue: txModel.scale.y
                zValue: txModel.scale.z
                xFrom: -20.0; xTo: 20.0
                yFrom: -20.0; yTo: 20.0
                zFrom: -20.0; zTo: 20.0
                onValueChanged: {
                    txModel.scale.x = xValue
                    txModel.scale.y = yValue
                    txModel.scale.z = zValue
                }
            }

            Label { text: "Rotation Order" }
            ComboBox {
                model: txModel.rotation_orders()
                onCurrentIndexChanged: txModel.rotationOrderIndex = currentIndex
            }
        }
    }
}
```

- [ ] **Step 2: Write LookAtWidget.qml**

```qml
// src/ncca/ngl/qml/LookAtWidget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ncca.ngl.qml 1.0

Frame {
    id: root

    property string name: ""
    property alias model: lookAtModel
    signal valueChanged()

    LookAtModel {
        id: lookAtModel
        onValueChanged: root.valueChanged()
    }

    ColumnLayout {
        anchors.fill: parent

        ToolButton {
            id: toggle
            text: root.name
            checkable: true
            checked: true
        }

        ColumnLayout {
            visible: toggle.checked

            Vec3Widget {
                name: "Eye"
                xValue: lookAtModel.eye.x
                yValue: lookAtModel.eye.y
                zValue: lookAtModel.eye.z
                xFrom: -20.0; xTo: 20.0
                yFrom: -20.0; yTo: 20.0
                zFrom: -20.0; zTo: 20.0
                onValueChanged: {
                    lookAtModel.eye.x = xValue
                    lookAtModel.eye.y = yValue
                    lookAtModel.eye.z = zValue
                }
            }

            Vec3Widget {
                name: "Look"
                xValue: lookAtModel.look.x
                yValue: lookAtModel.look.y
                zValue: lookAtModel.look.z
                xFrom: -20.0; xTo: 20.0
                yFrom: -20.0; yTo: 20.0
                zFrom: -20.0; zTo: 20.0
                onValueChanged: {
                    lookAtModel.look.x = xValue
                    lookAtModel.look.y = yValue
                    lookAtModel.look.z = zValue
                }
            }

            Label { text: "World Up" }
            ComboBox {
                model: lookAtModel.up_names()
                onCurrentIndexChanged: lookAtModel.upIndex = currentIndex
            }
        }
    }
}
```

- [ ] **Step 3: Manually smoke-test both views**

Run (repeat for `LookAtWidget.qml`):

```bash
QT_QPA_PLATFORM=offscreen uv run pyside6-qml src/ncca/ngl/qml/TransformWidget.qml -I src/ncca/ngl/qml
```

Expected: no red QML error output on stderr.

- [ ] **Step 4: Commit**

```bash
git add src/ncca/ngl/qml/TransformWidget.qml src/ncca/ngl/qml/LookAtWidget.qml
git commit -m "feat(qml): add TransformWidget and LookAtWidget views"
```

---

### Task 14: RGBColourWidget.qml + RGBAColourWidget.qml

**Files:**
- Create: `src/ncca/ngl/qml/RGBColourWidget.qml`
- Create: `src/ncca/ngl/qml/RGBAColourWidget.qml`

**Interfaces:**
- Consumes: `RGBColourModel` (Task 9), `RGBAColourModel` (Task 10), `DecimalSpinBox` (Task 11).
- Produces: `RGBColourWidget`/`RGBAColourWidget` — `Frame` with `property string name`, `property alias model`, `signal colourChanged()`, plus a swatch `Rectangle` bound to `model.hex`.

- [ ] **Step 1: Write RGBColourWidget.qml**

```qml
// src/ncca/ngl/qml/RGBColourWidget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ncca.ngl.qml 1.0

Frame {
    id: root

    property string name: ""
    property alias model: colourModel
    signal colourChanged()

    RGBColourModel {
        id: colourModel
        onColourChanged: root.colourChanged()
    }

    RowLayout {
        anchors.fill: parent
        Label { text: root.name }
        DecimalSpinBox {
            from_: 0.0
            to_: 1.0
            realValue: colourModel.r
            onRealValueChanged: colourModel.r = realValue
        }
        DecimalSpinBox {
            from_: 0.0
            to_: 1.0
            realValue: colourModel.g
            onRealValueChanged: colourModel.g = realValue
        }
        DecimalSpinBox {
            from_: 0.0
            to_: 1.0
            realValue: colourModel.b
            onRealValueChanged: colourModel.b = realValue
        }
        Rectangle {
            width: 20
            height: 20
            color: colourModel.hex
            border.color: "black"
        }
    }
}
```

- [ ] **Step 2: Write RGBAColourWidget.qml**

```qml
// src/ncca/ngl/qml/RGBAColourWidget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ncca.ngl.qml 1.0

Frame {
    id: root

    property string name: ""
    property alias model: colourModel
    signal colourChanged()

    RGBAColourModel {
        id: colourModel
        onColourChanged: root.colourChanged()
    }

    RowLayout {
        anchors.fill: parent
        Label { text: root.name }
        DecimalSpinBox {
            from_: 0.0
            to_: 1.0
            realValue: colourModel.r
            onRealValueChanged: colourModel.r = realValue
        }
        DecimalSpinBox {
            from_: 0.0
            to_: 1.0
            realValue: colourModel.g
            onRealValueChanged: colourModel.g = realValue
        }
        DecimalSpinBox {
            from_: 0.0
            to_: 1.0
            realValue: colourModel.b
            onRealValueChanged: colourModel.b = realValue
        }
        DecimalSpinBox {
            from_: 0.0
            to_: 1.0
            realValue: colourModel.a
            onRealValueChanged: colourModel.a = realValue
        }
        Rectangle {
            width: 20
            height: 20
            color: colourModel.hex
            border.color: "black"
        }
    }
}
```

- [ ] **Step 3: Manually smoke-test both views**

Run (repeat for `RGBAColourWidget.qml`):

```bash
QT_QPA_PLATFORM=offscreen uv run pyside6-qml src/ncca/ngl/qml/RGBColourWidget.qml -I src/ncca/ngl/qml
```

Expected: no red QML error output on stderr.

- [ ] **Step 4: Commit**

```bash
git add src/ncca/ngl/qml/RGBColourWidget.qml src/ncca/ngl/qml/RGBAColourWidget.qml
git commit -m "feat(qml): add RGBColourWidget and RGBAColourWidget views"
```

---

### Task 15: Demo app (`__main__.py` + `main.qml`)

**Files:**
- Create: `src/ncca/ngl/qml/main.qml`
- Create: `src/ncca/ngl/qml/__main__.py`

**Interfaces:**
- Consumes: every widget view from Tasks 11–14.
- Produces: `python -m ncca.ngl.qml` entry point, mirroring `python -m ncca.ngl.widgets`.

- [ ] **Step 1: Write main.qml**

```qml
// src/ncca/ngl/qml/main.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import ncca.ngl.qml 1.0

ApplicationWindow {
    id: window

    title: "PyNGL ncca.ngl.qml widgets demo"
    visible: true
    width: Math.min(1000, Screen.desktopAvailableWidth - 80)
    height: Math.min(800, Screen.desktopAvailableHeight - 80)

    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth

        GridLayout {
            columns: 2
            columnSpacing: 12
            rowSpacing: 12

            Vec2Widget {
                id: vec2Widget
                name: "Vec2 Widget"
                xValue: 1.0
                yValue: 2.0
            }
            Label {
                text: "[" + vec2Widget.xValue.toFixed(2) + ", " + vec2Widget.yValue.toFixed(2) + "]"
            }

            Vec3Widget {
                id: vec3Widget
                name: "Vec3 Widget"
                xValue: 1.0
                yValue: 2.0
                zValue: 3.0
            }
            Label {
                text: "[" + vec3Widget.xValue.toFixed(2) + ", " + vec3Widget.yValue.toFixed(2)
                    + ", " + vec3Widget.zValue.toFixed(2) + "]"
            }

            Vec4Widget {
                id: vec4Widget
                name: "Vec4 Widget"
                xValue: 1.0
                yValue: 2.0
                zValue: 3.0
                wValue: 1.0
            }
            Label {
                text: "[" + vec4Widget.xValue.toFixed(2) + ", " + vec4Widget.yValue.toFixed(2)
                    + ", " + vec4Widget.zValue.toFixed(2) + ", " + vec4Widget.wValue.toFixed(2) + "]"
            }

            Mat2Widget { id: mat2Widget; name: "Mat2 Widget" }
            Item {}

            Mat3Widget { id: mat3Widget; name: "Mat3 Widget" }
            Item {}

            Mat4Widget { id: mat4Widget; name: "Mat4 Widget" }
            Item {}

            TransformWidget { id: transformWidget; name: "Transform Widget" }
            Label {
                font.family: "monospace"
                text: transformWidget.model.matrix_text()
                Connections {
                    target: transformWidget.model
                    function onValueChanged() {
                        text = transformWidget.model.matrix_text()
                    }
                }
            }

            LookAtWidget { id: lookAtWidget; name: "Look At" }
            Label {
                font.family: "monospace"
                text: lookAtWidget.model.matrix_text()
                Connections {
                    target: lookAtWidget.model
                    function onValueChanged() {
                        text = lookAtWidget.model.matrix_text()
                    }
                }
            }

            RGBColourWidget { id: rgbWidget; name: "RGB Colour Widget" }
            Item {}

            RGBAColourWidget { id: rgbaWidget; name: "RGBA Colour Widget" }
            Item {}
        }
    }
}
```

- [ ] **Step 2: Write __main__.py**

```python
# src/ncca/ngl/qml/__main__.py
"""Demo Qt Quick app showcasing all of the NGL QML widgets."""

import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

import ncca.ngl.qml  # noqa: F401  (import registers every QML type)


def main() -> int:
    """Launch the QML widgets demo application.

    Returns:
        The process exit code (-1 if the QML file failed to load).
    """
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    package_dir = Path(__file__).parent
    engine.addImportPath(str(package_dir))
    engine.load(QUrl.fromLocalFile(str(package_dir / "main.qml")))
    if not engine.rootObjects():
        return -1
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Manually run the demo**

Run:

```bash
uv run python -m ncca.ngl.qml
```

Expected: a window titled "PyNGL ncca.ngl.qml widgets demo" opens showing all 10 widgets in a two-column grid, each with a live value/matrix label beside it; editing any spin box updates its label immediately. If no display is available, verify headlessly instead:

```bash
QT_QPA_PLATFORM=offscreen uv run python -m ncca.ngl.qml &
sleep 2
kill %1
```

Expected: no QML error output and the background process starts cleanly (confirms `main.qml` loads and every referenced type resolves).

- [ ] **Step 4: Commit**

```bash
git add src/ncca/ngl/qml/main.qml src/ncca/ngl/qml/__main__.py
git commit -m "feat(qml): add demo application"
```

---

### Task 16: QML view smoke tests (automated)

**Files:**
- Create: `tests/test_qml_views.py`

**Interfaces:**
- Consumes: every `.qml` file under `src/ncca/ngl/qml/`, loaded via `QQmlApplicationEngine`.
- Produces: a `qt`-marked regression test that catches QML syntax errors, missing imports, and unresolved property bindings without requiring a visual review — this is additional coverage beyond the approved spec's model-only testing floor.

- [ ] **Step 1: Write the test**

```python
# tests/test_qml_views.py
from pathlib import Path

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine

import ncca.ngl.qml  # noqa: F401  (import registers every QML type)

QML_DIR = Path(__file__).parent.parent / "src" / "ncca" / "ngl" / "qml"

STANDALONE_VIEWS = [
    "Vec2Widget.qml",
    "Vec3Widget.qml",
    "Vec4Widget.qml",
    "Mat2Widget.qml",
    "Mat3Widget.qml",
    "Mat4Widget.qml",
    "TransformWidget.qml",
    "LookAtWidget.qml",
    "RGBColourWidget.qml",
    "RGBAColourWidget.qml",
]


@pytest.mark.parametrize("qml_file", STANDALONE_VIEWS)
def test_widget_view_loads_without_errors(qt_app, qml_file):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(QML_DIR))

    errors = []
    engine.warnings.connect(lambda msgs: errors.extend(msgs))
    engine.load(QUrl.fromLocalFile(str(QML_DIR / qml_file)))

    assert engine.rootObjects(), f"{qml_file} failed to load: {errors}"
    assert not errors, f"{qml_file} produced warnings: {errors}"


def test_main_qml_loads_without_errors(qt_app):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(QML_DIR))

    errors = []
    engine.warnings.connect(lambda msgs: errors.extend(msgs))
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "main.qml")))

    assert engine.rootObjects(), f"main.qml failed to load: {errors}"
    assert not errors, f"main.qml produced warnings: {errors}"
```

- [ ] **Step 2: Run tests (expect them to catch any remaining QML mistakes)**

Run: `QT_QPA_PLATFORM=offscreen uv run pytest tests/test_qml_views.py -m qt -v`
Expected: PASS (11 tests). If any fail, fix the reported `.qml` file in place (this is the point of this task — it's the safety net for Tasks 11–15) and re-run until green.

- [ ] **Step 3: Commit**

```bash
git add tests/test_qml_views.py
git commit -m "test(qml): add QQmlApplicationEngine smoke tests for every view"
```

---

### Task 17: Tutorial doc — `docs/docs/qml/index.md`

**Files:**
- Create: `docs/docs/qml/index.md`
- Modify: `docs/mkdocs.yml` (nav)

**Interfaces:**
- Consumes: nothing (pure documentation).
- Produces: a tutorial page mirroring `docs/docs/widgets/index.md`'s structure and tone, adapted to QML usage (models + `.qml` views instead of `QWidget` construction).

- [ ] **Step 1: Write the tutorial page**

```markdown
# Qt Quick (QML) Widgets for NGL Types

`ncca.ngl.qml` provides Qt Quick equivalents of the `ncca.ngl.widgets`
PySide6 widgets — the same editors for NGL math types, built as QML
components instead of `QWidget`s. Each widget pairs a Python model
(a `QObject` holding the actual `ncca.ngl` value) with a `.qml` view file
that binds to it declaratively.

See them all at once with the bundled demo:

```bash
uv run python -m ncca.ngl.qml
```

## The widgets

| QML type | Edits | Value signal |
|---|---|---|
| `Vec2Widget` | two spin boxes | `valueChanged()` |
| `Vec3Widget` | three spin boxes | `valueChanged()` |
| `Vec4Widget` | four spin boxes | `valueChanged()` |
| `Mat2Widget` | 2x2 grid + reset buttons | `valueChanged()` |
| `Mat3Widget` | 3x3 grid + reset buttons + method combo | `valueChanged()` |
| `Mat4Widget` | 4x4 grid + reset buttons + method combo | `valueChanged()` |
| `TransformWidget` | position / rotation / scale | `valueChanged()` |
| `LookAtWidget` | eye / look / up | `valueChanged()` (a `look_at` view matrix) |
| `RGBColourWidget` | RGB spin boxes + swatch | `colourChanged()` |
| `RGBAColourWidget` | RGBA spin boxes + swatch | `colourChanged()` |

Unlike the PySide6 widgets (which emit the actual `Vec3`/`Mat4` object),
the QML signals are plain no-argument notifications — QML/JS can't hold a
numpy-backed `ncca.ngl` object directly, so read the value back through the
widget's aliased properties (`xValue`/`yValue`/`zValue`/...) or its
`model.get_value()` slot.

## Using a widget in your own `.qml` file

Every widget registers itself under the `ncca.ngl.qml` import, so importing
the package from Python (which happens automatically if you import
anything from `ncca.ngl.qml`) makes the types available to any `.qml` file
on the engine's import path:

```qml
import QtQuick
import QtQuick.Layouts
import ncca.ngl.qml 1.0

ColumnLayout {
    Vec3Widget {
        id: position
        name: "Position"
        xValue: 0.0; yValue: 1.0; zValue: 0.0
        onValueChanged: console.log(position.xValue, position.yValue, position.zValue)
    }
}
```

```python
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

import ncca.ngl.qml  # registers every widget type

app = QGuiApplication(sys.argv)
engine = QQmlApplicationEngine()
engine.addImportPath(str(Path("src/ncca/ngl/qml")))  # ships alongside your .qml files
engine.load(QUrl.fromLocalFile("my_panel.qml"))
sys.exit(app.exec())
```

## Ranges

The vector and matrix-cell spin boxes default to a small range, matching
the PySide6 widgets. Override per axis/cell via the exposed properties:

```qml
Vec3Widget {
    name: "Position"
    xFrom: -10.0; xTo: 10.0
    yFrom: 0.0; yTo: 5.0
}
```

`MatrixGridWidget` (used internally by `Mat2Widget`/`Mat3Widget`/`Mat4Widget`)
exposes `cellMin`/`cellMax` the same way.

## Matrix grid widgets

`Mat2Widget`/`Mat3Widget`/`Mat4Widget` edit a matrix as a grid of spin
boxes, with **Identity**/**Zero**/**Transpose**/**Inverse** buttons —
`Inverse` sets `model.statusMessage` to `"Matrix is singular"` instead of
raising if the matrix isn't invertible, which the view surfaces as a label.

`Mat3Widget`/`Mat4Widget` also expose a method combo box
(`rotate_x`/`rotate_y`/`rotate_z`/`scale`, plus `translate` on `Mat4Widget`)
that sets the matrix from the matching classmethod — a single angle spin
box for rotations, an embedded `Vec3Widget` for `scale`/`translate`.

### Read-only (view) mode

Set `readOnly: true` for a plain display grid with no reset buttons and no
method combo — cells can't be typed into, but the bound model still
updates what's shown:

```qml
Mat4Widget { id: modelMatrix; name: "Model" }
Mat4Widget {
    id: modelMatrixView
    name: "Model Matrix"
    readOnly: true
    Connections {
        target: modelMatrix.model
        function onValueChanged() {
            for (var r = 0; r < 4; r++)
                for (var c = 0; c < 4; c++)
                    modelMatrixView.model.set_cell(r, c, modelMatrix.model.get_cell(r, c))
        }
    }
}
```

## Driving a viewport

`TransformWidget`/`LookAtWidget` compute a `Mat4` you can read via
`widget.model.get_matrix()` (a `Slot`) or display live via
`widget.model.matrix_text()`, exactly as shown in the bundled demo's
`main.qml`:

```qml
TransformWidget { id: transformWidget; name: "Model" }
Label {
    text: transformWidget.model.matrix_text()
    Connections {
        target: transformWidget.model
        function onValueChanged() { text = transformWidget.model.matrix_text() }
    }
}
```

The demo app in
[`src/ncca/ngl/qml/main.qml`](https://github.com/NCCA/PyNGL/blob/main/src/ncca/ngl/qml/main.qml)
and
[`src/ncca/ngl/qml/__main__.py`](https://github.com/NCCA/PyNGL/blob/main/src/ncca/ngl/qml/__main__.py)
shows every widget wired up and is a good copy-paste source.

Full API: [QML Widgets reference](../QmlWidgets.md).
```

- [ ] **Step 2: Add to nav in `docs/mkdocs.yml`**

```yaml
# docs/mkdocs.yml  (edit nav, add after the "Widgets:" section)
  - QML Widgets:
      - Qt Quick Widgets for NGL Types: qml/index.md
```

- [ ] **Step 3: Commit**

```bash
git add docs/docs/qml/index.md docs/mkdocs.yml
git commit -m "docs(qml): add Qt Quick widgets tutorial page"
```

---

### Task 18: API reference doc — `docs/docs/QmlWidgets.md`

**Files:**
- Create: `docs/docs/QmlWidgets.md`
- Modify: `docs/mkdocs.yml` (nav, API Reference section)
- Modify: `README.md` (feature list)
- Modify: `CLAUDE.md` (Architecture section)

**Interfaces:**
- Consumes: every model class from Tasks 1–10.
- Produces: an mkdocstrings reference page mirroring `docs/docs/Widgets.md`.

- [ ] **Step 1: Write the API reference page**

```markdown
# QML Widget Models

See the [Qt Quick Widgets guide](qml/index.md) for an introduction and
usage examples.

## Vec2Model

::: ncca.ngl.qml.Vec2Model

## Vec3Model

::: ncca.ngl.qml.Vec3Model

## Vec4Model

::: ncca.ngl.qml.Vec4Model

## TransformModel

::: ncca.ngl.qml.TransformModel

## LookAtModel

::: ncca.ngl.qml.LookAtModel

## RGBColourModel

::: ncca.ngl.qml.RGBColourModel

## RGBAColourModel

::: ncca.ngl.qml.RGBAColourModel

## Mat2Model

::: ncca.ngl.qml.Mat2Model

## Mat3Model

::: ncca.ngl.qml.Mat3Model

## Mat4Model

::: ncca.ngl.qml.Mat4Model
```

- [ ] **Step 2: Add to nav in `docs/mkdocs.yml`**

```yaml
# docs/mkdocs.yml  (edit nav, API Reference section — add after "Widgets: Widgets.md")
      - QML Widgets: QmlWidgets.md
```

- [ ] **Step 3: Update `README.md` feature list**

Add a line alongside the existing widgets feature bullet (find it via `grep -n "widgets" README.md` and add directly beneath), e.g.:

```markdown
- **Qt Widgets & QML** — ready-made PySide6 widgets (`ncca.ngl.widgets`) and Qt Quick components (`ncca.ngl.qml`) for editing/displaying NGL math types in a GUI.
```

- [ ] **Step 4: Update `CLAUDE.md` Architecture section**

Add a subsection after the existing `src/ncca/ngl/widgets/` description:

```markdown
### `src/ncca/ngl/qml/`

Qt Quick (QML) equivalents of the `widgets/` PySide6 widgets: `vec2_model.py`/`vec3_model.py`/`vec4_model.py`,
`mat_grid_model.py` (shared base) + `mat2_model.py`/`mat3_model.py`/`mat4_model.py`, `transform_model.py`,
`lookat_model.py`, `rgb_colour_model.py`/`rgba_colour_model.py` — each a `QObject` registered as a QML type via
`@QmlElement`, paired with a same-named `.qml` view file (`Vec3Widget.qml`, `Mat4Widget.qml`, etc.) plus shared
`DecimalSpinBox.qml`/`MatrixGridWidget.qml` components. Has its own `__main__.py` + `main.qml` demo, run via
`python -m ncca.ngl.qml`.
```

- [ ] **Step 5: Build docs strictly and fix any drift**

Run: `uv run --with mkdocs --with "mkdocstrings[python]" mkdocs build --strict -f docs/mkdocs.yml`
Expected: build succeeds with zero warnings. If it reports a missing docstring section or broken `:::` target, fix the referenced model file and re-run.

- [ ] **Step 6: Commit**

```bash
git add docs/docs/QmlWidgets.md docs/mkdocs.yml README.md CLAUDE.md
git commit -m "docs(qml): add QML widgets API reference and update architecture docs"
```

---

### Task 19: Full verification pass

**Files:** none (verification only).

- [ ] **Step 1: Run the full test suite (default + qt-marked)**

Run: `uv run pytest`
Expected: PASS, non-GPU suite green.

Run: `uv run pytest -m qt`
Expected: PASS, all Qt-marked tests (existing widgets + new `test_qml_*.py` files) green.

- [ ] **Step 2: Run lint**

Run: `uv run ruff check src/`
Expected: no errors (in particular no missing type hints / docstrings on the new `qml/` package).

Run: `uv run ruff format src/ --check`
Expected: no reformatting needed (run `uv run ruff format src/` and re-check if it does).

- [ ] **Step 3: Run the strict docs build again (final check)**

Run: `uv run --with mkdocs --with "mkdocstrings[python]" mkdocs build --strict -f docs/mkdocs.yml`
Expected: PASS, zero warnings.

- [ ] **Step 4: Manually run the demo app one more time**

Run: `uv run python -m ncca.ngl.qml`
Expected: opens cleanly, all 10 widgets editable, all value labels update live (see Task 15 Step 3 for the offscreen fallback if no display is available).

- [ ] **Step 5: Final commit (if Steps 2–3 required any fixes)**

```bash
git add -A
git commit -m "fix(qml): address lint/docs findings from verification pass"
```

(Skip this step entirely if Steps 1–4 required no changes.)
