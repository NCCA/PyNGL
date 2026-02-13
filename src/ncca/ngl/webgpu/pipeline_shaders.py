from dataclasses import dataclass


@dataclass
class ShaderConfig:
    """Configuration for generating WGSL shaders"""

    name: str
    geometry_type: str  # 'point', 'line', 'triangle', 'instanced', 'point_list'
    colour_mode: str  # 'single', 'multi'
    has_lighting: bool = False
    has_uv: bool = False
    has_size: bool = False
    has_view_matrix: bool = False
    has_instance_transform: bool = False


# Shader component templates
UNIFORMS_BASE = """
@group(0) @binding(0) var<uniform> uniforms : Uniforms;
"""

UNIFORMS_MVP = """
struct Uniforms
{{
    MVP : mat4x4<f32>,
{additional_fields}
}};
"""

UNIFORMS_MVP_VIEW = """
struct Uniforms
{{
    MVP : mat4x4<f32>,
    ViewMatrix : mat4x4<f32>,
{additional_fields}
}};
"""

VERTEX_IN_POSITION = """
struct VertexIn {{
    @location(0) position: vec3<f32>,
{colour_input}
}};
"""

VERTEX_IN_INSTANCED = """
struct InstanceData {{
    @location(0) position: vec3<f32>,
{colour_input}
    @location(2) instance_id: f32,
}};

struct GeometryVertex {{
    @location(3) geometry_position: vec3<f32>,
    @location(4) geometry_normal: vec3<f32>,
    @location(5) geometry_uv: vec2<f32>,
}};
"""

VERTEX_OUT_BASE = """
struct VertexOut {{
    @builtin(position) position: vec4<f32>,
{colour_output}
{uv_output}
{normal_output}
{world_pos_output}
}};
"""

QUAD_OFFSETS = """
    let quad_offsets = array<vec2<f32>, 4>(
        vec2<f32>(-1.0, -1.0), // bottom-left
        vec2<f32>(1.0, -1.0),  // bottom-right
        vec2<f32>(-1.0, 1.0),   // top-left
        vec2<f32>(1.0, 1.0)    // top-right
    );
"""

CAMERA_EXTRACTION = """
    // Extract camera right and up vectors from view matrix
    let cameraRight = normalize(vec3<f32>(uniforms.ViewMatrix[0][0], uniforms.ViewMatrix[1][0], uniforms.ViewMatrix[2][0]));
    let cameraUp = normalize(vec3<f32>(uniforms.ViewMatrix[0][1], uniforms.ViewMatrix[1][1], uniforms.ViewMatrix[2][1]));
"""

LIGHTING_CALCULATION = """
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
"""

CIRCLE_DISCARD = """
    let center = vec2<f32>(0.5, 0.5); // Center of the quad in UV space
    let dist = distance(fragData.uv, center); // Distance from center
    let radius = 0.5; // Circle radius (quad is 1.0 in UV space)

    if (dist > radius)
    {{
        discard; // Remove pixels outside the circle
    }}
"""


def _build_uniforms(config: ShaderConfig) -> str:
    """Build uniform structure based on configuration"""
    additional_fields = []

    if config.geometry_type == "point":
        if config.colour_mode == "single":
            additional_fields.append("    ColourSize: vec4<f32>,")
        else:
            additional_fields.extend(
                [
                    "    size: f32,",
                    "    padding: u32,",
                    "    padding2: u32,",
                    "    padding3: u32,",
                ]
            )
    elif config.geometry_type in ["line", "triangle", "point_list"]:
        if config.colour_mode == "single":
            additional_fields.extend(["    Colour: vec3<f32>,", "    padding: f32,"])
    elif config.geometry_type == "instanced":
        if config.colour_mode == "single":
            additional_fields.extend(
                [
                    "    colour: vec3<f32>,",
                    "    padding: f32,",
                    "    instance_transform: mat4x4<f32>,",
                ]
            )
        else:
            additional_fields.append("    instance_transform: mat4x4<f32>,")

    base_template = UNIFORMS_MVP_VIEW if config.has_view_matrix else UNIFORMS_MVP
    return base_template.format(
        additional_fields="\n".join(additional_fields) if additional_fields else ""
    )


def _build_vertex_input(config: ShaderConfig) -> str:
    """Build vertex input structure based on configuration"""
    if config.geometry_type == "instanced":
        if config.colour_mode == "single":
            colour_input = (
                "    @location(1) colour: vec3<f32>,  // Provided but ignored"
            )
        else:
            colour_input = "    @location(1) colour: vec3<f32>,"

        return VERTEX_IN_INSTANCED.format(colour_input=colour_input)
    else:
        # For lines, use 'pos' instead of 'position' to match original shaders
        if config.geometry_type == "line":
            position_input = "    @location(0) pos: vec3<f32>,"
            colour_input = (
                "    @location(1) color: vec3<f32>,"
                if config.colour_mode == "multi"
                else ""
            )
        elif config.geometry_type == "triangle":
            position_input = "    @location(0) pos: vec3<f32>,"
            colour_input = (
                "    @location(1) color: vec3<f32>,"
                if config.colour_mode == "multi"
                else ""
            )
        else:
            position_input = "    @location(0) position: vec3<f32>,"
            colour_input = (
                "    @location(1) colour: vec3<f32>,"
                if config.colour_mode == "multi"
                else ""
            )

        return f"""
struct VertexIn {{
{position_input}
{colour_input}
}};
"""


def _build_vertex_output(config: ShaderConfig) -> str:
    """Build vertex output structure based on configuration"""
    outputs = []

    if config.colour_mode == "multi":
        if config.geometry_type in ["point", "point_list"]:
            outputs.append("    @location(0) fragColour: vec3<f32>,")
        elif config.geometry_type in ["line", "triangle"]:
            outputs.append("    @location(0) color: vec3<f32>,")
        elif config.geometry_type == "instanced":
            outputs.append("    @location(0) fragColour: vec3<f32>,")

    if config.has_uv:
        outputs.append("    @location(1) uv: vec2<f32>,")

    if config.has_lighting:
        if config.geometry_type == "instanced" and config.colour_mode == "single":
            outputs = [
                "    @location(0) fragNormal: vec3<f32>,",
                "    @location(1) fragUV: vec2<f32>,",
                "    @location(2) worldPos: vec3<f32>,",
            ]
        else:
            start_idx = len(outputs)
            outputs.append(f"    @location({start_idx}) fragNormal: vec3<f32>,")
            outputs.append(f"    @location({start_idx + 1}) fragUV: vec2<f32>,")
            outputs.append(f"    @location({start_idx + 2}) worldPos: vec3<f32>,")

    colour_output = ""
    uv_output = ""
    normal_output = ""
    world_pos_output = ""

    for output in outputs:
        if "fragColour" in output or "color" in output:
            colour_output = output
        elif "uv" in output and "fragUV" not in output:
            uv_output = output
        elif "fragNormal" in output:
            normal_output = output
        elif "fragUV" in output:
            uv_output = output
        elif "worldPos" in output:
            world_pos_output = output

    return VERTEX_OUT_BASE.format(
        colour_output=colour_output,
        uv_output=uv_output,
        normal_output=normal_output,
        world_pos_output=world_pos_output,
    )


def _build_vertex_main(config: ShaderConfig) -> str:
    """Build vertex shader main function"""
    if config.geometry_type == "point":
        return _build_point_vertex(config)
    elif config.geometry_type in ["line", "triangle", "point_list"]:
        return _build_simple_vertex(config)
    elif config.geometry_type == "instanced":
        return _build_instanced_vertex(config)
    return ""


def _build_point_vertex(config: ShaderConfig) -> str:
    """Build point sprite vertex shader"""
    size_source = (
        "uniforms.size" if config.colour_mode == "multi" else "uniforms.ColourSize.w"
    )

    return f"""
@vertex
fn vertex_main(input: VertexIn, @builtin(vertex_index) vertex_index: u32) -> VertexOut {{
    var output: VertexOut;
{QUAD_OFFSETS}

{CAMERA_EXTRACTION if config.has_view_matrix else ""}

    // Calculate billboard offset in world space
    let offset2D = quad_offsets[vertex_index] * {size_source};
    let offset3D = cameraRight * offset2D.x + cameraUp * offset2D.y;
    let worldPos = input.position + offset3D;

    output.position = uniforms.MVP * vec4<f32>(worldPos, 1.0);
{("    output.fragColour = input.colour;" if config.colour_mode == "multi" else "")}
    // convert offset from -1 -> 1 to 0 -> 1 for uv
    output.uv = quad_offsets[vertex_index] * 0.5 + 0.5;

    return output;
}}
"""


def _build_simple_vertex(config: ShaderConfig) -> str:
    """Build simple vertex shader for lines, triangles, point lists"""
    # Use the correct attribute names based on geometry type
    if config.geometry_type in ["line", "triangle"]:
        position_source = "input.pos"
        colour_source = "input.color"
    else:
        position_source = "input.position"
        colour_source = (
            "input.colour" if config.geometry_type == "point_list" else "input.color"
        )

    colour_output = ""
    if config.colour_mode == "multi" and config.geometry_type == "point_list":
        colour_output = f"    output.fragColour = {colour_source};"
    elif config.colour_mode == "multi" and config.geometry_type in ["line", "triangle"]:
        colour_output = f"    output.color = {colour_source};"

    return f"""
@vertex
fn vertex_main(input: VertexIn) -> VertexOut {{
    var output: VertexOut;
    output.position = uniforms.MVP * vec4<f32>({position_source}, 1.0);
{colour_output}

    return output;
}}
"""


def _build_instanced_vertex(config: ShaderConfig) -> str:
    """Build instanced vertex shader"""
    return f"""
@vertex
fn vertex_main(instance_data: InstanceData, geom_vertex: GeometryVertex, @builtin(vertex_index) vertex_index: u32) -> VertexOut {{
    var output: VertexOut;

    // Transform geometry vertex by instance transform and position
    let transformed_vertex = uniforms.instance_transform * vec4<f32>(geom_vertex.geometry_position, 1.0);
    let world_position = transformed_vertex.xyz + instance_data.position;

    output.position = uniforms.MVP * vec4<f32>(world_position, 1.0);
{("    output.fragColour = instance_data.colour;" if config.colour_mode == "multi" else "")}

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
}}
"""


def _build_fragment_main(config: ShaderConfig) -> str:
    """Build fragment shader main function"""
    if config.geometry_type == "point":
        return _build_point_fragment(config)
    elif config.geometry_type == "instanced":
        return _build_instanced_fragment(config)
    else:
        return _build_simple_fragment(config)


def _build_point_fragment(config: ShaderConfig) -> str:
    """Build point sprite fragment shader"""
    colour_source = (
        "fragData.fragColour"
        if config.colour_mode == "multi"
        else "uniforms.ColourSize.xyz"
    )

    return f"""
@fragment
fn fragment_main(fragData: VertexOut) -> @location(0) vec4<f32>
{{
{CIRCLE_DISCARD if config.has_uv else ""}

    return vec4<f32>({colour_source}, 1.0);
}}
"""


def _build_simple_fragment(config: ShaderConfig) -> str:
    """Build simple fragment shader for lines, triangles, point lists"""
    if config.colour_mode == "single":
        return """
@fragment
fn fragment_main() -> @location(0) vec4<f32> {
    return vec4<f32>(uniforms.Colour, 1.0);
}
"""
    else:
        # Use the correct output attribute name based on geometry type
        if config.geometry_type == "point_list":
            colour_source = "fragData.fragColour"
        else:
            colour_source = "fragData.color"
        return f"""
@fragment
fn fragment_main(fragData: VertexOut) -> @location(0) vec4<f32>
{{
    return vec4<f32>({colour_source}, 1.0);
}}
"""


def _build_instanced_fragment(config: ShaderConfig) -> str:
    """Build instanced fragment shader with lighting"""
    colour_source = (
        "uniforms.colour" if config.colour_mode == "single" else "fragData.fragColour"
    )

    return f"""
@fragment
fn fragment_main(fragData: VertexOut) -> @location(0) vec4<f32>
{{
    // Enhanced diffuse lighting calculation

{LIGHTING_CALCULATION}

    // Apply lighting to the fragment color
    let lit_color = {colour_source} * final_lighting;

    return vec4<f32>(lit_color, 1.0);
}}
"""


def generate_shader(config: ShaderConfig) -> str:
    """Generate complete WGSL shader from configuration"""
    uniforms = _build_uniforms(config)
    vertex_in = _build_vertex_input(config)
    vertex_out = _build_vertex_output(config)
    vertex_main = _build_vertex_main(config)
    fragment_main = _build_fragment_main(config)

    return f"""
{UNIFORMS_BASE}
{uniforms}

{vertex_in}

{vertex_out}

{vertex_main}

{fragment_main}
"""


# Generate all existing shaders using the new system
POINT_SHADER_MULTI_COLOURED = generate_shader(
    ShaderConfig(
        name="POINT_SHADER_MULTI_COLOURED",
        geometry_type="point",
        colour_mode="multi",
        has_uv=True,
        has_view_matrix=True,
    )
)

POINT_SHADER_SINGLE_COLOUR = generate_shader(
    ShaderConfig(
        name="POINT_SHADER_SINGLE_COLOUR",
        geometry_type="point",
        colour_mode="single",
        has_uv=True,
        has_view_matrix=True,
    )
)

INSTANCED_SHADER_MULTI_COLOURED = generate_shader(
    ShaderConfig(
        name="INSTANCED_SHADER_MULTI_COLOURED",
        geometry_type="instanced",
        colour_mode="multi",
        has_lighting=True,
        has_view_matrix=True,
        has_instance_transform=True,
    )
)

INSTANCED_SHADER_SINGLE_COLOUR = generate_shader(
    ShaderConfig(
        name="INSTANCED_SHADER_SINGLE_COLOUR",
        geometry_type="instanced",
        colour_mode="single",
        has_lighting=True,
        has_view_matrix=True,
        has_instance_transform=True,
    )
)

LINE_SHADER_SINGLE_COLOUR = generate_shader(
    ShaderConfig(
        name="LINE_SHADER_SINGLE_COLOUR", geometry_type="line", colour_mode="single"
    )
)

LINE_SHADER_MULTI_COLOURED = generate_shader(
    ShaderConfig(
        name="LINE_SHADER_MULTI_COLOURED", geometry_type="line", colour_mode="multi"
    )
)

POINT_LIST_SHADER_MULTI_COLOURED = generate_shader(
    ShaderConfig(
        name="POINT_LIST_SHADER_MULTI_COLOURED",
        geometry_type="point_list",
        colour_mode="multi",
    )
)

POINT_LIST_SHADER_SINGLE_COLOUR = generate_shader(
    ShaderConfig(
        name="POINT_LIST_SHADER_SINGLE_COLOUR",
        geometry_type="point_list",
        colour_mode="single",
    )
)

TRIANGLE_SHADER_SINGLE_COLOUR = generate_shader(
    ShaderConfig(
        name="TRIANGLE_SHADER_SINGLE_COLOUR",
        geometry_type="triangle",
        colour_mode="single",
    )
)

TRIANGLE_SHADER_MULTI_COLOURED = generate_shader(
    ShaderConfig(
        name="TRIANGLE_SHADER_MULTI_COLOURED",
        geometry_type="triangle",
        colour_mode="multi",
    )
)
