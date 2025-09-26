#!/usr/bin/env python3
"""
Event Handling Mixin for PyNGL Applications

This module provides a reusable mixin class that implements common event handling
patterns used across PyNGL applications, including mouse-based camera control,
keyboard shortcuts, and wheel-based zooming.

Usage:
    class MyWindow(EventHandlingMixin, QOpenGLWindow):
        def __init__(self):
            super().__init__()
            self.setup_event_handling()  # Initialize mixin attributes
            # ... rest of your initialization
"""

from typing import Protocol

import OpenGL.GL as gl
from PySide6.QtCore import Qt

from .vec3 import Vec3


class EventHandlingTarget(Protocol):
    """
    Protocol defining the interface that classes using EventHandlingMixin must implement.

    This ensures that the mixin has access to the necessary methods and attributes.
    """

    def update(self) -> None:
        """Trigger a redraw of the window."""
        ...

    def close(self) -> None:
        """Close the window."""
        ...


class PySideEventHandlingMixin:
    """
    Mixin class providing standard event handling for PyNGL applications.

    This mixin provides common functionality for:
    - Mouse-based camera control (rotation with left button, translation with right button)
    - Keyboard shortcuts (wireframe/solid mode, reset, escape)
    - Mouse wheel zooming

    Classes using this mixin should call setup_event_handling() in their __init__ method.
    """

    # Default sensitivity values
    DEFAULT_ROTATION_SENSITIVITY = 0.5
    DEFAULT_TRANSLATION_SENSITIVITY = 0.01
    DEFAULT_ZOOM_SENSITIVITY = 0.1

    def setup_event_handling(
        self,
        rotation_sensitivity: float = DEFAULT_ROTATION_SENSITIVITY,
        translation_sensitivity: float = DEFAULT_TRANSLATION_SENSITIVITY,
        zoom_sensitivity: float = DEFAULT_ZOOM_SENSITIVITY,
        initial_position: Vec3 = None,
    ) -> None:
        """
        Initialize event handling attributes.

        Args:
            rotation_sensitivity: Mouse sensitivity for rotation (default: 0.5)
            translation_sensitivity: Mouse sensitivity for translation (default: 0.01)
            zoom_sensitivity: Mouse wheel sensitivity for zooming (default: 0.1)
            initial_position: Initial model position (default: Vec3(0,0,0))
        """
        # Mouse control state
        self.rotate: bool = False
        self.translate: bool = False

        # Rotation state
        self.spin_x_face: int = 0
        self.spin_y_face: int = 0

        # Mouse position tracking for rotation
        self.original_x_rotation: float = 0.0
        self.original_y_rotation: float = 0.0

        # Mouse position tracking for translation
        self.original_x_pos: float = 0.0
        self.original_y_pos: float = 0.0

        # Model position and sensitivity settings
        self.model_position: Vec3 = initial_position or Vec3(0, 0, 0)
        self.rotation_sensitivity: float = rotation_sensitivity
        self.translation_sensitivity: float = translation_sensitivity
        self.zoom_sensitivity: float = zoom_sensitivity

        self.INCREMENT = self.translation_sensitivity
        self.ZOOM = self.zoom_sensitivity

    # def sync_legacy_attributes(self) -> None:
    #     """
    #     Synchronize legacy attribute names with new ones.
    #     Call this if you modify the legacy attributes directly.
    #     """
    #     self.spin_x_face = self.spinXFace
    #     self.spin_y_face = self.spinYFace
    #     self.model_position = self.modelPos
    #     self.original_x_rotation = self.origX
    #     self.original_y_rotation = self.origY
    #     self.original_x_pos = self.origXPos
    #     self.original_y_pos = self.origYPos
    #     self.translation_sensitivity = self.INCREMENT
    #     self.zoom_sensitivity = self.ZOOM

    def reset_camera(self) -> None:
        """Reset camera rotation and model position to defaults."""
        self.spin_x_face = 0
        self.spin_y_face = 0
        self.model_position.set(0, 0, 0)

        # # Sync legacy attributes
        # self.spinXFace = 0
        # self.spinYFace = 0
        # self.modelPos.set(0, 0, 0)

    def keyPressEvent(self, event) -> None:
        """
        Handle keyboard press events with common shortcuts.

        Shortcuts:
        - Escape: Close application
        - W: Switch to wireframe mode
        - S: Switch to solid fill mode
        - Space: Reset camera rotation and position

        Args:
            event: The QKeyEvent object
        """
        key = event.key()

        if key == Qt.Key_Escape:
            self.close()
        elif key == Qt.Key_W:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
        elif key == Qt.Key_S:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
        elif key == Qt.Key_Space:
            self.reset_camera()
        else:
            # Let subclasses handle other keys
            super().keyPressEvent(event)
            return

        self.update()

    def mouseMoveEvent(self, event) -> None:
        """
        Handle mouse movement for camera control.

        - Left button: Rotate the scene
        - Right button: Translate (pan) the scene

        Args:
            event: The QMouseEvent object
        """
        position = event.position()

        # Handle rotation with left mouse button
        if self.rotate and event.buttons() == Qt.LeftButton:
            diff_x = position.x() - self.original_x_rotation
            diff_y = position.y() - self.original_y_rotation

            self.spin_x_face += int(self.rotation_sensitivity * diff_y)
            self.spin_y_face += int(self.rotation_sensitivity * diff_x)

            self.original_x_rotation = position.x()
            self.original_y_rotation = position.y()

            # # Sync legacy attributes
            # self.spinXFace = self.spin_x_face
            # self.spinYFace = self.spin_y_face
            # self.origX = self.original_x_rotation
            # self.origY = self.original_y_rotation

            self.update()

        # Handle translation with right mouse button
        elif self.translate and event.buttons() == Qt.RightButton:
            diff_x = int(position.x() - self.original_x_pos)
            diff_y = int(position.y() - self.original_y_pos)

            self.original_x_pos = position.x()
            self.original_y_pos = position.y()

            self.model_position.x += self.translation_sensitivity * diff_x
            self.model_position.y -= self.translation_sensitivity * diff_y

            # # Sync legacy attributes
            # self.origXPos = self.original_x_pos
            # self.origYPos = self.original_y_pos
            # self.modelPos = self.model_position

            self.update()

    def mousePressEvent(self, event) -> None:
        """
        Handle mouse button press events to initiate rotation or translation.

        - Left button: Start rotation mode
        - Right button: Start translation mode

        Args:
            event: The QMouseEvent object
        """
        position = event.position()

        if event.button() == Qt.LeftButton:
            self.original_x_rotation = position.x()
            self.original_y_rotation = position.y()
            self.rotate = True

            # # Sync legacy attributes
            # self.origX = self.original_x_rotation
            # self.origY = self.original_y_rotation

        elif event.button() == Qt.RightButton:
            self.original_x_pos = position.x()
            self.original_y_pos = position.y()
            self.translate = True

            # # Sync legacy attributes
            # self.origXPos = self.original_x_pos
            # self.origYPos = self.original_y_pos

    def mouseReleaseEvent(self, event) -> None:
        """
        Handle mouse button release events to stop rotation or translation.

        Args:
            event: The QMouseEvent object
        """
        if event.button() == Qt.LeftButton:
            self.rotate = False
        elif event.button() == Qt.RightButton:
            self.translate = False

    def wheelEvent(self, event) -> None:
        """
        Handle mouse wheel events for zooming.

        Zooming is performed by adjusting the Z coordinate of the model position.

        Args:
            event: The QWheelEvent object
        """
        angle_delta = event.angleDelta()

        # Handle both x and y wheel movement (some mice/trackpads use different axes)
        delta = angle_delta.y() if angle_delta.y() != 0 else angle_delta.x()

        if delta > 0:
            self.model_position.z += self.zoom_sensitivity
        elif delta < 0:
            self.model_position.z -= self.zoom_sensitivity

        # # Sync legacy attributes
        # self.modelPos = self.model_position

        self.update()

    def get_camera_state(self) -> dict:
        """
        Get the current camera state for serialization or debugging.

        Returns:
            Dictionary containing current camera state
        """
        return {
            "spin_x_face": self.spin_x_face,
            "spin_y_face": self.spin_y_face,
            "model_position": [
                self.model_position.x,
                self.model_position.y,
                self.model_position.z,
            ],
            "rotation_sensitivity": self.rotation_sensitivity,
            "translation_sensitivity": self.translation_sensitivity,
            "zoom_sensitivity": self.zoom_sensitivity,
        }

    def set_camera_state(self, state: dict) -> None:
        """
        Restore camera state from a dictionary.

        Args:
            state: Dictionary containing camera state (from get_camera_state())
        """
        self.spin_x_face = state.get("spin_x_face", 0)
        self.spin_y_face = state.get("spin_y_face", 0)

        pos = state.get("model_position", [0, 0, 0])
        # Handle cases where pos might have fewer than 3 elements
        x = pos[0] if len(pos) > 0 else 0
        y = pos[1] if len(pos) > 1 else 0
        z = pos[2] if len(pos) > 2 else 0
        self.model_position.set(x, y, z)

        self.rotation_sensitivity = state.get(
            "rotation_sensitivity", self.DEFAULT_ROTATION_SENSITIVITY
        )
        self.translation_sensitivity = state.get(
            "translation_sensitivity", self.DEFAULT_TRANSLATION_SENSITIVITY
        )
        self.zoom_sensitivity = state.get(
            "zoom_sensitivity", self.DEFAULT_ZOOM_SENSITIVITY
        )

        # # Sync legacy attributes
        # self.sync_legacy_attributes()
