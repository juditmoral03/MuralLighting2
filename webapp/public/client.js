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

let selectedWindow = '';

containerL.addEventListener('click', () => {
    containerL.classList.remove('hidden');
    containerR.classList.add('hidden');
    selectedWindow = 'left';
    localStorage.setItem('selectedWindow', selectedWindow); 
    notifyPython('left'); 
});

containerR.addEventListener('click', () => {
    containerR.classList.remove('hidden');
    containerL.classList.add('hidden');
    selectedWindow = 'right';
    localStorage.setItem('selectedWindow', selectedWindow); 
    notifyPython('right');
});

function applyStoredSelection() {
    const stored = localStorage.getItem('selectedWindow');
    if (!stored) return;

    if (stored === 'left') {
        containerL.classList.remove('hidden');
        containerR.classList.add('hidden');
        selectedWindow = 'left';
        notifyPython('left'); 
    } else if (stored === 'right') {
        containerR.classList.remove('hidden');
        containerL.classList.add('hidden');
        selectedWindow = 'right';
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
exrLoader.setDataType(THREE.FloatType); // --- CANVI: HalfFloat és més ràpid que Float
const textureLoader = new THREE.TextureLoader(); // --- CANVI: Loader pels JPGs

const TEXTURE_BASE_PATH = './textures/';

// Variables d'estat per evitar que una càrrega antiga sobreescrigui una nova
let currentLeftFile = "";
let currentRightFile = "";

let leftRequestID = 0;
let rightRequestID = 0;

// Variables per saber si l'EXR ja ha guanyat la carrera
let leftEXRLoaded = false;
let rightEXRLoaded = false;

let leftTimeout = null;
let rightTimeout = null;

// --- CANVI: Nova lògica de càrrega progressiva ---
function loadLeftImage(filename) {
    if (!filename) return;
    
    // Cancel·lem la càrrega "Full" anterior si l'usuari canvia ràpid
    if (leftTimeout) clearTimeout(leftTimeout);

    leftRequestID++; 
    const myRequestID = leftRequestID; 

    // Neteja del nom base (traiem .exr)
    let baseName = filename;
    if (baseName.toLowerCase().endsWith('.exr')) {
        baseName = baseName.substring(0, baseName.length - 4);
    }

    // 1. CÀRREGA PREVIEW (_small.exr)
    // Utilitzem exrLoader, però carreguem l'arxiu petit.
    const smallUrl = TEXTURE_BASE_PATH + baseName + '_small.exr';
    
    // console.log(`🔍 [ID:${myRequestID}] Buscant preview: ${baseName}_small.exr`);

    exrLoader.load(smallUrl, (texture) => {
        // Només apliquem si l'usuari no ha canviat d'imatge
        if (myRequestID === leftRequestID) {
            // console.log("✅ Small EXR carregat (Esquerra)");
            updateLeftView(texture); 
        }
    }, undefined, (err) => {
        // Si no existeix el _small, no passa res greu, esperarem al gran.
        console.warn(`⚠️ No s'ha trobat ${baseName}_small.exr (Esquerra)`);
    });

    // 2. CÀRREGA FINAL (Original .exr)
    // Esperem 200ms per no bloquejar la interfície si l'usuari passa el ratolí ràpid
    leftTimeout = setTimeout(() => {
        const fullUrl = TEXTURE_BASE_PATH + baseName + '.exr';
        console.log(`🚀 [ID:${myRequestID}] Iniciant EXR Full (Background): ${baseName}`);

        exrLoader.load(fullUrl, (texture) => {
            if (myRequestID === leftRequestID) {
                console.log(`✅ [ID:${myRequestID}] EXR Full carregat i aplicat.`);
                
                // Opcional: Si vols assegurar-te que s'allibera la memòria del small:
                if(leftView.texture) leftView.texture.dispose();
                
                updateLeftView(texture);
            } else {
                texture.dispose(); // Si arriba tard, a la brossa
            }
        }, undefined, (err) => console.error("Error EXR Full Left:", err));

    }, 200); // Retard de seguretat per fluïdesa del menú
}


// --- CANVI: Aquesta funció fa la feina real d'actualitzar la vista (abans es deia loadLeftImage) ---
function updateLeftView(texture) {
    if (!texture) return;

    // DETECCIÓ ROBUSTA:
    // Els EXR carregats tenen tipus Float (1015) o HalfFloat (1016).
    // Els JPG tenen tipus UnsignedByte (1009).
    const isHDR = (texture.type === THREE.FloatType || texture.type === THREE.HalfFloatType);

    // Cridem a loadImage passant el flag isHDR
    leftView.loadImage(texture, isHDR);

    // Si és JPG, forcem manualment els uniforms per si imageView.js no ho ha fet
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

    // Sincronització normalització (només si els dos són HDR realment)
    if (params.fixNormalization && isHDR) {
        leftView.maxInputLuminance = rightView.maxInputLuminance;
        leftView.avgInputLuminance = rightView.avgInputLuminance;
        leftView.logAvgInputLuminance = rightView.logAvgInputLuminance;
    }

    // Actualitzar finestra diferència
    difWin.leftTexture = texture;
    difWin.uMaxLum = leftView.avgInputLuminance || 1.0; // Evita valors nuls
    recomputeDiff = true;

    render(leftView);
}

// --- CANVI: Mateixa lògica per la dreta ---
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
            // console.log("✅ Small EXR carregat (Dreta)");
            updateRightView(texture);
        }
    }, undefined, (err) => {
        console.warn(`⚠️ No s'ha trobat ${baseName}_small.exr (Dreta)`);
    });

    // 2. FULL (.exr)
    rightTimeout = setTimeout(() => {
        const fullUrl = TEXTURE_BASE_PATH + baseName + '.exr';
        console.log(`🚀 [ID:${myRequestID}] Iniciant EXR Full Dreta...`);

        exrLoader.load(fullUrl, (texture) => {
            if (myRequestID === rightRequestID) {
                console.log(`✅ [ID:${myRequestID}] EXR Full Dreta carregat.`);
                
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
        // Forcem un render de l'esquerra per actualitzar valors
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
        console.log("📥 Cargando desde URL (Python):", img1, img2);
        
        params.leftImage = img1;
        params.rightImage = img2;

        if (leftImageMenu && rightImageMenu) {
            leftImageMenu.setValue(img1);   
            rightImageMenu.setValue(img2);  
        } else {
            // --- CANVI: Ara cridem loadLeftImage amb el NOM (string), no amb el loader
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

const gui = new GUI();

gui.add(params, 'syncViews').name('Sync Views');

const toneMappingFolder = gui.addFolder('Tone Mapping');
toneMappingFolder.add(params, 'selectedTarget', { 'Both Windows': 'both', 'Window 1': 'window1', 'Window 2': 'window2' }).name('Apply To');

var options = toneMappingMethods.map(method => method.name);
toneMappingFolder.add(params, 'toneMappingMethodName', options).name('Tone mapping').onChange((value) => {
    updateFolders(value);
    updateToneMapping();
});

toneMappingFolder.add(params, 'fixNormalization').name('Fix normalization');

for (let method of toneMappingMethods) {
    const folder = toneMappingFolder.addFolder(method.name);
    for (const [_, param] of Object.entries(method.parameters)) {
        folder.add(param, "value", param.min, param.max).name(param.name).onChange(() => updateToneMapping());
    }
}

toneMappingFolder.close(); 
updateFolders(params.toneMappingMethodName); 

function updateFolders(selectedOption) {
    toneMappingFolder.folders.forEach(folder => {
        const titleElement = folder.domElement.querySelector('.title');
        if (folder._title === selectedOption) {
            folder.open(); 
            folder.domElement.style.display = ''; 
            if (titleElement) titleElement.style.display = 'none'; 
        } else {
            folder.close(); 
            folder.domElement.style.display = 'none'; 
            if (titleElement) titleElement.style.display = ''; 
        }
    });
}

const imgDiffFolder = gui.addFolder('Image Difference');
imgDiffFolder.add({ openDialog: () => openDialog() }, 'openDialog').name('Show Difference');
imgDiffFolder.add(params, 'maxDiff', 0.001, 1.0).name('Max Difference').onChange((value) => updateDiffParams());
imgDiffFolder.add(params, 'imgOverlay', 0.0, 1.0).name('Image Overlay').onChange((value) => updateDiffParams());


///// Input images

let leftImageMenu, rightImageMenu;
let images = [];

fetch('/app/images')
    .then(response => {
        if (!response.ok) throw new Error("No se pudo cargar la lista de imágenes");
        return response.json();
    })
    .then(files => {
        images = files;

        // --- CANVI: Ara el onChange crida la nostra funció wrapper amb el nom de l'arxiu ---
        leftImageMenu = gui.add(params, 'leftImage', images).name('Left Image').onChange((value) => {
            console.log("Cambio manual Left:", value);
            loadLeftImage(value); // Passem el string
        });
        
        rightImageMenu = gui.add(params, 'rightImage', images).name('Right Image').onChange((value) => {
            console.log("Cambio manual Right:", value);
            loadRightImage(value); // Passem el string
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
        console.warn('⚠️ Error cargando menú fetch.', error);
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

// Funció per enviar la selecció a Python
async function notifyPython(selection) {
    // ⚠️ IMPORTANT: Si estàs en local, descomenta la línia del localhost
    // Si estàs a Render/Nginx (producció), deixa la relativa.
    
    // Opció A: Producció / Nginx (mateix port)
    // let url = '/set_selected_window'; 
    
    // Opció B: Desenvolupament Local (Python al port 8080, JS en un altre)
    let url = 'http://localhost:8080/set_selected_window'; 

    console.log(`📡 Enviant selecció '${selection}' a: ${url}`);

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ selected: selection })
        });

        // Comprovem si el servidor ha respost OK (codi 200-299)
        if (!response.ok) {
            throw new Error(`Error HTTP del servidor: ${response.status}`);
        }

        const data = await response.json();
        console.log("✅ Python actualitzat:", data);

    } catch (error) {
        // Aquest console.warn evita que l'error aturi tot el programa
        console.warn("⚠️ No s'ha pogut contactar amb Python (és normal si només proves el frontend):", error.message);
    }
}

window.addEventListener('DOMContentLoaded', applyStoredSelection);