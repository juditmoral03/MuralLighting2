#!/bin/bash

# 1. Replace port in Nginx
sed -i "s/listen 10000;/listen $PORT;/g" /etc/nginx/nginx.conf

# 2. Start Node (WebApp)
echo "Starting Node..."
cd webapp && PORT=3006 npm start &

# 3. Start NiceGUI (Menu)
echo "Starting NiceGUI..."
cd menu && python3 main.py &

# 4. --- THE CHANGE IS HERE ---
echo "Waiting for Python and Node to start..."
# Increased from 5 to 15 seconds to ensure NiceGUI is ready
sleep 15 

# 5. Start Nginx
echo "Starting Nginx..."
nginx -g 'daemon off;'