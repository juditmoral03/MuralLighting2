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
    execSync('python3 -m pip show nicegui', { stdio: 'ignore' })
  } catch (error) {
    execSync('pip3 install nicegui', { stdio: 'inherit' })
  }
}

// Start main.py
function startPythonApp() {
  const mainPath = path.join(__dirname, '../menu/main.py')
  const pythonProcess = spawn('python3', [mainPath], { stdio: 'inherit' })
}

// List of .EXR images
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

// Start only the Node server
app.listen(3006, () => {
  console.log('Visit http://127.0.0.1:3006')
  // ensureNiceguiInstalled()
  // startPythonApp()
})
