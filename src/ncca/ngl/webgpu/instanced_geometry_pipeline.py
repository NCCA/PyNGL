"""
Instanced geometry rendering pipeline for WebGPU.
Renders multiple instances of the same geometry at different positions with optional per-instance colors.
"""

from typing import Optional

import numpy as np
import wgpu

from .base_webgpu_pipeline import BaseWebGPUPipeline
from .webgpu_constants import NGLToWebGPU

_INSTANCED_SHADER_MULTI_COLOURED = """
@group(0) @binding(0) var<uniform> uniforms : Uniforms;
struct Uniforms
{
    MVP : mat4x4<f32>,
    ViewMatrix : mat4x4<f32>,
    instance_transform: mat4x4<f32>,
};

struct InstanceData {
    @location(0) position: vec3<f32>,
    @location(1) colour: vec3<f32>,
    @location(2) instance_id: f32,
};

struct GeometryVertex {
    @location(3) geometry_position: vec3<f32>,
    @location(4) geometry_normal: vec3<f32>,
    @location(5) geometry_uv: vec2<f32>,
};

struct VertexOut {
    @builtin(position) position: vec4<f32>,
    @location(0) fragColour: vec3<f32>,
    @location(1) fragNormal: vec3<f32>,
    @location(2) fragUV: vec2<f32>,
    @location(3) worldPos: vec3<f32>,
};

@vertex
fn vertex_main(instance_data: InstanceData, geom_vertex: GeometryVertex, @builtin(vertex_index) vertex_index: u32) -> VertexOut {
    var output: VertexOut;

    // Transform geometry vertex by instance transform and position
    let transformed_vertex = uniforms.instance_transform * vec4<f32>(geom_vertex.geometry_position, 1.0);
    let world_position = transformed_vertex.xyz + instance_data.position;

    output.position = uniforms.MVP * vec4<f32>(world_position, 1.0);
    output.fragColour = instance_data.colour;

    // Transform normal by instance transform (skip translation)
    let normal_matrix = mat3x3<f32>(
        uniforms.instance_transform[0].xyz,
        uniforms.instance_transform[1].xyz,
        uniforms.instance_transform[2].xyz
    );
    output.fragNormal = normalize(normal_matrix * geom_vertex.geometry_normal);
    output.fragUV = geom_vertex.geometry_uv;
    output.worldPos = world_position;

    return output;
}

@fragment
fn fragment_main(fragData: VertexOut) -> @location(0) vec4<f32>
{
    // Enhanced diffuse lighting calculation

    // Light properties
    let light_direction = normalize(vec3<f32>(0.5, 1.0, 0.3));  // World space light direction
    let light_color = vec3<f32>(1.0, 1.0, 1.0);  // White light
    let ambient_intensity = 0.15;  // Lower ambient for better contrast
    let diffuse_intensity = 0.85;  // Higher diffuse for stronger lighting

    // Ambient component (base illumination)
    let ambient = vec3<f32>(ambient_intensity);

    // Diffuse component (Lambertian reflection)
    let normal = normalize(fragData.fragNormal);
    let n_dot_l = max(dot(normal, light_direction), 0.0);
    let diffuse = light_color * n_dot_l * diffuse_intensity;

    // Combine lighting components
    let final_lighting = ambient + diffuse;

    // Apply lighting to the fragment color
    let lit_color = fragData.fragColour * final_lighting;

    return vec4<f32>(lit_color, 1.0);
}
"""

_INSTANCED_SHADER_SINGLE_COLOUR = """
@group(0) @binding(0) var<uniform> uniforms : Uniforms;
struct Uniforms
{
    MVP : mat4x4<f32>,
    ViewMatrix : mat4x4<f32>,
    colour: vec3<f32>,
    padding: f32,
    instance_transform: mat4x4<f32>,
};

struct InstanceData {
    @location(0) position: vec3<f32>,
    @location(1) instance_id: f32,
    @location(2) colour: vec3<f32>,  // Provided but ignored
};

struct GeometryVertexSingle {
    @location(3) geometry_position: vec3<f32>,
    @location(4) geometry_normal: vec3<f32>,
    @location(5) geometry_uv: vec2<f32>,
};

struct VertexOutSingle {
    @builtin(position) position: vec4<f32>,
    @location(0) fragNormal: vec3<f32>,
    @location(1) fragUV: vec2<f32>,
    @location(2) worldPos: vec3<f32>,
};

@vertex
fn vertex_main(instance_data: InstanceData, geom_vertex: GeometryVertexSingle, @builtin(vertex_index) vertex_index: u32) -> VertexOutSingle {
    var output: VertexOutSingle;

    // Transform geometry vertex by instance transform and position
    let transformed_vertex = uniforms.instance_transform * vec4<f32>(geom_vertex.geometry_position, 1.0);
    let world_position = transformed_vertex.xyz + instance_data.position;

    output.position = uniforms.MVP * vec4<f32>(world_position, 1.0);

    // Transform normal by instance transform (skip translation)
    let normal_matrix = mat3x3<f32>(
        uniforms.instance_transform[0].xyz,
        uniforms.instance_transform[1].xyz,
        uniforms.instance_transform[2].xyz
    );
    output.fragNormal = normalize(normal_matrix * geom_vertex.geometry_normal);
    output.fragUV = geom_vertex.geometry_uv;
    output.worldPos = world_position;

    return output;
}

@fragment
fn fragment_main(fragData: VertexOutSingle) -> @location(0) vec4<f32>
{
    // Enhanced diffuse lighting calculation

    // Light properties
    let light_direction = normalize(vec3<f32>(0.5, 1.0, 0.3));  // World space light direction
    let light_color = vec3<f32>(1.0, 1.0, 1.0);  // White light
    let ambient_intensity = 0.15;  // Lower ambient for better contrast
    let diffuse_intensity = 0.85;  // Higher diffuse for stronger lighting

    // Ambient component (base illumination)
    let ambient = vec3<f32>(ambient_intensity);

    // Diffuse component (Lambertian reflection)
    let normal = normalize(fragData.fragNormal);
    let n_dot_l = max(dot(normal, light_direction), 0.0);
    let diffuse = light_color * n_dot_l * diffuse_intensity;

    // Combine lighting components
    let final_lighting = ambient + diffuse;

    // Apply lighting to the uniform color
    let lit_color = uniforms.colour * final_lighting;

    return vec4<f32>(lit_color, 1.0);
}
"""


class BaseInstancedGeometryPipeline(BaseWebGPUPipeline):
    """
    Base class for instanced geometry rendering pipelines.

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
        """
        Initialize the instanced geometry pipeline.

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
        self.geometry_buffer: Optional[wgpu.GPUBuffer] = None  # Single interleaved buffer x,y,z,nx,ny,nz,u,v
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
        """
        Get default vertex buffer layouts for instanced geometry rendering.



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
        layouts.append({
            "array_stride": NGLToWebGPU.stride_from_type("Vec3"),
            "step_mode": "instance",
            "attributes": [
                {
                    "format": NGLToWebGPU.vertex_format("Vec3"),
                    "offset": 0,
                    "shader_location": 1,
                },
            ],
        })

        # Add instance ID buffer for potential use in shaders
        layouts.append({
            "array_stride": 4,  # float32
            "step_mode": "instance",
            "attributes": [
                {
                    "format": wgpu.VertexFormat.float32,
                    "offset": 0,
                    "shader_location": 2,
                },
            ],
        })

        # Single interleaved geometry buffer (step_mode="vertex")
        layouts.append({
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
        })

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
    """
    A reusable pipeline for rendering instanced geometry in WebGPU with per-instance colors.

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
        return np.dtype([
            ("MVP", "float32", (4, 4)),
            ("ViewMatrix", "float32", (4, 4)),
            ("instance_transform", "float32", (4, 4)),
        ])

    def _get_shader_code(self) -> str:
        """Get the WGSL shader code for this pipeline."""
        return _INSTANCED_SHADER_MULTI_COLOURED

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

    def set_data(
        self,
        positions,
        colours=None,
        geometry_data=None,
    ) -> None:
        """
        Set the instanced geometry data for rendering.

        Args:
            positions: Nx3 array of instance positions or a pre-existing GPUBuffer.
            colours: Nx3 array of instance colors (RGB) or a pre-existing GPUBuffer.
                     If None, uses white.
            geometry_data: Mx8 array of interleaved geometry data in format
                          x,y,z,nx,ny,nz,u,v or pre-existing GPUBuffer.
                          Must match the format output by PrimData methods.
        """
        # Handle instance positions
        if isinstance(positions, wgpu.GPUBuffer):
            self.position_buffer = positions
            self.num_instances = positions.size // self._stride
        else:  # numpy array
            self.num_instances = len(positions)
            # Always recreate to avoid caching issues
            if self.position_buffer:
                self.position_buffer.destroy()
            self.position_buffer = self.device.create_buffer_with_data(
                data=positions.astype(np.float32).tobytes(),
                usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
                label="instanced_geometry_multi_colour_position_buffer",
            )

        # Create instance ID buffer
        if self.instance_id_buffer:
            self.instance_id_buffer.destroy()
        self.instance_id_buffer = self._create_instance_id_buffer(self.num_instances)

        # Handle colours - always recreate to avoid stale buffer issues
        if self.colour_buffer:
            self.colour_buffer.destroy()
            self.colour_buffer = None  # Clear reference immediately

        if colours is None:
            # Create default white colours
            default_colours = np.ones((self.num_instances, 3), dtype=np.float32)
            self.colour_buffer = self.device.create_buffer_with_data(
                data=default_colours.tobytes(),
                usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
            )
        else:
            # Colors are already (num_instances, 3), create buffer directly
            if isinstance(colours, wgpu.GPUBuffer):
                self.colour_buffer = colours
            else:
                colour_array = colours.astype(np.float32)
                self.colour_buffer = self.device.create_buffer_with_data(
                    data=colour_array.tobytes(),
                    usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
                )

        # Handle geometry data (required, interleaved format x,y,z,nx,ny,nz,u,v)
        if geometry_data is None:
            raise ValueError("geometry_data is required for instanced geometry pipelines")

        if isinstance(geometry_data, wgpu.GPUBuffer):
            # Use GPU buffer directly
            self.geometry_buffer = geometry_data
            self.num_vertices = geometry_data.size // (8 * 4)  # 8 floats * 4 bytes each
        else:
            # Handle numpy array
            geometry_data = np.asarray(geometry_data, dtype=np.float32)
            if geometry_data.ndim == 1:
                geometry_data = geometry_data.reshape(-1, 8)
            elif geometry_data.ndim != 2:
                raise ValueError(f"geometry_data must be 1D or 2D array, got {geometry_data.ndim}D")

            if geometry_data.shape[1] != 8:
                raise ValueError(
                    f"geometry_data must have 8 components (x,y,z,nx,ny,nz,u,v), got {geometry_data.shape[1]}"
                )

            self.num_vertices = geometry_data.shape[0]  # Number of vertices

            # Create single interleaved buffer
            if self.geometry_buffer:
                self.geometry_buffer.destroy()
            self.geometry_buffer = self.device.create_buffer_with_data(
                data=geometry_data.tobytes(),
                usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
                label="instanced_geometry_buffer",
            )

    def update_uniforms(self, **kwargs) -> None:
        """
        Update uniform buffer values.

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

        self.device.queue.write_buffer(self.uniform_buffer, 0, self.uniform_data.tobytes())

    def render(self, render_pass: wgpu.GPURenderPassEncoder, **kwargs) -> None:
        """
        Render the instanced geometry.

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
        render_pass.set_vertex_buffer(2, self.instance_id_buffer)  # location(2) instance_id

        # Set single interleaved geometry buffer
        render_pass.set_vertex_buffer(3, self.geometry_buffer)  # locations(3,4,5) interleaved

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
    """
    A reusable pipeline for rendering instanced geometry in WebGPU with single color.

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
        return np.dtype([
            ("MVP", "float32", (4, 4)),
            ("ViewMatrix", "float32", (4, 4)),
            ("colour", "float32", 4),  # Vec4 for alignment (RGB + padding)
            ("instance_transform", "float32", (4, 4)),
        ])

    def _get_shader_code(self) -> str:
        """Get the WGSL shader code for this pipeline."""
        return _INSTANCED_SHADER_SINGLE_COLOUR

    def _get_vertex_buffer_layouts(self) -> list:
        """Get vertex buffer layout configurations for the pipeline."""
        return self._get_default_vertex_layouts()

    def _set_default_uniforms(self) -> None:
        """Set default values for uniform data."""
        self.uniform_data["colour"] = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32)  # White
        self.uniform_data["instance_transform"] = np.eye(4, dtype=np.float32)
        self.uniform_data["ViewMatrix"] = np.eye(4, dtype=np.float32)

    def _get_pipeline_label(self) -> str:
        """Get the label for the pipeline."""
        return "instanced_geometry_pipeline_single_colour"

    def set_data(
        self,
        positions,
        geometry_data=None,
    ) -> None:
        """
        Set the instanced geometry data for rendering.

        Args:
            positions: Nx3 array of instance positions or a pre-existing GPUBuffer.
            geometry_data: Mx8 array of interleaved geometry data in format
                          x,y,z,nx,ny,nz,u,v or pre-existing GPUBuffer.
                          Must match the format output by PrimData methods.
        """
        # Handle instance positions
        if isinstance(positions, wgpu.GPUBuffer):
            self.position_buffer = positions
            self.num_instances = positions.size // self._stride
        else:  # numpy array
            self.num_instances = len(positions)
            self.position_buffer, _ = self._create_or_update_buffer(
                self.position_buffer,
                positions,
                wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
                "instanced_geometry_single_colour_position_buffer",
            )

        # Create instance ID buffer
        if self.instance_id_buffer:
            self.instance_id_buffer.destroy()
        self.instance_id_buffer = self._create_instance_id_buffer(self.num_instances)

        # Create dummy colour buffer for shader compatibility
        if self.colour_buffer:
            self.colour_buffer.destroy()
        default_colours = np.ones((self.num_instances, 3), dtype=np.float32)
        self.colour_buffer = self.device.create_buffer_with_data(
            data=default_colours.tobytes(),
            usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
        )

        # Handle geometry data (required, interleaved format x,y,z,nx,ny,nz,u,v)
        if geometry_data is None:
            raise ValueError("geometry_data is required for instanced geometry pipelines")

        if isinstance(geometry_data, wgpu.GPUBuffer):
            # Use GPU buffer directly
            self.geometry_buffer = geometry_data
            self.num_vertices = geometry_data.size // (8 * 4)  # 8 floats * 4 bytes each
        else:
            # Handle numpy array
            geometry_data = np.asarray(geometry_data, dtype=np.float32)
            if geometry_data.ndim == 1:
                geometry_data = geometry_data.reshape(-1, 8)
            elif geometry_data.ndim != 2:
                raise ValueError(f"geometry_data must be 1D or 2D array, got {geometry_data.ndim}D")

            if geometry_data.shape[1] != 8:
                raise ValueError(
                    f"geometry_data must have 8 components (x,y,z,nx,ny,nz,u,v), got {geometry_data.shape[1]}"
                )

            self.num_vertices = geometry_data.shape[0]  # Number of vertices

            # Create single interleaved buffer
            if self.geometry_buffer:
                self.geometry_buffer.destroy()
            self.geometry_buffer = self.device.create_buffer_with_data(
                data=geometry_data.tobytes(),
                usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
                label="instanced_geometry_buffer",
            )

    def update_uniforms(self, **kwargs) -> None:
        """
        Update uniform buffer values.

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

        self.device.queue.write_buffer(self.uniform_buffer, 0, self.uniform_data.tobytes())

    def render(self, render_pass: wgpu.GPURenderPassEncoder, **kwargs) -> None:
        """
        Render the instanced geometry.

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
        render_pass.set_vertex_buffer(3, self.geometry_buffer)  # locations(3,4,5) interleaved

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
