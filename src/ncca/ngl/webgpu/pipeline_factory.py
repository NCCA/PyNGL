"""
Extensible factory for WebGPU pipelines It will create several default pipelines used in demos
and allow the user to create custom pipelines.
Provides abstract base class and factory for creating various pipeline types.
"""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Type

import numpy as np
import wgpu


class PipelineType(Enum):
    """Enumeration of available pipeline types."""

    MULTI_COLOURED_LINES = "multi_coloured_lines"
    SINGLE_COLOUR_LINES = "single_colour_lines"
    MULTI_COLOURED_POINTS = "multi_coloured_points"
    SINGLE_COLOUR_POINTS = "single_colour_points"


class BasePipeline(ABC):
    """
    Abstract base class for all rendering pipelines.

    Defines the interface that all pipeline implementations must follow.
    """

    def __init__(
        self,
        device: wgpu.GPUDevice,
        texture_format: wgpu.TextureFormat = wgpu.TextureFormat.rgba8unorm,
        depth_format: wgpu.TextureFormat = wgpu.TextureFormat.depth24plus,
        msaa_sample_count: int = 4,
    ):
        """
        Initialize base pipeline.

        Args:
            device: WebGPU device
            texture_format: Color attachment format
            depth_format: Depth attachment format
            msaa_sample_count: Number of MSAA samples
        """
        self.device = device
        self.texture_format = texture_format
        self.depth_format = depth_format
        self.msaa_sample_count = msaa_sample_count

        # Core pipeline resources
        self.pipeline: Optional[wgpu.GPURenderPipeline] = None
        self.uniform_buffer: Optional[wgpu.GPUBuffer] = None
        self.bind_group: Optional[wgpu.GPUBindGroup] = None

    @abstractmethod
    def _create_pipeline(self) -> None:
        """Create the render pipeline. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def set_data(self, **kwargs) -> None:
        """
        Set rendering data (vertices, colors, etc.).

        Args:
            **kwargs: Pipeline-specific data parameters
        """
        pass

    @abstractmethod
    def update_uniforms(self, **kwargs) -> None:
        """
        Update uniform buffer values.

        Args:
            **kwargs: Pipeline-specific uniform parameters
        """
        pass

    @abstractmethod
    def render(self, render_pass: wgpu.GPURenderPassEncoder, **kwargs) -> None:
        """
        Render using this pipeline.

        Args:
            render_pass: Active render pass encoder
            **kwargs: Pipeline-specific render parameters
        """
        pass

    def cleanup(self) -> None:
        """Release pipeline resources. Can be overridden for additional cleanup."""
        if self.uniform_buffer:
            self.uniform_buffer.destroy()


class PipelineFactory:
    """
    Factory for creating pipeline instances with various configurations.
    """

    def __init__(self):
        """Initialize the pipeline factory with default pipeline types."""
        self._pipeline_registry: Dict[PipelineType, Type[BasePipeline]] = dict()

    def register_pipeline(self, pipeline_type: PipelineType, pipeline_class: Type[BasePipeline]) -> None:
        """
        Register a custom pipeline type.

        Args:
            pipeline_type: Enum identifier for the pipeline
            pipeline_class: Pipeline class to register
        """
        self._pipeline_registry[pipeline_type] = pipeline_class

    def create_pipeline(self, device: wgpu.GPUDevice, pipeline_type: PipelineType, **kwargs) -> BasePipeline:
        """
        Create a pipeline instance.

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

        pipeline_class = self._pipeline_registry[pipeline_type]
        return pipeline_class(device, **kwargs)

    # def create_line_pipeline(
    #     self,
    #     device: wgpu.GPUDevice,
    #     topology: wgpu.PrimitiveTopology = wgpu.PrimitiveTopology.line_strip,
    #     shader_path: Optional[Path] = None,
    #     **kwargs,
    # ) -> LinePipeline:
    #     """
    #     Convenience method to create a line pipeline.

    #     Args:
    #         device: WebGPU device
    #         topology: Line topology
    #         shader_path: Optional custom shader file
    #         **kwargs: Additional pipeline parameters

    #     Returns:
    #         Configured line pipeline
    #     """
    #     return self.create_pipeline(device, PipelineType.LINE, topology=topology, shader_path=shader_path, **kwargs)


# Example usage:
"""
# Initialize factory
factory = PipelineFactory()

# Create a basic line pipeline with defaults
line_pipeline = factory.create_line_pipeline(
    device=gpu_device,
    topology=wgpu.PrimitiveTopology.line_strip
)

# Create a line pipeline with custom shader
custom_line_pipeline = factory.create_line_pipeline(
    device=gpu_device,
    shader_path=Path("shaders/custom_line.wgsl"),
    topology=wgpu.PrimitiveTopology.line_list
)

# Set data and render
vertices = np.array([[0, 0], [1, 0], [1, 1]], dtype=np.float32)
colors = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=np.float32)

line_pipeline.set_data(vertices=vertices, colors=colors)
line_pipeline.update_uniforms(mvp=projection_matrix, line_width=2.0)
line_pipeline.render(render_pass)

# Register custom pipeline type
class MyCustomPipeline(BasePipeline):
    # ... implementation ...
    pass

factory.register_pipeline(PipelineType.CUSTOM, MyCustomPipeline)
custom_pipeline = factory.create_pipeline(device, PipelineType.CUSTOM)
"""
