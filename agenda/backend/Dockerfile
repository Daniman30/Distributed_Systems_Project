# Imagen base de Python
FROM python:3.10

# Definir el directorio de trabajo
WORKDIR /app

# Copiar los archivos del backend al contenedor
COPY requirements.txt .
COPY ./chord_dht .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer los puertos
EXPOSE 5000 8000 8880

# Variables de entorno
ENV NODE_IP="0.0.0.0"
ENV NODE_PORT_TCP=8000
ENV NODE_PORT_UDP=8880

# Ejecutar el backend y Chord
CMD ["sh", "-c", "python app.py"]
