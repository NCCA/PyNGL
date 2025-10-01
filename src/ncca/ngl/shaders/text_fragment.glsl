#version 410 core
in vec2 v_uv;
uniform sampler2D textureID;
uniform vec4 textColour;
out vec4 fragColor;
void main()
{
    float a = texture(textureID, v_uv).a;
    fragColor = vec4(textColour.rgb, textColour.a * a);
}
