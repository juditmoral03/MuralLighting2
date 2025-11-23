#!/bin/bash

# 1. Reemplazar el puerto de escucha de Nginx con el que Render nos asigne ($PORT)
sed -i "s/listen 10000;/listen $PORT;/g" /etc/nginx/nginx.conf

# 2. Iniciar Node (WebApp) en puerto 3000 en segundo plano
echo "Iniciando Node..."
cd webapp && PORT=3006 npm start &

# 3. Iniciar NiceGUI (Menu) en puerto 8080 en segundo plano
echo "Iniciando NiceGUI..."
# Asegúrate de que tu main.py use ui.run(port=8080)
cd menu && python3 main.py &

# 4. Iniciar Nginx en primer plano (para mantener el contenedor vivo)
echo "Iniciando Nginx..."
# Esperamos unos segundos para que Python y Node arranquen
sleep 5
nginx -g 'daemon off;'