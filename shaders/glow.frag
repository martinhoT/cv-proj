#version 330

#define PI 3.14159265359

uniform sampler2D tex;

in vec2 texcoord;

out vec4 p3d_FragColor;

void main() {
    vec2 st = 2 * (gl_FragCoord.xy/u_resolution) - 1;
    
    vec4 base = texture2D(tex, texcoord);
    
    // Get luminance using the YCoCg color space
    float luminance = 0.25 * neighbor.r + 0.5 * neighbor.g + 0.25 * neighbor.b;
 
    p3d_FragColor = step(0.7, luminance);
}
