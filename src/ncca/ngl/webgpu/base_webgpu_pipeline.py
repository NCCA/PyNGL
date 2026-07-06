"""Abstract base classes for WebGPU rendering pipelines.

Provides common functionality for buffer management, pipeline creation, and rendering.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import wgpu

from .webgpu_constants import NGLToWebGPU


class BaseWebGPUPipeline(ABC):
    """Abstract base class for all WebGPU rendering pipelines.

    Provides common functionality for:
    - Buffer management and creation
    - Pipeline configuration
    - Uniform buffer handling
    - Resource cleanup
    """

    def __init__(
        self,
        device: wgpu.GPUDevice,
        texture_format: wgpu.TextureFormat = wgpu.TextureFormat.rgba8unorm,
        depth_format: wgpu.TextureFormat = wgpu.TextureFormat.depth24plus,
        msaa_sample_count: int = 4,
        data_type: str = "Vec3",
        stride: int = 0,
    ) -> None:
        """Initialize base pipeline.

        Args:
            device: WebGPU device
            texture_format: Colour attachment format
            depth_format: Depth attachment format
            msaa_sample_count: Number of MSAA samples
            data_type: Vertex data type (e.g., "Vec3", "Vec2")
            stride: Vertex buffer stride. If 0, inferred from data_type
        """
        self.device = device
        self.texture_format = texture_format
        self.depth_format = depth_format
        self.msaa_sample_count = msaa_sample_count
        self._data_type = data_type

        if stride != 0:
            self._stride = stride
        else:
            self._stride = NGLToWebGPU.stride_from_type(self._data_type)

        # Core pipeline resources
        self.pipeline: Optional[wgpu.GPURenderPipeline] = None
        self.uniform_buffer: Optional[wgpu.GPUBuffer] = None
        self.bind_group: Optional[wgpu.GPUBindGroup] = None

        # Initialize uniform data structure
        self.uniform_data = np.zeros((), dtype=self.get_dtype())
        self._set_default_uniforms()

        # Create the pipeline
        self._create_pipeline()

    @abstractmethod
    def get_dtype(self) -> np.dtype:
        """Get the numpy dtype for the uniform buffer structure."""
        pass

    @abstractmethod
    def _get_shader_code(self) -> str:
        """Get the WGSL shader code for this pipeline."""
        pass

    @abstractmethod
    def _get_vertex_buffer_layouts(self) -> List[Dict[str, Any]]:
        """Get vertex buffer layout configurations for the pipeline."""
        pass

    @abstractmethod
    def _get_primitive_topology(self) -> wgpu.PrimitiveTopology:
        """Get the primitive topology for the pipeline."""
        pass

    @abstractmethod
    def _set_default_uniforms(self) -> None:
        """Set default values for uniform data."""
        pass

    @abstractmethod
    def _get_pipeline_label(self) -> str:
        """Get the label for the pipeline."""
        pass

    def _create_pipeline(self) -> None:
        """Create the render pipeline and associated resources."""
        # Load shader
        shader_module = self.device.create_shader_module(code=self._get_shader_code())

        # Create render pipeline
        self.pipeline = self.device.create_render_pipeline(
            label=self._get_pipeline_label(),
            layout="auto",
            vertex={
                "module": shader_module,
                "entry_point": "vertex_main",
                "buffers": self._get_vertex_buffer_layouts(),
            },
            fragment={
                "module": shader_module,
                "entry_point": "fragment_main",
                "targets": [{"format": self.texture_format}],
            },
            primitive={"topology": self._get_primitive_topology()},
            depth_stencil={
                "format": self.depth_format,
                "depth_write_enabled": True,
                "depth_compare": wgpu.CompareFunction.less,
            },
            multisample={"count": self.msaa_sample_count},
        )

        # Create uniform buffer
        self.uniform_buffer = self.device.create_buffer_with_data(
            data=self.uniform_data.tobytes(),
            usage=int(wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST),
            label=f"{self._get_pipeline_label()}_uniform_buffer",
        )

        # Create bind group
        bind_group_layout = self.pipeline.get_bind_group_layout(0)
        self.bind_group = self.device.create_bind_group(
            layout=bind_group_layout,
            entries=[
                {
                    "binding": 0,
                    "resource": {"buffer": self.uniform_buffer},
                }
            ],
        )

    def _create_or_update_buffer(
        self,
        current_buffer: Optional[wgpu.GPUBuffer],
        data: Union[np.ndarray, wgpu.GPUBuffer],
        usage: wgpu.BufferUsage,
        buffer_label: str,
    ) -> Tuple[Optional[wgpu.GPUBuffer], int]:
        """Create or update a GPU buffer with new data.

        Args:
            current_buffer: Existing buffer (may be None)
            data: New data (numpy array or GPU buffer)
            usage: Buffer usage flags
            buffer_label: Label for the buffer

        Returns:
            Tuple of (buffer, data_size)
        """
        if isinstance(data, wgpu.GPUBuffer):
            # Use provided buffer directly
            return data, data.size

        # Handle numpy array
        data_bytes = data.astype(np.float32).tobytes()
        data_size = len(data_bytes)

        # Create new buffer if needed or existing one is too small
        if current_buffer is None or current_buffer.size < data_size:
            if current_buffer:
                current_buffer.destroy()
            buffer = self.device.create_buffer_with_data(
                data=data_bytes,
                usage=usage,
                label=buffer_label,
            )
            return buffer, data_size
        else:
            # Update existing buffer
            self.device.queue.write_buffer(current_buffer, 0, data_bytes)
            return current_buffer, data_size

    def _process_vertex_data(
        self,
        data: Optional[Union[np.ndarray, wgpu.GPUBuffer]],
        default_value: Optional[np.ndarray] = None,
        padding_size: Optional[int] = None,
        buffer_label: str = "vertex_buffer",
    ) -> Optional[Union[wgpu.GPUBuffer, Tuple[wgpu.GPUBuffer, int]]]:
        """Process vertex data, handling numpy arrays, GPU buffers, and defaults.

        Args:
            data: Input data (numpy array, GPU buffer, or None)
            default_value: Default value if data is None
            padding_size: Size to pad arrays to (for alignment)
            buffer_label: Label for created buffers

        Returns:
            Processed buffer(s) or None
        """
        if data is None and default_value is not None:
            data = default_value

        if data is None:
            return None

        if isinstance(data, wgpu.GPUBuffer):
            return data

        # Handle numpy array
        if padding_size:
            # Pad array to specified size
            if data.ndim == 1:
                padded_data = np.zeros(padding_size, dtype=np.float32)
                padded_data[: len(data)] = data.astype(np.float32)
            else:
                padded_data = np.zeros((data.shape[0], padding_size), dtype=np.float32)
                padded_data[:, : data.shape[1]] = data.astype(np.float32)
            data = padded_data

        buffer, _ = self._create_or_update_buffer(
            None,  # Always create new for processed data
            data,
            wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
            buffer_label,
        )
        return buffer

    @abstractmethod
    def set_data(self, **kwargs: Any) -> None:
        """Set rendering data (vertices, colours, etc.).

        Args:
            **kwargs: Pipeline-specific data parameters
        """
        pass

    @abstractmethod
    def update_uniforms(self, **kwargs: Any) -> None:
        """Update uniform buffer values.

        Args:
            **kwargs: Pipeline-specific uniform parameters
        """
        pass

    @abstractmethod
    def render(self, render_pass: wgpu.GPURenderPassEncoder, **kwargs: Any) -> None:
        """Render using this pipeline.

        Args:
            render_pass: Active render pass encoder
            **kwargs: Pipeline-specific render parameters
        """
        pass

    def cleanup(self) -> None:
        """Release pipeline resources. Can be overridden for additional cleanup."""
        if self.uniform_buffer:
            self.uniform_buffer.destroy()


class BasePointPipeline(BaseWebGPUPipeline):
    """Base class for point rendering pipelines.

    Provides common functionality for:
    - Point billboarding
    - Quad generation
    - Circle clipping in fragment shader
    """

    def _get_primitive_topology(self) -> wgpu.PrimitiveTopology:
        """Points are rendered as triangle strips for quad generation."""
        return wgpu.PrimitiveTopology.triangle_strip

    def _get_default_vertex_layouts(
        self, has_colour_buffer: bool = False
    ) -> List[Dict[str, Any]]:
        """Get default vertex buffer layouts for point rendering.

        Args:
            has_colour_buffer: Whether to include colour buffer layout

        Returns:
            List of vertex buffer layout configurations
        """
        layouts = [
            {
                "array_stride": self._stride,
                "step_mode": "instance",
                "attributes": [
                    {
                        "format": NGLToWebGPU.vertex_format(self._data_type),
                        "offset": 0,
                        "shader_location": 0,
                    },
                ],
            },
        ]

        if has_colour_buffer:
            layouts.append(
                {
                    "array_stride": NGLToWebGPU.stride_from_type("Vec3"),
                    "step_mode": "instance",
                    "attributes": [
                        {
                            "format": NGLToWebGPU.vertex_format("Vec3"),
                            "offset": 0,
                            "shader_location": 1,
                        },
                    ],
                }
            )

        return layouts

    def _render_points(
        self,
        render_pass: wgpu.GPURenderPassEncoder,
        position_buffer: wgpu.GPUBuffer,
        colour_buffer: Optional[wgpu.GPUBuffer] = None,
        num_points: Optional[int] = None,
    ) -> None:
        """Common point rendering implementation.

        Args:
            render_pass: Active render pass encoder
            position_buffer: Buffer containing point positions
            colour_buffer: Optional buffer containing point colours
            num_points: Number of points to render
        """
        if position_buffer is None:
            return

        count = num_points if num_points is not None else getattr(self, "num_points", 0)

        render_pass.set_pipeline(self.pipeline)
        render_pass.set_bind_group(0, self.bind_group, [], 0, 999999)
        render_pass.set_vertex_buffer(0, position_buffer)

        if colour_buffer:
            render_pass.set_vertex_buffer(1, colour_buffer)

        # 4 vertices per quad for point rendering
        render_pass.draw(4, count)
