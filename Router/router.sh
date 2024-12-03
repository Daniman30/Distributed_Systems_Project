#!/bin/bash

# Redirigir tráfico según el puerto o ruta
while true; do
  # Escuchar en el puerto 80
  nc -l -p 80 -c '
    # Leer la solicitud
    read request
    if [[ $request == *"/api"* ]]; then
      # Si la solicitud es para el backend, redirigir a backend:8000
      nc backend 8000
    else
      # Si no, redirigir al frontend:8080
      nc frontend 8080
    fi
  '
done
