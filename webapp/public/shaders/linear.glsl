uniform float maxInputLuminance; // provided by the application  // NOTE: not used
uniform float avgInputLuminance; // provided by the application        
uniform float exposure; 

vec3 CustomToneMapping( vec3 color ) 
{
    color *= (1. / avgInputLuminance);
    color *= exposure; 
    float gamma = 2.2;
    color = pow(color, vec3(1.0 / gamma));
    return color;
}