#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;
out vec3 FragPos;
out vec3 Normal;
uniform mat4 model;
uniform mat4 MVP;
uniform mat3 normal_matrix;
void main()
{
    FragPos = vec3(model * vec4(aPos, 1.0));
    Normal = normal_matrix * aNormal;
    gl_Position = MVP * vec4(aPos, 1.0);
}