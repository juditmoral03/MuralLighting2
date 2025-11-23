# Dockerfile
FROM python:3.9-slim

# 1. Instalamos Node.js, Nginx y herramientas necesarias
RUN apt-get update && \
    apt-get install -y nodejs npm nginx gettext-base && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Instalamos dependencias de Python (NiceGUI)
COPY menu/requirements.txt ./menu/requirements.txt
RUN pip install -r menu/requirements.txt

# 3. Instalamos dependencias de Node
COPY webapp/package.json ./webapp/package.json
WORKDIR /app/webapp
RUN npm install

# 4. Copiamos todo el código fuente
WORKDIR /app
COPY . .

# 5. Copiamos la configuración de Nginx y el script de inicio
COPY nginx.conf /etc/nginx/nginx.conf
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Render usa la variable PORT, pero nosotros expondremos internamente
ENV PORT=10000

CMD ["./start.sh"]