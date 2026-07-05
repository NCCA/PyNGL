#version 410 core
layout(points) in;
layout(triangle_strip, max_vertices=4) out;

uniform vec2 screenSize;
uniform float fontSize;

in VS_OUT
{
    vec2 pos;
    vec4 uvRect;
    vec2 size;
}
gs_in[];

out vec2 v_uv;

vec2 toNDC(vec2 screenPos)
{
    return vec2(
        (screenPos.x / screenSize.x) * 2.0 - 1.0,
        1.0 - (screenPos.y /screenSize.y) * 2.0
    );
}

void main()
{
    vec2 base = gs_in[0].pos;
    vec2 gsize = gs_in[0].size * fontSize;
    vec4 uv = gs_in[0].uvRect;
    // generate a quad
    // Top Left
    gl_Position = vec4(toNDC(base), 0.0, 1.0);
    v_uv = uv.xy;
    EmitVertex();

    // Bottom Left
    gl_Position = vec4(toNDC(base + vec2(0.0, gsize.y)), 0.0, 1.0);
    v_uv = vec2(uv.x, uv.w);
    EmitVertex();

    // Top Right
    gl_Position = vec4(toNDC(base + vec2(gsize.x, 0.0)), 0.0, 1.0);
    v_uv = vec2(uv.z, uv.y);
    EmitVertex();

    // Bottom Right
    gl_Position = vec4(toNDC(base + gsize), 0.0, 1.0);
    v_uv = uv.zw;
    EmitVertex();

    EndPrimitive();
}
