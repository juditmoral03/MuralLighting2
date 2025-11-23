#!/bin/bash

# 1. Reemplazar puerto en Nginx
sed -i "s/listen 10000;/listen $PORT;/g" /etc/nginx/nginx.conf

# 2. Iniciar Node (WebApp)
echo "Iniciando Node..."
cd webapp && PORT=3006 npm start &

# 3. Iniciar NiceGUI (Menu)
echo "Iniciando NiceGUI..."
cd menu && python3 main.py &

# 4. --- EL CAMBIO ESTÁ AQUÍ ---
echo "Esperando a que Python y Node arranquen..."
# Aumentamos de 5 a 15 segundos para asegurar que NiceGUI esté listo
sleep 15 

# 5. Iniciar Nginx
echo "Iniciando Nginx..."
nginx -g 'daemon off;'