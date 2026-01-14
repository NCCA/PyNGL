import pytest
import wgpu
import wgpu.utils
import numpy as np

from ncca.ngl.webgpu import PipelineFactory, PipelineType
from ncca.ngl.webgpu.line_pipeline import (
    LinePipelineMultiColour,
    LinePipelineSingleColour,
)
from ncca.ngl.webgpu.point_pipeline import (
    PointPipelineMultiColour,
    PointPipelineSingleColour,
)
from ncca.ngl.webgpu.triangle_pipeline import (
    TrianglePipelineMultiColour,
    TrianglePipelineSingleColour,
)


def test_initial_factory():
    assert len(PipelineFactory._pipeline_registry) == 10


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
    ],
)
def test_pipeline_creation(webgpu_device, pipeline_type, expected_class):
    """Test that all pipeline types can be created and return correct class."""
    pipeline = PipelineFactory.create_pipeline(webgpu_device, pipeline_type)
    assert pipeline is not None
    assert isinstance(pipeline, expected_class)


def test_point_pipeline_set_data_with_numpy(webgpu_device):
    """Test point pipeline set_data method with numpy arrays."""
    # Test multi-coloured points
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_POINTS
    )
    positions = np.array(
        [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [-1.0, -1.0, 0.0]], dtype=np.float32
    )
    colors = np.array(
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], dtype=np.float32
    )

    pipeline.set_data(positions=positions, colours=colors)

    # Use getattr to avoid IDE type errors
    position_buffer = getattr(pipeline, "position_buffer", None)
    num_points = getattr(pipeline, "num_points", 0)
    assert position_buffer is not None
    assert num_points == 3

    # Test single-coloured points
    pipeline2 = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_POINTS
    )
    pipeline2.set_data(positions=positions, colours=np.array([0.5, 0.5, 0.5]))

    position_buffer2 = getattr(pipeline2, "position_buffer", None)
    num_points2 = getattr(pipeline2, "num_points", 0)
    assert position_buffer2 is not None
    assert num_points2 == 3


def test_line_and_triangle_pipeline_set_data_with_numpy(webgpu_device):
    """Test line and triangle pipeline set_data method with numpy arrays."""
    positions = np.array(
        [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [-1.0, -1.0, 0.0]], dtype=np.float32
    )
    colors = np.array(
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], dtype=np.float32
    )

    # Test multi-coloured lines
    line_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_LINES
    )
    line_pipeline.set_data(positions=positions, colours=colors)

    vertex_buffer = getattr(line_pipeline, "vertex_buffer", None)
    num_vertices = getattr(line_pipeline, "num_vertices", 0)
    assert vertex_buffer is not None
    assert num_vertices == 3

    # Test multi-coloured triangles
    triangle_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_TRIANGLES
    )
    triangle_pipeline.set_data(positions=positions, colours=colors)

    vertex_buffer2 = getattr(triangle_pipeline, "vertex_buffer", None)
    num_vertices2 = getattr(triangle_pipeline, "num_vertices", 0)
    assert vertex_buffer2 is not None
    assert num_vertices2 == 3


def test_point_pipeline_set_data_with_gpu_buffer(webgpu_device):
    """Test point pipeline set_data method with GPU buffers."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_POINTS
    )

    # Create test data as GPU buffer
    positions = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], dtype=np.float32)
    position_buffer = webgpu_device.create_buffer_with_data(
        data=positions.tobytes(),
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
    )

    pipeline.set_data(positions=position_buffer)

    # Verify buffer was used
    pipeline_position_buffer = getattr(pipeline, "position_buffer", None)
    num_points = getattr(pipeline, "num_points", 0)
    assert pipeline_position_buffer is position_buffer
    assert num_points == 2


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

    # Create test matrices
    mvp_matrix = np.eye(4, dtype=np.float32)
    view_matrix = np.eye(4, dtype=np.float32)
    view_matrix[0][3] = 1.0  # Small translation

    # Update uniforms
    pipeline.update_uniforms(mvp=mvp_matrix, view_matrix=view_matrix)

    # Verify uniforms were updated (check that no errors occurred)
    assert pipeline.uniform_buffer is not None

    if "SINGLE_COLOUR" in pipeline_type.name:
        # Test colour update for single colour pipelines
        pipeline.update_uniforms(colour=np.array([1.0, 0.0, 0.0]))

    if "POINTS" in pipeline_type.name:
        # Test point size update
        pipeline.update_uniforms(point_size=2.0)


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
def test_pipeline_render_without_data(webgpu_device, pipeline_type):
    """Test render method when no data is set."""
    pipeline = PipelineFactory.create_pipeline(webgpu_device, pipeline_type)

    # Create a mock render pass
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

    # Should not crash when no data is set
    pipeline.render(render_pass)
    render_pass.end()


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
def test_pipeline_cleanup(webgpu_device, pipeline_type):
    """Test cleanup method."""
    pipeline = PipelineFactory.create_pipeline(webgpu_device, pipeline_type)

    # Set some data to create buffers
    positions = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], dtype=np.float32)
    pipeline.set_data(positions=positions)

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
    # Point pipelines return string topology, convert to enum for comparison
    if isinstance(topology, str):
        # Map common string values to enum values
        topology_map = {
            "point-list": wgpu.PrimitiveTopology.point_list,
            "line-list": wgpu.PrimitiveTopology.line_list,
            "line-strip": wgpu.PrimitiveTopology.line_strip,
            "triangle-list": wgpu.PrimitiveTopology.triangle_list,
            "triangle-strip": wgpu.PrimitiveTopology.triangle_strip,
        }
        topology = topology_map.get(topology, topology)

    # Check if it's either already an enum or a valid string
    assert isinstance(topology, (wgpu.PrimitiveTopology, str))

    label = pipeline._get_pipeline_label()
    assert isinstance(label, str)
    assert len(label) > 0


def test_triangle_list_and_strip_pipelines(webgpu_device):
    """Test triangle list and strip pipeline variations."""
    # Test triangle list
    list_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.TRIANGLE_LIST_MULTI_COLOURED
    )
    assert (
        list_pipeline._get_primitive_topology() == wgpu.PrimitiveTopology.triangle_list
    )

    # Test triangle strip
    strip_pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.TRIANGLE_STRIP_MULTI_COLOURED
    )
    assert (
        strip_pipeline._get_primitive_topology()
        == wgpu.PrimitiveTopology.triangle_strip
    )

    # Test that they can still be used normally
    positions = np.array(
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.5, 1.0, 0.0]], dtype=np.float32
    )
    colors = np.array(
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], dtype=np.float32
    )

    list_pipeline.set_data(positions=positions, colours=colors)
    strip_pipeline.set_data(positions=positions, colours=colors)

    # Triangle pipelines use vertex_buffer, not position_buffer
    assert getattr(list_pipeline, "vertex_buffer", None) is not None
    assert getattr(strip_pipeline, "vertex_buffer", None) is not None
