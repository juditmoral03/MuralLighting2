console.log("Client started");

import * as THREE from 'three';
import { OrbitControls } from './jsm/controls/OrbitControls.js';
import Stats from './jsm/libs/stats.module.js';
import { GUI } from './jsm/libs/lil-gui.module.min.js'; 
import { EXRLoader } from './jsm/loaders/EXRLoader.js'; 
import toneMappingLinear from './toneMappingLinear.js';
import toneMappingReinhardBasic from './toneMappingReinhardBasic.js'; 
import toneMappingReinhardExtended from './toneMappingReinhardExtended.js'
import toneMappingLuminance from './toneMappingLuminance.js'
import ImageView from './imageView.js';
import DifferenceWindow from './differenceWindow.js';
import readTextFile from './shaderReader.js';

const toneMappingMethods = [toneMappingLinear, toneMappingReinhardBasic, toneMappingReinhardExtended, toneMappingLuminance]; 

///// Image Views

var colorOpsGLSL = await readTextFile("shaders/colorOperations.glsl");
THREE.ShaderChunk.ColorOps = colorOpsGLSL;
window.three = THREE; 

// Left view
const containerL = document.getElementById('window1');
var leftView = new ImageView(containerL.clientWidth, containerL.clientHeight);
containerL.appendChild(leftView.renderer.domElement);

// Right View
const containerR = document.getElementById('window2');
var rightView = new ImageView(containerR.clientWidth, containerR.clientHeight);
containerR.appendChild(rightView.renderer.domElement);

// Interactive frames
containerL.classList.add('image-frame', 'hidden');
containerR.classList.add('image-frame', 'hidden');

let selectedWindow = ''; // Initially empty

// LEFT WINDOW CLICK
containerL.addEventListener('click', () => {
    if (selectedWindow === 'left') {
        // If already selected, deselect it
        containerL.classList.add('hidden'); // Hide border
        selectedWindow = ''; // Empty state
        localStorage.removeItem('selectedWindow'); 
        //notifyPython(null); // Send null to Python
    } else {
        // If NOT selected, activate it (and deactivate the other)
        containerL.classList.remove('hidden'); // Show border
        containerR.classList.add('hidden');    // Hide right border
        selectedWindow = 'left';
        localStorage.setItem('selectedWindow', selectedWindow); 
        //notifyPython('left'); 
    }
});

// RIGHT WINDOW CLICK
containerR.addEventListener('click', () => {
    if (selectedWindow === 'right') {
        // If already selected, deselect it
        containerR.classList.add('hidden'); // Hide border
        selectedWindow = ''; // Empty state
        localStorage.removeItem('selectedWindow');
        //notifyPython(null);
    } else {
        // If NOT selected, activate it (and deactivate the other)
        containerR.classList.remove('hidden'); // Show border
        containerL.classList.add('hidden');    // Hide left border
        selectedWindow = 'right';
        localStorage.setItem('selectedWindow', selectedWindow); 
        //notifyPython('right');
    }
});

function applyStoredSelection() {
    const stored = localStorage.getItem('selectedWindow');
    if (!stored) return;

    if (stored === 'left') {
        containerL.classList.remove('hidden');
        containerR.classList.add('hidden');
        selectedWindow = 'left';
        //notifyPython('left'); 
    } else if (stored === 'right') {
        containerR.classList.remove('hidden');
        containerL.classList.add('hidden');
        selectedWindow = 'right';
        //notifyPython('right');
    }
}

// Difference dialog
const containerD = document.getElementById('winDiff');
var vs = await readTextFile("shaders/vs_difference.glsl");
var fs = await readTextFile("shaders/fs_difference.glsl");
var difWin = new DifferenceWindow(vs, fs)
difWin.renderer.setSize(containerD.clientWidth, containerD.clientHeight);
containerD.appendChild(difWin.renderer.domElement);

// Set up Orbit Controls
const controlsL = new OrbitControls(leftView.camera, leftView.renderer.domElement);
const controlsR = new OrbitControls(rightView.camera, rightView.renderer.domElement);
const controlsD = new OrbitControls(difWin.camera, difWin.renderer.domElement);

controlsL.enableRotate = false;
controlsR.enableRotate = false;
controlsD.enableRotate = false;

controlsL.mouseButtons = { LEFT: THREE.MOUSE.PAN, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.PAN }
controlsR.mouseButtons = { LEFT: THREE.MOUSE.PAN, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.PAN }
controlsD.mouseButtons = { LEFT: THREE.MOUSE.PAN, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.PAN }

controlsL.addEventListener('change', () => { syncCameraViews(controlsL, rightView.camera, controlsR); });
controlsR.addEventListener('change', () => { syncCameraViews(controlsR, leftView.camera, controlsL); });

// Tone mapping
leftView.renderer.toneMapping = THREE.CustomToneMapping; 
leftView.renderer.toneMappingExposure = 1.0; 

///// EXR & JPG Loading (PROGRESSIVE)

const exrLoader = new EXRLoader();
exrLoader.setDataType(THREE.FloatType); // --- CHANGE: HalfFloat is faster than Float
const textureLoader = new THREE.TextureLoader(); // --- CHANGE: Loader for JPGs

const TEXTURE_BASE_PATH = './textures/';

// State variables to prevent an old load from overwriting a new one
let currentLeftFile = "";
let currentRightFile = "";

let leftRequestID = 0;
let rightRequestID = 0;

// Variables to know if the EXR has already won the race
let leftEXRLoaded = false;
let rightEXRLoaded = false;

let leftTimeout = null;
let rightTimeout = null;

// --- CHANGE: New progressive loading logic ---
function loadLeftImage(filename) {
    if (!filename) return;
    
    // Cancel previous "Full" load if user changes quickly
    if (leftTimeout) clearTimeout(leftTimeout);

    leftRequestID++; 
    const myRequestID = leftRequestID; 

    // Cleanup base name (remove .exr)
    let baseName = filename;
    if (baseName.toLowerCase().endsWith('.exr')) {
        baseName = baseName.substring(0, baseName.length - 4);
    }

    // 1. PREVIEW LOAD (_small.exr)
    // We use exrLoader, but load the small file.
    const smallUrl = TEXTURE_BASE_PATH + baseName + '_small.exr';
    
    // console.log(`🔍 [ID:${myRequestID}] Looking for preview: ${baseName}_small.exr`);

    exrLoader.load(smallUrl, (texture) => {
        // Only apply if user hasn't changed image
        if (myRequestID === leftRequestID) {
            // console.log("✅ Small EXR loaded (Left)");
            updateLeftView(texture); 
        }
    }, undefined, (err) => {
        // If _small doesn't exist, it's fine, wait for the big one.
        console.warn(`⚠️ ${baseName}_small.exr not found (Left)`);
    });

    // 2. FINAL LOAD (Original .exr)
    // Wait 200ms to avoid blocking interface if user scrolls mouse quickly
    leftTimeout = setTimeout(() => {
        const fullUrl = TEXTURE_BASE_PATH + baseName + '.exr';
        console.log(`🚀 [ID:${myRequestID}] Starting Full EXR (Background): ${baseName}`);

        exrLoader.load(fullUrl, (texture) => {
            if (myRequestID === leftRequestID) {
                console.log(`✅ [ID:${myRequestID}] Full EXR loaded and applied.`);
                
                // Optional: Ensure small memory is released:
                if(leftView.texture) leftView.texture.dispose();
                
                updateLeftView(texture);
            } else {
                texture.dispose(); // If it arrives late, discard it
            }
        }, undefined, (err) => console.error("Error EXR Full Left:", err));

    }, 200); // Safety delay for menu fluidity
}


// --- CHANGE: This function does the actual work of updating the view (previously called loadLeftImage) ---
function updateLeftView(texture) {
    if (!texture) return;

    // ROBUST DETECTION:
    // Loaded EXRs have type Float (1015) or HalfFloat (1016).
    // JPGs have type UnsignedByte (1009).
    const isHDR = (texture.type === THREE.FloatType || texture.type === THREE.HalfFloatType);

    // Call loadImage passing the isHDR flag
    leftView.loadImage(texture, isHDR);

    // If JPG, manually force uniforms in case imageView.js didn't do it
    if (!isHDR) {
        leftView.scene.traverse((object) => {
            if (object.isMesh && object.material) {
                object.material.uniforms.maxInputLuminance.value = 1.0;
                object.material.uniforms.avgInputLuminance.value = 0.5; 
                object.material.needsUpdate = true;
            }
        });
    }

    applyStoredSelection();

    // Normalization sync (only if both are truly HDR)
    if (params.fixNormalization && isHDR) {
        leftView.maxInputLuminance = rightView.maxInputLuminance;
        leftView.avgInputLuminance = rightView.avgInputLuminance;
        leftView.logAvgInputLuminance = rightView.logAvgInputLuminance;
    }

    // Update difference window
    difWin.leftTexture = texture;
    difWin.uMaxLum = leftView.avgInputLuminance || 1.0; // Avoid null values
    recomputeDiff = true;

    render(leftView);
}

// --- CHANGE: Same logic for the right ---
function loadRightImage(filename) {
    if (!filename) return;

    if (rightTimeout) clearTimeout(rightTimeout);

    rightRequestID++;
    const myRequestID = rightRequestID;

    let baseName = filename;
    if (baseName.toLowerCase().endsWith('.exr')) {
        baseName = baseName.substring(0, baseName.length - 4);
    }

    // 1. PREVIEW (_small.exr)
    const smallUrl = TEXTURE_BASE_PATH + baseName + '_small.exr';
    
    exrLoader.load(smallUrl, (texture) => {
        if (myRequestID === rightRequestID) {
            // console.log("✅ Small EXR loaded (Right)");
            updateRightView(texture);
        }
    }, undefined, (err) => {
        console.warn(`⚠️ ${baseName}_small.exr not found (Right)`);
    });

    // 2. FULL (.exr)
    rightTimeout = setTimeout(() => {
        const fullUrl = TEXTURE_BASE_PATH + baseName + '.exr';
        console.log(`🚀 [ID:${myRequestID}] Starting Full EXR Right...`);

        exrLoader.load(fullUrl, (texture) => {
            if (myRequestID === rightRequestID) {
                console.log(`✅ [ID:${myRequestID}] Full EXR Right loaded.`);
                
                if(rightView.texture) rightView.texture.dispose();
                
                updateRightView(texture);
            } else {
                texture.dispose();
            }
        }, undefined, (err) => console.error("Error EXR Full Right:", err));

    }, 200); 
}

function updateRightView(texture) {
    if (!texture) return;

    const isHDR = (texture.type === THREE.FloatType || texture.type === THREE.HalfFloatType);

    rightView.loadImage(texture, isHDR);

    if (!isHDR) {
        rightView.scene.traverse((object) => {
            if (object.isMesh && object.material) {
                object.material.uniforms.maxInputLuminance.value = 1.0;
                object.material.uniforms.avgInputLuminance.value = 0.5;
                object.material.needsUpdate = true;
            }
        });
    }

    difWin.rightTexture = texture;
    recomputeDiff = true;
    
    if (params.fixNormalization && leftView.texture) {
        // Force a render of the left view to update values
        render(leftView);
    }

    render(rightView);
}

function loadingError(error) {
    console.error('An error occurred while loading the texture:', error);
}

function getQueryParams() {
    const params = new URLSearchParams(window.location.search);
    return {
        img1: params.get('img1'),
        img2: params.get('img2')
    };
}

function loadImagesFromUrlParams() {
    const { img1, img2 } = getQueryParams();

    if (img1 && img2) {
        console.log("📥 Loading from URL (Python):", img1, img2);
        
        params.leftImage = img1;
        params.rightImage = img2;

        if (leftImageMenu && rightImageMenu) {
            leftImageMenu.setValue(img1);   
            rightImageMenu.setValue(img2);  
        } else {
            // --- CHANGE: Now we call loadLeftImage with the NAME (string), not the loader
            loadLeftImage(img1);
            loadRightImage(img2);
        }
    }
}


///// GUI

const params = {
    leftImage : '',
    rightImage : '',
    syncViews : true,
    fixNormalization : false,
    selectedTarget: 'both',
    toneMappingMethodName: toneMappingMethods[1].name, 
    maxDiff : 0.1,
    imgOverlay : 0.,
};


///// Input images

let leftImageMenu, rightImageMenu;
let images = [];

fetch('/app/images')
    .then(response => {
        if (!response.ok) throw new Error("Could not load image list");
        return response.json();
    })
    .then(files => {
        images = files;

        // --- CHANGE: Now onChange calls our wrapper function with the filename ---
        leftImageMenu = gui.add(params, 'leftImage', images).name('Left Image').onChange((value) => {
            console.log("Manual Change Left:", value);
            loadLeftImage(value); // Pass string
        });
        
        rightImageMenu = gui.add(params, 'rightImage', images).name('Right Image').onChange((value) => {
            console.log("Manual Change Right:", value);
            loadRightImage(value); // Pass string
        });

        leftImageMenu.domElement.closest('.controller')?.style.setProperty('display', 'none');
        rightImageMenu.domElement.closest('.controller')?.style.setProperty('display', 'none');

        const { img1, img2 } = getQueryParams();
        if (img1 && img2) {
            leftImageMenu.setValue(img1);
            rightImageMenu.setValue(img2);
        } else {
            params.leftImage = images[0];
            params.rightImage = images[1];
            leftImageMenu.setValue(images[0]);
            rightImageMenu.setValue(images[1]);
        }
    })
    .catch(error => {
        console.warn('⚠️ Error loading fetch menu.', error);
        loadImagesFromUrlParams();
    });

loadImagesFromUrlParams();


///// Rendering + Tone mapping

function updateToneMapping() {
    const method = toneMappingMethods.find(method => method.name === params.toneMappingMethodName);

    if (params.selectedTarget === 'both') {
        setToneMappingMethod(leftView.scene, method);
        setToneMappingMethod(rightView.scene, method);
    } else if (params.selectedTarget === 'window1') {
        setToneMappingMethod(leftView.scene, method);
    } else if (params.selectedTarget === 'window2') {
        setToneMappingMethod(rightView.scene, method);
    }

    render(); 
}

window.addEventListener('resize', function () {
    leftView.resize(containerL.clientWidth, containerL.clientHeight);
    rightView.resize(containerR.clientWidth, containerR.clientHeight);
    render(); 
}, false);

function animate() {
    requestAnimationFrame(animate);
    controlsL.update();
    controlsR.update();
    leftView.render();
    rightView.render();
}

function setToneMappingMethod(currentScene, method) {
    currentScene.traverse((object) => {
        if (object.isMesh && object.material) {
            object.material.fragmentShader = method.sourceCode + object.material.originalFragmentShader;
            object.material.needsUpdate = true;
        }
    });
}

function render(view = null) {
    const method = toneMappingMethods.find(method => method.name === params.toneMappingMethodName);

    let viewsToUpdate = [];
    if (view) viewsToUpdate = [view];
    else if (params.selectedTarget === 'both') viewsToUpdate = [leftView, rightView];
    else if (params.selectedTarget === 'window1') viewsToUpdate = [leftView];
    else if (params.selectedTarget === 'window2') viewsToUpdate = [rightView];

    viewsToUpdate.forEach((currentView) => {
        setToneMappingMethod(currentView.scene, method);

        currentView.scene.traverse((object) => {
            if (object.isMesh && object.material) {
                object.material.uniforms.maxInputLuminance.value = currentView.maxInputLuminance;
                object.material.uniforms.avgInputLuminance.value = currentView.avgInputLuminance;
                object.material.uniforms.avg_L_w.value = currentView.logAvgInputLuminance;

                for (const [key, param] of Object.entries(method.parameters)) {
                    if (object.material.uniforms[key]) {
                        object.material.uniforms[key].value = param.value;
                    } else {
                        object.material.uniforms[key] = { value: param.value };
                    }
                }
                object.material.needsUpdate = true;
            }
        });
        currentView.render();
    });
}

let syncing = false;

function syncCameraViews(sourceControls, targetCamera, targetControls) {
    if (!params.syncViews || syncing) return;
    syncing = true; 
    targetCamera.position.copy(sourceControls.object.position);
    targetCamera.quaternion.copy(sourceControls.object.quaternion);
    targetCamera.zoom = sourceControls.object.zoom;
    targetCamera.updateProjectionMatrix();
    targetControls.target.copy(sourceControls.target);
    targetControls.update();
    syncing = false; 
}

animate();


///// Image difference

const dialog = document.getElementById('differenceDialog'); 
const dragHandle = document.getElementById('drag-handle');  
const closeDialogButton = document.querySelector('.close-button'); 
let recomputeDiff = true;

function openDialog() {
    dialog.style.display = 'flex';
    document.body.style.overflow = 'hidden'; 
    difWin.updateDiffParams(params.maxDiff, params.imgOverlay);
    difWin.show(containerD.clientWidth, containerD.clientHeight, recomputeDiff);
    recomputeDiff = false;  
}

function closeDialog() {
    dialog.style.display = 'none'; 
    document.body.style.overflow = 'auto'; 
}

closeDialogButton.addEventListener('click', closeDialog);

dialog.addEventListener('click', (event) => {
    if (event.target === dialog) { closeDialog(); }
});

let offsetX = 0, offsetY = 0;
let isDragging = false;

dragHandle.addEventListener('mousedown', (e) => {
    isDragging = true;
    offsetX = e.clientX - dialog.offsetLeft;
    offsetY = e.clientY - dialog.offsetTop;
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
});

function onMouseMove(e) {
    if (isDragging) {
        dialog.style.left = `${e.clientX - offsetX}px`;
        dialog.style.top = `${e.clientY - offsetY}px`;
    }
}

function onMouseUp() {
    isDragging = false;
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);
}

function updateDiffParams() {
    difWin.updateDiffParams(params.maxDiff, params.imgOverlay);
}

// Function to send selection to Python
async function notifyPython(selection) {
    
    
    let url;
    if (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost') {
        // LOCAL Mode: Point to NiceGUI port (8080)
        url = 'http://127.0.0.1:8080/set_selected_window';
    } else {
        // PRODUCTION Mode: Assume same domain
        url = '/set_selected_window';
    }

    // console.log(`📡 Sending selection '${selection}' to: ${url}`);

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ selected: selection })
        });
        
        if (!response.ok) throw new Error(response.status);

    } catch (error) {
        console.warn("⚠️ Error connecting to Python:", error);
    }
}

window.addEventListener('DOMContentLoaded', applyStoredSelection);
window.loadLeftImage = loadLeftImage;
window.loadRightImage = loadRightImage;


// Listen for messages from parent (Python/NiceGUI on port 8080)
window.addEventListener('message', function(event) {
    // Good practice to verify origin, but locally we can skip or trust.
    const data = event.data;

    if (data.type === 'change_left') {
        console.log("📨 Received command change Left:", data.path);
        loadLeftImage(data.path);
    } 
    else if (data.type === 'change_right') {
        console.log("📨 Received command change Right:", data.path);
        loadRightImage(data.path);
    }

    // --- NEW CODE FOR SYNC ---
    if (data.type === 'toggle_sync') {
        console.log("🔄 Sync changed to:", data.value);
        
        // 1. Update logic variable
        params.syncViews = data.value;

        // 2. Visually update checkbox in right panel (lil-gui)
        if (gui && gui.controllers) {
            gui.controllers.forEach(controller => {
                if (controller.property === 'syncViews') {
                    controller.setValue(data.value);
                }
            });
        }
        
        // 3. Force immediate resync when activating
        if (data.value === true) {
            syncing = false; 
            // Copy Left camera to Right
            rightView.camera.position.copy(leftView.camera.position);
            rightView.camera.quaternion.copy(leftView.camera.quaternion);
            rightView.camera.zoom = leftView.camera.zoom;
            controlsR.target.copy(controlsL.target);
        }
    }

    // --- TONE MAPPING BLOCK (DEFINITIVE SOLUTION V2) ---
    if (data.type === 'tm_update') {
        
        // 1. Target
        if (data.target) params.selectedTarget = data.target;

        // 2. Mapping
        const algoMap = {
            "toneMappingLinear": toneMappingMethods[0],
            "toneMappingReinhardBasic": toneMappingMethods[1],
            "toneMappingReinhardExtended": toneMappingMethods[2],
            "toneMappingLuminance": toneMappingMethods[3]
        };

        const methodObj = algoMap[data.algo];

        if (methodObj && methodObj.parameters) {
            params.toneMappingMethodName = methodObj.name;
            if (typeof updateFolders === 'function') updateFolders(methodObj.name);

            // --- ROBUST PARAMETER APPLICATION ---
            
            // A) EXPOSURE (Linear, Basic)
            if (methodObj.parameters.exposure) {
                methodObj.parameters.exposure.value = data.exposure;
            }

            // B) REINHARD EXTENDED (Key & White)
            if (data.algo === "toneMappingReinhardExtended") {
                // Key / a
                if (methodObj.parameters.key) methodObj.parameters.key.value = data.key;
                else if (methodObj.parameters.a) methodObj.parameters.a.value = data.key;
                else if (methodObj.parameters.exposure) methodObj.parameters.exposure.value = data.key;

                // White / C_max
                if (methodObj.parameters.C_max) methodObj.parameters.C_max.value = data.white;
                else if (methodObj.parameters.C_white) methodObj.parameters.C_white.value = data.white;
                else if (methodObj.parameters.white) methodObj.parameters.white.value = data.white;
                else if (methodObj.parameters.whitePoint) methodObj.parameters.whitePoint.value = data.white;
                else if (methodObj.parameters.L_white) methodObj.parameters.L_white.value = data.white;
            }

            // C) LUMINANCE (Max Lum) - HERE IS THE FIX
            if (data.algo === "toneMappingLuminance") {
                const paramKeys = Object.keys(methodObj.parameters);
                
                if (paramKeys.length > 0) {
                    // TRICK: Pick the first parameter the shader has, whatever it's called.
                    // This fixes unknown name errors.
                    const realName = paramKeys[0]; 
                    console.log("🔗 Connecting slider to:", realName);
                    methodObj.parameters[realName].value = data.maxLum;
                } else {
                    console.warn("⚠️ No parameters found in toneMappingLuminance");
                }
            }
        }

        // 4. Render
        params.fixNormalization = data.fix;
        if (typeof updateToneMapping === 'function') updateToneMapping();
    }


    // --- IMAGE DIFFERENCE BLOCK ---
    if (data.type === 'open_diff') {
        console.log("🔘 Opening Difference Dialog from Menu");
        // Call global function openDialog() defined in client.js
        if (typeof openDialog === 'function') {
            openDialog();
        }
    }


    // =========================================================
    //  HTML CONTROLS LOGIC (Image Difference)
    // =========================================================

    // 1. References to DOM elements (Sliders in index.html)
    const sliderDiff = document.getElementById('slider_maxDiff');
    const sliderOver = document.getElementById('slider_overlay');
    const labelDiff  = document.getElementById('val_maxDiff');
    const labelOver  = document.getElementById('val_overlay');

    // 2. Activate listeners if elements exist
    if (sliderDiff && sliderOver) {
        // Listen for changes in Max Difference
        sliderDiff.addEventListener('input', (e) => {
            const val = parseFloat(e.target.value);
            params.maxDiff = val;
            labelDiff.textContent = val.toFixed(3); 
            updateDiffParams(); 
        });

        // Listen for changes in Image Overlay
        sliderOver.addEventListener('input', (e) => {
            const val = parseFloat(e.target.value);
            params.imgOverlay = val;
            labelOver.textContent = val.toFixed(2); 
            updateDiffParams(); 
        });
    }

    // =========================================================
    //  MESSAGE LISTENER (Python -> JS)
    // =========================================================

    window.addEventListener('message', function(event) {
        const data = event.data;

        

        if (data.type === 'change_left') { loadLeftImage(data.path); }
        if (data.type === 'change_right') { loadRightImage(data.path); }
        
        


        // --- IMAGE DIFFERENCE BLOCK (TOGGLE FIXED) ---
        if (data.type === 'toggle_diff') {
            console.log("🔘 Toggle Difference Window");
            
            const dialog = document.getElementById('differenceDialog');
            if (dialog) {
                // WE USE getComputedStyle: The robust way to know if it's visible
                const style = window.getComputedStyle(dialog);
                
                if (style.display === 'none') {
                    // If hidden -> Open
                    if (typeof openDialog === 'function') openDialog();
                } else {
                    // If visible (flex, block, etc) -> Close
                    if (typeof closeDialog === 'function') closeDialog();
                }
            }
        }
    });

});