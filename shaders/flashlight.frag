#version 330

uniform sampler2D tex;
uniform vec2 u_mouse;
uniform vec2 u_resolution;

in vec2 texcoord;

out vec4 p3d_FragColor;



vec3 filledCircle(in vec2 center, in float radius, in vec2 point, in float borderSmoothness) {
    float pct = distance(point, center);
    return vec3(1.0 - smoothstep(radius, radius+borderSmoothness, pct));
}

void main() {
    vec2 st = 2 * (gl_FragCoord.xy/u_resolution) - 1;

    vec4 base = texture2D(tex, texcoord);
    vec4 flashlight_lit = max(vec4(0.0, 0.0, 0.1, 0.0), vec4(filledCircle(u_mouse, 0.8, st, 0.1), 1.0));

    p3d_FragColor = base * flashlight_lit;
}