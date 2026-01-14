#!/usr/bin/env -S uv run --active --script
import argparse
import sys
import time

import numpy as np
import wgpu
import wgpu.utils
from cffi.cffi_opcode import _NUM_PRIM
from PySide6.QtCore import Qt, QTimer
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
        self.pipelines.append((
            PipelineFactory.create_pipeline(self.device, PipelineType.MULTI_COLOURED_POINTS),
            self._render_multi_colour_point_pipeline,
            "PipelineType.MULTI_COLOURED_POINTS",
        ))
        self.pipelines.append((
            PipelineFactory.create_pipeline(self.device, PipelineType.SINGLE_COLOUR_POINTS),
            self._render_single_colour_point_pipeline,
            "PipelineType.SINGLE_COLOUR_POINTS",
        ))
        self.current_pipeline_index = 1
        # Initialize render textures with default size
        self.texture_size = (1024, 720)
        self._create_render_buffer()

        # Setup timers
        self.startTimer(16)  # Animation timer (~60 FPS)
        self.pipeline_timer = QTimer()
        self.pipeline_timer.timeout.connect(self.switch_pipeline)
        self.pipeline_timer.start(5000)  # Switch every 5 seconds

    def _create_buffers(self, num_points):
        self.colours = np.random.random((num_points, 3)).astype(np.float32)
        self.positions = np.random.uniform(-4.0, 4.0, size=(num_points, 3)).astype(np.float32)

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
            colour=Qt.yellow,
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
            render_pass.set_viewport(0, 0, self.texture_size[0], self.texture_size[1], 0, 1)
            self.pipelines[self.current_pipeline_index][1](render_pass)
            render_pass.end()
            self.device.queue.submit([command_encoder.finish()])
        except Exception as e:
            print(f"Failed to paint WebGPU content: {e}")

    def resizeWebGPU(self, width, height) -> None:
        """
        Called whenever the window is resized.
        It's crucial to update the viewport and projection matrix here.

        Args:
            width: The new width of the window.
            height: The new height of the window.
        """

        # Update texture size to match window dimensions
        self.texture_size = (width, height)

        # Update projection matrix
        self.project = perspective(45.0, width / height if height > 0 else 1, 0.1, 100.0, PerspMode.WebGPU)

        self.update()

    def _render_multi_colour_point_pipeline(self, render_pass):
        self.pipelines[self.current_pipeline_index][0].set_data(self.positions, self.colours)
        self.pipelines[self.current_pipeline_index][0].render(render_pass)
        self.pipelines[self.current_pipeline_index][0].update_uniforms(self.mvp_matrix, self.view_matrix, 0.05)

    def _render_single_colour_point_pipeline(self, render_pass):
        self.pipelines[self.current_pipeline_index][0].set_data(self.positions)
        self.pipelines[self.current_pipeline_index][0].render(render_pass)
        self.pipelines[self.current_pipeline_index][0].update_uniforms(
            self.mvp_matrix,
            self.view_matrix,
            np.array([1, 0, 0], dtype=np.float32),
            0.05,
        )

    def update_uniform_buffers(self) -> None:
        """
        update the uniform buffers for the line pipeline.
        """
        rotation = Mat4.rotate_y(self.rotation)
        self.mvp_matrix = (self.project @ self.view @ rotation).to_numpy().astype(np.float32)
        self.view_matrix = (self.view @ rotation).to_numpy().astype(np.float32)

    def keyPressEvent(self, event) -> None:
        """
        Handles keyboard press events.

        Args:
            event: The QKeyEvent object containing information about the key press.
        """
        key = event.key()
        if key == Qt.Key_Escape:
            self.close()  # Exit the application
        elif key == Qt.Key_Space:
            self.animate = not self.animate
        self.update()

        # Call the base class implementation for any unhandled events
        super().keyPressEvent(event)

    def switch_pipeline(self) -> None:
        """Switch to the next pipeline in the list."""
        self.current_pipeline_index = (self.current_pipeline_index + 1) % len(self.pipelines)
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
