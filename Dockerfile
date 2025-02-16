# Usa una imagen oficial de Python como base
FROM python:3.10

# Configura el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos del backend al contenedor
COPY . /app

# Instala las dependencias necesarias
RUN pip install --no-cache-dir -r requirements.txt

# Expone los puertos TCP y UDP del nodo
EXPOSE 8000 8880

# Definir las variables de entorno necesarias
ENV NODE_IP="0.0.0.0"
ENV NODE_PORT_TCP=8000
ENV NODE_PORT_UDP=8880

# Ejecuta el nodo cuando el contenedor se inicia
CMD ["python", "chord.py"]
