"""Custom WebGPU pipeline that accepts user-provided shader source files.

Provides flexibility for users to write their own WGSL shaders.
"""

import os
from typing import Any, Dict, List, Optional, Union

import numpy as np
import wgpu

from .base_webgpu_pipeline import BaseWebGPUPipeline
from .webgpu_constants import NGLToWebGPU


class CustomShaderPipeline(BaseWebGPUPipeline):
    """A WebGPU pipeline that uses custom shader source provided by the user.

    This pipeline allows users to provide their own WGSL shader source code
    while handling the boilerplate for buffer management, uniform updates,
    and rendering setup.
    """

    def __init__(
        self,
        device: wgpu.GPUDevice,
        shader_source: str,
        vertex_formats: Optional[List[Union[str, wgpu.VertexFormat]]] = None,
        primitive_topology: wgpu.PrimitiveTopology = wgpu.PrimitiveTopology.triangle_list,
        texture_format: wgpu.TextureFormat = wgpu.TextureFormat.rgba8unorm,
        depth_format: wgpu.TextureFormat = wgpu.TextureFormat.depth24plus,
        msaa_sample_count: int = 4,
        uniform_struct_definition: Optional[str] = None,
        pipeline_label: str = "CustomShaderPipeline",
    ) -> None:
        """Initialize custom shader pipeline.

        Args:
            device: WebGPU device
            shader_source: WGSL shader source code as string
            vertex_formats: List of vertex data formats (e.g., ["Vec3", "Vec3"] for position+colour)
            primitive_topology: Primitive topology for rendering
            texture_format: Colour attachment format
            depth_format: Depth attachment format
            msaa_sample_count: Number of MSAA samples
            uniform_struct_definition: Custom uniform struct definition (optional)
            pipeline_label: Label for debugging
        """
        self._shader_source = shader_source
        self._vertex_formats = vertex_formats or ["Vec3"]
        self._primitive_topology = primitive_topology
        self._uniform_struct_definition = uniform_struct_definition
        self._pipeline_label = pipeline_label

        # Calculate stride from vertex formats
        self._stride = sum(
            NGLToWebGPU.stride_from_type(fmt) for fmt in self._vertex_formats
        )

        # Initialize buffers storage
        self.vertex_buffers: Dict[int, wgpu.GPUBuffer] = {}
        self.num_vertices = 0

        # Call parent constructor after setting up our attributes
        super().__init__(
            device=device,
            texture_format=texture_format,
            depth_format=depth_format,
            msaa_sample_count=msaa_sample_count,
            data_type=self._vertex_formats[0],  # Use first format as default
            stride=self._stride,
        )

    def get_dtype(self) -> np.dtype:
        """Get the numpy dtype for the uniform buffer structure."""
        if self._uniform_struct_definition:
            # For custom uniforms, we need to parse the struct or use a default
            # For now, use a basic MVP + colour structure
            return np.dtype(
                [
                    ("MVP", np.float32, (4, 4)),
                    ("colour", np.float32, 4),
                ]
            )
        else:
            # Default uniform structure
            return np.dtype(
                [
                    ("MVP", np.float32, (4, 4)),
                    ("colour", np.float32, 4),
                ]
            )

    def _get_shader_code(self) -> str:
        """Return the custom shader source."""
        return self._shader_source

    def _get_vertex_buffer_layouts(self) -> List[Dict[str, any]]:
        """Get vertex buffer layouts based on provided vertex formats."""
        if len(self._vertex_formats) == 1:
            # Single interleaved buffer
            return [
                {
                    "array_stride": self._stride,
                    "step_mode": "vertex",
                    "attributes": [
                        {
                            "format": NGLToWebGPU.vertex_format(
                                self._vertex_formats[0]
                            ),
                            "offset": 0,
                            "shader_location": 0,
                        },
                    ],
                },
            ]
        else:
            # Multiple separate buffers or interleaved with multiple attributes
            layouts = []
            current_offset = 0

            for i, fmt in enumerate(self._vertex_formats):
                stride = NGLToWebGPU.stride_from_type(fmt)
                layouts.append(
                    {
                        "array_stride": stride,
                        "step_mode": "vertex",
                        "attributes": [
                            {
                                "format": NGLToWebGPU.vertex_format(fmt),
                                "offset": 0,
                                "shader_location": i,
                            },
                        ],
                    }
                )
                current_offset += stride

            return layouts

    def _get_primitive_topology(self) -> wgpu.PrimitiveTopology:
        """Return the primitive topology."""
        return self._primitive_topology

    def _set_default_uniforms(self) -> None:
        """Set default uniform values."""
        self.uniform_data["MVP"] = np.eye(4, dtype=np.float32)
        self.uniform_data["colour"] = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32)

    def _get_pipeline_label(self) -> str:
        """Return the pipeline label."""
        return self._pipeline_label

    def set_data(
        self,
        positions: Optional[np.ndarray] = None,
        colours: Optional[np.ndarray] = None,
        interleaved_data: Optional[np.ndarray] = None,
        **kwargs: Any,
    ) -> None:
        """Set vertex data for rendering.

        Args:
            positions: Vertex position data (N, 3)
            colours: Vertex colour data (N, 3) or (N, 4)
            interleaved_data: Pre-interleaved vertex data
            **kwargs: Additional vertex data arrays (e.g., velocities, life, initial_position)
        """
        if interleaved_data is not None:
            # Use pre-interleaved data
            buffer = self._create_or_update_buffer(
                self.vertex_buffers.get(0),
                interleaved_data,
                wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
                f"{self._pipeline_label}_vertex_buffer_0",
            )
            self.vertex_buffers[0] = buffer[0]
            self.num_vertices = len(interleaved_data)
        else:
            # Handle separate vertex data arrays
            binding = 0

            if positions is not None:
                buffer = self._create_or_update_buffer(
                    self.vertex_buffers.get(binding),
                    positions,
                    wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
                    f"{self._pipeline_label}_vertex_buffer_{binding}",
                )
                self.vertex_buffers[binding] = buffer[0]
                self.num_vertices = len(positions)
                binding += 1

            if colours is not None:
                buffer = self._create_or_update_buffer(
                    self.vertex_buffers.get(binding),
                    colours,
                    wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
                    f"{self._pipeline_label}_vertex_buffer_{binding}",
                )
                self.vertex_buffers[binding] = buffer[0]
                binding += 1

            # Handle additional vertex attributes (velocities, life, initial_position, etc.)
            for attr_name, attr_data in kwargs.items():
                if attr_data is not None:
                    buffer = self._create_or_update_buffer(
                        self.vertex_buffers.get(binding),
                        attr_data,
                        wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
                        f"{self._pipeline_label}_vertex_buffer_{binding}",
                    )
                    self.vertex_buffers[binding] = buffer[0]
                    binding += 1

    def update_uniforms(self, **kwargs: Any) -> None:
        """Update uniform buffer values.

        Args:
            **kwargs: Uniform values to update (e.g., mvp=matrix, colour=array)
        """
        if "mvp" in kwargs:
            self.uniform_data["MVP"] = kwargs["mvp"]

        if "colour" in kwargs:
            colour = kwargs["colour"]
            if len(colour) == 3:
                self.uniform_data["colour"] = np.array([*colour, 1.0], dtype=np.float32)
            else:
                self.uniform_data["colour"] = np.array(colour, dtype=np.float32)

        # Update the GPU buffer
        if self.uniform_buffer:
            self.device.queue.write_buffer(
                self.uniform_buffer, 0, self.uniform_data.tobytes()
            )

    def render(self, render_pass: wgpu.GPURenderPassEncoder, **kwargs: Any) -> None:
        """Render using this pipeline.

        Args:
            render_pass: Active render pass encoder
            **kwargs: Additional render parameters
        """
        if self.pipeline is None or self.num_vertices == 0:
            return

        render_pass.set_pipeline(self.pipeline)
        render_pass.set_bind_group(0, self.bind_group, [], 0, 999999)

        # Set vertex buffers
        for binding, buffer in self.vertex_buffers.items():
            render_pass.set_vertex_buffer(binding, buffer)

        # Draw
        render_pass.draw(self.num_vertices)

    @classmethod
    def from_file(
        cls, device: wgpu.GPUDevice, shader_file: str, **kwargs: Any
    ) -> "CustomShaderPipeline":
        """Create a CustomShaderPipeline from a WGSL file.

        Args:
            device: WebGPU device
            shader_file: Path to WGSL shader file
            **kwargs: Additional arguments to pass to constructor

        Returns:
            CustomShaderPipeline instance
        """
        if not os.path.exists(shader_file):
            raise FileNotFoundError(f"Shader file not found: {shader_file}")

        with open(shader_file, "r", encoding="utf-8") as f:
            shader_source = f.read()

        # Use filename as default pipeline label if not provided
        if "pipeline_label" not in kwargs:
            kwargs["pipeline_label"] = f"Custom_{os.path.basename(shader_file)}"

        return cls(device, shader_source, **kwargs)
