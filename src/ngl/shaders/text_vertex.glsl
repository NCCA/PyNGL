#version 410 core
layout(location=0) in vec2 a_position;
layout(location=1) in vec4 a_uvRect;
layout(location=2) in vec2 a_size;

out VS_OUT
{
    vec2 pos;
    vec4 uvRect;
    vec2 size;
} vs_out;

void main()
{
    vs_out.pos = a_position;
    vs_out.uvRect = a_uvRect;
    vs_out.size = a_size;
}

// #version 410
// layout (location = 0) in vec4 inVert; // <vec2 pos, vec2 tex>
// out vec2 TexCoords;
// uniform vec3 textColour;
// uniform mat4 projection;

// void main()
// {
//   gl_Position = projection * vec4(inVert.xy, 0.0, 1.0);
//   TexCoords = inVert.zw;
// }
