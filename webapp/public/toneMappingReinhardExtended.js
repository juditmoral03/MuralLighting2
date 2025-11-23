import ToneMappingFunction from './toneMappingFunction.js';   
import readTextFile from './shaderReader.js'; 

var shaderCode = await readTextFile("shaders/reinhardExtended.glsl");

var shaderParameters = {
    "a": { min: 0.0, max: 1.0, value: 0.18, name: "Key" },
    "L_white": { min: 0.0, max: 10, value: 1, decimals: 3, name: "L White" },
};

const toneMappingReinhardExtended = new ToneMappingFunction("Reinhard Extended", shaderCode, shaderParameters);

export default toneMappingReinhardExtended;