/**
 * Function to analyze and output the max, min, avg RGB values of a texture.
 * @param {THREE.Texture} texture - The loaded texture to analyze.
 * @returns {object} An object containing the max and min values for R, G and B.
 */
function analyzeTexture(texture) {
    // Ensure the texture has an image
    if (!texture.image) {
        console.error('Texture image not found.');
        return;
    }

    const arr = texture.source.data.data;
    var r = findMaxMinReduce(arr, 0);
    var g = findMaxMinReduce(arr, 1);
    var b = findMaxMinReduce(arr, 2);
    var L = computeLuminanceStats(arr, r.average/3 + g.average/3 + b.average/3);

    return {r, g, b, L};
}

/*
* Function to find the maximum and minimum for R, G or B values in an array.
* @param {number[]} arr - The array to analyze.
* @param {number} component - The component to analyze, 0 for R, 1 for G, 2 for B.
* @returns {object} An object containing the max, min, sum values
*/
function findMaxMinReduce(arr, component) {
    if (component < 0 || component > 2) {
        throw new Error("Invalid component. It must be 0, 1, or 2.");
    }

    const result = arr.reduce((acc, num, index) => {
        if (index % 4 === component) {
            acc.sum += num;
            acc.count += 1;
            if (num > acc.max) acc.max = num;
            if (num < acc.min) acc.min = num;
        }
        return acc;
    }, { max: -Infinity, min: Infinity, sum: 0, count: 0, average: null });

    result.average = result.sum / result.count;
    
    return result;
}

/*
* Function to find the maximum and minimum for R, G or B values in an array.
* @param {number[]} arr - The array to analyze.
* @returns {Object} Returns stats of the luminance including the value of 
*                   the logarithmic avg luminance of the image as described in reinhard02 paper.
*/
function computeLuminanceStats(arr, max_L) {
    const d = 0.0000001;

    const result = arr.reduce((acc, num, index) => {
        const component = index % 4; // Determine the component type (0: R, 1: G, 2: B, 3: A)

        if (component === 0) { // Start of a new pixel (Red component)
            const r = arr[index];
            const g = arr[index + 1];
            const b = arr[index + 2];



            // Calculate luminance using the CIE XYZ 1931 sRGB D65
            const luminance = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b;
            
            //if(luminance < max_L*0.02) 
            {
                acc.sum += Math.log(luminance+d);
                acc.count += 1;

                if (luminance > acc.max) acc.max = luminance;
                if (luminance < acc.min) acc.min = luminance;
            }
        }

        return acc;
    }, {
        max: -Infinity, min: Infinity, 
        sum: 0,
        count: 0,
        average: null
    });

    // Calculate the average luminance
    result.average = Math.exp(result.sum / result.count);//the 1/N needs to be inside the exp or it fails
    //console.log('Result avg: ', result.average);

    return result;
}

export default analyzeTexture;
