#version 330

#define PI 3.14159265359

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

const float lightBorder = 0.3;
const int fbmNFuncs = 10;
const float fbmLacunarity = 8.0;
const float fbmGain = 0.5;
const float fbmOffset = 0.9;

// From the book of shaders: https://thebookofshaders.com/10/
float random(vec2 st) {
    return fract(sin(dot(st.xy,
                         vec2(12.9898,78.233)))*
        43758.5453123);
}

// Vector st should be in range [0, 1]
// Formula from: https://en.wikipedia.org/wiki/Bilinear_interpolation
float bilinearInterpolation(float v00, float v10, float v01, float v11, vec2 st) {
    float f = .01;
    float f1 = f;
    float f2 = 1.-f;
    
    float vx0 = mix(v00, v10, smoothstep(f1, f2, st.x));
    float vx1 = mix(v01, v11, smoothstep(f1, f2, st.x));

    return mix(vx0, vx1, smoothstep(f1, f2, st.y));
}

// Value noise: https://en.wikipedia.org/wiki/Value_noise
float noise(vec2 st, float interval) {

    vec2 stStep = interval * floor(st / interval);
    vec2 noiseInterp = fract(st / interval);
    
    float random00 = random(stStep);
    float random10 = random(vec2(stStep.x + interval, stStep.y));
    float random01 = random(vec2(stStep.x, stStep.y + interval));
    float random11 = random(stStep + interval);
    
    return bilinearInterpolation(random00, random10, random01, random11, noiseInterp);
}

float fbm(vec2 st, float lacunarity, float gain) {
    float res = 0.;
    float frequency = 1.;
    float amplitude = 1.;

    for (int i = 0; i < fbmNFuncs; i++) {
        res += amplitude * (noise(st, 1. / frequency));
        frequency *= lacunarity;
        amplitude *= gain;
    }

    return res;
}

vec3 filledCircle(in vec2 center, in float radius, in vec2 point, in float borderSmoothness) {
    float pct = distance(point, center);
    return vec3(1.0 - smoothstep(radius, radius+borderSmoothness, pct));
}



void main() {
    vec2 st = 2 * (gl_FragCoord.xy/u_resolution) - 1;
    // Blue makes it harder to distinguish the details, virtue of the human visual system
    vec4 backgroundColor = vec4(0.0, 0.0, 0.1, 0.0);

    // Equal to just picking the y normal
    vec3 normal = texture2D(ntex, texcoord).rgb;
    // We only need the y coordinate, since the flashlight is pointing in the y direction
    float normalDiff = 1.0 - max(normal.g, 0.0);

    float depth = texture2D(dtex, texcoord).x;
    // How much is the light affected by the distance to the camera. 0 means full fog.
    float fogDisturbance = 1 - pow(depth, 50);

    float lightFlicker = mix(1.0, fbm(vec2(u_time, 0), fbmLacunarity, fbmGain) - fbmOffset, lightFlickerRatio);

    vec4 flashlightCircle = vec4(filledCircle(u_mouse, lightRadius, st, lightBorder), 1.0);

    vec4 flashlightColor = fogDisturbance * lightPower * normalDiff * lightFlicker * flashlightCircle;
    vec4 flashlightLit = max(backgroundColor, flashlightColor);

    vec4 base = texture2D(tex, texcoord);
    
    // How should lit should a color be considered, and thus not need the flashlight light?
    // In this case we take the strongest color component (the HSV value V)
    float lightnessFactor = max(max(base.r, base.g), base.b);
    // Determine how much of the base color to keep based on the previous lightness factor
    float useBaseColor = smoothstep(0.4, 1.0, lightnessFactor);
    
    // Use the flashlight if the base color is not too lit, and keep the base lighting otherwise
    vec4 mixed = mix(base * flashlightLit, base, useBaseColor);
    // Let all other lights flicker as well (affects the moon too...)
    // mixed = mix(base * flashlightLit, base * lightFlicker, useBaseColor);

    p3d_FragColor = mixed;
    
    // Test values
    // p3d_FragColor = vec4(depth);   // Depth buffer
    // p3d_FragColor = vec4(normal, 1.0);   // Normal buffer
    // p3d_FragColor = vec4(fogDisturbance);
    // p3d_FragColor = vec4(normalDiff);
    // p3d_FragColor = vec4(.5 + .5*sin(u_time));
    // p3d_FragColor = vec4(luminance);
    // p3d_FragColor = vec4(lightnessFactor);
    // p3d_FragColor = vec4(smoothstep(0.4, 1.0, luminance));
    // p3d_FragColor = vec4(useBaseColor);
    // p3d_FragColor = vec4(base);
}
