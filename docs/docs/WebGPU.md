# WebGPU Classes

See the [WebGPU section](webgpu/index.md) for tutorials and usage guides.

## WebGPUWidget

::: ncca.ngl.webgpu.WebGPUWidget

## PipelineType

::: ncca.ngl.webgpu.PipelineType

## PipelineFactory

`PipelineFactory` is a module-level singleton instance of the factory
class below — use it directly
(`PipelineFactory.create_pipeline(device, pipeline_type)`) rather than
instantiating your own.

::: ncca.ngl.webgpu.pipeline_factory._PipelineFactory

## NGLToWebGPU

::: ncca.ngl.webgpu.NGLToWebGPU

## BaseWebGPUPipeline

::: ncca.ngl.webgpu.base_webgpu_pipeline.BaseWebGPUPipeline

## BasePointPipeline

::: ncca.ngl.webgpu.base_webgpu_pipeline.BasePointPipeline

## CustomShaderPipeline

::: ncca.ngl.webgpu.custom_shader_pipeline.CustomShaderPipeline

## Built-in pipeline classes

These are the concrete classes behind each
[`PipelineType`](#pipelinetype); you normally create them through
`PipelineFactory` rather than directly.

### PointPipelineMultiColour

::: ncca.ngl.webgpu.point_pipeline.PointPipelineMultiColour

### PointPipelineSingleColour

::: ncca.ngl.webgpu.point_pipeline.PointPipelineSingleColour

### PointListPipelineMultiColour

::: ncca.ngl.webgpu.point_list_pipeline.PointListPipelineMultiColour

### PointListPipelineSingleColour

::: ncca.ngl.webgpu.point_list_pipeline.PointListPipelineSingleColour

### LinePipelineMultiColour

::: ncca.ngl.webgpu.line_pipeline.LinePipelineMultiColour

### LinePipelineSingleColour

::: ncca.ngl.webgpu.line_pipeline.LinePipelineSingleColour

### TrianglePipelineMultiColour

::: ncca.ngl.webgpu.triangle_pipeline.TrianglePipelineMultiColour

### TrianglePipelineSingleColour

::: ncca.ngl.webgpu.triangle_pipeline.TrianglePipelineSingleColour

### InstancedGeometryPipelineMultiColour

::: ncca.ngl.webgpu.instanced_geometry_pipeline.InstancedGeometryPipelineMultiColour

### InstancedGeometryPipelineSingleColour

::: ncca.ngl.webgpu.instanced_geometry_pipeline.InstancedGeometryPipelineSingleColour
