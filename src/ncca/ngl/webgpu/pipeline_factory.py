"""Extensible factory for WebGPU pipelines.

It will create several default pipelines used in demos and allow the user
to create custom pipelines. Provides abstract base class and factory for
creating various pipeline types.
"""

from enum import Enum
from typing import Any, Callable, Dict

import wgpu

from .base_webgpu_pipeline import BaseWebGPUPipeline
from .point_pipeline import PointPipelineMultiColour, PointPipelineSingleColour
from .point_list_pipeline import (
    PointListPipelineMultiColour,
    PointListPipelineSingleColour,
)
from .line_pipeline import LinePipelineMultiColour, LinePipelineSingleColour
from .triangle_pipeline import TrianglePipelineMultiColour, TrianglePipelineSingleColour
from .instanced_geometry_pipeline import (
    InstancedGeometryPipelineMultiColour,
    InstancedGeometryPipelineSingleColour,
)


class PipelineType(Enum):
    """Enumeration of available pipeline types."""

    MULTI_COLOURED_LINES = "multi_coloured_lines"
    SINGLE_COLOUR_LINES = "single_colour_lines"
    MULTI_COLOURED_POINTS = "multi_coloured_points"
    SINGLE_COLOUR_POINTS = "single_colour_points"
    MULTI_COLOURED_TRIANGLES = "multi_coloured_triangles"
    SINGLE_COLOUR_TRIANGLES = "single_colour_triangles"
    TRIANGLE_LIST_MULTI_COLOURED = "triangle_list_multi_coloured"
    TRIANGLE_LIST_SINGLE_COLOUR = "triangle_list_single_colour"
    TRIANGLE_STRIP_MULTI_COLOURED = "triangle_strip_multi_coloured"
    TRIANGLE_STRIP_SINGLE_COLOUR = "triangle_strip_single_colour"
    POINT_LIST_MULTI_COLOURED = "point_list_multi_coloured"
    POINT_LIST_SINGLE_COLOUR = "point_list_single_colour"
    MULTI_COLOURED_INSTANCED_GEOMETRY = "multi_coloured_instanced_geometry"
    SINGLE_COLOUR_INSTANCED_GEOMETRY = "single_colour_instanced_geometry"


# Backward compatibility alias
BasePipeline = BaseWebGPUPipeline

# A registered entry is either a pipeline class or a factory callable (e.g. a
# lambda binding a fixed keyword like `topology`); both are called as
# `factory(device, **kwargs)` by create_pipeline.
PipelineFactoryFn = Callable[..., BaseWebGPUPipeline]


class _PipelineFactory:
    """Factory for creating pipeline instances with various configurations."""

    def __init__(self) -> None:
        """Initialize the pipeline factory with default pipeline types."""
        self._pipeline_registry: Dict[PipelineType, PipelineFactoryFn] = {}
        self.register_pipeline(
            PipelineType.MULTI_COLOURED_POINTS, PointPipelineMultiColour
        )
        self.register_pipeline(
            PipelineType.SINGLE_COLOUR_POINTS, PointPipelineSingleColour
        )
        self.register_pipeline(
            PipelineType.MULTI_COLOURED_LINES, LinePipelineMultiColour
        )
        self.register_pipeline(
            PipelineType.SINGLE_COLOUR_LINES, LinePipelineSingleColour
        )
        self.register_pipeline(
            PipelineType.MULTI_COLOURED_TRIANGLES, TrianglePipelineMultiColour
        )
        self.register_pipeline(
            PipelineType.SINGLE_COLOUR_TRIANGLES, TrianglePipelineSingleColour
        )

        # Triangle pipelines pinned to a specific topology: registered as
        # factory callables (rather than classes) so the fixed `topology`
        # keyword can be bound while still forwarding any other **kwargs
        # create_pipeline receives (e.g. `colour`, `data_type`) to the
        # underlying pipeline class.
        self.register_pipeline(
            PipelineType.TRIANGLE_LIST_MULTI_COLOURED,
            lambda device, **kwargs: TrianglePipelineMultiColour(
                device, topology=wgpu.PrimitiveTopology.triangle_list, **kwargs
            ),
        )
        self.register_pipeline(
            PipelineType.TRIANGLE_LIST_SINGLE_COLOUR,
            lambda device, **kwargs: TrianglePipelineSingleColour(
                device, topology=wgpu.PrimitiveTopology.triangle_list, **kwargs
            ),
        )
        self.register_pipeline(
            PipelineType.TRIANGLE_STRIP_MULTI_COLOURED,
            lambda device, **kwargs: TrianglePipelineMultiColour(
                device, topology=wgpu.PrimitiveTopology.triangle_strip, **kwargs
            ),
        )
        self.register_pipeline(
            PipelineType.TRIANGLE_STRIP_SINGLE_COLOUR,
            lambda device, **kwargs: TrianglePipelineSingleColour(
                device, topology=wgpu.PrimitiveTopology.triangle_strip, **kwargs
            ),
        )
        self.register_pipeline(
            PipelineType.POINT_LIST_MULTI_COLOURED, PointListPipelineMultiColour
        )
        self.register_pipeline(
            PipelineType.POINT_LIST_SINGLE_COLOUR, PointListPipelineSingleColour
        )
        self.register_pipeline(
            PipelineType.MULTI_COLOURED_INSTANCED_GEOMETRY,
            InstancedGeometryPipelineMultiColour,
        )
        self.register_pipeline(
            PipelineType.SINGLE_COLOUR_INSTANCED_GEOMETRY,
            InstancedGeometryPipelineSingleColour,
        )

    def register_pipeline(
        self, pipeline_type: PipelineType, pipeline_factory: PipelineFactoryFn
    ) -> None:
        """Register a custom pipeline type.

        Args:
            pipeline_type: Enum identifier for the pipeline
            pipeline_factory: Pipeline class, or a factory callable with the
                same `(device, **kwargs) -> BaseWebGPUPipeline` signature, to
                register for this type
        """
        self._pipeline_registry[pipeline_type] = pipeline_factory

    def create_pipeline(
        self, device: wgpu.GPUDevice, pipeline_type: PipelineType, **kwargs: Any
    ) -> BaseWebGPUPipeline:
        """Create a pipeline instance.

        Args:
            device: WebGPU device
            pipeline_type: Type of pipeline to create
            **kwargs: Pipeline-specific configuration parameters

        Returns:
            Configured pipeline instance

        Raises:
            ValueError: If pipeline type is not registered
        """
        if pipeline_type not in self._pipeline_registry:
            raise ValueError(
                f"Unknown pipeline type: {pipeline_type}. Available types: {list(self._pipeline_registry.keys())}"
            )

        pipeline_factory = self._pipeline_registry[pipeline_type]
        return pipeline_factory(device, **kwargs)


PipelineFactory = _PipelineFactory()
