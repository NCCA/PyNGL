#!/usr/bin/env -S uv run --active --script
import sys
import time
from typing import Tuple

import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication
from wgpu.utils import get_default_device

from ncca.ngl import Mat4, PerspMode, PrimData, Vec3, look_at, perspective
from ncca.ngl.webgpu import PipelineFactory, PipelineType, WebGPUWidget, __version__

NUM_POINTS = 10000


class WebGPUScene(WebGPUWidget):
    """
    A concrete implementation of NumpyBufferWidget for a WebGPU scene.

    This class implements the abstract methods to provide functionality for initializing,
    painting, and resizing the WebGPU context.
    """

    def __init__(
        self,
        background_colour: Tuple[float, float, float, float] = (0.4, 0.4, 0.4, 1.0),
    ):
        super().__init__(background_colour=background_colour)
        self.setWindowTitle("WebGPU Pipeline Demo - Dynamic Background Colors")
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
        self.pipeline_backgrounds = {}  # Store background colors for each pipeline

        # Define subtle background colors for each pipeline type
        pipeline_colors = {
            "MULTI_COLOURED_POINTS": (0.1, 0.1, 0.3, 1.0),  # Dark blue
            "SINGLE_COLOUR_POINTS": (0.3, 0.1, 0.1, 1.0),  # Dark red
            "MULTI_COLOURED_LINES": (0.1, 0.3, 0.1, 1.0),  # Dark green
            "SINGLE_COLOUR_LINES": (0.3, 0.3, 0.1, 1.0),  # Dark yellow
            "MULTI_COLOURED_TRIANGLES": (0.3, 0.1, 0.3, 1.0),  # Dark magenta
            "SINGLE_COLOUR_TRIANGLES": (0.1, 0.3, 0.3, 1.0),  # Dark cyan
            "TRIANGLE_LIST_MULTI_COLOURED": (0.2, 0.1, 0.4, 1.0),  # Dark purple
            "TRIANGLE_LIST_SINGLE_COLOUR": (0.4, 0.2, 0.1, 1.0),  # Dark orange
            "TRIANGLE_STRIP_MULTI_COLOURED": (0.1, 0.4, 0.2, 1.0),  # Dark teal
            "TRIANGLE_STRIP_SINGLE_COLOUR": (0.2, 0.2, 0.2, 1.0),  # Dark gray
            "POINT_LIST_MULTI_COLOURED": (0.4, 0.1, 0.2, 1.0),  # Dark pink
            "POINT_LIST_SINGLE_COLOUR": (0.1, 0.2, 0.4, 1.0),  # Dark indigo
            "MULTI_COLOURED_INSTANCED_GEOMETRY": (0.3, 0.15, 0.05, 1.0),  # Dark gold
            "SINGLE_COLOUR_INSTANCED_GEOMETRY": (0.05, 0.15, 0.3, 1.0),  # Dark navy
        }

        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.MULTI_COLOURED_POINTS
                ),
                self._render_multi_colour_point_pipeline,
                "PipelineType.MULTI_COLOURED_POINTS",
                pipeline_colors["MULTI_COLOURED_POINTS"],
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.SINGLE_COLOUR_POINTS
                ),
                self._render_single_colour_point_pipeline,
                "PipelineType.SINGLE_COLOUR_POINTS",
                pipeline_colors["SINGLE_COLOUR_POINTS"],
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.MULTI_COLOURED_LINES
                ),
                self._render_multi_colour_line_pipeline,
                "PipelineType.MULTI_COLOURED_LINES",
                pipeline_colors["MULTI_COLOURED_LINES"],
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.SINGLE_COLOUR_LINES
                ),
                self._render_single_colour_line_pipeline,
                "PipelineType.SINGLE_COLOUR_LINES",
                pipeline_colors["SINGLE_COLOUR_LINES"],
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.MULTI_COLOURED_TRIANGLES
                ),
                self._render_multi_colour_triangle_pipeline,
                "PipelineType.MULTI_COLOURED_TRIANGLES",
                pipeline_colors["MULTI_COLOURED_TRIANGLES"],
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.SINGLE_COLOUR_TRIANGLES
                ),
                self._render_single_colour_triangle_pipeline,
                "PipelineType.SINGLE_COLOUR_TRIANGLES",
                pipeline_colors["SINGLE_COLOUR_TRIANGLES"],
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.TRIANGLE_LIST_MULTI_COLOURED
                ),
                self._render_multi_colour_triangle_pipeline,
                "PipelineType.TRIANGLE_LIST_MULTI_COLOURED",
                pipeline_colors["TRIANGLE_LIST_MULTI_COLOURED"],
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.TRIANGLE_LIST_SINGLE_COLOUR
                ),
                self._render_triangle_list_single_colour_pipeline,
                "PipelineType.TRIANGLE_LIST_SINGLE_COLOUR",
                pipeline_colors["TRIANGLE_LIST_SINGLE_COLOUR"],
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.TRIANGLE_STRIP_MULTI_COLOURED
                ),
                self._render_triangle_strip_multi_colour_pipeline,
                "PipelineType.TRIANGLE_STRIP_MULTI_COLOURED",
                pipeline_colors["TRIANGLE_STRIP_MULTI_COLOURED"],
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.TRIANGLE_STRIP_SINGLE_COLOUR
                ),
                self._render_triangle_strip_single_colour_pipeline,
                "PipelineType.TRIANGLE_STRIP_SINGLE_COLOUR",
                pipeline_colors["TRIANGLE_STRIP_SINGLE_COLOUR"],
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.POINT_LIST_MULTI_COLOURED
                ),
                self._render_point_list_multi_colour_pipeline,
                "PipelineType.POINT_LIST_MULTI_COLOURED",
                pipeline_colors["POINT_LIST_MULTI_COLOURED"],
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.POINT_LIST_SINGLE_COLOUR
                ),
                self._render_point_list_single_colour_pipeline,
                "PipelineType.POINT_LIST_SINGLE_COLOUR",
                pipeline_colors["POINT_LIST_SINGLE_COLOUR"],
            )
        )

        # Add instanced geometry pipelines
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.MULTI_COLOURED_INSTANCED_GEOMETRY
                ),
                self._render_multi_colour_instanced_geometry_pipeline,
                "PipelineType.MULTI_COLOURED_INSTANCED_GEOMETRY",
                pipeline_colors["MULTI_COLOURED_INSTANCED_GEOMETRY"],
            )
        )
        self.pipelines.append(
            (
                PipelineFactory.create_pipeline(
                    self.device, PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY
                ),
                self._render_single_colour_instanced_geometry_pipeline,
                "PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY",
                pipeline_colors["SINGLE_COLOUR_INSTANCED_GEOMETRY"],
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

            # Alternate between upper and lower points of strip
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

        # Create instanced geometry data
        self._create_instanced_geometry_data(rng)

    def _create_instanced_geometry_data(self, rng):
        """Create data for instanced geometry rendering."""
        # Create geometry using PrimData (in correct interleaved format)
        # geometry_data = PrimData.sphere(0.25, 16)  # Small sphere with good detail
        # geometry_data = PrimData.cylinder(0.25, 1, 40, 40)  # Small cylinder with good detail
        # geometry_data = PrimData.cone(0.25, 1, 20, 10)  # Small cone with good detail
        geometry_data = PrimData.primitive("teapot")

        # Ensure data is in (num_vertices, 8) format for new API
        if geometry_data.ndim == 1:
            geometry_data = geometry_data.reshape(-1, 8)
        elif geometry_data.shape[1] != 8:
            raise ValueError(
                f"Expected 8 components per vertex, got {geometry_data.shape[1]}"
            )

        # Store the complete interleaved geometry data (x,y,z,nx,ny,nz,u,v)
        self.geometry_data = geometry_data

        # Create instance positions (grid of geometry instances)
        grid_size = 5
        self.instance_positions = []
        self.instance_colours = []

        for i in range(grid_size):
            for j in range(grid_size):
                x = (i - grid_size / 2 + 0.5) * 1.2
                y = (j - grid_size / 2 + 0.5) * 1.2
                z = 0.0
                self.instance_positions.append([x, y, z])

                # Create a nice color gradient
                # r = i / (grid_size - 1)  # Red increases with x
                # g = j / (grid_size - 1)  # Green increases with y
                # b = 0.5  # Constant blue component
                r = np.random.uniform(0, 1)
                g = np.random.uniform(0, 1)
                b = np.random.uniform(0, 1)
                self.instance_colours.append([r, g, b])

        self.instance_positions = np.array(self.instance_positions, dtype=np.float32)
        self.instance_colours = np.array(self.instance_colours, dtype=np.float32)

    def _create_render_buffer(self):
        """Delegate to parent class method."""
        super()._create_render_buffer()

    def paintWebGPU(self) -> None:
        """
        Paint WebGPU content.

        This method renders WebGPU content for the scene.
        """
        # Get the current pipeline and its background color
        current_pipeline = self.pipelines[self.current_pipeline_index]
        pipeline_name = current_pipeline[2]
        pipeline_bg_color = current_pipeline[3]

        # Temporarily update the background color for this pipeline
        original_bg_color = self.background_colour
        self.background_colour = pipeline_bg_color

        self.render_text(
            10,
            20,
            f"{pipeline_name}",
            size=20,
            colour=QColor(255, 255, 255),  # White text for better contrast
        )
        try:
            # Create a new command encoder for the render pass
            command_encoder = self.device.create_command_encoder()
            render_pass = self._create_render_pass(command_encoder)
            self.update_uniform_buffers()
            render_pass.set_viewport(
                0, 0, self.texture_size[0], self.texture_size[1], 0, 1
            )
            self.pipelines[self.current_pipeline_index][1](render_pass)
            render_pass.end()
            self.device.queue.submit([command_encoder.finish()])
        except Exception as e:
            print(f"Failed to paint WebGPU content: {e}")
        finally:
            # Restore original background color
            self.background_colour = original_bg_color

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

    def _render_multi_colour_instanced_geometry_pipeline(self, render_pass):
        """Render multi-colour instanced geometry."""
        pipeline = self.pipelines[self.current_pipeline_index][0]

        # Set instanced geometry data using new simplified API
        pipeline.set_data(
            positions=self.instance_positions,
            colours=self.instance_colours,
            geometry_data=self.geometry_data,  # Single interleaved parameter!
        )

        # Update uniforms
        pipeline.update_uniforms(
            mvp=self.mvp_matrix,
            view_matrix=self.view_matrix,
            instance_transform=np.eye(4, dtype=np.float32),
        )

        pipeline.render(render_pass, num_instances=len(self.instance_positions))

    def _render_single_colour_instanced_geometry_pipeline(self, render_pass):
        """Render single-colour instanced geometry."""
        pipeline = self.pipelines[self.current_pipeline_index][0]

        # Set instanced geometry data using new simplified API
        pipeline.set_data(
            positions=self.instance_positions,
            geometry_data=self.geometry_data,  # Single interleaved parameter!
        )

        # Update uniforms with orange color
        pipeline.update_uniforms(
            mvp=self.mvp_matrix,
            view_matrix=self.view_matrix,
            colour=np.array([1.0, 0.6, 0.1], dtype=np.float32),  # Orange
            instance_transform=np.eye(4, dtype=np.float32),
        )

        pipeline.render(render_pass, num_instances=len(self.instance_positions))

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
        elif key == Qt.Key.Key_Left:
            # Switch to previous pipeline
            self.current_pipeline_index = (self.current_pipeline_index - 1) % len(
                self.pipelines
            )
            print(f"Switched to {self.pipelines[self.current_pipeline_index][2]}")
        elif key == Qt.Key.Key_Right:
            # Switch to next pipeline
            self.current_pipeline_index = (self.current_pipeline_index + 1) % len(
                self.pipelines
            )
            print(f"Switched to {self.pipelines[self.current_pipeline_index][2]}")
        elif key == Qt.Key.Key_A:
            # Toggle automatic pipeline switching
            if self.pipeline_timer.isActive():
                self.pipeline_timer.stop()
                print("Pipeline auto-switch disabled")
            else:
                self.pipeline_timer.start(1000)
                print("Pipeline auto-switch enabled")
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

    # Use basic blue background as requested
    # Each pipeline will override this with its own subtle background color
    background_colour = (0.1, 0.1, 0.3, 1.0)  # Basic blue background

    win = WebGPUScene(background_colour=background_colour)
    win.resize(1024, 720)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    print(f"ncca-ngl.WebGPU {__version__}")
    main()
