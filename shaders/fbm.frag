#ifdef GL_ES
precision mediump float;
#endif

uniform vec2 u_resolution;
uniform vec2 u_mouse;
uniform float u_time;

const int fbmNFuncs = 10;

/*
Test code for fractional brownian motion.
*/

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
    // f = mix(0.0, 0.49, .5 + .5*sin(u_time));
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
    
    // return mix(random00, random10, smoothstep(.2, .8, .5 + .5*sin(4.*u_time)));
    // return stStep.x*.5 + stStep.y*.5;
    // return bilinearInterpolation(
    //     .5*(stStep.x + stStep.y),
    //     .5*(stStep.x + interval + stStep.y),
    //     .5*(stStep.x + stStep.y + interval),
    //     .5*(stStep.x + stStep.y + 2.*interval),
    //     noiseInterp);
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

void main() {
    vec2 st = gl_FragCoord.xy / u_resolution.xy;
    // gl_FragColor = vec4(noise(st, 0.1));
    gl_FragColor = vec4(fbm(st, 8.0, .3));
}
