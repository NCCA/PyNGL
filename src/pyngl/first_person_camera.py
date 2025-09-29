import math

from .mat4 import Mat4
from .util import perspective
from .vec3 import Vec3


class FirstPersonCamera:
    """
    A class representing a first-person camera.

    This class provides functionality for a first-person camera, including movement,
    rotation, and projection matrix calculation.

    Attributes:
        eye (Vec3): The position of the camera.
        look (Vec3): The point the camera is looking at.
        world_up (Vec3): The world's up vector.
        front (Vec3): The front direction vector of the camera.
        up (Vec3): The up direction vector of the camera.
        right (Vec3): The right direction vector of the camera.
        yaw (float): The yaw angle of the camera.
        pitch (float): The pitch angle of the camera.
        speed (float): The movement speed of the camera.
        sensitivity (float): The mouse sensitivity.
        zoom (float): The zoom level of the camera.
        near (float): The near clipping plane.
        far (float): The far clipping plane.
        aspect (float): The aspect ratio.
        fov (float): The field of view.
        projection (Mat4): The projection matrix.
        view (Mat4): The view matrix.
    """

    def __init__(self, eye: Vec3, look: Vec3, up: Vec3, fov: float) -> None:
        """
        Initialize the FirstPersonCamera.

        Args:
            eye (Vec3): The position of the camera.
            look (Vec3): The point the camera is looking at.
            up (Vec3): The world's up vector.
            fov (float): The field of view.
        """
        self.eye: Vec3 = eye
        self.look: Vec3 = look
        self.world_up: Vec3 = up
        self.front: Vec3 = Vec3()
        self.up: Vec3 = Vec3()
        self.right: Vec3 = Vec3()
        self.yaw: float = -90.0
        self.pitch: float = 0.0
        self.speed: float = 2.5
        self.sensitivity: float = 0.1
        self.zoom: float = 45.0
        self.near: float = 0.1
        self.far: float = 100.0
        self.aspect: float = 1.2
        self.fov: float = fov
        self._update_camera_vectors()
        self.projection: Mat4 = self.set_projection(
            self.fov, self.aspect, self.near, self.far
        )
        from .util import look_at

        self.view: Mat4 = look_at(self.eye, self.eye + self.front, self.up)

    def __str__(self) -> str:
        return f"Camera {self.eye} {self.look} {self.world_up} {self.fov}"

    def __repr__(self) -> str:
        return f"Camera {self.eye} {self.look} {self.world_up} {self.fov}"

    def process_mouse_movement(
        self, diffx: float, diffy: float, _constrain_pitch: bool = True
    ) -> None:
        """
        Process mouse movement to update the camera's direction vectors.

        Args:
            diffx (float): The difference in the x-coordinate of the mouse movement.
            diffy (float): The difference in the y-coordinate of the mouse movement.
            _constrain_pitch (bool, optional): Whether to constrain the pitch angle. Defaults to True.
        """
        diffx *= self.sensitivity
        diffy *= self.sensitivity

        self.yaw += diffx
        self.pitch += diffy

        # Make sure that when pitch is out of bounds, screen doesn't get flipped
        if _constrain_pitch:
            if self.pitch > 89.0:
                self.pitch = 89.0
            if self.pitch < -89.0:
                self.pitch = -89.0

        self._update_camera_vectors()

    def _update_camera_vectors(self) -> None:
        """
        Update the camera's direction vectors based on the current yaw and pitch angles.
        """
        pitch = math.radians(self.pitch)
        yaw = math.radians(self.yaw)
        self.front.x = math.cos(yaw) * math.cos(pitch)
        self.front.y = math.sin(pitch)
        self.front.z = math.sin(yaw) * math.cos(pitch)
        self.front.normalize()
        # Also re-calculate the Right and Up vector
        self.right = self.front.cross(self.world_up)
        self.up = self.right.cross(self.front)
        # normalize as fast movement can cause issues
        self.right.normalize()
        self.front.normalize()
        from .util import look_at

        self.view = look_at(self.eye, self.eye + self.front, self.up)

    def set_projection(
        self, fov: float, aspect: float, near: float, far: float
    ) -> Mat4:
        """
        Set the projection matrix for the camera.

        Args:
            fov (float): The field of view.
            aspect (float): The aspect ratio.
            near (float): The near clipping plane.
            far (float): The far clipping plane.

        Returns:
            Mat4: The projection matrix.
        """

        return perspective(fov, aspect, near, far)

    def move(self, x: float, y: float, delta: float) -> None:
        """
        Move the camera based on input directions.

        Args:
            x (float): The movement in the x-direction.
            y (float): The movement in the y-direction.
            delta (float): The amount to move the camera.
        """
        velocity = self.speed * delta
        self.eye += self.front * velocity * x
        self.eye += self.right * velocity * y
        self._update_camera_vectors()

    def get_vp(self) -> Mat4:
        """
        Get the view-projection matrix.

        Returns:
            Mat4: The view-projection matrix.
        """
        return self.projection @ self.view

    def process_mouse_scroll(self, y_offset: float) -> None:
        """
        Process mouse scroll events.

        Args:
            _yoffset (float): The scroll offset.
        """
        if self.zoom >= 1.0 and self.zoom <= 45.0:
            self.zoom -= y_offset
        if self.zoom <= 1.0:
            self.zoom = 1.0
        if self.zoom >= 45.0:
            self.zoom = 45.0
        self.projection = perspective(self.zoom, self.aspect, self.near, self.far)
