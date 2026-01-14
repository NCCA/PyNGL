"""
Generic point rendering pipeline for WebGPU.
Handles point rendering with customizable size, colour, and projection.
"""

from typing import Optional

import numpy as np
import wgpu

from .webgpu_constants import NGLToWebGPU

_POINT_SHADER_MULTI_COLOURED = """
@group(0) @binding(0) var<uniform> uniforms : Uniforms;
struct Uniforms
{
    MVP : mat4x4<f32>,
    ViewMatrix : mat4x4<f32>,
    size: f32,
};

struct VertexIn {
    @location(0) position: vec3<f32>,
    @location(1) colour: vec3<f32>,
};

// We now need to pass uv to the fragment shader
struct VertexOut {
    @builtin(position) position: vec4<f32>,
    @location(0) fragColour: vec3<f32>,
    @location(1) uv: vec2<f32>,
};

@vertex
fn vertex_main(input: VertexIn, @builtin(vertex_index) vertex_index: u32) -> VertexOut {
    var output: VertexOut;
    let quad_offsets = array<vec2<f32>, 4>(
        vec2<f32>(-1.0, -1.0), // bottom-left
        vec2<f32>(1.0, -1.0),  // bottom-right
        vec2<f32>(-1.0, 1.0),   // top-left
        vec2<f32>(1.0, 1.0)    // top-right
    );

    // Extract camera right and up vectors from view matrix
    let cameraRight = normalize(vec3<f32>(uniforms.ViewMatrix[0][0], uniforms.ViewMatrix[1][0], uniforms.ViewMatrix[2][0]));
    let cameraUp = normalize(vec3<f32>(uniforms.ViewMatrix[0][1], uniforms.ViewMatrix[1][1], uniforms.ViewMatrix[2][1]));

    // Calculate billboard offset in world space
    let offset2D = quad_offsets[vertex_index] * uniforms.size;
    let offset3D = cameraRight * offset2D.x + cameraUp * offset2D.y;
    let worldPos = input.position + offset3D;

    output.position = uniforms.MVP * vec4<f32>(worldPos, 1.0);
    output.fragColour = input.colour;
    // convert offset from -1 -> 1 to 0 -> 1 for uv
    output.uv = quad_offsets[vertex_index] * 0.5 + 0.5;

    return output;
}

@fragment
fn fragment_main(fragData: VertexOut) -> @location(0) vec4<f32>
{
    let center = vec2<f32>(0.5, 0.5); // Center of the quad in UV space
    let dist = distance(fragData.uv, center); // Distance from center
    let radius = 0.5; // Circle radius (quad is 1.0 in UV space)

    if (dist > radius)
    {
        discard; // Remove pixels outside the circle
    }

    return vec4<f32>(fragData.fragColour, 1.0); // Simple colour output
}
"""


class PointPipelineMultiColour:
    """
    A reusable pipeline for rendering points in WebGPU.

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
    ):
        """
        Initialize the point rendering pipeline.

        Args:
            device: WebGPU device
            texture_format: colour attachment format
            depth_format: Depth attachment format
            msaa_sample_count: Number of MSAA samples
            stride: The stride of the vertex buffer. If 0, it is inferred from data_type.
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
        # Buffers
        self.position_buffer: Optional[wgpu.GPUBuffer] = None
        self.colour_buffer: Optional[wgpu.GPUBuffer] = None
        self.uniform_buffer: Optional[wgpu.GPUBuffer] = None
        self.bind_group: Optional[wgpu.GPUBindGroup] = None

        # Uniform data
        self.uniform_data = np.zeros(
            (),
            dtype=[
                ("MVP", "float32", (4, 4)),
                ("ViewMatrix", "float32", (4, 4)),
                ("size", "float32"),
                ("padding", np.uint32, 3),
            ],
        )
        self.uniform_data["size"] = 1.0  # Default point size

        # Create the pipeline
        self._create_pipeline()

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

    def _create_pipeline(self) -> None:
        """Create the render pipeline and buffers."""
        # Load shader
        shader_module = self.device.create_shader_module(
            code=_POINT_SHADER_MULTI_COLOURED
        )

        # Create render pipeline
        self.pipeline = self.device.create_render_pipeline(
            label="point_pipeline_multi_coloured",
            layout="auto",
            vertex={
                "module": shader_module,
                "entry_point": "vertex_main",
                "buffers": [
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
                    },
                ],
            },
            fragment={
                "module": shader_module,
                "entry_point": "fragment_main",
                "targets": [{"format": self.texture_format}],
            },
            primitive={"topology": wgpu.PrimitiveTopology.triangle_strip},
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
            usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST,
            label="point_pipeline_multi_coloured_uniform_buffer",
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

    def _add_point_data(self, positions):
        if isinstance(positions, wgpu.GPUBuffer):
            # If a buffer is passed, we just use it.
            # Note: The old buffer is not destroyed, it is up to the caller to manage it.
            self.position_buffer = positions
            self.num_points = positions.size // self._stride
        else:  # numpy array
            self.num_points = len(positions)
            data_bytes = positions.astype(np.float32).tobytes()
            # Ensure buffer exists and is large enough
            if self.position_buffer is None or self.position_buffer.size < len(
                data_bytes
            ):
                if self.position_buffer:
                    self.position_buffer.destroy()
                self.position_buffer = self.device.create_buffer_with_data(
                    data=data_bytes,
                    usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
                )
            else:
                self.device.queue.write_buffer(self.position_buffer, 0, data_bytes)

    def _add_colour_data(self, colours):
        if isinstance(colours, wgpu.GPUBuffer):
            self.colour_buffer = colours
        else:
            # We need to pad the colour data to match the 16-byte stride for vec3.
            # Create a new array with 4 components (RGBA) and copy RGB data.
            # The vertex format is float32x3, so only the first 3 components are used.
            padded_colours = np.zeros((self.num_points, 4), dtype=np.float32)
            if colours is not None:  # numpy array
                padded_colours[:, :3] = colours.astype(np.float32)
            else:  # colours is None, create default white colours
                padded_colours[:, :3] = 1.0

            colours_bytes = padded_colours.tobytes()
            # Ensure buffer exists and is large enough
            if self.colour_buffer is None or self.colour_buffer.size < len(
                colours_bytes
            ):
                if self.colour_buffer:
                    self.colour_buffer.destroy()
                self.colour_buffer = self.device.create_buffer_with_data(
                    data=colours_bytes,
                    usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
                )
            else:
                self.device.queue.write_buffer(self.colour_buffer, 0, colours_bytes)

    def set_data(
        self,
        positions: np.ndarray | wgpu.GPUBuffer,
        colours: Optional[np.ndarray | wgpu.GPUBuffer] = None,
    ) -> None:
        """
        Set the point data for rendering.

        Args:
            positions: Nx2 array of point positions or a pre-existing GPUBuffer.
            colours: Nx3 array of point colours (RGB) or a pre-existing GPUBuffer.
                    If None, uses white.
        """
        # Handle positions
        self._add_point_data(positions)
        # Handle colours
        self._add_colour_data(colours)

    def update_uniforms(
        self,
        mvp: Optional[np.ndarray] = None,
        view_matrix: Optional[np.ndarray] = None,
        point_size: Optional[float] = None,
    ) -> None:
        """
        Update uniform buffer values.

        Args:
            mvp: 4x4 model view projection matrix (can just be projection if 2D)
            view_matrix: 4x4 view matrix for billboarding calculations
            point_size: Size of points in world units
        """
        if mvp is not None:
            self.uniform_data["MVP"] = mvp

        if view_matrix is not None:
            self.uniform_data["ViewMatrix"] = view_matrix

        if point_size is not None:
            self.uniform_data["size"] = point_size

        self.device.queue.write_buffer(
            self.uniform_buffer, 0, self.uniform_data.tobytes()
        )

    def render(
        self, render_pass: wgpu.GPURenderPassEncoder, num_points: Optional[int] = None
    ) -> None:
        """
        Render the points.

        Args:
            render_pass: Active render pass encoder
            num_points: Number of points to render (defaults to all)
        """
        if self.position_buffer is None or self.colour_buffer is None:
            return

        count = num_points if num_points is not None else self.num_points

        render_pass.set_pipeline(self.pipeline)
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
        if self.uniform_buffer:
            self.uniform_buffer.destroy()


_POINT_SHADER_SINGLE_COLOUR = """
@group(0) @binding(0) var<uniform> uniforms : Uniforms;
struct Uniforms
{
    MVP : mat4x4<f32>,
    ViewMatrix : mat4x4<f32>,
    ColourSize: vec4<f32>,

};

struct VertexIn {
    @location(0) position: vec3<f32>,
};

// We now need to pass uv to the fragment shader
struct VertexOut {
    @builtin(position) position: vec4<f32>,
    @location(1) uv: vec2<f32>,
};

@vertex
fn vertex_main(input: VertexIn, @builtin(vertex_index) vertex_index: u32) -> VertexOut {
    var output: VertexOut;
    let quad_offsets = array<vec2<f32>, 4>(
        vec2<f32>(-1.0, -1.0), // bottom-left
        vec2<f32>(1.0, -1.0),  // bottom-right
        vec2<f32>(-1.0, 1.0),   // top-left
        vec2<f32>(1.0, 1.0)    // top-right
    );

    // Extract camera right and up vectors from view matrix
    let cameraRight = normalize(vec3<f32>(uniforms.ViewMatrix[0][0], uniforms.ViewMatrix[1][0], uniforms.ViewMatrix[2][0]));
    let cameraUp = normalize(vec3<f32>(uniforms.ViewMatrix[0][1], uniforms.ViewMatrix[1][1], uniforms.ViewMatrix[2][1]));

    // Calculate billboard offset in world space
    let offset2D = quad_offsets[vertex_index] * uniforms.ColourSize.w;
    let offset3D = cameraRight * offset2D.x + cameraUp * offset2D.y;
    let worldPos = input.position + offset3D;

    output.position = uniforms.MVP * vec4<f32>(worldPos, 1.0);
    // convert offset from -1 -> 1 to 0 -> 1 for uv
    output.uv = quad_offsets[vertex_index] * 0.5 + 0.5;

    return output;
}

@fragment
fn fragment_main(fragData: VertexOut) -> @location(0) vec4<f32>
{
    let center = vec2<f32>(0.5, 0.5); // Center of the quad in UV space
    let dist = distance(fragData.uv, center); // Distance from center
    let radius = 0.5; // Circle radius (quad is 1.0 in UV space)

    if (dist > radius)
    {
        discard; // Remove pixels outside the circle
    }

    return vec4<f32>(uniforms.ColourSize.xyz, 1.0); // Simple colour output
}
"""


class PointPipelineSingleColour:
    """
    A reusable pipeline for rendering points in WebGPU.

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
    ):
        """
        Initialize the point rendering pipeline.

        Args:
            device: WebGPU device
            texture_format: colour attachment format
            depth_format: Depth attachment format
            msaa_sample_count: Number of MSAA samples
            stride: The stride of the vertex buffer. If 0, it is inferred from data_type.
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
        # Buffers
        self.position_buffer: Optional[wgpu.GPUBuffer] = None
        self.colour_buffer: Optional[wgpu.GPUBuffer] = None
        self.uniform_buffer: Optional[wgpu.GPUBuffer] = None
        self.bind_group: Optional[wgpu.GPUBindGroup] = None

        # Uniform data
        self.uniform_data = np.zeros((), dtype=self.get_dtype())
        self.uniform_data["ColourSize"] = np.array(
            [1.0, 1.0, 1.0, 1.0], dtype=np.float32
        )  # Default White with point size 1

        # Create the pipeline
        self._create_pipeline()

    def get_dtype(self) -> np.dtype:
        """Get the data type of the pipeline."""
        return np.dtype(
            [
                ("MVP", "float32", (4, 4)),
                ("ViewMatrix", "float32", (4, 4)),
                ("ColourSize", "float32", 4),
            ]
        )

    def _create_pipeline(self) -> None:
        """Create the render pipeline and buffers."""
        # Load shader
        shader_module = self.device.create_shader_module(
            code=_POINT_SHADER_SINGLE_COLOUR
        )

        # Create render pipeline
        self.pipeline = self.device.create_render_pipeline(
            label="point_pipeline_single_colour",
            layout="auto",
            vertex={
                "module": shader_module,
                "entry_point": "vertex_main",
                "buffers": [
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
                ],
            },
            fragment={
                "module": shader_module,
                "entry_point": "fragment_main",
                "targets": [{"format": self.texture_format}],
            },
            primitive={"topology": wgpu.PrimitiveTopology.triangle_strip},
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
            usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST,
            label="point_pipeline_single_colour_uniform_buffer",
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

    def _add_point_data(self, positions):
        if isinstance(positions, wgpu.GPUBuffer):
            # If a buffer is passed, we just use it.
            # Note: The old buffer is not destroyed, it is up to the caller to manage it.
            self.position_buffer = positions
            self.num_points = positions.size // self._stride
        else:  # numpy array
            self.num_points = len(positions)
            data_bytes = positions.astype(np.float32).tobytes()
            # Ensure buffer exists and is large enough
            if self.position_buffer is None or self.position_buffer.size < len(
                data_bytes
            ):
                if self.position_buffer:
                    self.position_buffer.destroy()
                self.position_buffer = self.device.create_buffer_with_data(
                    data=data_bytes,
                    usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
                )
            else:
                self.device.queue.write_buffer(self.position_buffer, 0, data_bytes)

    def set_data(
        self,
        positions: np.ndarray | wgpu.GPUBuffer,
        colours: Optional[np.ndarray | wgpu.GPUBuffer] = None,
    ) -> None:
        """
        Set the point data for rendering.

        Args:
            positions: Nx2 array of point positions or a pre-existing GPUBuffer.
            colours: Nx3 array of point colours (RGB) or a pre-existing GPUBuffer.
                    If None, uses white.
        """
        # Handle positions
        self._add_point_data(positions)

    def update_uniforms(
        self,
        mvp: Optional[np.ndarray] = None,
        view_matrix: Optional[np.ndarray] = None,
        colour: Optional[np.ndarray] = None,
        point_size: Optional[float] = None,
    ) -> None:
        """
        Update uniform buffer values.

        Args:
            mvp: 4x4 model view projection matrix (can just be projection if 2D)
            view_matrix: 4x4 view matrix for billboarding calculations
            colour: 3-element array of RGB colour values
            point_size: Size of points in world units
        """
        if mvp is not None:
            self.uniform_data["MVP"] = mvp

        if view_matrix is not None:
            self.uniform_data["ViewMatrix"] = view_matrix

        if colour is not None:
            self.uniform_data["ColourSize"][:3] = colour

        if point_size is not None:
            self.uniform_data["ColourSize"][3] = point_size

        self.device.queue.write_buffer(
            self.uniform_buffer, 0, self.uniform_data.tobytes()
        )

    def render(
        self, render_pass: wgpu.GPURenderPassEncoder, num_points: Optional[int] = None
    ) -> None:
        """
        Render the points.

        Args:
            render_pass: Active render pass encoder
            num_points: Number of points to render (defaults to all)
        """
        if self.position_buffer is None or self.uniform_buffer is None:
            return

        count = num_points if num_points is not None else self.num_points

        render_pass.set_pipeline(self.pipeline)
        render_pass.set_bind_group(0, self.bind_group, [], 0, 999999)
        render_pass.set_vertex_buffer(0, self.position_buffer)
        render_pass.draw(4, count)  # 4 vertices per quad, instanced

    def cleanup(self) -> None:
        """Release resources."""
        if self.position_buffer:
            self.position_buffer.destroy()
        if self.uniform_buffer:
            self.uniform_buffer.destroy()
