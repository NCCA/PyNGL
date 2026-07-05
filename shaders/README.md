# Custom Shader Examples for PyNGL WebGPU

This directory contains example WGSL shaders that demonstrate how to create custom rendering effects with the PyNGL WebGPU pipeline system.

## Available Examples

### 1. gradient_triangle.wgsl
Creates animated gradient triangles with barycentric coordinate-based coloring. Shows how to:
- Use vertex colours with gradient effects
- Calculate barycentric coordinates in the vertex shader
- Create smooth color transitions across triangles

### 2. wave_points.wgsl
Demonstrates animated point sprites with wave displacement effects. Shows how to:
- Create point sprites with custom shapes
- Apply time-based animations
- Use distance-based color calculations
- Implement soft edge blending for points

### 3. rainbow_wireframe.wgsl
Creates animated rainbow-colored wireframe lines with pulsing effects. Shows how to:
- Generate rainbow colors using trigonometric functions
- Create time-based pulsing animations
- Implement line rendering with custom colors

### 4. particle_explosion.wgsl
Simulates particle explosion physics with gravity and fade effects. Shows how to:
- Implement particle physics simulation with gravity
- Create time-based life cycles for particles
- Use heat-based coloring (fast particles = hot colors)
- Generate point sprites with soft edges and texture effects

## How to Use These Shaders

### Method 1: Using the Demo
Run the WebGPU demo to see all custom shaders in action:
```bash
uv run python -m ncca.ngl.webgpu
```
The demo now includes 4 custom shader examples:
- **Gradient Triangles**: Barycentric gradient effects
- **Wave Points**: Animated point sprites with displacement
- **Rainbow Wireframe**: Pulsing rainbow-colored lines  
- **Particle Explosion**: Physics-based particle system with gravity

Use arrow keys to navigate manually, or let it auto-cycle every 2 seconds.

### Method 2: Loading Custom Shaders in Your Code

```python
import wgpu
from ncca.ngl.webgpu import CustomShaderPipeline

# Create device
device = wgpu.utils.get_default_device()

# Load shader from file
pipeline = CustomShaderPipeline.from_file(
    device,
    "path/to/your/shader.wgsl",
    vertex_formats=["Vec3", "Vec3"],  # position + colour
    primitive_topology=wgpu.PrimitiveTopology.triangle_list
)

# Set data and render
pipeline.set_data(
    positions=vertex_positions,
    colours=vertex_colours
)
pipeline.update_uniforms(mvp=projection_matrix)
pipeline.render(render_pass)
```

### Method 3: Using Shader Source Directly

```python
import wgpu
from ncca.ngl.webgpu import CustomShaderPipeline

shader_source = """
struct Uniforms {
    MVP : mat4x4<f32>,
    colour : vec4<f32>,
};

@group(0) @binding(0) var<uniform> uniforms : Uniforms;

struct VertexIn {
    @location(0) position : vec3<f32>,
};

struct VertexOut {
    @builtin(position) position : vec4<f32>,
};

@vertex
fn vertex_main(input: VertexIn) -> VertexOut {
    var output: VertexOut;
    output.position = uniforms.MVP * vec4<f32>(input.position, 1.0);
    return output;
}

@fragment
fn fragment_main() -> @location(0) vec4<f32> {
    return uniforms.colour;
}
"""

pipeline = CustomShaderPipeline(
    device,
    shader_source,
    vertex_formats=["Vec3"],
    primitive_topology=wgpu.PrimitiveTopology.triangle_list
)
```

## Shader Requirements

### Uniform Buffer Structure
Your shader should include a Uniforms struct with at least an MVP matrix:
```wgsl
struct Uniforms {
    MVP : mat4x4<f32>,
    // Add your custom uniform fields here
};
```

### Vertex Input
Configure vertex inputs to match your data:
```wgsl
struct VertexIn {
    @location(0) position : vec3<f32>,
    @location(1) colour : vec3<f32>,  // Optional
    // Add more attributes as needed
};
```

### Vertex and Fragment Functions
Your shader must have:
- A vertex function named `vertex_main`
- A fragment function named `fragment_main` that returns `vec4<f32>`

## Pipeline Configuration Options

When creating a CustomShaderPipeline, you can specify:

- **vertex_formats**: List of vertex data formats (e.g., `["Vec3", "Vec3"]` for position+colour)
- **primitive_topology**: Rendering topology (points, lines, triangles, etc.)
- **uniform_struct_definition**: Custom uniform structure (optional)
- **pipeline_label**: Debug label for the pipeline

## Tips for Custom Shaders

1. **Matrix Layout**: WebGPU uses column-major matrices. PyNGL provides matrices in the correct format.

2. **Color Space**: Use linear RGB values (0.0-1.0) for colors.

3. **Time-based Animation**: Pass time values through uniforms and use `sin()`, `cos()` for smooth animations.

4. **Coordinate Systems**: 
   - Vertex positions are in object space
   - MVP matrix transforms to clip space
   - Fragment shader works in normalized device coordinates

5. **Performance**: Minimize texture lookups and complex calculations in fragment shaders for better performance.

## Creating Your Own Shaders

1. Start with one of the examples as a template
2. Modify the uniform structure to add your custom parameters
3. Update the vertex input structure to match your data
4. Implement your vertex and fragment logic
5. Create the pipeline with appropriate vertex formats
6. Set data and update uniforms as needed

For more information on WGSL syntax and WebGPU concepts, see the [WebGPU specification](https://www.w3.org/TR/webgpu/).