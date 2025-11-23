#!/bin/bash

echo "Instal·lant deps Python..."
pip3 install -r menu/requirements.txt

echo "Iniciant NiceGUI..."
cd menu || exit 1
python3 main.py &  # Python en background
PYTHON_PID=$!

echo "Iniciant Node/Express..."
cd ../webapp || exit 1
npm start

echo "Node ha tancat, tancant Python..."
kill $PYTHON_PID
