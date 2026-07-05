// Gradient triangle shader with vertex colours
// This shader creates a smooth gradient effect across triangles

struct Uniforms {
    MVP : mat4x4<f32>,
    colour : vec4<f32>,
};

@group(0) @binding(0) var<uniform> uniforms : Uniforms;

struct VertexIn {
    @location(0) position : vec3<f32>,
    @location(1) colour : vec3<f32>,
};

struct VertexOut {
    @builtin(position) position : vec4<f32>,
    @location(0) fragColour : vec3<f32>,
    @location(1) barycentric : vec3<f32>,
};

@vertex
fn vertex_main(input: VertexIn, @builtin(vertex_index) vertex_index: u32) -> VertexOut {
    var output: VertexOut;
    
    // Transform position
    output.position = uniforms.MVP * vec4<f32>(input.position, 1.0);
    
    // Pass vertex colour
    output.fragColour = input.colour;
    
    // Calculate barycentric coordinates based on vertex index
    // This creates a nice gradient effect from each vertex
    if (vertex_index == 0u) {
        output.barycentric = vec3<f32>(1.0, 0.0, 0.0);
    } else if (vertex_index == 1u) {
        output.barycentric = vec3<f32>(0.0, 1.0, 0.0);
    } else {
        output.barycentric = vec3<f32>(0.0, 0.0, 1.0);
    }
    
    return output;
}

@fragment
fn fragment_main(input: VertexOut) -> @location(0) vec4<f32> {
    // Mix the vertex colour with barycentric coordinates for a gradient effect
    let gradient_factor = length(input.barycentric);
    let final_colour = mix(input.fragColour, vec3<f32>(1.0, 1.0, 0.8), gradient_factor * 0.3);
    
    return vec4<f32>(final_colour, 1.0);
}