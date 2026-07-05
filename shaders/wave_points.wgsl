// Wave animation shader for points
// This shader creates a pulsing wave effect with point sprites

struct Uniforms {
    MVP : mat4x4<f32>,
    colour : vec4<f32>,
    time : f32,
    point_size : f32,
};

@group(0) @binding(0) var<uniform> uniforms : Uniforms;

struct VertexIn {
    @location(0) position : vec3<f32>,
    @location(1) colour : vec3<f32>,
};

struct VertexOut {
    @builtin(position) position : vec4<f32>,
    @location(0) fragColour : vec3<f32>,
    @location(1) uv : vec2<f32>,
    @location(2) wave_factor : f32,
};

@vertex
fn vertex_main(input: VertexIn, @builtin(vertex_index) vertex_index: u32) -> VertexOut {
    var output: VertexOut;
    
    // Calculate wave effect based on position and time
    let distance_from_center = length(input.position.xz);
    let wave = sin(distance_from_center * 2.0 - uniforms.time * 3.0) * 0.5 + 0.5;
    
    // Apply wave displacement to Y position
    let displaced_position = input.position + vec3<f32>(0.0, wave * 2.0, 0.0);
    
    output.position = uniforms.MVP * vec4<f32>(displaced_position, 1.0);
    output.fragColour = input.colour;
    output.wave_factor = wave;
    
    // Generate quad UV coordinates for point sprite
    let quad_offsets = array<vec2<f32>, 4>(
        vec2<f32>(-1.0, -1.0), // bottom-left
        vec2<f32>(1.0, -1.0),  // bottom-right
        vec2<f32>(-1.0, 1.0),   // top-left
        vec2<f32>(1.0, 1.0)    // top-right
    );
    
    // Convert to 0-1 UV range
    output.uv = quad_offsets[vertex_index % 4u] * 0.5 + 0.5;
    
    return output;
}

@fragment
fn fragment_main(input: VertexOut) -> @location(0) vec4<f32> {
    // Create circular point sprite
    let center = vec2<f32>(0.5, 0.5);
    let dist = distance(input.uv, center);
    let radius = 0.5;
    
    if (dist > radius) {
        discard;
    }
    
    // Create soft edge
    let edge_softness = 0.1;
    let alpha = 1.0 - smoothstep(radius - edge_softness, radius, dist);
    
    // Modulate colour with wave factor
    let animated_colour = input.fragColour * (0.5 + input.wave_factor * 0.5);
    
    return vec4<f32>(animated_colour, alpha);
}