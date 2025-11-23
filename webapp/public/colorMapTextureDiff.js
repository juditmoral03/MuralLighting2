import * as THREE from 'three';


// Generate n interpolated colors from 3 input colors
function generateInterpolatedColors(color1, color2, color3, n) {
    const colors = [];
    const step = 1 / (n - 1);  // Determine how many steps to take

    const color1Obj = new THREE.Color(color1);
    const color2Obj = new THREE.Color(color2);
    const color3Obj = new THREE.Color(color3);

    for (let i = 0; i < n; i++) {
        let t = i * step;
        let color;

        if (i < n / 2) {
            // Interpolate between color1 and color2
            color = color1Obj.clone().lerp(color2Obj, t * 2); // Double the factor to speed up transition
        } else {
            // Interpolate between color2 and color3
            color = color2Obj.clone().lerp(color3Obj, (t - 0.5) * 2); // Adjust factor to smoothly transition
        }

        // colors.push(color.getHexString()); // Store color as hexadecimal string
        colors.push(color); // Store color
    }

    return colors;
}


const colorMapSize = 255;

// Base colors (BWR colormap)
const color1 = "#0000ff";  // Blue
const color2 = "#ffffff";  // White
const color3 = "#ff0000";  // Red

// // Base colors (BYR colormap)
// const color1 = "#0000ff";  // Blue
// const color2 = "#ffffc5";  // Light Yellow
// const color3 = "#ff0000";  // Red

// Generate color map by interpolation
const colors = generateInterpolatedColors(color1, color2, color3, colorMapSize);

// Convert colors into RGBA data
const width = colors.length;
const height = 1;
const data = new Uint8Array(4 * width * height);
// colors.forEach((hex, i) => {
//     const color = new THREE.Color(hex);
colors.forEach((color, i) => {
    const stride = i * 4;
    data[stride] = Math.round(color.r * 255);     // Red
    data[stride + 1] = Math.round(color.g * 255); // Green
    data[stride + 2] = Math.round(color.b * 255); // Blue
    data[stride + 3] = 255;                       // Alpha
});

// Create DataTexture
const colorMapTextureDiff = new THREE.DataTexture(data, width, height, THREE.RGBAFormat);
colorMapTextureDiff.needsUpdate = true;

export default colorMapTextureDiff;