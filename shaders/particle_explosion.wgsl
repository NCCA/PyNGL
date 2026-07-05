// Particle explosion shader with fade and physics simulation
// This shader creates an animated particle explosion effect with gravity and fade

struct Uniforms {
    MVP : mat4x4<f32>,
    colour : vec4<f32>,
    time : f32,
    particle_size : f32,
    gravity : f32,
};

@group(0) @binding(0) var<uniform> uniforms : Uniforms;

struct VertexIn {
    @location(0) position : vec3<f32>,
    @location(1) velocity : vec3<f32>,
    @location(2) life : f32,
    @location(3) initial_position : vec3<f32>,
};

struct VertexOut {
    @builtin(position) position : vec4<f32>,
    @location(0) fragColour : vec3<f32>,
    @location(1) life : f32,
    @location(2) uv : vec2<f32>,
};

@vertex
fn vertex_main(input: VertexIn, @builtin(vertex_index) vertex_index: u32) -> VertexOut {
    var output: VertexOut;
    
    // Simulate particle physics
    let time_factor = min(uniforms.time, input.life);
    let gravity_force = vec3<f32>(0.0, -uniforms.gravity, 0.0);
    
    // Current position = initial + velocity * time + 0.5 * gravity * time^2
    let current_position = input.initial_position + 
                       input.velocity * time_factor + 
                       0.5 * gravity_force * time_factor * time_factor;
    
    // Transform to screen space
    output.position = uniforms.MVP * vec4<f32>(current_position, 1.0);
    
    // Calculate particle life (normalized 0-1, where 1 is full life)
    output.life = 1.0 - (time_factor / max(input.life, 0.01));
    
    // Color based on life and initial velocity (fast particles = hot/warm colors)
    let velocity_magnitude = length(input.velocity);
    let heat = min(velocity_magnitude * 0.3, 1.0);
    
    if (heat > 0.7) {
        // Fast particles: white -> yellow -> orange
        output.fragColour = mix(
            vec3<f32>(1.0, 1.0, 0.0),  // Yellow
            vec3<f32>(1.0, 0.5, 0.0),  // Orange
            (heat - 0.7) * 3.33
        );
    } else if (heat > 0.3) {
        // Medium particles: yellow -> red
        output.fragColour = mix(
            vec3<f32>(1.0, 0.0, 0.0),  // Red
            vec3<f32>(1.0, 1.0, 0.0),  // Yellow
            (heat - 0.3) * 2.5
        );
    } else {
        // Slow particles: red -> dark red
        output.fragColour = mix(
            vec3<f32>(0.3, 0.0, 0.0),  // Dark red
            vec3<f32>(1.0, 0.0, 0.0),  // Red
            heat * 3.33
        );
    }
    
    // Generate quad UV coordinates for point sprite
    let quad_offsets = array<vec2<f32>, 4>(
        vec2<f32>(-1.0, -1.0), // bottom-left
        vec2<f32>(1.0, -1.0),  // bottom-right
        vec2<f32>(-1.0, 1.0),   // top-left
        vec2<f32>(1.0, 1.0)    // top-right
    );
    
    // Convert to 0-1 UV range and apply particle size that decreases with life
    let size = uniforms.particle_size * output.life;
    output.uv = quad_offsets[vertex_index % 4u] * 0.5 + 0.5;
    
    // Adjust point size in screen space
    let screen_size = uniforms.particle_size * output.life;
    output.position.xy += (quad_offsets[vertex_index % 4u] * screen_size * 0.5) / output.position.w;
    
    return output;
}

@fragment
fn fragment_main(input: VertexOut) -> @location(0) vec4<f32> {
    // Create circular particle with soft edges
    let center = vec2<f32>(0.5, 0.5);
    let dist = distance(input.uv, center);
    let radius = 0.5;
    
    if (dist > radius) {
        discard;
    }
    
    // Soft edge falloff
    let edge_softness = 0.2;
    let alpha = (1.0 - smoothstep(radius - edge_softness, radius, dist)) * input.life;
    
    // Add some brightness variation based on UV position for texture effect
    let brightness_variation = 1.0 + 0.1 * sin(dist * 20.0);
    let final_colour = input.fragColour * brightness_variation * alpha;
    
    return vec4<f32>(final_colour, alpha);
}