const express = require('express');
const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();

// Servir arxius estàtics
app.use(express.static(__dirname + '/public'));
app.use('/build/', express.static(path.join(__dirname, 'node_modules/three/build')));
app.use('/jsm/', express.static(path.join(__dirname, 'node_modules/three/examples/jsm')));

// Instal·lar NiceGUI dins d'un entorn virtual local (venv)
function ensureNiceguiInstalled() {
  try {
    execSync('python3 -m venv venv', { stdio: 'inherit' });
    execSync('./venv/bin/pip install nicegui', { stdio: 'inherit' });
  } catch (error) {
    console.error('Error creant l\'entorn virtual o instal·lant NiceGUI:', error);
  }
}

// Iniciar el procés Python (NiceGUI) al port 8080
function startPythonApp() {
  const mainPath = path.join(__dirname, '../menu/main.py');
  const pythonProcess = spawn('./venv/bin/python', [mainPath], { stdio: 'inherit' });
  console.log('Procés NiceGUI iniciat (Python)');
}

// Llistar arxius .EXR
function getEXRFiles(basePath, dir = '', arrayOfFiles = []) {
  const dirPath = basePath + dir;
  const files = fs.readdirSync(dirPath);

  files.forEach(function (file) {
    const fullPath = path.join(dirPath, file);
    const relPath = dir + file;
    if (fs.statSync(fullPath).isDirectory())
      arrayOfFiles = getEXRFiles(basePath, relPath + '/', arrayOfFiles);
    else if (path.extname(file) === '.exr')
      arrayOfFiles.push(relPath);
  });

  return arrayOfFiles;
}

// Endpoint JSON amb llista d'imatges
app.get('/images', (req, res) => {
  const files = getEXRFiles(__dirname + '/public/textures/');
  res.json(files);
});

// Proxy per a NiceGUI
app.use(
  '/gui',
  createProxyMiddleware({
    target: 'http://127.0.0.1:8081', // 👈 canviat de 8080 → 8081
    changeOrigin: true,
  })
);


// Iniciar servidor Express (Render exposarà aquest port)
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Servidor Node/Express iniciat a port ${PORT}`);
  ensureNiceguiInstalled();
  startPythonApp();
});

