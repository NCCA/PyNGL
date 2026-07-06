"""Native point-list rendering pipeline for WebGPU.

Handles point rendering using WebGPU's native point-list topology instead of billboarding.
"""

from typing import Any, Dict, List, Optional

import numpy as np
import wgpu

from .base_webgpu_pipeline import BaseWebGPUPipeline
from .pipeline_shaders import (
    POINT_LIST_SHADER_MULTI_COLOURED,
    POINT_LIST_SHADER_SINGLE_COLOUR,
)
from .webgpu_constants import NGLToWebGPU


class PointListPipelineMultiColour(BaseWebGPUPipeline):
    """A pipeline for rendering points using WebGPU's native point-list topology.

    Features:
    - Native WebGPU point-list rendering (no billboarding)
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
    ) -> None:
        """Initialize the point list rendering pipeline.

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
            ]
        )

    def _get_shader_code(self) -> str:
        """Get the WGSL shader code for this pipeline."""
        return POINT_LIST_SHADER_MULTI_COLOURED

    def _get_primitive_topology(self) -> wgpu.PrimitiveTopology:
        """Points are rendered as point list."""
        return wgpu.PrimitiveTopology.point_list

    def _get_vertex_buffer_layouts(self) -> List[Dict[str, Any]]:
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
        ...

    def _get_pipeline_label(self) -> str:
        """Get the label for the pipeline."""
        return "point_list_pipeline_multi_coloured"

    def set_data(
        self,
        positions: np.ndarray | wgpu.GPUBuffer,
        colours: np.ndarray | wgpu.GPUBuffer | None = None,
    ) -> None:
        """Set the point data for rendering.

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

    def update_uniforms(self, **kwargs: Any) -> None:
        """Update uniform buffer values.

        Args:
            **kwargs: Pipeline-specific uniform parameters
                - mvp: 4x4 model view projection matrix
        """
        if "mvp" in kwargs and kwargs["mvp"] is not None:
            self.uniform_data["MVP"] = kwargs["mvp"]

        self.device.queue.write_buffer(
            self.uniform_buffer, 0, self.uniform_data.tobytes()
        )

    def render(self, render_pass: wgpu.GPURenderPassEncoder, **kwargs: Any) -> None:
        """Render the points.

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
    """A pipeline for rendering points using WebGPU's native point-list topology.

    Features:
    - Native WebGPU point-list rendering (no billboarding)
    - Single colour for all points
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
    ) -> None:
        """Initialize the point list rendering pipeline.

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
                ("Colour", "float32", 3),
                ("padding", "float32"),
            ]
        )

    def _get_shader_code(self) -> str:
        """Get the WGSL shader code for this pipeline."""
        return POINT_LIST_SHADER_SINGLE_COLOUR

    def _get_primitive_topology(self) -> wgpu.PrimitiveTopology:
        """Points are rendered as point list."""
        return wgpu.PrimitiveTopology.point_list

    def _get_vertex_buffer_layouts(self) -> List[Dict[str, Any]]:
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
        self.uniform_data["Colour"] = np.array(
            [1.0, 1.0, 1.0], dtype=np.float32
        )  # Default White
        self.uniform_data["padding"] = 0.0

    def _get_pipeline_label(self) -> str:
        """Get the label for the pipeline."""
        return "point_list_pipeline_single_colour"

    def set_data(
        self,
        positions: np.ndarray | wgpu.GPUBuffer,
        colours: np.ndarray | wgpu.GPUBuffer | None = None,
    ) -> None:
        """Set the point data for rendering.

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

    def update_uniforms(self, **kwargs: Any) -> None:
        """Update uniform buffer values.

        Args:
            **kwargs: Pipeline-specific uniform parameters
                - mvp: 4x4 model view projection matrix
                - colour: 3-element array of RGB colour values
                - point_size: Size of points
        """
        if "mvp" in kwargs and kwargs["mvp"] is not None:
            self.uniform_data["MVP"] = kwargs["mvp"]

        if "colour" in kwargs and kwargs["colour"] is not None:
            self.uniform_data["Colour"] = kwargs["colour"]

        self.device.queue.write_buffer(
            self.uniform_buffer, 0, self.uniform_data.tobytes()
        )

    def render(self, render_pass: wgpu.GPURenderPassEncoder, **kwargs: Any) -> None:
        """Render the points.

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
