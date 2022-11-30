#version 330

uniform vec2 u_mouse;

out vec4 p3d_FragColor;

void main() {
    vec3 color = vec3(1.0);
    p3d_FragColor = vec4(color, 1.0)
}