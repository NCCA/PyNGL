"""
Unit tests for PySideEventHandlingMixin

Tests cover mouse-based camera control, keyboard shortcuts, wheel zooming,
and camera state management functionality.
"""

from unittest.mock import Mock, patch

import pytest
from PySide6.QtCore import QPointF, Qt

from ncca.ngl import PySideEventHandlingMixin, Vec3


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
def event_window():
    """Create a test window with event handling"""
    window = MockEventHandlingWindow()
    window.setup_event_handling()
    return window


def test_setup_event_handling_default_values(event_window):
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
    assert event_window.rotation_sensitivity == PySideEventHandlingMixin.DEFAULT_ROTATION_SENSITIVITY
    assert event_window.translation_sensitivity == PySideEventHandlingMixin.DEFAULT_TRANSLATION_SENSITIVITY
    assert event_window.zoom_sensitivity == PySideEventHandlingMixin.DEFAULT_ZOOM_SENSITIVITY


def test_setup_event_handling_custom_values():
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


def test_reset_camera(event_window):
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


def test_keyPressEvent_escape(event_window):
    """Test escape key closes the application"""
    # Create mock key event
    event = Mock()
    event.key.return_value = Qt.Key_Escape

    event_window.keyPressEvent(event)

    assert event_window.close_called is True
    assert event_window.update_called is True


@patch("OpenGL.GL.glPolygonMode")
def test_keyPressEvent_wireframe_mode(mock_gl_polygon_mode, event_window):
    """Test W key switches to wireframe mode"""
    event = Mock()
    event.key.return_value = Qt.Key_W

    event_window.keyPressEvent(event)

    mock_gl_polygon_mode.assert_called_once()
    assert event_window.update_called is True


@patch("OpenGL.GL.glPolygonMode")
def test_keyPressEvent_solid_mode(mock_gl_polygon_mode, event_window):
    """Test S key switches to solid fill mode"""
    event = Mock()
    event.key.return_value = Qt.Key_S

    event_window.keyPressEvent(event)

    mock_gl_polygon_mode.assert_called_once()
    assert event_window.update_called is True


def test_keyPressEvent_space_reset(event_window):
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


def test_keyPressEvent_other_key(event_window):
    """Test other keys call parent keyPressEvent"""
    event = Mock()
    event.key.return_value = Qt.Key_A

    # Mock super() call
    with patch("builtins.super") as mock_super:
        mock_parent = Mock()
        mock_super.return_value = mock_parent

        event_window.keyPressEvent(event)

        mock_parent.keyPressEvent.assert_called_once_with(event)


def test_mousePressEvent_left_button(event_window):
    """Test left mouse button press starts rotation"""
    event = Mock()
    event.button.return_value = Qt.LeftButton
    event.position.return_value = QPointF(100, 200)

    event_window.mousePressEvent(event)

    assert event_window.rotate is True
    assert event_window.original_x_rotation == 100
    assert event_window.original_y_rotation == 200


def test_mousePressEvent_right_button(event_window):
    """Test right mouse button press starts translation"""
    event = Mock()
    event.button.return_value = Qt.RightButton
    event.position.return_value = QPointF(150, 250)

    event_window.mousePressEvent(event)

    assert event_window.translate is True
    assert event_window.original_x_pos == 150
    assert event_window.original_y_pos == 250


def test_mouseReleaseEvent_left_button(event_window):
    """Test left mouse button release stops rotation"""
    event_window.rotate = True

    event = Mock()
    event.button.return_value = Qt.LeftButton

    event_window.mouseReleaseEvent(event)

    assert event_window.rotate is False


def test_mouseReleaseEvent_right_button(event_window):
    """Test right mouse button release stops translation"""
    event_window.translate = True

    event = Mock()
    event.button.return_value = Qt.RightButton

    event_window.mouseReleaseEvent(event)

    assert event_window.translate is False


def test_mouseMoveEvent_rotation(event_window):
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


def test_mouseMoveEvent_translation(event_window):
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


def test_mouseMoveEvent_no_action(event_window):
    """Test mouse movement when no buttons active"""
    event_window.rotate = False
    event_window.translate = False

    event = Mock()
    event.buttons.return_value = Qt.NoButton

    event_window.mouseMoveEvent(event)

    # Should not update anything
    assert event_window.update_called is False


def test_wheelEvent_positive_delta(event_window):
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


def test_wheelEvent_negative_delta(event_window):
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


def test_wheelEvent_x_axis_delta(event_window):
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


def test_wheelEvent_zero_delta(event_window):
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


def test_get_camera_state(event_window):
    """Test getting camera state"""
    # Set some values
    event_window.spin_x_face = 45
    event_window.spin_y_face = 90
    event_window.model_position.set(1, 2, 3)
    event_window.rotation_sensitivity = pytest.approx(0.8)
    event_window.translation_sensitivity = pytest.approx(0.02)
    event_window.zoom_sensitivity = pytest.approx(0.15)

    state = event_window.get_camera_state()

    expected = {
        "spin_x_face": 45,
        "spin_y_face": 90,
        "model_position": [pytest.approx(1), pytest.approx(2), pytest.approx(3)],
        "rotation_sensitivity": pytest.approx(0.8),
        "translation_sensitivity": pytest.approx(0.02),
        "zoom_sensitivity": pytest.approx(0.15),
    }

    assert state == expected


def test_set_camera_state(event_window):
    """Test setting camera state from dictionary"""
    state = {
        "spin_x_face": 30,
        "spin_y_face": 60,
        "model_position": [5, 10, 15],
        "rotation_sensitivity": 0.75,
        "translation_sensitivity": 0.05,
        "zoom_sensitivity": 0.25,
    }

    event_window.set_camera_state(state)

    assert event_window.spin_x_face == 30
    assert event_window.spin_y_face == 60
    assert event_window.model_position.x == pytest.approx(5)
    assert event_window.model_position.y == pytest.approx(10)
    assert event_window.model_position.z == pytest.approx(15)
    assert event_window.rotation_sensitivity == pytest.approx(0.75)
    assert event_window.translation_sensitivity == pytest.approx(0.05)
    assert event_window.zoom_sensitivity == pytest.approx(0.25)


def test_set_camera_state_partial(event_window):
    """Test setting camera state with missing values (uses defaults)"""
    state = {
        "spin_x_face": 15,
        "model_position": [2, 4, 6],
    }

    event_window.set_camera_state(state)

    assert event_window.spin_x_face == 15
    assert event_window.spin_y_face == 0  # Default
    assert event_window.model_position.x == pytest.approx(2)
    assert event_window.model_position.y == pytest.approx(4)
    assert event_window.model_position.z == pytest.approx(6)
    assert event_window.rotation_sensitivity == PySideEventHandlingMixin.DEFAULT_ROTATION_SENSITIVITY
    assert event_window.translation_sensitivity == PySideEventHandlingMixin.DEFAULT_TRANSLATION_SENSITIVITY
    assert event_window.zoom_sensitivity == PySideEventHandlingMixin.DEFAULT_ZOOM_SENSITIVITY


def test_set_camera_state_empty_dict(event_window):
    """Test setting camera state with empty dictionary"""
    event_window.set_camera_state({})

    # Should use all defaults
    assert event_window.spin_x_face == 0
    assert event_window.spin_y_face == 0
    assert event_window.model_position.x == pytest.approx(0)
    assert event_window.model_position.y == pytest.approx(0)
    assert event_window.model_position.z == pytest.approx(0)
    assert event_window.rotation_sensitivity == PySideEventHandlingMixin.DEFAULT_ROTATION_SENSITIVITY
    assert event_window.translation_sensitivity == PySideEventHandlingMixin.DEFAULT_TRANSLATION_SENSITIVITY
    assert event_window.zoom_sensitivity == PySideEventHandlingMixin.DEFAULT_ZOOM_SENSITIVITY


def test_camera_state_round_trip(event_window):
    """Test saving and restoring camera state"""
    # Set some values
    event_window.spin_x_face = 25
    event_window.spin_y_face = 50
    event_window.model_position.set(3, 6, 9)
    event_window.rotation_sensitivity = pytest.approx(0.6)
    event_window.translation_sensitivity = pytest.approx(0.03)
    event_window.zoom_sensitivity = pytest.approx(0.12)

    # Save state
    state = event_window.get_camera_state()

    # Change values
    event_window.reset_camera()
    event_window.rotation_sensitivity = pytest.approx(1.0)

    # Restore state
    event_window.set_camera_state(state)

    # Check values are restored
    assert event_window.spin_x_face == 25
    assert event_window.spin_y_face == 50
    assert event_window.model_position.x == pytest.approx(3)
    assert event_window.model_position.y == pytest.approx(6)
    assert event_window.model_position.z == pytest.approx(9)
    assert event_window.rotation_sensitivity == pytest.approx(0.6)
    assert event_window.translation_sensitivity == pytest.approx(0.03)
    assert event_window.zoom_sensitivity == pytest.approx(0.12)


def test_constants():
    """Test default sensitivity constants"""
    assert PySideEventHandlingMixin.DEFAULT_ROTATION_SENSITIVITY == pytest.approx(0.5)
    assert PySideEventHandlingMixin.DEFAULT_TRANSLATION_SENSITIVITY == pytest.approx(0.01)
    assert PySideEventHandlingMixin.DEFAULT_ZOOM_SENSITIVITY == pytest.approx(0.1)


def test_mouse_movement_rotation_with_different_sensitivity():
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


def test_mouse_movement_translation_with_different_sensitivity():
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


def test_event_handling_target_protocol():
    """Test that the protocol is properly defined"""

    # This should not raise any errors
    window = MockEventHandlingWindow()

    # Check that our test class implements the protocol
    assert hasattr(window, "update")
    assert hasattr(window, "close")
    assert callable(window.update)
    assert callable(window.close)


def test_mouseMoveEvent_rotation_without_left_button(event_window):
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


def test_mouseMoveEvent_translation_without_right_button(event_window):
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


def test_mousePressEvent_middle_button(event_window):
    """Test middle mouse button press (should be ignored)"""
    event = Mock()
    event.button.return_value = Qt.MiddleButton
    event.position.return_value = QPointF(100, 200)

    event_window.mousePressEvent(event)

    # Should not change any state
    assert event_window.rotate is False
    assert event_window.translate is False


def test_mouseReleaseEvent_middle_button(event_window):
    """Test middle mouse button release (should be ignored)"""
    event_window.rotate = True
    event_window.translate = True

    event = Mock()
    event.button.return_value = Qt.MiddleButton

    event_window.mouseReleaseEvent(event)

    # Should not change state
    assert event_window.rotate is True
    assert event_window.translate is True


def test_setup_event_handling_with_none_position():
    """Test setup_event_handling with None initial position"""
    window = MockEventHandlingWindow()
    window.setup_event_handling(initial_position=None)

    assert window.model_position.x == 0
    assert window.model_position.y == 0
    assert window.model_position.z == 0


def test_wheelEvent_priority_y_over_x(event_window):
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
    assert event_window.model_position.z == initial_z + 0.5
    assert event_window.update_called is True


def test_set_camera_state_partial_model_position():
    """Test set_camera_state with partial model position data"""
    window = MockEventHandlingWindow()
    window.setup_event_handling()

    state = {
        "spin_x_face": 25,
        "model_position": [7, 8],  # Only 2 values instead of 3
    }

    # This should handle the IndexError gracefully
    window.set_camera_state(state)

    assert window.spin_x_face == 25
    assert window.model_position.x == pytest.approx(7)
    assert window.model_position.y == pytest.approx(8)
    # z should remain default
    assert window.model_position.z == pytest.approx(0)


def test_set_camera_state_empty_model_position():
    """Test set_camera_state with empty model position list"""
    window = MockEventHandlingWindow()
    window.setup_event_handling()

    state = {
        "model_position": [],  # Empty list
    }

    # This should handle gracefully and use defaults
    window.set_camera_state(state)

    assert window.model_position.x == pytest.approx(0)
    assert window.model_position.y == pytest.approx(0)
    assert window.model_position.z == pytest.approx(0)
