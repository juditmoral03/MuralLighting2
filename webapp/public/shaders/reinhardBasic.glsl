uniform float maxInputLuminance; // provided by the application // NOTE: not used  
uniform float avgInputLuminance; // provided by the application    
uniform float exposure; 

vec3 ReinhardBasicToneMapping( vec3 color ) {
    return color / (1.0 + color); 
}

vec3 CustomToneMapping( vec3 color ) {
    // NOTE: same as compute_L in the extended version but on the whole color, using exposure instead of key, and avg luminance instead of avg Log luminance
    color *= 1. / avgInputLuminance;
    color *= exposure;
    vec3 toned_color = ReinhardBasicToneMapping(color);

    return pow(toned_color, vec3(1.0 / 2.2));   // gamma correction
    // return toned_color;
}