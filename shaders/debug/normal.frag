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
    vec3 normal = texture2D(ntex, texcoord).rgb;
    
    p3d_FragColor = vec4(normal, 1.0);
}
