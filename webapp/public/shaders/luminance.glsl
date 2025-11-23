#include <ColorOps>

uniform sampler2D uColorMap;    // Magma colormap (treated as 2D texture)
uniform float Max_L;           // Maximum luminance of the scene or which luminance maps to white



vec3 CustomToneMapping( vec3 color ) {
    // Obtain luminance from input color
    vec3 XYZ = convert_RGB2XYZ(color);
    float luminance = XYZ.y;

    // Normalize luminance
    float norm_lum = clamp(luminance / Max_L, 0.0, 1.0);

    //float x = gl_FragCoord.x/800.0;
    //float y = gl_FragCoord.y/800.0;

    // Map normalized luminance to the colormap (using a fixed vertical coordinate of 0.5)
    vec3 mappedColor = texture(uColorMap, vec2(norm_lum, 0.5)).rgb;
    //mappedColor = texture(uColorMap, vec2(x, y)).rgb;

    /*
    mappedColor *= (1. / 0.00007817795498173835);
    mappedColor *= 1.; 
    float gamma = 2.2;
    mappedColor = pow(mappedColor, vec3(1.0 / gamma)); 
    */

    //vec3 mappedColor = mix(vec3(1.0, 0.0, 0.0), vec3(0.0, 0.0, 1.0), norm_lum);

    return mappedColor;
}
