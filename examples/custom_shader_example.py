#!/usr/bin/env -S uv run --script
"""
Example script demonstrating custom shader usage with PyNGL WebGPU.

This script shows how to:
1. Create custom shader pipelines from WGSL files
2. Set vertex data and uniforms
3. Render with custom effects

Run with: uv run python examples/custom_shader_example.py
"""

import sys
import time
import numpy as np
from PySide6.QtWidgets import QApplication
from wgpu.utils import get_default_device
import wgpu

from ncca.ngl import Mat4, look_at, perspective, PerspMode
from ncca.ngl.webgpu import CustomShaderPipeline, WebGPUWidget


class CustomShaderExample(WebGPUWidget):
    """Example application showing custom shader usage."""

    def __init__(self):
        super().__init__(background_colour=(0.1, 0.1, 0.2, 1.0))
        self.setWindowTitle("Custom Shader Example - Gradient Triangles")

        # Initialize WebGPU
        self.device = get_default_device()
        if self.device is None:
            raise RuntimeError("Failed to initialize WebGPU device")

        self.pipeline = None
        self.rotation = 0.0
        self.start_time = time.time()

        # Setup camera
        self.view = look_at(
            np.array([0, 0, 5]), np.array([0, 0, 0]), np.array([0, 1, 0])
        )

        self._create_pipeline()
        self._create_geometry()
        self.resize(800, 600)

        # Start animation timer
        self.startTimer(16)  # ~60 FPS

    def _create_pipeline(self):
        """Create custom shader pipeline from inline WGSL source."""
        shader_source = """
struct Uniforms {
    MVP : mat4x4<f32>,
    colour : vec4<f32>,
    time : f32,
};

@group(0) @binding(0) var<uniform> uniforms : Uniforms;

struct VertexIn {
    @location(0) position : vec3<f32>,
    @location(1) colour : vec3<f32>,
};

struct VertexOut {
    @builtin(position) position : vec4<f32>,
    @location(0) fragColour : vec3<f32>,
    @location(1) barycentric : vec3<f32>,
};

@vertex
fn vertex_main(input: VertexIn, @builtin(vertex_index) vertex_index: u32) -> VertexOut {
    var output: VertexOut;
    
    // Transform position
    output.position = uniforms.MVP * vec4<f32>(input.position, 1.0);
    
    // Pass vertex colour with time-based modulation
    let pulse = sin(uniforms.time * 2.0) * 0.5 + 0.5;
    output.fragColour = input.colour * (0.5 + pulse * 0.5);
    
    // Calculate barycentric coordinates
    if (vertex_index == 0u) {
        output.barycentric = vec3<f32>(1.0, 0.0, 0.0);
    } else if (vertex_index == 1u) {
        output.barycentric = vec3<f32>(0.0, 1.0, 0.0);
    } else {
        output.barycentric = vec3<f32>(0.0, 0.0, 1.0);
    }
    
    return output;
}

@fragment
fn fragment_main(input: VertexOut) -> @location(0) vec4<f32> {
    // Create gradient effect using barycentric coordinates
    let gradient_factor = length(input.barycentric) * 0.3;
    let final_colour = mix(input.fragColour, vec3<f32>(1.0, 1.0, 0.8), gradient_factor);
    
    return vec4<f32>(final_colour, 1.0);
}
"""

        self.pipeline = CustomShaderPipeline(
            self.device,
            shader_source,
            vertex_formats=["Vec3", "Vec3"],  # position + colour
            primitive_topology=wgpu.PrimitiveTopology.triangle_list,
            pipeline_label="Example Gradient Shader",
        )

    def _create_geometry(self):
        """Create triangle geometry for demonstration."""
        # Create a grid of triangles
        grid_size = 5
        spacing = 1.5

        positions = []
        colours = []

        for i in range(grid_size):
            for j in range(grid_size):
                # Calculate center position
                center_x = (i - grid_size / 2 + 0.5) * spacing
                center_y = (j - grid_size / 2 + 0.5) * spacing

                # Create triangle vertices
                radius = 0.6
                for k in range(3):
                    angle = k * 2.0 * 3.14159 / 3.0
                    x = center_x + radius * np.cos(angle)
                    y = center_y + radius * np.sin(angle)
                    z = 0.0

                    positions.append([x, y, z])

                    # Create vibrant colors based on position
                    hue = (i * grid_size + j) * 0.1
                    colour = [
                        0.5 + 0.5 * np.sin(hue),
                        0.5 + 0.5 * np.sin(hue + 2.094),  # +120°
                        0.5 + 0.5 * np.sin(hue + 4.189),  # +240°
                    ]
                    colours.append(colour)

        self.positions = np.array(positions, dtype=np.float32)
        self.colours = np.array(colours, dtype=np.float32)

    def paintWebGPU(self):
        """Render the custom shader scene."""
        if self.pipeline is None or self.device is None:
            return

        # Update uniforms
        current_time = time.time() - self.start_time

        # Calculate MVP matrix
        aspect_ratio = self.width() / self.height() if self.height() > 0 else 1.0
        projection = perspective(45.0, aspect_ratio, 0.1, 100.0, PerspMode.WebGPU)
        rotation = Mat4.rotate_y(self.rotation) @ Mat4.rotate_x(
            np.sin(self.rotation * 0.5) * 0.2
        )
        mvp = (projection @ self.view @ rotation).to_numpy().astype(np.float32)

        # Set data and uniforms
        self.pipeline.set_data(positions=self.positions, colours=self.colours)
        self.pipeline.update_uniforms(mvp=mvp, time=current_time)

        # Render
        try:
            command_encoder = self.device.create_command_encoder()
            render_pass = self._create_render_pass(command_encoder)

            render_pass.set_viewport(0, 0, self.width(), self.height(), 0, 1)
            self.pipeline.render(render_pass)

            render_pass.end()
            self.device.queue.submit([command_encoder.finish()])

        except Exception as e:
            print(f"Rendering error: {e}")

    def resizeWebGPU(self, w, h):
        """Handle window resize."""
        self.update()

    def timerEvent(self, event):
        """Animation timer."""
        self.rotation += 0.01
        self.update()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)

    try:
        window = CustomShaderExample()
        window.show()
        return app.exec()
    except RuntimeError as e:
        print(f"Error: {e}")
        print("Make sure WebGPU is supported on your system.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
