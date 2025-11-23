//REFERENCES:
//https://www-old.cs.utah.edu/docs/techreports/2002/pdf/UUCS-02-001.pdf
//https://www.ryanjuckett.com/rgb-color-space-conversion/
//https://bruop.github.io/exposure/
//https://bruop.github.io/tonemapping
//PRE-CONDITION: RGB Values are linearized!!!

//uniform float maxInputLuminance; // provided by the application    
//uniform float avgInputLuminance; // provided by the application    
//uniform float exposure; 

#include <ColorOps>

uniform float avg_L_w; //logarithmic average Luminance;
uniform float a;// = 0.18; //key parameter describes the key of the image.
uniform float L_white; //maximum luminance of the scene or which luminance will map to white

float compute_L(float L_w) {
    return (a/avg_L_w)*L_w;
}

vec3 ReinhardExtendedToneMapping( vec3 color) {
    
    vec3 Yxy = convert_RGB2Yxy(color);

    float L = compute_L(Yxy.x);

    float numerator = L * (1.f + (L / (L_white * L_white)));
    float denominator = 1.f + L;
    
    float L_d = numerator/denominator;

    Yxy.x = L_d;

    return convert_Yxy2RGB(Yxy);
}

vec3 ReinhardExtendedToneMappingXYZ( vec3 color) {

    vec3 XYZ = convert_RGB2XYZ(color);

    float L = compute_L(XYZ.y);
    
    float lw = L_white;

    float numerator = L * (1.f + (L / ((lw * lw))));
    float denominator = 1.f + L;
    
    float L_d = numerator/denominator;

    float scale = L_d / XYZ.y;

    XYZ = XYZ * scale;

    return convert_XYZ2RGB(XYZ);
}

vec3 CustomToneMapping( vec3 color ) {
    //check why i'm not using eq 1 and 2 from the reinhard paper.
    //luminance does it so, we have two parameters a = [0,1] maps the image to mid tones
    //then luminance is changed using L_white that is the another parameter that we can modify and represents the max value of luminance that will be white.

    //color *= (1. / 0.05); // normalize to avgInputLuminance

    vec3 xyz = convert_RGB2XYZ(color);
    //if(xyz.y > 0.05) return vec3(1,0,0);

    vec3 toned_color = ReinhardExtendedToneMappingXYZ(color);

    //return toned_color;
    return pow(toned_color, vec3(1.0 / 2.2));;

}