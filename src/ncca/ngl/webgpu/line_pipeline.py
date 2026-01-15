"""
Generic line rendering pipeline for WebGPU.
Handles line rendering with customizable color and projection.
"""

from typing import Optional

import numpy as np
import wgpu

from .base_webgpu_pipeline import BaseWebGPUPipeline
from .webgpu_constants import NGLToWebGPU

_LINE_SHADER_SINGLE_COLOUR = """
// LineShader.wgsl
struct Uniforms {
    MVP: mat4x4<f32>,
};

@binding(0) @group(0) var<uniform> uniforms: Uniforms;

@vertex
fn vertex_main(@location(0) pos: vec3<f32>) -> @builtin(position) vec4<f32> {
    return uniforms.MVP * vec4<f32>(pos, 1.0);
}

@fragment
fn fragment_main() -> @location(0) vec4<f32> {
    return vec4<f32>(1.0, 1.0, 1.0, 1.0); // Grey color for grid lines
}
"""

_LINE_SHADER_MULTI_COLOURED = """
// LineShader.wgsl
struct Uniforms {
    MVP: mat4x4<f32>,
};

@binding(0) @group(0) var<uniform> uniforms: Uniforms;

struct VertexIn {
    @location(0) pos: vec3<f32>,
    @location(1) color: vec3<f32>,
};

struct VertexOut {
    @builtin(position) position: vec4<f32>,
    @location(0) color: vec3<f32>,
};

@vertex
fn vertex_main(input: VertexIn) -> VertexOut {
    var output: VertexOut;
    output.position = uniforms.MVP * vec4<f32>(input.pos, 1.0);
    output.color = input.color;
    return output;
}

@fragment
fn fragment_main(input: VertexOut) -> @location(0) vec4<f32> {
    return vec4<f32>(input.color, 1.0);
}
"""


class BaseLinePipeline(BaseWebGPUPipeline):
    """Base class for line rendering pipelines."""

    def __init__(
        self,
        device: wgpu.GPUDevice,
        data_type: str = "Vec3",
        texture_format: wgpu.TextureFormat = wgpu.TextureFormat.rgba8unorm,
        depth_format: wgpu.TextureFormat = wgpu.TextureFormat.depth24plus,
        msaa_sample_count: int = 4,
        stride: int = 0,
        topology: wgpu.PrimitiveTopology = wgpu.PrimitiveTopology.line_list,
    ):
        """
        Initialize the base line pipeline.

        Args:
            device: WebGPU device
            texture_format: Color attachment format
            depth_format: Depth attachment format
            msaa_sample_count: Number of MSAA samples
            stride: The stride of the vertex buffer. If 0, it is inferred from data_type.
            topology: Primitive topology (line_list or line_strip)
        """
        self._topology = topology
        super().__init__(
            device=device,
            texture_format=texture_format,
            depth_format=depth_format,
            msaa_sample_count=msaa_sample_count,
            data_type=data_type,
            stride=stride,
        )

    def _get_primitive_topology(self) -> wgpu.PrimitiveTopology:
        """Line pipelines use configurable topology."""
        return self._topology


class LinePipelineMultiColour(BaseLinePipeline):
    """
    A reusable pipeline for rendering lines in WebGPU with per-vertex colors.

    Features:
    - Line strips or line segments
    - Per-vertex colors
    - MVP matrix support
    - MSAA support
    """

    def __init__(
        self,
        device: wgpu.GPUDevice,
        data_type: str = "Vec3",
        texture_format: wgpu.TextureFormat = wgpu.TextureFormat.rgba8unorm,
        depth_format: wgpu.TextureFormat = wgpu.TextureFormat.depth24plus,
        msaa_sample_count: int = 4,
        stride: int = 0,
        topology: wgpu.PrimitiveTopology = wgpu.PrimitiveTopology.line_list,
    ):
        """
        Initialize the line rendering pipeline.

        Args:
            device: WebGPU device
            texture_format: Color attachment format
            depth_format: Depth attachment format
            msaa_sample_count: Number of MSAA samples
            stride: The stride of the vertex buffer. If 0, it is inferred from data_type.
            topology: Primitive topology (line_list or line_strip)
        """
        # Pipeline-specific buffer tracking
        self.vertex_buffer: Optional[wgpu.GPUBuffer] = None
        self.color_buffer: Optional[wgpu.GPUBuffer] = None
        self.num_vertices: int = 0

        super().__init__(
            device=device,
            texture_format=texture_format,
            depth_format=depth_format,
            msaa_sample_count=msaa_sample_count,
            data_type=data_type,
            stride=stride,
            topology=topology,
        )

    def get_dtype(self) -> np.dtype:
        """Get the data type of the pipeline."""
        return np.dtype([
            ("MVP", "float32", (4, 4)),
        ])

    def _get_shader_code(self) -> str:
        """Get the WGSL shader code for this pipeline."""
        return _LINE_SHADER_MULTI_COLOURED

    def _get_vertex_buffer_layouts(self):
        """Get vertex buffer layout configurations for the pipeline."""
        return [
            {
                "array_stride": self._stride,
                "step_mode": wgpu.VertexStepMode.vertex,
                "attributes": [
                    {
                        "format": NGLToWebGPU.vertex_format(self._data_type),
                        "offset": 0,
                        "shader_location": 0,
                    },
                ],
            },
            {
                "array_stride": NGLToWebGPU.stride_from_type("Vec3"),
                "step_mode": wgpu.VertexStepMode.vertex,
                "attributes": [
                    {
                        "format": NGLToWebGPU.vertex_format("Vec3"),
                        "offset": 0,
                        "shader_location": 1,
                    },
                ],
            },
        ]

    def _set_default_uniforms(self) -> None:
        """Set default values for uniform data."""
        pass

    def _get_pipeline_label(self) -> str:
        """Get the label for the pipeline."""
        return "line_pipeline_multi_coloured"

    def set_data(self, positions=None, colors=None, **kwargs) -> None:
        """
        Set the line data for rendering.

        Args:
            positions: Nx2/Nx3 array of line positions or a pre-existing GPUBuffer.
            colors: Nx3 array of line colors (RGB) or a pre-existing GPUBuffer.
        """
        if positions is not None:
            if isinstance(positions, wgpu.GPUBuffer):
                self.vertex_buffer = positions
                self.num_vertices = positions.size // self._stride
            else:  # numpy array
                self.vertex_buffer, buffer_size = self._create_or_update_buffer(
                    self.vertex_buffer,
                    positions,
                    wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
                    "line_pipeline_multi_coloured_position_buffer",
                )
                self.num_vertices = buffer_size // self._stride

        if colors is not None:
            if isinstance(colors, wgpu.GPUBuffer):
                self.color_buffer = colors
            else:
                color_result = self._process_vertex_data(
                    colors,
                    None,
                    padding_size=4,  # Pad to vec4 for alignment
                    buffer_label="line_pipeline_multi_coloured_colour_buffer",
                )
                if isinstance(color_result, wgpu.GPUBuffer):
                    self.color_buffer = color_result
                elif color_result:
                    self.color_buffer = color_result[0]
                else:
                    self.color_buffer = None

    def update_uniforms(self, **kwargs) -> None:
        """
        Update uniform buffer values.

        Args:
            **kwargs: Pipeline-specific uniform parameters
                - mvp: 4x4 projection matrix
        """
        if "mvp" in kwargs and kwargs["mvp"] is not None:
            self.uniform_data["MVP"] = kwargs["mvp"]

        self.device.queue.write_buffer(self.uniform_buffer, 0, self.uniform_data.tobytes())

    def render(self, render_pass: wgpu.GPURenderPassEncoder, **kwargs) -> None:
        """
        Render the lines.

        Args:
            render_pass: Active render pass encoder
            **kwargs: Pipeline-specific render parameters
                - num_vertices: Number of vertices to render (defaults to all)
        """
        num_vertices = kwargs.get("num_vertices", None)

        if self.vertex_buffer is None or self.color_buffer is None:
            return

        count = num_vertices if num_vertices is not None else self.num_vertices

        render_pass.set_pipeline(self.pipeline)
        if self.bind_group:
            render_pass.set_bind_group(0, self.bind_group, [], 0, 999999)
        render_pass.set_vertex_buffer(0, self.vertex_buffer)
        render_pass.set_vertex_buffer(1, self.color_buffer)
        render_pass.draw(count)

    def cleanup(self) -> None:
        """Release resources."""
        if self.vertex_buffer:
            self.vertex_buffer.destroy()
        if self.color_buffer:
            self.color_buffer.destroy()
        super().cleanup()


class LinePipelineSingleColour(BaseLinePipeline):
    """
    A reusable pipeline for rendering lines in WebGPU with single color.

    Features:
    - Line strips or line segments
    - Single color for all lines
    - MVP matrix support
    - MSAA support
    """

    def __init__(
        self,
        device: wgpu.GPUDevice,
        data_type: str = "Vec3",
        texture_format: wgpu.TextureFormat = wgpu.TextureFormat.rgba8unorm,
        depth_format: wgpu.TextureFormat = wgpu.TextureFormat.depth24plus,
        msaa_sample_count: int = 4,
        stride: int = 0,
        topology: wgpu.PrimitiveTopology = wgpu.PrimitiveTopology.line_list,
    ):
        """
        Initialize the line rendering pipeline.

        Args:
            device: WebGPU device
            texture_format: Color attachment format
            depth_format: Depth attachment format
            msaa_sample_count: Number of MSAA samples
            stride: The stride of the vertex buffer. If 0, it is inferred from data_type.
            topology: Primitive topology (line_list or line_strip)
        """
        # Pipeline-specific buffer tracking
        self.vertex_buffer: Optional[wgpu.GPUBuffer] = None
        self.num_vertices: int = 0

        super().__init__(
            device=device,
            texture_format=texture_format,
            depth_format=depth_format,
            msaa_sample_count=msaa_sample_count,
            data_type=data_type,
            stride=stride,
            topology=topology,
        )

    def get_dtype(self) -> np.dtype:
        """Get the data type of the pipeline."""
        return np.dtype([
            ("MVP", "float32", (4, 4)),
        ])

    def _get_shader_code(self) -> str:
        """Get the WGSL shader code for this pipeline."""
        return _LINE_SHADER_SINGLE_COLOUR

    def _get_vertex_buffer_layouts(self):
        """Get vertex buffer layout configurations for the pipeline."""
        return [
            {
                "array_stride": self._stride,
                "step_mode": wgpu.VertexStepMode.vertex,
                "attributes": [
                    {
                        "format": NGLToWebGPU.vertex_format(self._data_type),
                        "offset": 0,
                        "shader_location": 0,
                    },
                ],
            },
        ]

    def _set_default_uniforms(self) -> None:
        """Set default values for uniform data."""
        pass

    def _get_pipeline_label(self) -> str:
        """Get the label for the pipeline."""
        return "line_pipeline_single_colour"

    def set_data(self, positions=None, colors=None, **kwargs) -> None:
        """
        Set the line data for rendering.

        Args:
            positions: Nx2/Nx3 array of line positions or a pre-existing GPUBuffer.
            colors: Ignored for single colour pipeline
        """
        if positions is not None:
            if isinstance(positions, wgpu.GPUBuffer):
                self.vertex_buffer = positions
                self.num_vertices = positions.size // self._stride
            else:  # numpy array
                self.vertex_buffer, buffer_size = self._create_or_update_buffer(
                    self.vertex_buffer,
                    positions,
                    wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
                    "line_pipeline_single_colour_position_buffer",
                )
                self.num_vertices = buffer_size // self._stride

    def update_uniforms(self, **kwargs) -> None:
        """
        Update uniform buffer values.

        Args:
            **kwargs: Pipeline-specific uniform parameters
                - mvp: 4x4 projection matrix
        """
        if "mvp" in kwargs and kwargs["mvp"] is not None:
            self.uniform_data["MVP"] = kwargs["mvp"]

        self.device.queue.write_buffer(self.uniform_buffer, 0, self.uniform_data.tobytes())

    def render(self, render_pass: wgpu.GPURenderPassEncoder, **kwargs) -> None:
        """
        Render the lines.

        Args:
            render_pass: Active render pass encoder
            **kwargs: Pipeline-specific render parameters
                - num_vertices: Number of vertices to render (defaults to all)
        """
        num_vertices = kwargs.get("num_vertices", None)

        if self.vertex_buffer is None:
            return

        count = num_vertices if num_vertices is not None else self.num_vertices

        render_pass.set_pipeline(self.pipeline)
        if self.bind_group:
            render_pass.set_bind_group(0, self.bind_group, [], 0, 999999)
        render_pass.set_vertex_buffer(0, self.vertex_buffer)
        render_pass.draw(count)

    def cleanup(self) -> None:
        """Release resources."""
        if self.vertex_buffer:
            self.vertex_buffer.destroy()
        super().cleanup()


# Backward compatibility alias
LinePipeline = LinePipelineSingleColour
