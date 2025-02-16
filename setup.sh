#!/bin/bash

# Configuración de la red
NETWORK_NAME="chord_network"
SUBNET="172.20.0.0/24"
BACKEND_IP="172.20.0.2"
FRONTEND_IP="172.20.0.3"

# Crear la red Docker si no existe
if ! docker network inspect $NETWORK_NAME &>/dev/null; then
    echo "Creando red Docker..."
    docker network create --subnet=$SUBNET $NETWORK_NAME
else
    echo "La red $NETWORK_NAME ya existe."
fi

# Construir la imagen del backend
echo "Construyendo la imagen de backend..."
docker build -t chord_node ./backend

# Ejecutar el backend Flask
echo "Levantando el backend..."
docker run -d --name backend \
  --network $NETWORK_NAME \
  --ip $BACKEND_IP \
  -p 5000:5000 \
  -e NODE_IP="0.0.0.0" \
  -e NODE_PORT_TCP=8000 \
  -e NODE_PORT_UDP=8880 \
  chord_node

# Ejecutar el frontend con Nginx
echo "Levantando el frontend..."
docker run -d --name frontend \
  --network $NETWORK_NAME \
  --ip $FRONTEND_IP \
  -p 80:80 \
  -v $(pwd)/frontend/templates:/usr/share/nginx/html \
  -v $(pwd)/frontend2/static:/usr/share/nginx/html/static \
  nginx

echo "Backend y frontend están corriendo."
echo "Para agregar nodos, usa: python docker_manager.py"
