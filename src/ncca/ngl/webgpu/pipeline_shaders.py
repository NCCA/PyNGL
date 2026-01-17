POINT_SHADER_MULTI_COLOURED = """
@group(0) @binding(0) var<uniform> uniforms : Uniforms;
struct Uniforms
{
    MVP : mat4x4<f32>,
    ViewMatrix : mat4x4<f32>,
    size: f32,
    padding: u32,
    padding2: u32,
    padding3: u32,
};

struct VertexIn {
    @location(0) position: vec3<f32>,
    @location(1) colour: vec3<f32>,
};

// We now need to pass uv to the fragment shader
struct VertexOut {
    @builtin(position) position: vec4<f32>,
    @location(0) fragColour: vec3<f32>,
    @location(1) uv: vec2<f32>,
};

@vertex
fn vertex_main(input: VertexIn, @builtin(vertex_index) vertex_index: u32) -> VertexOut {
    var output: VertexOut;
    let quad_offsets = array<vec2<f32>, 4>(
        vec2<f32>(-1.0, -1.0), // bottom-left
        vec2<f32>(1.0, -1.0),  // bottom-right
        vec2<f32>(-1.0, 1.0),   // top-left
        vec2<f32>(1.0, 1.0)    // top-right
    );

    // Extract camera right and up vectors from view matrix
    let cameraRight = normalize(vec3<f32>(uniforms.ViewMatrix[0][0], uniforms.ViewMatrix[1][0], uniforms.ViewMatrix[2][0]));
    let cameraUp = normalize(vec3<f32>(uniforms.ViewMatrix[0][1], uniforms.ViewMatrix[1][1], uniforms.ViewMatrix[2][1]));

    // Calculate billboard offset in world space
    let offset2D = quad_offsets[vertex_index] * uniforms.size;
    let offset3D = cameraRight * offset2D.x + cameraUp * offset2D.y;
    let worldPos = input.position + offset3D;

    output.position = uniforms.MVP * vec4<f32>(worldPos, 1.0);
    output.fragColour = input.colour;
    // convert offset from -1 -> 1 to 0 -> 1 for uv
    output.uv = quad_offsets[vertex_index] * 0.5 + 0.5;

    return output;
}

@fragment
fn fragment_main(fragData: VertexOut) -> @location(0) vec4<f32>
{
    let center = vec2<f32>(0.5, 0.5); // Center of the quad in UV space
    let dist = distance(fragData.uv, center); // Distance from center
    let radius = 0.5; // Circle radius (quad is 1.0 in UV space)

    if (dist > radius)
    {
        discard; // Remove pixels outside the circle
    }

    return vec4<f32>(fragData.fragColour, 1.0); // Simple colour output
}
"""

POINT_SHADER_SINGLE_COLOUR = """
@group(0) @binding(0) var<uniform> uniforms : Uniforms;
struct Uniforms
{
    MVP : mat4x4<f32>,
    ViewMatrix : mat4x4<f32>,
    ColourSize: vec4<f32>,
};

struct VertexIn {
    @location(0) position: vec3<f32>,
};

// We now need to pass uv to the fragment shader
struct VertexOut {
    @builtin(position) position: vec4<f32>,
    @location(1) uv: vec2<f32>,
};

@vertex
fn vertex_main(input: VertexIn, @builtin(vertex_index) vertex_index: u32) -> VertexOut {
    var output: VertexOut;
    let quad_offsets = array<vec2<f32>, 4>(
        vec2<f32>(-1.0, -1.0), // bottom-left
        vec2<f32>(1.0, -1.0),  // bottom-right
        vec2<f32>(-1.0, 1.0),   // top-left
        vec2<f32>(1.0, 1.0)    // top-right
    );

    // Extract camera right and up vectors from view matrix
    let cameraRight = normalize(vec3<f32>(uniforms.ViewMatrix[0][0], uniforms.ViewMatrix[1][0], uniforms.ViewMatrix[2][0]));
    let cameraUp = normalize(vec3<f32>(uniforms.ViewMatrix[0][1], uniforms.ViewMatrix[1][1], uniforms.ViewMatrix[2][1]));

    // Calculate billboard offset in world space
    let offset2D = quad_offsets[vertex_index] * uniforms.ColourSize.w;
    let offset3D = cameraRight * offset2D.x + cameraUp * offset2D.y;
    let worldPos = input.position + offset3D;

    output.position = uniforms.MVP * vec4<f32>(worldPos, 1.0);
    // convert offset from -1 -> 1 to 0 -> 1 for uv
    output.uv = quad_offsets[vertex_index] * 0.5 + 0.5;

    return output;
}

@fragment
fn fragment_main(fragData: VertexOut) -> @location(0) vec4<f32>
{
    let center = vec2<f32>(0.5, 0.5); // Center of the quad in UV space
    let dist = distance(fragData.uv, center); // Distance from center
    let radius = 0.5; // Circle radius (quad is 1.0 in UV space)

    if (dist > radius)
    {
        discard; // Remove pixels outside the circle
    }

    return vec4<f32>(uniforms.ColourSize.xyz, 1.0); // Simple colour output
}
"""

INSTANCED_SHADER_MULTI_COLOURED = """
@group(0) @binding(0) var<uniform> uniforms : Uniforms;
struct Uniforms
{
    MVP : mat4x4<f32>,
    ViewMatrix : mat4x4<f32>,
    instance_transform: mat4x4<f32>,
};

struct InstanceData {
    @location(0) position: vec3<f32>,
    @location(1) colour: vec3<f32>,
    @location(2) instance_id: f32,
};

struct GeometryVertex {
    @location(3) geometry_position: vec3<f32>,
    @location(4) geometry_normal: vec3<f32>,
    @location(5) geometry_uv: vec2<f32>,
};

struct VertexOut {
    @builtin(position) position: vec4<f32>,
    @location(0) fragColour: vec3<f32>,
    @location(1) fragNormal: vec3<f32>,
    @location(2) fragUV: vec2<f32>,
    @location(3) worldPos: vec3<f32>,
};

@vertex
fn vertex_main(instance_data: InstanceData, geom_vertex: GeometryVertex, @builtin(vertex_index) vertex_index: u32) -> VertexOut {
    var output: VertexOut;

    // Transform geometry vertex by instance transform and position
    let transformed_vertex = uniforms.instance_transform * vec4<f32>(geom_vertex.geometry_position, 1.0);
    let world_position = transformed_vertex.xyz + instance_data.position;

    output.position = uniforms.MVP * vec4<f32>(world_position, 1.0);
    output.fragColour = instance_data.colour;

    // Transform normal by instance transform (skip translation)
    let normal_matrix = mat3x3<f32>(
        uniforms.instance_transform[0].xyz,
        uniforms.instance_transform[1].xyz,
        uniforms.instance_transform[2].xyz
    );
    output.fragNormal = normalize(normal_matrix * geom_vertex.geometry_normal);
    output.fragUV = geom_vertex.geometry_uv;
    output.worldPos = world_position;

    return output;
}

@fragment
fn fragment_main(fragData: VertexOut) -> @location(0) vec4<f32>
{
    // Enhanced diffuse lighting calculation

    // Light properties
    let light_direction = normalize(vec3<f32>(0.5, 1.0, 0.3));  // World space light direction
    let light_color = vec3<f32>(1.0, 1.0, 1.0);  // White light
    let ambient_intensity = 0.15;  // Lower ambient for better contrast
    let diffuse_intensity = 0.85;  // Higher diffuse for stronger lighting

    // Ambient component (base illumination)
    let ambient = vec3<f32>(ambient_intensity);

    // Diffuse component (Lambertian reflection)
    let normal = normalize(fragData.fragNormal);
    let n_dot_l = max(dot(normal, light_direction), 0.0);
    let diffuse = light_color * n_dot_l * diffuse_intensity;

    // Combine lighting components
    let final_lighting = ambient + diffuse;

    // Apply lighting to the fragment color
    let lit_color = fragData.fragColour * final_lighting;

    return vec4<f32>(lit_color, 1.0);
}
"""

INSTANCED_SHADER_SINGLE_COLOUR = """
@group(0) @binding(0) var<uniform> uniforms : Uniforms;
struct Uniforms
{
    MVP : mat4x4<f32>,
    ViewMatrix : mat4x4<f32>,
    colour: vec3<f32>,
    padding: f32,
    instance_transform: mat4x4<f32>,
};

struct InstanceData {
    @location(0) position: vec3<f32>,
    @location(1) instance_id: f32,
    @location(2) colour: vec3<f32>,  // Provided but ignored
};

struct GeometryVertexSingle {
    @location(3) geometry_position: vec3<f32>,
    @location(4) geometry_normal: vec3<f32>,
    @location(5) geometry_uv: vec2<f32>,
};

struct VertexOutSingle {
    @builtin(position) position: vec4<f32>,
    @location(0) fragNormal: vec3<f32>,
    @location(1) fragUV: vec2<f32>,
    @location(2) worldPos: vec3<f32>,
};

@vertex
fn vertex_main(instance_data: InstanceData, geom_vertex: GeometryVertexSingle, @builtin(vertex_index) vertex_index: u32) -> VertexOutSingle {
    var output: VertexOutSingle;

    // Transform geometry vertex by instance transform and position
    let transformed_vertex = uniforms.instance_transform * vec4<f32>(geom_vertex.geometry_position, 1.0);
    let world_position = transformed_vertex.xyz + instance_data.position;

    output.position = uniforms.MVP * vec4<f32>(world_position, 1.0);

    // Transform normal by instance transform (skip translation)
    let normal_matrix = mat3x3<f32>(
        uniforms.instance_transform[0].xyz,
        uniforms.instance_transform[1].xyz,
        uniforms.instance_transform[2].xyz
    );
    output.fragNormal = normalize(normal_matrix * geom_vertex.geometry_normal);
    output.fragUV = geom_vertex.geometry_uv;
    output.worldPos = world_position;

    return output;
}

@fragment
fn fragment_main(fragData: VertexOutSingle) -> @location(0) vec4<f32>
{
    // Enhanced diffuse lighting calculation

    // Light properties
    let light_direction = normalize(vec3<f32>(0.5, 1.0, 0.3));  // World space light direction
    let light_color = vec3<f32>(1.0, 1.0, 1.0);  // White light
    let ambient_intensity = 0.15;  // Lower ambient for better contrast
    let diffuse_intensity = 0.85;  // Higher diffuse for stronger lighting

    // Ambient component (base illumination)
    let ambient = vec3<f32>(ambient_intensity);

    // Diffuse component (Lambertian reflection)
    let normal = normalize(fragData.fragNormal);
    let n_dot_l = max(dot(normal, light_direction), 0.0);
    let diffuse = light_color * n_dot_l * diffuse_intensity;

    // Combine lighting components
    let final_lighting = ambient + diffuse;

    // Apply lighting to the uniform color
    let lit_color = uniforms.colour * final_lighting;

    return vec4<f32>(lit_color, 1.0);
}
"""


LINE_SHADER_SINGLE_COLOUR = """
// LineShader.wgsl
struct Uniforms {
    MVP: mat4x4<f32>,
};

@binding(0) @group(0) var<uniform> uniforms: Uniforms;

@vertex
fn vertex_main(@location(0) pos: vec3<f32>) -> @builtin(position) vec4<f32> {
    return uniforms.MVP * vec4<f32>(pos, 1.0);
}

@fragment
fn fragment_main() -> @location(0) vec4<f32> {
    return vec4<f32>(1.0, 1.0, 1.0, 1.0); // Grey color for grid lines
}
"""

LINE_SHADER_MULTI_COLOURED = """
// LineShader.wgsl
struct Uniforms {
    MVP: mat4x4<f32>,
};

@binding(0) @group(0) var<uniform> uniforms: Uniforms;

struct VertexIn {
    @location(0) pos: vec3<f32>,
    @location(1) color: vec3<f32>,
};

struct VertexOut {
    @builtin(position) position: vec4<f32>,
    @location(0) color: vec3<f32>,
};

@vertex
fn vertex_main(input: VertexIn) -> VertexOut {
    var output: VertexOut;
    output.position = uniforms.MVP * vec4<f32>(input.pos, 1.0);
    output.color = input.color;
    return output;
}

@fragment
fn fragment_main(input: VertexOut) -> @location(0) vec4<f32> {
    return vec4<f32>(input.color, 1.0);
}
"""

POINT_LIST_SHADER_MULTI_COLOURED = """
@group(0) @binding(0) var<uniform> uniforms : Uniforms;

struct Uniforms
{
    MVP : mat4x4<f32>,
};

struct VertexIn {
    @location(0) position: vec3<f32>,
    @location(1) colour: vec3<f32>,
};

struct VertexOut {
    @builtin(position) position: vec4<f32>,
    @location(0) fragColour: vec3<f32>,
};

@vertex
fn vertex_main(input: VertexIn) -> VertexOut {
    var output: VertexOut;
    output.position = uniforms.MVP * vec4<f32>(input.position, 1.0);
    output.fragColour = input.colour;
    return output;
}

@fragment
fn fragment_main(fragData: VertexOut) -> @location(0) vec4<f32>
{
    return vec4<f32>(fragData.fragColour, 1.0);
}
"""

POINT_LIST_SHADER_SINGLE_COLOUR = """
@group(0) @binding(0) var<uniform> uniforms : Uniforms;

struct Uniforms
{
    MVP : mat4x4<f32>,
    Colour: vec3<f32>,
    padding : f32


};

struct VertexIn {
    @location(0) position: vec3<f32>,
};

struct VertexOut {
    @builtin(position) position: vec4<f32>,
};

@vertex
fn vertex_main(input: VertexIn) -> VertexOut {
    var output: VertexOut;
    output.position = uniforms.MVP * vec4<f32>(input.position, 1.0);
    return output;
}

@fragment
fn fragment_main(fragData: VertexOut) -> @location(0) vec4<f32>
{
    return vec4<f32>(uniforms.Colour, 1.0);
}
"""


TRIANGLE_SHADER_SINGLE_COLOUR = """
// TriangleShader.wgsl
struct Uniforms {
    MVP: mat4x4<f32>,
};

@binding(0) @group(0) var<uniform> uniforms: Uniforms;

@vertex
fn vertex_main(@location(0) pos: vec3<f32>) -> @builtin(position) vec4<f32> {
    return uniforms.MVP * vec4<f32>(pos, 1.0);
}

@fragment
fn fragment_main() -> @location(0) vec4<f32> {
    return vec4<f32>(1.0, 1.0, 1.0, 1.0); // White color
}
"""

TRIANGLE_SHADER_MULTI_COLOURED = """
// TriangleShader.wgsl
struct Uniforms {
    MVP: mat4x4<f32>,
};

@binding(0) @group(0) var<uniform> uniforms: Uniforms;

struct VertexIn {
    @location(0) pos: vec3<f32>,
    @location(1) color: vec3<f32>,
};

struct VertexOut {
    @builtin(position) position: vec4<f32>,
    @location(0) color: vec3<f32>,
};

@vertex
fn vertex_main(input: VertexIn) -> VertexOut {
    var output: VertexOut;
    output.position = uniforms.MVP * vec4<f32>(input.pos, 1.0);
    output.color = input.color;
    return output;
}

@fragment
fn fragment_main(input: VertexOut) -> @location(0) vec4<f32> {
    return vec4<f32>(input.color, 1.0);
}
"""
