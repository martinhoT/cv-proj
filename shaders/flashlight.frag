#version 330

uniform sampler2D tex;
uniform sampler2D dtex;
uniform sampler2D ntex;
uniform vec2 u_mouse;
uniform vec2 u_resolution;
uniform float lightPower;

in vec2 texcoord;

out vec4 p3d_FragColor;



vec3 filledCircle(in vec2 center, in float radius, in vec2 point, in float borderSmoothness) {
    float pct = distance(point, center);
    return vec3(1.0 - smoothstep(radius, radius+borderSmoothness, pct));
}

void main() {
    vec2 st = 2 * (gl_FragCoord.xy/u_resolution) - 1;
    vec4 backgroundColor = vec4(0.0, 0.0, 0.1, 0.0);

    vec3 normals = texture2D(ntex, texcoord).rgb;

    float depth = texture2D(dtex, texcoord).x;
    // How much is the light affected by the distance to the camera. 1 means full fog.
    float fogDisturbance = pow(depth, 50);

    vec4 flashlightColor = vec4(filledCircle(u_mouse, 0.4, st, 0.5), 1.0);

    vec4 base = texture2D(tex, texcoord);
    vec4 flashlight_lit = max(backgroundColor, mix(lightPower * flashlightColor, backgroundColor, fogDisturbance) );

    p3d_FragColor = base * flashlight_lit;
    // p3d_FragColor = vec4(depth);   // Depth buffer
    // p3d_FragColor = vec4(normals, 1.0);   // Normal buffer
    // p3d_FragColor = vec4(fogDisturbance);
}