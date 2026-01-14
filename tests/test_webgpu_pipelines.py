import wgpu
import wgpu.utils

from ncca.ngl.webgpu import PipelineFactory, PipelineType
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


def test_pipeline_create_point_coloured(webgpu_device):
    # Create a pipeline using the factory
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_POINTS
    )
    assert pipeline is not None
    assert isinstance(pipeline, PointPipelineMultiColour)


def test_pipeline_create_point_single_coloured(webgpu_device):
    # Create a pipeline using the factory
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_POINTS
    )
    assert pipeline is not None
    assert isinstance(pipeline, PointPipelineSingleColour)


def test_pipeline_create_triangle_multi_coloured(webgpu_device):
    # Create a pipeline using factory
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.MULTI_COLOURED_TRIANGLES
    )
    assert pipeline is not None
    assert isinstance(pipeline, TrianglePipelineMultiColour)


def test_pipeline_create_triangle_single_coloured(webgpu_device):
    # Create a pipeline using factory
    pipeline = PipelineFactory.create_pipeline(
        webgpu_device, PipelineType.SINGLE_COLOUR_TRIANGLES
    )
    assert pipeline is not None
    assert isinstance(pipeline, TrianglePipelineSingleColour)
