"""Instanced geometry rendering pipeline for WebGPU.
Renders multiple instances of the same geometry at different positions with optional per-instance colors.
"""

from typing import Optional

import numpy as np
import wgpu

from .base_webgpu_pipeline import BaseWebGPUPipeline
from .pipeline_shaders import (
    INSTANCED_SHADER_MULTI_COLOURED,
    INSTANCED_SHADER_SINGLE_COLOUR,
)
from .webgpu_constants import NGLToWebGPU

GEOM_ERROR = "geometry_data is required for instanced geometry pipelines"


class BaseInstancedGeometryPipeline(BaseWebGPUPipeline):
    """Base class for instanced geometry rendering pipelines.

    Provides common functionality for:
    - Instanced rendering of arbitrary geometry
    - Per-instance positioning
    - Optional per-instance colors
    - Geometry buffer management
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
        """Initialize the instanced geometry pipeline.

        Args:
            device: WebGPU device
            data_type: Instance position data type (e.g., "Vec3", "Vec2")
            texture_format: Color attachment format
            depth_format: Depth attachment format
            msaa_sample_count: Number of MSAA samples
            stride: The stride of the instance buffer. If 0, inferred from data_type.
        """
        # Pipeline-specific buffer tracking
        self.position_buffer: Optional[wgpu.GPUBuffer] = None
        self.colour_buffer: Optional[wgpu.GPUBuffer] = None
        self.instance_id_buffer: Optional[wgpu.GPUBuffer] = None
        self.geometry_buffer: Optional[wgpu.GPUBuffer] = (
            None  # Single interleaved buffer x,y,z,nx,ny,nz,u,v
        )
        self.num_instances: int = 0
        self.num_vertices: int = 0

        super().__init__(
            device=device,
            texture_format=texture_format,
            depth_format=depth_format,
            msaa_sample_count=msaa_sample_count,
            data_type=data_type,
            stride=stride,
        )

    def _get_primitive_topology(self) -> wgpu.PrimitiveTopology:
        """Default to triangle list for geometry rendering."""
        return wgpu.PrimitiveTopology.triangle_list

    def _get_default_vertex_layouts(self) -> list:
        """Get default vertex buffer layouts for instanced geometry rendering.

        Returns:
            List of vertex buffer layout configurations
        """
        layouts = [
            # Instance position buffer (step_mode="instance")
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

        # Always add colour buffer layout (used or not by shader)
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

        # Add instance ID buffer for potential use in shaders
        layouts.append(
            {
                "array_stride": 4,  # float32
                "step_mode": "instance",
                "attributes": [
                    {
                        "format": wgpu.VertexFormat.float32,
                        "offset": 0,
                        "shader_location": 2,
                    },
                ],
            }
        )

        # Single interleaved geometry buffer (step_mode="vertex")
        layouts.append(
            {
                "array_stride": 8 * 4,  # 8 floats * 4 bytes each
                "step_mode": "vertex",
                "attributes": [
                    {
                        "format": NGLToWebGPU.vertex_format("Vec3"),
                        "offset": 0,
                        "shader_location": 3,  # geometry_position
                    },
                    {
                        "format": NGLToWebGPU.vertex_format("Vec3"),
                        "offset": 3 * 4,  # 12 bytes offset
                        "shader_location": 4,  # geometry_normal
                    },
                    {
                        "format": NGLToWebGPU.vertex_format("Vec2"),
                        "offset": 6 * 4,  # 24 bytes offset
                        "shader_location": 5,  # geometry_uv
                    },
                ],
            }
        )

        return layouts

    def _create_instance_id_buffer(self, num_instances: int) -> wgpu.GPUBuffer:
        """Create a buffer containing instance IDs 0, 1, 2, ..."""
        instance_ids = np.arange(num_instances, dtype=np.float32)
        return self.device.create_buffer_with_data(
            data=instance_ids.tobytes(),
            usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
            label="instance_id_buffer",
        )


class InstancedGeometryPipelineMultiColour(BaseInstancedGeometryPipeline):
    """A reusable pipeline for rendering instanced geometry in WebGPU with per-instance colors.

    Features:
    - Instanced rendering of arbitrary geometry using interleaved x,y,z,nx,ny,nz,u,v format
    - Per-instance colors
    - Per-instance positioning
    - Configurable instance transformation matrix
    - Model, View Projection matrix support
    - MSAA support
    """

    def get_dtype(self) -> np.dtype:
        """Get the data type of the pipeline."""
        return np.dtype(
            [
                ("MVP", "float32", (4, 4)),
                ("ViewMatrix", "float32", (4, 4)),
                ("instance_transform", "float32", (4, 4)),
            ]
        )

    def _get_shader_code(self) -> str:
        """Get the WGSL shader code for this pipeline."""
        return INSTANCED_SHADER_MULTI_COLOURED

    def _get_vertex_buffer_layouts(self) -> list:
        """Get vertex buffer layout configurations for the pipeline."""
        return self._get_default_vertex_layouts()

    def _set_default_uniforms(self) -> None:
        """Set default values for uniform data."""
        self.uniform_data["instance_transform"] = np.eye(4, dtype=np.float32)
        self.uniform_data["ViewMatrix"] = np.eye(4, dtype=np.float32)

    def _get_pipeline_label(self) -> str:
        """Get the label for the pipeline."""
        return "instanced_geometry_pipeline_multi_colour"

    def set_data(self, **kwargs) -> None:
        """Set the instanced geometry data for rendering.

        Args:
            **kwargs: Pipeline-specific data parameters
                - positions: Nx3 array of instance positions or a pre-existing GPUBuffer.
                - colours: Nx3 array of instance colors (RGB) or a pre-existing GPUBuffer.
                           If None, uses white.
                - geometry_data: Mx8 array of interleaved geometry data in format
                                x,y,z,nx,ny,nz,u,v or pre-existing GPUBuffer.
                                Must match the format output by PrimData methods.
        """
        positions = kwargs.get("positions")
        colours = kwargs.get("colours")
        geometry_data = kwargs.get("geometry_data")

        self._set_position_data(positions)
        self._setup_instance_id_buffer()
        self._set_colour_data(colours)
        self._set_geometry_data(geometry_data)

    def _set_position_data(self, positions) -> None:
        """Set instance position data from GPUBuffer or numpy array."""
        if isinstance(positions, wgpu.GPUBuffer):
            self.position_buffer = positions
            self.num_instances = positions.size // self._stride
        else:
            self.num_instances = len(positions)
            if self.position_buffer:
                self.position_buffer.destroy()
            self.position_buffer = self.device.create_buffer_with_data(
                data=positions.astype(np.float32).tobytes(),
                usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
                label="instanced_geometry_multi_colour_position_buffer",
            )

    def _setup_instance_id_buffer(self) -> None:
        """Create buffer containing instance IDs."""
        if self.instance_id_buffer:
            self.instance_id_buffer.destroy()
        self.instance_id_buffer = super()._create_instance_id_buffer(self.num_instances)

    def _set_colour_data(self, colours) -> None:
        """Set colour data from GPUBuffer, numpy array, or create default."""
        if self.colour_buffer:
            self.colour_buffer.destroy()
            self.colour_buffer = None

        if colours is None:
            self._create_default_colours()
        else:
            self._create_colour_buffer(colours)

    def _create_default_colours(self) -> None:
        """Create default white colours for all instances."""
        default_colours = np.ones((self.num_instances, 3), dtype=np.float32)
        self.colour_buffer = self.device.create_buffer_with_data(
            data=default_colours.tobytes(),
            usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
        )

    def _create_colour_buffer(self, colours) -> None:
        """Create colour buffer from GPUBuffer or numpy array."""
        if isinstance(colours, wgpu.GPUBuffer):
            self.colour_buffer = colours
        else:
            colour_array = colours.astype(np.float32)
            self.colour_buffer = self.device.create_buffer_with_data(
                data=colour_array.tobytes(),
                usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
            )

    def _set_geometry_data(self, geometry_data) -> None:
        """Set geometry data from GPUBuffer or numpy array."""
        if geometry_data is None:
            raise ValueError(GEOM_ERROR)

        if isinstance(geometry_data, wgpu.GPUBuffer):
            self.geometry_buffer = geometry_data
            self.num_vertices = geometry_data.size // (8 * 4)
        else:
            self._process_geometry_array(geometry_data)

    def _process_geometry_array(self, geometry_data) -> None:
        """Process geometry numpy array and create buffer."""
        geometry_data = np.asarray(geometry_data, dtype=np.float32)
        geometry_data = self._validate_and_reshape_geometry(geometry_data)
        self.num_vertices = geometry_data.shape[0]

        if self.geometry_buffer:
            self.geometry_buffer.destroy()
        self.geometry_buffer = self.device.create_buffer_with_data(
            data=geometry_data.tobytes(),
            usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
            label="instanced_geometry_buffer",
        )

    def _validate_and_reshape_geometry(self, geometry_data) -> np.ndarray:
        """Validate geometry data dimensions and reshape if needed."""
        if geometry_data.ndim == 1:
            geometry_data = geometry_data.reshape(-1, 8)
        elif geometry_data.ndim != 2:
            raise ValueError(
                f"geometry_data must be 1D or 2D array, got {geometry_data.ndim}D"
            )

        if geometry_data.shape[1] != 8:
            raise ValueError(
                f"geometry_data must have 8 components (x,y,z,nx,ny,nz,u,v), got {geometry_data.shape[1]}"
            )

        return geometry_data

    def update_uniforms(self, **kwargs) -> None:
        """Update uniform buffer values.

        Args:
            **kwargs: Pipeline-specific uniform parameters
                - mvp: 4x4 model view projection matrix
                - view_matrix: 4x4 view matrix
                - instance_transform: 4x4 transformation matrix for each instance
        """
        if "mvp" in kwargs and kwargs["mvp"] is not None:
            self.uniform_data["MVP"] = kwargs["mvp"]

        if "view_matrix" in kwargs and kwargs["view_matrix"] is not None:
            self.uniform_data["ViewMatrix"] = kwargs["view_matrix"]

        if "instance_transform" in kwargs and kwargs["instance_transform"] is not None:
            self.uniform_data["instance_transform"] = kwargs["instance_transform"]

        self.device.queue.write_buffer(
            self.uniform_buffer, 0, self.uniform_data.tobytes()
        )

    def render(self, render_pass: wgpu.GPURenderPassEncoder, **kwargs) -> None:
        """Render the instanced geometry.

        Args:
            render_pass: Active render pass encoder
            **kwargs: Pipeline-specific render parameters
                - num_instances: Number of instances to render (defaults to all)
        """
        num_instances = kwargs.get("num_instances", None)

        if (
            self.position_buffer is None
            or self.colour_buffer is None
            or self.instance_id_buffer is None
            or self.geometry_buffer is None
        ):
            return

        count = num_instances if num_instances is not None else self.num_instances

        render_pass.set_pipeline(self.pipeline)
        if self.bind_group:
            render_pass.set_bind_group(0, self.bind_group, [], 0, 999999)

        # Set instance buffers (match shader layout)
        render_pass.set_vertex_buffer(0, self.position_buffer)  # location(0) position
        render_pass.set_vertex_buffer(1, self.colour_buffer)  # location(1) colour
        render_pass.set_vertex_buffer(
            2, self.instance_id_buffer
        )  # location(2) instance_id

        # Set single interleaved geometry buffer
        render_pass.set_vertex_buffer(
            3, self.geometry_buffer
        )  # locations(3,4,5) interleaved

        render_pass.draw(self.num_vertices, count)

    def cleanup(self) -> None:
        """Release resources."""
        if self.position_buffer:
            self.position_buffer.destroy()
        if self.colour_buffer:
            self.colour_buffer.destroy()
        if self.instance_id_buffer:
            self.instance_id_buffer.destroy()
        if self.geometry_buffer:
            self.geometry_buffer.destroy()

        super().cleanup()


class InstancedGeometryPipelineSingleColour(BaseInstancedGeometryPipeline):
    """A reusable pipeline for rendering instanced geometry in WebGPU with single color.

    Features:
    - Instanced rendering of arbitrary geometry using interleaved x,y,z,nx,ny,nz,u,v format
    - Single color for all instances
    - Per-instance positioning
    - Configurable instance transformation matrix
    - Model, View Projection matrix support
    - MSAA support
    """

    def get_dtype(self) -> np.dtype:
        """Get the data type of the pipeline."""
        return np.dtype(
            [
                ("MVP", "float32", (4, 4)),
                ("ViewMatrix", "float32", (4, 4)),
                ("colour", "float32", 4),  # Vec4 for alignment (RGB + padding)
                ("instance_transform", "float32", (4, 4)),
            ]
        )

    def _get_shader_code(self) -> str:
        """Get the WGSL shader code for this pipeline."""
        return INSTANCED_SHADER_SINGLE_COLOUR

    def _get_vertex_buffer_layouts(self) -> list:
        """Get vertex buffer layout configurations for the pipeline."""
        return self._get_default_vertex_layouts()

    def _set_default_uniforms(self) -> None:
        """Set default values for uniform data."""
        self.uniform_data["colour"] = np.array(
            [1.0, 1.0, 1.0, 1.0], dtype=np.float32
        )  # White
        self.uniform_data["instance_transform"] = np.eye(4, dtype=np.float32)
        self.uniform_data["ViewMatrix"] = np.eye(4, dtype=np.float32)

    def _get_pipeline_label(self) -> str:
        """Get the label for the pipeline."""
        return "instanced_geometry_pipeline_single_colour"

    def set_data(self, **kwargs) -> None:
        """Set the instanced geometry data for rendering.

        Args:
            **kwargs: Pipeline-specific data parameters
                - positions: Nx3 array of instance positions or a pre-existing GPUBuffer.
                - colours: Nx3 array of instance colors (RGB) or a pre-existing GPUBuffer.
                           If None, uses white.
                - geometry_data: Mx8 array of interleaved geometry data in format
                                x,y,z,nx,ny,nz,u,v or pre-existing GPUBuffer.
                                Must match the format output by PrimData methods.
        """
        positions = kwargs.get("positions")
        colours = kwargs.get("colours")
        geometry_data = kwargs.get("geometry_data")

        self._set_position_data(positions)
        self._setup_instance_id_buffer()
        self._set_colour_data(colours)
        self._set_geometry_data(geometry_data)

    def _set_position_data(self, positions) -> None:
        """Set instance position data from GPUBuffer or numpy array."""
        if isinstance(positions, wgpu.GPUBuffer):
            self.position_buffer = positions
            self.num_instances = positions.size // self._stride
        else:
            self.num_instances = len(positions)
            if self.position_buffer:
                self.position_buffer.destroy()
            self.position_buffer = self.device.create_buffer_with_data(
                data=positions.astype(np.float32).tobytes(),
                usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
                label="instanced_geometry_multi_colour_position_buffer",
            )

    def _setup_instance_id_buffer(self) -> None:
        """Create buffer containing instance IDs."""
        if self.instance_id_buffer:
            self.instance_id_buffer.destroy()
        self.instance_id_buffer = super()._create_instance_id_buffer(self.num_instances)

    def _set_colour_data(self, colours) -> None:
        """Set colour data from GPUBuffer, numpy array, or create default."""
        if self.colour_buffer:
            self.colour_buffer.destroy()
            self.colour_buffer = None

        if colours is None:
            self._create_default_colours()
        else:
            self._create_colour_buffer(colours)

    def _create_default_colours(self) -> None:
        """Create default white colours for all instances."""
        default_colours = np.ones((self.num_instances, 3), dtype=np.float32)
        self.colour_buffer = self.device.create_buffer_with_data(
            data=default_colours.tobytes(),
            usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
        )

    def _create_colour_buffer(self, colours) -> None:
        """Create colour buffer from GPUBuffer or numpy array."""
        if isinstance(colours, wgpu.GPUBuffer):
            self.colour_buffer = colours
        else:
            colour_array = colours.astype(np.float32)
            self.colour_buffer = self.device.create_buffer_with_data(
                data=colour_array.tobytes(),
                usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
            )

    def _set_geometry_data(self, geometry_data) -> None:
        """Set geometry data from GPUBuffer or numpy array."""
        if geometry_data is None:
            raise ValueError(GEOM_ERROR)

        if isinstance(geometry_data, wgpu.GPUBuffer):
            self.geometry_buffer = geometry_data
            self.num_vertices = geometry_data.size // (8 * 4)
        else:
            self._process_geometry_array(geometry_data)

    def _process_geometry_array(self, geometry_data) -> None:
        """Process geometry numpy array and create buffer."""
        geometry_data = np.asarray(geometry_data, dtype=np.float32)
        geometry_data = self._validate_and_reshape_geometry(geometry_data)
        self.num_vertices = geometry_data.shape[0]

        if self.geometry_buffer:
            self.geometry_buffer.destroy()
        self.geometry_buffer = self.device.create_buffer_with_data(
            data=geometry_data.tobytes(),
            usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
            label="instanced_geometry_buffer",
        )

    def _validate_and_reshape_geometry(self, geometry_data) -> np.ndarray:
        """Validate geometry data dimensions and reshape if needed."""
        if geometry_data.ndim == 1:
            geometry_data = geometry_data.reshape(-1, 8)
        elif geometry_data.ndim != 2:
            raise ValueError(
                f"geometry_data must be 1D or 2D array, got {geometry_data.ndim}D"
            )

        if geometry_data.shape[1] != 8:
            raise ValueError(
                f"geometry_data must have 8 components (x,y,z,nx,ny,nz,u,v), got {geometry_data.shape[1]}"
            )

        return geometry_data

    def update_uniforms(self, **kwargs) -> None:
        """Update uniform buffer values.

        Args:
            **kwargs: Pipeline-specific uniform parameters
                - mvp: 4x4 model view projection matrix
                - view_matrix: 4x4 view matrix
                - colour: 3-element array of RGB color values
                - instance_transform: 4x4 transformation matrix for each instance
        """
        if "mvp" in kwargs and kwargs["mvp"] is not None:
            self.uniform_data["MVP"] = kwargs["mvp"]

        if "view_matrix" in kwargs and kwargs["view_matrix"] is not None:
            self.uniform_data["ViewMatrix"] = kwargs["view_matrix"]

        if "colour" in kwargs and kwargs["colour"] is not None:
            self.uniform_data["colour"][:3] = kwargs["colour"]

        if "instance_transform" in kwargs and kwargs["instance_transform"] is not None:
            self.uniform_data["instance_transform"] = kwargs["instance_transform"]

        self.device.queue.write_buffer(
            self.uniform_buffer, 0, self.uniform_data.tobytes()
        )

    def render(self, render_pass: wgpu.GPURenderPassEncoder, **kwargs) -> None:
        """Render the instanced geometry.

        Args:
            render_pass: Active render pass encoder
            **kwargs: Pipeline-specific render parameters
                - num_instances: Number of instances to render (defaults to all)
        """
        num_instances = kwargs.get("num_instances", None)

        if (
            self.position_buffer is None
            or self.colour_buffer is None
            or self.instance_id_buffer is None
            or self.geometry_buffer is None
        ):
            return

        count = num_instances if num_instances is not None else self.num_instances

        render_pass.set_pipeline(self.pipeline)
        if self.bind_group:
            render_pass.set_bind_group(0, self.bind_group, [], 0, 999999)

        # Set instance buffers (must match base class layout)
        render_pass.set_vertex_buffer(0, self.position_buffer)
        render_pass.set_vertex_buffer(1, self.colour_buffer)  # Dummy colour buffer
        render_pass.set_vertex_buffer(2, self.instance_id_buffer)

        # Set single interleaved geometry buffer
        render_pass.set_vertex_buffer(
            3, self.geometry_buffer
        )  # locations(3,4,5) interleaved

        render_pass.draw(self.num_vertices, count)

    def cleanup(self) -> None:
        """Release resources."""
        if self.position_buffer:
            self.position_buffer.destroy()
        if self.colour_buffer:
            self.colour_buffer.destroy()
        if self.instance_id_buffer:
            self.instance_id_buffer.destroy()
        if self.geometry_buffer:
            self.geometry_buffer.destroy()

        super().cleanup()
