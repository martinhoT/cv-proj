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

    // Equal to just picking the y normal
    vec3 normal = texture2D(ntex, texcoord).rgb;
    // We only need the y coordinate, since the flashlight is pointing in the y direction
    float normalDiff = 1.0 - max(normal.g, 0.0);

    float depth = texture2D(dtex, texcoord).x;
    // How much is the light affected by the distance to the camera. 0 means full fog.
    float fogDisturbance = 1 - pow(depth, 50);

    vec4 flashlightColor = vec4(filledCircle(u_mouse, 0.4, st, 0.5), 1.0);

    // TODO: Make depth affect the flashlight radius & smoothness instead
    // TODO: Deferred lighting?
    vec4 base = texture2D(tex, texcoord);
    vec4 flashlightLit = max(backgroundColor, fogDisturbance * lightPower * normalDiff * flashlightColor);

    p3d_FragColor = base * flashlightLit;
    // p3d_FragColor = vec4(depth);   // Depth buffer
    // p3d_FragColor = vec4(normal, 1.0);   // Normal buffer
    // p3d_FragColor = vec4(fogDisturbance);
    // p3d_FragColor = vec4(normalDiff);
}
