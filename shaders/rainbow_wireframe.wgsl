// Rainbow wireframe shader with pulsing effect
// This shader creates animated rainbow-coloured lines with a glow effect

struct Uniforms {
    MVP : mat4x4<f32>,
    colour : vec4<f32>,
    time : f32,
    line_width : f32,
};

@group(0) @binding(0) var<uniform> uniforms : Uniforms;

struct VertexIn {
    @location(0) position : vec3<f32>,
    @location(1) colour : vec3<f32>,
};

struct VertexOut {
    @builtin(position) position : vec4<f32>,
    @location(0) fragColour : vec3<f32>,
    @location(1) barycentric : f32,
};

@vertex
fn vertex_main(input: VertexIn, @builtin(vertex_index) vertex_index: u32) -> VertexOut {
    var output: VertexOut;
    
    // Transform position
    output.position = uniforms.MVP * vec4<f32>(input.position, 1.0);
    
    // Generate rainbow color based on position and time
    let hue = (input.position.x + input.position.y + uniforms.time * 0.5) * 0.1;
    let r = sin(hue) * 0.5 + 0.5;
    let g = sin(hue + 2.094) * 0.5 + 0.5;  // + 120 degrees
    let b = sin(hue + 4.189) * 0.5 + 0.5;  // + 240 degrees
    
    output.fragColour = vec3<f32>(r, g, b);
    
    // Barycentric coordinate for line fragment generation
    output.barycentric = f32(vertex_index % 2u);
    
    return output;
}

@fragment
fn fragment_main(input: VertexOut) -> @location(0) vec4<f32> {
    // Create pulsing glow effect
    let pulse = sin(uniforms.time * 2.0) * 0.3 + 0.7;
    
    // Apply pulse to rainbow color
    let glowing_colour = input.fragColour * pulse;
    
    // Add white core to make lines more visible
    let core_intensity = 1.2;
    let final_colour = min(glowing_colour + vec3<f32>(0.2, 0.2, 0.2) * core_intensity, vec3<f32>(1.0));
    
    return vec4<f32>(final_colour, 1.0);
}