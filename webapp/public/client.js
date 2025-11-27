console.log("Client started");

import * as THREE from 'three';
import { OrbitControls } from './jsm/controls/OrbitControls.js';
import Stats from './jsm/libs/stats.module.js';
import { GUI } from './jsm/libs/lil-gui.module.min.js'; // Import lil-gui for the exposure slider
import { EXRLoader } from './jsm/loaders/EXRLoader.js'; // Ensure you have this loader
// import analyzeTexture from './analyzeTexture.js'; // Import the analyzeTexture function
import toneMappingLinear from './toneMappingLinear.js';
//import toneMappingLinearGamma from './toneMappingLinearGamma.js';
import toneMappingReinhardBasic from './toneMappingReinhardBasic.js'; // Import the toneMappingReinhardBasic shader
import toneMappingReinhardExtended from './toneMappingReinhardExtended.js'
import toneMappingLuminance from './toneMappingLuminance.js'
import ImageView from './imageView.js';
import DifferenceWindow from './differenceWindow.js';
import readTextFile from './shaderReader.js';
// import colorMapTexture from './colorMapTexture.js';
// import colorMapTextureDiff from './colorMapTextureDiff.js';

const toneMappingMethods = [toneMappingLinear, toneMappingReinhardBasic, toneMappingReinhardExtended, toneMappingLuminance]; // Add more tone mapping methods here


///// Image Views

// Create the color ops chunk
var colorOpsGLSL = await readTextFile("shaders/colorOperations.glsl");
THREE.ShaderChunk.ColorOps = colorOpsGLSL;
window.three = THREE; // For debugging

// Left view
const containerL = document.getElementById('window1');
var leftView = new ImageView(containerL.clientWidth, containerL.clientHeight);
containerL.appendChild(leftView.renderer.domElement);
console.log("container size: " + containerL.clientWidth + " x " + containerL.clientHeight);

// Right View
const containerR = document.getElementById('window2');
var rightView = new ImageView(containerR.clientWidth, containerR.clientHeight);
containerR.appendChild(rightView.renderer.domElement);

//Add interactive frames
containerL.classList.add('image-frame', 'hidden');
containerR.classList.add('image-frame', 'hidden');

let selectedWindow = '';

// Only one frame visible at a time and save selection
// Only one frame visible at a time and save selection
containerL.addEventListener('click', () => {
    containerL.classList.remove('hidden');
    containerR.classList.add('hidden');
    selectedWindow = 'left';
    localStorage.setItem('selectedWindow', selectedWindow); 
    console.log("Seleccionat: esquerra");
    
    // --- NUEVO: AVISAR A PYTHON ---
    notifyPython('left'); 
});

containerR.addEventListener('click', () => {
    containerR.classList.remove('hidden');
    containerL.classList.add('hidden');
    selectedWindow = 'right';
    localStorage.setItem('selectedWindow', selectedWindow); 
    console.log("Seleccionat: dreta");

    // --- NUEVO: AVISAR A PYTHON ---
    notifyPython('right');
});


function applyStoredSelection() {
    const stored = localStorage.getItem('selectedWindow');
    if (!stored) {
        return;
    }

    if (stored === 'left') {
        containerL.classList.remove('hidden');
        containerR.classList.add('hidden');
        selectedWindow = 'left';
        // Avisamos a Python al cargar la página
        notifyPython('left'); 
        
    } else if (stored === 'right') {
        containerR.classList.remove('hidden');
        containerL.classList.add('hidden');
        selectedWindow = 'right';
        // Avisamos a Python al cargar la página
        notifyPython('right');
    }
}



// Difference dialog
const containerD = document.getElementById('winDiff');
var vs = await readTextFile("shaders/vs_difference.glsl");
var fs = await readTextFile("shaders/fs_difference.glsl");
var difWin = new DifferenceWindow(vs, fs)
difWin.renderer.setSize(containerD.clientWidth, containerD.clientHeight);
containerD.appendChild(difWin.renderer.domElement);
// console.log("container size: " + containerD.clientWidth + " x " + containerD.clientHeight);



// Set up Orbit Controls
const controlsL = new OrbitControls(leftView.camera, leftView.renderer.domElement);
const controlsR = new OrbitControls(rightView.camera, rightView.renderer.domElement);
const controlsD = new OrbitControls(difWin.camera, difWin.renderer.domElement);

controlsL.enableRotate = false;
controlsR.enableRotate = false;
controlsD.enableRotate = false;

controlsL.mouseButtons = {
	LEFT: THREE.MOUSE.PAN,
	MIDDLE: THREE.MOUSE.DOLLY,
	RIGHT: THREE.MOUSE.PAN
}

controlsR.mouseButtons = {
	LEFT: THREE.MOUSE.PAN,
	MIDDLE: THREE.MOUSE.DOLLY,
	RIGHT: THREE.MOUSE.PAN
}

controlsD.mouseButtons = {
	LEFT: THREE.MOUSE.PAN,
	MIDDLE: THREE.MOUSE.DOLLY,
	RIGHT: THREE.MOUSE.PAN
}

controlsL.addEventListener('change', () => {
    syncCameraViews(controlsL, rightView.camera, controlsR);
});

controlsR.addEventListener('change', () => {
    syncCameraViews(controlsR, leftView.camera, controlsL);
});

// Initialize stats for performance monitoring
//const stats = Stats();
//document.body.appendChild(stats.dom);

// Tone mapping
var toneMappingDefaultShaderCode = THREE.ShaderChunk.tonemapping_pars_fragment;
leftView.renderer.toneMapping = THREE.CustomToneMapping; 
leftView.renderer.toneMappingExposure = 1.0; // Default exposure value


///// EXR loading

// // Luminance values used for tone mapping
// var maxInputLuminance = null;
// var avgInputLuminance = null;
// var logAvgInputLuminance = null;

const exrLoader = new EXRLoader();
exrLoader.setDataType(THREE.FloatType); 

function loadLeftImage(texture = null) {
    // Load image and update luminance values
    if (texture) leftView.loadImage(texture, true);

    applyStoredSelection();

    // maxInputLuminance = leftView.maxInputLuminance;
    // avgInputLuminance = leftView.avgInputLuminance;
    // logAvgInputLuminance = leftView.logAvgInputLuminance;

    // Update the L_white of extended reinhard
    //toneMappingReinhardExtended.updateParameterValue("L_white", L.max);
    //toneMappingReinhardExtended.updateParameterConfig("L_white", 0, L.max*2, L.max);
    //console.log(toneMappingFolder.folders);

    // // Find the Reinhard Folder
    // var folder = toneMappingFolder.folders.find(f => f._title === "Reinhard Extended");
    // if (folder) {
    //     // Find the controller for the parameter based on its name
    //     const controller = folder.controllers.find(ctrl => ctrl._name === "L White");
    //     if (controller) {
    //         // Update the GUI display
    //         //controller.max(L.max*2);
    //         //controller.updateDisplay();
    //     } else console.log("NOT FOUND");
    // }
    
    // // Find the Luminance Folder
    // //toneMappingLuminance.updateParameterValue("Max_L", L.max);
    // folder = toneMappingFolder.folders.find(f => f._title === "Luminance");
    // if (folder) {
    //     // Find the controller for the parameter based on its name
    //     const controller = folder.controllers.find(ctrl => ctrl._name === "Max Luminance");
    //     if (controller) {
    //         // Update the GUI display
    //     //      controller.max(L.max);
    //     //      controller.updateDisplay();
    //     } else console.log("NOT FOUND");
    // }

    // Use right-view normalization for this view too (overwrite computed values)
    if (params.fixNormalization) {
        leftView.maxInputLuminance = rightView.maxInputLuminance;
        leftView.avgInputLuminance = rightView.avgInputLuminance;
        leftView.logAvgInputLuminance = rightView.logAvgInputLuminance;
    }

    // Update texture for difference
    if (texture) difWin.leftTexture = texture;
    difWin.uMaxLum = leftView.avgInputLuminance;   // needed for image overlay
    recomputeDiff = true;

    // Re-render view 
    render(leftView);
}

function loadRightImage(texture) {
    // Load image and update luminance values
    rightView.loadImage(texture);
    // maxInputLuminance = rightView.maxInputLuminance;
    // avgInputLuminance = rightView.avgInputLuminance;
    // logAvgInputLuminance = rightView.logAvgInputLuminance;

    // Update texture for difference
    difWin.rightTexture = texture;
    recomputeDiff = true;
    
    // Recompute left view too if needed
    if (params.fixNormalization) loadLeftImage();

    // Re-render view
    render(rightView);
}

function showSelectedImages() {
    // Only if there are already two images selected
    if (params.leftImage && params.rightImage) {
        exrLoader.load('./textures/' + params.leftImage, loadLeftImage, undefined, loadingError);
        exrLoader.load('./textures/' + params.rightImage, loadRightImage, undefined, loadingError);
    }
}

function getQueryParams() {
    const params = new URLSearchParams(window.location.search);
    return {
        img1: params.get('img1'),
        img2: params.get('img2')
    };
}

const TEXTURE_BASE_PATH = '/textures/'; 

function loadImagesFromUrlParams() {
    const { img1, img2 } = getQueryParams();

    // Si Python nos envía imágenes, las cargamos INMEDIATAMENTE
    if (img1 && img2) {
        console.log("📥 Cargando desde URL (Python):", img1, img2);
        
        params.leftImage = img1;
        params.rightImage = img2;

        // Intentamos actualizar los menús de la GUI si ya existen
        if (leftImageMenu && rightImageMenu) {
            leftImageMenu.setValue(img1);   
            rightImageMenu.setValue(img2);  
        } else {
            // Si los menús no existen aún, cargamos las imágenes directamente usando la ruta absoluta
            exrLoader.load(TEXTURE_BASE_PATH + img1, loadLeftImage, undefined, loadingError);
            exrLoader.load(TEXTURE_BASE_PATH + img2, loadRightImage, undefined, loadingError);
        }
    }
}

// Call on page load
//window.addEventListener('DOMContentLoaded', loadSelectedImagesFromURL);



function loadingError(error) {
    console.error('An error occurred while loading the EXR texture:', error);
}





///// GUI

// Parameters
const params = {
    leftImage : '',
    rightImage : '',
    syncViews : true,
    fixNormalization : false,
    selectedTarget: 'both',
    toneMappingMethodName: toneMappingMethods[1].name, // Default tone mapping method
    maxDiff : 0.1,//1.0,
    imgOverlay : 0.,//0.25,
};

// Create the GUI
const gui = new GUI();

// // Image selection (temporary)
// const leftImageMenu = gui.add(params, 'leftImage').name('Left Image').onChange((value) => {
//     exrLoader.load('./textures/' + value, loadLeftImage, undefined, loadingError);
// });
// const rightImageMenu = gui.add(params, 'rightImage').name('Right Image').onChange((value) => {
//     exrLoader.load('./textures/' + value, loadRightImage, undefined, loadingError);
// });

// Basic params
gui.add(params, 'syncViews').name('Sync Views');

// Tone mapping
const toneMappingFolder = gui.addFolder('Tone Mapping');
toneMappingFolder.add(params, 'selectedTarget', { 'Both Windows': 'both', 'Window 1': 'window1', 'Window 2': 'window2' }).name('Apply To');

// Tone mapping selection dropdown
var options = toneMappingMethods.map(method => method.name);
toneMappingFolder.add(params, 'toneMappingMethodName', options).name('Tone mapping').onChange((value) => {
    updateFolders(value);
    updateToneMapping();
});


// To fix/share normalization between views
toneMappingFolder.add(params, 'fixNormalization').name('Fix normalization');

// Specific params of each method
for (let method of toneMappingMethods) {
    const folder = toneMappingFolder.addFolder(method.name);
    for (const [_, param] of Object.entries(method.parameters)) {
        folder.add(param, "value", param.min, param.max).name(param.name).onChange(() => updateToneMapping());
    }
}


// toneMappingFolder.open();
toneMappingFolder.close(); 
updateFolders(params.toneMappingMethodName); 


// Function to collapse other TM folders and expand the selected one
function updateFolders(selectedOption) {
    toneMappingFolder.folders.forEach(folder => {
        const titleElement = folder.domElement.querySelector('.title');

        if (folder._title === selectedOption) {
            folder.open(); 
            folder.domElement.style.display = ''; 
            if (titleElement) titleElement.style.display = 'none'; // 🔹 amaga el títol del mètode actiu
        } else {
            folder.close(); 
            folder.domElement.style.display = 'none'; 
            if (titleElement) titleElement.style.display = ''; // 🔹 mostra el títol quan no és actiu
        }
    });
}











// Image difference params
const imgDiffFolder = gui.addFolder('Image Difference');
imgDiffFolder.add({ openDialog: () => openDialog() }, 'openDialog').name('Show Difference');
imgDiffFolder.add(params, 'maxDiff', 0.001, 1.0).name('Max Difference').onChange((value) => updateDiffParams());
imgDiffFolder.add(params, 'imgOverlay', 0.0, 1.0).name('Image Overlay').onChange((value) => updateDiffParams());
// imgDiffFolder.close();



///// Input images

let leftImageMenu, rightImageMenu;
let images = [];

// Cargar lista de imágenes para el menú (Secundario)
fetch('/app/images')
    .then(response => {
        if (!response.ok) throw new Error("No se pudo cargar la lista de imágenes");
        return response.json();
    })
    .then(files => {
        images = files;

        // Creamos los menús del GUI
        leftImageMenu = gui.add(params, 'leftImage', images).name('Left Image').onChange((value) => {
            console.log("Cambio manual Left:", value);
            exrLoader.load(TEXTURE_BASE_PATH + value, loadLeftImage, undefined, loadingError);
        });
        
        rightImageMenu = gui.add(params, 'rightImage', images).name('Right Image').onChange((value) => {
            console.log("Cambio manual Right:", value);
            exrLoader.load(TEXTURE_BASE_PATH + value, loadRightImage, undefined, loadingError);
        });

        // Ocultar inputs extraños del GUI
        leftImageMenu.domElement.closest('.controller')?.style.setProperty('display', 'none');
        rightImageMenu.domElement.closest('.controller')?.style.setProperty('display', 'none');

        // Una vez creado el menú, sincronizamos por si la URL ya traía imágenes
        // (Esto evita que el menú sobrescriba la selección de Python)
        const { img1, img2 } = getQueryParams();
        if (img1 && img2) {
            leftImageMenu.setValue(img1);
            rightImageMenu.setValue(img2);
        } else {
            // Si no hay nada en la URL, cargamos los primeros por defecto
            params.leftImage = images[0];
            params.rightImage = images[1];
            leftImageMenu.setValue(images[0]);
            rightImageMenu.setValue(images[1]);
        }
    })
    .catch(error => {
        console.warn('⚠️ Error cargando menú de imágenes (fetch failed). Cargando imágenes de URL igualmente.', error);
        // Aunque falle el fetch del menú, CARGAMOS LAS IMÁGENES DE PYTHON
        loadImagesFromUrlParams();
    });

// EJECUCIÓN INMEDIATA:
// No esperamos al fetch. Si hay parámetros en la URL, cargamos la escena ya.
loadImagesFromUrlParams();


///// Rendering + Tone mapping

// Apply selected method on the images
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

    render(); // Render the selected scenes
}

// Handle window resizing
window.addEventListener('resize', function () {
    leftView.resize(containerL.clientWidth, containerL.clientHeight);
    rightView.resize(containerR.clientWidth, containerR.clientHeight);

    render(); // Re-render the scene after resizing
}, false);

// Animation loop
function animate() {
    requestAnimationFrame(animate);

    controlsL.update();
    controlsR.update();

    leftView.render();
    rightView.render();
}
// animate();

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

    // Select views to update (if not provided)
    let viewsToUpdate = [];
    if (view)
        viewsToUpdate = [view];
    else if (params.selectedTarget === 'both') {
        viewsToUpdate = [leftView, rightView];
    } else if (params.selectedTarget === 'window1') {
        viewsToUpdate = [leftView];
    } else if (params.selectedTarget === 'window2') {
        viewsToUpdate = [rightView];
    }

    // Process views
    viewsToUpdate.forEach((currentView) => {
        // Set tone mapping parameters
        setToneMappingMethod(currentView.scene, method);

        currentView.scene.traverse((object) => {
            if (object.isMesh && object.material) {
                object.material.uniforms.maxInputLuminance.value = currentView.maxInputLuminance;
                object.material.uniforms.avgInputLuminance.value = currentView.avgInputLuminance;
                object.material.uniforms.avg_L_w.value = currentView.logAvgInputLuminance;

                // Apply tone mapping parameters
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

        // Render scene
        currentView.render();
    });
}

let syncing = false;

function syncCameraViews(sourceControls, targetCamera, targetControls) {
    if (!params.syncViews || syncing) return;

    syncing = true; // Prevent recursive calls

    // Copy position and orientation
    targetCamera.position.copy(sourceControls.object.position);
    targetCamera.quaternion.copy(sourceControls.object.quaternion);

    // Copy zoom and ensure projection matrix is updated
    targetCamera.zoom = sourceControls.object.zoom;
    targetCamera.updateProjectionMatrix();

    // Sync the target (focus point)
    targetControls.target.copy(sourceControls.target);
    targetControls.update();

    syncing = false; // Allow further sync
}

// Start the animation loop
animate();




///// Image difference

// Reference the existing dialog and close button
const dialog = document.getElementById('differenceDialog'); // Dialog container
const dialogContent = document.getElementById('differenceView'); // Dialog content
const dragHandle = document.getElementById('drag-handle');  // Dragging header
const closeDialogButton = document.querySelector('.close-button'); // Close button inside dialog
let recomputeDiff = true;

// Function to open the dialog
function openDialog() {
    // Display the dialog (+ overlay)
    dialog.style.display = 'flex';
    document.body.style.overflow = 'hidden'; // Disable scrolling on the background

    // Update parameters
    difWin.updateDiffParams(params.maxDiff, params.imgOverlay);

    // Show dialog (recomputing difference if necessary)
    difWin.show(containerD.clientWidth, containerD.clientHeight, recomputeDiff);
    // console.log("container size: " + containerD.clientWidth + " x " + containerD.clientHeight);

    recomputeDiff = false;  // to reopen dialog faster
}

// Function to close the dialog
function closeDialog() {
    dialog.style.display = 'none'; // Hide the dialog
    document.body.style.overflow = 'auto'; // Re-enable scrolling
}

// Add functionality to close the dialog
closeDialogButton.addEventListener('click', closeDialog);

// Optional: Close the dialog by clicking outside the content
dialog.addEventListener('click', (event) => {
    if (event.target === dialog) {
        closeDialog();
    }
});


// Dragging variables
let offsetX = 0, offsetY = 0;
let isDragging = false;

// When mouse is pressed on the dialog header, start dragging
dragHandle.addEventListener('mousedown', (e) => {
    isDragging = true;
    offsetX = e.clientX - dialog.offsetLeft;
    offsetY = e.clientY - dialog.offsetTop;
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
});

// While dragging, update the dialog position
function onMouseMove(e) {
    if (isDragging) {
        dialog.style.left = `${e.clientX - offsetX}px`;
        dialog.style.top = `${e.clientY - offsetY}px`;
    }
}

// When mouse is released, stop dragging
function onMouseUp() {
    isDragging = false;
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);
}

// update max delta value (using GUI control)
function updateDiffParams() {
    difWin.updateDiffParams(params.maxDiff, params.imgOverlay);
}

// Función para enviar la selección a Python
async function notifyPython(selection) {
    // Detectamos si estamos en producción (Render/Nginx) o local
    // Si estamos en Nginx (Render), la ruta raíz / apunta a Python.
    // Si estamos en local (Node puerto 3006), necesitamos apuntar al 8080 explícitamente.
    
    let url = '/set_selected_window'; // Funciona en Render/Nginx
    
    // Si estás probando en local sin Nginx, descomenta la siguiente línea:
    // url = 'http://localhost:8080/set_selected_window'; 

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ selected: selection })
        });
        const data = await response.json();
        console.log("Python actualizado:", data);
    } catch (error) {
        console.error("Error contactando con Python:", error);
    }
}

window.addEventListener('DOMContentLoaded', applyStoredSelection);

