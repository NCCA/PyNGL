"""
Unit tests for PySideEventHandlingMixin

Tests cover mouse-based camera control, keyboard shortcuts, wheel zooming,
and camera state management functionality.
"""

from unittest.mock import Mock

import pytest
from PySide6.QtCore import QPointF, Qt

from ncca.ngl import Vec3
from ncca.ngl.opengl import PySideEventHandlingMixin


class MockEventHandlingWindow(PySideEventHandlingMixin):
    """Mock class that uses the EventHandlingMixin"""

    def __init__(self):
        self.update_called = False
        self.close_called = False

    def update(self) -> None:
        """Mock update method"""
        self.update_called = True

    def close(self) -> None:
        """Mock close method"""
        self.close_called = True


@pytest.fixture
def event_window(qt_app):
    """Create a test window with event handling"""
    window = MockEventHandlingWindow()
    window.setup_event_handling()
    return window


def test_setup_event_handling_default_values(qt_app, event_window):
    """Test setup_event_handling with default parameters"""
    assert event_window.rotate is False
    assert event_window.translate is False
    assert event_window.spin_x_face == pytest.approx(0.0)
    assert event_window.spin_y_face == pytest.approx(0.0)
    assert event_window.original_x_rotation == pytest.approx(0.0)
    assert event_window.original_y_rotation == pytest.approx(0.0)
    assert event_window.original_x_pos == pytest.approx(0.0)
    assert event_window.original_y_pos == pytest.approx(0.0)
    assert event_window.model_position == Vec3(0, 0, 0)
    assert (
        event_window.rotation_sensitivity
        == PySideEventHandlingMixin.DEFAULT_ROTATION_SENSITIVITY
    )
    assert (
        event_window.translation_sensitivity
        == PySideEventHandlingMixin.DEFAULT_TRANSLATION_SENSITIVITY
    )
    assert (
        event_window.zoom_sensitivity
        == PySideEventHandlingMixin.DEFAULT_ZOOM_SENSITIVITY
    )


def test_setup_event_handling_custom_values(qt_app):
    """Test setup_event_handling with custom parameters"""
    window = MockEventHandlingWindow()
    initial_pos = Vec3(1, 2, 3)
    window.setup_event_handling(
        rotation_sensitivity=0.8,
        translation_sensitivity=0.02,
        zoom_sensitivity=0.2,
        initial_position=initial_pos,
    )

    assert window.rotation_sensitivity == pytest.approx(0.8)
    assert window.translation_sensitivity == pytest.approx(0.02)
    assert window.zoom_sensitivity == pytest.approx(0.2)
    assert window.model_position.x == pytest.approx(1.0)
    assert window.model_position.y == pytest.approx(2.0)
    assert window.model_position.z == pytest.approx(3.0)
    assert window.INCREMENT == pytest.approx(0.02)
    assert window.ZOOM == pytest.approx(0.2)


def test_reset_camera(qt_app, event_window):
    """Test camera reset functionality"""
    # Set some non-zero values
    event_window.spin_x_face = 45
    event_window.spin_y_face = 90
    event_window.model_position.set(1, 2, 3)

    # Reset camera
    event_window.reset_camera()

    # Check values are reset
    assert event_window.spin_x_face == pytest.approx(0)
    assert event_window.spin_y_face == pytest.approx(0)
    assert event_window.model_position.x == pytest.approx(0)
    assert event_window.model_position.y == pytest.approx(0)
    assert event_window.model_position.z == pytest.approx(0)


def test_key_press_event_escape(qt_app, event_window):
    """Test escape key closes the application"""
    # Create mock key event
    event = Mock()
    event.key.return_value = Qt.Key_Escape

    event_window.keyPressEvent(event)

    assert event_window.close_called is True
    assert event_window.update_called is True


def test_key_press_event_wireframe_mode(qt_app, event_window, monkeypatch):
    """Test W key switches to wireframe mode"""
    event = Mock()
    event.key.return_value = Qt.Key_W

    mock_gl_polygon_mode = Mock()
    # Use fixture-provided monkeypatch to set attribute (non-raising to avoid import issues)
    monkeypatch.setattr("OpenGL.GL.glPolygonMode", mock_gl_polygon_mode, raising=False)

    event_window.keyPressEvent(event)

    mock_gl_polygon_mode.assert_called_once()
    assert event_window.update_called is True


def test_key_press_event_solid_mode(qt_app, event_window, monkeypatch):
    """Test S key switches to solid fill mode"""
    event = Mock()
    event.key.return_value = Qt.Key_S

    mock_gl_polygon_mode = Mock()
    monkeypatch.setattr("OpenGL.GL.glPolygonMode", mock_gl_polygon_mode, raising=False)

    event_window.keyPressEvent(event)

    mock_gl_polygon_mode.assert_called_once()
    assert event_window.update_called is True


def test_key_press_event_space_reset(qt_app, event_window):
    """Test space key resets camera"""
    # Set some values first
    event_window.spin_x_face = 45
    event_window.model_position.set(1, 2, 3)

    event = Mock()
    event.key.return_value = Qt.Key_Space

    event_window.keyPressEvent(event)

    assert event_window.spin_x_face == pytest.approx(0)
    assert event_window.model_position.x == pytest.approx(0)
    assert event_window.model_position.y == pytest.approx(0)
    assert event_window.model_position.z == pytest.approx(0)
    assert event_window.update_called is True


def test_key_press_event_other_key(qt_app, event_window, monkeypatch):
    """Test other keys call parent keyPressEvent"""
    event = Mock()
    event.key.return_value = Qt.Key_A

    # Mock super() call by temporarily replacing builtins.super via monkeypatch
    mock_parent = Mock()
    monkeypatch.setattr(
        "builtins.super", lambda *args, **kwargs: mock_parent, raising=False
    )

    event_window.keyPressEvent(event)

    mock_parent.keyPressEvent.assert_called_once_with(event)


def test_mouse_press_event_left_button(qt_app, event_window):
    """Test left mouse button press starts rotation"""
    event = Mock()
    event.button.return_value = Qt.LeftButton
    event.position.return_value = QPointF(100, 200)

    event_window.mousePressEvent(event)

    assert event_window.rotate is True
    assert event_window.original_x_rotation == 100
    assert event_window.original_y_rotation == 200


def test_mouse_press_event_right_button(qt_app, event_window):
    """Test right mouse button press starts translation"""
    event = Mock()
    event.button.return_value = Qt.RightButton
    event.position.return_value = QPointF(150, 250)

    event_window.mousePressEvent(event)

    assert event_window.translate is True
    assert event_window.original_x_pos == 150
    assert event_window.original_y_pos == 250


def test_mouse_release_event_left_button(qt_app, event_window):
    """Test left mouse button release stops rotation"""
    event_window.rotate = True

    event = Mock()
    event.button.return_value = Qt.LeftButton

    event_window.mouseReleaseEvent(event)

    assert event_window.rotate is False


def test_mouse_release_event_right_button(qt_app, event_window):
    """Test right mouse button release stops translation"""
    event_window.translate = True

    event = Mock()
    event.button.return_value = Qt.RightButton

    event_window.mouseReleaseEvent(event)

    assert event_window.translate is False


def test_mouse_move_event_rotation(qt_app, event_window):
    """Test mouse movement during rotation"""
    # Setup rotation state
    event_window.rotate = True
    event_window.original_x_rotation = 100
    event_window.original_y_rotation = 200
    event_window.rotation_sensitivity = 1

    event = Mock()
    event.buttons.return_value = Qt.LeftButton
    event.position.return_value = QPointF(120, 180)

    event_window.mouseMoveEvent(event)

    # Check rotation values updated
    assert event_window.spin_x_face == -20  # 1.0 * (180 - 200)
    assert event_window.spin_y_face == 20  # 1.0 * (120 - 100)
    assert event_window.original_x_rotation == 120
    assert event_window.original_y_rotation == 180
    assert event_window.update_called is True


def test_mouse_move_event_translation(qt_app, event_window):
    """Test mouse movement during translation"""
    # Setup translation state
    event_window.translate = True
    event_window.original_x_pos = 100
    event_window.original_y_pos = 200
    event_window.translation_sensitivity = 0.1

    event = Mock()
    event.buttons.return_value = Qt.RightButton
    event.position.return_value = QPointF(110, 190)

    event_window.mouseMoveEvent(event)

    # Check translation values updated
    assert event_window.model_position.x == pytest.approx(1.0)  # 0.1 * (110 - 100)
    assert event_window.model_position.y == pytest.approx(1.0)  # -0.1 * (190 - 200)
    assert event_window.original_x_pos == 110
    assert event_window.original_y_pos == 190
    assert event_window.update_called is True


def test_mouse_move_event_no_action(qt_app, event_window):
    """Test mouse movement when no buttons active"""
    event_window.rotate = False
    event_window.translate = False

    event = Mock()
    event.buttons.return_value = Qt.NoButton

    event_window.mouseMoveEvent(event)

    # Should not update anything
    assert event_window.update_called is False


def test_wheel_event_positive_delta(qt_app, event_window):
    """Test mouse wheel scroll up (zoom in)"""
    event_window.zoom_sensitivity = 0.5
    initial_z = event_window.model_position.z

    event = Mock()
    angle_delta = Mock()
    angle_delta.y.return_value = 120  # Positive wheel delta
    angle_delta.x.return_value = 0
    event.angleDelta.return_value = angle_delta

    event_window.wheelEvent(event)

    assert event_window.model_position.z == pytest.approx(initial_z + 0.5)
    assert event_window.update_called is True


def test_wheel_event_negative_delta(qt_app, event_window):
    """Test mouse wheel scroll down (zoom out)"""
    event_window.zoom_sensitivity = 0.5
    initial_z = event_window.model_position.z

    event = Mock()
    angle_delta = Mock()
    angle_delta.y.return_value = -120  # Negative wheel delta
    angle_delta.x.return_value = 0
    event.angleDelta.return_value = angle_delta

    event_window.wheelEvent(event)

    assert event_window.model_position.z == pytest.approx(initial_z - 0.5)
    assert event_window.update_called is True


def test_wheel_event_x_axis_delta(qt_app, event_window):
    """Test mouse wheel using x-axis delta (horizontal scroll)"""
    event_window.zoom_sensitivity = 0.3
    initial_z = event_window.model_position.z

    event = Mock()
    angle_delta = Mock()
    angle_delta.y.return_value = 0
    angle_delta.x.return_value = 120  # Positive x delta
    event.angleDelta.return_value = angle_delta

    event_window.wheelEvent(event)

    assert event_window.model_position.z == pytest.approx(initial_z + 0.3)
    assert event_window.update_called is True


def test_wheel_event_zero_delta(qt_app, event_window):
    """Test mouse wheel with zero delta"""
    initial_z = event_window.model_position.z

    event = Mock()
    angle_delta = Mock()
    angle_delta.y.return_value = 0
    angle_delta.x.return_value = 0
    event.angleDelta.return_value = angle_delta

    event_window.wheelEvent(event)

    # Position should not change
    assert event_window.model_position.z == initial_z
    assert event_window.update_called is True


def test_constants(qt_app):
    """Test default sensitivity constants"""
    assert PySideEventHandlingMixin.DEFAULT_ROTATION_SENSITIVITY == pytest.approx(0.5)
    assert PySideEventHandlingMixin.DEFAULT_TRANSLATION_SENSITIVITY == pytest.approx(
        0.01
    )
    assert PySideEventHandlingMixin.DEFAULT_ZOOM_SENSITIVITY == pytest.approx(0.1)


def test_mouse_movement_rotation_with_different_sensitivity(qt_app):
    """Test mouse rotation with different sensitivity values"""
    window = MockEventHandlingWindow()
    window.setup_event_handling(rotation_sensitivity=2.0)

    # Setup rotation state
    window.rotate = True
    window.original_x_rotation = 50
    window.original_y_rotation = 50

    event = Mock()
    event.buttons.return_value = Qt.LeftButton
    event.position.return_value = QPointF(60, 40)

    window.mouseMoveEvent(event)

    # With sensitivity 2.0: diff_y = 40-50 = -10, so spin_x_face = 2.0 * -10 = -20
    # diff_x = 60-50 = 10, so spin_y_face = 2.0 * 10 = 20
    assert window.spin_x_face == -20
    assert window.spin_y_face == 20


def test_mouse_movement_translation_with_different_sensitivity(qt_app):
    """Test mouse translation with different sensitivity values"""
    window = MockEventHandlingWindow()
    window.setup_event_handling(translation_sensitivity=0.5)

    # Setup translation state
    window.translate = True
    window.original_x_pos = 100
    window.original_y_pos = 100

    event = Mock()
    event.buttons.return_value = Qt.RightButton
    event.position.return_value = QPointF(120, 80)

    window.mouseMoveEvent(event)

    # With sensitivity 0.5: diff_x = 120-100 = 20, so x += 0.5 * 20 = 10
    # diff_y = 80-100 = -20, so y -= 0.5 * -20 = 10
    assert window.model_position.x == pytest.approx(10.0)
    assert window.model_position.y == pytest.approx(10.0)


def test_event_handling_target_protocol(qt_app):
    """Test that the protocol is properly defined"""

    # This should not raise any errors
    window = MockEventHandlingWindow()

    # Check that our test class implements the protocol
    assert hasattr(window, "update")
    assert hasattr(window, "close")
    assert callable(window.update)
    assert callable(window.close)


def test_mouse_move_event_rotation_without_left_button(qt_app, event_window):
    """Test mouse movement during rotation mode but without left button pressed"""
    # Setup rotation state
    event_window.rotate = True
    event_window.original_x_rotation = 100
    event_window.original_y_rotation = 200

    event = Mock()
    event.buttons.return_value = Qt.NoButton  # No button pressed
    event.position.return_value = QPointF(120, 180)

    event_window.mouseMoveEvent(event)

    # Should not update rotation values
    assert event_window.spin_x_face == 0
    assert event_window.spin_y_face == 0
    assert event_window.update_called is False


def test_mouse_move_event_translation_without_right_button(qt_app, event_window):
    """Test mouse movement during translation mode but without right button pressed"""
    # Setup translation state
    event_window.translate = True
    event_window.original_x_pos = 100
    event_window.original_y_pos = 200

    event = Mock()
    event.buttons.return_value = Qt.NoButton  # No button pressed
    event.position.return_value = QPointF(110, 190)

    event_window.mouseMoveEvent(event)

    # Should not update position
    assert event_window.model_position.x == 0
    assert event_window.model_position.y == 0
    assert event_window.update_called is False


def test_mouse_press_event_middle_button(qt_app, event_window):
    """Test middle mouse button press (should be ignored)"""
    event = Mock()
    event.button.return_value = Qt.MiddleButton
    event.position.return_value = QPointF(100, 200)

    event_window.mousePressEvent(event)

    # Should not change any state
    assert event_window.rotate is False
    assert event_window.translate is False


def test_mouse_release_event_middle_button(qt_app, event_window):
    """Test middle mouse button release (should be ignored)"""
    event_window.rotate = True
    event_window.translate = True

    event = Mock()
    event.button.return_value = Qt.MiddleButton

    event_window.mouseReleaseEvent(event)

    # Should not change state
    assert event_window.rotate is True
    assert event_window.translate is True


def test_setup_event_handling_with_none_position(qt_app):
    """Test setup_event_handling with None initial position"""
    window = MockEventHandlingWindow()
    window.setup_event_handling(initial_position=None)

    assert window.model_position.x == 0
    assert window.model_position.y == 0
    assert window.model_position.z == 0


def test_wheel_event_priority_y_over_x(qt_app, event_window):
    """Test that y delta takes priority over x delta when both are non-zero"""
    event_window.zoom_sensitivity = 0.5
    initial_z = event_window.model_position.z

    event = Mock()
    angle_delta = Mock()
    angle_delta.y.return_value = 120  # Positive y delta
    angle_delta.x.return_value = -120  # Negative x delta
    event.angleDelta.return_value = angle_delta

    event_window.wheelEvent(event)

    # Should use y delta (120), not x delta (-120)
    assert event_window.model_position.z == pytest.approx(initial_z + 0.5)
    assert event_window.update_called is True


class MockEmbeddedWidget(PySideEventHandlingMixin):
    """Mixin host that lives inside a window, the way a QOpenGLWidget does.

    QWidget has window() to walk up to the top level, so this stands in for the
    embedded case, where closing the host itself would only hide the viewport
    and leave the rest of the window sitting there.
    """

    def __init__(self):
        self.update_called = False
        self.close_called = False
        self.top_level = Mock()

    def update(self) -> None:
        self.update_called = True

    def close(self) -> None:
        self.close_called = True

    def window(self):
        return self.top_level


def test_close_target_is_self_when_there_is_no_window(qt_app, event_window):
    """A QOpenGLWindow is already top level and has no window() to walk up to."""
    assert event_window.close_target() is event_window


def test_close_target_is_the_top_level_window_when_embedded(qt_app):
    """A QOpenGLWidget must close the window it is in, not itself."""
    widget = MockEmbeddedWidget()
    widget.setup_event_handling()

    assert widget.close_target() is widget.top_level


def test_key_press_event_escape_closes_the_window_not_the_widget(qt_app):
    """Escape used to hide the viewport and leave the panel behind."""
    widget = MockEmbeddedWidget()
    widget.setup_event_handling()

    event = Mock()
    event.key.return_value = Qt.Key_Escape
    widget.keyPressEvent(event)

    widget.top_level.close.assert_called_once()
    assert widget.close_called is False


def test_key_shortcuts_can_be_declined(qt_app, monkeypatch):
    """handle_key_shortcuts=False hands every key to the parent untouched."""
    window = MockEventHandlingWindow()
    window.setup_event_handling(handle_key_shortcuts=False)

    mock_parent = Mock()
    monkeypatch.setattr(
        "builtins.super", lambda *args, **kwargs: mock_parent, raising=False
    )

    for key in (Qt.Key_Escape, Qt.Key_W, Qt.Key_S, Qt.Key_Space):
        event = Mock()
        event.key.return_value = key
        window.keyPressEvent(event)

    assert mock_parent.keyPressEvent.call_count == 4
    assert window.close_called is False


def test_key_shortcuts_are_on_by_default(qt_app, event_window):
    """The 52 window demos rely on this, so the default must not change."""
    assert event_window.handle_key_shortcuts is True


def test_wireframe_flag_tracks_the_w_and_s_keys(qt_app, event_window, monkeypatch):
    """paintGL that sets the polygon mode itself needs state, not a bare GL call."""
    monkeypatch.setattr("OpenGL.GL.glPolygonMode", Mock(), raising=False)
    assert event_window.wireframe is False

    event = Mock()
    event.key.return_value = Qt.Key_W
    event_window.keyPressEvent(event)
    assert event_window.wireframe is True

    event = Mock()
    event.key.return_value = Qt.Key_S
    event_window.keyPressEvent(event)
    assert event_window.wireframe is False


def test_setup_does_not_clobber_an_existing_wireframe_attribute(qt_app):
    """Several demos own a wireframe of their own before calling setup."""
    window = MockEventHandlingWindow()
    window.wireframe = True
    window.setup_event_handling()

    assert window.wireframe is True
