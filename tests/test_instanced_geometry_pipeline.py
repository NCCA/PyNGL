"""
Additional tests for instanced geometry pipeline to improve coverage.
Tests specific edge cases and error conditions not covered in main test suite.
"""

import pytest
import wgpu
import numpy as np

from ncca.ngl.webgpu import PipelineFactory, PipelineType
from ncca.ngl.webgpu.instanced_geometry_pipeline import (
    InstancedGeometryPipelineMultiColour,
    InstancedGeometryPipelineSingleColour,
    BaseInstancedGeometryPipeline,
    GEOM_ERROR,
)
from ncca.ngl.prim_data import PrimData


# Test data fixtures
TEST_POSITIONS = np.array(
    [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [-1.0, -1.0, 0.0]], dtype=np.float32
)
TEST_COLORS = np.array(
    [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], dtype=np.float32
)
TEST_MVP_MATRIX = np.eye(4, dtype=np.float32)


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


def test_instanced_geometry_pipeline_gpu_buffer_position_handling(webgpu_device):
    """Test GPU buffer handling for positions (covers lines 381-382)."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_INSTANCED_GEOMETRY
    )

    # Create GPU buffer for positions
    position_buffer = webgpu_device.create_buffer_with_data(
        data=TEST_POSITIONS.tobytes(),
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
    )

    # Test with GPU buffer - should set buffer directly and calculate num_instances
    pipeline.set_data(positions=position_buffer, geometry_data=PrimData.sphere(1.0, 8))

    assert pipeline.position_buffer is position_buffer
    assert pipeline.num_instances == position_buffer.size // pipeline._stride


def test_instanced_geometry_pipeline_gpu_buffer_colour_handling(webgpu_device):
    """Test GPU buffer handling for colours (covers line 421)."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_INSTANCED_GEOMETRY
    )

    # Create GPU buffer for colours
    colour_buffer = webgpu_device.create_buffer_with_data(
        data=TEST_COLORS.tobytes(),
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
    )

    # Test with GPU buffer - should set buffer directly
    pipeline.set_data(
        positions=TEST_POSITIONS,
        colours=colour_buffer,
        geometry_data=PrimData.sphere(1.0, 8),
    )

    assert pipeline.colour_buffer is colour_buffer


def test_instanced_geometry_pipeline_invalid_geometry_dimensions(webgpu_device):
    """Test invalid geometry data dimensions (covers line 459)."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_INSTANCED_GEOMETRY
    )

    # Test with 3D array (should raise error)
    bad_3d_data = np.ones((2, 2, 8), dtype=np.float32)

    with pytest.raises(ValueError, match="geometry_data must be 1D or 2D array"):
        pipeline.set_data(positions=TEST_POSITIONS, geometry_data=bad_3d_data)


def test_instanced_geometry_pipeline_render_without_buffers(webgpu_device, render_pass):
    """Test render method when required buffers are missing (covers line 504)."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_INSTANCED_GEOMETRY
    )

    # Set only some buffers but not all
    pipeline.position_buffer = webgpu_device.create_buffer_with_data(
        data=TEST_POSITIONS.tobytes(),
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
    )
    pipeline.num_instances = 3
    # Missing colour_buffer, instance_id_buffer, geometry_buffer

    # Should return early without rendering
    pipeline.render(render_pass)


def test_instanced_geometry_pipeline_single_colour_gpu_position_handling(webgpu_device):
    """Test single colour pipeline GPU buffer position handling (covers lines 601-602)."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY
    )

    # Create GPU buffer for positions
    position_buffer = webgpu_device.create_buffer_with_data(
        data=TEST_POSITIONS.tobytes(),
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
    )

    # Test with GPU buffer
    pipeline.set_data(positions=position_buffer, geometry_data=PrimData.sphere(1.0, 8))

    assert pipeline.position_buffer is position_buffer
    assert pipeline.num_instances == position_buffer.size // pipeline._stride


def test_instanced_geometry_pipeline_single_colour_buffer_destruction(webgpu_device):
    """Test single colour pipeline buffer destruction (covers line 606)."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY
    )

    # Create initial buffer
    pipeline.set_data(positions=TEST_POSITIONS, geometry_data=PrimData.sphere(1.0, 8))

    old_buffer = pipeline.position_buffer
    assert old_buffer is not None

    # Set new data - should destroy old buffer
    pipeline.set_data(
        positions=TEST_POSITIONS[:2],  # Different data
        geometry_data=PrimData.sphere(1.0, 8),
    )

    assert pipeline.position_buffer is not None
    assert pipeline.position_buffer is not old_buffer


def test_instanced_geometry_pipeline_single_colour_instance_id_destruction(
    webgpu_device,
):
    """Test single colour pipeline instance ID buffer destruction (covers line 616)."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY
    )

    # Create initial data
    pipeline.set_data(positions=TEST_POSITIONS, geometry_data=PrimData.sphere(1.0, 8))

    old_instance_buffer = pipeline.instance_id_buffer
    assert old_instance_buffer is not None

    # Set new data with different number of instances
    pipeline.set_data(
        positions=TEST_POSITIONS[:2],  # Fewer instances
        geometry_data=PrimData.sphere(1.0, 8),
    )

    assert pipeline.instance_id_buffer is not None
    assert pipeline.instance_id_buffer is not old_instance_buffer


def test_instanced_geometry_pipeline_single_colour_buffer_cleanup(webgpu_device):
    """Test single colour pipeline colour buffer cleanup (covers lines 622-623)."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY
    )

    # Create initial colour buffer
    pipeline.set_data(
        positions=TEST_POSITIONS,
        colours=TEST_COLORS,
        geometry_data=PrimData.sphere(1.0, 8),
    )

    old_colour_buffer = pipeline.colour_buffer
    assert old_colour_buffer is not None

    # Set new data - should destroy old colour buffer
    pipeline.set_data(positions=TEST_POSITIONS, geometry_data=PrimData.sphere(1.0, 8))

    assert pipeline.colour_buffer is not None
    assert pipeline.colour_buffer is not old_colour_buffer


def test_instanced_geometry_pipeline_single_colour_default_colours(webgpu_device):
    """Test single colour pipeline default colours creation (covers line 628)."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY
    )

    # Set data without colours - should create default
    pipeline.set_data(positions=TEST_POSITIONS, geometry_data=PrimData.sphere(1.0, 8))

    assert pipeline.colour_buffer is not None
    assert pipeline.num_instances == 3


def test_instanced_geometry_pipeline_single_colour_gpu_colour_handling(webgpu_device):
    """Test single colour pipeline GPU colour buffer handling (covers lines 640-644)."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY
    )

    # Create GPU buffer for colours
    colour_buffer = webgpu_device.create_buffer_with_data(
        data=TEST_COLORS.tobytes(),
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
    )

    # Test with GPU buffer
    pipeline.set_data(
        positions=TEST_POSITIONS,
        colours=colour_buffer,
        geometry_data=PrimData.sphere(1.0, 8),
    )

    assert pipeline.colour_buffer is colour_buffer


def test_instanced_geometry_pipeline_single_colour_geometry_gpu_buffer(webgpu_device):
    """Test single colour pipeline geometry GPU buffer handling (covers lines 652, 655-656)."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY
    )

    # Create GPU buffer for geometry
    geometry_data = PrimData.sphere(1.0, 8)
    geometry_buffer = webgpu_device.create_buffer_with_data(
        data=geometry_data.tobytes(),
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
    )

    # Test with GPU buffer
    pipeline.set_data(positions=TEST_POSITIONS, geometry_data=geometry_buffer)

    assert pipeline.geometry_buffer is geometry_buffer
    assert pipeline.num_vertices == geometry_data.shape[0]


def test_instanced_geometry_pipeline_single_colour_geometry_array_processing(
    webgpu_device,
):
    """Test single colour pipeline geometry array processing (covers line 667)."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY
    )

    # Test with numpy array
    geometry_data = PrimData.sphere(1.0, 8)

    pipeline.set_data(positions=TEST_POSITIONS, geometry_data=geometry_data)

    assert pipeline.geometry_buffer is not None
    assert pipeline.num_vertices == geometry_data.shape[0]


def test_instanced_geometry_pipeline_single_colour_invalid_geometry_dimensions(
    webgpu_device,
):
    """Test single colour pipeline invalid geometry dimensions (covers lines 677, 679)."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY
    )

    # Test with 3D array
    bad_3d_data = np.ones((2, 2, 8), dtype=np.float32)

    with pytest.raises(ValueError, match="geometry_data must be 1D or 2D array"):
        pipeline.set_data(positions=TEST_POSITIONS, geometry_data=bad_3d_data)

    # Test with wrong number of components
    bad_2d_data = np.ones((2, 7), dtype=np.float32)  # Only 7 components instead of 8

    with pytest.raises(ValueError, match="geometry_data must have 8 components"):
        pipeline.set_data(positions=TEST_POSITIONS, geometry_data=bad_2d_data)


def test_instanced_geometry_pipeline_single_colour_render_without_buffers(
    webgpu_device, render_pass
):
    """Test single colour pipeline render without required buffers (covers line 682)."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY
    )

    # Set only some buffers
    pipeline.position_buffer = webgpu_device.create_buffer_with_data(
        data=TEST_POSITIONS.tobytes(),
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
    )
    pipeline.num_instances = 3
    # Missing other required buffers

    # Should return early without rendering
    pipeline.render(render_pass)


def test_instanced_geometry_pipeline_single_colour_render_with_missing_geometry(
    webgpu_device, render_pass
):
    """Test single colour pipeline render with missing geometry buffer (covers line 728)."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY
    )

    # Set all buffers except geometry
    pipeline.position_buffer = webgpu_device.create_buffer_with_data(
        data=TEST_POSITIONS.tobytes(),
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
    )
    pipeline.colour_buffer = webgpu_device.create_buffer_with_data(
        data=TEST_COLORS.tobytes(),
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
    )
    pipeline.instance_id_buffer = webgpu_device.create_buffer_with_data(
        data=np.arange(3, dtype=np.float32).tobytes(),
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
    )
    pipeline.num_instances = 3
    # Missing geometry_buffer

    # Should return early without rendering
    pipeline.render(render_pass)


def test_base_instanced_geometry_pipeline_create_instance_id_buffer(webgpu_device):
    """Test base class instance ID buffer creation."""
    pipeline = InstancedGeometryPipelineMultiColour(webgpu_device)

    # Test instance ID buffer creation
    buffer = pipeline._create_instance_id_buffer(5)

    assert buffer is not None
    assert buffer.label == "instance_id_buffer"
    assert buffer.size == 5 * 4  # 5 floats * 4 bytes each


def test_instanced_geometry_pipeline_error_message(webgpu_device):
    """Test that the geometry error message is accessible."""
    assert GEOM_ERROR == "geometry_data is required for instanced geometry pipelines"


def test_instanced_geometry_pipeline_single_colour_missing_geometry_error(
    webgpu_device,
):
    """Test single colour pipeline missing geometry error (covers line 652)."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY
    )

    # Test with None geometry_data - should raise error
    with pytest.raises(ValueError, match=GEOM_ERROR):
        pipeline._set_geometry_data(None)


def test_instanced_geometry_pipeline_single_colour_1d_geometry_reshape(webgpu_device):
    """Test single colour pipeline 1D geometry data reshaping (covers line 677)."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY
    )

    # Create 1D geometry data (8 components for one vertex)
    flat_geometry = np.array(
        [
            0.0,
            0.0,
            0.0,  # position
            0.0,
            0.0,
            1.0,  # normal
            0.5,
            0.5,  # UV
        ],
        dtype=np.float32,
    )

    # Should reshape 1D data to 2D
    pipeline.set_data(
        positions=np.array([[0.0, 0.0, 0.0]], dtype=np.float32),
        geometry_data=flat_geometry,
    )

    assert pipeline.num_vertices == 1
    assert pipeline.geometry_buffer is not None


def test_instanced_geometry_pipeline_buffer_reuse(webgpu_device):
    """Test buffer reuse and destruction patterns."""
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_INSTANCED_GEOMETRY
    )

    geometry_data = PrimData.sphere(1.0, 8)

    # Set initial data
    pipeline.set_data(
        positions=TEST_POSITIONS, colours=TEST_COLORS, geometry_data=geometry_data
    )

    # Get initial buffers
    initial_pos_buffer = pipeline.position_buffer
    initial_colour_buffer = pipeline.colour_buffer
    initial_geom_buffer = pipeline.geometry_buffer
    initial_id_buffer = pipeline.instance_id_buffer

    # Update with same size data - should reuse buffers
    new_positions = TEST_POSITIONS * 2.0  # Different values, same size
    new_colours = TEST_COLORS * 0.5  # Different values, same size

    pipeline.set_data(
        positions=new_positions, colours=new_colours, geometry_data=geometry_data
    )

    # Buffers should be updated (may be same or new objects)
    assert pipeline.position_buffer is not None
    assert pipeline.colour_buffer is not None
    assert pipeline.geometry_buffer is not None
    assert pipeline.instance_id_buffer is not None


def test_instanced_geometry_pipeline_different_data_types(webgpu_device):
    """Test pipeline with different data types."""
    # Test with Vec2 data type
    pipeline = InstancedGeometryPipelineMultiColour(webgpu_device, data_type="Vec2")
    assert pipeline._stride == 8  # Vec2 = 2 floats * 4 bytes

    # Test with custom stride
    custom_pipeline = InstancedGeometryPipelineMultiColour(webgpu_device, stride=16)
    assert custom_pipeline._stride == 16
