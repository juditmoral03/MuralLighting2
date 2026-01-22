/* This module provides a class to encapsulate the widget where we show each image */

import * as THREE from 'three';
import analyzeTexture from './analyzeTexture.js'; 
import colorMapTexture from './colorMapTexture.js';

const VS = `
      varying vec2 vUv;
  
      void main() {
        vUv = uv; 
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `;
const FS = `
      uniform sampler2D uTexture;
      varying vec2 vUv;
  
      void main() {
        vec4 textureColor = texture2D(uTexture, vUv);
        gl_FragColor = vec4(CustomToneMapping(textureColor.rgb),1.0); 
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
        this.texture = null;
    }

   
    loadImage(texture, isHDR = true, log_properties = false) {
        console.log(`Loading texture... (Is HDR: ${isHDR})`);

        
        while(this.scene.children.length > 0){ 
            const object = this.scene.children[0];
            if (object.geometry) object.geometry.dispose();
            if (object.material) object.material.dispose();
            this.scene.remove(object); 
        }

        this.texture = texture;
        const t_width = texture.image.width;
        const t_height = texture.image.height;
        const aspectRatio = t_width / t_height;
    
        
        if (isHDR) {
            const {r, g, b, L} = analyzeTexture(texture); 
            this.maxInputLuminance = Math.max(r.max, g.max, b.max);
            this.avgInputLuminance = (r.average/3 + g.average/3 + b.average/3);
            this.logAvgInputLuminance = L.average;

            if (log_properties) {
                console.log('Texture properties:', L.max);
            }
        } else {
            
            this.maxInputLuminance = 1.0;
            this.avgInputLuminance = 0.5;
            this.logAvgInputLuminance = 0.5;
        }
        
        
        this.material = new THREE.ShaderMaterial({
            uniforms: {
                uTexture: { type: 't', value: texture }, 
                maxInputLuminance: { value: this.maxInputLuminance },
                avgInputLuminance: { value: this.avgInputLuminance },
                avg_L_w:           { value: this.logAvgInputLuminance },
                uColorMap:         { type: 't', value: colorMapTexture}
            },
            toneMapped: false,
            vertexShader: VS,
            fragmentShader: FS
        });

        this.material.originalFragmentShader = this.material.fragmentShader;
        this.material.fragmentShader = "vec3 CustomToneMapping( vec3 color ) {return color;}" + this.material.originalFragmentShader;
    
        const geometry = new THREE.PlaneGeometry(3.2 * aspectRatio, 3.2); 
        const mesh = new THREE.Mesh(geometry, this.material);
        mesh.position.set(0, 0, 0); 
    
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

export default ImageView;