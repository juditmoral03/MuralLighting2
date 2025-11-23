// Convert RGB to XYZ color space
vec3 convert_RGB2XYZ(vec3 rgb) {
    vec3 linearRGB = rgb;//linearizeRGB(rgb);

    // Transformation matrix from linear sRGB to XYZ (D65 reference white)
    const mat3 RGB2XYZ = mat3(
        0.4124564, 0.3575761, 0.1804375,
        0.2126729, 0.7151522, 0.0721750,
        0.0193339, 0.1191920, 0.9503041
    );

    vec3 xyz = RGB2XYZ * linearRGB;
    return xyz;
}

// Convert XYZ to RGB color space
vec3 convert_XYZ2RGB(vec3 xyz) {
    // Transformation matrix from XYZ to linear sRGB (D65 reference white)
    const mat3 XYZ2RGB = mat3(
        3.2404542, -1.5371385, -0.4985314,
        -0.9692660,  1.8760108,  0.0415560,
        0.0556434, -0.2040259,  1.0572252
    );

    vec3 linearRGB = XYZ2RGB * xyz;
    vec3 rgb = linearRGB;//delinearizeRGB(linearRGB);
    return rgb;
}

vec3 convert_RGB2Yxy(vec3 rgb) {

    vec3 xyz = convert_RGB2XYZ(rgb);
    float X = xyz.x;
    float Y = xyz.y;
    float Z = xyz.z;
    float sum = X + Y + Z;

    // Calculate chromaticity coordinates x and y
    float x = (sum == 0.0) ? 0.0 : X / sum;
    float y = (sum == 0.0) ? 0.0 : Y / sum;

    return vec3(Y, x, y);
}

vec3 convert_Yxy2RGB(vec3 Yxy) {
    float Y = Yxy.x;
    float x = Yxy.y;
    float y = Yxy.z;

    // Convert Yxy to XYZ
    float X = (y == 0.0) ? 0.0 : (x * Y) / y;
    float Z = (y == 0.0) ? 0.0 : ((1.0 - x - y) * Y) / y;

    vec3 xyz = vec3(X, Y, Z);
    return convert_XYZ2RGB(xyz);
}