# Dockerfile
FROM python:3.9-slim

# 1. Install Node.js, Nginx, and necessary tools
RUN apt-get update && \
    apt-get install -y nodejs npm nginx gettext-base && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Install Python dependencies (NiceGUI)
COPY menu/requirements.txt ./menu/requirements.txt
RUN pip install -r menu/requirements.txt

# 3. Install Node dependencies
COPY webapp/package.json ./webapp/package.json
WORKDIR /app/webapp
RUN npm install

# 4. Copy all source code
WORKDIR /app
COPY . .

# 5. Copy Nginx configuration and start script
COPY nginx.conf /etc/nginx/nginx.conf
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Render uses the PORT variable, but we will expose it internally
ENV PORT=10000

CMD ["./start.sh"]