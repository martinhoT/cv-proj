#version 330

uniform vec2 u_resolution;
uniform vec2 u_mouse;

out vec4 p3d_FragColor;



vec3 filledCircle(in vec2 center, in float radius, in vec2 point, in float borderSmoothness) {
    float pct = distance(point, center);
    return vec3(1.0 - smoothstep(radius, radius+borderSmoothness, pct));
}

void main() {
    vec2 st = 2 * (gl_FragCoord.xy/u_resolution) - 1;

    vec3 color = filledCircle(u_mouse, 0.1, st, 0.1);
    p3d_FragColor = vec4(color, 1.0);
}