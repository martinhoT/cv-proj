#version 330

uniform sampler2D tex;
uniform sampler2D dtex;
uniform sampler2D ntex;
uniform vec2 u_mouse;
uniform vec2 u_resolution;
uniform float u_time;
uniform float lightRadius;
uniform float lightPower;
uniform float lightFlickerRatio;

in vec2 texcoord;

out vec4 p3d_FragColor;



void main() {
    float depth = texture2D(dtex, texcoord).x;
    float fogDisturbance = 1 - pow(depth, 50);

    p3d_FragColor = vec4(vec3(fogDisturbance), 1.0);
}
