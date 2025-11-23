/* This module provides a class to encapsulate the widget where we show each image */

import * as THREE from 'three';
import analyzeTexture from './analyzeTexture.js'; // Import the analyzeTexture function
import colorMapTexture from './colorMapTexture.js';

const VS = `
      varying vec2 vUv;
  
      void main() {
        vUv = uv; // Pass UV coordinates to the fragment shader
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `;
const FS = `
      uniform sampler2D uTexture;
      varying vec2 vUv;
  
      void main() {
        vec4 textureColor = texture2D(uTexture, vUv);
        gl_FragColor = vec4(CustomToneMapping(textureColor.rgb),1.0); // Set the color of the fragment to the sampled texture color
      }
    `;


class ImageView {

    constructor(width, height) {
        this.renderer = new THREE.WebGLRenderer();
        this.renderer.setSize(width, height);
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 100);
        this.camera.position.z = 2;
        this.material = null;
        this.maxInputLuminance = null;
        this.avgInputLuminance = null;
        this.logAvgInputLuminance = null;
    }

    loadImage(texture, log_properties=false) {
        console.log("Loading texture ...");

        const t_width = texture.image.width;
        const t_height = texture.image.height;
        const aspectRatio = t_width / t_height;
    
        // Analyze the texture
        const {r, g, b, L} = analyzeTexture(texture); // max and min RGB values of the texture
        this.maxInputLuminance = Math.max(r.max, g.max, b.max);
        this.avgInputLuminance = (r.average/3 + g.average/3 + b.average/3);
        // this.maxInputLuminance = 0.2126 * r.max + 0.7152 * g.max + 0.0722 * b.max;
        // this.avgInputLuminance = 0.2126 * r.average + 0.7152 * g.average + 0.0722 * b.average;
        this.logAvgInputLuminance = L.average;

        // Log the properties of the texture
        if (log_properties) {
            console.log('Texture properties:',
                '\n  Format:', texture.format,
                '\n  Type:', texture.type,
                '\n  Size:', texture.image.width, 'x', texture.image.height,
                '\n  Mipmap generation:', texture.generateMipmaps,
                '\n  MinFilter:', texture.minFilter,
                '\n  MagFilter:', texture.magFilter);

            console.log('Texture RGB Analysis:',
                `\n  Red - Min: ${r.min}, Max: ${r.max}, Sum: ${r.sum}, Count:${r.count}, Avg: ${r.average}`,
                `\n  Green - Min: ${g.min}, Max: ${g.max}, Sum: ${g.sum}, Count:${g.count}, Avg: ${g.average}`,
                `\n  Blue - Min: ${b.min}, Max: ${b.max}, Sum: ${b.sum}, Count:${b.count}, Avg: ${b.average}`,
                '\n  Max input luminance:', this.maxInputLuminance,
                '\n  Avg input luminance:', this.avgInputLuminance,
                '\n  Log Avg input L:', this.logAvgInputLuminance,
                '\n  Max input L:', L.max);
        }
        
        // Create a material using the texture
        this.material = new THREE.ShaderMaterial({
            uniforms: {
                uTexture: { type: 't', value: texture }, // Add the texture as a uniform
                maxInputLuminance: { value: () => this.maxInputLuminance },
                avgInputLuminance: { value: () => this.avgInputLuminance },
                avg_L_w:           { value: () => this.logAvgInputLuminance },
                uColorMap:         { type: 't', value: colorMapTexture}
            },
            toneMapped: false,
            vertexShader: VS,
            fragmentShader: FS
        });
        this.material.originalFragmentShader = this.material.fragmentShader;
        this.material.fragmentShader = "vec3 CustomToneMapping( vec3 color ) {return color;}" + this.material.originalFragmentShader;
    
        // Create a plane geometry for displaying the image
        const geometry = new THREE.PlaneGeometry(3.2 * aspectRatio, 3.2); // Adjust the size as needed for the image
    
        // Create a mesh using the geometry and material
        const mesh = new THREE.Mesh(geometry, this.material);
        mesh.position.set(0, 0, 0); // Center the mesh in the scene
    
        // Add mesh to the scene
        this.scene.add(mesh);
        
        console.log("Done");
    }    

    resize(width, height) {
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    render() {
        this.renderer.render(this.scene, this.camera);
    }
}

export default ImageView