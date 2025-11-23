#!/bin/bash

# --- Arrancar NiceGUI (Python) ---
echo "Iniciant NiceGUI..."
cd menu || exit 1
python3 main.py &            # Executa Python en background
PYTHON_PID=$!                # Guarda el PID del procés Python

# --- Tornar a webapp i arrencar Node ---
cd ../webapp || exit 1
echo "Iniciant Node/Express..."
npm start

# --- Quan Node es tanqui, tanca Python ---
echo "Node ha tancat, tancant Python..."
kill $PYTHON_PID

