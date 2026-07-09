# Perspective Widget Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `PerspectiveWidget` (PySide6) and a matching `PerspectiveModel` +
`PerspectiveWidget.qml` (Qt Quick) that let a user edit fov/aspect/near/far
interactively and expose the resulting `Mat4` from `ncca.ngl.perspective()`.

**Architecture:** Both widgets follow the existing `LookAtWidget` / `LookAtModel`
pattern exactly (foldable frame, `valueChanged(Mat4)` signal, recompute-on-change),
but with four independent scalar fields instead of composed `Vec3` sub-widgets — so
the QML model exposes flat `float` properties directly (like `Vec2Model`), and the
QML view binds `DecimalSpinBox` controls straight to the model (like `Vec3Widget.qml`),
not through the wrapper/`_ready`-guard pattern `LookAtWidget.qml` uses to compose
child `Vec3Widget`s.

**Tech Stack:** PySide6 (`QFrame`, `QDoubleSpinBox`, `QComboBox`, `QToolButton`),
Qt Quick (`Frame`, `DecimalSpinBox`, `ComboBox`), `ncca.ngl.perspective`,
`ncca.ngl.PerspMode`, `ncca.ngl.Mat4`.

## Global Constraints

- Type hints required on all function signatures and class attributes; Google-style
  docstrings with Args/Returns/Raises — enforced by `uv run ruff check src/`.
- "Colour" spelling only (not applicable here — no colour fields).
- New public symbols must be added to the matching `docs/docs/*.md` page's `:::`
  directives or they never render — see Task 4.
- Verify docs with:
  `uv run --with mkdocs --with "mkdocstrings[python]" mkdocs build --strict -f docs/mkdocs.yml`
- Run the full test suite (not just touched files) after changes: `uv run pytest`.
- Qt-dependent tests require the `qt_app`/`qtbot` fixtures from `tests/conftest.py`
  and only run when Qt tests are selected — this project's default `uv run pytest`
  run auto-deselects them (see `tests/conftest.py`), so explicitly run
  `uv run pytest -m qt` (or the specific test files) to confirm they pass, in
  addition to the full default suite.
- Global git workflow (`~/.claude/CLAUDE.md`): current branch must be committed
  before editing (it is — verify with `git status`), then create an isolated
  worktree before making code changes: `git worktree add .worktrees/perspective-widget -b agent/perspective-widget`.
  Do all work for this plan inside that worktree. Never commit to `main`/`master`.

---

### Task 1: Qt `PerspectiveWidget`

**Files:**
- Create: `src/ncca/ngl/widgets/perspectivewidget.py`
- Modify: `src/ncca/ngl/widgets/__init__.py`
- Test: `tests/test_perspective_widget.py`

**Interfaces:**
- Consumes: `ncca.ngl.Mat4`, `ncca.ngl.PerspMode`, `ncca.ngl.perspective(fov, aspect, near, far, mode) -> Mat4`.
- Produces: `PerspectiveWidget` class with `Signal valueChanged(Mat4)`; methods
  `get_fov()->float`, `set_fov(float)`, `get_aspect()->float`, `set_aspect(float)`,
  `get_near()->float`, `set_near(float)`, `get_far()->float`, `set_far(float)`,
  `get_mode()->PerspMode`, `set_mode(PerspMode | int)`, `get_name()->str`,
  `set_name(str)`, `matrix()->Mat4`; `Property` aliases `fov`, `aspect`, `near`,
  `far`, `mode`, `name`. Later tasks (QML) do not depend on this class directly —
  they're independent implementations of the same spec.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_perspective_widget.py`:

```python
import pytest
from PySide6.QtCore import Qt

from ncca.ngl import Mat4, PerspMode, perspective
from ncca.ngl.widgets import PerspectiveWidget


def test_perspectivewidget_initial_value(qt_app, qtbot):
    """Test default initialization values."""
    widget = PerspectiveWidget()
    qtbot.addWidget(widget)

    assert widget.get_fov() == pytest.approx(45.0)
    assert widget.get_aspect() == pytest.approx(1.333)
    assert widget.get_near() == pytest.approx(0.1)
    assert widget.get_far() == pytest.approx(100.0)
    assert widget.get_mode() == PerspMode.OpenGL
    assert widget.get_name() == ""


def test_perspectivewidget_constructor_with_parameters(qt_app, qtbot):
    """Test initialization with custom parameters."""
    name = "MainCamera"
    widget = PerspectiveWidget(name=name, fov=60.0, aspect=1.777, near=1.0, far=500.0)
    qtbot.addWidget(widget)

    assert widget.get_fov() == pytest.approx(60.0)
    assert widget.get_aspect() == pytest.approx(1.777)
    assert widget.get_near() == pytest.approx(1.0)
    assert widget.get_far() == pytest.approx(500.0)
    assert widget.get_name() == name
    assert widget._toggle_button.text() == name


def test_set_fov_aspect_near_far(qt_app, qtbot):
    """Test setting each field individually."""
    widget = PerspectiveWidget()
    qtbot.addWidget(widget)

    widget.set_fov(90.0)
    assert widget.get_fov() == pytest.approx(90.0)

    widget.set_aspect(2.0)
    assert widget.get_aspect() == pytest.approx(2.0)

    widget.set_near(0.5)
    assert widget.get_near() == pytest.approx(0.5)

    widget.set_far(200.0)
    assert widget.get_far() == pytest.approx(200.0)


def test_set_name(qt_app, qtbot):
    """Test setting the widget name."""
    widget = PerspectiveWidget()
    qtbot.addWidget(widget)

    widget.set_name("Cam1")
    assert widget.get_name() == "Cam1"
    assert widget._toggle_button.text() == "Cam1"


def test_property_accessors(qt_app, qtbot):
    """Test Qt Property wrappers."""
    widget = PerspectiveWidget()
    qtbot.addWidget(widget)

    widget.fov = 50.0
    assert widget.get_fov() == pytest.approx(50.0)

    widget.aspect = 1.5
    assert widget.get_aspect() == pytest.approx(1.5)

    widget.near = 0.2
    assert widget.get_near() == pytest.approx(0.2)

    widget.far = 300.0
    assert widget.get_far() == pytest.approx(300.0)

    widget.name = "PropCam"
    assert widget.get_name() == "PropCam"


def test_value_changed_signal_on_fov_change(qt_app, qtbot):
    """Test that valueChanged signal emits a Mat4 when fov changes."""
    widget = PerspectiveWidget()
    qtbot.addWidget(widget)

    with qtbot.waitSignal(widget.valueChanged, timeout=1000) as signal:
        widget.set_fov(60.0)

    assert isinstance(signal.args[0], Mat4)


def test_matrix_calculation(qt_app, qtbot):
    """Test that the perspective matrix matches ncca.ngl.perspective() directly."""
    widget = PerspectiveWidget(fov=50.0, aspect=1.5, near=0.5, far=200.0)
    qtbot.addWidget(widget)

    expected = perspective(50.0, 1.5, 0.5, 200.0, PerspMode.OpenGL)
    actual = widget.matrix()

    for i in range(4):
        for j in range(4):
            assert actual[i][j] == pytest.approx(expected[i][j])


def test_matrix_updates_on_parameter_change(qt_app, qtbot):
    """Test that the matrix updates when a parameter changes."""
    widget = PerspectiveWidget()
    qtbot.addWidget(widget)

    initial = widget.matrix()
    widget.set_fov(90.0)
    updated = widget.matrix()

    assert initial != updated


def test_toggle_collapsed_expand_and_collapse(qt_app, qtbot):
    """Test expanding/collapsing the collapsible section."""
    widget = PerspectiveWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)

    assert widget._toggle_button.isChecked()
    assert widget._content_widget.isVisible()
    assert widget._toggle_button.arrowType() == Qt.ArrowType.DownArrow

    widget._toggle_button.setChecked(False)
    widget.toggle_collapsed(False)
    assert not widget._content_widget.isVisible()
    assert widget._toggle_button.arrowType() == Qt.ArrowType.RightArrow

    widget.toggle_collapsed(True)
    assert widget._content_widget.isVisible()


def test_show_mode_false_hides_combobox(qt_app, qtbot):
    """Test that the mode combo box is absent when show_mode=False."""
    widget = PerspectiveWidget(show_mode=False)
    qtbot.addWidget(widget)

    assert not hasattr(widget, "_mode_combo")
    assert widget.get_mode() == PerspMode.OpenGL


def test_show_mode_true_shows_combobox(qt_app, qtbot):
    """Test that the mode combo box is present with correct items when show_mode=True."""
    widget = PerspectiveWidget(show_mode=True)
    qtbot.addWidget(widget)

    assert widget._mode_combo.count() == 3
    assert widget._mode_combo.itemText(0) == "OpenGL"
    assert widget._mode_combo.itemText(1) == "Vulkan"
    assert widget._mode_combo.itemText(2) == "WebGPU"


def test_mode_switch_changes_matrix(qt_app, qtbot):
    """Test that changing mode produces a different matrix (WebGPU vs OpenGL)."""
    widget = PerspectiveWidget(show_mode=True, fov=50.0, aspect=1.5, near=0.5, far=200.0)
    qtbot.addWidget(widget)

    opengl_matrix = widget.matrix()
    widget._mode_combo.setCurrentIndex(2)  # WebGPU
    webgpu_matrix = widget.matrix()

    assert opengl_matrix != webgpu_matrix
    assert widget.get_mode() == PerspMode.WebGPU


def test_set_mode_programmatically_without_show_mode(qt_app, qtbot):
    """Test that mode can still be set programmatically when show_mode=False."""
    widget = PerspectiveWidget(show_mode=False, fov=50.0, aspect=1.5, near=0.5, far=200.0)
    qtbot.addWidget(widget)

    widget.set_mode(PerspMode.Vulkan)
    assert widget.get_mode() == PerspMode.Vulkan
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_perspective_widget.py -v -m qt`
Expected: FAIL / ERROR — `ModuleNotFoundError` or `ImportError: cannot import name 'PerspectiveWidget'`.

- [ ] **Step 3: Implement `PerspectiveWidget`**

Create `src/ncca/ngl/widgets/perspectivewidget.py`:

```python
"""Widget for editing fov/aspect/near/far and producing a perspective matrix."""

from PySide6.QtCore import Property, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ncca.ngl import Mat4, PerspMode, perspective

_MODE_NAMES = ["OpenGL", "Vulkan", "WebGPU"]
_MODE_BY_NAME = {
    "OpenGL": PerspMode.OpenGL,
    "Vulkan": PerspMode.Vulkan,
    "WebGPU": PerspMode.WebGPU,
}


class PerspectiveWidget(QFrame):
    """A widget for editing fov/aspect/near/far and viewing the resulting perspective Mat4."""

    valueChanged = Signal(Mat4)

    def __init__(
        self,
        parent: QWidget | None = None,
        name: str = "",
        fov: float = 45.0,
        aspect: float = 1.333,
        near: float = 0.1,
        far: float = 100.0,
        show_mode: bool = False,
    ) -> None:
        """Initialize the widget.

        Args:
            parent: The parent widget.
            name: The name of the widget.
            fov: Initial field of view in degrees.
            aspect: Initial aspect ratio.
            near: Initial near clipping plane distance.
            far: Initial far clipping plane distance.
            show_mode: If True, show a combo box to choose the clip-space
                convention (OpenGL/Vulkan/WebGPU); otherwise mode is fixed
                to PerspMode.OpenGL (but can still be set programmatically).
        """
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._name = name
        self._mode = PerspMode.OpenGL
        self._matrix = Mat4()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)

        self._toggle_button = QToolButton(self)
        self._toggle_button.setText(self._name)
        self._toggle_button.setCheckable(True)
        self._toggle_button.setChecked(True)
        self._toggle_button.setStyleSheet("QToolButton { border: none; }")
        self._toggle_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self._toggle_button.setArrowType(Qt.ArrowType.DownArrow)
        self._toggle_button.clicked.connect(self.toggle_collapsed)

        self._content_widget = QWidget(self)
        content_layout = QVBoxLayout(self._content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self._fov_spinbox = self._create_row(
            content_layout, "Fov", fov, 1.0, 179.0, 1.0
        )
        self._aspect_spinbox = self._create_row(
            content_layout, "Aspect", aspect, 0.1, 4.0, 0.01
        )
        self._near_spinbox = self._create_row(
            content_layout, "Near", near, 0.01, 10.0, 0.01
        )
        self._far_spinbox = self._create_row(
            content_layout, "Far", far, 1.0, 1000.0, 1.0
        )

        if show_mode:
            self._mode_combo = QComboBox(self)
            for item in _MODE_NAMES:
                self._mode_combo.addItem(item)
            self._mode_combo.currentIndexChanged.connect(self._on_mode_index_changed)
            row = QHBoxLayout()
            row.addWidget(QLabel("Mode"))
            row.addWidget(self._mode_combo)
            content_layout.addLayout(row)

        main_layout.addWidget(self._toggle_button)
        main_layout.addWidget(self._content_widget)
        self._update_matrix()

    def _create_row(
        self,
        layout: QVBoxLayout,
        label: str,
        value: float,
        minimum: float,
        maximum: float,
        step: float,
    ) -> QDoubleSpinBox:
        """Create a labelled spinbox row and add it to the content layout.

        Args:
            layout: The layout to add the row to.
            label: The row's label text.
            value: The spinbox's initial value.
            minimum: The spinbox's minimum value.
            maximum: The spinbox's maximum value.
            step: The spinbox's single step.

        Returns:
            The created QDoubleSpinBox.
        """
        spinbox = QDoubleSpinBox()
        spinbox.setRange(minimum, maximum)
        spinbox.setSingleStep(step)
        spinbox.setValue(value)
        spinbox.valueChanged.connect(self._update_matrix)
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        row.addWidget(spinbox)
        layout.addLayout(row)
        return spinbox

    def _on_mode_index_changed(self, index: int) -> None:
        """Update the mode from the combo box index and recompute the matrix.

        Args:
            index: The new combo box index.
        """
        self._mode = _MODE_BY_NAME[_MODE_NAMES[index]]
        self._update_matrix()

    def _update_matrix(self) -> None:
        """Recompute the perspective matrix from the current widget values."""
        self._matrix = perspective(
            self._fov_spinbox.value(),
            self._aspect_spinbox.value(),
            self._near_spinbox.value(),
            self._far_spinbox.value(),
            self._mode,
        )
        self.valueChanged.emit(self._matrix)

    def matrix(self) -> Mat4:
        """Return the current perspective matrix.

        Returns:
            The current Mat4.
        """
        return self._matrix

    def toggle_collapsed(self, checked: bool) -> None:
        """Toggle the visibility of the content widget.

        Args:
            checked: Whether the section should be expanded.
        """
        if checked:
            self._toggle_button.setArrowType(Qt.ArrowType.DownArrow)
            self._content_widget.setVisible(True)
        else:
            self._toggle_button.setArrowType(Qt.ArrowType.RightArrow)
            self._content_widget.setVisible(False)

    def get_fov(self) -> float:
        """Return the field of view in degrees."""
        return self._fov_spinbox.value()

    def set_fov(self, fov: float) -> None:
        """Set the field of view in degrees."""
        self._fov_spinbox.setValue(fov)

    def get_aspect(self) -> float:
        """Return the aspect ratio."""
        return self._aspect_spinbox.value()

    def set_aspect(self, aspect: float) -> None:
        """Set the aspect ratio."""
        self._aspect_spinbox.setValue(aspect)

    def get_near(self) -> float:
        """Return the near clipping plane distance."""
        return self._near_spinbox.value()

    def set_near(self, near: float) -> None:
        """Set the near clipping plane distance."""
        self._near_spinbox.setValue(near)

    def get_far(self) -> float:
        """Return the far clipping plane distance."""
        return self._far_spinbox.value()

    def set_far(self, far: float) -> None:
        """Set the far clipping plane distance."""
        self._far_spinbox.setValue(far)

    def get_mode(self) -> PerspMode:
        """Return the current clip-space convention."""
        return self._mode

    def set_mode(self, mode: PerspMode | int) -> None:
        """Set the clip-space convention.

        Args:
            mode: A PerspMode, or an index into the mode combo box order
                (OpenGL, Vulkan, WebGPU).
        """
        if isinstance(mode, int):
            mode = _MODE_BY_NAME[_MODE_NAMES[mode]]
        self._mode = mode
        if hasattr(self, "_mode_combo"):
            self._mode_combo.setCurrentIndex(_MODE_NAMES.index(mode.value))
        else:
            self._update_matrix()

    def get_name(self) -> str:
        """Return the widget name shown on the toggle button."""
        return self._name

    def set_name(self, name: str) -> None:
        """Set the widget name shown on the toggle button."""
        self._name = name
        self._toggle_button.setText(name)

    name = Property(str, get_name, set_name)
    fov = Property(float, get_fov, set_fov)
    aspect = Property(float, get_aspect, set_aspect)
    near = Property(float, get_near, set_near)
    far = Property(float, get_far, set_far)
    mode = Property(PerspMode, get_mode, set_mode)
```

Note: `set_mode` calling `self._mode_combo.setCurrentIndex(...)` triggers
`_on_mode_index_changed`, which calls `_update_matrix()` again — so the
`else: self._update_matrix()` branch only fires when there's no combo box
to trigger it. This avoids a double emit when `show_mode=True`.

Modify `src/ncca/ngl/widgets/__init__.py` — add the import and `__all__` entry,
keeping alphabetical grouping consistent with existing entries:

```python
from .lookatwidget import LookAtWidget
from .mat2widget import Mat2Widget
from .mat3widget import Mat3Widget
from .mat4widget import Mat4Widget
from .perspectivewidget import PerspectiveWidget
from .rgbacolourwidget import RGBAColourWidget
```

```python
__all__ = [
    "Vec2Widget",
    "Vec3Widget",
    "Vec4Widget",
    "TransformWidget",
    "LookAtWidget",
    "PerspectiveWidget",
    "RGBColourWidget",
    "RGBAColourWidget",
    "Mat2Widget",
    "Mat3Widget",
    "Mat4Widget",
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_perspective_widget.py -v -m qt`
Expected: PASS (all tests green).

- [ ] **Step 5: Lint**

Run: `uv run ruff check src/ncca/ngl/widgets/perspectivewidget.py src/ncca/ngl/widgets/__init__.py`
Expected: no errors. Fix any `ANN`/`D` issues before proceeding.

- [ ] **Step 6: Commit**

```bash
git add src/ncca/ngl/widgets/perspectivewidget.py src/ncca/ngl/widgets/__init__.py tests/test_perspective_widget.py
git commit -m "feat(widgets): add PerspectiveWidget for editing fov/aspect/near/far"
```

---

### Task 2: QML `PerspectiveModel`

**Files:**
- Create: `src/ncca/ngl/qml/perspective_model.py`
- Modify: `src/ncca/ngl/qml/__init__.py`
- Test: `tests/test_qml_perspective_model.py`

**Interfaces:**
- Consumes: `ncca.ngl.Mat4`, `ncca.ngl.PerspMode`, `ncca.ngl.perspective(...)`.
- Produces: `PerspectiveModel(QObject)` registered via `@QmlElement`, with
  `Property(float)` for `fov`, `aspect`, `near`, `far` (getters `get_fov` etc.,
  setters `set_fov` etc.), `Property(int) modeIndex` (getter `get_mode_index`,
  setter `set_mode_index`), `Signal valueChanged()`, `Slot(result=list) mode_names()`,
  `Property(Mat4) matrix` (getter `get_matrix`), `Slot(result=str) matrix_text()`.
  Task 3 (the `.qml` view) binds directly to these property names.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_qml_perspective_model.py`:

```python
from ncca.ngl import PerspMode, perspective


def test_default_values_and_matrix(qt_app):
    from ncca.ngl.qml.perspective_model import PerspectiveModel

    model = PerspectiveModel()

    assert model.fov == 45.0
    assert model.aspect == 1.333
    assert model.near == 0.1
    assert model.far == 100.0
    assert model.modeIndex == 0
    assert model.get_matrix() == perspective(45.0, 1.333, 0.1, 100.0, PerspMode.OpenGL)


def test_changing_fov_updates_matrix(qt_app):
    from ncca.ngl.qml.perspective_model import PerspectiveModel

    model = PerspectiveModel()
    model.fov = 60.0

    assert model.get_matrix() == perspective(60.0, 1.333, 0.1, 100.0, PerspMode.OpenGL)


def test_changing_aspect_near_far_updates_matrix(qt_app):
    from ncca.ngl.qml.perspective_model import PerspectiveModel

    model = PerspectiveModel()
    model.aspect = 1.777
    model.near = 1.0
    model.far = 500.0

    assert model.get_matrix() == perspective(45.0, 1.777, 1.0, 500.0, PerspMode.OpenGL)


def test_changing_mode_index_updates_matrix(qt_app):
    from ncca.ngl.qml.perspective_model import PerspectiveModel

    model = PerspectiveModel()
    model.modeIndex = model.mode_names().index("WebGPU")

    assert model.get_matrix() == perspective(45.0, 1.333, 0.1, 100.0, PerspMode.WebGPU)


def test_mode_names(qt_app):
    from ncca.ngl.qml.perspective_model import PerspectiveModel

    model = PerspectiveModel()

    assert model.mode_names() == ["OpenGL", "Vulkan", "WebGPU"]


def test_changing_fov_emits_value_changed(qt_app, qtbot):
    from ncca.ngl.qml.perspective_model import PerspectiveModel

    model = PerspectiveModel()

    with qtbot.waitSignal(model.valueChanged, timeout=1000):
        model.fov = 70.0


def test_matrix_text_format(qt_app):
    from ncca.ngl.qml.perspective_model import PerspectiveModel

    model = PerspectiveModel()
    text = model.matrix_text()

    rows = text.split("\n")
    assert len(rows) == 4
    for row in rows:
        assert len(row.split()) == 4
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_qml_perspective_model.py -v -m qt`
Expected: FAIL — `ModuleNotFoundError: No module named 'ncca.ngl.qml.perspective_model'`.

- [ ] **Step 3: Implement `PerspectiveModel`**

Create `src/ncca/ngl/qml/perspective_model.py`:

```python
"""QML-exposed model combining fov/aspect/near/far into a perspective matrix."""

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtQml import QmlElement

from ncca.ngl import Mat4, PerspMode, perspective

QML_IMPORT_NAME = "ncca.ngl.qml"
QML_IMPORT_MAJOR_VERSION = 1

MODE_NAMES = ["OpenGL", "Vulkan", "WebGPU"]
MODES = [PerspMode.OpenGL, PerspMode.Vulkan, PerspMode.WebGPU]


@QmlElement
class PerspectiveModel(QObject):
    """Combines fov/aspect/near/far and a clip-space mode into a perspective Mat4."""

    valueChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize the model with default projection parameters.

        Args:
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._fov = 45.0
        self._aspect = 1.333
        self._near = 0.1
        self._far = 100.0
        self._mode_index = 0
        self._matrix = Mat4()
        self._update_matrix()

    def get_fov(self) -> float:
        """Return the field of view in degrees.

        Returns:
            The current fov value.
        """
        return self._fov

    def set_fov(self, value: float) -> None:
        """Set the field of view and recompute the matrix.

        Args:
            value: The new fov value in degrees.
        """
        self._fov = value
        self._update_matrix()

    fov = Property(float, get_fov, set_fov, notify=valueChanged)

    def get_aspect(self) -> float:
        """Return the aspect ratio.

        Returns:
            The current aspect ratio.
        """
        return self._aspect

    def set_aspect(self, value: float) -> None:
        """Set the aspect ratio and recompute the matrix.

        Args:
            value: The new aspect ratio.
        """
        self._aspect = value
        self._update_matrix()

    aspect = Property(float, get_aspect, set_aspect, notify=valueChanged)

    def get_near(self) -> float:
        """Return the near clipping plane distance.

        Returns:
            The current near value.
        """
        return self._near

    def set_near(self, value: float) -> None:
        """Set the near clipping plane distance and recompute the matrix.

        Args:
            value: The new near value.
        """
        self._near = value
        self._update_matrix()

    near = Property(float, get_near, set_near, notify=valueChanged)

    def get_far(self) -> float:
        """Return the far clipping plane distance.

        Returns:
            The current far value.
        """
        return self._far

    def set_far(self, value: float) -> None:
        """Set the far clipping plane distance and recompute the matrix.

        Args:
            value: The new far value.
        """
        self._far = value
        self._update_matrix()

    far = Property(float, get_far, set_far, notify=valueChanged)

    def get_mode_index(self) -> int:
        """Return the index into MODE_NAMES currently in use.

        Returns:
            The current mode index.
        """
        return self._mode_index

    def set_mode_index(self, index: int) -> None:
        """Set the clip-space mode by index and recompute the matrix.

        Args:
            index: An index into MODE_NAMES/MODES.
        """
        self._mode_index = index
        self._update_matrix()

    modeIndex = Property(int, get_mode_index, set_mode_index, notify=valueChanged)

    @Slot(result=list)
    def mode_names(self) -> list:
        """Return the ordered list of clip-space mode display names.

        Returns:
            The mode names, in combo-box order.
        """
        return list(MODE_NAMES)

    def _update_matrix(self) -> None:
        """Recompute the perspective matrix from the current property values."""
        self._matrix = perspective(
            self._fov, self._aspect, self._near, self._far, MODES[self._mode_index]
        )
        self.valueChanged.emit()

    @Slot(result=Mat4)
    def get_matrix(self) -> Mat4:
        """Return the current perspective matrix.

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

Modify `src/ncca/ngl/qml/__init__.py` — add the import and `__all__` entry:

```python
from .mat4_model import Mat4Model
from .perspective_model import PerspectiveModel
from .rgb_colour_model import RGBColourModel
```

```python
__all__ = [
    "Vec2Model",
    "Vec3Model",
    "Vec4Model",
    "Mat2Model",
    "Mat3Model",
    "Mat4Model",
    "TransformModel",
    "LookAtModel",
    "PerspectiveModel",
    "RGBColourModel",
    "RGBAColourModel",
    "import_path",
    "add_import_path",
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_qml_perspective_model.py -v -m qt`
Expected: PASS (all tests green).

- [ ] **Step 5: Lint**

Run: `uv run ruff check src/ncca/ngl/qml/perspective_model.py src/ncca/ngl/qml/__init__.py`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add src/ncca/ngl/qml/perspective_model.py src/ncca/ngl/qml/__init__.py tests/test_qml_perspective_model.py
git commit -m "feat(qml): add PerspectiveModel for editing fov/aspect/near/far"
```

---

### Task 3: QML `PerspectiveWidget.qml` view + registration + demo wiring

**Files:**
- Create: `src/ncca/ngl/qml/PerspectiveWidget.qml`
- Modify: `src/ncca/ngl/qml/qmldir`
- Modify: `src/ncca/ngl/qml/main.qml`

**Interfaces:**
- Consumes: `PerspectiveModel` from Task 2 — properties `fov`, `aspect`, `near`,
  `far`, `modeIndex`, `matrix`; slots `mode_names()`, `matrix_text()`; signal
  `valueChanged()`. `DecimalSpinBox` component (`realValue`, `from_`, `to_`
  properties) already exists in `qmldir`.
- Produces: `PerspectiveWidget` QML type — `property string name`,
  `property alias model: perspectiveModel`, `property bool showMode: false`,
  `signal valueChanged()`. Registered in `qmldir` so `import ncca.ngl.qml 1.0`
  resolves it; used in `main.qml`.

This task has no automated test (QML views aren't unit tested elsewhere in this
codebase — `LookAtWidget.qml` has none either); verification is manual via the
demo app in Step 3.

- [ ] **Step 1: Create the QML view**

Create `src/ncca/ngl/qml/PerspectiveWidget.qml`:

```qml
// src/ncca/ngl/qml/PerspectiveWidget.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ncca.ngl.qml 1.0

Frame {
    id: root

    property string name: ""
    property alias model: perspectiveModel
    property bool showMode: false
    signal valueChanged()

    PerspectiveModel {
        id: perspectiveModel
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

            RowLayout {
                Label { text: "Fov" }
                DecimalSpinBox {
                    id: fovSpin
                    realValue: perspectiveModel.fov
                    from_: 1.0; to_: 179.0; stepSize_: 1.0; decimals: 1
                    onRealValueChanged: {
                        if (perspectiveModel.fov !== realValue) {
                            perspectiveModel.fov = realValue
                        }
                    }
                }
            }

            RowLayout {
                Label { text: "Aspect" }
                DecimalSpinBox {
                    id: aspectSpin
                    realValue: perspectiveModel.aspect
                    from_: 0.1; to_: 4.0; stepSize_: 0.01; decimals: 3
                    onRealValueChanged: {
                        if (perspectiveModel.aspect !== realValue) {
                            perspectiveModel.aspect = realValue
                        }
                    }
                }
            }

            RowLayout {
                Label { text: "Near" }
                DecimalSpinBox {
                    id: nearSpin
                    realValue: perspectiveModel.near
                    from_: 0.01; to_: 10.0; stepSize_: 0.01; decimals: 2
                    onRealValueChanged: {
                        if (perspectiveModel.near !== realValue) {
                            perspectiveModel.near = realValue
                        }
                    }
                }
            }

            RowLayout {
                Label { text: "Far" }
                DecimalSpinBox {
                    id: farSpin
                    realValue: perspectiveModel.far
                    from_: 1.0; to_: 1000.0; stepSize_: 1.0; decimals: 1
                    onRealValueChanged: {
                        if (perspectiveModel.far !== realValue) {
                            perspectiveModel.far = realValue
                        }
                    }
                }
            }

            RowLayout {
                visible: root.showMode
                Label { text: "Mode" }
                ComboBox {
                    model: perspectiveModel.mode_names()
                    currentIndex: perspectiveModel.modeIndex
                    onCurrentIndexChanged: perspectiveModel.modeIndex = currentIndex
                }
            }
        }
    }
}
```

- [ ] **Step 2: Register the type in `qmldir`**

Modify `src/ncca/ngl/qml/qmldir` — add after the `LookAtWidget` line, keeping the
existing declaration order (widgets before colour widgets):

```
LookAtWidget 1.0 LookAtWidget.qml
PerspectiveWidget 1.0 PerspectiveWidget.qml
RGBColourWidget 1.0 RGBColourWidget.qml
```

- [ ] **Step 3: Wire into the demo `main.qml` and verify manually**

Modify `src/ncca/ngl/qml/main.qml` — add after the `LookAtWidget` block:

```qml
            PerspectiveWidget { id: perspectiveWidget; name: "Perspective Widget"; showMode: true }
            Label {
                id: perspectiveMatrixLabel
                font.family: "monospace"
                text: perspectiveWidget.model.matrix_text()
                Connections {
                    target: perspectiveWidget.model
                    function onValueChanged() {
                        perspectiveMatrixLabel.text = perspectiveWidget.model.matrix_text()
                    }
                }
            }
```

Run the demo and confirm the widget appears, the four spinboxes and mode combo
work, and the matrix label updates live:

Run: `uv run python -m ncca.ngl.qml`
Expected: window opens showing all widgets including "Perspective Widget" with
a working fov/aspect/near/far/mode UI and a live-updating matrix label.
Manually verify, then close the window.

- [ ] **Step 4: Commit**

```bash
git add src/ncca/ngl/qml/PerspectiveWidget.qml src/ncca/ngl/qml/qmldir src/ncca/ngl/qml/main.qml
git commit -m "feat(qml): add PerspectiveWidget.qml view and wire into demo"
```

---

### Task 4: Docs

**Files:**
- Modify: `docs/docs/Widgets.md`
- Modify: `docs/docs/QmlWidgets.md`

**Interfaces:**
- Consumes: `ncca.ngl.widgets.PerspectiveWidget` (Task 1), `ncca.ngl.qml.PerspectiveModel` (Task 2).
- Produces: rendered docs pages; no code interface.

- [ ] **Step 1: Add `PerspectiveWidget` to `docs/docs/Widgets.md`**

Insert after the `## LookAtWidget` section (after line 25, before `## RGBColourWidget`):

```markdown
## PerspectiveWidget

::: ncca.ngl.widgets.PerspectiveWidget

```

- [ ] **Step 2: Add `PerspectiveModel` to `docs/docs/QmlWidgets.md`**

Insert after the `## LookAtModel` section (after line 25, before `## RGBColourModel`):

```markdown
## PerspectiveModel

::: ncca.ngl.qml.PerspectiveModel

```

- [ ] **Step 3: Verify the strict docs build**

Run: `uv run --with mkdocs --with "mkdocstrings[python]" mkdocs build --strict -f docs/mkdocs.yml`
Expected: build succeeds with zero warnings.

- [ ] **Step 4: Commit**

```bash
git add docs/docs/Widgets.md docs/docs/QmlWidgets.md
git commit -m "docs(widgets): document PerspectiveWidget and PerspectiveModel"
```

---

### Task 5: Full verification

**Files:** none (verification only).

- [ ] **Step 1: Run the full default test suite**

Run: `uv run pytest`
Expected: all pass (Qt/OpenGL/WebGPU-marked tests are deselected by default, per
`tests/conftest.py`).

- [ ] **Step 2: Run the Qt-marked suite explicitly**

Run: `uv run pytest -m qt`
Expected: all pass, including the new `test_perspective_widget.py` and
`test_qml_perspective_model.py`.

- [ ] **Step 3: Run the full lint check**

Run: `uv run ruff check src/`
Expected: no errors.

- [ ] **Step 4: Re-run the strict docs build**

Run: `uv run --with mkdocs --with "mkdocstrings[python]" mkdocs build --strict -f docs/mkdocs.yml`
Expected: zero warnings.

No commit for this task — it's a verification checkpoint only. If any step
fails, fix the issue in the relevant earlier task's files and re-commit there.
