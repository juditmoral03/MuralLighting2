#include <ColorOps>

uniform sampler2D uLeftTexture;
uniform sampler2D uRightTexture;
uniform sampler2D uColorMap;    // colormap (treated as 2D texture)
uniform float uMaxDelta;
uniform float uImgOverlay;   // left image overlay (weight)
uniform float uMaxLum;       // max luminance for the overlayed luminance       
varying vec2 vUv;

void main() {
    
    vec4 lTexColor = texture2D(uLeftTexture, vUv);
    vec4 rTexColor = texture2D(uRightTexture, vUv);

    // Obtain luminance for both images
    vec3 lXYZ = convert_RGB2XYZ(lTexColor.xyz); 
    float lLum = lXYZ.y;
    vec3 rXYZ = convert_RGB2XYZ(rTexColor.xyz); 
    float rLum = rXYZ.y;

    // Compute difference (campled to 0..1)
    // float delta = clamp(abs(lLum-rLum) / uMaxDelta, 0., 1.);     // abs difference
    float delta = (rLum - lLum) / uMaxDelta;    // std difference
    delta = clamp(delta * 0.5 + 0.5, 0., 1.);   // map from -1..1 to 0..1

    // Map difference to the colormap (using a fixed vertical coordinate of 0.5)
    vec3 color = texture(uColorMap, vec2(delta, 0.5)).rgb;

    // Overlay with left image (luminance one)
    color = uImgOverlay * clamp(lLum / uMaxLum, 0., 1.) + (1.f - uImgOverlay) * color;

    gl_FragColor = vec4(color, 1.0);

    //if (delta>0.9)
    //    gl_FragColor = vec4(1,0,0,1);
}