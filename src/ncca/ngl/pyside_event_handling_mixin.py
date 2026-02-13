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

import OpenGL.GL as gl
from PySide6.QtCore import Qt

from .vec3 import Vec3


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

    def reset_camera(self) -> None:
        """Reset camera rotation and model position to defaults."""
        self.spin_x_face = 0
        self.spin_y_face = 0
        self.model_position.set(0, 0, 0)

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

            self.update()

        # Handle translation with right mouse button
        elif self.translate and event.buttons() == Qt.RightButton:
            diff_x = int(position.x() - self.original_x_pos)
            diff_y = int(position.y() - self.original_y_pos)

            self.original_x_pos = position.x()
            self.original_y_pos = position.y()

            self.model_position.x += self.translation_sensitivity * diff_x
            self.model_position.y -= self.translation_sensitivity * diff_y

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

        elif event.button() == Qt.RightButton:
            self.original_x_pos = position.x()
            self.original_y_pos = position.y()
            self.translate = True

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

        self.update()
