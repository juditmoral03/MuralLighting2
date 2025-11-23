const express = require('express')
const fs = require('fs')
const path = require('path')

const app = express()

app.use(express.static(__dirname + '/public'))
app.use('/build/', express.static(path.join(__dirname, 'node_modules/three/build')))
app.use('/jsm/', express.static(path.join(__dirname, 'node_modules/three/examples/jsm')))

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

// Start the server
app.listen(3006, () => {
  console.log('Visit http://127.0.0.1:3006')
})
