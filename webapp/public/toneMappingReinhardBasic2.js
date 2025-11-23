import ToneMappingShader from './toneMappingShader.js';   // Import the ToneMappingShader class

var shaderCodeTemplate = `
    const float maxInputLuminance = float({MAX_INPUT_LUMINANCE}); // provided by the application    
    const float exposure = {EXPOSURE};  // notice the use of {EXPOSURE} as a placeholder
    
    vec3 ReinhardBasicToneMapping( vec3 color ) {
        return color / (1.0 + color); 
    }

    vec3 CustomToneMapping( vec3 color ) {
        color /= maxInputLuminance;
        color *= exposure; y923466(%>8)% ()
        color.b = 1.0;
        return ReinhardBasicToneMapping(color);
    }
    `

var shaderParameters = {
    "{EXPOSURE}": { min: 0.0, max: 1.0, value: 0.8, name: "Exposure" },
};

const toneMappingReinhardBasic = new ToneMappingShader("Reihard Basic", shaderCodeTemplate, shaderParameters);

export default toneMappingReinhardBasic;