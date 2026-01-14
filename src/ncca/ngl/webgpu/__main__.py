#!/usr/bin/env -S uv run --active --script
import sys
import time

import numpy as np
import wgpu
import wgpu.utils
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication
from wgpu.utils import get_default_device

from ncca.ngl import Mat4, PerspMode, Vec3, look_at, perspective
from ncca.ngl.webgpu import PipelineFactory, PipelineType, WebGPUWidget, __version__

NUM_POINTS = 10000


class WebGPUScene(WebGPUWidget):
    """
    A concrete implementation of NumpyBufferWidget for a WebGPU scene.

    This class implements the abstract methods to provide functionality for initializing,
    painting, and resizing the WebGPU context.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("WebGPU Points")
        self.device = None
        self.pipeline = None
        self.vertex_buffer = None
        self.msaa_sample_count = 4
        self.rotation = 0.0
        self.view = look_at(Vec3(0, 2, 14), Vec3(0, 0, 0), Vec3(0, 1, 0))
        self.animate = True
        self.project = Mat4()
        self._initialize_web_gpu()
        self.update()

    def _initialize_web_gpu(self) -> None:
        """
        Initialize the WebGPU context.

        This method sets up the WebGPU context for the scene.
        """
        print("initializeWebGPU")
        try:
            self.device = get_default_device()
        except Exception as e:
            print(f"Failed to initialize WebGPU: {e}")
            return
        self._create_buffers(NUM_POINTS)

        self.pipelines = []
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.MULTI_COLOURED_POINTS
                ),
                self._render_multi_colour_point_pipeline,
                "PipelineType.MULTI_COLOURED_POINTS",
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.SINGLE_COLOUR_POINTS
                ),
                self._render_single_colour_point_pipeline,
                "PipelineType.SINGLE_COLOUR_POINTS",
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.MULTI_COLOURED_LINES
                ),
                self._render_multi_colour_line_pipeline,
                "PipelineType.MULTI_COLOURED_LINES",
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.SINGLE_COLOUR_LINES
                ),
                self._render_single_colour_line_pipeline,
                "PipelineType.SINGLE_COLOUR_LINES",
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.MULTI_COLOURED_TRIANGLES
                ),
                self._render_multi_colour_triangle_pipeline,
                "PipelineType.MULTI_COLOURED_TRIANGLES",
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.SINGLE_COLOUR_TRIANGLES
                ),
                self._render_single_colour_triangle_pipeline,
                "PipelineType.SINGLE_COLOUR_TRIANGLES",
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.TRIANGLE_LIST_MULTI_COLOURED
                ),
                self._render_triangle_list_multi_colour_pipeline,
                "PipelineType.TRIANGLE_LIST_MULTI_COLOURED",
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.TRIANGLE_LIST_SINGLE_COLOUR
                ),
                self._render_triangle_list_single_colour_pipeline,
                "PipelineType.TRIANGLE_LIST_SINGLE_COLOUR",
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.TRIANGLE_STRIP_MULTI_COLOURED
                ),
                self._render_triangle_strip_multi_colour_pipeline,
                "PipelineType.TRIANGLE_STRIP_MULTI_COLOURED",
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.TRIANGLE_STRIP_SINGLE_COLOUR
                ),
                self._render_triangle_strip_single_colour_pipeline,
                "PipelineType.TRIANGLE_STRIP_SINGLE_COLOUR",
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.POINT_LIST_MULTI_COLOURED
                ),
                self._render_point_list_multi_colour_pipeline,
                "PipelineType.POINT_LIST_MULTI_COLOURED",
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.POINT_LIST_SINGLE_COLOUR
                ),
                self._render_point_list_single_colour_pipeline,
                "PipelineType.POINT_LIST_SINGLE_COLOUR",
            )
        )
        self.current_pipeline_index = 1
        # Initialize render textures with default size
        self.texture_size = (1024, 720)
        self._create_render_buffer()

        # Setup timers
        self.startTimer(16)  # Animation timer (~60 FPS)
        self.pipeline_timer = QTimer()
        self.pipeline_timer.timeout.connect(self.switch_pipeline)
        self.pipeline_timer.start(1000)  # Switch every 5 seconds

    def _create_buffers(self, num_points):
        rng = np.random.default_rng(int(time.time()))
        self.colours = rng.random((num_points, 3)).astype(np.float32)
        # Create 3D positions for line rendering with Z elevation
        self.positions = rng.uniform(-4.0, 4.0, size=(num_points, 3)).astype(np.float32)
        # For line rendering, we can use the full 3D positions or just X,Y depending on desired effect
        self.positions_2d = self.positions[
            :, :2
        ]  # Take only X,Y components for 2D line effects

        # Create triangle data for triangle list
        num_triangles = 100
        self.triangle_positions = np.zeros((num_triangles * 3, 3), dtype=np.float32)
        self.triangle_colours = rng.random((num_triangles * 3, 3)).astype(np.float32)

        for i in range(num_triangles):
            # Create a triangle around a random center point in 3D space
            center = rng.uniform(-3.0, 3.0, 3)
            radius = rng.uniform(0.2, 0.8)

            # Generate random triangle vertices in 3D using spherical coordinates
            # First vertex
            theta1 = rng.uniform(0, 2 * np.pi)  # azimuth
            phi1 = rng.uniform(0, np.pi)  # polar
            vertex1 = radius * np.array(
                [
                    np.sin(phi1) * np.cos(theta1),
                    np.sin(phi1) * np.sin(theta1),
                    np.cos(phi1),
                ]
            )

            # Second vertex (different orientation)
            theta2 = theta1 + rng.uniform(2.0, 3.0)
            phi2 = rng.uniform(0, np.pi)
            vertex2 = radius * np.array(
                [
                    np.sin(phi2) * np.cos(theta2),
                    np.sin(phi2) * np.sin(theta2),
                    np.cos(phi2),
                ]
            )

            # Third vertex (completes the triangle)
            theta3 = theta2 + rng.uniform(2.0, 3.0)
            phi3 = rng.uniform(0, np.pi)
            vertex3 = radius * np.array(
                [
                    np.sin(phi3) * np.cos(theta3),
                    np.sin(phi3) * np.sin(theta3),
                    np.cos(phi3),
                ]
            )

            self.triangle_positions[i * 3] = center + vertex1
            self.triangle_positions[i * 3 + 1] = center + vertex2
            self.triangle_positions[i * 3 + 2] = center + vertex3

        # Create triangle strip data with 3D helix/spring pattern
        strip_length = 50
        self.triangle_strip_positions = np.zeros((strip_length, 3), dtype=np.float32)
        self.triangle_strip_colours = rng.random((strip_length, 3)).astype(np.float32)

        for i in range(strip_length):
            t = i / (strip_length - 1)
            # Create a 3D helix/spring pattern for triangle strip
            angle = t * 4 * np.pi  # Multiple rotations
            radius = 2.0 + 0.5 * np.sin(angle * 2)  # Varying radius

            # Alternate between upper and lower points of the strip
            if i % 2 == 0:
                # Upper points
                self.triangle_strip_positions[i] = [
                    radius * np.cos(angle),  # X
                    radius * np.sin(angle) + 1.0,  # Y (offset up)
                    -2 + t * 4,  # Z (forward progression)
                ]
            else:
                # Lower points
                self.triangle_strip_positions[i] = [
                    radius * np.cos(angle),  # X
                    radius * np.sin(angle) - 1.0,  # Y (offset down)
                    -2 + t * 4,  # Z (forward progression)
                ]

    def _create_render_buffer(self):
        """Delegate to parent class method."""
        super()._create_render_buffer()

    def paintWebGPU(self) -> None:
        """
        Paint the WebGPU content.

        This method renders the WebGPU content for the scene.
        """
        self.render_text(
            10,
            20,
            f"{self.pipelines[self.current_pipeline_index][2]}",
            size=20,
            colour=QColor(255, 255, 0),  # Yellow
        )
        try:
            # Create a new command encoder for the render pass
            command_encoder = self.device.create_command_encoder()
            render_pass = command_encoder.begin_render_pass(
                color_attachments=[
                    {
                        "view": self.multisample_texture_view,
                        "resolve_target": self.colour_buffer_texture_view,
                        "load_op": wgpu.LoadOp.clear,
                        "store_op": wgpu.StoreOp.store,
                        "clear_value": (0.4, 0.4, 0.4, 1.0),
                    }
                ],
                depth_stencil_attachment={
                    "view": self.depth_buffer_view,
                    "depth_load_op": wgpu.LoadOp.clear,
                    "depth_store_op": wgpu.StoreOp.store,
                    "depth_clear_value": 1.0,
                },
            )
            self.update_uniform_buffers()
            render_pass.set_viewport(
                0, 0, self.texture_size[0], self.texture_size[1], 0, 1
            )
            self.pipelines[self.current_pipeline_index][1](render_pass)
            render_pass.end()
            self.device.queue.submit([command_encoder.finish()])
        except Exception as e:
            print(f"Failed to paint WebGPU content: {e}")

    def resizeWebGPU(self, w, h) -> None:
        """
        Called whenever the window is resized.
        It's crucial to update the viewport and projection matrix here.

        Args:
            w: The new width of the window.
            h: The new height of the window.
        """

        # Update texture size to match window dimensions
        self.texture_size = (w, h)

        # Update projection matrix
        self.project = perspective(
            45.0, w / h if h > 0 else 1, 0.1, 100.0, PerspMode.WebGPU
        )

        self.update()

    def _render_pipeline(
        self, render_pass, positions, colours=None, point_size=None, colour=None
    ):
        """Generic pipeline rendering method to eliminate code duplication."""
        pipeline = self.pipelines[self.current_pipeline_index][0]

        # Set data based on whether we have colours
        if colours is not None:
            pipeline.set_data(positions, colours)
        else:
            pipeline.set_data(positions)

        pipeline.render(render_pass)

        # Update uniforms based on what's provided
        if point_size is not None:
            if colours is not None:
                pipeline.update_uniforms(
                    mvp=self.mvp_matrix,
                    view_matrix=self.view_matrix,
                    point_size=point_size,
                )
            else:
                pipeline.update_uniforms(
                    mvp=self.mvp_matrix,
                    view_matrix=self.view_matrix,
                    colour=np.array([1, 1, 1], dtype=np.float32),
                    point_size=point_size,
                )
        else:
            pipeline.update_uniforms(mvp=self.mvp_matrix)

    def _render_multi_colour_point_pipeline(self, render_pass):
        self._render_pipeline(
            render_pass, self.positions, colours=self.colours, point_size=0.05
        )

    def _render_single_colour_point_pipeline(self, render_pass):
        self._render_pipeline(render_pass, self.positions, point_size=0.05)

    def _render_multi_colour_line_pipeline(self, render_pass):
        self._render_pipeline(render_pass, self.positions_2d, colours=self.colours)

    def _render_single_colour_line_pipeline(self, render_pass):
        self._render_pipeline(render_pass, self.positions_2d)

    def _render_multi_colour_triangle_pipeline(self, render_pass):
        self._render_pipeline(
            render_pass, self.triangle_positions, colours=self.triangle_colours
        )

    def _render_single_colour_triangle_pipeline(self, render_pass):
        self._render_pipeline(render_pass, self.triangle_positions)

    def _render_triangle_list_multi_colour_pipeline(self, render_pass):
        self._render_pipeline(
            render_pass, self.triangle_positions, colours=self.triangle_colours
        )

    def _render_triangle_list_single_colour_pipeline(self, render_pass):
        self._render_pipeline(render_pass, self.triangle_positions)

    def _render_triangle_strip_multi_colour_pipeline(self, render_pass):
        self._render_pipeline(
            render_pass,
            self.triangle_strip_positions,
            colours=self.triangle_strip_colours,
        )

    def _render_triangle_strip_single_colour_pipeline(self, render_pass):
        self._render_pipeline(render_pass, self.triangle_strip_positions)

    def _render_point_list_multi_colour_pipeline(self, render_pass):
        self._render_pipeline(
            render_pass, self.positions, colours=self.colours, point_size=5.0
        )

    def _render_point_list_single_colour_pipeline(self, render_pass):
        self._render_pipeline(render_pass, self.positions, point_size=5.0)

    def update_uniform_buffers(self) -> None:
        """
        update the uniform buffers for the line pipeline.
        """
        rotation = Mat4.rotate_y(self.rotation)
        self.mvp_matrix = (
            (self.project @ self.view @ rotation).to_numpy().astype(np.float32)
        )
        self.view_matrix = (self.view @ rotation).to_numpy().astype(np.float32)

    def keyPressEvent(self, event) -> None:
        """
        Handles keyboard press events.

        Args:
            event: The QKeyEvent object containing information about the key press.
        """
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.close()  # Exit the application
        elif key == Qt.Key.Key_Space:
            self.animate = not self.animate
        self.update()

        # Call the base class implementation for any unhandled events
        super().keyPressEvent(event)

    def switch_pipeline(self) -> None:
        """Switch to the next pipeline in the list."""
        self.current_pipeline_index = (self.current_pipeline_index + 1) % len(
            self.pipelines
        )
        print(f"Switched to {self.pipelines[self.current_pipeline_index][2]}")
        self.update()

    def timerEvent(self, event) -> None:
        """
        Handle timer events to update the scene.
        """
        if self.animate:
            self.rotation += 0.5
        self.update()


def main():
    """
    Main function to run the application.
    Parses command line arguments and initializes the WebGPUScene.
    """
    app = QApplication(sys.argv)
    win = WebGPUScene()
    win.resize(1024, 720)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    print(f"ncca-ngl.WebGPU {__version__}")
    main()
