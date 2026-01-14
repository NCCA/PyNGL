import wgpu
import wgpu.utils

from ncca.ngl.webgpu import PipelineFactory, PipelineType
from ncca.ngl.webgpu.point_pipeline import (
    PointPipelineMultiColour,
    PointPipelineSingleColour,
)


def test_initial_factory():
    assert len(PipelineFactory._pipeline_registry) == 2


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
