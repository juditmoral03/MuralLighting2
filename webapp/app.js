const express = require('express');
const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();

// Serveix arxius estàtics
app.use(express.static(__dirname + '/public'));
app.use('/build/', express.static(path.join(__dirname, 'node_modules/three/build')));
app.use('/jsm/', express.static(path.join(__dirname, 'node_modules/three/examples/jsm')));

// Instal·la NiceGUI en un venv local
function ensureNiceguiInstalled() {
  try {
    execSync('python3 -m venv venv', { stdio: 'inherit' });
    execSync('./venv/bin/pip install --no-cache-dir nicegui', { stdio: 'inherit' });
  } catch (error) {
    console.error('Error creant venv o instal·lant NiceGUI:', error);
  }
}

// Inicia el procés Python amb autorestart
let pythonProcess = null;
function startPythonApp() {
  const mainPath = path.join(__dirname, '../menu/main.py');

  function launch() {
    pythonProcess = spawn('./venv/bin/python', [mainPath], { stdio: 'inherit' });

    pythonProcess.on('exit', (code) => {
      console.log(`Procés Python tancat (codi ${code}), reiniciant en 3s...`);
      setTimeout(launch, 3000);
    });
  }

  launch();
}

// Endpoint per obtenir fitxers EXR
function getEXRFiles(basePath, dir = '', arrayOfFiles = []) {
  const dirPath = basePath + dir;
  const files = fs.readdirSync(dirPath);
  for (const file of files) {
    const fullPath = path.join(dirPath, file);
    const relPath = dir + file;
    if (fs.statSync(fullPath).isDirectory())
      arrayOfFiles = getEXRFiles(basePath, relPath + '/', arrayOfFiles);
    else if (path.extname(file) === '.exr')
      arrayOfFiles.push(relPath);
  }
  return arrayOfFiles;
}

app.get('/images', (req, res) => {
  const files = getEXRFiles(__dirname + '/public/textures/');
  res.json(files);
});

// Configura el proxy a NiceGUI (port intern 8081)
app.use(
  '/gui',
  createProxyMiddleware({
    target: 'http://127.0.0.1:8081',
    changeOrigin: true,
    ws: true, // permet WebSockets (necessari per NiceGUI)
    logLevel: 'debug',
  })
);

// Inicia el servidor Express
const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  console.log(`Servidor Node/Express iniciat al port ${PORT}`);
  ensureNiceguiInstalled();

  // Espera uns segons per evitar col·lisions
  setTimeout(() => {
    console.log('Iniciant NiceGUI...');
    startPythonApp();
  }, 5000);
});
