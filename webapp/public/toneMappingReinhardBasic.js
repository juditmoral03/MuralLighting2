import ToneMappingFunction from './toneMappingFunction.js';   
import readTextFile from './shaderReader.js'; 

var shaderCode = await readTextFile("shaders/reinhardBasic.glsl");

var shaderParameters = {
    "exposure": { min: 0.0, max: 10.0, value: 1, name: "Exposure" },
};

const toneMappingReinhardBasic = new ToneMappingFunction("Reinhard Basic", shaderCode, shaderParameters);

export default toneMappingReinhardBasic;