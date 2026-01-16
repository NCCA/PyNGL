"""
Additional tests for point pipeline to improve coverage.
Tests specific edge cases and error conditions not covered in main test suite.
"""

import pytest
import wgpu
import numpy as np

from ncca.ngl.webgpu import PipelineFactory, PipelineType
from ncca.ngl.webgpu.point_pipeline import (
    PointPipelineMultiColour,
    PointPipelineSingleColour,
)


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


def test_point_pipeline_multi_colour_default_colour_result_tuple(webgpu_device):
    """Test multi-colour pipeline when colour processing returns tuple (covers lines 248-251)."""
    pipeline = PointPipelineMultiColour(webgpu_device)

    # Mock the _process_vertex_data to return a tuple (simulating edge case)
    original_process = pipeline._process_vertex_data

    def mock_process_vertex_data(*args, **kwargs):
        # Return a tuple to trigger the elif branch
        return (None, None)

    pipeline._process_vertex_data = mock_process_vertex_data

    # Set data with None colours (should trigger default colour creation)
    pipeline.set_data(positions=TEST_POSITIONS, colours=None)

    # Should hit the elif colour_result branch (lines 248-251)
    assert pipeline.position_buffer is not None
    assert pipeline.colour_buffer is None  # Due to our mock


def test_point_pipeline_multi_colour_custom_colour_result_tuple(webgpu_device):
    """Test multi-colour pipeline when colour processing returns tuple (covers lines 261-264)."""
    pipeline = PointPipelineMultiColour(webgpu_device)

    # Mock the _process_vertex_data to return a tuple
    def mock_process_vertex_data(*args, **kwargs):
        # Return a tuple to trigger the elif branch
        return (None, None)

    pipeline._process_vertex_data = mock_process_vertex_data

    # Set data with colours (should trigger colour processing)
    pipeline.set_data(positions=TEST_POSITIONS, colours=TEST_COLORS)

    # Should hit the elif colour_result branch (lines 261-264)
    assert pipeline.position_buffer is not None
    assert pipeline.colour_buffer is None  # Due to our mock


def test_point_pipeline_multi_colour_update_view_matrix(webgpu_device):
    """Test multi-colour pipeline view matrix update (covers line 281)."""
    pipeline = PointPipelineMultiColour(webgpu_device)
    pipeline.set_data(positions=TEST_POSITIONS, colours=TEST_COLORS)

    view_matrix = np.eye(4, dtype=np.float32)
    view_matrix[0, 3] = 5.0  # Translate X

    # Test view_matrix update
    pipeline.update_uniforms(
        mvp=TEST_MVP_MATRIX, view_matrix=view_matrix, point_size=2.0
    )

    assert pipeline.uniform_buffer is not None
    np.testing.assert_array_equal(pipeline.uniform_data["ViewMatrix"], view_matrix)


def test_point_pipeline_multi_colour_render_with_buffers(webgpu_device, render_pass):
    """Test multi-colour pipeline render with all buffers (covers lines 302-309)."""
    pipeline = PointPipelineMultiColour(webgpu_device)
    pipeline.set_data(positions=TEST_POSITIONS, colours=TEST_COLORS)
    pipeline.update_uniforms(mvp=TEST_MVP_MATRIX)

    # This should execute all the render setup code (lines 302-309)
    pipeline.render(render_pass, num_points=2)


def test_point_pipeline_single_colour_gpu_buffer_position(webgpu_device):
    """Test single-colour pipeline with GPU buffer positions (covers lines 401-402)."""
    pipeline = PointPipelineSingleColour(webgpu_device)

    # Create GPU buffer for positions
    position_buffer = webgpu_device.create_buffer_with_data(
        data=TEST_POSITIONS.tobytes(),
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
    )

    # Test with GPU buffer - should set buffer directly and calculate num_points
    pipeline.set_data(positions=position_buffer)

    assert pipeline.position_buffer is position_buffer
    assert pipeline.num_points == position_buffer.size // pipeline._stride


def test_point_pipeline_single_colour_update_view_matrix(webgpu_device):
    """Test single-colour pipeline view matrix update (covers line 427)."""
    pipeline = PointPipelineSingleColour(webgpu_device)
    pipeline.set_data(positions=TEST_POSITIONS)

    view_matrix = np.eye(4, dtype=np.float32)
    view_matrix[1, 3] = 3.0  # Translate Y

    # Test view_matrix update
    pipeline.update_uniforms(
        mvp=TEST_MVP_MATRIX,
        view_matrix=view_matrix,
        colour=np.array([1.0, 0.0, 0.0]),
        point_size=2.0,
    )

    assert pipeline.uniform_buffer is not None
    np.testing.assert_array_equal(pipeline.uniform_data["ViewMatrix"], view_matrix)


def test_point_pipeline_single_colour_render_without_position(
    webgpu_device, render_pass
):
    """Test single-colour pipeline render without position buffer (covers line 449)."""
    pipeline = PointPipelineSingleColour(webgpu_device)

    # Don't set any data, so position_buffer is None
    pipeline.update_uniforms(mvp=TEST_MVP_MATRIX)

    # Should return early due to missing position buffer
    pipeline.render(render_pass)


def test_point_pipeline_single_colour_cleanup_with_position(webgpu_device):
    """Test single-colour pipeline cleanup with position buffer (covers lines 461-463)."""
    pipeline = PointPipelineSingleColour(webgpu_device)
    pipeline.set_data(positions=TEST_POSITIONS)

    # Verify position buffer exists
    assert pipeline.position_buffer is not None

    # Cleanup should destroy position buffer and call super().cleanup()
    pipeline.cleanup()

    # Buffer should be destroyed (setting to None happens in base class)
    # The important part is that destroy() was called without error


def test_point_pipeline_multi_colour_custom_strides(webgpu_device):
    """Test multi-colour pipeline with custom stride."""
    # Test with custom stride
    pipeline = PointPipelineMultiColour(webgpu_device, stride=16)
    assert pipeline._stride == 16

    # Test data setting with custom stride
    custom_positions = np.array([[0.0, 0.0, 0.0, 0.0]], dtype=np.float32)
    pipeline.set_data(positions=custom_positions)

    assert pipeline.num_points == 1
    assert pipeline.position_buffer is not None


def test_point_pipeline_single_colour_custom_strides(webgpu_device):
    """Test single-colour pipeline with custom stride."""
    # Test with custom stride
    pipeline = PointPipelineSingleColour(webgpu_device, stride=16)
    assert pipeline._stride == 16

    # Test data setting with custom stride
    custom_positions = np.array([[0.0, 0.0, 0.0, 0.0]], dtype=np.float32)
    pipeline.set_data(positions=custom_positions)

    assert pipeline.num_points == 1
    assert pipeline.position_buffer is not None


def test_point_pipeline_multi_colour_empty_colors_processing(webgpu_device):
    """Test multi-colour pipeline edge case in color processing."""
    pipeline = PointPipelineMultiColour(webgpu_device)

    # Mock _process_vertex_data to return empty/falsy values to test different paths
    call_count = 0

    def mock_process_vertex_data(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call (default colors) - return None
            return None
        else:
            # Second call (custom colors) - return empty tuple
            return ()

    pipeline._process_vertex_data = mock_process_vertex_data

    # Test default colors (None return)
    pipeline.set_data(positions=TEST_POSITIONS, colours=None)
    assert pipeline.position_buffer is not None
    assert pipeline.colour_buffer is None

    # Test custom colors (empty tuple return)
    pipeline.set_data(positions=TEST_POSITIONS, colours=TEST_COLORS)
    assert pipeline.position_buffer is not None
    assert pipeline.colour_buffer is None


def test_point_pipeline_single_colour_colour_and_size_updates(webgpu_device):
    """Test single-colour pipeline colour and size updates."""
    pipeline = PointPipelineSingleColour(webgpu_device)
    pipeline.set_data(positions=TEST_POSITIONS)

    # Test updating colour only
    pipeline.update_uniforms(colour=np.array([0.5, 0.25, 0.75]))
    expected_colour = np.array([0.5, 0.25, 0.75, 1.0], dtype=np.float32)
    np.testing.assert_array_equal(
        pipeline.uniform_data["ColourSize"][:3], expected_colour[:3]
    )

    # Test updating point size only
    pipeline.update_uniforms(point_size=3.5)
    assert pipeline.uniform_data["ColourSize"][3] == 3.5

    # Test updating both colour and size
    pipeline.update_uniforms(colour=np.array([1.0, 0.0, 0.0]), point_size=5.0)
    expected = np.array([1.0, 0.0, 0.0, 5.0], dtype=np.float32)
    np.testing.assert_array_equal(pipeline.uniform_data["ColourSize"], expected)


def test_point_pipeline_render_with_num_points(webgpu_device, render_pass):
    """Test both pipelines with explicit num_points parameter."""
    # Test multi-colour
    multi_pipeline = PointPipelineMultiColour(webgpu_device)
    multi_pipeline.set_data(positions=TEST_POSITIONS, colours=TEST_COLORS)
    multi_pipeline.update_uniforms(mvp=TEST_MVP_MATRIX)
    multi_pipeline.render(render_pass, num_points=2)

    # Test single-colour
    single_pipeline = PointPipelineSingleColour(webgpu_device)
    single_pipeline.set_data(positions=TEST_POSITIONS)
    single_pipeline.update_uniforms(mvp=TEST_MVP_MATRIX)
    single_pipeline.render(render_pass, num_points=2)


def test_point_pipeline_edge_case_data_types(webgpu_device):
    """Test pipelines with different data types."""
    # Test with Vec2 data
    vec2_positions = np.array([[0.0, 0.0], [1.0, 1.0]], dtype=np.float32)

    multi_pipeline = PointPipelineMultiColour(webgpu_device, data_type="Vec2")
    multi_pipeline.set_data(positions=vec2_positions)
    assert multi_pipeline.num_points == 2

    single_pipeline = PointPipelineSingleColour(webgpu_device, data_type="Vec2")
    single_pipeline.set_data(positions=vec2_positions)
    assert single_pipeline.num_points == 2


def test_point_pipeline_buffer_reuse_patterns(webgpu_device):
    """Test buffer reuse and update patterns."""
    pipeline = PointPipelineMultiColour(webgpu_device)

    # Set initial data
    pipeline.set_data(positions=TEST_POSITIONS, colours=TEST_COLORS)
    initial_pos_buffer = pipeline.position_buffer
    initial_colour_buffer = pipeline.colour_buffer

    # Update with same size data
    new_positions = TEST_POSITIONS * 2.0
    new_colours = TEST_COLORS * 0.5
    pipeline.set_data(positions=new_positions, colours=new_colours)

    # Buffers should be updated (may reuse or recreate)
    assert pipeline.position_buffer is not None
    assert pipeline.colour_buffer is not None
    assert pipeline.num_points == 3
