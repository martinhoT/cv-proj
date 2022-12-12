#ifdef GL_ES
precision mediump float;
#endif

uniform vec2 u_resolution;
uniform vec2 u_mouse;
uniform float u_time;



// From the book of shaders: https://thebookofshaders.com/10/
float random(vec2 st) {
    return fract(sin(dot(st.xy,
                         vec2(12.9898,78.233)))*
        43758.5453123);
}

// Vector st should be in range [0, 1]
// Formula from: https://en.wikipedia.org/wiki/Bilinear_interpolation
float bilinearInterpolation(float v00, float v10, float v01, float v11, vec2 st) {
    float vx0 = mix(v00, v10, st.x);
    float vx1 = mix(v01, v11, st.x);

    return mix(vx0, vx1, st.y);
}

float noise(vec2 st, float interval) {

    vec2 stStep = interval * floor(st / interval);
    vec2 noiseInterp = fract(st / interval);
    
    float random00 = random(stStep);
    float random10 = random(vec2(stStep.x + interval, stStep.y));
    float random01 = random(vec2(stStep.x, stStep.y + interval));
    float random11 = random(stStep + interval);
    
    return bilinearInterpolation(random00, random10, random01, random11, noiseInterp);
}

void main() {
    vec2 st = gl_FragCoord.xy/u_resolution.xy;
    gl_FragColor = vec4(noise(st, .1));
}
