"""Generic point rendering pipeline for WebGPU.

Handles point rendering with customizable size, colour, and projection.
"""

from typing import Any, Dict, List, Optional

import numpy as np
import wgpu

from .base_webgpu_pipeline import BasePointPipeline
from .pipeline_shaders import POINT_SHADER_MULTI_COLOURED, POINT_SHADER_SINGLE_COLOUR


class PointPipelineMultiColour(BasePointPipeline):
    """A reusable pipeline for rendering points in WebGPU.

    Features:
    - Instanced rendering of points as quads
    - Per-point colours
    - Configurable point size
    - Model, View Projection matrix support pass a projection only for 2D
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
        """Initialize the point rendering pipeline.

        Args:
            device: WebGPU device
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
                ("ViewMatrix", "float32", (4, 4)),
                ("size", "float32"),
                ("padding", np.uint32, 3),
            ]
        )

    def _get_shader_code(self) -> str:
        """Get the WGSL shader code for this pipeline."""
        return POINT_SHADER_MULTI_COLOURED

    def _get_vertex_buffer_layouts(self) -> List[Dict[str, Any]]:
        """Get vertex buffer layout configurations for the pipeline."""
        return self._get_default_vertex_layouts(has_colour_buffer=True)

    def _set_default_uniforms(self) -> None:
        """Set default values for uniform data."""
        self.uniform_data["size"] = 1.0  # Default point size
        self.uniform_data["ViewMatrix"] = np.eye(4, dtype=np.float32)

    def _get_pipeline_label(self) -> str:
        """Get the label for the pipeline."""
        return "point_pipeline_multi_coloured"

    def set_data(self, positions, colours=None) -> None:
        """Set the point data for rendering.

        Args:
            positions: Nx2 array of point positions or a pre-existing GPUBuffer.
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
                "point_pipeline_multi_coloured_position_buffer",
            )

        # Handle colours
        if colours is None:
            # Create default white colours
            default_colours = np.ones((self.num_points, 3), dtype=np.float32)
            colour_result = self._process_vertex_data(
                None,
                default_colours,
                padding_size=4,  # Pad to vec4 for alignment
                buffer_label="point_pipeline_multi_coloured_colour_buffer",
            )
            if isinstance(colour_result, wgpu.GPUBuffer):
                self.colour_buffer = colour_result
            elif colour_result:
                self.colour_buffer = colour_result[0]
            else:
                self.colour_buffer = None
        else:
            colour_result = self._process_vertex_data(
                colours,
                None,
                padding_size=4,  # Pad to vec4 for alignment
                buffer_label="point_pipeline_multi_coloured_colour_buffer",
            )
            if isinstance(colour_result, wgpu.GPUBuffer):
                self.colour_buffer = colour_result
            elif colour_result:
                self.colour_buffer = colour_result[0]
            else:
                self.colour_buffer = None

    def update_uniforms(self, **kwargs: Any) -> None:
        """Update uniform buffer values.

        Args:
            **kwargs: Pipeline-specific uniform parameters
                - mvp: 4x4 model view projection matrix
                - view_matrix: 4x4 view matrix for billboarding calculations
                - point_size: Size of points in world units
        """
        if "mvp" in kwargs and kwargs["mvp"] is not None:
            self.uniform_data["MVP"] = kwargs["mvp"]

        if "view_matrix" in kwargs and kwargs["view_matrix"] is not None:
            self.uniform_data["ViewMatrix"] = kwargs["view_matrix"]

        if "point_size" in kwargs and kwargs["point_size"] is not None:
            self.uniform_data["size"] = kwargs["point_size"]

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
        render_pass.draw(4, count)  # 4 vertices per quad, instanced

    def cleanup(self) -> None:
        """Release resources."""
        if self.position_buffer:
            self.position_buffer.destroy()
        if self.colour_buffer:
            self.colour_buffer.destroy()
        super().cleanup()


class PointPipelineSingleColour(BasePointPipeline):
    """A reusable pipeline for rendering points in WebGPU.

    Features:
    - Instanced rendering of points as quads
    - Single colour for all points
    - Configurable point size
    - Model, View Projection matrix support pass a projection only for 2D
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
        """Initialize the point rendering pipeline.

        Args:
            device: WebGPU device
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
                ("ViewMatrix", "float32", (4, 4)),
                ("ColourSize", "float32", 4),
            ]
        )

    def _get_shader_code(self) -> str:
        """Get the WGSL shader code for this pipeline."""
        return POINT_SHADER_SINGLE_COLOUR

    def _get_vertex_buffer_layouts(self) -> List[Dict[str, Any]]:
        """Get vertex buffer layout configurations for the pipeline."""
        return self._get_default_vertex_layouts(has_colour_buffer=False)

    def _set_default_uniforms(self) -> None:
        """Set default values for uniform data."""
        self.uniform_data["ColourSize"] = np.array(
            [1.0, 1.0, 1.0, 1.0], dtype=np.float32
        )  # Default White with point size 1
        self.uniform_data["ViewMatrix"] = np.eye(4, dtype=np.float32)

    def _get_pipeline_label(self) -> str:
        """Get the label for the pipeline."""
        return "point_pipeline_single_colour"

    def set_data(self, positions, colours=None) -> None:
        """Set the point data for rendering.

        Args:
            positions: Nx2 array of point positions or a pre-existing GPUBuffer.
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
                "point_pipeline_single_colour_position_buffer",
            )

    def update_uniforms(self, **kwargs: Any) -> None:
        """Update uniform buffer values.

        Args:
            **kwargs: Pipeline-specific uniform parameters
                - mvp: 4x4 model view projection matrix
                - view_matrix: 4x4 view matrix for billboarding calculations
                - colour: 3-element array of RGB colour values
                - point_size: Size of points in world units
        """
        if "mvp" in kwargs and kwargs["mvp"] is not None:
            self.uniform_data["MVP"] = kwargs["mvp"]

        if "view_matrix" in kwargs and kwargs["view_matrix"] is not None:
            self.uniform_data["ViewMatrix"] = kwargs["view_matrix"]

        if "colour" in kwargs and kwargs["colour"] is not None:
            self.uniform_data["ColourSize"][:3] = kwargs["colour"]

        if "point_size" in kwargs and kwargs["point_size"] is not None:
            self.uniform_data["ColourSize"][3] = kwargs["point_size"]

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
        render_pass.draw(4, count)  # 4 vertices per quad, instanced

    def cleanup(self) -> None:
        """Release resources."""
        if self.position_buffer:
            self.position_buffer.destroy()
        super().cleanup()
