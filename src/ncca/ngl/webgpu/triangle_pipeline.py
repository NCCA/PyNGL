"""Generic triangle rendering pipeline for WebGPU.

Handles triangle rendering with customizable colors, projection, and topology.
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import wgpu

from .base_webgpu_pipeline import BaseWebGPUPipeline
from .pipeline_shaders import (
    TRIANGLE_SHADER_MULTI_COLOURED,
    TRIANGLE_SHADER_SINGLE_COLOUR,
)
from .webgpu_constants import NGLToWebGPU


class BaseTrianglePipeline(BaseWebGPUPipeline):
    """Base class for triangle rendering pipelines."""

    def __init__(
        self,
        device: wgpu.GPUDevice,
        data_type: str = "Vec3",
        texture_format: wgpu.TextureFormat = wgpu.TextureFormat.rgba8unorm,
        depth_format: wgpu.TextureFormat = wgpu.TextureFormat.depth24plus,
        msaa_sample_count: int = 4,
        stride: int = 0,
        topology: wgpu.PrimitiveTopology = wgpu.PrimitiveTopology.triangle_list,
    ) -> None:
        """Initialize the triangle rendering pipeline.

        Args:
            device: WebGPU device
            data_type: NGL vertex data type name (e.g. "Vec3")
            texture_format: Color attachment format
            depth_format: Depth attachment format
            msaa_sample_count: Number of MSAA samples
            stride: The stride of the vertex buffer. If 0, it is inferred from data_type.
            topology: Triangle topology (triangle_list or triangle_strip)
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
        """Triangle pipelines use configurable topology."""
        return self._topology


class TrianglePipelineMultiColour(BaseTrianglePipeline):
    """A reusable pipeline for rendering triangles in WebGPU with per-vertex colors.

    Features:
    - Triangle lists or triangle strips
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
        topology: wgpu.PrimitiveTopology = wgpu.PrimitiveTopology.triangle_list,
    ) -> None:
        """Initialize the triangle rendering pipeline.

        Args:
            device: WebGPU device
            data_type: NGL vertex data type name (e.g. "Vec3")
            texture_format: Color attachment format
            depth_format: Depth attachment format
            msaa_sample_count: Number of MSAA samples
            stride: The stride of the vertex buffer. If 0, it is inferred from data_type.
            topology: Triangle topology (triangle_list or triangle_strip)
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
        return np.dtype(
            [
                ("MVP", "float32", (4, 4)),
                ("padding", "float32", 4),
            ]
        )

    def _get_shader_code(self) -> str:
        """Get the WGSL shader code for this pipeline."""
        return TRIANGLE_SHADER_MULTI_COLOURED

    def _get_vertex_buffer_layouts(self) -> List[Dict[str, Any]]:
        """Get vertex buffer layout configurations for the pipeline."""
        return [
            {
                "array_stride": self._stride,
                "step_mode": "vertex",
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
                "step_mode": "vertex",
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
        pass  # No specific defaults for triangle pipeline

    def _get_pipeline_label(self) -> str:
        """Get the label for the pipeline."""
        topology_name = (
            "list"
            if self._topology == wgpu.PrimitiveTopology.triangle_list
            else "strip"
        )
        return f"triangle_pipeline_multi_coloured_{topology_name}"

    def set_data(
        self,
        positions: np.ndarray | wgpu.GPUBuffer | None = None,
        colors: np.ndarray | wgpu.GPUBuffer | None = None,
        **kwargs: Any,
    ) -> None:
        """Set the triangle data for rendering.

        Args:
            positions: Nx2/Nx3 array of triangle positions or a pre-existing GPUBuffer.
            colors: Nx3 array of triangle colors (RGB) or a pre-existing GPUBuffer.
            **kwargs: Unused, accepted for interface compatibility.
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
                    f"triangle_pipeline_multi_coloured_position_buffer_{self._get_pipeline_label()}",
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
                    buffer_label=f"triangle_pipeline_multi_coloured_colour_buffer_{self._get_pipeline_label()}",
                )
                if isinstance(color_result, wgpu.GPUBuffer):
                    self.color_buffer = color_result
                elif color_result:
                    self.color_buffer = color_result[0]
                else:
                    self.color_buffer = None

    def update_uniforms(self, **kwargs: Any) -> None:
        """Update uniform buffer values.

        Args:
            **kwargs: Pipeline-specific uniform parameters
                - mvp: 4x4 projection matrix
        """
        if "mvp" in kwargs and kwargs["mvp"] is not None:
            self.uniform_data["MVP"] = kwargs["mvp"]

        self.device.queue.write_buffer(
            self.uniform_buffer, 0, self.uniform_data.tobytes()
        )

    def render(self, render_pass: wgpu.GPURenderPassEncoder, **kwargs: Any) -> None:
        """Render the triangles.

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


class TrianglePipelineSingleColour(BaseTrianglePipeline):
    """A reusable pipeline for rendering triangles in WebGPU with single color.

    Features:
    - Triangle lists or triangle strips
    - Single color for all triangles
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
        topology: wgpu.PrimitiveTopology = wgpu.PrimitiveTopology.triangle_list,
        colour: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    ) -> None:
        """Initialize the triangle rendering pipeline.

        Args:
            device: WebGPU device
            data_type: NGL vertex data type name (e.g. "Vec3")
            texture_format: Color attachment format
            depth_format: Depth attachment format
            msaa_sample_count: Number of MSAA samples
            stride: The stride of the vertex buffer. If 0, it is inferred from data_type.
            topology: Triangle topology (triangle_list or triangle_strip)
            colour: RGB color tuple for triangles (default white)
        """
        # Pipeline-specific buffer tracking
        self.vertex_buffer: Optional[wgpu.GPUBuffer] = None
        self.num_vertices: int = 0
        self._colour = np.array(colour, dtype=np.float32)

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
        return np.dtype(
            [
                ("MVP", "float32", (4, 4)),
                ("Colour", "float32", 3),
                ("padding", "float32", 1),
            ]
        )

    def _get_shader_code(self) -> str:
        """Get the WGSL shader code for this pipeline."""
        return TRIANGLE_SHADER_SINGLE_COLOUR

    def _get_vertex_buffer_layouts(self) -> List[Dict[str, Any]]:
        """Get vertex buffer layout configurations for the pipeline."""
        return [
            {
                "array_stride": self._stride,
                "step_mode": "vertex",
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
        pass  # No specific defaults for triangle pipeline

    def _get_pipeline_label(self) -> str:
        """Get the label for the pipeline."""
        topology_name = (
            "list"
            if self._topology == wgpu.PrimitiveTopology.triangle_list
            else "strip"
        )
        return f"triangle_pipeline_single_colour_{topology_name}"

    def set_data(
        self,
        positions: np.ndarray | wgpu.GPUBuffer | None = None,
        colors: np.ndarray | wgpu.GPUBuffer | None = None,
        **kwargs: Any,
    ) -> None:
        """Set the triangle data for rendering.

        Args:
            positions: Nx2/Nx3 array of triangle positions or a pre-existing GPUBuffer.
            colors: Ignored for single colour pipeline
            **kwargs: Unused, accepted for interface compatibility.
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
                    f"triangle_pipeline_single_colour_position_buffer_{self._get_pipeline_label()}",
                )
                self.num_vertices = buffer_size // self._stride

    def update_uniforms(self, **kwargs: Any) -> None:
        """Update uniform buffer values.

        Args:
            **kwargs: Pipeline-specific uniform parameters
                - mvp: 4x4 projection matrix
                - colour: RGB color tuple
        """
        if "mvp" in kwargs and kwargs["mvp"] is not None:
            self.uniform_data["MVP"] = kwargs["mvp"]

        if "colour" in kwargs and kwargs["colour"] is not None:
            colour = np.array(kwargs["colour"], dtype=np.float32)
            if colour.shape == (3,):
                self.uniform_data["Colour"] = colour
                self._colour = colour

        self.device.queue.write_buffer(
            self.uniform_buffer, 0, self.uniform_data.tobytes()
        )

    def set_color(self, colour: Tuple[float, float, float]) -> None:
        """Set the color for the triangles.

        Args:
            colour: RGB color tuple
        """
        colour_array = np.array(colour, dtype=np.float32)
        if colour_array.shape == (3,):
            self.uniform_data["Colour"] = colour_array
            self._colour = colour_array
            self.device.queue.write_buffer(
                self.uniform_buffer, 0, self.uniform_data.tobytes()
            )

    def render(self, render_pass: wgpu.GPURenderPassEncoder, **kwargs: Any) -> None:
        """Render the triangles.

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
