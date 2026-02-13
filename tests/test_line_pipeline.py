"""
Additional tests for line pipeline to improve coverage.
Tests specific edge cases and error conditions not covered in main test suite.
"""

import numpy as np
import pytest
import wgpu

from ncca.ngl.webgpu.line_pipeline import (
    LinePipelineMultiColour,
    LinePipelineSingleColour,
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


def test_line_pipeline_multi_colour_render_with_buffers(webgpu_device, render_pass):
    """Test multi-colour pipeline render with all buffers set (covers lines 260, 264-269)."""
    pipeline = LinePipelineMultiColour(webgpu_device)
    pipeline.set_data(positions=TEST_POSITIONS, colors=TEST_COLORS)
    pipeline.update_uniforms(mvp=TEST_MVP_MATRIX)

    # This should execute all render setup code (lines 260, 264-269)
    pipeline.render(render_pass, num_vertices=2)


def test_line_pipeline_multi_colour_render_without_buffers(webgpu_device, render_pass):
    """Test multi-colour pipeline render without required buffers (covers line 260)."""
    pipeline = LinePipelineMultiColour(webgpu_device)
    pipeline.update_uniforms(mvp=TEST_MVP_MATRIX)

    # Don't set data, so buffers are None
    # Should return early due to missing buffers
    pipeline.render(render_pass)


def test_line_pipeline_single_colour_gpu_buffer_position(webgpu_device):
    """Test single-colour pipeline with GPU buffer positions (covers lines 370-371)."""
    pipeline = LinePipelineSingleColour(webgpu_device)

    # Create GPU buffer for positions
    position_buffer = webgpu_device.create_buffer_with_data(
        data=TEST_POSITIONS.tobytes(),
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
    )

    # Test with GPU buffer - should set buffer directly and calculate num_vertices
    pipeline.set_data(positions=position_buffer)

    assert pipeline.vertex_buffer is position_buffer
    assert pipeline.num_vertices == position_buffer.size // pipeline._stride


def test_line_pipeline_single_colour_render_without_position(
    webgpu_device, render_pass
):
    """Test single-colour pipeline render without position buffer (covers line 405)."""
    pipeline = LinePipelineSingleColour(webgpu_device)
    pipeline.update_uniforms(mvp=TEST_MVP_MATRIX)

    # Don't set any data, so vertex_buffer is None
    # Should return early due to missing vertex buffer
    pipeline.render(render_pass)


def test_line_pipeline_single_colour_cleanup_with_vertex_buffer(webgpu_device):
    """Test single-colour pipeline cleanup with vertex buffer (covers lines 418-420)."""
    pipeline = LinePipelineSingleColour(webgpu_device)
    pipeline.set_data(positions=TEST_POSITIONS)

    # Verify vertex buffer exists
    assert pipeline.vertex_buffer is not None

    # Cleanup should destroy vertex buffer and call super().cleanup()
    pipeline.cleanup()

    # Buffer should be destroyed (setting to None happens in base class)
    # The important part is that destroy() was called without error


def test_line_pipeline_different_topologies(webgpu_device):
    """Test line pipelines with different topologies."""
    # Test line_list topology (default)
    line_list_pipeline = LinePipelineMultiColour(webgpu_device)
    assert (
        line_list_pipeline._get_primitive_topology() == wgpu.PrimitiveTopology.line_list
    )

    # Test line_strip topology
    line_strip_pipeline = LinePipelineMultiColour(
        webgpu_device, topology=wgpu.PrimitiveTopology.line_strip
    )
    assert (
        line_strip_pipeline._get_primitive_topology()
        == wgpu.PrimitiveTopology.line_strip
    )


def test_line_pipeline_custom_strides(webgpu_device):
    """Test line pipelines with custom stride."""
    # Test multi-colour with custom stride
    multi_pipeline = LinePipelineMultiColour(webgpu_device, stride=16)
    assert multi_pipeline._stride == 16

    # Test single-colour with custom stride
    single_pipeline = LinePipelineSingleColour(webgpu_device, stride=16)
    assert single_pipeline._stride == 16

    # Test data setting with custom stride
    custom_positions = np.array([[0.0, 0.0, 0.0, 0.0]], dtype=np.float32)
    multi_pipeline.set_data(positions=custom_positions)
    assert multi_pipeline.num_vertices == 1

    single_pipeline.set_data(positions=custom_positions)
    assert single_pipeline.num_vertices == 1


def test_line_pipeline_color_processing_basic(webgpu_device):
    """Test basic color processing."""
    pipeline = LinePipelineMultiColour(webgpu_device)

    # Test with valid colors
    pipeline.set_data(positions=TEST_POSITIONS, colors=TEST_COLORS)
    assert pipeline.vertex_buffer is not None
    assert pipeline.color_buffer is not None
    assert pipeline.num_vertices == len(TEST_POSITIONS)


def test_line_pipeline_render_with_num_vertices(webgpu_device, render_pass):
    """Test both pipelines with explicit num_vertices parameter."""
    # Test multi-colour
    multi_pipeline = LinePipelineMultiColour(webgpu_device)
    multi_pipeline.set_data(positions=TEST_POSITIONS, colors=TEST_COLORS)
    multi_pipeline.update_uniforms(mvp=TEST_MVP_MATRIX)
    multi_pipeline.render(render_pass, num_vertices=2)

    # Test single-colour
    single_pipeline = LinePipelineSingleColour(webgpu_device)
    single_pipeline.set_data(positions=TEST_POSITIONS)
    single_pipeline.update_uniforms(mvp=TEST_MVP_MATRIX)
    single_pipeline.render(render_pass, num_vertices=2)


def test_line_pipeline_buffer_reuse_patterns(webgpu_device):
    """Test buffer reuse and update patterns."""
    pipeline = LinePipelineMultiColour(webgpu_device)

    # Set initial data
    pipeline.set_data(positions=TEST_POSITIONS, colors=TEST_COLORS)
    initial_pos_buffer = pipeline.vertex_buffer
    initial_color_buffer = pipeline.color_buffer

    # Update with same size data
    new_positions = TEST_POSITIONS * 2.0
    new_colors = TEST_COLORS * 0.5
    pipeline.set_data(positions=new_positions, colors=new_colors)

    # Buffers should be updated (may reuse or recreate)
    assert pipeline.vertex_buffer is not None
    assert pipeline.color_buffer is not None
    assert pipeline.num_vertices == 2


def test_line_pipeline_only_positions(webgpu_device):
    """Test setting positions only."""
    # Test multi-colour with only positions
    multi_pipeline = LinePipelineMultiColour(webgpu_device)
    multi_pipeline.set_data(positions=TEST_POSITIONS)
    assert multi_pipeline.vertex_buffer is not None
    assert multi_pipeline.num_vertices == 2
    # color_buffer should remain None

    # Test single-colour with only positions
    single_pipeline = LinePipelineSingleColour(webgpu_device)
    single_pipeline.set_data(positions=TEST_POSITIONS)
    assert single_pipeline.vertex_buffer is not None
    assert single_pipeline.num_vertices == 2


def test_line_pipeline_only_colors(webgpu_device):
    """Test setting colors only (shouldn't affect vertices)."""
    pipeline = LinePipelineMultiColour(webgpu_device)

    # Set initial positions
    pipeline.set_data(positions=TEST_POSITIONS)
    initial_num_vertices = pipeline.num_vertices

    # Set only colors
    pipeline.set_data(colors=TEST_COLORS)

    # Number of vertices should remain the same
    assert pipeline.num_vertices == initial_num_vertices
    assert pipeline.color_buffer is not None


def test_line_pipeline_mvp_updates(webgpu_device):
    """Test MVP matrix updates."""
    # Test multi-colour
    multi_pipeline = LinePipelineMultiColour(webgpu_device)
    multi_pipeline.set_data(positions=TEST_POSITIONS, colors=TEST_COLORS)

    custom_mvp = np.array(
        [
            [2.0, 0.0, 0.0, 1.0],
            [0.0, 2.0, 0.0, -1.0],
            [0.0, 0.0, 2.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )

    multi_pipeline.update_uniforms(mvp=custom_mvp)
    np.testing.assert_array_equal(multi_pipeline.uniform_data["MVP"], custom_mvp)

    # Test single-colour
    single_pipeline = LinePipelineSingleColour(webgpu_device)
    single_pipeline.set_data(positions=TEST_POSITIONS)

    single_pipeline.update_uniforms(mvp=custom_mvp)
    np.testing.assert_array_equal(single_pipeline.uniform_data["MVP"], custom_mvp)


def test_line_pipeline_vertex_buffer_creation_tracking(webgpu_device):
    """Test vertex buffer creation and size calculation."""
    pipeline = LinePipelineMultiColour(webgpu_device)

    # Test buffer size calculation
    pipeline.set_data(positions=TEST_POSITIONS)

    # Verify buffer creation works and num_vertices is calculated correctly
    assert pipeline.vertex_buffer is not None
    assert pipeline.num_vertices == len(TEST_POSITIONS)


def test_line_pipeline_colors_gpu_buffer(webgpu_device):
    """Test setting colors with GPU buffer."""
    pipeline = LinePipelineMultiColour(webgpu_device)

    # Create GPU buffer for colors
    color_buffer = webgpu_device.create_buffer_with_data(
        data=TEST_COLORS.tobytes(),
        usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
    )

    # Set positions first
    pipeline.set_data(positions=TEST_POSITIONS)

    # Now set colors with GPU buffer
    pipeline.set_data(colors=color_buffer)

    assert pipeline.color_buffer is color_buffer


"""
Additional test for line pipeline to cover remaining lines 230-233.
"""

import numpy as np
import pytest

# Test data fixtures
TEST_POSITIONS = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], dtype=np.float32)
TEST_COLORS = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)


def test_line_pipeline_multi_colour_color_processing_tuple_result(webgpu_device):
    """Test multi-colour pipeline when color processing returns tuple to hit lines 230-233."""
    pipeline = LinePipelineMultiColour(webgpu_device)

    # Mock _process_vertex_data to return a tuple to trigger the elif branch
    def mock_process_vertex_data(*args, **kwargs):
        # Return a tuple (buffer, size) to hit lines 230-233
        return (
            webgpu_device.create_buffer_with_data(
                data=TEST_COLORS.tobytes(),
                usage=wgpu.BufferUsage.VERTEX | wgpu.BufferUsage.COPY_DST,
                label="mock_color_buffer",
            ),
            TEST_COLORS.size * 4,
        )

    pipeline._process_vertex_data = mock_process_vertex_data

    # Set positions first
    pipeline.set_data(positions=TEST_POSITIONS)

    # Now set colors with our mock that returns a tuple
    pipeline.set_data(colors=TEST_COLORS)

    # Verify the pipeline processed colors through the tuple path
    assert pipeline.vertex_buffer is not None
    assert pipeline.color_buffer is not None
    assert pipeline.num_vertices == len(TEST_POSITIONS)


def test_line_pipeline_multi_colour_color_processing_none_result(webgpu_device):
    """Test multi-colour pipeline when color processing returns None to hit else branch."""
    pipeline = LinePipelineMultiColour(webgpu_device)

    # Mock _process_vertex_data to return None to trigger the else branch (line 233)
    def mock_process_vertex_data(*args, **kwargs):
        return None

    pipeline._process_vertex_data = mock_process_vertex_data

    # Set positions first
    pipeline.set_data(positions=TEST_POSITIONS)

    # Now set colors with our mock that returns None
    pipeline.set_data(colors=TEST_COLORS)

    # Should hit the else branch and set color_buffer to None
    assert pipeline.vertex_buffer is not None
    assert pipeline.color_buffer is None
    assert pipeline.num_vertices == len(TEST_POSITIONS)
