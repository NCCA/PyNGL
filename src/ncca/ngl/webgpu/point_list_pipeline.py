"""
Native point-list rendering pipeline for WebGPU.
Handles point rendering using WebGPU's native point-list topology instead of billboarding.
"""

from typing import Optional

import numpy as np
import wgpu

from .base_webgpu_pipeline import BaseWebGPUPipeline
from .webgpu_constants import NGLToWebGPU

_POINT_LIST_SHADER_MULTI_COLOURED = """
@group(0) @binding(0) var<uniform> uniforms : Uniforms;

struct Uniforms
{
    MVP : mat4x4<f32>,
    point_size: f32,
    padding: u32,
    padding2: u32,
    padding3: u32,
};

struct VertexIn {
    @location(0) position: vec3<f32>,
    @location(1) colour: vec3<f32>,
};

struct VertexOut {
    @builtin(position) position: vec4<f32>,
    @location(0) fragColour: vec3<f32>,
};

@vertex
fn vertex_main(input: VertexIn) -> VertexOut {
    var output: VertexOut;
    output.position = uniforms.MVP * vec4<f32>(input.position, 1.0);
    output.fragColour = input.colour;
    return output;
}

@fragment
fn fragment_main(fragData: VertexOut) -> @location(0) vec4<f32>
{
    return vec4<f32>(fragData.fragColour, 1.0);
}
"""

_POINT_LIST_SHADER_SINGLE_COLOUR = """
@group(0) @binding(0) var<uniform> uniforms : Uniforms;

struct Uniforms
{
    MVP : mat4x4<f32>,
    ColourSize: vec4<f32>,
};

struct VertexIn {
    @location(0) position: vec3<f32>,
};

struct VertexOut {
    @builtin(position) position: vec4<f32>,
};

@vertex
fn vertex_main(input: VertexIn) -> VertexOut {
    var output: VertexOut;
    output.position = uniforms.MVP * vec4<f32>(input.position, 1.0);
    return output;
}

@fragment
fn fragment_main(fragData: VertexOut) -> @location(0) vec4<f32>
{
    return vec4<f32>(uniforms.ColourSize.xyz, 1.0);
}
"""


class PointListPipelineMultiColour(BaseWebGPUPipeline):
    """
    A pipeline for rendering points using WebGPU's native point-list topology.

    Features:
    - Native WebGPU point-list rendering (no billboarding)
    - Per-point colours
    - Configurable point size
    - Model, View Projection matrix support
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
    ):
        """
        Initialize the point list rendering pipeline.

        Args:
            device: WebGPU device
            data_type: Vertex data type (e.g., "Vec3", "Vec2")
            texture_format: colour attachment format
            depth_format: Depth attachment format
            msaa_sample_count: Number of MSAA samples
            stride: The stride of the vertex buffer. If 0, it is inferred from data_type.
        """
        # Pipeline-specific buffer tracking
        self.position_buffer: Optional[wgpu.GPUBuffer] = None
        self.colour_buffer: Optional[wgpu.GPUBuffer] = None
        self.num_points: int = 0

        super().__init__(
            device=device,
            texture_format=texture_format,
            depth_format=depth_format,
            msaa_sample_count=msaa_sample_count,
            data_type=data_type,
            stride=stride,
        )

    def get_dtype(self) -> np.dtype:
        """Get the data type of the pipeline."""
        return np.dtype(
            [
                ("MVP", "float32", (4, 4)),
                ("point_size", "float32"),
                ("padding", np.uint32, 3),
            ]
        )

    def _get_shader_code(self) -> str:
        """Get the WGSL shader code for this pipeline."""
        return _POINT_LIST_SHADER_MULTI_COLOURED

    def _get_primitive_topology(self) -> wgpu.PrimitiveTopology:
        """Points are rendered as point list."""
        return wgpu.PrimitiveTopology.point_list

    def _get_vertex_buffer_layouts(self):
        """Get vertex buffer layout configurations for the pipeline."""
        position_layout = {
            "array_stride": self._stride,
            "step_mode": wgpu.VertexStepMode.vertex,
            "attributes": [
                {
                    "format": NGLToWebGPU.vertex_format(self._data_type),
                    "offset": 0,
                    "shader_location": 0,
                }
            ],
        }

        colour_layout = {
            "array_stride": 12,  # 3 * float32 for RGB
            "step_mode": wgpu.VertexStepMode.vertex,
            "attributes": [
                {
                    "format": wgpu.VertexFormat.float32x3,
                    "offset": 0,
                    "shader_location": 1,
                }
            ],
        }

        return [position_layout, colour_layout]

    def _set_default_uniforms(self) -> None:
        """Set default values for uniform data."""
        self.uniform_data["point_size"] = 1.0  # Default point size

    def _get_pipeline_label(self) -> str:
        """Get the label for the pipeline."""
        return "point_list_pipeline_multi_coloured"

    def set_data(
        self,
        positions,
        colours=None,
    ) -> None:
        """
        Set the point data for rendering.

        Args:
            positions: Nx3 array of point positions or a pre-existing GPUBuffer.
            colours: Nx3 array of point colours (RGB) or a pre-existing GPUBuffer.
                    If None, uses white.
        """
        # Handle positions
        if isinstance(positions, wgpu.GPUBuffer):
            self.position_buffer = positions
            self.num_points = positions.size // self._stride
        else:  # numpy array
            self.num_points = len(positions)
            self.position_buffer, _ = self._create_or_update_buffer(
                self.position_buffer,
                positions,
                wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
                "point_list_pipeline_multi_coloured_position_buffer",
            )

        # Handle colours
        if colours is None:
            # Create default white colours
            default_colours = np.ones((self.num_points, 3), dtype=np.float32)
            self.colour_buffer, _ = self._create_or_update_buffer(
                self.colour_buffer,
                default_colours,
                wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
                "point_list_pipeline_multi_coloured_colour_buffer",
            )
        else:
            self.colour_buffer, _ = self._create_or_update_buffer(
                self.colour_buffer,
                colours,
                wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
                "point_list_pipeline_multi_coloured_colour_buffer",
            )

    def update_uniforms(self, **kwargs) -> None:
        """
        Update uniform buffer values.

        Args:
            **kwargs: Pipeline-specific uniform parameters
                - mvp: 4x4 model view projection matrix
                - point_size: Size of points
        """
        if "mvp" in kwargs and kwargs["mvp"] is not None:
            self.uniform_data["MVP"] = kwargs["mvp"]

        if "point_size" in kwargs and kwargs["point_size"] is not None:
            self.uniform_data["point_size"] = kwargs["point_size"]

        self.device.queue.write_buffer(
            self.uniform_buffer, 0, self.uniform_data.tobytes()
        )

    def render(self, render_pass: wgpu.GPURenderPassEncoder, **kwargs) -> None:
        """
        Render the points.

        Args:
            render_pass: Active render pass encoder
            **kwargs: Pipeline-specific render parameters
                - num_points: Number of points to render (defaults to all)
        """
        num_points = kwargs.get("num_points", None)

        if self.position_buffer is None or self.colour_buffer is None:
            return

        count = num_points if num_points is not None else self.num_points

        render_pass.set_pipeline(self.pipeline)
        if self.bind_group:
            render_pass.set_bind_group(0, self.bind_group, [], 0, 999999)
        render_pass.set_vertex_buffer(0, self.position_buffer)
        render_pass.set_vertex_buffer(1, self.colour_buffer)
        render_pass.draw(count)  # Draw points as point list

    def cleanup(self) -> None:
        """Release resources."""
        if self.position_buffer:
            self.position_buffer.destroy()
        if self.colour_buffer:
            self.colour_buffer.destroy()
        super().cleanup()


class PointListPipelineSingleColour(BaseWebGPUPipeline):
    """
    A pipeline for rendering points using WebGPU's native point-list topology.

    Features:
    - Native WebGPU point-list rendering (no billboarding)
    - Single colour for all points
    - Configurable point size
    - Model, View Projection matrix support
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
    ):
        """
        Initialize the point list rendering pipeline.

        Args:
            device: WebGPU device
            data_type: Vertex data type (e.g., "Vec3", "Vec2")
            texture_format: colour attachment format
            depth_format: Depth attachment format
            msaa_sample_count: Number of MSAA samples
            stride: The stride of the vertex buffer. If 0, it is inferred from data_type.
        """
        # Pipeline-specific buffer tracking
        self.position_buffer: Optional[wgpu.GPUBuffer] = None
        self.num_points: int = 0

        super().__init__(
            device=device,
            texture_format=texture_format,
            depth_format=depth_format,
            msaa_sample_count=msaa_sample_count,
            data_type=data_type,
            stride=stride,
        )

    def get_dtype(self) -> np.dtype:
        """Get the data type of the pipeline."""
        return np.dtype(
            [
                ("MVP", "float32", (4, 4)),
                ("ColourSize", "float32", 4),
            ]
        )

    def _get_shader_code(self) -> str:
        """Get the WGSL shader code for this pipeline."""
        return _POINT_LIST_SHADER_SINGLE_COLOUR

    def _get_primitive_topology(self) -> wgpu.PrimitiveTopology:
        """Points are rendered as point list."""
        return wgpu.PrimitiveTopology.point_list

    def _get_vertex_buffer_layouts(self):
        """Get vertex buffer layout configurations for the pipeline."""
        position_layout = {
            "array_stride": self._stride,
            "step_mode": wgpu.VertexStepMode.vertex,
            "attributes": [
                {
                    "format": NGLToWebGPU.vertex_format(self._data_type),
                    "offset": 0,
                    "shader_location": 0,
                }
            ],
        }

        return [position_layout]

    def _set_default_uniforms(self) -> None:
        """Set default values for uniform data."""
        self.uniform_data["ColourSize"] = np.array(
            [1.0, 1.0, 1.0, 1.0], dtype=np.float32
        )  # Default White with point size 1

    def _get_pipeline_label(self) -> str:
        """Get the label for the pipeline."""
        return "point_list_pipeline_single_colour"

    def set_data(self, positions, colours=None) -> None:
        """
        Set the point data for rendering.

        Args:
            positions: Nx3 array of point positions or a pre-existing GPUBuffer.
            colours: Ignored for single colour pipeline
        """
        # Handle positions
        if isinstance(positions, wgpu.GPUBuffer):
            self.position_buffer = positions
            self.num_points = positions.size // self._stride
        else:  # numpy array
            self.num_points = len(positions)
            self.position_buffer, _ = self._create_or_update_buffer(
                self.position_buffer,
                positions,
                wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
                "point_list_pipeline_single_colour_position_buffer",
            )

    def update_uniforms(self, **kwargs) -> None:
        """
        Update uniform buffer values.

        Args:
            **kwargs: Pipeline-specific uniform parameters
                - mvp: 4x4 model view projection matrix
                - colour: 3-element array of RGB colour values
                - point_size: Size of points
        """
        if "mvp" in kwargs and kwargs["mvp"] is not None:
            self.uniform_data["MVP"] = kwargs["mvp"]

        if "colour" in kwargs and kwargs["colour"] is not None:
            self.uniform_data["ColourSize"][:3] = kwargs["colour"]

        if "point_size" in kwargs and kwargs["point_size"] is not None:
            self.uniform_data["ColourSize"][3] = kwargs["point_size"]

        self.device.queue.write_buffer(
            self.uniform_buffer, 0, self.uniform_data.tobytes()
        )

    def render(self, render_pass: wgpu.GPURenderPassEncoder, **kwargs) -> None:
        """
        Render the points.

        Args:
            render_pass: Active render pass encoder
            **kwargs: Pipeline-specific render parameters
                - num_points: Number of points to render (defaults to all)
        """
        num_points = kwargs.get("num_points", None)

        if self.position_buffer is None:
            return

        count = num_points if num_points is not None else self.num_points

        render_pass.set_pipeline(self.pipeline)
        if self.bind_group:
            render_pass.set_bind_group(0, self.bind_group, [], 0, 999999)
        render_pass.set_vertex_buffer(0, self.position_buffer)
        render_pass.draw(count)  # Draw points as point list

    def cleanup(self) -> None:
        """Release resources."""
        if self.position_buffer:
            self.position_buffer.destroy()
        super().cleanup()
