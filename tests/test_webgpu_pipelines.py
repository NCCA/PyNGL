import numpy as np
import pytest
import wgpu
import wgpu.utils

from ncca.ngl.webgpu import PipelineFactory, PipelineType
from ncca.ngl.webgpu.instanced_geometry_pipeline import (
    InstancedGeometryPipelineMultiColour,
    InstancedGeometryPipelineSingleColour,
)
from ncca.ngl.webgpu.line_pipeline import (
    LinePipelineMultiColour,
    LinePipelineSingleColour,
)
from ncca.ngl.webgpu.point_list_pipeline import (
    PointListPipelineMultiColour,
    PointListPipelineSingleColour,
)
from ncca.ngl.webgpu.point_pipeline import (
    PointPipelineMultiColour,
    PointPipelineSingleColour,
)
from ncca.ngl.webgpu.triangle_pipeline import (
    TrianglePipelineMultiColour,
    TrianglePipelineSingleColour,
)

# Test data fixtures
TEST_POSITIONS = np.array(
    [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [-1.0, -1.0, 0.0]], dtype=np.float32
)
TEST_COLORS = np.array(
    [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], dtype=np.float32
)
TEST_MVP_MATRIX = np.eye(4, dtype=np.float32)

# Geometry test data for instanced rendering
TEST_GEOMETRY_VERTICES = np.array(
    [
        [0.0, 0.0, 0.0],  # Triangle vertex 1
        [1.0, 0.0, 0.0],  # Triangle vertex 2
        [0.5, 1.0, 0.0],  # Triangle vertex 3
    ],
    dtype=np.float32,
)

TEST_GEOMETRY_NORMALS = np.array(
    [
        [0.0, 0.0, 1.0],  # Normal for vertex 1
        [0.0, 0.0, 1.0],  # Normal for vertex 2
        [0.0, 0.0, 1.0],  # Normal for vertex 3
    ],
    dtype=np.float32,
)

TEST_GEOMETRY_UVS = np.array(
    [
        [0.5, 0.0],  # UV for vertex 1
        [1.0, 0.0],  # UV for vertex 2
        [0.5, 1.0],  # UV for vertex 3
    ],
    dtype=np.float32,
)


@pytest.fixture
def render_pass(webgpu_device):
    """Create a basic render pass for testing."""
    command_encoder = webgpu_device.create_command_encoder()
    texture = webgpu_device.create_texture(
        size=(100, 100),
        usage=wgpu.TextureUsage.RENDER_ATTACHMENT,
        format=wgpu.TextureFormat.rgba8unorm,
    )
    return command_encoder.begin_render_pass(
        color_attachments=[
            {
                "view": texture.create_view(),
                "load_op": "load",
                "store_op": "store",
            }
        ],
        depth_stencil_attachment={
            "view": webgpu_device.create_texture(
                size=(100, 100),
                usage=wgpu.TextureUsage.RENDER_ATTACHMENT,
                format=wgpu.TextureFormat.depth24plus,
            ).create_view(),
            "depth_load_op": "load",
            "depth_store_op": "store",
        },
    )


@pytest.mark.parametrize(
    "pipeline_type,expected_class",
    [
        (PipelineType.MULTI_COLOURED_POINTS, PointPipelineMultiColour),
        (PipelineType.SINGLE_COLOUR_POINTS, PointPipelineSingleColour),
        (PipelineType.MULTI_COLOURED_LINES, LinePipelineMultiColour),
        (PipelineType.SINGLE_COLOUR_LINES, LinePipelineSingleColour),
        (PipelineType.MULTI_COLOURED_TRIANGLES, TrianglePipelineMultiColour),
        (PipelineType.SINGLE_COLOUR_TRIANGLES, TrianglePipelineSingleColour),
        (PipelineType.TRIANGLE_LIST_MULTI_COLOURED, TrianglePipelineMultiColour),
        (PipelineType.TRIANGLE_LIST_SINGLE_COLOUR, TrianglePipelineSingleColour),
        (PipelineType.TRIANGLE_STRIP_MULTI_COLOURED, TrianglePipelineMultiColour),
        (PipelineType.TRIANGLE_STRIP_SINGLE_COLOUR, TrianglePipelineSingleColour),
        (PipelineType.POINT_LIST_MULTI_COLOURED, PointListPipelineMultiColour),
        (PipelineType.POINT_LIST_SINGLE_COLOUR, PointListPipelineSingleColour),
        (
            PipelineType.MULTI_COLOURED_INSTANCED_GEOMETRY,
            InstancedGeometryPipelineMultiColour,
        ),
        (
            PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY,
            InstancedGeometryPipelineSingleColour,
        ),
    ],
)
def test_pipeline_creation(webgpu_device, pipeline_type, expected_class):
    """Test that all pipeline types can be created and return correct class."""
    pipeline = PipelineFactory.create_pipeline(webgpu_device, pipeline_type)
    assert pipeline is not None
    assert isinstance(pipeline, expected_class)


def test_pipeline_set_data_with_numpy(webgpu_device):
    """Test pipeline set_data method with numpy arrays."""
    # Test multi-coloured points
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_POINTS
    )
    pipeline.set_data(positions=TEST_POSITIONS, colours=TEST_COLORS)

    assert getattr(pipeline, "position_buffer", None) is not None
    assert getattr(pipeline, "num_points", 0) == 3

    # Test single-coloured points
    pipeline2 = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_POINTS
    )
    pipeline2.set_data(positions=TEST_POSITIONS, colours=np.array([0.5, 0.5, 0.5]))

    assert getattr(pipeline2, "position_buffer", None) is not None
    assert getattr(pipeline2, "num_points", 0) == 3


def test_pipeline_set_data_with_gpu_buffer(webgpu_device):
    """Test pipeline set_data method with GPU buffers."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_POINTS
    )

    # Create test data as GPU buffer
    position_buffer = webgpu_device.create_buffer_with_data(
        data=TEST_POSITIONS.tobytes(),
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
    )

    pipeline.set_data(positions=position_buffer)

    assert getattr(pipeline, "position_buffer", None) is position_buffer
    assert getattr(pipeline, "num_points", 0) == 3


@pytest.mark.parametrize(
    "pipeline_type",
    [
        PipelineType.MULTI_COLOURED_POINTS,
        PipelineType.SINGLE_COLOUR_POINTS,
        PipelineType.MULTI_COLOURED_LINES,
        PipelineType.SINGLE_COLOUR_LINES,
        PipelineType.MULTI_COLOURED_TRIANGLES,
        PipelineType.SINGLE_COLOUR_TRIANGLES,
    ],
)
def test_pipeline_update_uniforms(webgpu_device, pipeline_type):
    """Test update_uniforms method."""
    pipeline = PipelineFactory.create_pipeline(webgpu_device, pipeline_type)
    pipeline.update_uniforms(mvp=TEST_MVP_MATRIX)

    assert pipeline.uniform_buffer is not None

    if "SINGLE_COLOUR" in pipeline_type.name:
        pipeline.update_uniforms(colour=np.array([1.0, 0.0, 0.0]))

    if "POINTS" in pipeline_type.name or "POINT_LIST" in pipeline_type.name:
        pipeline.update_uniforms(point_size=2.0)


def test_pipeline_render_without_data(webgpu_device, render_pass):
    """Test render method when no data is set."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_POINTS
    )

    # Should not crash when no data is set
    pipeline.render(render_pass)


def test_pipeline_cleanup(webgpu_device):
    """Test cleanup method."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_POINTS
    )
    pipeline.set_data(positions=TEST_POSITIONS)

    # Cleanup should not raise exceptions
    pipeline.cleanup()


def test_pipeline_abstract_methods(webgpu_device):
    """Test that abstract methods are properly implemented."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_POINTS
    )

    # Test abstract method implementations
    assert callable(pipeline.get_dtype)
    assert callable(pipeline._get_shader_code)
    assert callable(pipeline._get_vertex_buffer_layouts)
    assert callable(pipeline._get_primitive_topology)
    assert callable(pipeline._set_default_uniforms)
    assert callable(pipeline._get_pipeline_label)

    # Test that methods return expected types
    dtype = pipeline.get_dtype()
    assert isinstance(dtype, np.dtype)

    shader_code = pipeline._get_shader_code()
    assert isinstance(shader_code, str)
    assert len(shader_code) > 0

    vertex_layouts = pipeline._get_vertex_buffer_layouts()
    assert isinstance(vertex_layouts, list)

    topology = pipeline._get_primitive_topology()
    assert topology is not None

    label = pipeline._get_pipeline_label()
    assert isinstance(label, str)
    assert len(label) > 0


def test_gpu_buffer_handling_for_triangle_line_pipelines(webgpu_device):
    """Test GPU buffer handling in triangle and line pipelines (covers lines 175-176, 217-218, 340-341, 383-384)."""
    position_buffer = webgpu_device.create_buffer_with_data(
        data=TEST_POSITIONS.tobytes(),
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
    )
    color_buffer = webgpu_device.create_buffer_with_data(
        data=TEST_COLORS.tobytes(),
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
    )

    # Test triangle pipelines
    triangle_multi = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_TRIANGLES
    )
    triangle_multi.set_data(positions=position_buffer, colors=color_buffer)
    assert getattr(triangle_multi, "vertex_buffer", None) is position_buffer
    assert getattr(triangle_multi, "color_buffer", None) is color_buffer

    triangle_single = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_TRIANGLES
    )
    triangle_single.set_data(positions=position_buffer)
    assert getattr(triangle_single, "vertex_buffer", None) is position_buffer

    # Test line pipelines
    line_multi = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_LINES
    )
    line_multi.set_data(positions=position_buffer, colors=color_buffer)
    assert getattr(line_multi, "vertex_buffer", None) is position_buffer
    assert getattr(line_multi, "color_buffer", None) is color_buffer

    line_single = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_LINES
    )
    line_single.set_data(positions=position_buffer)
    assert getattr(line_single, "vertex_buffer", None) is position_buffer


def test_pipeline_rendering_with_data(webgpu_device, render_pass):
    """Test rendering with actual data set (covers lines 233-240, 273-280, 380-386, 421-427)."""
    mvp_matrix = np.eye(4, dtype=np.float32)

    # Test triangle pipeline rendering
    triangle_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_TRIANGLES
    )
    triangle_pipeline.set_data(positions=TEST_POSITIONS, colors=TEST_COLORS)
    triangle_pipeline.update_uniforms(mvp=mvp_matrix)
    triangle_pipeline.render(render_pass, num_vertices=3)

    # Test line pipeline rendering
    line_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_LINES
    )
    line_pipeline.set_data(positions=TEST_POSITIONS, colors=TEST_COLORS)
    line_pipeline.update_uniforms(mvp=mvp_matrix)
    line_pipeline.render(render_pass, num_vertices=3)


def test_pipeline_cleanup_with_buffers(webgpu_device):
    """Test pipeline cleanup with existing buffers (covers lines 247, 287)."""
    # Test triangle pipeline cleanup
    triangle_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_TRIANGLES
    )
    triangle_pipeline.set_data(positions=TEST_POSITIONS, colors=TEST_COLORS)

    assert getattr(triangle_pipeline, "vertex_buffer", None) is not None
    assert getattr(triangle_pipeline, "color_buffer", None) is not None
    triangle_pipeline.cleanup()
    triangle_pipeline.cleanup()  # Should not fail

    # Test line pipeline cleanup
    line_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_LINES
    )
    line_pipeline.set_data(positions=TEST_POSITIONS, colors=TEST_COLORS)

    assert getattr(line_pipeline, "vertex_buffer", None) is not None
    assert getattr(line_pipeline, "color_buffer", None) is not None
    line_pipeline.cleanup()
    line_pipeline.cleanup()  # Should not fail


def test_triangle_topology_wrappers(webgpu_device):
    """Test triangle topology wrapper classes (covers lines 78, 82, 86, 90)."""
    wrappers_and_topologies = [
        (
            PipelineType.TRIANGLE_LIST_MULTI_COLOURED,
            wgpu.PrimitiveTopology.triangle_list,
        ),
        (
            PipelineType.TRIANGLE_LIST_SINGLE_COLOUR,
            wgpu.PrimitiveTopology.triangle_list,
        ),
        (
            PipelineType.TRIANGLE_STRIP_MULTI_COLOURED,
            wgpu.PrimitiveTopology.triangle_strip,
        ),
        (
            PipelineType.TRIANGLE_STRIP_SINGLE_COLOUR,
            wgpu.PrimitiveTopology.triangle_strip,
        ),
    ]

    for pipeline_type, expected_topology in wrappers_and_topologies:
        pipeline = PipelineFactory.create_pipeline(webgpu_device, pipeline_type)
        assert pipeline._get_primitive_topology() == expected_topology


def test_point_list_pipeline_functionality(webgpu_device, render_pass):
    """Test specific point list pipeline functionality (covers lines 197-220, 236-242, 255-267, 375-380, 397-406, 419-430, 434-436)."""
    # Test multi-coloured point list
    multi_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.POINT_LIST_MULTI_COLOURED
    )

    # Verify it uses point-list topology
    assert multi_pipeline._get_primitive_topology() == wgpu.PrimitiveTopology.point_list

    # Test data setting with GPU buffers (covers lines 197-220)
    positions = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], dtype=np.float32)
    colors = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)

    # Create GPU buffers for testing
    position_buffer = webgpu_device.create_buffer_with_data(
        data=positions.tobytes(),
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
    )
    color_buffer = webgpu_device.create_buffer_with_data(
        data=colors.tobytes(),
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
    )

    # Test with GPU buffers
    multi_pipeline.set_data(positions=position_buffer, colours=color_buffer)
    assert getattr(multi_pipeline, "position_buffer", None) is position_buffer
    assert getattr(multi_pipeline, "colour_buffer", None) is color_buffer
    assert getattr(multi_pipeline, "num_points", 0) == 2

    # Test with None colours (should create default white colors)
    multi_pipeline.set_data(positions=positions, colours=None)
    assert getattr(multi_pipeline, "position_buffer", None) is not None
    assert getattr(multi_pipeline, "colour_buffer", None) is not None
    assert getattr(multi_pipeline, "num_points", 0) == 2

    # Test uniform updates (covers lines 236-242)
    mvp_matrix = np.eye(4, dtype=np.float32)
    multi_pipeline.update_uniforms(mvp=mvp_matrix, point_size=3.0)
    assert multi_pipeline.uniform_buffer is not None

    # Test rendering (covers lines 255-267)
    multi_pipeline.render(render_pass, num_points=2)

    # Test cleanup (covers lines 271-275)
    multi_pipeline.cleanup()
    multi_pipeline.cleanup()  # Should not fail

    # Test single-coloured point list
    single_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.POINT_LIST_SINGLE_COLOUR
    )

    # Test GPU buffer handling (covers lines 375-380)
    single_pipeline.set_data(positions=position_buffer)
    assert getattr(single_pipeline, "position_buffer", None) is position_buffer
    assert getattr(single_pipeline, "num_points", 0) == 2

    # Test uniform updates with colour parameter (covers lines 397-406)
    single_pipeline.update_uniforms(
        mvp=mvp_matrix, colour=np.array([1.0, 0.0, 0.0]), point_size=2.0
    )
    assert single_pipeline.uniform_buffer is not None

    # Test rendering (covers lines 419-430)
    single_pipeline.render(render_pass, num_points=2)

    # Test cleanup (covers lines 434-436)
    single_pipeline.cleanup()
    single_pipeline.cleanup()  # Should not fail


def test_pipeline_factory_error_handling(webgpu_device):
    """Test pipeline factory error handling (covers line 168)."""
    original_registry = PipelineFactory._pipeline_registry.copy()

    try:
        # Clear registry to force unknown pipeline type error
        PipelineFactory._pipeline_registry.clear()

        with pytest.raises(ValueError, match="Unknown pipeline type"):
            PipelineFactory.create_pipeline(
                webgpu_device, PipelineType.MULTI_COLOURED_POINTS
            )

    finally:
        # Restore registry
        PipelineFactory._pipeline_registry.clear()
        PipelineFactory._pipeline_registry.update(original_registry)


def test_base_pipeline_internal_operations(webgpu_device):
    """Test base pipeline internal operations (covers lines 53, 167, 176, 185-186, 211, 214, 220-221)."""
    # Test custom stride by creating a pipeline with custom stride through direct instantiation
    from ncca.ngl.webgpu.point_pipeline import PointPipelineSingleColour

    # Test custom stride (line 53)
    pipeline = PointPipelineSingleColour(webgpu_device, stride=16)
    assert pipeline._stride == 16

    # Test default stride when stride=0
    pipeline_default = PointPipelineSingleColour(webgpu_device, stride=0)
    assert pipeline_default._stride == 12  # Vec3 default stride

    # Test _create_or_update_buffer with GPUBuffer (line 167)
    positions = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], dtype=np.float32)
    gpu_buffer = webgpu_device.create_buffer_with_data(
        data=positions.tobytes(),
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
    )

    buffer_usage = wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST
    buffer, size = pipeline_default._create_or_update_buffer(
        None, gpu_buffer, buffer_usage, "test_buffer"
    )
    assert buffer is gpu_buffer
    assert size == gpu_buffer.size

    # Test buffer update path (lines 185-186)
    small_data = np.array([[0.0, 0.0, 0.0]], dtype=np.float32)
    large_data = np.array(
        [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0]], dtype=np.float32
    )

    # Create initial buffer
    temp_buffer, _ = pipeline_default._create_or_update_buffer(
        None, small_data, buffer_usage, "temp_buffer"
    )
    old_buffer = temp_buffer

    # Update with larger data (should update existing buffer, lines 185-186)
    updated_buffer, updated_size = pipeline_default._create_or_update_buffer(
        old_buffer, large_data, buffer_usage, "temp_buffer"
    )

    # If the buffer was large enough, it should be updated in place
    # If it was too small, a new buffer should be created
    assert updated_buffer is not None
    assert updated_size > 0

    # Test vertex data processing with None (line 211)
    result = pipeline_default._process_vertex_data(
        None, None, padding_size=4, buffer_label="test_none"
    )
    assert result is None

    # Test vertex data processing with GPU buffer (line 214)
    result = pipeline_default._process_vertex_data(
        gpu_buffer, None, padding_size=0, buffer_label="test_gpu"
    )
    assert result is gpu_buffer

    # Test 1D array padding (lines 220-221)
    small_data = np.array([1.0, 0.0], dtype=np.float32)
    result = pipeline_default._process_vertex_data(
        small_data, None, padding_size=4, buffer_label="test_padding"
    )
    assert result is not None

    # Test buffer recreation through data updates
    small_positions = np.array([[0.0, 0.0, 0.0]], dtype=np.float32)
    large_positions = np.array(
        [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0]], dtype=np.float32
    )

    pipeline_default.set_data(positions=small_positions)
    pipeline_default.set_data(
        positions=large_positions
    )  # Should trigger buffer recreation
    assert getattr(pipeline_default, "position_buffer", None) is not None


def test_abstract_method_implementations(webgpu_device):
    """Test that all abstract methods are properly implemented (covers lines 72, 77, 82, 87, 92, 97, 243, 253, 264)."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_POINTS
    )

    # Test abstract methods don't raise exceptions
    pipeline.get_dtype()
    pipeline._get_shader_code()
    pipeline._get_vertex_buffer_layouts()
    pipeline._get_primitive_topology()
    pipeline._set_default_uniforms()
    pipeline._get_pipeline_label()
    pipeline.set_data(positions=TEST_POSITIONS)
    pipeline.update_uniforms()

    # Test render method
    command_encoder = webgpu_device.create_command_encoder()
    texture = webgpu_device.create_texture(
        size=(100, 100),
        usage=wgpu.TextureUsage.RENDER_ATTACHMENT,
        format=wgpu.TextureFormat.rgba8unorm,
    )
    render_pass = command_encoder.begin_render_pass(
        color_attachments=[
            {
                "view": texture.create_view(),
                "load_op": "load",
                "store_op": "store",
            }
        ],
        depth_stencil_attachment={
            "view": webgpu_device.create_texture(
                size=(100, 100),
                usage=wgpu.TextureUsage.RENDER_ATTACHMENT,
                format=wgpu.TextureFormat.depth24plus,
            ).create_view(),
            "depth_load_op": "load",
            "depth_store_op": "store",
        },
    )

    pipeline.render(render_pass)
    render_pass.end()


def test_render_points_helper_method(webgpu_device, render_pass):
    """Test the _render_points helper method (covers lines 345-358)."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_POINTS
    )
    pipeline.set_data(positions=TEST_POSITIONS, colours=TEST_COLORS)

    # Test _render_points with None position buffer (early return)
    getattr(pipeline, "_render_points", lambda *args: None)(None, None, 2)

    # Test _render_points with valid buffers
    position_buffer = getattr(pipeline, "position_buffer", None)
    color_buffer = getattr(pipeline, "colour_buffer", None)

    if position_buffer and color_buffer:
        # Should not crash and should set up the render pass correctly
        getattr(pipeline, "_render_points", lambda *args: None)(
            render_pass, position_buffer, color_buffer, 3
        )
    pipeline.set_data(positions=TEST_POSITIONS, colours=TEST_COLORS)

    # Test _render_points with None position buffer (early return)
    getattr(pipeline, "_render_points", lambda x, y, z: None)(None, None, 2)

    # Test _render_points with valid buffers
    position_buffer = getattr(pipeline, "position_buffer", None)
    color_buffer = getattr(pipeline, "colour_buffer", None)

    if position_buffer and color_buffer:
        # Should not crash and should set up the render pass correctly
        getattr(pipeline, "_render_points", lambda x, y, z, w: None)(
            render_pass, position_buffer, color_buffer, 3
        )


def test_instanced_geometry_pipeline_creation(webgpu_device):
    """Test instanced geometry pipeline creation and basic properties."""
    # Test multi-coloured instanced geometry
    multi_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_INSTANCED_GEOMETRY
    )
    assert isinstance(multi_pipeline, InstancedGeometryPipelineMultiColour)
    assert (
        multi_pipeline._get_primitive_topology() == wgpu.PrimitiveTopology.triangle_list
    )

    # Test single-coloured instanced geometry
    single_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY
    )
    assert isinstance(single_pipeline, InstancedGeometryPipelineSingleColour)
    assert (
        single_pipeline._get_primitive_topology()
        == wgpu.PrimitiveTopology.triangle_list
    )


def test_instanced_geometry_pipeline_data_setting(webgpu_device):
    """Test data setting for instanced geometry pipelines using simplified API."""
    from ncca.ngl.prim_data import PrimData

    # Test multi-coloured pipeline
    multi_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_INSTANCED_GEOMETRY
    )

    # Set instance data with numpy arrays and interleaved geometry
    instance_positions = np.array([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]], dtype=np.float32)
    instance_colours = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
    sphere_data = PrimData.sphere(1.0, 8)  # Interleaved format

    multi_pipeline.set_data(
        positions=instance_positions,
        colours=instance_colours,
        geometry_data=sphere_data,
    )

    assert getattr(multi_pipeline, "position_buffer", None) is not None
    assert getattr(multi_pipeline, "colour_buffer", None) is not None
    assert getattr(multi_pipeline, "geometry_buffer", None) is not None
    assert getattr(multi_pipeline, "num_instances", 0) == 2

    # Test with default colours (None)
    multi_pipeline.set_data(
        positions=instance_positions,
        colours=None,
        geometry_data=sphere_data,
    )
    assert (
        getattr(multi_pipeline, "colour_buffer", None) is not None
    )  # Should create default white

    # Test single-colour pipeline
    single_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY
    )

    single_pipeline.set_data(
        positions=instance_positions,
        geometry_data=sphere_data,
    )

    assert getattr(single_pipeline, "position_buffer", None) is not None
    assert getattr(single_pipeline, "geometry_buffer", None) is not None
    assert getattr(single_pipeline, "num_instances", 0) == 2


def test_instanced_geometry_pipeline_uniforms(webgpu_device):
    """Test uniform updates for instanced geometry pipelines."""
    from ncca.ngl.prim_data import PrimData

    mvp_matrix = np.eye(4, dtype=np.float32)
    view_matrix = np.eye(4, dtype=np.float32)
    instance_transform = np.eye(4, dtype=np.float32)
    instance_transform[0, 0] = 2.0  # Scale X by 2

    # Test multi-coloured pipeline
    multi_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_INSTANCED_GEOMETRY
    )
    sphere_data = PrimData.sphere(1.0, 8)  # Use interleaved format
    multi_pipeline.set_data(
        positions=TEST_POSITIONS,
        geometry_data=sphere_data,
    )
    multi_pipeline.update_uniforms(
        mvp=mvp_matrix,
        view_matrix=view_matrix,
        instance_transform=instance_transform,
    )
    assert multi_pipeline.uniform_buffer is not None

    # Test single-colour pipeline
    single_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY
    )
    single_pipeline.set_data(
        positions=TEST_POSITIONS,
        geometry_data=sphere_data,
    )
    single_pipeline.update_uniforms(
        mvp=mvp_matrix,
        view_matrix=view_matrix,
        colour=np.array([1.0, 0.0, 0.0]),
        instance_transform=instance_transform,
    )
    assert single_pipeline.uniform_buffer is not None


def test_instanced_geometry_pipeline_rendering(webgpu_device, render_pass):
    """Test rendering for instanced geometry pipelines."""
    from ncca.ngl.prim_data import PrimData

    mvp_matrix = np.eye(4, dtype=np.float32)
    sphere_data = PrimData.sphere(1.0, 8)  # Use interleaved format

    # Test multi-coloured rendering
    multi_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_INSTANCED_GEOMETRY
    )
    multi_pipeline.set_data(
        positions=TEST_POSITIONS,
        colours=TEST_COLORS,
        geometry_data=sphere_data,  # Single interleaved format
    )
    multi_pipeline.update_uniforms(mvp=mvp_matrix)
    multi_pipeline.render(render_pass, num_instances=2)

    # Test single-coloured rendering
    single_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY
    )
    single_pipeline.set_data(
        positions=TEST_POSITIONS,
        geometry_data=sphere_data,  # Single interleaved format
    )
    single_pipeline.update_uniforms(mvp=mvp_matrix)
    single_pipeline.render(render_pass, num_instances=2)


def test_instanced_geometry_pipeline_cleanup(webgpu_device):
    """Test cleanup for instanced geometry pipelines."""
    from ncca.ngl.prim_data import PrimData

    sphere_data = PrimData.sphere(1.0, 8)

    multi_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_INSTANCED_GEOMETRY
    )
    multi_pipeline.set_data(
        positions=TEST_POSITIONS,
        colours=TEST_COLORS,
        geometry_data=sphere_data,  # Single interleaved format
    )

    # Verify buffers exist
    assert getattr(multi_pipeline, "position_buffer", None) is not None
    assert getattr(multi_pipeline, "colour_buffer", None) is not None
    assert getattr(multi_pipeline, "geometry_buffer", None) is not None

    # Cleanup should not raise exceptions
    multi_pipeline.cleanup()
    multi_pipeline.cleanup()  # Should not fail

    # Test single-colour cleanup
    single_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY
    )
    single_pipeline.set_data(
        positions=TEST_POSITIONS,
        geometry_data=sphere_data,  # Single interleaved format
    )

    assert getattr(single_pipeline, "position_buffer", None) is not None
    assert getattr(single_pipeline, "geometry_buffer", None) is not None

    single_pipeline.cleanup()
    single_pipeline.cleanup()  # Should not fail


def test_instanced_geometry_pipeline_vertex_layouts(webgpu_device):
    """Test vertex buffer layouts for instanced geometry pipelines."""
    multi_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_INSTANCED_GEOMETRY
    )
    layouts = multi_pipeline._get_vertex_buffer_layouts()

    # Should have 4 layouts: instance position, instance ID, instance colour,
    # single interleaved geometry buffer
    assert len(layouts) == 4

    # Check instance buffers have step_mode="instance"
    assert layouts[0]["step_mode"] == "instance"  # instance position
    assert layouts[1]["step_mode"] == "instance"  # instance ID
    assert layouts[2]["step_mode"] == "instance"  # instance colour

    # Check single interleaved geometry buffer has step_mode="vertex"
    assert layouts[3]["step_mode"] == "vertex"  # interleaved geometry

    # Verify interleaved geometry buffer layout attributes
    geom_layout = layouts[3]
    assert len(geom_layout["attributes"]) == 3  # position, normal, UV
    assert geom_layout["attributes"][0]["shader_location"] == 3  # geometry_position
    assert geom_layout["attributes"][0]["offset"] == 0  # position offset
    assert geom_layout["attributes"][1]["shader_location"] == 4  # geometry_normal
    assert geom_layout["attributes"][1]["offset"] == 12  # normal offset (3 * 4)
    assert geom_layout["attributes"][2]["shader_location"] == 5  # geometry_uv
    assert geom_layout["attributes"][2]["offset"] == 24  # UV offset (6 * 4)
    assert geom_layout["array_stride"] == 32  # 8 floats * 4 bytes

    single_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY
    )
    single_layouts = single_pipeline._get_vertex_buffer_layouts()

    # Should have 4 layouts: instance position, instance ID, dummy colour buffer,
    # single interleaved geometry buffer
    assert len(single_layouts) == 4


def test_instanced_geometry_pipeline_simplified_format(webgpu_device):
    """Test simplified interleaved geometry data format (x,y,z,nx,ny,nz,u,v)."""
    from ncca.ngl.prim_data import PrimData

    # Get test data from PrimData (already in correct format)
    sphere_data = PrimData.sphere(1.0, 8)  # Small sphere for testing

    # Test multi-coloured pipeline with interleaved data
    multi_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_INSTANCED_GEOMETRY
    )

    instance_positions = np.array([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]], dtype=np.float32)
    instance_colours = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)

    # Test with interleaved geometry data
    multi_pipeline.set_data(
        positions=instance_positions,
        colours=instance_colours,
        geometry_data=sphere_data,  # Single interleaved format
    )

    assert getattr(multi_pipeline, "position_buffer", None) is not None
    assert getattr(multi_pipeline, "colour_buffer", None) is not None
    assert getattr(multi_pipeline, "geometry_buffer", None) is not None
    assert getattr(multi_pipeline, "num_instances", 0) == 2

    # Verify sphere data has correct format
    expected_vertices = sphere_data.shape[0]  # sphere_data is (num_vertices, 8)
    assert getattr(multi_pipeline, "num_vertices", 0) == expected_vertices

    # Test single-coloured pipeline with interleaved data
    single_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY
    )

    single_pipeline.set_data(
        positions=instance_positions,
        geometry_data=sphere_data,  # Single interleaved format
    )

    assert getattr(single_pipeline, "position_buffer", None) is not None
    assert getattr(single_pipeline, "geometry_buffer", None) is not None
    assert getattr(single_pipeline, "num_instances", 0) == 2
    assert getattr(single_pipeline, "num_vertices", 0) == expected_vertices


def test_instanced_geometry_pipeline_gpu_buffers(webgpu_device):
    """Test interleaved geometry data format with GPU buffers."""
    from ncca.ngl.prim_data import PrimData

    # Get test data and convert to GPU buffer
    sphere_data = PrimData.sphere(1.0, 8)
    geometry_buffer = webgpu_device.create_buffer_with_data(
        data=sphere_data.tobytes(),
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
    )

    multi_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_INSTANCED_GEOMETRY
    )

    instance_positions = np.array([[0.0, 0.0, 0.0]], dtype=np.float32)

    # Test with GPU buffer
    multi_pipeline.set_data(
        positions=instance_positions,
        geometry_data=geometry_buffer,  # GPU buffer version
    )

    assert getattr(multi_pipeline, "geometry_buffer", None) is geometry_buffer
    expected_vertices = sphere_data.shape[0]  # sphere_data is (num_vertices, 8)
    assert getattr(multi_pipeline, "num_vertices", 0) == expected_vertices


def test_instanced_geometry_pipeline_validation(webgpu_device):
    """Test validation of interleaved geometry data format."""
    multi_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_INSTANCED_GEOMETRY
    )

    instance_positions = np.array([[0.0, 0.0, 0.0]], dtype=np.float32)

    # Test with incorrect number of components
    bad_data = np.array([[1.0, 2.0, 3.0]], dtype=np.float32)  # Only 3 components

    with pytest.raises(ValueError, match="geometry_data must have 8 components"):
        multi_pipeline.set_data(
            positions=instance_positions,
            geometry_data=bad_data,
        )

    # Test with correct but 1D data (should be reshaped)
    flat_data = np.array(
        [
            1.0,
            2.0,
            3.0,  # x,y,z
            0.0,
            0.0,
            1.0,  # nx,ny,nz
            0.5,
            0.5,  # u,v
        ],
        dtype=np.float32,
    )

    # Should not raise an error
    multi_pipeline.set_data(
        positions=instance_positions,
        geometry_data=flat_data,
    )

    assert getattr(multi_pipeline, "num_vertices", 0) == 1


def test_instanced_geometry_pipeline_required_geometry_data(webgpu_device):
    """Test that geometry_data is required parameter."""
    multi_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_INSTANCED_GEOMETRY
    )

    instance_positions = np.array([[0.0, 0.0, 0.0]], dtype=np.float32)

    # Test missing geometry_data should raise error
    with pytest.raises(ValueError, match="geometry_data is required"):
        multi_pipeline.set_data(positions=instance_positions)
