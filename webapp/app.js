const express = require('express')
const fs = require('fs')
const path = require('path')
const { execSync, spawn } = require('child_process')

const app = express()

app.use(express.static(__dirname + '/public'))
app.use('/build/', express.static(path.join(__dirname, 'node_modules/three/build')))
app.use('/jsm/', express.static(path.join(__dirname, 'node_modules/three/examples/jsm')))

// Function to check and install nicegui if necessary 
function ensureNiceguiInstalled() {
  try {
    execSync('python3 -m venv venv', { stdio: 'inherit' });
    execSync('./venv/bin/pip install nicegui', { stdio: 'inherit' });
  } catch (error) {
    console.error('Error creando entorno virtual o instalando NiceGUI:', error);
  }
}


// Start main.py
function startPythonApp() {
  const mainPath = path.join(__dirname, '../menu/main.py');
  const pythonProcess = spawn('./venv/bin/python', [mainPath], { stdio: 'inherit' });
}


//List of .EXR images
function getEXRFiles(basePath, dir = '', arrayOfFiles = []) {
  const dirPath = basePath + dir
  const files = fs.readdirSync(dirPath)

  files.forEach(function (file) {
    const fullPath = path.join(dirPath, file)
    const relPath = dir + file
    if (fs.statSync(fullPath).isDirectory())
      arrayOfFiles = getEXRFiles(basePath, relPath + '/', arrayOfFiles)
    else if (path.extname(file) === '.exr')
      arrayOfFiles.push(relPath)
  })

  return arrayOfFiles
}

app.get('/images', (req, res) => {
  const files = getEXRFiles(__dirname + '/public/textures/')
  res.json(files)
})


// Start the server and then Python
app.listen(3006, () => {
  console.log('Visit http://127.0.0.1:3006')
  ensureNiceguiInstalled()
  startPythonApp()
})
