/* This module provides a class to encapsulate the widget where we show luminance differences between two images */

import * as THREE from 'three';
import colorMapTextureDiff from './colorMapTextureDiff.js';

class DifferenceWindow {

    constructor(VS, FS) {
        this.renderer = new THREE.WebGLRenderer();
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, 1, 0.1, 100);
        this.camera.position.z = 2;
        this.leftTexture = null;
        this.rightTexture = null;
        this.colorMap = colorMapTextureDiff;
        this.uMaxDelta = 0;
        this.uMaxDeltaWeight = 0;
        this.uImgOverlay = 0;
        this.uMaxLum = 0;

        this.material = new THREE.ShaderMaterial({
            uniforms: {
                uLeftTexture: { type: 't', value: this.leftTexture }, // Add the texture as a uniform
                uRightTexture: { type: 't', value: this.rightTexture }, // Add the texture as a uniform
                uColorMap: { type: 't', value: this.colorMap }, // Add the texture as a uniform
                uMaxDelta: { value: () => this.uMaxDelta },
                uImgOverlay: { value: () => this.uImgOverlay },
                uMaxLum: { value: () => this.uMaxLum },
            },
            toneMapped: false,
            vertexShader: VS,
            fragmentShader: FS
        });
        
        // Create a plane geometry for displaying the image
        this.geometry = new THREE.PlaneGeometry(3.1, 3.1); // Adjust the size as needed for the image
    
        // Create a mesh using the geometry and material
        this.mesh = new THREE.Mesh(this.geometry, this.material);
        //mesh.position.x = -1.35;
        this.mesh.position.set(0, 0, 0);

        // Add the mesh to the scene
        this.scene.add(this.mesh);
    }

    /**
     * Show the dialog and update the scene and camera
     */
    show(width, height, recompute = true) {
        //update textures, they are changed in client.js when loading them
        if (recompute) {
            this.material.uniforms.uLeftTexture.value = this.leftTexture;
            this.material.uniforms.uRightTexture.value = this.rightTexture;
            this.material.uniforms.uColorMap.value = this.colorMap;
            this.uMaxDelta = this.computeMaxDelta();
            this.material.uniforms.uMaxDelta.value = this.uMaxDelta * this.uMaxDeltaWeight;
            this.material.uniforms.uImgOverlay.value = this.uImgOverlay;
            this.material.uniforms.uMaxLum.value = this.uMaxLum;
            this.material.needsUpdate = true;
        }

        //update renderer size
        this.renderer.setSize(width, height);

        //update camera aspect ratio and PM
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();

        //reset the scene to allow changes in size
        this.mesh.scale.set(this.leftTexture.image.width / this.leftTexture.image.height, 1, 1);

        this.startRendering();
    }

    /**
     * Hide the dialog and stop rendering
     */
    stop() {
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
          }
    }

    /**
     * Start rendering the scene
     */
    startRendering() {
        const renderLoop = () => {
            this.renderer.render(this.scene, this.camera);
            this.animationFrameId = requestAnimationFrame(renderLoop);
        };
        this.animationFrameId = requestAnimationFrame(renderLoop);
    }

    /**
     * Estimate the max luminance delta between both images
     */
    computeMaxDelta() {
        // Calculate luminance using the CIE XYZ 1931 sRGB D65
        const computeLuminance = (r, g, b) => 0.2126729 * r + 0.7151522 * g + 0.0721750 * b;

        const lArr = this.leftTexture.source.data.data; // Assuming this is a flat array
        const rArr = this.rightTexture.source.data.data;

        // Iterate over the RGBA arrays in chunks of 4 (r, g, b, a)
        const stats = lArr.reduce((result, _, i) => {
            if (i % 4 !== 0) return result; // Skip indices that aren't the start of an RGBA set

            const r1 = lArr[i], g1 = lArr[i + 1], b1 = lArr[i + 2]; // Left texture RGB
            const r2 = rArr[i], g2 = rArr[i + 1], b2 = rArr[i + 2]; // Right texture RGB

            const luminance1 = computeLuminance(r1, g1, b1);
            const luminance2 = computeLuminance(r2, g2, b2);
            const difference = Math.abs(luminance1 - luminance2);

            result.sum += difference;
            result.sum2 += difference * difference;
            result.count += 1;
            result.max = Math.max(result.max, difference); // Update maxDiff

            return result;
        }, {
            sum: 0,
            sum2: 0,
            count: 0,
            max: 0
        });

        const avg = stats.sum / stats.count;
        const stdDev = Math.sqrt(stats.sum2 / stats.count - avg * avg);
        // const max2 = avg + stdDev * 3;    // w/o outliers 
        const max2 = avg + stdDev;        // w/o outliers 

        console.log('Max Delta:', stats.max,
                    '\nAvg Delta:', avg,
                    '\nStdDev Delta:', stdDev,
                    '\nMax Delta 2:', max2);

        // return stats.sum / stats.count;      // avg delta
        // return stats.max;                    // max delta
        return max2;                            // modified max delta
    }

    /**
     * Update difference parameters 
     */
    updateDiffParams(maxDeltaWeight, imgOverlay) {
        this.uMaxDeltaWeight = maxDeltaWeight;
        this.uImgOverlay = imgOverlay;

        this.material.uniforms.uMaxDelta.value = this.uMaxDelta * maxDeltaWeight;     // weighted max value
        this.material.uniforms.uImgOverlay.value = imgOverlay;
    }
}

export default DifferenceWindow