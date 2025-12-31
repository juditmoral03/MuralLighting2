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
// Interactive frames
containerL.classList.add('image-frame', 'hidden');
containerR.classList.add('image-frame', 'hidden');

let selectedWindow = ''; // Inicialmente vacío

// CLICK EN VENTANA IZQUIERDA
containerL.addEventListener('click', () => {
    if (selectedWindow === 'left') {
        // Si ya estaba seleccionada, la deseleccionamos
        containerL.classList.add('hidden'); // Ocultamos borde
        selectedWindow = ''; // Estado vacío
        localStorage.removeItem('selectedWindow'); 
        //notifyPython(null); // Enviamos null a Python
    } else {
        // Si NO estaba seleccionada, la activamos (y desactivamos la otra)
        containerL.classList.remove('hidden'); // Mostramos borde
        containerR.classList.add('hidden');    // Ocultamos borde derecha
        selectedWindow = 'left';
        localStorage.setItem('selectedWindow', selectedWindow); 
        //notifyPython('left'); 
    }
});

// CLICK EN VENTANA DERECHA
containerR.addEventListener('click', () => {
    if (selectedWindow === 'right') {
        // Si ya estaba seleccionada, la deseleccionamos
        containerR.classList.add('hidden'); // Ocultamos borde
        selectedWindow = ''; // Estado vacío
        localStorage.removeItem('selectedWindow');
        //notifyPython(null);
    } else {
        // Si NO estaba seleccionada, la activamos (y desactivamos la otra)
        containerR.classList.remove('hidden'); // Mostramos borde
        containerL.classList.add('hidden');    // Ocultamos borde izquierda
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
// Funció per enviar la selecció a Python
async function notifyPython(selection) {
    
    // --- CORRECCIÓN IMPORTANTE ---
    // En local, el JS vive en el puerto 3006 y Python en el 8080.
    // Debemos poner la URL completa de Python.
    // Si estás en producción (Render), probablemente ambos estén bajo el mismo dominio, 
    // así que podrías necesitar una comprobación.
    
    let url;
    if (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost') {
        // Modo LOCAL: Apuntamos al puerto de NiceGUI (8080)
        url = 'http://127.0.0.1:8080/set_selected_window';
    } else {
        // Modo PRODUCCIÓN: Asumimos que están en el mismo dominio
        url = '/set_selected_window';
    }

    // console.log(`📡 Enviant selecció '${selection}' a: ${url}`);

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
        console.warn("⚠️ Error conectando con Python:", error);
    }
}

window.addEventListener('DOMContentLoaded', applyStoredSelection);
window.loadLeftImage = loadLeftImage;
window.loadRightImage = loadRightImage;


// Escuchar mensajes desde el padre (Python/NiceGUI en puerto 8080)
window.addEventListener('message', function(event) {
    // Es buena práctica verificar el origen, pero en local podemos saltarlo o confiar.
    const data = event.data;

    if (data.type === 'change_left') {
        console.log("📨 Recibida orden cambiar Izquierda:", data.path);
        loadLeftImage(data.path);
    } 
    else if (data.type === 'change_right') {
        console.log("📨 Recibida orden cambiar Derecha:", data.path);
        loadRightImage(data.path);
    }

    // --- NUEVO CÓDIGO PARA SYNC ---
    if (data.type === 'toggle_sync') {
        console.log("🔄 Sync cambiado a:", data.value);
        
        // 1. Actualizar la variable lógica
        params.syncViews = data.value;

        // 2. Actualizar visualmente el checkbox del panel derecho (lil-gui)
        if (gui && gui.controllers) {
            gui.controllers.forEach(controller => {
                if (controller.property === 'syncViews') {
                    controller.setValue(data.value);
                }
            });
        }
        
        // 3. Forzar resincronización inmediata al activar
        if (data.value === true) {
            syncing = false; 
            // Copiamos la cámara Izquierda a la Derecha
            rightView.camera.position.copy(leftView.camera.position);
            rightView.camera.quaternion.copy(leftView.camera.quaternion);
            rightView.camera.zoom = leftView.camera.zoom;
            controlsR.target.copy(controlsL.target);
        }
    }

    // --- BLOQUE TONE MAPPING (SOLUCIÓN DEFINITIVA V2) ---
    if (data.type === 'tm_update') {
        
        // 1. Target
        if (data.target) params.selectedTarget = data.target;

        // 2. Mapeo
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

            // --- APLICACIÓN DE PARÁMETROS ROBUSTA ---
            
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

            // C) LUMINANCE (Max Lum) - AQUÍ ESTÁ EL ARREGLO
            if (data.algo === "toneMappingLuminance") {
                const paramKeys = Object.keys(methodObj.parameters);
                
                if (paramKeys.length > 0) {
                    // TRUCO: Cogemos el primer parámetro que tenga el shader, se llame como se llame.
                    // Esto arregla el error de nombres desconocidos.
                    const realName = paramKeys[0]; 
                    console.log("🔗 Conectando slider a:", realName);
                    methodObj.parameters[realName].value = data.maxLum;
                } else {
                    console.warn("⚠️ No se encontraron parámetros en toneMappingLuminance");
                }
            }
        }

        // 4. Render
        params.fixNormalization = data.fix;
        if (typeof updateToneMapping === 'function') updateToneMapping();
    }


    // --- BLOQUE IMAGE DIFFERENCE ---
    if (data.type === 'open_diff') {
        console.log("🔘 Opening Difference Dialog from Menu");
        // Llamamos a la función global openDialog() que ya tienes definida en client.js
        if (typeof openDialog === 'function') {
            openDialog();
        }
    }


    // =========================================================
//  LÓGICA DE CONTROLES HTML (Diferencia de Imágenes)
// =========================================================

// 1. Referencias a los elementos del DOM (Sliders en index.html)
const sliderDiff = document.getElementById('slider_maxDiff');
const sliderOver = document.getElementById('slider_overlay');
const labelDiff  = document.getElementById('val_maxDiff');
const labelOver  = document.getElementById('val_overlay');

// 2. Activar listeners si existen los elementos
if (sliderDiff && sliderOver) {
    // Escuchar cambios en Max Difference
    sliderDiff.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        params.maxDiff = val;
        labelDiff.textContent = val.toFixed(3); 
        updateDiffParams(); 
    });

    // Escuchar cambios en Image Overlay
    sliderOver.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        params.imgOverlay = val;
        labelOver.textContent = val.toFixed(2); 
        updateDiffParams(); 
    });
}

// =========================================================
//  LISTENER DE MENSAJES (Python -> JS)
// =========================================================

window.addEventListener('message', function(event) {
    const data = event.data;

    // --- (Aquí van tus otros ifs: change_left, tm_update, sync, etc.) ---
    // Asegúrate de MANTENER los bloques anteriores de tone mapping, sync, etc.
    // Solo reemplaza o añade la parte de 'toggle_diff' abajo.

    if (data.type === 'change_left') { loadLeftImage(data.path); }
    if (data.type === 'change_right') { loadRightImage(data.path); }
    
    // ... Tu bloque de toggle_sync ...
    // ... Tu bloque de tm_update ...


    // --- BLOQUE IMAGE DIFFERENCE (TOGGLE ARREGLADO) ---
    if (data.type === 'toggle_diff') {
        console.log("🔘 Toggle Difference Window");
        
        const dialog = document.getElementById('differenceDialog');
        if (dialog) {
            // USAMOS getComputedStyle: La forma robusta de saber si está visible
            const style = window.getComputedStyle(dialog);
            
            if (style.display === 'none') {
                // Si está oculto -> Abrir
                if (typeof openDialog === 'function') openDialog();
            } else {
                // Si está visible (flex, block, etc) -> Cerrar
                if (typeof closeDialog === 'function') closeDialog();
            }
        }
    }
});

});