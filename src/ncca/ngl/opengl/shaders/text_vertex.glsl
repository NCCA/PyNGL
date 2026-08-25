#version 410 core
layout(location=0) in vec2 position;
layout(location=1) in vec4 uvRect;
layout(location=2) in vec2 size;

out VS_OUT
{
    vec2 pos;
    vec4 uvRect;
    vec2 size;
} vs_out;

void main()
{
    vs_out.pos = position;
    vs_out.uvRect = uvRect;
    vs_out.size = size;
}
